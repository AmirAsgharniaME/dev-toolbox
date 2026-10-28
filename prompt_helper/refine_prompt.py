#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import requests

def get_api_key():
    # Priority 1: Check environment variable
    api_key = os.getenv("GAPGPT_API_KEY")
    if api_key:
        return api_key.strip()

    # Priority 2: Read from local .gapgpt_key file next to this script
    key_file = Path(__file__).resolve().parent / ".gapgpt_key"
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

def refine_prompt(raw_text):
    if not API_KEY:
        raise RuntimeError(
            "API Key not found! Please place your key inside '.gapgpt_key' "
            f"in {Path(__file__).resolve().parent} or set the GAPGPT_API_KEY environment variable."
        )

    system_prompt = (
        "You are an expert prompt engineer for coding, modern C++, CFD, and Linux systems. "
        "The user will provide a raw prompt in Persian, English, or mixed. "
        "Refine it into a clear, professional, context-rich engineering prompt in English. "
        "Output ONLY the refined prompt text without any introductory or concluding remarks."
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
        "temperature": 0.3
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    result = response.json()
    return result["choices"][0]["message"]["content"].strip()

if __name__ == "__main__":
    raw_input_text = sys.stdin.read().strip()
    if not raw_input_text:
        sys.exit(0)

    try:
        refined = refine_prompt(raw_input_text)
        print(refined)
    except Exception as err:
        sys.stderr.write(f"Error: {err}\n")
        sys.exit(1)
