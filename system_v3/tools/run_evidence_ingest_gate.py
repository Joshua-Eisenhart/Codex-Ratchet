#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile


TEXT_SUFFIXES = {".txt", ".log", ".md", ".jsonl", ".json"}


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _status(flag: bool) -> str:
    return "PASS" if flag else "FAIL"


def _iter_sim_files(sim_root: Path) -> list[Path]:
    out: list[Path] = []
    if not sim_root.exists():
        return out
    for path in sorted(sim_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        out.append(path)
    return out


def _iter_sim_zip_packets(zip_root: Path) -> list[Path]:
    out: list[Path] = []
    if not zip_root.exists():
        return out
    for path in sorted(zip_root.glob("*_SIM_TO_A0_SIM_RESULT_ZIP.zip")):
        if path.is_file():
            out.append(path)
    return out


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_last_sim_event(run_dir: Path) -> dict:
    candidates = [run_dir / "logs" / "events.000.jsonl", run_dir / "events.jsonl"]
    for path in candidates:
        if not path.exists():
            continue
        rows = [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
        for line in reversed(rows):
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row.get("sim"), dict):
                return row
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate P5 evidence-ingest gate.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--min-positive-signals", type=int, default=1)
    parser.add_argument("--min-negative-signals", type=int, default=1)
    parser.add_argument("--min-kill-signals", type=int, default=1)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    sim_root = run_dir / "sim"
    zip_root = run_dir / "zip_packets"
    reports_dir = run_dir / "reports"

    sim_files = _iter_sim_files(sim_root)
    sim_zips = _iter_sim_zip_packets(zip_root)
    evidence_blocks = 0
    evidence_tokens: set[str] = set()
    positive_signal_count = 0
    negative_signal_count = 0
    kill_signal_count = 0

    for path in sim_files:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines:
            if line.strip() == "BEGIN SIM_EVIDENCE v1":
                evidence_blocks += 1
                continue
            if line.startswith("EVIDENCE_SIGNAL "):
                positive_signal_count += 1
                parts = line.split()
                if len(parts) >= 4:
                    evidence_tokens.add(parts[-1])
                upper = line.upper()
                if "NEG_" in upper or "NEGATIVE" in upper:
                    negative_signal_count += 1
                continue
            if line.startswith("KILL_SIGNAL "):
                kill_signal_count += 1

    for path in sim_zips:
        try:
            with zipfile.ZipFile(path, "r") as zf:
                lines = zf.read("SIM_EVIDENCE.txt").decode("utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for line in lines:
            if line.strip() == "BEGIN SIM_EVIDENCE v1":
                evidence_blocks += 1
                continue
            if line.startswith("EVIDENCE_SIGNAL "):
                positive_signal_count += 1
                parts = line.split()
                if len(parts) >= 4:
                    evidence_tokens.add(parts[-1])
                upper = line.upper()
                if "NEG_" in upper or "NEGATIVE" in upper:
                    negative_signal_count += 1
                continue
            if line.startswith("KILL_SIGNAL "):
                kill_signal_count += 1

    summary = _read_json(run_dir / "summary.json")
    last_sim_event = _read_last_sim_event(run_dir)
    sim_event = last_sim_event.get("sim", {}) if isinstance(last_sim_event.get("sim"), dict) else {}
    campaign_program_ids = [str(x).strip() for x in (summary.get("campaign_program_ids") or []) if str(x).strip()]
    suite_modes_seen = [str(x).strip() for x in (sim_event.get("suite_modes_seen") or []) if str(x).strip()]
    stages_seen = [str(x).strip() for x in (sim_event.get("stages_seen") or []) if str(x).strip()]

    checks = [
        {
            "check_id": "SIM_EVIDENCE_BLOCK_PRESENT",
            "status": _status(evidence_blocks >= 1),
            "detail": f"evidence_blocks={evidence_blocks}",
        },
        {
            "check_id": "POSITIVE_SIGNAL_MIN",
            "status": _status(positive_signal_count >= args.min_positive_signals),
            "detail": f"positive_signal_count={positive_signal_count} min_required={args.min_positive_signals}",
        },
        {
            "check_id": "NEGATIVE_SIGNAL_MIN",
            "status": _status(negative_signal_count >= args.min_negative_signals),
            "detail": f"negative_signal_count={negative_signal_count} min_required={args.min_negative_signals}",
        },
        {
            "check_id": "KILL_SIGNAL_MIN",
            "status": _status(kill_signal_count >= args.min_kill_signals),
            "detail": f"kill_signal_count={kill_signal_count} min_required={args.min_kill_signals}",
        },
        {
            "check_id": "SIM_CAMPAIGN_METADATA_PRESENT",
            "status": _status(bool(campaign_program_ids) or bool(sim_event.get("campaign_program_id"))),
            "detail": f"campaign_program_ids={campaign_program_ids or [str(sim_event.get('campaign_program_id', '')).strip()]}",
        },
        {
            "check_id": "SIM_STAGE_METADATA_PRESENT",
            "status": _status(len(stages_seen) >= 1),
            "detail": f"stages_seen={stages_seen}",
        },
        {
            "check_id": "SIM_SUITE_MODE_METADATA_PRESENT",
            "status": _status(len(suite_modes_seen) >= 1),
            "detail": f"suite_modes_seen={suite_modes_seen}",
        },
    ]

    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    report = {
        "schema": "EVIDENCE_INGEST_REPORT_v1",
        "run_id": run_dir.name,
        "status": status,
        "checks": checks,
        "sim_files_scanned": [str(p) for p in sim_files],
        "sim_file_count": len(sim_files),
        "sim_zip_packets_scanned": [str(p) for p in sim_zips],
        "sim_zip_packet_count": len(sim_zips),
        "evidence_block_count": evidence_blocks,
        "positive_signal_count": positive_signal_count,
        "negative_signal_count": negative_signal_count,
        "kill_signal_count": kill_signal_count,
        "ingested_evidence_tokens": sorted(evidence_tokens),
        "campaign_program_ids": campaign_program_ids,
        "stages_seen": stages_seen,
        "suite_modes_seen": suite_modes_seen,
        "errors": [] if status == "PASS" else ["EVIDENCE_GATE_UNSATISFIED"],
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }
    out_path = reports_dir / "evidence_ingest_report.json"
    _write_json(out_path, report)
    print(json.dumps({"status": status, "report_path": str(out_path)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
