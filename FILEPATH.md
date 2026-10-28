# SYNTAX: TYPE | LABEL | PATH
# LABEL: Mechanical conversion of filename snake_case to Title Case + type suffix. NEVER add subjective words like "placeholder", "temporary", or status notes.
# TYPES: MD (docs), H (headers), CPP (sources), EXE (tests/mains), CFG (configs),  SH (Shell Script), PY (Python Script)
# Keep exact section headers below. Append new verified project files in-place.

# docs
MD | License | LICENSE
MD | Readme | README.md
MD | Agents | AGENTS.md
MD | Filepath | FILEPATH.md
MD | Readme | prompt_picker/README.md

# Shell Script
SH | Prompt Picker | prompt_picker/prompt_picker.sh
