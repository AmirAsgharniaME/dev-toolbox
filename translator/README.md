
## Translator

`run_translator.sh` launches a Python utility that translates Persian or mixed text into polished academic English and improves English text. In an X11 desktop session, select text and run the launcher to replace the selection. You can also pipe text to the Python script; it prints the result to standard output.

## Requirements

- Python 3 and the `requests` package
- `xclip`, `xdotool`, and `notify-send`
- An X11 desktop session for selected-text replacement
- A GapGPT API key

Set `GAPGPT_API_KEY`, or save the key in `.api_translator` beside `translator.py`. Keep `.api_translator` private and out of version control.

## Run

From the repository root, launch the desktop utility with:

```bash
bash translator/run_translator.sh
```

To process piped text directly:

```bash
printf 'Text to improve' | python3 translator/translator.py
```
