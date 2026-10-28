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
        subprocess.run(["notify-send", "-t", "6000", title, message], check=False)
    except Exception:
        pass

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
    # Determine the text to process:
    # 1. First command line argument (passed from run_translator.sh)
    # 2. Piped stdin
    # 3. Fallback to primary selection
    target_text = ""
    if len(sys.argv) > 1 and sys.argv[1].strip():
        target_text = sys.argv[1].strip()
    elif not sys.stdin.isatty():
        target_text = sys.stdin.read().strip()
    else:
        try:
            res = subprocess.run(
                ["xclip", "-o", "-selection", "primary"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            target_text = res.stdout.strip()
        except Exception:
            target_text = ""

    if not target_text:
        notify("Translator / Polisher", "Clipboard is empty! Copy some text first.")
        sys.exit(0)

    notify("Translator / Polisher", "Translating / Polishing...")
    try:
        refined = polish_ielts(target_text)
        # Update clipboard with the result
        p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True)
        p.communicate(input=refined)
        
        # Display the result in a notification
        notify("Translation Result", refined)
        print(refined)
    except Exception as err:
        notify("Translator - Error", str(err))
        sys.stderr.write(f"Error: {err}\n")
        sys.exit(1)
