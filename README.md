# dev-toolbox

A small collection of Linux desktop helpers for building coding prompts and polishing text. The tools work from Bash or Python and connect to the desktop through X11 utilities.

## Utilities

| Utility | What it does | Start here |
| --- | --- | --- |
| **Prompt Picker** | Uses a project's `FILEPATH.md` to build file-specific coding prompts, plus project maintenance and Git prompts. Copies the prompt to the clipboard and can paste it into the previously active window. | [`prompt_picker/README.md`](prompt_picker/README.md) |
| **Prompt Helper** | Opens an editable dialog, refines the text through the GapGPT API, then copies and pastes the result. | [`prompt_helper/README.md`](prompt_helper/README.md) |
| **Translator** | Translates Persian or mixed text into polished academic English, or improves English text. The launcher reads clipboard text; the Python script also accepts an argument, piped input, or the X11 primary selection. | [`translator/README.md`](translator/README.md) |

## Start a utility

Run commands from the repository root:

```bash
bash prompt_picker/prompt_picker.sh
bash prompt_helper/prompt_helper.sh
bash translator/run_translator.sh
```

The desktop flows are designed for Linux with an X11 session. See each utility's README for its required packages, clipboard and paste behavior, and setup details.

## Setup notes

- **Prompt Picker** needs Bash 4+, Rofi, and a clipboard tool (`xclip` or `xsel`). `xdotool` enables active-window detection and automatic paste. `xprop` and `notify-send` are optional.
- **Prompt Helper** needs Zenity, Python 3 with `requests`, `xclip`, and `xdotool`. Set `GAPGPT_API_KEY` or save the key in `prompt_helper/.gapgpt_key`.
- **Translator** needs Python 3 with `requests`, `xclip`, and `notify-send` for the launcher flow. Set `GAPGPT_API_KEY` or save the key in `translator/.api_translator`.

Keep API key files private and out of version control. Both Prompt Helper and Translator currently refer to Python scripts through absolute paths under `/home/amir/Documents/dev-toolbox`; update those paths if the repository is installed elsewhere.

## Project inventory

[`FILEPATH.md`](FILEPATH.md) is the pipe-separated `TYPE | LABEL | PATH` inventory used by Prompt Picker to find project files and populate its file menu. Keep its paths accurate and update it whenever project files are added, removed, moved, renamed, or change type.

## Repository layout

```text
prompt_picker/   Rofi prompt picker and its guide
prompt_helper/   Zenity prompt refiner and its guide
translator/      Text translator and its guide
FILEPATH.md      Project file inventory
AGENTS.md        Repository instructions
```

There is no build system or automated test suite. For repository guidance and Bash syntax-check commands, see [`AGENTS.md`](AGENTS.md).
