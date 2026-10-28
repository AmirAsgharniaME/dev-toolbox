# Repository Guidelines

## Project Structure & Module Organization

This repository contains standalone Linux desktop utilities. `prompt_picker/prompt_picker.sh` is the Rofi picker, with setup and usage notes in `prompt_picker/README.md`. `prompt_helper/prompt_helper.sh` opens a Zenity prompt and uses `prompt_helper/refine_prompt.py` to refine it through the GapGPT API. `translator/run_translator.sh` launches `translator/translator.py`, which polishes selected or piped text through the GapGPT API. The root `README.md` gives the project overview; `LICENSE` contains licensing terms. The root `FILEPATH.md` is the pipe-separated project inventory (`TYPE | LABEL | PATH`), used to populate file menus and prompts. Keep it synchronized with project files as described below. There is no separate asset or test tree at present.

## Build, Test, and Development Commands

There is no build system or automated test suite currently configured. Run the utility from its directory with:

```bash
cd prompt_picker
bash prompt_picker.sh
```

For direct execution, use `chmod +x prompt_picker.sh` once, then `./prompt_picker.sh`. It needs Bash 4+, Rofi, and (for full window and clipboard behavior) `xdotool`, `xprop`, and either `xclip` or `xsel`. `notify-send` is optional. To check Bash syntax after editing, run `bash -n prompt_picker/prompt_picker.sh`.

Run the prompt helper with `bash prompt_helper/prompt_helper.sh`. It needs Zenity, Python 3 with the `requests` package, `xclip`, and `xdotool`. The refiner reads `GAPGPT_API_KEY` first; if it is unset or empty, it reads the key from `prompt_helper/.gapgpt_key`. Keep that local key file private and out of version control. Check its Bash syntax with `bash -n prompt_helper/prompt_helper.sh`.

Run the translator with `bash translator/run_translator.sh`. The launcher reads text from the X11 clipboard and passes it to the Python script, which sends the polished result to standard output, copies it to the clipboard, and shows desktop notifications. The launcher needs Python 3, `xclip`, and `notify-send`; the Python script needs `requests` and `xclip` for its primary-selection fallback and clipboard output. Piped text and a command-line argument are also supported when running `translator/translator.py` directly. The script reads `GAPGPT_API_KEY` first, then `translator/.api_translator`; keep that local key file private and out of version control. Check its launcher syntax with `bash -n translator/run_translator.sh`.

## Coding Style & Naming Conventions

Keep shell code compatible with Bash 4+, use four spaces for indentation, quote expansions, and prefer small functions with descriptive `snake_case` names. Keep Python code compatible with the Python 3 version available on supported Linux desktops. Preserve existing checks and fallback behavior for desktop utilities where present.

## Keeping README Files Current

For every project change, review the root `README.md` and the README for each utility touched by the change. Keep documentation accurate in the same change as the code or project structure it describes: update affected overviews, behavior, setup, dependencies, configuration, run instructions, and workflows, and remove or revise instructions that are no longer accurate. When a README changes, check related links and examples against the current files and commands.

## Keeping `FILEPATH.md` Synchronized

Check and update the root `FILEPATH.md` in the same change whenever a project file is added, deleted, renamed, moved, or changes file type. Add one entry for each new or changed project file using `TYPE | LABEL | PATH`; remove stale entries for deleted or old paths, and replace them with the current entry. Keep paths exact and relative to the repository root. Choose the type from the inventory’s `# TYPES` list (for example, `MD` for Markdown and `SH` for shell scripts); when an extension or role changes, update the type too. If a file needs a type not yet listed, add an appropriate type to `# TYPES` and document the convention here. Use the inventory’s mechanical filename-to-title label rule, retain its section headers, and place entries under the matching section. Before finishing, compare the inventory against the project files so no changed path remains stale. Include `AGENTS.md` in the inventory.

## Testing Guidelines

No test framework or coverage requirement is defined. For script changes, at minimum run the syntax check above. When changing interactive behavior, manually exercise the relevant Rofi flow in a Linux X11 session with the required tools installed; do not treat that manual check as an automated test.

## Commit & Pull Request Guidelines

Git history currently contains only the initial commit, so no commit-message convention is established. Use a short imperative summary (for example, `Improve clipboard fallback`). Pull requests should explain the user-visible change, list manual or automated checks performed, and include screenshots for visible menu changes when useful. Link related issues when applicable.

## Keeping This Guide Current

For every project change, check this `AGENTS.md` and `FILEPATH.md` as part of the same work. Update this guide whenever the change adds or alters project structure, build or test commands, dependencies, coding conventions, or contribution workflows. Update `FILEPATH.md` for every project file addition, deletion, rename, move, or type change, following the rules above. Keep both accurate for the repository after the change; do not finish a change while either file contains stale guidance or paths.
