# Project State

Layout: this file is organized around repository purpose, implemented utilities, project rules, verification, Git state, and open questions. Keep these sections stable; update facts in place and put historical updates only in the dated change log.

## Project Purpose and Scope

- This repository contains three standalone Linux desktop utilities: Prompt Picker, Prompt Helper, and Translator.
- Prompt Picker also includes C++/CFD prompt templates for other projects; this repository itself has no C++/CFD implementation.
- There is no build system, example tree, or separate asset tree. Focused picker tests are in `tests/`.
- The root `README.md` summarizes the utilities; utility-specific setup and behavior are documented in each utility directory.

## Repository Structure

- `prompt_picker/` contains the Bash prompt generator, GTK 3 window, and README.
- `prompt_helper/` contains the Zenity launcher, Python prompt refiner, and README.
- `translator/` contains the Bash launcher, Python text polisher, and README.
- `FILEPATH.md` is the pipe-separated project file inventory used by Prompt Picker; keep it synchronized with project files.
- `AGENTS.md` contains repository workflow, documentation, style, and verification rules.
- API key files are local runtime configuration and are not tracked: `prompt_helper/.gapgpt_key` and `translator/.api_translator`.

## Utility Behavior and Constraints

- Prompt Picker discovers `FILEPATH.md` (with legacy filename fallbacks), builds file-specific, project-maintenance, and Git prompt menus, and copies generated prompts to the clipboard. It can restore the previously active window and paste when the X11 tools are available.
- Prompt Picker's main project menu offers prompts for `AGENTS.md`, `FILEPATH.md`, `STATE.md`, `AGENT_REPORT.md`, and `TASK_PLAN.md`, plus execution of the first unchecked task-plan step and a Markdown math-render repair prompt for a user-selected path. Those prompts generate instructions; the picker does not perform the requested repository edits itself.
- Prompt Helper gathers editable text in Zenity, sends it to the GapGPT chat completions API, and copies/pastes the returned English prompt. It uses `GAPGPT_API_KEY` before its local key file and currently invokes its Python script through an absolute path.
- Translator sends text to the GapGPT chat completions API, then prints and copies the polished result. The Python entry point accepts an argument, piped standard input, or X11 primary selection; its launcher reads the clipboard and invokes the script through an absolute path.
- Prompt Helper and Translator use model `gpt-4o-mini-2024-07-18`; their request timeouts are 30 and 20 seconds respectively. These are implementation defaults, not project-wide API guarantees.
- Desktop flows target Linux/X11. Required programs and fallback behavior are documented in `AGENTS.md` and the utility READMEs.

## Governing Project Rules

- Follow `AGENTS.md`: keep shell compatible with Bash 4+, quote expansions, use four-space indentation, and prefer small descriptive `snake_case` functions. Keep Python compatible with supported desktop Python 3 versions.
- For project changes, review the root README and the README for each touched utility; keep documentation accurate alongside code or structure changes.
- Update `FILEPATH.md` for added, removed, moved, renamed, or retyped project files. Use its `TYPE | LABEL | PATH` schema, existing section headers, exact repository-relative paths, and mechanical filename-to-title labels.
- `AGENTS.md` specifies the focused unittest command, Bash syntax checks, and X11/GTK exercise for interactive behavior changes.
- Keep API keys private and out of version control. Both API clients prefer `GAPGPT_API_KEY` over their local key file.
- Git history uses mostly Conventional Commit-shaped messages, while `AGENTS.md` asks for a short imperative summary; no binding commit convention is established in the repository.

## Current Git State

- Use `git status` and `git log` for the current branch, working tree, and history; these change independently of this document.

## Verification and Known Limitations

- No build command is configured; run `python3 -m unittest discover -s tests` for focused picker tests.
- Use the syntax checks in `AGENTS.md` after changing the corresponding Bash launchers.
- Prompt Helper and Translator contain absolute paths rooted at `/home/amir/Documents/dev-toolbox`; relocation requires updating those paths.
- Interactive clipboard, window-focus, paste, and notification behavior depends on the documented desktop utilities and an X11 session.

## Open Questions

- `translator/README.md` describes selecting text and replacing the selection, but `translator/run_translator.sh` reads the clipboard and does not itself capture or replace a selection. Confirm whether the README or launcher behavior should be corrected.
- Prompt Picker can search for `FILEPATH.md` in the active project's process tree, but the repository does not document all process-discovery edge cases; verify from an X11 session if a reported issue depends on that behavior.

## Change Log

- 2026-11-15: Created this repository-grounded status reference and added `STATE.md` to the project inventory. Recorded current utility behavior, governing workflow rules, verified Git baseline, and documentation questions.
- 2026-11-15: Updated the state for the new Prompt Picker Fix Markdown prompt, current 17-commit Git history and dirty working tree; recorded the `AGENTS.md` history correction, removed its resolved open question, and retained the unverified translator documentation and process-discovery questions.

- 2026-11-18: Added a GTK picker window with navigable menu history and focused tests; updated inventory and desktop documentation.
