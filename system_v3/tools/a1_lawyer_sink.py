#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"
TRANSIENT_A1_LAWYER_ROOT = REPO / "work" / "a1_transient_lawyer"


def _now_utc_compact() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _transient_memos_dir(*, run_id: str) -> Path:
    return TRANSIENT_A1_LAWYER_ROOT / str(run_id).strip() / "lawyer_memos"


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


_REQUIRED_BRANCH_TRACK_TOKENS: tuple[str, ...] = (
    "TRACK_IGT_TYPE1_ENGINE",
    "TRACK_IGT_TYPE2_ENGINE",
    "TRACK_AXIS0_PERTURBATION",
    "TRACK_CONSTRAINT_LADDER",
    "TRACK_PHYSICS_OVERLAY_OPERATORIZATION",
    "TRACK_GRAVEYARD_RESCUE",
)


def _validate_strategy_substance(obj: dict) -> None:
    """
    Enforce that an A1_STRATEGY_v1 is not "kernel-safe filler".

    This is intentionally minimal and structural:
    - Every item must be tagged with BRANCH_TRACK.
    - Coverage and minimum counts across the anchor tracks must hold.
    """

    alts = obj.get("alternatives")
    if not isinstance(alts, list) or not alts:
        raise SystemExit("strategy missing alternatives[]")

    track_counts: dict[str, int] = {t: 0 for t in _REQUIRED_BRANCH_TRACK_TOKENS}
    missing_branch_track = 0
    invalid_track = 0
    for item in alts:
        if not isinstance(item, dict):
            continue
        def_fields = item.get("def_fields")
        if not isinstance(def_fields, list):
            missing_branch_track += 1
            continue
        found: str | None = None
        for f in def_fields:
            if not isinstance(f, dict):
                continue
            if str(f.get("name", "")).strip().upper() != "BRANCH_TRACK":
                continue
            found = str(f.get("value", "")).strip()
            break
        if not found:
            missing_branch_track += 1
            continue
        if found not in track_counts:
            invalid_track += 1
            continue
        track_counts[found] += 1

    if missing_branch_track > 0:
        raise SystemExit(f"strategy substance fail: {missing_branch_track} items missing BRANCH_TRACK")
    if invalid_track > 0:
        raise SystemExit(
            f"strategy substance fail: {invalid_track} items have invalid BRANCH_TRACK (must be one of required anchors)"
        )

    used = [t for t, c in track_counts.items() if c > 0]
    if len(used) < 4:
        raise SystemExit(f"strategy substance fail: only {len(used)} BRANCH_TRACK anchors used; need >= 4. used={used}")

    too_small = [(t, c) for t, c in track_counts.items() if c > 0 and c < 20]
    if too_small:
        raise SystemExit(f"strategy substance fail: track counts below 20: {too_small}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Ingest A1 lawyer-pack outputs into the run-local sandbox. "
            "Memos are stored under transient work surfaces. "
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
    memos_dir = _transient_memos_dir(run_id=run_id)
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
        _validate_strategy_substance(obj)
        for stale in sorted(outgoing_dir.glob("*__A1_STRATEGY_v1.json")):
            stale.unlink(missing_ok=True)
        out_path = outgoing_dir / f"{_now_utc_compact()}__A1_STRATEGY_v1.json"
        _write_json(out_path, obj)
        print(json.dumps({"schema": "A1_LAWYER_SINK_RESULT_v1", "status": "STRATEGY_STORED", "out": str(out_path)}, sort_keys=True))
        return 0

    raise SystemExit("unsupported schema: expected A1_LAWYER_MEMO_v1 or A1_STRATEGY_v1")


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
