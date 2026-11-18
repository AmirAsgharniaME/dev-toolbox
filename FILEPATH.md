# SYNTAX: TYPE | LABEL | PATH
# LABEL: Mechanical conversion of filename snake_case to Title Case + type suffix. NEVER add subjective words like "placeholder", "temporary", or status notes.
# TYPES: MD (docs), H (headers), CPP (sources), EXE (tests/mains), CFG (configs),  SH (Shell Script), PY (Python Script)
# Keep exact section headers below. Append new verified project files in-place.

# docs
MD | License | LICENSE
MD | Readme | README.md
MD | Agents | AGENTS.md
MD | Filepath | FILEPATH.md
MD | State | STATE.md
MD | Readme | prompt_picker/README.md
MD | Readme | prompt_helper/README.md
MD | Readme | translator/README.md

# Config
CFG | Gitignore | .gitignore

# Shell Script
SH | Prompt Picker | prompt_picker/prompt_picker.sh
SH | Prompt Helper | prompt_helper/prompt_helper.sh
SH | Run Translator | translator/run_translator.sh

# Python Script
PY | Picker Ui | prompt_picker/picker_ui.py
PY | Test Picker Ui | tests/test_picker_ui.py
PY | Test Picker Gui | tests/test_picker_gui.py
PY | Refine Prompt | prompt_helper/refine_prompt.py
PY | Translator | translator/translator.py
