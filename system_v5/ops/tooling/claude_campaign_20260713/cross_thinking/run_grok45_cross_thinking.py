#!/usr/bin/env python3
"""Run one receipt-bound Grok 4.5 advisory audit.

The provider response is proposal-only. It cannot satisfy or promote any local
scientific gate.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any


HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
PROMPT_PATH = HERE / "grok45_cross_thinking_prompt.md"
RESULTS_DIR = HERE / "results"
RECEIPT_PATH = RESULTS_DIR / "grok45_cross_thinking_receipt.json"
RAW_PATH = RESULTS_DIR / "grok45_cross_thinking_raw.md"
MODEL = "grok-4.5"
ENDPOINT = "https://api.x.ai/v1/chat/completions"
SCHEMA = "codex-ratchet.grok-cross-thinking-receipt.v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=HERE,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def post_json(payload: dict[str, Any], key: str, timeout: float = 300.0) -> dict[str, Any]:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    key = os.environ.get("XAI_API_KEY")
    if not key:
        print("ERROR: XAI_API_KEY not set", file=sys.stderr)
        return 2

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    try:
        raw = post_json(payload, key)
        proposal = raw["choices"][0]["message"]["content"]
    except (KeyError, json.JSONDecodeError, TimeoutError, urllib.error.URLError) as exc:
        print(f"ERROR: provider call failed: {exc!r}", file=sys.stderr)
        return 3

    if not isinstance(proposal, str) or not proposal.strip():
        print("ERROR: provider returned no proposal text", file=sys.stderr)
        return 4

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(proposal.rstrip() + "\n", encoding="utf-8")
    usage = raw.get("usage") or {}
    receipt = {
        "schema": SCHEMA,
        "provider": "xai",
        "route": "grok45.cross_thinking.codex_ratchet_campaign",
        "status": "completed",
        "classification": "provider_audit",
        "advisory_only": True,
        "evidence_allowed": False,
        "promotion_allowed": False,
        "claim_ceiling": "External cross-thinking only; local executions, receipts, validators, and authority files decide truth.",
        "requested_model": MODEL,
        "returned_model": raw.get("model"),
        "endpoint": ENDPOINT,
        "provider_response_id": raw.get("id"),
        "started_at": started_at,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prompt": {
            "path": str(PROMPT_PATH.relative_to(REPO_ROOT)),
            "sha256": sha256_file(PROMPT_PATH),
        },
        "raw_response": {
            "path": str(RAW_PATH.relative_to(REPO_ROOT)),
            "sha256": sha256_file(RAW_PATH),
            "nonempty": True,
        },
        "runner": {
            "path": str(pathlib.Path(__file__).resolve()),
            "sha256": sha256_file(pathlib.Path(__file__).resolve()),
            "python": sys.executable,
            "cwd": os.getcwd(),
            "git_head_before_run": git_head(),
            "command": [sys.executable, str(pathlib.Path(__file__).resolve())],
        },
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        },
    }
    RECEIPT_PATH.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "requested_model": MODEL,
                "returned_model": receipt["returned_model"],
                "receipt": str(RECEIPT_PATH),
                "raw_response": str(RAW_PATH),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
