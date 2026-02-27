#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
A2_STATE_DEFAULT = ROOT / "system_v3" / "a2_state"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Append a structured A2 memory event (deterministic JSONL).")
    ap.add_argument("--event-type", required=True)
    ap.add_argument("--payload-json", required=True, help="JSON object string payload")
    ap.add_argument("--a2-state-dir", default=str(A2_STATE_DEFAULT))
    args = ap.parse_args(argv)

    try:
        payload = json.loads(args.payload_json)
    except Exception as exc:
        raise SystemExit(f"invalid payload json: {exc}")
    if not isinstance(payload, dict):
        raise SystemExit("payload must be a JSON object")

    row = {
        "schema": "A2_MEMORY_EVENT_v1",
        "created_utc": _utc_iso(),
        "type": str(args.event_type),
        "payload": payload,
    }
    a2_state_dir = Path(args.a2_state_dir).expanduser().resolve()
    _append_jsonl(a2_state_dir / "memory.jsonl", row)
    print(json.dumps({"schema": "A2_MEMORY_APPEND_RESULT_v1", "out": str(a2_state_dir / "memory.jsonl")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
