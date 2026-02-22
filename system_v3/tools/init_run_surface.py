#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _require_hex64(name: str, value: str) -> str:
    if not HEX64_RE.fullmatch(value):
        raise ValueError(f"{name} must be 64 lowercase hex characters")
    return value


def _require_run_id(value: str) -> str:
    if not RUN_ID_RE.fullmatch(value):
        raise ValueError("run_id contains invalid characters")
    return value


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json_template(path: Path, mapping: dict[str, str]) -> dict:
    raw = _read_text(path)
    for key, value in mapping.items():
        raw = raw.replace(key, value)
    data = json.loads(raw)
    return data


def _write_json(path: Path, obj: dict) -> None:
    _write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize deterministic run surface from templates.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--baseline-state-hash", required=True)
    parser.add_argument("--strategy-hash", required=True)
    parser.add_argument("--spec-hash", required=True)
    parser.add_argument("--bootpack-b-hash", required=True)
    parser.add_argument("--bootpack-a-hash", required=True)
    args = parser.parse_args()

    run_id = _require_run_id(args.run_id)
    baseline_state_hash = _require_hex64("baseline_state_hash", args.baseline_state_hash)
    strategy_hash = _require_hex64("strategy_hash", args.strategy_hash)
    spec_hash = _require_hex64("spec_hash", args.spec_hash)
    bootpack_b_hash = _require_hex64("bootpack_b_hash", args.bootpack_b_hash)
    bootpack_a_hash = _require_hex64("bootpack_a_hash", args.bootpack_a_hash)

    repo_root = Path(__file__).resolve().parents[2]
    templates_root = repo_root / "system_v3" / "runs" / "_run_templates_v1"
    if not templates_root.exists():
        raise FileNotFoundError(f"missing templates root: {templates_root}")

    runs_root = repo_root / "system_v3" / "runs"
    run_root = runs_root / run_id

    if run_root.exists():
        if any(run_root.iterdir()):
            raise FileExistsError(f"target run directory exists and is non-empty: {run_root}")
    else:
        run_root.mkdir(parents=True, exist_ok=False)

    created_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    mapping = {
        "__RUN_ID__": run_id,
        "__CREATED_UTC__": created_utc,
        "__BASELINE_STATE_HASH__": baseline_state_hash,
        "__STRATEGY_HASH__": strategy_hash,
        "__SPEC_HASH__": spec_hash,
        "__BOOTPACK_B_HASH__": bootpack_b_hash,
        "__BOOTPACK_A_HASH__": bootpack_a_hash,
    }

    # Required deterministic directory surface.
    for d in [
        "outbox",
        "b_reports",
        "snapshots",
        "sim",
        "tapes",
        "logs",
        "reports",
        "tuning",
    ]:
        (run_root / d).mkdir(parents=True, exist_ok=True)

    # Materialize manifest.
    manifest_template = templates_root / "RUN_MANIFEST_v1.template.json"
    manifest = _load_json_template(manifest_template, mapping)
    _write_json(run_root / "RUN_MANIFEST_v1.json", manifest)

    # Materialize report templates.
    report_templates = {
        "spec_lock_report.template.json": "spec_lock_report.json",
        "artifact_grammar_report.template.json": "artifact_grammar_report.json",
        "phase_transition_report.template.json": "phase_transition_report.json",
        "conformance_report.template.json": "conformance_report.json",
        "a0_compile_report.template.json": "a0_compile_report.json",
        "replay_pass_1.template.json": "replay_pass_1.json",
        "replay_pass_2.template.json": "replay_pass_2.json",
        "replay_pair_report.template.json": "replay_pair_report.json",
        "evidence_ingest_report.template.json": "evidence_ingest_report.json",
        "graveyard_integrity_report.template.json": "graveyard_integrity_report.json",
        "long_run_write_guard_report.template.json": "long_run_write_guard_report.json",
        "loop_health_diagnostic.template.json": "loop_health_diagnostic.json",
        "release_checklist_v1.template.json": "release_checklist_v1.json",
    }
    for src_name, dst_name in sorted(report_templates.items()):
        src = templates_root / "reports" / src_name
        if not src.exists():
            raise FileNotFoundError(f"missing template: {src}")
        obj = _load_json_template(src, mapping)
        _write_json(run_root / "reports" / dst_name, obj)

    # Deterministic empty tape/log shards.
    for dst in [
        run_root / "tapes" / "export_tape.000.jsonl",
        run_root / "tapes" / "campaign_tape.000.jsonl",
        run_root / "logs" / "events.000.jsonl",
    ]:
        _write_text(dst, "")

    print(
        json.dumps(
            {
                "run_id": run_id,
                "run_root": str(run_root),
                "status": "INITIALIZED",
                "template_version": "RUN_TEMPLATES_v1",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
