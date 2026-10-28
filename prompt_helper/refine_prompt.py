#!/usr/bin/env python3
import sys
import os
import requests

# GapGPT API configuration (loaded from your environment)
API_KEY = os.getenv("GAPGPT_API_KEY")
API_URL = "https://api.gapgpt.app/v1/chat/completions"
MODEL_NAME = "gpt-4o-mini-2024-07-18"

def refine_prompt(raw_text):
    if not API_KEY:
        raise RuntimeError("GAPGPT_API_KEY is not set.")

    # Specialized system prompt for coding, C++, CFD, and CLI assistants
    system_prompt = (
        "You are an expert prompt engineer for coding, modern C++, CFD, and Linux systems. "
        "The user will provide broken English, quick notes, or Persian describing an engineering or coding task. "
        "Your task: Convert and rewrite this into a crisp, concise, direct, high-impact English prompt "
        "ready to be fed into a coding CLI assistant (like gapcode). "
        "Rules: "
        "- Do NOT answer the user's question. "
        "- Output ONLY the final polished English prompt without quotes, markdown backticks, or conversational greetings. "
        "- Retain all technical terms, function names, class names, and constraints."
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text}
        ],
        "temperature": 0.2
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()
    result = data["choices"][0]["message"]["content"].strip()
    if not result:
        raise RuntimeError("The API returned an empty prompt.")
    return result

if __name__ == "__main__":
    # Handle input arguments or pipeline stdin
    if len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])
    else:
        raw_input = sys.stdin.read().strip()
    
    if raw_input:
        try:
            print(refine_prompt(raw_input))
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError, RuntimeError) as error:
            print(f"Prompt refinement failed: {error}", file=sys.stderr)
            sys.exit(1)

