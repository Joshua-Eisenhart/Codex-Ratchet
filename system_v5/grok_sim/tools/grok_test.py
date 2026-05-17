#!/usr/bin/env python3
"""Grok API connectivity + smoke test. Reads XAI_API_KEY from env."""
import os
import sys

from openai import OpenAI

key = os.environ.get("XAI_API_KEY")
if not key:
    print("ERROR: XAI_API_KEY not set. Run: export XAI_API_KEY='your-key'")
    sys.exit(1)

client = OpenAI(api_key=key, base_url="https://api.x.ai/v1")

print("=== Listing available models ===")
try:
    models = client.models.list()
    for m in models.data:
        print(f"  {m.id}")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

print("\n=== Smoke chat (grok-4-fast if available, else first model) ===")
model_ids = [m.id for m in models.data]
test_model = "grok-4-fast" if "grok-4-fast" in model_ids else (
    "grok-4" if "grok-4" in model_ids else model_ids[0]
)
print(f"Using: {test_model}")

resp = client.chat.completions.create(
    model=test_model,
    messages=[
        {"role": "user", "content": "Reply with exactly: 'grok api working'"}
    ],
    max_tokens=20,
)
print(f"Response: {resp.choices[0].message.content}")
print(f"Tokens used: prompt={resp.usage.prompt_tokens}, completion={resp.usage.completion_tokens}")
