#!/bin/bash

set -u

# Step 1: Open a large Zenity text input box (editable text info dialog)
# We create a temporary file to capture multi-line input from user
TEMP_FILE=$(mktemp) || {
    zenity --error --text="Could not create a temporary file for the prompt."
    exit 1
}

# Using zenity --text-info with --editable allows multi-line typing and proper viewing
if ! zenity --text-info \
    --title="GapCode Prompt Assistant" \
    --editable \
    --width=700 \
    --height=400 \
    --filename="" > "$TEMP_FILE"; then
    rm -f "$TEMP_FILE"
    exit 0
fi

# Read the content entered by the user
RAW_INPUT=$(cat "$TEMP_FILE")
rm -f "$TEMP_FILE"

# Exit if input is empty
if [ -z "$RAW_INPUT" ]; then
    exit 0
fi

# Step 2: Pass raw input to the Python refiner script
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! REFINED_PROMPT=$(python3 "$SCRIPT_DIR/refine_prompt.py" <<< "$RAW_INPUT" 2>&1); then
    ERROR_MESSAGE="$REFINED_PROMPT"
    if [ -z "$ERROR_MESSAGE" ]; then
        ERROR_MESSAGE="Prompt refinement failed. Check GAPGPT_API_KEY and your network connection."
    fi
    zenity --error --title="Prompt Assistant" --text="$ERROR_MESSAGE"
    exit 1
fi

# Check if refinement was successful
if [ -z "$REFINED_PROMPT" ]; then
    zenity --error --text="Failed to refine prompt!"
    exit 1
fi

# Step 3: Copy the refined prompt to the system clipboard
if ! printf '%s' "$REFINED_PROMPT" | xclip -selection clipboard; then
    zenity --error --text="Could not copy the refined prompt to the clipboard."
    exit 1
fi

# Step 4: Automatically paste into the active terminal window (without pressing Enter)
sleep 0.3
xdotool key ctrl+shift+v

