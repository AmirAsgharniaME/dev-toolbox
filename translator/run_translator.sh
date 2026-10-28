#!/bin/bash
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# Read text from clipboard (Ctrl + C)
TEXT=$(/usr/bin/xclip -selection clipboard -o 2>/dev/null)

if [ -z "$TEXT" ]; then
    /usr/bin/notify-send "AI Translator" "Clipboard is empty! Copy some text first." -u low
    exit 0
fi

# Pass the copied text directly to the Python translator engine
/usr/bin/python3 /home/amir/Documents/dev-toolbox/translator/translator.py "$TEXT"
