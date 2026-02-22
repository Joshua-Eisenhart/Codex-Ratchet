#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run(cmd: list[str]) -> tuple[int, str, str]:
    cp = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return cp.returncode, cp.stdout.strip(), cp.stderr.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic phase-gate producers in sequence.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--fixture-pack", required=True)
    parser.add_argument("--bootpack-hash", required=True)
    parser.add_argument("--min-export-blocks", type=int, default=1)
    parser.add_argument("--min-cycles", type=int, default=50)
    parser.add_argument("--min-positive-signals", type=int, default=1)
    parser.add_argument("--min-negative-signals", type=int, default=1)
    parser.add_argument("--min-kill-signals", type=int, default=1)
    parser.add_argument("--min-graveyard-records", type=int, default=1)
    parser.add_argument("--max-shard-bytes", type=int, default=5_000_000)
    parser.add_argument("--max-shard-lines", type=int, default=200_000)
    parser.add_argument("--max-run-bytes", type=int, default=200_000_000)
    parser.add_argument("--max-run-files", type=int, default=5_000)
    parser.add_argument("--use-expected-as-observed", action="store_true")
    parser.add_argument("--run-loop-health", action="store_true")
    parser.add_argument("--enforce-loop-health", action="store_true")
    parser.add_argument("--allow-loop-health-warn", action="store_true")
    parser.add_argument("--no-pending-stall-threshold", type=int, default=5)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    run_dir = str(Path(args.run_dir).resolve())

    conformance_cmd = [
        "python3",
        str(repo_root / "system_v3" / "tools" / "run_conformance_fixture_matrix.py"),
        "--run-dir",
        run_dir,
        "--fixture-pack",
        str(Path(args.fixture_pack).resolve()),
        "--bootpack-hash",
        args.bootpack_hash,
    ]
    if args.use_expected_as_observed:
        conformance_cmd.append("--use-expected-as-observed")

    release_cmd = [
        "python3",
        str(repo_root / "system_v3" / "tools" / "run_release_candidate_gate.py"),
        "--run-dir",
        run_dir,
    ]
    if args.enforce_loop_health:
        release_cmd.append("--require-loop-health")
    if args.allow_loop_health_warn:
        release_cmd.append("--allow-loop-health-warn")

    commands: list[tuple[str, list[str]]] = [
        (
            "P0_SPEC_LOCK",
            ["python3", str(repo_root / "system_v3" / "tools" / "run_spec_lock_gate.py"), "--run-dir", run_dir],
        ),
        (
            "P1_ARTIFACT_GRAMMAR",
            ["python3", str(repo_root / "system_v3" / "tools" / "run_artifact_grammar_gate.py"), "--run-dir", run_dir],
        ),
        ("P2_B_CONFORMANCE", conformance_cmd),
        (
            "P3_A0_COMPILER",
            [
                "python3",
                str(repo_root / "system_v3" / "tools" / "run_a0_compile_gate.py"),
                "--run-dir",
                run_dir,
                "--min-export-blocks",
                str(args.min_export_blocks),
            ],
        ),
        (
            "P4_A1_TO_B_SMOKE",
            [
                "python3",
                str(repo_root / "system_v3" / "tools" / "run_replay_pair_gate.py"),
                "--run-dir",
                run_dir,
                "--min-cycles",
                str(args.min_cycles),
            ],
        ),
        (
            "P5_SIM_EVIDENCE_LOOP_A",
            [
                "python3",
                str(repo_root / "system_v3" / "tools" / "run_evidence_ingest_gate.py"),
                "--run-dir",
                run_dir,
                "--min-positive-signals",
                str(args.min_positive_signals),
                "--min-negative-signals",
                str(args.min_negative_signals),
                "--min-kill-signals",
                str(args.min_kill_signals),
            ],
        ),
        (
            "P5_SIM_EVIDENCE_LOOP_B",
            [
                "python3",
                str(repo_root / "system_v3" / "tools" / "run_graveyard_integrity_gate.py"),
                "--run-dir",
                run_dir,
                "--min-graveyard-records",
                str(args.min_graveyard_records),
            ],
        ),
        (
            "P6_LONG_RUN_DISCIPLINE",
            [
                "python3",
                str(repo_root / "system_v3" / "tools" / "run_long_run_write_guard_gate.py"),
                "--run-dir",
                run_dir,
                "--max-shard-bytes",
                str(args.max_shard_bytes),
                "--max-shard-lines",
                str(args.max_shard_lines),
                "--max-run-bytes",
                str(args.max_run_bytes),
                "--max-run-files",
                str(args.max_run_files),
            ],
        ),
        (
            "PHASE_ADVANCE_PRE_P7",
            ["python3", str(repo_root / "system_v3" / "tools" / "advance_phase_gate.py"), "--run-dir", run_dir],
        ),
        (
            "P7_RELEASE_CANDIDATE",
            release_cmd,
        ),
        (
            "PHASE_ADVANCE_FINAL",
            ["python3", str(repo_root / "system_v3" / "tools" / "advance_phase_gate.py"), "--run-dir", run_dir],
        ),
    ]
    if args.run_loop_health or args.enforce_loop_health:
        loop_health_cmd = [
            "python3",
            str(repo_root / "system_v3" / "tools" / "run_loop_health_diagnostic.py"),
            "--run-dir",
            run_dir,
            "--no-pending-stall-threshold",
            str(args.no_pending_stall_threshold),
        ]
        insert_idx = next(
            idx for idx, (step_id, _) in enumerate(commands) if step_id == "PHASE_ADVANCE_PRE_P7"
        )
        commands.insert(insert_idx, ("LOOP_HEALTH_DIAGNOSTIC", loop_health_cmd))

    steps: list[dict] = []
    overall_ok = True
    for step_id, cmd in commands:
        rc, out, err = _run(cmd)
        step = {
            "step_id": step_id,
            "cmd": cmd,
            "return_code": rc,
            "stdout": out,
            "stderr": err,
            "status": "PASS" if rc == 0 else "FAIL",
        }
        steps.append(step)
        if rc != 0:
            overall_ok = False
            break

    report = {
        "schema": "PHASE_GATE_PIPELINE_REPORT_v1",
        "run_id": Path(run_dir).name,
        "status": "PASS" if overall_ok else "FAIL",
        "steps": steps,
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }

    report_path = Path(run_dir) / "reports" / "phase_gate_pipeline_report.json"
    _write_json(report_path, report)
    print(json.dumps({"status": report["status"], "report_path": str(report_path)}, sort_keys=True))
    return 0 if overall_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
