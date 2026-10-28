#!/usr/bin/env bash

# File Path Picker & AI Prompt Generator for Rofi
# Dynamic action selection (Syntax, Logic, Refactor, Rewrite, Sync, None)
# Standalone use: chmod +x prompt_picker.sh && ./prompt_picker.sh

TARGET_FILE="file_path.md"
LEGACY_TARGET_FILES=("file_path" "file_path.txt")
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Capture the currently focused window before opening any menus.
ACTIVE_WIN=$(xdotool getactivewindow 2>/dev/null || true)

FILE_PATH=""

trim_input() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

find_target_in_dir() {
    local dir="$1"

    [[ -n "$dir" && -d "$dir" ]] || return 1

    if [[ -f "$dir/$TARGET_FILE" ]]; then
        FILE_PATH="$dir/$TARGET_FILE"
        return 0
    fi

    local legacy_file
    for legacy_file in "${LEGACY_TARGET_FILES[@]}"; do
        if [[ -f "$dir/$legacy_file" ]]; then
            FILE_PATH="$dir/$legacy_file"
            return 0
        fi
    done

    return 1
}

declare -A VISITED_PIDS=()

search_pid_tree_for_target() {
    local pid="$1"
    local cwd
    local child
    local children_file
    local -a children=() child_batch=()

    [[ "$pid" =~ ^[0-9]+$ ]] || return 1
    [[ -d "/proc/$pid" ]] || return 1
    [[ -z "${VISITED_PIDS[$pid]+x}" ]] || return 1

    VISITED_PIDS["$pid"]=1

    cwd=$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)
    if find_target_in_dir "$cwd"; then
        return 0
    fi

    # Read the kernel's child list directly instead of scanning all processes.
    # Fall back for systems where this procfs interface is unavailable.
    if [[ -r "/proc/$pid/task/$pid/children" ]]; then
        # Worker threads can own child processes too.
        for children_file in /proc/"$pid"/task/*/children; do
            child_batch=()
            { read -r -a child_batch < "$children_file"; } 2>/dev/null || true
            children+=("${child_batch[@]}")
        done
    else
        mapfile -t children < <(pgrep -P "$pid" 2>/dev/null || true)
    fi

    for child in "${children[@]}"; do
        if search_pid_tree_for_target "$child"; then
            return 0
        fi
    done

    return 1
}

# First, check beside this script, then the directory from which it was launched.
find_target_in_dir "$SCRIPT_DIR" || true
find_target_in_dir "$PWD" || true

# Then check the active window process and its descendants.
if [[ -z "$FILE_PATH" && -n "$ACTIVE_WIN" ]]; then
    WINDOW_PID=$(xdotool getwindowpid "$ACTIVE_WIN" 2>/dev/null || true)

    if [[ -n "$WINDOW_PID" ]]; then
        search_pid_tree_for_target "$WINDOW_PID" || true
    fi
fi

LIST_ACTION="2. Create/update project file list"
AGENTS_ACTION="1. Update AGENTS.md File"
DELETE_BRANCH_ACTION="Delete Current Branch"
GIT_PROMPTS_ACTION="1. Git Prompts"
MAIN_PROJECT_PROMPTS_ACTION="2. Main Project Prompts"

make_delete_branch_message() {
    cat <<'PROMPT'
Safely discard all uncommitted work in the current branch, switch back to main, and force-delete the feature branch:

1. Discard all unstaged and staged changes, and clean untracked files:
   git reset --hard HEAD
   git clean -fd

2. Switch back to the main branch:
   git checkout main

3. Force-delete the feature branch completely:
   git branch -D "Current Branch Name"

4. Confirm by running `git status` and `git branch -v` to ensure we are cleanly on `main` with no leftover changes.
PROMPT
}

make_agents_prompt() {
    cat <<'PROMPT'
Please review the recent changes in the project architecture (such as CMakeLists.txt, include/, src/, or examples/), analyze the structural updates made to our C++20 CFD library, and update the AGENTS.md file accordingly to keep the documentation fully synchronized.
PROMPT
}

make_list_prompt() {
    cat <<'PROMPT'
Inspect workspace and update `file_path.md` at project root using its embedded schema.
Derive labels strictly by converting the filename's snake_case to Title Case (do not append words like 'placeholder').
Ensure exact file paths on disk without duplicating extensions. Do not touch source files.

PROMPT
}

make_commit_changes_prompt() {
    cat <<'PROMPT'
Please inspect the current git status and git diff of my C++ CFD project. Based on the latest modifications, perform the following steps precisely:

1. Analyze Changes: Review what files have changed and understand the technical intent.
2. Formulate Conventional Commit: Choose a standard type (feat, fix, refactor, docs, test, chore) with an appropriate scope (e.g., core, mesh, solver, cfd-toolkit).
3. Draft Commit Message:
   - Summary: Write a concise, standardized, and meaningful title (imperative mood, under 50 chars).
   - Description: Write a professional, bullet-pointed body explaining *what* was changed and *why* from a mechanical engineering / software design perspective (avoiding trivial or overly granular details).
4. Stage & Commit: Stage all modified files and execute the local git commit using this exact message.
*Strict Constraint:* Do NOT push to the remote repository (`git push`). Only perform the local commit and output the final commit summary and description for my review.
PROMPT
}

make_push_commits_prompt() {
    cat <<'PROMPT'
Please check the current git status and inspect any local commits that have not yet been pushed to the remote repository (origin). Follow these steps carefully:

1. Identify Unpushed Commits: Run a check (such as reviewing git status or checking log differences against the remote tracking branch) to list any local commits waiting to be pushed.
2. Push to Remote: Safely push these local commits to the corresponding remote branch on GitHub.
3. Verify Synchronization: Confirm that the push was successful and that the local working tree and remote repository are fully synchronized.
*Strict Constraint:* Only push the current active branch. Do not perform any destructive resets or force pushes unless explicitly requested, and report the final status clearly.
PROMPT
}

make_create_branch_prompt() {
    local branch_name="$1"

    printf 'Please create a new local Git branch named "%s" originating from the current branch\x27s latest commit (HEAD), following these exact constraints:\n\n1. Verification Check: Check if a branch named "%s" already exists locally. If it exists, abort and notify me.\n2. Branch Creation: Run `git branch %s` (without using checkout, switch, or `--`).\n3. Stay on Current Branch: Do NOT switch/checkout to the newly created branch. Keep the currently checked-out branch active.\n4. Local Only: Do NOT push the new branch to the remote repository (`origin`).\n5. Confirm Output: Run `git branch --list` and `git status` to verify that "%s" exists and that the active branch remains unchanged.\n' \
        "$branch_name" "$branch_name" "$branch_name" "$branch_name"
}

show_create_branch_prompt() {
    local branch_name

    branch_name=$(rofi -dmenu -i -p "New branch name:" -matching fuzzy </dev/null) || exit 0
    branch_name=$(trim_input "$branch_name")
    [[ -n "$branch_name" ]] || exit 0

    copy_and_paste_prompt "$(make_create_branch_prompt "$branch_name")"
}

make_switch_branch_prompt() {
    local branch_name="$1"

    printf 'Please switch to the branch named "%s", strictly adhering to the following rules:\n\n1. Working Tree Pre-check: Run `git status` to verify that there are no uncommitted or untracked changes that could conflict with the branch switch. If there are pending changes, stop and ask me before proceeding.\n2. Branch Switch: Switch to the branch using the modern Git command `git switch %s` (or alternatively `git checkout %s`).\n3. Verification: Run `git status` and `git branch --show-current` to confirm that the active working branch is now indeed "%s".\n4. Safety Constraint: Do NOT pull from or push to any remote repository; keep the operation strictly local.\n' \
        "$branch_name" "$branch_name" "$branch_name" "$branch_name"
}

show_switch_branch_prompt() {
    local branch_name

    branch_name=$(rofi -dmenu -i -p "Branch name to switch to:" -matching fuzzy </dev/null) || exit 0
    branch_name=$(trim_input "$branch_name")
    [[ -n "$branch_name" ]] || exit 0

    copy_and_paste_prompt "$(make_switch_branch_prompt "$branch_name")"
}

make_delete_named_branch_prompt() {
    local branch_name="$1"

    printf 'Please completely delete the branch named "%s" both locally and from the remote repository (GitHub), strictly following these steps:\n\n1. Safety Pre-check: Ensure that the currently active checked-out branch is NOT "%s". If I am currently on that branch, switch to the default branch (e.g., `main` or `feat/1d-core`) first.\n2. Local Deletion: Force delete the local branch by running `git branch -D %s` to ensure unmerged changes don\x27t block the cleanup.\n3. Remote Deletion: Delete the branch from the remote repository by running `git push origin --delete %s`.\n4. Prune Tracking References: Run `git remote prune origin` (or `git fetch --prune`) to clean up any stale remote-tracking branches.\n5. Verification: Run `git branch -a` to verify that "%s" is completely gone from both local and remote lists.\n' \
        "$branch_name" "$branch_name" "$branch_name" "$branch_name" "$branch_name"
}

show_delete_named_branch_prompt() {
    local branch_name

    branch_name=$(rofi -dmenu -i -p "Branch name to delete:" -matching fuzzy </dev/null) || exit 0
    branch_name=$(trim_input "$branch_name")
    [[ -n "$branch_name" ]] || exit 0

    copy_and_paste_prompt "$(make_delete_named_branch_prompt "$branch_name")"
}

show_git_prompts_menu() {
    local chosen_action

    chosen_action=$(
        printf '%s\n' "1. Commit Changes" "2. Push Commits" "3. Remove" "4. Rename" "5. Move" "6. Create New Branch" "7. Switch Branch" "8. $DELETE_BRANCH_ACTION" "9. Delete Branch" |
            rofi -dmenu -i -no-custom -p "Git Prompts:" -matching fuzzy
    )

    case "$chosen_action" in
        "1. Commit Changes") copy_and_paste_prompt "$(make_commit_changes_prompt)" ;;
        "2. Push Commits") copy_and_paste_prompt "$(make_push_commits_prompt)" ;;
        "3. Remove") show_remove_prompt ;;
        "4. Rename") show_rename_prompt ;;
        "5. Move") show_move_prompt ;;
        "6. Create New Branch") show_create_branch_prompt ;;
        "7. Switch Branch") show_switch_branch_prompt ;;
        "8. $DELETE_BRANCH_ACTION") show_delete_branch_message ;;
        "9. Delete Branch") show_delete_named_branch_prompt ;;
    esac
}

copy_and_paste_prompt() {
    local prompt="$1"
    local window_class="" paste_key="shift+Insert" clipboard_tool clipboard_text
    local primary_ok=0 focused_win=""

    # Always expose the generated prompt to callers and terminal users.
    printf '%s\n' "$prompt"

    if command -v xclip >/dev/null 2>&1; then
        clipboard_tool=xclip
        if ! printf '%s' "$prompt" | xclip -selection clipboard 2>/dev/null; then
            notify-send "Error" "Could not copy the prompt to the clipboard." -i dialog-error
            return 1
        fi
        # Shift+Insert uses PRIMARY in VTE terminals and CLIPBOARD in others.
        if printf '%s' "$prompt" | xclip -selection primary 2>/dev/null; then
            primary_ok=1
        fi
    elif command -v xsel >/dev/null 2>&1; then
        clipboard_tool=xsel
        if ! printf '%s' "$prompt" | xsel --clipboard --input; then
            notify-send "Error" "Could not copy the prompt to the clipboard." -i dialog-error
            return 1
        fi
        if printf '%s' "$prompt" | xsel --primary --input; then
            primary_ok=1
        fi
    else
        notify-send "Error" "Could not copy the prompt to the clipboard." -i dialog-error
        return 1
    fi

    if [[ -n "$ACTIVE_WIN" ]]; then
        # Rofi exits before Cinnamon consistently restores the previous window.
        # Let focus settle before querying window metadata or sending keys.
        sleep 0.25
        # Older xdotool versions have no getwindowclassname command. Read the
        # actual WM_CLASS with xprop; titles can contain arbitrary project names.
        if command -v xprop >/dev/null 2>&1; then
            window_class=$(xprop -id "$ACTIVE_WIN" WM_CLASS 2>/dev/null || true)
            window_class="${window_class##*, \"}"
            window_class="${window_class%\"}"
        else
            window_class=$(xdotool getwindowclassname "$ACTIVE_WIN" 2>/dev/null || true)
        fi
        window_class="${window_class,,}"

        # A bare Ctrl+V can reach a terminal application as image paste. Ask
        # the terminal to paste text with Shift+Insert instead, preserving its
        # bracketed-paste handling for multiline prompts. Never type newlines.
        case "$window_class" in
            code|code-oss|vscode|visual-studio-code|vscodium|codium|"code - insiders"|\
            gedit|org.gnome.gedit|org.gnome.texteditor|xed|kate|mousepad|\
            google-chrome|chromium|chromium-browser|firefox)
                paste_key="ctrl+v"
                ;;
            *terminal*|*ghostty*|*wezterm*|kitty|alacritty|terminator|tilix|\
            konsole|xterm|uxterm|urxvt|rxvt|st|st-256color|sakura)
                paste_key="${PROMPT_PICKER_PASTE_KEY:-shift+Insert}"
                ;;
            *)
                # Shift+Insert is also a text-paste shortcut in GUI toolkits.
                paste_key="${PROMPT_PICKER_PASTE_KEY:-shift+Insert}"
                ;;
        esac

        if [[ "${paste_key,,}" == "shift+insert" ]] && ((primary_ok == 0)); then
            notify-send "Error" "Could not copy the prompt to PRIMARY; automatic paste was skipped." -i dialog-error
            return 1
        fi

        if [[ "$clipboard_tool" == xclip ]]; then
            clipboard_text=$(xclip -selection clipboard -o 2>/dev/null || true)
        else
            clipboard_text=$(xsel --clipboard --output 2>/dev/null || true)
        fi
        if [[ -z "$prompt" || -z "$clipboard_text" ]]; then
            notify-send "Error" "The prompt is not available on the clipboard." -i dialog-error
            return 1
        fi
        # Activate synchronously so the paste key cannot land in Rofi.
        if ! xdotool windowactivate --sync "$ACTIVE_WIN" 2>/dev/null; then
            printf '%s\n' 'Could not focus the original window; the prompt is on the clipboard.' >&2
            return 1
        fi
        sleep 0.05
        focused_win=$(xdotool getactivewindow 2>/dev/null || true)
        if [[ "$focused_win" != "$ACTIVE_WIN" ]]; then
            printf '%s\n' 'Focus changed before paste; the prompt is on the clipboard.' >&2
            return 1
        fi
        if ! xdotool key --clearmodifiers "$paste_key" 2>/dev/null; then
            printf '%s\n' 'Could not paste the prompt; it is on the clipboard.' >&2
            return 1
        fi
    fi
}

show_delete_branch_message() {
    local message
    message=$(make_delete_branch_message)
    copy_and_paste_prompt "$message"
}

show_main_project_prompts_menu() {
    local chosen_action

    chosen_action=$(
        printf '%s\n' "$AGENTS_ACTION" "$LIST_ACTION" |
            rofi -dmenu -i -no-custom -p "Main Project Prompts:" -matching fuzzy
    )

    case "$chosen_action" in
        "$LIST_ACTION") copy_and_paste_prompt "$(make_list_prompt)" ;;
        "$AGENTS_ACTION") copy_and_paste_prompt "$(make_agents_prompt)" ;;
    esac
}

# Generate a standard path description based on TYPE and LABEL.
make_raw_desc() {
    local t="$1"
    local l="$2"
    local p="$3"
    local noun="file"

    case "$t" in
        CLASS|FUNCTION) noun="files" ;;
    esac

    printf '%s %s in the path: `%s`' "$l" "$noun" "$p"
}

# Build menu entries from the selected file.
get_file_menu_list() {
    awk -F'|' '
    BEGIN { OFS = " | " }

    /^[[:space:]]*#/ { next }
    /^[[:space:]]*-+/ { next }
    /^[[:space:]]*=+/ { next }
    /^[[:space:]]*$/ { next }

    {
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", $1)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3)

        if ($1 != "" && $2 != "" && $3 != "") {
            print $1, $2, $3
        } else if ($1 != "") {
            print "<<RAW>>", $0, $0
        }
    }' "$FILE_PATH"
}

trim() {
    local -n value_ref="$1"
    value_ref="${value_ref#"${value_ref%%[![:space:]]*}"}"
    value_ref="${value_ref%"${value_ref##*[![:space:]]}"}"
}

parse_menu_line() {
    local line="$1"
    local -n type_ref="$2"
    local -n label_ref="$3"
    local -n path_ref="$4"

    IFS='|' read -r type_ref label_ref path_ref <<< "$line"

    trim "$2"
    trim "$3"
    trim "$4"
}

describe_menu_line() {
    local line="$1"
    local type label path

    parse_menu_line "$line" type label path

    if [[ "$type" == "<<RAW>>" ]]; then
        printf '%s' "$path"
    else
        make_raw_desc "$type" "$label" "$path"
    fi
}

show_remove_prompt() {
    local selected_line current_desc target_desc="" target_path=""
    local selected_type selected_label
    local selected_count=0 next_action

    while true; do
        if [[ -n "$FILE_PATH" ]]; then
            selected_line=$(
                printf '%s\n' "$FILE_MENU_LIST" |
                    rofi -dmenu -i -no-custom -p "Select file to remove:" -matching normal
            ) || exit 0
            [[ -n "$selected_line" ]] || exit 0

            current_desc=$(describe_menu_line "$selected_line")
            parse_menu_line "$selected_line" selected_type selected_label target_path
        else
            target_path=$(rofi -dmenu -p "Enter file path to remove:" </dev/null) || exit 0
            target_path=$(trim_input "$target_path")
            [[ -n "$target_path" ]] || exit 0
            current_desc="$target_path"
        fi

        if [[ -n "$target_desc" ]]; then
            target_desc+=" And $current_desc"
        else
            target_desc="$current_desc"
        fi
        ((selected_count += 1))

        next_action=$(
            printf '%s\n' "1. Add File" "2. Done" |
                rofi -dmenu -i -no-custom -p "Select another file or finish:" -matching fuzzy
        )

        case "$next_action" in
            "1. Add File") ;;
            "2. Done") break ;;
            *) exit 0 ;;
        esac
    done

    if ((selected_count == 1)); then
        REMOVE_MESSAGE="Safely remove '$target_path' file using \`git rm\` so Git properly stages the deletion, and verify with \`git status\`."
    else
        REMOVE_MESSAGE="Safely remove the following files using \`git rm\` so Git properly stages the deletions, and verify with \`git status\`: $target_desc."
    fi

    copy_and_paste_prompt "$REMOVE_MESSAGE"
}

show_rename_prompt() {
    local selected_line current_desc target_path new_name rename_desc=""
    local next_action selected_type selected_label

    while true; do
        if [[ -n "$FILE_PATH" ]]; then
            selected_line=$(
                printf '%s\n' "$FILE_MENU_LIST" |
                    rofi -dmenu -i -no-custom -p "Select file to rename:" -matching normal
            ) || exit 0
            [[ -n "$selected_line" ]] || exit 0

            current_desc=$(describe_menu_line "$selected_line")
            parse_menu_line "$selected_line" selected_type selected_label target_path
        else
            target_path=$(rofi -dmenu -p "Enter file path to rename:" </dev/null) || exit 0
            target_path=$(trim_input "$target_path")
            [[ -n "$target_path" ]] || exit 0
            current_desc="$target_path"
        fi

        new_name=$(zenity --entry --title="Enter new name." --text="Enter the new name for $target_path:" 2>/dev/null) || exit 0
        new_name=$(trim_input "$new_name")
        [[ -n "$new_name" ]] || exit 0

        if [[ -n "$rename_desc" ]]; then
            rename_desc+=" And "
        fi
        rename_desc+="$current_desc to \`$new_name\`"

        next_action=$(
            printf '%s\n' "1. Add File" "2. Done" |
                rofi -dmenu -i -no-custom -p "Select another file or finish:" -matching fuzzy
        )

        case "$next_action" in
            "1. Add File") ;;
            "2. Done") break ;;
            *) exit 0 ;;
        esac
    done

    RENAME_MESSAGE="Rename $rename_desc using \`git mv\` so Git tracks each rename without losing history. Then verify with \`git status\`."
    copy_and_paste_prompt "$RENAME_MESSAGE"
}

show_move_prompt() {
    local selected_line current_desc target_path new_path move_desc=""
    local next_action selected_type selected_label

    while true; do
        if [[ -n "$FILE_PATH" ]]; then
            selected_line=$(
                printf '%s\n' "$FILE_MENU_LIST" |
                    rofi -dmenu -i -no-custom -p "Select file to move:" -matching normal
            ) || exit 0
            [[ -n "$selected_line" ]] || exit 0

            current_desc=$(describe_menu_line "$selected_line")
            parse_menu_line "$selected_line" selected_type selected_label target_path
        else
            target_path=$(rofi -dmenu -p "Enter file path to move:" </dev/null) || exit 0
            target_path=$(trim_input "$target_path")
            [[ -n "$target_path" ]] || exit 0
            current_desc="$target_path"
        fi

        new_path=$(zenity --entry --title="Enter new path." --text="Enter the new path for $target_path:" 2>/dev/null) || exit 0
        new_path=$(trim_input "$new_path")
        [[ -n "$new_path" ]] || exit 0

        if [[ -n "$move_desc" ]]; then
            move_desc+=" And "
        fi
        move_desc+="$current_desc to \`$new_path\`"

        next_action=$(
            printf '%s\n' "1. Add File" "2. Done" |
                rofi -dmenu -i -no-custom -p "Select another file or finish:" -matching fuzzy
        )

        case "$next_action" in
            "1. Add File") ;;
            "2. Done") break ;;
            *) exit 0 ;;
        esac
    done

    MOVE_MESSAGE="Move $move_desc using \`git mv\` so Git tracks each move as a rename without losing history. Then verify with \`git status\`."
    copy_and_paste_prompt "$MOVE_MESSAGE"
}

if [[ -z "$FILE_PATH" ]]; then
    if command -v zenity >/dev/null 2>&1; then
        zenity --info --title="No file list found" \
            --text="Could not find file_path.md (or a legacy file_path/file_path.txt) beside the script, in the current directory, or in the active project's process tree. Project and Git prompts remain available." \
            2>/dev/null || true
    elif command -v rofi >/dev/null 2>&1; then
        rofi -e "No file_path.md (or legacy file_path/file_path.txt) found. Project and Git prompts remain available." 2>/dev/null || true
    elif command -v notify-send >/dev/null 2>&1; then
        notify-send "No file list found" "Project and Git prompts remain available." -i dialog-information
    fi

    # The no-list route follows the file-operation definitions so Git actions
    # can use their manual path-entry fallback.
    CHOSEN_NO_LIST_ACTION=$(
        printf '%s\n' "$GIT_PROMPTS_ACTION" "$MAIN_PROJECT_PROMPTS_ACTION" |
            rofi -dmenu -i -no-custom -p "No file list found:" -matching fuzzy
    )
    case "$CHOSEN_NO_LIST_ACTION" in
        "$GIT_PROMPTS_ACTION") show_git_prompts_menu || exit 1 ;;
        "$MAIN_PROJECT_PROMPTS_ACTION") show_main_project_prompts_menu || exit 1 ;;
        *) exit 0 ;;
    esac
    exit 0
fi

ACTIONS=(
    "1. None (Just Paste File Path)"
    "2. Add File Path"
    "3. Fix Compiler / Syntax Issues"
    "4. Fix Logic / CFD Implementation"
    "5. Refactor (Clean Code & Modern C++)"
    "6. Rewrite from Scratch"
    "7. Sync / Adapt with another file..."
    "8. ApexFVM : The 5-Stage C++ Performance Pipeline For Project"
    "9. The 3-Stage C++ Performance Pipeline For Class"
    "10. The 3-Stage C++ Performance Pipeline For Function"
)

# Normalize the file list once and reuse the same snapshot in every menu.
# A new invocation reloads the list after project-list updates.
FILE_MENU_LIST=$(get_file_menu_list)
MAIN_MENU_LIST=$(printf '%s\n' "$GIT_PROMPTS_ACTION" "$MAIN_PROJECT_PROMPTS_ACTION" "$FILE_MENU_LIST")

# Keep collecting files until another action is selected.
TARGET_DESC=""
SELECTED_COUNT=0
while true; do
    SELECTED_LINE=$(
        printf '%s\n' "$MAIN_MENU_LIST" |
            rofi -dmenu -i -no-custom -p "Select File or Action:" -matching normal
    )

    if [[ -z "$SELECTED_LINE" ]]; then
        exit 0
    fi

    if [[ "$SELECTED_LINE" == "$LIST_ACTION" ]]; then
        copy_and_paste_prompt "$(make_list_prompt)" || exit 1
        exit 0
    fi

    if [[ "$SELECTED_LINE" == "$GIT_PROMPTS_ACTION" ]]; then
        show_git_prompts_menu || exit 1
        exit 0
    fi

    if [[ "$SELECTED_LINE" == "$MAIN_PROJECT_PROMPTS_ACTION" ]]; then
        show_main_project_prompts_menu || exit 1
        exit 0
    fi

    CURRENT_DESC=$(describe_menu_line "$SELECTED_LINE")
    parse_menu_line "$SELECTED_LINE" TARGET_TYPE TARGET_LABEL TARGET_PATH

    if [[ -n "$TARGET_DESC" ]]; then
        TARGET_DESC+=" And $CURRENT_DESC"
    else
        TARGET_DESC="$CURRENT_DESC"
    fi
    ((SELECTED_COUNT += 1))

    # Step 2: Add another file or choose the action for the collected files.
    CHOSEN_ACTION=$(
        printf '%s\n' "${ACTIONS[@]}" |
            rofi -dmenu -i -no-custom -p "Action for target:" -matching fuzzy
    )

    if [[ -z "$CHOSEN_ACTION" ]]; then
        exit 0
    fi

    [[ "$CHOSEN_ACTION" == "2. Add File Path" ]] || break
done

FINAL_PROMPT=""

case "$CHOSEN_ACTION" in
    *"Fix Compiler / Syntax Issues"*)
        FINAL_PROMPT="Please review and fix all C++ compiler errors, syntax issues, and clangd warnings in the following: $TARGET_DESC."
        ;;
    *"Fix Logic / CFD Implementation"*)
        FINAL_PROMPT="Please inspect the implementation, mathematical logic, and CFD/numerical algorithm (loops, signs, and boundary conditions) to fix bugs in: $TARGET_DESC."
        ;;
    *"Refactor"*)
        FINAL_PROMPT="Please refactor the following without altering its external behavior, applying modern C++ best practices and improving readability: $TARGET_DESC."
        ;;
    *"Rewrite from Scratch"*)
        FINAL_PROMPT="Please rewrite and redesign the following from scratch with a clean, modern, and high-performance C++ design: $TARGET_DESC."
        ;;
    *"Sync / Adapt"*)
        # Collect one or more base/dependency files for the selected targets.
        DEP_DESC=""
        while true; do
            DEP_LINE=$(
                printf '%s\n' "$FILE_MENU_LIST" |
                    rofi -dmenu -i -no-custom -p "Select Base/Dependency File:" -matching normal
            )

            [[ -n "$DEP_LINE" ]] || exit 0

            CURRENT_DEP_DESC=$(describe_menu_line "$DEP_LINE")
            if [[ -n "$DEP_DESC" ]]; then
                DEP_DESC+=" And $CURRENT_DEP_DESC"
            else
                DEP_DESC="$CURRENT_DEP_DESC"
            fi

            SYNC_DEP_ACTION=$(
                printf '%s\n' "2. Add File Path" "3. Done" |
                    rofi -dmenu -i -no-custom -p "Add another base/dependency file?" -matching fuzzy
            )

            [[ -n "$SYNC_DEP_ACTION" ]] || exit 0
            [[ "$SYNC_DEP_ACTION" == "2. Add File Path" ]] || break
        done

        FINAL_PROMPT="Please update and sync $TARGET_DESC based on the interface and changes introduced in $DEP_DESC."
        ;;
    *"ApexFVM : The 5-Stage C++ Performance Pipeline For Project"*)
        APEXFVM_STAGES=(
            "Stage 1: Heap Memory Audit & Pre-allocation"
            "Stage 2: Reference Pass & Move Semantics Optimization"
            "Stage 3: Compile-Time Optimizations (constexpr & Inline)"
            "Stage 4: Compiler & CMake Optimization Flags"
            "Stage 5: Cache Locality & Data Layout Optimization"
        )

        CHOSEN_STAGE=$(
            printf '%s\n' "${APEXFVM_STAGES[@]}" |
                rofi -dmenu -i -no-custom -p "ApexFVM Stage for target:" -matching fuzzy
        )

        [[ -n "$CHOSEN_STAGE" ]] || exit 0

        case "$CHOSEN_STAGE" in
            "Stage 1: Heap Memory Audit & Pre-allocation")
                FINAL_PROMPT=$(cat <<'PROMPT'
Act as an expert C++ performance engineer specializing in Computational Fluid Dynamics (CFD) and high-performance computing (HPC). 

Please review the provided project codebase, specifically focusing on the time loops, solver iterations, and frequently called step functions. 

Your tasks for this first stage are:
1. Identify any dynamic memory allocations occurring inside time loops or frequent function calls (e.g., using `new`, `malloc`, or instantiating/resizing `std::vector` and other containers dynamically).
2. Propose refactoring strategies to eliminate these runtime allocations by shifting them to a pre-allocation (initialization) phase outside the loops.
3. Ensure that data structures are reused across time steps using proper references or pointer swapping (e.g., `std::swap`) to maintain 100% memory locality and avoid memory fragmentation.
4. Provide concrete code snippets/diffs for any flagged violations.

Do not focus on micro-optimizations or compiler flags yet; keep your strict focus entirely on Heap memory management and pre-allocation within the time-marching loops.
PROMPT
)
                ;;
            "Stage 2: Reference Pass & Move Semantics Optimization")
                FINAL_PROMPT=$(cat <<'PROMPT'
Act as an expert C++ performance engineer specializing in Computational Fluid Dynamics (CFD) and modern C++ (C++17/20). 

Please review the codebase, specifically focusing on function signatures, method parameters, and return types across the FVM solver classes and utility modules.

Your tasks for this second stage are:
1. Identify any instances where large data structures (such as `std::vector`, custom mesh grids, or field matrices) are passed to functions or returned by **value**, which triggers expensive and unnecessary deep copies.
2. Refactor these signatures to pass by reference (`const T&` for read-only access, or `T&` when modification is required) or leverage Move Semantics (`std::move`) where resource ownership transfer is intended.
3. Enforce strict `const`-correctness across member functions to prevent accidental modifications and assist the compiler in optimization.
4. Provide clear before-and-after code snippets or diffs for the refactored functions.

Do not touch CMake flags or Heap allocation loops yet; keep your strict focus entirely on function parameter passing, references, and eliminating redundant copying overhead.
PROMPT
)
                ;;
            "Stage 3: Compile-Time Optimizations (constexpr & Inline)")
                FINAL_PROMPT=$(cat <<'PROMPT'
Act as an expert C++ performance engineer specializing in Computational Fluid Dynamics (CFD) and modern C++ (C++17/20) optimization. 

Please review the codebase, focusing on physical/mathematical constants, configuration parameters, and small, frequently-called helper functions or accessor methods (e.g., cell-indexing formulas, boundary check functions, or interpolation utilities).

Your tasks for this third stage are:
1. Identify constants, configuration variables, or lookup calculations that can be evaluated at compile-time using `constexpr` (or `consteval` if applicable) to embed values directly into machine instructions and eliminate runtime overhead.
2. Spot small, performance-critical helper functions called inside heavy loops and suggest `inline` specifiers (or rely on compiler heuristics where appropriate) to eliminate function-call stack frame overhead.
3. Ensure proper usage of `const` member functions and compile-time expressions to help the compiler optimize instruction paths.
4. Provide precise code snippets or diffs showing the applied changes.

Do not focus on Heap allocations or function parameter copying yet; keep your strict focus entirely on compile-time evaluation (`constexpr`) and function inlining.
PROMPT
)
                ;;
            "Stage 4: Compiler & CMake Optimization Flags")
                FINAL_PROMPT=$(cat <<'PROMPT'
Act as an expert Build and Performance Engineer specializing in modern CMake, GCC/Clang compilers, and High-Performance Computing (HPC) workflows. 

Please review the project's `CMakeLists.txt` and any related build configuration files, specifically focusing on release build modes, compiler optimization flags, and link-time optimizations.

Your tasks for this fourth stage are:
1. Review the existing compiler flags and ensure there is a clean distinction between `Debug` and `Release` build configurations.
2. Inject high-performance optimization flags for the `Release` profile targeting GCC/Clang (e.g., `-O3`, `-march=native` to leverage local CPU architecture instruction sets like AVX/SSE, and `-flto` for Link-Time Optimization).
3. Check and configure appropriate warning levels (e.g., `-Wall -Wextra`) to catch potential issues early without hurting execution speed.
4. Provide the updated `CMakeLists.txt` snippets or complete blocks with clear explanations for each flag added.

Do not focus on source code refactoring, heap management, or inline functions here; keep your strict focus entirely on CMake configuration, build types, and hardware-specific compiler optimization flags.
PROMPT
)
                ;;
            "Stage 5: Cache Locality & Data Layout Optimization")
                FINAL_PROMPT=$(cat <<'PROMPT'
Act as an expert C++ performance engineer specializing in High-Performance Computing (HPC), memory hierarchies, and Computational Fluid Dynamics (CFD). 

Please review the codebase, specifically focusing on multi-dimensional data structures (such as grids, matrices, or fields for velocity, pressure, etc.) and how nested loops traverse these arrays.

Your tasks for this fifth and final stage are:
1. Identify how multi-dimensional grids are represented (e.g., flattened 1D arrays vs nested `std::vector<std::vector<double>>`) and ensure continuous, contiguous memory allocation.
2. Verify memory access patterns (Row-Major vs Column-Major order) to ensure stride-1 sequential access, maximizing spatial locality and preventing CPU cache misses.
3. Restructure loop nests or array indexing formulas where necessary so that inner loops access contiguous memory cells in cache lines.
4. Provide concrete code snippets or refactored array-access implementations highlighting the performance gains.

Do not focus on basic parameter passing or CMake flags here; keep your strict focus entirely on cache locality, data layout, and memory access patterns.
PROMPT
)
                ;;
            *)
                exit 1
                ;;
        esac
        ;;
    *"The 3-Stage C++ Performance Pipeline For Class"*)
        CLASS_STAGES=(
            "Stage 1: Memory Encapsulation & Rule of Five"
            "Stage 2: Accessor APIs, Const-Overloading & Inlining"
            "Stage 3: Template Architecture & Zero-Virtual Overhead"
        )

        CHOSEN_STAGE=$(
            printf '%s\n' "${CLASS_STAGES[@]}" |
                rofi -dmenu -i -no-custom -p "Class Pipeline Stage for target:" -matching fuzzy
        )

        [[ -n "$CHOSEN_STAGE" ]] || exit 0

        case "$CHOSEN_STAGE" in
            "Stage 1: Memory Encapsulation & Rule of Five")
                FINAL_PROMPT=$(cat <<'PROMPT'
Act as an expert C++ systems engineer specializing in high-performance computing (HPC) and Computational Fluid Dynamics (CFD).

Please inspect the provided C++ class implementation (header and source files) with a strict focus on memory layout and resource management:

1. Verify that numerical data buffers (e.g., matrix entries, grid coordinates, field arrays) are stored in continuous, contiguous memory (prefer contiguous structures like flattened std::vector or raw managed buffers over fragmented pointer-to-pointer or jagged array designs).
2. Audit compliance with the Rule of Zero / Rule of Five: if the class directly manages raw dynamic resources, ensure explicit, non-throwing move operations (move constructor and move assignment operator marked noexcept) are correctly implemented.
3. Guard against accidental deep copies: determine whether copy constructors and copy assignment operators should be marked `= delete` or carefully controlled to prevent catastrophic performance hits in computational pipelines.
4. Show refactored code snippets demonstrating proper encapsulation, contiguous buffer usage, and efficient move semantics.

Do not focus on indexing methods, templates, or external compiler flags in this step. Focus purely on internal memory organization and class lifecycle mechanics.
PROMPT
)
                ;;
            "Stage 2: Accessor APIs, Const-Overloading & Inlining")
                FINAL_PROMPT=$(cat <<'PROMPT'
Act as an expert C++ performance engineer specializing in low-overhead API design for scientific computing.

Review the member functions and indexing operators of this C++ class:

1. Audit accessor operators (e.g., operator[], operator(), value accessors) to ensure proper const/non-const overloading (`T&` for mutable access and `const T&` for read-only access) without redundant copies.
2. Ensure lightweight, performance-critical accessors and index calculation helpers are defined inline (or within the class definition) so the compiler can aggressively inline them and optimize address arithmetic.
3. Check and apply the `noexcept` specifier to all non-throwing accessors and arithmetic helper methods to assist compiler optimization and code generation.
4. Ensure member functions that do not alter the object's internal state are strictly marked `const`.

Provide concrete before-and-after code comparisons for accessors and indexing interfaces. Do not focus on memory allocation architecture or template organization here.
PROMPT
)
                ;;
            "Stage 3: Template Architecture & Zero-Virtual Overhead")
                FINAL_PROMPT=$(cat <<'PROMPT'
Act as a modern C++ software architect specializing in generic programming and CFD framework design.

Review the compilation structure, template design, and abstraction patterns of this C++ class:

1. Eliminate runtime polymorphism (virtual functions and vtables) from tight computational loops and inner mesh/field data classes. If polymorphism is required, recommend zero-overhead static polymorphism alternatives (such as CRTP).
2. Audit template structure: verify that templated class definitions and their member implementations are correctly placed in header files (`.h`/`.hpp` or dedicated `-impl.hpp` files) to prevent linker errors (`undefined reference`) and satisfy ODR.
3. Clean up header dependencies: use forward declarations where possible, remove unused `#include` directives from headers, and push non-templated implementation details into `.cpp` files to reduce compilation bloat.
4. Provide the refactored header/source structure ensuring clean separation, zero virtual dispatch overhead, and safe template instantiation.

Limit your review specifically to template separation, header hygiene, and the elimination of runtime virtual overhead.
PROMPT
)
                ;;
            *)
                exit 1
                ;;
        esac
        ;;
    *"The 3-Stage C++ Performance Pipeline For Function"*)
        FUNCTION_STAGES=(
            "Stage 1: Inlining & Compile-Time Evaluation"
            "Stage 2: Parameter Passing & Const-Correctness"
            "Stage 3: Header Hygiene & ODR Enforcement"
        )

        CHOSEN_STAGE=$(
            printf '%s\n' "${FUNCTION_STAGES[@]}" |
                rofi -dmenu -i -no-custom -p "Function Pipeline Stage for target:" -matching fuzzy
        )

        [[ -n "$CHOSEN_STAGE" ]] || exit 0

        case "$CHOSEN_STAGE" in
            "Stage 1: Inlining & Compile-Time Evaluation")
                FINAL_PROMPT=$(cat <<'PROMPT'
Act as an expert C++ performance engineer specializing in high-performance computing (HPC) and zero-overhead mathematical algorithms.

Please inspect the provided standalone functions or standalone module files with a strict focus on eliminating function call overhead and leveraging compile-time evaluation:

1. Identify small, performance-critical math or utility functions (e.g., interpolation helpers, distance formulas, grid metric evaluations) and ensure they are marked with the `inline` specifier to allow the compiler to substitute their bodies directly at call sites.
2. Verify if input parameters or constant factors are known at compile-time (e.g., fixed grid dimensions, physical constants, static configuration coefficients) and refactor those functions to use `constexpr` so computations are fully resolved during compilation and completely bypassed at runtime.
3. Show refactored code snippets demonstrating proper use of `inline` and `constexpr` to optimize code generation for the CPU pipeline.

Do not focus on parameter passing by reference, exception handling specs, or header-include hygiene in this step. Focus purely on inlining and compile-time evaluation.
PROMPT
)
                ;;
            "Stage 2: Parameter Passing & Const-Correctness")
                FINAL_PROMPT=$(cat <<'PROMPT'
Act as an expert C++ software engineer specializing in low-level memory efficiency and robust API design for scientific computing.

Review the function signatures and parameter passing mechanics in this C++ module:

1. Audit parameter types: ensure large data structures, fields, arrays, or custom objects are never passed by-value, enforcing pass-by-reference-to-const (`const T&`) to prevent heavy, redundant memory copying.
2. Apply the `noexcept` specifier to all non-throwing mathematical and low-level computational functions, allowing the compiler to generate optimized assembly code without exception-handling overhead.
3. Ensure strict `const`-correctness across all input arguments and helper functions to maintain safe, predictable state management.
4. Provide concrete before-and-after code comparisons for function signatures demonstrating efficient memory handling and optimized specifiers.

Do not focus on inlining thresholds, compile-time evaluation, or header-include dependencies here. Focus exclusively on parameter passing and safety specifiers.
PROMPT
)
                ;;
            "Stage 3: Header Hygiene & ODR Enforcement")
                FINAL_PROMPT=$(cat <<'PROMPT'
Act as an expert C++ systems architect specializing in compilation speed, linkage mechanics, and header-only library design.

Review the structure, inclusion guards, and linkage of standalone functions implemented within header files (`.h` or `.hpp`):

1. Enforce the One Definition Rule (ODR): ensure all standalone functions defined directly inside header files are explicitly marked `inline` (or `static` where appropriate) to prevent multiple-definition linker errors when included across multiple translation units.
2. Audit header file hygiene: clean up unused or redundant `#include` directives, prevent circular dependencies, and use forward declarations wherever possible to reduce compilation bloat and speed up build times.
3. Provide the refactored header structure guaranteeing linker safety, clean dependencies, and optimal compilation performance.

Limit your review strictly to header hygiene, ODR enforcement for header-defined functions, and compilation dependency management.
PROMPT
)
                ;;
            *)
                exit 1
                ;;
        esac
        ;;
    *"None"*)
        FINAL_PROMPT="$TARGET_DESC"
        ;;
    *)
        exit 1
        ;;
esac

if ((SELECTED_COUNT > 1)) && [[ "$CHOSEN_ACTION" == *"Performance Pipeline"* ]]; then
    FINAL_PROMPT+=$'\n\n'"Selected files: $TARGET_DESC."
fi

# Copy the prompt to the clipboard and paste it into the original window.
copy_and_paste_prompt "$FINAL_PROMPT" || exit 1
