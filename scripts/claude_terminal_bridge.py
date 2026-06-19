#!/usr/bin/env python3
"""File bridge for running Claude from an authenticated macOS Terminal shell.

Codex Desktop may not see Claude Code OAuth/keychain auth even when the user's
normal Terminal does. This bridge writes a prompt/job file and prints the exact
Terminal command to run. Codex can then read the output artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_DIR = Path("/tmp/codex_claude_bridge")
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_CLAUDE_BIN = Path("/Users/joshuaeisenhart/.claude/local/claude")


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    if args.prompt:
        return args.prompt
    data = sys.stdin.read()
    if data.strip():
        return data
    raise SystemExit("missing prompt")


def slugify(text: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-")
    return "-".join(part for part in cleaned.split("-") if part)[:48] or "claude-job"


def create_job(args: argparse.Namespace) -> int:
    prompt = read_prompt(args)
    out_dir = args.dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    base = f"{stamp}-{slugify(prompt)}"
    prompt_path = out_dir / f"{base}.prompt.txt"
    output_path = out_dir / f"{base}.output.txt"
    receipt_path = out_dir / f"{base}.receipt.json"
    runner_path = out_dir / f"{base}.command"

    prompt_path.write_text(prompt, encoding="utf-8")
    claude_args = [
        str(args.claude_bin),
        "-p",
        "--model",
        args.model,
    ]
    if args.output_format:
        claude_args.extend(["--output-format", args.output_format])
    claude_cmd = " ".join(shlex.quote(part) for part in claude_args)
    shell = f"""#!/bin/zsh
set -u
cd {shlex.quote(str(Path.cwd()))}
{claude_cmd} < {shlex.quote(str(prompt_path))} > {shlex.quote(str(output_path))} 2>&1
rc=$?
CLAUDE_BRIDGE_RC=$rc python3 - <<'PY'
import json
import os
from datetime import UTC, datetime
from pathlib import Path
rc = int(os.environ["CLAUDE_BRIDGE_RC"])
receipt = {{
  "generated_at": datetime.now(UTC).isoformat(),
  "model": {args.model!r},
  "output_format": {args.output_format!r},
  "prompt_sha256": {hashlib.sha256(prompt.encode("utf-8")).hexdigest()!r},
  "status": "spawned" if rc == 0 else "blocked",
  "returncode": rc,
  "prompt_path": {{"prompt_path"!r}},
  "output_path": {{"output_path"!r}},
  "output_preview": Path({{"output_path"!r}}).read_text(encoding="utf-8", errors="replace")[:4000],
}}
Path({{"receipt_path"!r}}).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
PY
exit $rc
"""
    shell = shell.replace('{"prompt_path"!r}', repr(str(prompt_path)))
    shell = shell.replace('{"output_path"!r}', repr(str(output_path)))
    shell = shell.replace('{"receipt_path"!r}', repr(str(receipt_path)))
    runner_path.write_text(shell, encoding="utf-8")
    runner_path.chmod(0o755)

    payload = {
        "model": args.model,
        "output_format": args.output_format,
        "prompt_path": str(prompt_path),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "output_path": str(output_path),
        "receipt_path": str(receipt_path),
        "runner_path": str(runner_path),
        "terminal_command": str(runner_path),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def read_job(args: argparse.Namespace) -> int:
    receipt_path = args.receipt
    if not receipt_path.exists():
        print(json.dumps({"ok": False, "blocker": f"receipt not found: {receipt_path}"}, indent=2))
        return 1
    print(receipt_path.read_text(encoding="utf-8"))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--prompt")
    create.add_argument("--prompt-file")
    create.add_argument("--model", default=DEFAULT_MODEL)
    create.add_argument("--output-format", choices=["text", "json", "stream-json"])
    create.add_argument("--claude-bin", type=Path, default=DEFAULT_CLAUDE_BIN)
    create.add_argument("--dir", type=Path, default=DEFAULT_DIR)

    read = sub.add_parser("read")
    read.add_argument("receipt", type=Path)

    args = parser.parse_args(argv)
    if args.command == "create":
        return create_job(args)
    if args.command == "read":
        return read_job(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
