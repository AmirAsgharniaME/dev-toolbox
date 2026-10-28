# Prompt Helper

Prompt Helper opens an editable Zenity dialog for a rough prompt, sends the text to the GapGPT chat completions API, and copies the refined English prompt to the clipboard. It then returns focus to the window that was active before the dialog opened and simulates `Ctrl+Shift+V` to paste the result without pressing Enter.

The refiner is intended for coding, modern C++, CFD, and Linux systems prompts. It accepts Persian, English, or mixed-language input and asks the model to return only the refined prompt text in English.

## Requirements

- Bash
- Zenity
- Python 3 and the Python `requests` package
- `xdotool` to capture and restore the active window and paste the result
- `xclip` to copy the result to the clipboard
- A GapGPT API key

The paste step uses `Ctrl+Shift+V`, which is common in terminal emulators. The script does not detect whether the active application supports that shortcut.

## Configure the API key

The refiner checks for an API key in this order:

1. The `GAPGPT_API_KEY` environment variable.
2. A `.gapgpt_key` file in this directory (`prompt_helper/.gapgpt_key`).

For example, set the environment variable in the shell before launching the helper:

```bash
export GAPGPT_API_KEY="your-api-key"
bash prompt_helper/prompt_helper.sh
```

Alternatively, put the key by itself in `prompt_helper/.gapgpt_key`. Keep this file private and do not commit it. The key file is read at runtime and is not included in the repository.

## Run

From the repository root, run:

```bash
bash prompt_helper/prompt_helper.sh
```

The shell script currently calls the refiner by its absolute path, `/home/amir/Documents/dev-toolbox/prompt_helper/refine_prompt.py`. If you keep the project elsewhere, update that path in `prompt_helper.sh` before running it.

You can also make the script executable once with `chmod +x prompt_helper/prompt_helper.sh` and then run `./prompt_helper/prompt_helper.sh`.

Type or paste a prompt in the dialog and submit it. The refined text is copied to the clipboard and pasted into the previously active window. Canceling the dialog or submitting empty text exits without refining anything.

## How refinement works

`prompt_helper.sh` captures the active window, opens the editable dialog, and pipes its text to `refine_prompt.py`. The Python script sends the prompt to the GapGPT chat completions endpoint using the `gpt-4o-mini-2024-07-18` model. It uses a 30-second request timeout and returns the model response text. The shell script copies that text with `xclip` and attempts to paste it into the captured window.

If the API key is missing or the request fails, the Python script prints an error to standard error and exits unsuccessfully; the shell helper exits without copying or pasting an empty result. Ensure the listed desktop tools are installed and that an X11 session is available for window and clipboard operations.
