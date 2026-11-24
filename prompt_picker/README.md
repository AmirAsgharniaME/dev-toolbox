# Prompt Picker

`prompt_picker.sh` is a Bash utility with a GTK 3 window that builds AI prompts from a project's file list, copies the result to the clipboard, and can paste it into the window that was active when the script started. It also provides project maintenance and Git prompt menus.

## Requirements

- Bash 4 or later
- Python 3 with PyGObject and GTK 3 (on Debian/Ubuntu: `python3-gi` and `gir1.2-gtk-3.0`)
- `xdotool` for detecting and restoring the previously active window and sending the paste shortcut
- One clipboard utility: `xclip` (preferred) or `xsel`
- `xprop` to identify the active window's application for paste shortcut selection; if unavailable, the script tries `xdotool getwindowclassname`
- `notify-send` for error notifications; notifications are optional

The script is intended for a Linux desktop session with X11 tools available. If `xdotool` cannot identify the active window, it can still show menus and copy prompts, but automatic paste is unavailable.

## Setup and launch

From this directory, make the script executable and launch it:

```bash
chmod +x prompt_picker.sh
./prompt_picker.sh
```

You can also run it with `bash prompt_picker.sh`. A desktop shortcut can launch the same script; the existing Cinnamon Super+F binding needs no change. If multiple inventories are found, choose the project in the picker before continuing.

## Project file list

The picker checks its launch directory, the working directory of the active X11 window's process and every accessible descendant, and the directory containing the script. GNOME Terminal normally uses a shared server, so this can include projects from multiple open terminal sessions. It cannot determine which of those sessions is focused, and sessions outside the active window's process tree may not be discovered. Process working directories must be accessible and contain the inventory directly; parent directories are not searched.

In each directory, `FILEPATH.md` takes precedence over the legacy names `file_path.md`, `file_path`, and `file_path.txt`. Resolved paths are deduplicated. When multiple inventories are found, the picker shows the parent directory name and full inventory path; select one to use throughout that invocation. One inventory is selected automatically. Canceling the selection exits without generating a prompt. When none is found, the existing no-file menu offers Git and project prompts.

The file list uses pipe separated records:

```text
TYPE | LABEL | PATH
```

For example:

```text
MD | Readme | README.md
SH | Prompt Picker | prompt_picker/prompt_picker.sh
```

Blank lines and lines beginning with `#`, `-`, or `=` are ignored. Entries with three non-empty fields become selectable files. A line with just one field is treated as a raw menu entry. Paths are used in the generated prompt as written; keep them accurate relative to the project.

Choose **Create/update project file list** from the main menu to copy a prompt for updating the project's root `FILEPATH.md` inventory. If no file list is found, the script still offers Git prompts and main project prompts, including the file list update prompt.

## Using the picker

The picker uses one decorated, movable window. Drag its title bar to move it, minimize it with the title-bar button, and restore it from the Cinnamon panel. Clicking outside leaves it open. Use the visible X, **Cancel**, or Escape to close the workflow without generating a prompt.

Use Up and Down to change the highlighted item and type to filter. In a multi-file group, press Enter or double-click (or click **Toggle file**) to toggle the highlighted file. Checked files show `✓`; the count and a compact filename list remain visible while filtering. Click **Done** to commit the group. Plain Enter never commits a multi-file group. Left and **Back** return one stage; Right and **Forward** advance ordinary single-choice stages. Earlier choices are restored where possible, and changing an earlier choice clears dependent later stages. To move the filter cursor, use Ctrl+B and Ctrl+F, Home and End, or the mouse; plain Left and Right navigate stages. An explicit **Generate prompt** confirmation shows the selected-file summary and is required before the picker copies or pastes a prompt; press Enter or click **Generate prompt**.

The selected-files panel sits beside the file list, updates immediately when a row is toggled, and remains scoped to the current group. Each multi-file stage opens with the file list focused and its first visible row highlighted. Enter toggles only when the file list has focus; Enter in the filter field does nothing to the selection. On the last visible (including filtered) file row, press the keyboard Right Arrow to focus the visible **Done** control, then press Enter to commit; Right on another row does not advance. Left from Done returns to the file list without changing selections. Use Tab or Shift+Tab to reach **Done** as an alternative. Ctrl+Enter also commits when the file list has focus; it does not commit while editing the filter.

The initial **Select File or Action** menu keeps Git Prompts and Main Project Prompts alongside the root inventory. Inventory rows use the shared multi-file controls: toggle rows to show checkmarks and update the selected-files panel, then move to the last selected row, press Right to reveal and focus **Done**, and press Enter to commit. That Enter completes the direct root selection: the picker prints, copies, and pastes a sentence describing all selected entries joined by `And`, without opening another menu. Git and Main Project Prompts remain single-choice actions in that menu. Each inventory entry includes its label and path; raw entries are included as written. For example: ``Selected files: Prompt Picker file in the path: `prompt_picker/prompt_picker.sh`.`` Actions inside Main Project Prompts continue to generate prompts for selected files. Available actions include:

- Choose **None (Just Paste File Path)** to print, copy, and paste the same description for the current selection
- Open the Git prompts menu
- Open the main project prompts menu, including the AGENTS.md and file list prompts, the priority-3 Create STATE.md prompt, AGENT_REPORT.md and TASK_PLAN.md prompts, Exec-Task, the Update STATE.md prompt, Create and Update Theory Guide Sections, Fix Markdown, Scientific Copy Editor, Fix Compiler / Syntax Issues, Fix Logic / CFD Implementation, Refactor, Rewrite from Scratch, Sync / Adapt with another file, Backup File, Restore File From Backup, and all three staged C++ performance prompt pipelines

The **15. ApexFVM: The 5-Stage C++ Performance Pipeline for Project**, **16. The 3-Stage C++ Performance Pipeline for Class**, and **17. The 3-Stage C++ Performance Pipeline for Function** options are in **Main Project Prompts**. Each asks you to select one or more target files, then choose a pipeline stage.

The priority-3 **Create STATE.md** option generates a prompt to rewrite `STATE.md` as a fact-based, project-specific status reference, with a stable section structure, open questions for unverifiable details, and a dated change log.
The **Create AGENT_REPORT.md** option generates a prompt for a fresh architectural report using a fixed five-section structure, without modifying C++ source files.
The **Create TASK_PLAN.md** option generates a prompt to overwrite `TASK_PLAN.md` with a self-contained, atomic execution checklist derived from `AGENT_REPORT.md`, without modifying C++ source files.
The **Exec-Task** option generates a prompt to execute only the first unchecked step in `TASK_PLAN.md`, verify it using that step's command, and update the checklist and execution log.
The final **Update STATE.md** option generates a prompt to update `STATE.md` incrementally from the last change-log entry, using Git history and repository evidence while preserving the existing section structure.
The **Create Theory Guide Sections** option generates a prompt to parse the project's root `Theory_Guide.md` and create or incrementally update `Theory_Guide_Sections.md` with a structured table of H1–H4 headings, anchors, status, dates, and concise CFD scope summaries.
The **Update Theory Guide Sections** option generates a prompt to back up `Theory_Guide_Sections.md`, inspect Git changes to `Theory_Guide.md`, and apply targeted table updates while preserving unchanged rows and prior timestamps.
The **Fix Markdown**, **Scientific Copy Editor**, **Fix Compiler / Syntax Issues**, **Fix Logic / CFD Implementation**, **Refactor**, **Rewrite from Scratch**, **Backup File**, and **Restore File From Backup** options each show one multi-file group. Choose one or more files and click **Done** to generate the prompt with their paths separated by `And`. **Sync / Adapt with another file** has two separate groups: target files, then source files. The picker shows the group name and its position, keeps each group's selections separate, and summarizes both groups before final confirmation. Existing prompt definitions do not encode count constraints, so these groups default to at least one file and no maximum. If no file list is available, the existing manual path entry flow remains. Canceling a group produces no prompt.
The **Fix Markdown** prompt applies the formatting rules in `Markdown_Rules.md` to each selected file and inserts the selected paths into `TARGET_FILE`. The **Scientific Copy Editor** prompt directs technical and scientific writing edits under `Markdown_Rules.md`, requests a backup before editing, and flags unsupported claims and inconsistencies while preserving math and document structure.
The **Backup File** prompt creates an exact `.bak` copy beside each selected target, overwriting an existing backup with that name and leaving the target and all other files unchanged.
The **Restore File From Backup** prompt replaces each selected target with an exact copy of its same-directory `.bak` file, without modifying or deleting the backup, and requests confirmation of each restored path.

The Git menu can create commit, push, branch, and file operation prompts. It generates prompt text; it does not execute Git commands itself. File remove, rename, and move actions collect paths and generate a prompt for an AI assistant.

## Tests

Run `python3 -m unittest discover -s tests` from the repository root for the non-GUI tests. To also run the X11 integration tests on a Cinnamon desktop, use `PICKER_GUI_TESTS=1 python3 -m unittest discover -s tests`. The GUI tests open and focus picker windows and send keyboard events; they also require `xdotool` and, for the close test, `wmctrl`.

## Clipboard and paste behavior

The generated prompt is printed to standard output and copied to the clipboard. The script captures the active window before opening its window, then attempts to reactivate it and paste the prompt. It uses `Ctrl+V` for common editors and browsers, and `Shift+Insert` for terminals and other applications by default.

Set `PROMPT_PICKER_PASTE_KEY` to override the paste shortcut for the active window, for example:

```bash
PROMPT_PICKER_PASTE_KEY=ctrl+v ./prompt_picker.sh
```

Automatic paste is skipped if the required clipboard selection is unavailable. In that case, the prompt remains printed and copied when clipboard access succeeded, so it can be pasted manually.
