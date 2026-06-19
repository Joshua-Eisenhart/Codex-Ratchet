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

print("\n=== Smoke chat (prefer grok-build-0.1, then grok-4.3) ===")
model_ids = [m.id for m in models.data]
preferred = [
    "grok-build-0.1",
    "grok-4.3",
    "grok-4.20-0309-reasoning",
    "grok-4.20-0309-non-reasoning",
]
test_model = next((model for model in preferred if model in model_ids), model_ids[0])
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
