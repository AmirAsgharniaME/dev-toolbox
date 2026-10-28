# dev-toolbox

Small desktop utilities for building coding prompts and working with project files on a Linux desktop. The repository includes a Rofi based project and Git prompt picker, a Zenity dialog that refines prompts through the GapGPT API, and a text translator and polisher for Linux desktop workflows.

## Tools

### Prompt Picker

[`prompt_picker/prompt_picker.sh`](prompt_picker/prompt_picker.sh) reads a project's `FILEPATH.md` inventory and offers file-specific coding prompts, project prompts, and Git workflow prompts. It prints generated prompts and copies them to the clipboard; when the desktop tools are available, it can also return to the previously focused window and paste the prompt.

See [`prompt_picker/README.md`](prompt_picker/README.md) for setup, requirements, and usage details.

### Prompt Helper

[`prompt_helper/prompt_helper.sh`](prompt_helper/prompt_helper.sh) opens an editable Zenity dialog, sends the text to [`prompt_helper/refine_prompt.py`](prompt_helper/refine_prompt.py) for refinement through GapGPT, then copies the result and attempts to paste it into the window that was active before the dialog opened.

The refiner reads `GAPGPT_API_KEY` from the environment, or falls back to `prompt_helper/.gapgpt_key`. Keep that local key file private and do not commit it. See [`prompt_helper/README.md`](prompt_helper/README.md) for requirements and usage details.

### Translator

[`translator/run_translator.sh`](translator/run_translator.sh) launches [`translator/translator.py`](translator/translator.py). With text selected in an X11 application, it translates Persian or mixed text into polished academic English, or improves English text, then replaces the selection. It also accepts piped text and writes the result to standard output.

The translator needs Python 3, `requests`, `xclip`, `xdotool`, and `notify-send`. It reads `GAPGPT_API_KEY` from the environment or falls back to `translator/.api_translator`; keep that local key file private and do not commit it. See [`translator/README.md`](translator/README.md) for setup and usage details.

## Requirements

- Bash 4 or later
- Linux desktop session with X11 utilities
- Rofi and `xdotool` for the full Prompt Picker flow
- Zenity, Python 3, `requests`, `xclip`, and `xdotool` for Prompt Helper
- A GapGPT API key to refine prompts with Prompt Helper
- Python 3, `requests`, `xclip`, `xdotool`, `notify-send`, and a GapGPT API key for Translator

The Prompt Picker also supports `xsel` as a clipboard alternative. `xprop` and `notify-send` are optional; details and graceful fallback behavior are documented in its README.

## Run

Run a utility with Bash from the repository root:

```bash
bash prompt_picker/prompt_picker.sh
bash prompt_helper/prompt_helper.sh
bash translator/run_translator.sh
```

Alternatively, make a script executable with `chmod +x` and run it directly. The Prompt Helper currently invokes its Python script using the repository's absolute path, so it expects this project at `/home/amir/Documents/dev-toolbox` unless that script is adjusted.

## Project file inventory

The root [`FILEPATH.md`](FILEPATH.md) lists project files as `TYPE | LABEL | PATH`. The Prompt Picker uses this inventory to populate its file selection menu and generated prompts. Keep paths relative to the repository root and update the inventory when project files are added, removed, renamed, moved, or change type. Its embedded comments describe the supported types and label format.

## Development

There is no build system or automated test suite. After changing a shell script, check its syntax with:

```bash
bash -n prompt_picker/prompt_picker.sh
bash -n prompt_helper/prompt_helper.sh
```

See [`AGENTS.md`](AGENTS.md) for repository structure, style, inventory, and contribution guidance.
