#!/usr/bin/env bash

# Capture the currently active window (your terminal running gapcode)
ACTIVE_WIN=$(xdotool getactivewindow)

# Open a large multi-line editable popup dialog
USER_INPUT=$(zenity --text-info \
                    --editable \
                    --title="GapCode Prompt Assistant" \
                    --width=700 \
                    --height=400)

# Exit quietly if the user pressed Cancel or submitted empty text
if [ -z "$USER_INPUT" ]; then
    exit 0
fi

# Send the input to the python refinement script using its absolute path
REFINED_PROMPT=$(echo "$USER_INPUT" | python3 /home/amir/Documents/dev-toolbox/prompt_helper/refine_prompt.py)

# Exit if python returned an empty string or failed
if [ -z "$REFINED_PROMPT" ]; then
    exit 1
fi

# Copy refined prompt to the system clipboard (without adding a trailing newline)
echo -n "$REFINED_PROMPT" | xclip -selection clipboard

# Restore focus to the target terminal and simulate Ctrl+Shift+V to paste without Enter
if [ -n "$ACTIVE_WIN" ]; then
    xdotool windowactivate --sync "$ACTIVE_WIN"
    sleep 0.1
    xdotool key --clearmodifiers ctrl+shift+v
fi
