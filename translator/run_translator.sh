#!/usr/bin/env bash

# Resolve the absolute path of this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Target python script
PYTHON_SCRIPT="$SCRIPT_DIR/translator.py"

# Ensure environment variables for X11 / Cinnamon display are loaded
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# Check required system utilities
for cmd in xclip xdotool notify-send python3; do
    if ! command -v "$cmd" &>/dev/null; then
        notify-send -t 3000 "Translator Error" "Missing dependency: $cmd"
        exit 1
    fi
done

# Run the python script
python3 "$PYTHON_SCRIPT"

