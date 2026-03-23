#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
BOOTPACK = REPO / "system_v3" / "runtime" / "bootpack_b_kernel_v1"
RUNS_DEFAULT = REPO / "system_v3" / "runs"

if str(BOOTPACK) not in sys.path:
    sys.path.insert(0, str(BOOTPACK))

from a1_strategy import validate_strategy  # noqa: E402
from zip_protocol_v2_writer import write_zip_protocol_v2  # noqa: E402


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _next_sequence(run_dir: Path, run_id: str) -> int:
    """
    Next expected inbound A1 packet sequence.

    IMPORTANT:
    - The bootpack runtime consumes external A1 packets via A1Bridge(packet), which persists
      monotone sequence continuity in: run_dir/a1_inbox/sequence_state.json.
    - This is intentionally separate from run_dir/sequence_state.json, which tracks the
      runtime-generated ZIP packet journal (zip_packets/) sequences.
    """

    inbox = run_dir / "a1_inbox"
    seq_state_path = inbox / "sequence_state.json"
    if seq_state_path.is_file():
        try:
            raw = json.loads(seq_state_path.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
        if isinstance(raw, dict):
            key = f"{run_id}|A1"
            try:
                last = int(raw.get(key, 0))
            except Exception:
                last = 0
            return last + 1

    # Fallback: infer next seq from packet headers currently in the inbox.
    max_seen = 0
    if inbox.is_dir():
        for p in sorted(inbox.glob("*.zip")):
            if not p.is_file():
                continue
            try:
                with zipfile.ZipFile(p, "r") as zf:
                    header = json.loads(zf.read("ZIP_HEADER.json").decode("utf-8"))
            except Exception:
                continue
            if str(header.get("run_id", "")).strip() != run_id:
                continue
            if str(header.get("source_layer", "")).strip() != "A1":
                continue
            try:
                seq = int(header.get("sequence", 0))
            except Exception:
                continue
            if seq > max_seen:
                max_seen = seq
    if max_seen > 0:
        return max_seen + 1
    return 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT), help="Override runs root (default: system_v3/runs).")
    ap.add_argument("--strategy-json", required=True, help="Path to A1_STRATEGY_v1 JSON file")
    ap.add_argument("--sequence", type=int, default=None, help="Optional explicit sequence override")
    ap.add_argument("--created-utc", default="1970-01-01T00:00:00Z")
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    if not run_id:
        raise SystemExit("missing run_id")
    runs_root = Path(args.runs_root).expanduser().resolve()
    run_dir = runs_root / run_id
    if not run_dir.is_dir():
        raise SystemExit(f"missing run_dir: {run_dir}")
    inbox = run_dir / "a1_inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    strategy_path = Path(args.strategy_json).expanduser().resolve()
    strategy = _read_json(strategy_path)
    errors = validate_strategy(strategy)
    if errors:
        raise SystemExit("invalid A1_STRATEGY_v1:\n- " + "\n- ".join(errors))

    seq = int(args.sequence) if args.sequence is not None else _next_sequence(run_dir, run_id)
    if seq <= 0:
        raise SystemExit(f"invalid sequence: {seq}")

    out_path = inbox / f"{seq:06d}_A1_TO_A0_STRATEGY_ZIP.zip"
    write_zip_protocol_v2(
        out_path=out_path,
        header={
            "zip_type": "A1_TO_A0_STRATEGY_ZIP",
            "direction": "FORWARD",
            "source_layer": "A1",
            "target_layer": "A0",
            "run_id": run_id,
            "sequence": int(seq),
            "created_utc": str(args.created_utc),
            "compiler_version": "",
        },
        payload_json={"A1_STRATEGY_v1.json": strategy},
    )
    print(json.dumps({"schema": "A1_PACKET_WRITE_RESULT_v1", "out": str(out_path), "sequence": seq}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
