# Repository Guidelines

## Project Structure & Module Organization

This repository contains standalone Linux desktop utilities. `prompt_picker/prompt_picker.sh` discovers inventories and generates prompts; `prompt_picker/picker_ui.py` provides its GTK window, with setup and usage notes in `prompt_picker/README.md`. Its **Prompts** menu starts with **AGENTS.md**, which opens a submenu containing **Update**; **FILEPATH.md**, which opens **Create/Update**; and **STATE.md**, which opens **Create/Update**. The menu also groups report and task-plan actions, Markdown editing, C++ maintenance and performance prompts, CFD implementation and performance prompts, file operations, and theory-guide section actions. Canceling any submenu returns to **Prompts** without generating a prompt. File-targeted actions collect one or more paths until Done is selected; Sync collects target and source paths separately. **Backup File** emits one exact `.bak` copy instruction for each selected path. The `STATE.md` submenu's Create prompt asks for a repository-grounded status reference with a stable section structure, open questions for unverifiable details, and a dated change log. Its Update prompt uses the last change-log entry as an anchor, preserves the established sections, and records verified changes. `STATE.md` is the repository's current status reference and describes the utilities, constraints, workflow rules, and open documentation questions. The picker also contains C++/CFD-oriented prompt templates, but this repository does not contain the CFD library those prompts may target: there is no `CMakeLists.txt`, `include/`, `src/`, `examples/`, or C++ source tree here. `prompt_helper/prompt_helper.sh` opens a Zenity prompt and uses `prompt_helper/refine_prompt.py` to refine it through the GapGPT API. `translator/run_translator.sh` reads clipboard text and launches `translator/translator.py`; the Python script also accepts an argument, piped input, or an X11 primary selection. The root `README.md` gives the project overview; `LICENSE` contains licensing terms. The root `FILEPATH.md` is the pipe-separated project inventory (`TYPE | LABEL | PATH`), used to populate file menus and prompts. Keep it synchronized with project files as described below. `tests/` contains focused picker tests; there is no separate asset tree.

## Project Root Discovery Invariant

The primary project-selection menu MUST discover and list project roots exclusively by the presence and location of `FILEPATH.md`: a directory qualifies as a selectable project root if and only if it contains `FILEPATH.md`. Never use `Theory_Guide_Sections.md` or any other file to discover project roots. `Theory_Guide_Sections.md` is a secondary, context-dependent target within an already-discovered project root and may be offered only during prompt target selection. Preserve this invariant through refactoring, feature additions, and prompt updates.

## Theory Guide Sections Resolution Invariant

Resolve `Theory_Guide_Sections.md` only after a project root has been selected through `FILEPATH.md`, and only within that selected root. Never search for it globally, independently, or before project selection. When the selected root contains the index, conditionally offer **Theory Guide Sections** at the subsequent prompt target-selection stage, subject to the existing requirement that `Theory_Guide.md` also exists. When the index is absent, show no theory target options or errors and continue with the standard file-target workflow. Preserve this two-stage hierarchy through future changes.

The **Update Theory Guide Sections** prompt backs up `Theory_Guide_Sections.md`, reviews Git diffs for `Theory_Guide.md`, and directs targeted manifest changes while preserving rows and timestamps for unaffected sections.

The C++20 CFD architecture described by some prompt templates is an external target project, not a component of this repository. The current tree has no `CMakeLists.txt`, `include/`, `src/`, `examples/`, C++ headers, C++ sources, executable targets, or CFD build artifacts. Do not add C++ build commands, library module descriptions, or architecture claims to this guide unless those files are actually added here; if that happens, document the concrete target layout, required C++ standard, dependencies, build presets, and executable examples from the checked-in configuration.

The initial root menu keeps Git Prompts and **Prompts** beside the inventory. Selecting inventory rows uses the shared multi-file UI: checked rows, a live selected-files panel, and Right on the last selected row to reveal and focus **Done** before Enter commits. Enter on root **Done** prints, copies, and attempts to paste the selected entries' description, then finishes without another menu. Git and **Prompts** remain single-choice actions. **Prompts** begins with **AGENTS.md**, **FILEPATH.md**, and **STATE.md**. The AGENTS submenu contains **Update**; the FILEPATH submenu contains **Create/Update**; the STATE submenu contains **Create/Update**. Left Arrow or canceling any submenu returns to **Prompts** without selecting a prompt. Inventory entries include their labels and paths, multiple descriptions are joined by `And`, and raw entries are included as written. The file-targeted actions in **Prompts** use selected paths in their generated prompts. Their multi-file groups open with the file list focused and use the same checked rows and live side panel. Tab navigation reaches **Done**; Enter or Space activates it when focused, and Ctrl+Enter confirms when the file list has focus. Sync target and source groups remain separate through Back navigation and final confirmation.

When both theory-guide files exist beside the selected inventory, file-targeted **Prompts** actions offer a choice between inventory files and indexed theory-guide sections. Section selection includes the indexed headings and their current guide content in the generated prompt; sync still selects source files separately.

## Build, Test, and Development Commands

There is no build system in this repository; the C++/CFD build and architecture instructions in picker prompts apply to the project being prompted, not to `dev-toolbox`. Run the utility from its directory with:

```bash
cd prompt_picker
bash prompt_picker.sh
```

The picker collects inventories from its launch directory, the active window’s accessible process tree, and its script directory; it asks the user to choose when several are found. The GTK window supports stage navigation and can be minimized and restored. Sessions outside that process tree may not be discovered. For direct execution, use `chmod +x prompt_picker.sh` once, then `./prompt_picker.sh`. It needs Bash 4+, Python 3 with PyGObject and GTK 3. `xdotool`, `xprop`, and either `xclip` or `xsel` provide full window and clipboard behavior; `notify-send` is optional. To check Bash syntax after editing, run `bash -n prompt_picker/prompt_picker.sh`.

Run the prompt helper with `bash prompt_helper/prompt_helper.sh`. It needs Zenity, Python 3 with the `requests` package, `xclip`, and `xdotool`. The refiner reads `GAPGPT_API_KEY` first; if it is unset or empty, it reads the key from `prompt_helper/.gapgpt_key`. Keep that local key file private and out of version control. Check its Bash syntax with `bash -n prompt_helper/prompt_helper.sh`.

Run the translator with `bash translator/run_translator.sh`. The launcher reads text from the X11 clipboard and passes it to the Python script, which sends the polished result to standard output, copies it to the clipboard, and shows desktop notifications. The launcher needs Python 3, `xclip`, and `notify-send`; the Python script needs `requests` and `xclip` for its primary-selection fallback and clipboard output. Piped text and a command-line argument are also supported when running `translator/translator.py` directly. The script reads `GAPGPT_API_KEY` first, then `translator/.api_translator`; keep that local key file private and out of version control. Check its launcher syntax with `bash -n translator/run_translator.sh`.

## Coding Style & Naming Conventions

Keep shell code compatible with Bash 4+, use four spaces for indentation, quote expansions, and prefer small functions with descriptive `snake_case` names. Keep Python code compatible with the Python 3 version available on supported Linux desktops. Preserve existing checks and fallback behavior for desktop utilities where present.

## Keeping README Files Current

For every project change, review the root `README.md` and the README for each utility touched by the change. Keep documentation accurate in the same change as the code or project structure it describes: update affected overviews, behavior, setup, dependencies, configuration, run instructions, and workflows, and remove or revise instructions that are no longer accurate. When a README changes, check related links and examples against the current files and commands.

## Keeping `FILEPATH.md` Synchronized

Check and update the root `FILEPATH.md` in the same change whenever a project file is added, deleted, renamed, moved, or changes file type. Add one entry for each new or changed project file using `TYPE | LABEL | PATH`; remove stale entries for deleted or old paths, and replace them with the current entry. Keep paths exact and relative to the repository root. Choose the type from the inventory’s `# TYPES` list (for example, `MD` for Markdown and `SH` for shell scripts); when an extension or role changes, update the type too. If a file needs a type not yet listed, add an appropriate type to `# TYPES` and document the convention here. Use the inventory’s mechanical filename-to-title label rule, retain its section headers, and place entries under the matching section. Before finishing, compare the inventory against the project files so no changed path remains stale. Include `AGENTS.md` in the inventory.

## Testing Guidelines

Run `python3 -m unittest discover -s tests` for the focused picker tests. On an X11 desktop, set `PICKER_GUI_TESTS=1` to include the GUI tests; these focus windows and send keyboard events. No coverage requirement is defined. For script changes, at minimum run the syntax check above. When changing interactive behavior, exercise the relevant GTK flow in a Linux X11 session with the required tools installed. Do not treat manual checks as automated tests.

## Commit & Pull Request Guidelines

Git history contains multiple commits, with many messages using a `type(scope): summary` form; no formal commit convention is enforced. Use a short imperative summary (for example, `Improve clipboard fallback`). Pull requests should explain the user-visible change, list manual or automated checks performed, and include screenshots for visible menu changes when useful. Link related issues when applicable.

## Keeping This Guide Current

For every project change, check this `AGENTS.md` and `FILEPATH.md` as part of the same work. Update this guide whenever the change adds or alters project structure, build or test commands, dependencies, coding conventions, or contribution workflows. Update `FILEPATH.md` for every project file addition, deletion, rename, move, or type change, following the rules above. Keep both accurate for the repository after the change; do not finish a change while either file contains stale guidance or paths.
