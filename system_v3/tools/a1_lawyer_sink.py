#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"


def _now_utc_compact() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_strategy(obj: dict) -> bool:
    return str(obj.get("schema", "")).strip() == "A1_STRATEGY_v1"


def _is_memo(obj: dict) -> bool:
    return str(obj.get("schema", "")).strip() == "A1_LAWYER_MEMO_v1"


def _validate_memo(obj: dict) -> None:
    required = {
        "schema",
        "run_id",
        "sequence",
        "role",
        "claims",
        "risks",
        "graveyard_rescue_targets",
        "proposed_negative_classes",
        "proposed_terms",
    }
    missing = sorted(required - set(obj.keys()))
    if missing:
        raise SystemExit(f"memo missing keys: {missing}")
    if not isinstance(obj.get("claims"), list):
        raise SystemExit("memo.claims must be list")
    if not isinstance(obj.get("risks"), list):
        raise SystemExit("memo.risks must be list")
    if not isinstance(obj.get("graveyard_rescue_targets"), list):
        raise SystemExit("memo.graveyard_rescue_targets must be list")
    if not isinstance(obj.get("proposed_negative_classes"), list):
        raise SystemExit("memo.proposed_negative_classes must be list")
    if not isinstance(obj.get("proposed_terms"), list):
        raise SystemExit("memo.proposed_terms must be list")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Ingest A1 lawyer-pack outputs into the run-local sandbox. "
            "Memos are stored under a1_sandbox/lawyer_memos/. "
            "SYNTHESIS strategy is stored under a1_sandbox/outgoing/ for packetization."
        )
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT), help="Override runs root (default: system_v3/runs).")
    ap.add_argument("--input-json", required=True, help="Path to the raw JSON output from a role prompt.")
    ap.add_argument("--sequence", type=int, default=0, help="Optional override if not present in memo.")
    ap.add_argument("--role", default="", help="Optional override if not present in memo.")
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    if not run_id:
        raise SystemExit("missing run-id")
    runs_root = Path(args.runs_root).expanduser().resolve()
    run_dir = runs_root / run_id
    if not run_dir.exists():
        raise SystemExit(f"missing run dir: {run_dir}")

    in_path = Path(args.input_json).expanduser().resolve()
    obj = _read_json(in_path)
    if not isinstance(obj, dict):
        raise SystemExit("input must be a JSON object")

    sandbox_root = run_dir / "a1_sandbox"
    memos_dir = sandbox_root / "lawyer_memos"
    outgoing_dir = sandbox_root / "outgoing"
    for d in (memos_dir, outgoing_dir):
        d.mkdir(parents=True, exist_ok=True)

    if _is_memo(obj):
        _validate_memo(obj)
        seq = int(obj.get("sequence") or args.sequence or 0)
        role = str(obj.get("role") or args.role or "UNKNOWN").strip().upper()
        if seq <= 0:
            raise SystemExit("memo missing valid sequence")
        if not role:
            role = "UNKNOWN"
        out_path = memos_dir / f"{seq:06d}_MEMO_{role}__{_now_utc_compact()}.json"
        _write_json(out_path, obj)
        print(json.dumps({"schema": "A1_LAWYER_SINK_RESULT_v1", "status": "MEMO_STORED", "out": str(out_path)}, sort_keys=True))
        return 0

    if _is_strategy(obj):
        out_path = outgoing_dir / f"{_now_utc_compact()}__A1_STRATEGY_v1.json"
        _write_json(out_path, obj)
        print(json.dumps({"schema": "A1_LAWYER_SINK_RESULT_v1", "status": "STRATEGY_STORED", "out": str(out_path)}, sort_keys=True))
        return 0

    raise SystemExit("unsupported schema: expected A1_LAWYER_MEMO_v1 or A1_STRATEGY_v1")


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
