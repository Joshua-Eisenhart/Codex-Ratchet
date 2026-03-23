#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_ROOT = SYSTEM_V3 / "runs"

RUN_DIRS = (
    "b_reports",
    "tapes",
    "logs",
    "zip_packets",
    "sim",
    "reports",
    "a1_inbox",
    "a1_sandbox",
    "tuning",
)

A1_SANDBOX_DIRS = (
    "cold_core",
    "external_memo_exchange/requests",
    "incoming",
    "incoming_consumed",
    "incoming_drop",
    "lawyer_memos",
    "outgoing",
    "prepack_reports",
    "prompt_queue",
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _state_counts(state: dict) -> dict:
    term_registry = state.get("term_registry", {}) if isinstance(state, dict) else {}
    return {
        "canonical_term_count": sum(
            1
            for row in term_registry.values()
            if isinstance(row, dict) and str(row.get("state", "")) == "CANONICAL_ALLOWED"
        ),
        "graveyard_count": len(state.get("graveyard", {}) or {}),
        "kill_log_count": len(state.get("kill_log", []) or []),
        "sim_registry_count": len(state.get("sim_registry", {}) or {}),
    }


def _build_run_surface(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    for name in RUN_DIRS:
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    for name in A1_SANDBOX_DIRS:
        (run_dir / "a1_sandbox" / name).mkdir(parents=True, exist_ok=True)


def _bootstrap_sequence_state(*, source_payload: dict, dest_run_id: str) -> dict:
    seq_by_source = source_payload.get("seq_by_source", {})
    if not isinstance(seq_by_source, dict):
        seq_by_source = {}
    return {
        "run_id": str(dest_run_id),
        "seq_by_source": {str(k): int(v) for k, v in seq_by_source.items()},
    }


def _bootstrap_a1_inbox_sequence(*, source_run_id: str, source_path: Path, dest_run_id: str, preserve: bool) -> dict:
    if preserve and source_path.exists():
        payload = _read_json(source_path)
        key = f"{source_run_id}|A1"
        preserved = int((payload.get(key, 0) or 0))
    else:
        preserved = 0
    return {f"{dest_run_id}|A1": int(preserved)}


def _bootstrap_driver_report(*, source_path: Path, dest_run_id: str) -> dict | None:
    if not source_path.exists():
        return None
    payload = _read_json(source_path)
    if str(payload.get("schema", "")).strip() != "A1_EXTERNAL_MEMO_BATCH_DRIVER_REPORT_v1":
        return None
    timeline = payload.get("timeline", []) or []
    last_row = timeline[-1] if timeline and isinstance(timeline[-1], dict) else {}
    if isinstance(last_row, dict):
        last_row = dict(last_row)
        fill_status = last_row.get("fill_status", {})
        if isinstance(fill_status, dict):
            fill_status = dict(fill_status)
            fill_status["path_build_novelty_stall"] = 0
            fill_status["rescue_novelty_stall"] = 0
            last_row["fill_status"] = fill_status
        last_row["run_stop_reason"] = ""
        last_row["driver_override_stop_reason"] = ""
    compact_payload = {
        "schema": "A1_EXTERNAL_MEMO_BATCH_DRIVER_REPORT_v1",
        "run_id": str(dest_run_id),
        "executed_cycles": 0,
        "wait_cycles": 0,
        "executed_cycles_total": int(payload.get("executed_cycles_total", payload.get("executed_cycles", 0)) or 0),
        "wait_cycles_total": int(payload.get("wait_cycles_total", payload.get("wait_cycles", 0)) or 0),
        "last_unique_structural": int(payload.get("last_unique_structural", -1) or -1),
        "timeline": [last_row] if last_row else [],
    }
    return compact_payload


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Create a clean seeded continuation run by preserving lower-loop state "
            "while resetting stale A1 sandbox/exchange surfaces."
        )
    )
    ap.add_argument("--source-run-id", required=True)
    ap.add_argument("--dest-run-id", required=True)
    ap.add_argument("--runs-root", default=str(RUNS_ROOT))
    ap.add_argument("--clean-dest", action="store_true")
    ap.add_argument("--preserve-a1-inbox-sequence", action="store_true")
    args = ap.parse_args(argv)

    runs_root = Path(args.runs_root).expanduser().resolve()
    source_run_id = str(args.source_run_id).strip()
    dest_run_id = str(args.dest_run_id).strip()
    if not source_run_id or not dest_run_id:
        raise SystemExit("source-run-id and dest-run-id are required")

    source_dir = runs_root / source_run_id
    dest_dir = runs_root / dest_run_id
    if not source_dir.is_dir():
        raise SystemExit(f"source run missing: {source_dir}")
    if source_run_id == dest_run_id:
        raise SystemExit("dest-run-id must differ from source-run-id")

    if dest_dir.exists():
        if not bool(args.clean_dest):
            raise SystemExit(f"dest run already exists: {dest_dir}")
        shutil.rmtree(dest_dir)

    state_path = source_dir / "state.json"
    heavy_state_path = source_dir / "state.heavy.json"
    seq_path = source_dir / "sequence_state.json"
    if not state_path.exists():
        raise SystemExit(f"source state missing: {state_path}")
    if not seq_path.exists():
        raise SystemExit(f"source sequence_state missing: {seq_path}")

    state = _read_json(state_path)
    sequence_state = _read_json(seq_path)

    _build_run_surface(dest_dir)

    dest_state = dest_dir / "state.json"
    shutil.copy2(state_path, dest_state)
    _write_text(dest_dir / "state.json.sha256", _sha256_file(dest_state) + "\n")
    if heavy_state_path.exists():
        dest_heavy_state = dest_dir / "state.heavy.json"
        shutil.copy2(heavy_state_path, dest_heavy_state)
        _write_text(dest_dir / "state.heavy.json.sha256", _sha256_file(dest_heavy_state) + "\n")
    _write_json(
        dest_dir / "sequence_state.json",
        _bootstrap_sequence_state(source_payload=sequence_state, dest_run_id=dest_run_id),
    )
    _write_json(
        dest_dir / "a1_inbox" / "sequence_state.json",
        _bootstrap_a1_inbox_sequence(
            source_run_id=source_run_id,
            source_path=source_dir / "a1_inbox" / "sequence_state.json",
            dest_run_id=dest_run_id,
            preserve=bool(args.preserve_a1_inbox_sequence),
        ),
    )
    seeded_driver_report = _bootstrap_driver_report(
        source_path=source_dir / "reports" / "a1_external_memo_batch_driver_report.json",
        dest_run_id=dest_run_id,
    )
    if seeded_driver_report is not None:
        _write_json(dest_dir / "reports" / "a1_external_memo_batch_driver_report.json", seeded_driver_report)

    counts = _state_counts(state)
    bootstrap_report = {
        "schema": "SEEDED_CONTINUATION_BOOTSTRAP_REPORT_v1",
        "source_run_id": source_run_id,
        "dest_run_id": dest_run_id,
        "preserved_surfaces": [
            "state.json",
            "state.heavy.json" if heavy_state_path.exists() else "",
            "sequence_state.json",
        ],
        "reset_surfaces": [
            "a1_inbox/*",
            "a1_sandbox/*",
            "reports/*",
            "b_reports/*",
            "sim/*",
            "tapes/*",
            "zip_packets/*",
            "logs/*",
        ],
        "preserve_a1_inbox_sequence": bool(args.preserve_a1_inbox_sequence),
        "preserved_driver_phase_state": bool(seeded_driver_report is not None),
        "state_counts": counts,
    }
    bootstrap_report["preserved_surfaces"] = [x for x in bootstrap_report["preserved_surfaces"] if x]
    _write_json(dest_dir / "reports" / "seeded_continuation_bootstrap_report.json", bootstrap_report)

    print(json.dumps(bootstrap_report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
