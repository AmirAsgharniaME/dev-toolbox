# dev-toolbox

A small collection of Linux desktop helpers for building coding prompts and polishing text. The tools work from Bash or Python and connect to the desktop through X11 utilities.

## Utilities

| Utility | What it does | Start here |
| --- | --- | --- |
| **Prompt Picker** | Uses a project's `FILEPATH.md` to build file-specific coding prompts, backup and restore prompts, project maintenance and Git prompts, and prompts targeted at headings indexed in `Theory_Guide_Sections.md`. Its **Prompts** menu groups actions by document, Markdown, C++, CFD, file operations, and theory guide sections. Copies the prompt to the clipboard and can paste it into the previously active window. | [`prompt_picker/README.md`](prompt_picker/README.md) |
| **Prompt Helper** | Opens an editable dialog, refines the text through the GapGPT API, then copies and pastes the result. | [`prompt_helper/README.md`](prompt_helper/README.md) |
| **Translator** | Translates Persian or mixed text into polished academic English, or improves English text. The launcher reads clipboard text; the Python script also accepts an argument, piped input, or the X11 primary selection. | [`translator/README.md`](translator/README.md) |

## Start a utility

Run commands from the repository root:

```bash
bash prompt_picker/prompt_picker.sh
bash prompt_helper/prompt_helper.sh
bash translator/run_translator.sh
```

Prompt Picker discovers inventories in its launch directory and the active window’s process tree. When it finds multiple inventories, choose one in a window that can be minimized and restored; see its guide for controls, discovery limits, and shortcut details.

The picker’s initial menu offers the inventory entries, **Git Prompts**, and **Prompts**. The Prompts menu starts with **AGENTS.md**, **FILEPATH.md**, and **STATE.md** submenus, followed by report and task-plan prompts and grouped Markdown, C++, CFD, file-operation, and theory-guide actions. Canceling a submenu returns to **Prompts** without generating a prompt. File-targeted actions let you select multiple paths; theory-guide sections are offered when both the guide and its section index are available. Before copying or pasting, the **Prompt action** menu lets you generate the prompt or choose **Modify Prompt** to edit it in a large multiline dialog. The modified text is sent as an instruction to replace only the selected prompt template in `prompt_picker.sh` while preserving the other templates and picker behavior.

The desktop flows are designed for Linux with an X11 session. See each utility's README for its required packages, clipboard and paste behavior, and setup details.

## Setup notes

- **Prompt Picker** needs Bash 4+, Python 3 with PyGObject and GTK 3, and a clipboard tool (`xclip` or `xsel`). `xdotool` enables active-window detection and automatic paste. `xprop` and `notify-send` are optional.
- **Prompt Helper** needs Zenity, Python 3 with `requests`, `xclip`, and `xdotool`. Set `GAPGPT_API_KEY` or save the key in `prompt_helper/.gapgpt_key`.
- **Translator** needs Python 3 with `requests`, `xclip`, and `notify-send` for the launcher flow. Set `GAPGPT_API_KEY` or save the key in `translator/.api_translator`.

Keep API key files private and out of version control. Both Prompt Helper and Translator currently refer to Python scripts through absolute paths under `/home/amir/Documents/dev-toolbox`; update those paths if the repository is installed elsewhere.

## Project inventory

[`FILEPATH.md`](FILEPATH.md) is the pipe-separated `TYPE | LABEL | PATH` inventory used by Prompt Picker to find project files and populate its file menu. Keep its paths accurate and update it whenever project files are added, removed, moved, renamed, or change type.

## Repository layout

```text
prompt_picker/   GTK prompt picker and its guide
prompt_helper/   Zenity prompt refiner and its guide
translator/      Text translator and its guide
tests/           Focused picker tests
FILEPATH.md      Project file inventory
AGENTS.md        Repository instructions
STATE.md         Current repository status
```

There is no build system. Run the focused picker tests with `python3 -m unittest discover -s tests`; for repository guidance and Bash syntax-check commands, see [`AGENTS.md`](AGENTS.md).
