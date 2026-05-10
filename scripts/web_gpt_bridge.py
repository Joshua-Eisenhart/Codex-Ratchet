#!/usr/bin/env python3
"""Repo-local bridge around the external chatgpt-browser helper.

This script does not implement browser automation itself. It verifies and calls
the already-installed helper so Codex Ratchet work can use one stable repo
entrypoint for Web GPT/browser-assisted review.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "work" / "web_gpt_bridge"


def run_helper(args: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    helper = shutil.which("chatgpt-browser")
    if not helper:
        raise SystemExit("chatgpt-browser helper is not on PATH")
    return subprocess.run(
        [helper, *args],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def write_receipt(action: str, result: subprocess.CompletedProcess[str], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"{stamp}_{action}.json"
    payload = {
        "action": action,
        "timestamp_utc": stamp,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "helper": shutil.which("chatgpt-browser"),
        "repo": str(REPO),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def build_visualizer_prompt() -> str:
    return """Review the Codex Ratchet main visualizer UI as a browser-visible interface.

Scope:
- Main URL: http://localhost:8765/ratchet-visualizer.html?view=rosetta&v=combined-main-2
- Engine tabs: Carnot, Szilard, Rosetta
- Source/fallback rule: sim/proof outputs are source of truth; UI must not invent proof claims.

Please return:
1. Top 5 UI clarity issues.
2. Top 5 interaction improvements.
3. Any overclaiming or source/fallback ambiguity.
4. A short patch checklist for the local repo.

Do not propose changing canonical sim/proof/math truth. Focus on layout, affordance, source labels, and browser usability.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex Ratchet Web GPT browser bridge")
    parser.add_argument("action", choices=["status", "snapshot", "read", "send", "ask-visualizer"])
    parser.add_argument("text", nargs="*", help="Prompt text for send")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    if args.action == "status":
      helper = shutil.which("chatgpt-browser")
      if not helper:
          print("chatgpt-browser: missing")
          return 1
      result = run_helper(["url"], timeout=30)
      receipt = write_receipt("status", result, out_dir)
      print(result.stdout.strip())
      print(f"receipt: {receipt}")
      return result.returncode

    if args.action == "snapshot":
        result = run_helper(["snapshot"], timeout=45)
        receipt = write_receipt("snapshot", result, out_dir)
        print(result.stdout)
        print(f"receipt: {receipt}")
        return result.returncode

    if args.action == "read":
        result = run_helper(["read"], timeout=45)
        receipt = write_receipt("read", result, out_dir)
        print(result.stdout)
        print(f"receipt: {receipt}")
        return result.returncode

    if args.action == "send":
        prompt = " ".join(args.text).strip()
        if not prompt:
            print("send requires prompt text", file=sys.stderr)
            return 2
        result = run_helper(["send", prompt], timeout=45)
        receipt = write_receipt("send", result, out_dir)
        print(result.stdout.strip())
        print(f"receipt: {receipt}")
        return result.returncode

    if args.action == "ask-visualizer":
        result = run_helper(["send", build_visualizer_prompt()], timeout=45)
        receipt = write_receipt("ask_visualizer", result, out_dir)
        print(result.stdout.strip())
        print(f"receipt: {receipt}")
        return result.returncode

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
