#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
A2_STATE = SYSTEM_V3 / "a2_state"


def _now_utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Append a structured A1 brain event (noncanonical heat, persisted).")
    ap.add_argument("--event-type", required=True)
    ap.add_argument("--payload-json", required=True, help="JSON object string payload")
    ap.add_argument("--a2-state-dir", default=str(A2_STATE))
    args = ap.parse_args(argv)

    event_type = str(args.event_type).strip().upper()
    if not event_type:
        raise SystemExit("missing event-type")
    if len(event_type) > 64:
        raise SystemExit("event-type too long")

    try:
        payload = json.loads(str(args.payload_json))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"payload-json must be valid JSON: {exc}")
    if not isinstance(payload, dict):
        raise SystemExit("payload-json must be a JSON object")

    a2_state_dir = Path(args.a2_state_dir).expanduser().resolve()
    a2_state_dir.mkdir(parents=True, exist_ok=True)
    path = a2_state_dir / "a1_brain.jsonl"

    row = {
        "schema": "A1_BRAIN_EVENT_v1",
        "ts_utc": _now_utc_iso(),
        "event_type": event_type,
        "payload": payload,
    }
    row_bytes = _canonical_json_bytes(row)
    row["row_sha256"] = _sha256_bytes(row_bytes)
    row_bytes = _canonical_json_bytes(row)

    with path.open("a", encoding="utf-8") as fh:
        fh.write(row_bytes.decode("utf-8"))

    print(json.dumps({"schema": "A1_BRAIN_APPEND_RESULT_v1", "out": str(path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))

