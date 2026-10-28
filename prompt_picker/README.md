# Prompt Picker

`prompt_picker.sh` is a Rofi based Bash utility that builds AI prompts from a project's file list, copies the result to the clipboard, and can paste it into the window that was active when the script started. It also provides project maintenance and Git prompt menus.

## Requirements

- Bash 4 or later
- Rofi
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

You can also run it with `bash prompt_picker.sh`. For convenient access, bind the script to a desktop keyboard shortcut or launch it from a terminal while the target project is open.

## Project file list

The picker reads `file_path.md` first. For backward compatibility, it also accepts the legacy names `file_path` and `file_path.txt` when the Markdown inventory is absent. It looks in these locations, in order:

1. The directory containing `prompt_picker.sh`
2. The current working directory
3. The active window's process and its child processes, checking their working directories

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

Choose **Create/update project file list** from the main menu to copy a prompt for updating the project's root `file_path.md` inventory. If no file list is found, the script still offers Git prompts and main project prompts, including the file list update prompt.

## Using the picker

Select a file from the Rofi menu. Then choose an action, or choose **Add File Path** to select additional target files before choosing an action. Available actions include:

- Paste the selected file path
- Fix compiler or syntax issues
- Fix logic or CFD implementation
- Refactor or rewrite the selected code
- Sync selected files with one or more dependency files
- Run one of the staged C++ performance prompt pipelines for a project, class, or function
- Open the Git prompts menu
- Open the main project prompts menu, including the AGENTS.md and file list prompts

The Git menu can create commit, push, branch, and file operation prompts. It generates prompt text; it does not execute Git commands itself. File remove, rename, and move actions collect paths and generate a prompt for an AI assistant.

## Clipboard and paste behavior

The generated prompt is printed to standard output and copied to the clipboard. The script captures the active window before opening Rofi, then attempts to reactivate it and paste the prompt. It uses `Ctrl+V` for common editors and browsers, and `Shift+Insert` for terminals and other applications by default.

Set `PROMPT_PICKER_PASTE_KEY` to override the paste shortcut for the active window, for example:

```bash
PROMPT_PICKER_PASTE_KEY=ctrl+v ./prompt_picker.sh
```

Automatic paste is skipped if the required clipboard selection is unavailable. In that case, the prompt remains printed and copied when clipboard access succeeded, so it can be pasted manually.
