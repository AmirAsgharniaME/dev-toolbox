#!/usr/bin/env python3
import sys
import os
import time
import subprocess
from pathlib import Path
import requests

def get_api_key():
    # Priority 1: Check environment variable
    api_key = os.getenv("GAPGPT_API_KEY")
    if api_key:
        return api_key.strip()

    # Priority 2: Read from local .api_translator file next to this script
    key_file = Path(__file__).resolve().parent / ".api_translator"
    if key_file.is_file():
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except OSError as e:
            sys.stderr.write(f"Warning: Could not read {key_file}: {e}\n")

    return None

API_KEY = get_api_key()
API_URL = "https://api.gapgpt.app/v1/chat/completions"
MODEL_NAME = "gpt-4o-mini-2024-07-18"

def notify(title, message):
    """Show desktop notification in Linux Mint Cinnamon."""
    try:
        subprocess.run(["notify-send", "-t", "2000", title, message], check=False)
    except Exception:
        pass

def get_selected_text():
    """Retrieve highlighted text from the X11 primary selection."""
    try:
        res = subprocess.run(
            ["xclip", "-o", "-selection", "primary"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return ""

def replace_selected_text(new_text):
    """Copy the refined text to clipboard and simulate Ctrl+V for in-place replacement."""
    p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True)
    p.communicate(input=new_text)
    time.sleep(0.08)
    # The --clearmodifiers flag prevents stuck modifier keys during shortcut execution
    subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"])

def polish_ielts(raw_text):
    if not API_KEY:
        raise RuntimeError(
            f"API Key not found! Please place your key inside '.api_translator' "
            f"in {Path(__file__).resolve().parent} or set the GAPGPT_API_KEY environment variable."
        )

    system_prompt = (
        "You are an expert IELTS Academic English writing coach and proofreader targeting Band 8.0+.\n"
        "Your task is to take the user's text and refine it according to these rules:\n"
        "1. If the input is in Persian or mixed: Accurately translate it into sophisticated, academic English. Use precise collocations and natural syntactic structures.\n"
        "2. If the input is in English: Proofread and elevate it. Fix all grammatical, lexical, and prepositional errors. Replace weak/informal phrases with academic alternatives without being overly verbose or archaic.\n"
        "3. Preserve all technical terms, code snippets, mathematical notation, and proper nouns verbatim.\n"
        "4. Output STRICTLY the polished English text only. Do NOT provide explanations, alternative choices, greetings, or markdown code blocks."
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text}
        ],
        "temperature": 0.25
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
    response.raise_for_status()

    result = response.json()
    return result["choices"][0]["message"]["content"].strip()

if __name__ == "__main__":
    # Handle standard input (pipe mode) if connected
    if not sys.stdin.isatty():
        raw_text = sys.stdin.read().strip()
        if raw_text:
            try:
                print(polish_ielts(raw_text))
            except Exception as err:
                sys.stderr.write(f"Error: {err}\n")
                sys.exit(1)
        sys.exit(0)

    # Otherwise, run in GUI shortcut mode using highlighted text
    selected = get_selected_text()
    if not selected:
        notify("Translator / Polisher", "No text selected.")
        sys.exit(0)

    notify("Translator / Polisher", "Polishing and elevating text...")
    try:
        refined = polish_ielts(selected)
        replace_selected_text(refined)
    except Exception as err:
        notify("Translator - Error", str(err))
        sys.stderr.write(f"Error: {err}\n")
        sys.exit(1)

