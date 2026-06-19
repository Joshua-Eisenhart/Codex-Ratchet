#!/usr/bin/env python3
"""Quick Grok chat. Usage: ./grok_chat.py 'your prompt here'"""
import os
import sys

from openai import OpenAI

if len(sys.argv) < 2:
    print("Usage: grok_chat.py 'your prompt'  [--model grok-4.3|grok-build-0.1]  [--stream]")
    sys.exit(1)

key = os.environ.get("XAI_API_KEY")
if not key:
    print("ERROR: XAI_API_KEY not set.")
    sys.exit(1)

# Parse args: prompt is positional, --model and --stream optional
args = sys.argv[1:]
model = os.environ.get("GROK_CHAT_MODEL", "grok-4.3")
stream = False
if "--model" in args:
    i = args.index("--model")
    model = args[i + 1]
    args = args[:i] + args[i + 2:]
if "--stream" in args:
    stream = True
    args = [a for a in args if a != "--stream"]
prompt = " ".join(args)

client = OpenAI(api_key=key, base_url="https://api.x.ai/v1")

if stream:
    for chunk in client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    ):
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print()
else:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    print(resp.choices[0].message.content)
