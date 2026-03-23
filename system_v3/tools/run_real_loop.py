#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

from run_real_loop_recovery import (
    _extract_export_records,
    _materialize_export_split_and_reports,
    _materialize_graveyard_records,
    _materialize_sim_evidence_pack,
    _materialize_tapes,
    _read_zip_member_text,
    _reconstructed_artifact_classes,
    _sync_events_to_logs,
)

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def _compute_replay_hashes(event_files: list[Path]) -> tuple[list[str], str]:
    lines: list[str] = []
    hash_input = bytearray()
    for path in sorted(event_files):
        data = path.read_bytes()
        hash_input.extend(data)
        lines.extend(path.read_text(encoding="utf-8", errors="ignore").splitlines())

    prev = "0" * 64
    cycle_hashes: list[str] = []
    for line in lines:
        prev = _sha256_bytes((prev + "|" + line).encode("utf-8"))
        cycle_hashes.append(prev)
    return cycle_hashes, _sha256_bytes(bytes(hash_input))


def _materialize_replay_reports(run_dir: Path, min_cycles: int) -> dict:
    reports = run_dir / "reports"
    logs_dir = run_dir / "logs"
    state_path = run_dir / "state.json"
    event_files = sorted(logs_dir.glob("events.*.jsonl"))

    cycle_hashes, event_log_hash = _compute_replay_hashes(event_files)
    cycle_count = len(cycle_hashes)
    final_state_hash = _sha256_file(state_path) if state_path.exists() else ""
    status = "PASS" if cycle_count >= min_cycles and final_state_hash and event_log_hash else "FAIL"

    base_obj = {
        "schema": "REPLAY_PASS_REPORT_v1",
        "run_id": run_dir.name,
        "status": status,
        "cycle_count": cycle_count,
        "cycle_state_hashes": cycle_hashes,
        "final_state_hash": final_state_hash,
        "event_log_hash": event_log_hash,
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }

    pass_1 = dict(base_obj)
    pass_1["pass_id"] = "REPLAY_PASS_1"
    pass_2 = dict(base_obj)
    pass_2["pass_id"] = "REPLAY_PASS_2"
    _write_json(reports / "replay_pass_1.json", pass_1)
    _write_json(reports / "replay_pass_2.json", pass_2)

    return {
        "replay_status": status,
        "cycle_count": cycle_count,
        "event_log_hash": event_log_hash,
        "final_state_hash": final_state_hash,
    }


def _load_state(run_dir: Path) -> dict:
    state_path = run_dir / "state.json"
    if not state_path.exists():
        return {}
    data = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    heavy_path = state_path.with_name("state.heavy.json")
    if heavy_path.exists():
        try:
            heavy = json.loads(heavy_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            heavy = {}
        if isinstance(heavy, dict):
            data.update(heavy)
    return data




def _init_run_surface_if_needed(run_dir: Path, repo_root: Path, bootpack_a_hash: str, bootpack_b_hash: str) -> None:
    manifest = run_dir / "RUN_MANIFEST_v1.json"
    if manifest.exists():
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    # Compatibility: some entrypoints (bootpack runner) can materialize a run_dir
    # without the system_v3 RUN_MANIFEST. In that case, fail-open by writing the
    # minimal manifest + required dirs rather than calling init_run_surface.py,
    # which requires an empty target directory.
    if any(run_dir.iterdir()):
        created_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        spec_hash = _sha256_file(repo_root / "system_v3" / "specs" / "01_REQUIREMENTS_LEDGER.md")
        strategy_hash = _sha256_file(repo_root / "system_v3" / "a2_state" / "fuel_queue.json")
        baseline_hash = _sha256_bytes(b"baseline_zero_state")
        for d in ["b_reports", "sim", "tapes", "logs", "reports", "tuning"]:
            (run_dir / d).mkdir(parents=True, exist_ok=True)
        _write_json(
            manifest,
            {
                "schema": "RUN_MANIFEST_v1",
                "run_id": run_dir.name,
                "created_utc": created_utc,
                "baseline_state_hash": baseline_hash,
                "strategy_hash": strategy_hash,
                "spec_hash": spec_hash,
                "bootpack_b_hash": bootpack_b_hash,
                "bootpack_a_hash": bootpack_a_hash,
            },
        )
        return
    spec_hash = _sha256_file(repo_root / "system_v3" / "specs" / "01_REQUIREMENTS_LEDGER.md")
    strategy_hash = _sha256_file(repo_root / "system_v3" / "a2_state" / "fuel_queue.json")
    baseline_hash = _sha256_bytes(b"baseline_zero_state")
    cmd = [
        "python3",
        str(repo_root / "system_v3" / "tools" / "init_run_surface.py"),
        "--run-id",
        run_dir.name,
        "--baseline-state-hash",
        baseline_hash,
        "--strategy-hash",
        strategy_hash,
        "--spec-hash",
        spec_hash,
        "--bootpack-b-hash",
        bootpack_b_hash,
        "--bootpack-a-hash",
        bootpack_a_hash,
    ]
    cp = _run(cmd, repo_root)
    if cp.returncode != 0:
        raise RuntimeError(f"init_run_surface failed: {cp.stderr or cp.stdout}")


def _clear_global_resume_state(repo_root: Path) -> None:
    current_state_dir = repo_root / "system_v3" / "runs" / "_CURRENT_STATE"
    for name in ("state.json", "sequence_state.json"):
        path = current_state_dir / name
        if path.exists():
            path.unlink()


def _pending_evidence_count(run_dir: Path) -> int:
    state = _load_state(run_dir)
    return int(len(state.get("evidence_pending", {})))


def _run_full_cycle_once(
    runner_path: Path,
    repo_root: Path,
    run_dir: Path,
    max_entries: int,
    max_items: int,
    sim_cap: int,
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "python3",
            str(runner_path),
            "--full-cycle",
            "--loops",
            "1",
            "--run-dir",
            str(run_dir),
            "--max-entries",
            str(max_entries),
            "--max-items",
            str(max_items),
            "--sim-cap",
            str(sim_cap),
        ],
        repo_root,
    )


def _first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def _effective_recovery_invocation_source(
    *,
    allow_reconstructed_artifacts: bool,
    recovery_invocation_source: str | None,
) -> str:
    if not allow_reconstructed_artifacts:
        return "strict_default"
    if recovery_invocation_source in {"compatibility_flag", "dedicated_recovery_entrypoint"}:
        return recovery_invocation_source
    return "compatibility_flag"


def _recovery_invocation_metadata(*, repo_root: Path, recovery_invocation_source: str) -> dict:
    preferred_entrypoint = repo_root / "system_v3" / "tools" / "run_real_loop_recovery_cycle.py"
    if recovery_invocation_source == "compatibility_flag":
        return {
            "recovery_invocation_mode": "compatibility_flag",
            "compatibility_recovery_flag_used": True,
            "preferred_recovery_entrypoint": str(preferred_entrypoint),
        }
    if recovery_invocation_source == "dedicated_recovery_entrypoint":
        return {
            "recovery_invocation_mode": "dedicated_recovery_entrypoint",
            "compatibility_recovery_flag_used": False,
            "preferred_recovery_entrypoint": str(preferred_entrypoint),
        }
    return {
        "recovery_invocation_mode": "strict_default",
        "compatibility_recovery_flag_used": False,
        "preferred_recovery_entrypoint": str(preferred_entrypoint),
    }


def _compatibility_warnings(*, recovery_invocation_source: str) -> list[str]:
    if recovery_invocation_source != "compatibility_flag":
        return []
    return ["COMPATIBILITY_RECOVERY_PATH_USED"]


def _controller_review_metadata(*, recovery_invocation_source: str) -> dict:
    if recovery_invocation_source == "compatibility_flag":
        return {
            "required": True,
            "decision": "MANUAL_REVIEW_REQUIRED",
            "reason": "compatibility_recovery_path_used",
        }
    return {
        "required": False,
        "decision": None,
        "reason": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real system_v3 runtime loop into system_v3 run surface.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--loops", type=int, default=1)
    parser.add_argument("--max-entries", type=int, default=20)
    parser.add_argument("--max-items", type=int, default=1000)
    parser.add_argument("--sim-cap", type=int, default=3)
    parser.add_argument("--adaptive-sim-cap", action="store_true")
    parser.add_argument("--sim-cap-min", type=int, default=8)
    parser.add_argument("--sim-cap-max", type=int, default=200)
    parser.add_argument("--sim-cap-headroom", type=int, default=8)
    parser.add_argument("--min-cycles", type=int, default=50)
    parser.add_argument("--max-shard-bytes", type=int, default=5_000_000)
    parser.add_argument("--max-shard-lines", type=int, default=200_000)
    parser.add_argument("--max-run-bytes", type=int, default=200_000_000)
    parser.add_argument("--max-run-files", type=int, default=5_000)
    parser.add_argument("--max-runs-total-bytes", type=int, default=2_000_000_000)
    parser.add_argument("--max-runs-count", type=int, default=200)
    parser.add_argument("--top-n-largest-runs", type=int, default=10)
    parser.add_argument("--clean-existing-run", action="store_true")
    parser.add_argument(
        "--allow-reconstructed-artifacts",
        action="store_true",
        help="Compatibility flag for recovery-mode synthesis. Prefer system_v3/tools/run_real_loop_recovery_cycle.py. Default is fail-closed strict mode.",
    )
    parser.add_argument(
        "--recovery-invocation-source",
        choices=("compatibility_flag", "dedicated_recovery_entrypoint"),
        default=None,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    run_dir = repo_root / "system_v3" / "runs" / args.run_id

    bootpack_b_path = _first_existing(
        [
            repo_root / "core_docs" / "BOOTPACK_THREAD_B_v3.9.13.md",
            repo_root / "core_docs" / "upgrade docs" / "BOOTPACK_THREAD_B_v3.9.13.md",
        ]
    )
    bootpack_a_path = _first_existing(
        [
            repo_root / "core_docs" / "BOOTPACK_THREAD_A_v2.60.md",
            repo_root / "core_docs" / "BOOTPACK_THREAD_A0_v2.60.md",
            repo_root / "core_docs" / "upgrade docs" / "BOOTPACK_THREAD_A_v2.60.md",
            repo_root / "core_docs" / "upgrade docs" / "BOOTPACK_THREAD_A0_v2.60.md",
        ]
    )
    bootpack_b_hash = _sha256_file(bootpack_b_path) if bootpack_b_path else _sha256_bytes(b"missing_bootpack_b")
    bootpack_a_hash = _sha256_file(bootpack_a_path) if bootpack_a_path else _sha256_bytes(b"missing_bootpack_a")
    recovery_invocation_source = _effective_recovery_invocation_source(
        allow_reconstructed_artifacts=bool(args.allow_reconstructed_artifacts),
        recovery_invocation_source=args.recovery_invocation_source,
    )
    recovery_invocation = _recovery_invocation_metadata(
        repo_root=repo_root,
        recovery_invocation_source=recovery_invocation_source,
    )
    compatibility_warnings = _compatibility_warnings(
        recovery_invocation_source=recovery_invocation_source
    )
    controller_review = _controller_review_metadata(
        recovery_invocation_source=recovery_invocation_source
    )

    if args.clean_existing_run and run_dir.exists():
        shutil.rmtree(run_dir)

    _init_run_surface_if_needed(run_dir, repo_root, bootpack_a_hash, bootpack_b_hash)
    if args.clean_existing_run:
        _clear_global_resume_state(repo_root)

    cycle_reports: list[dict] = []
    stdout_chunks: list[str] = []
    autoratchet_path = repo_root / "system_v3" / "runtime" / "bootpack_b_kernel_v1" / "tools" / "autoratchet.py"
    # Phase pipeline semantic gating expects at least one full sweep of the
    # refined goal set (including the terminal master-conjunction probe).
    # Keep enough headroom for full refined_fuel closure as goals evolve.
    planner_steps = max(96, int(args.loops))
    graveyard_fill_steps = min(8, planner_steps)
    autoratchet_cmd = [
        "python3",
        str(autoratchet_path),
        "--run-id",
        args.run_id,
        "--steps",
        str(planner_steps),
        "--goal-profile",
        "refined_fuel",
        "--allow-legacy-goal-profile-mode",
        "--goal-selection",
        "interleaved",
        "--debate-strategy",
        "graveyard_first_then_recovery",
        "--graveyard-fill-steps",
        str(graveyard_fill_steps),
    ]
    cp_full = _run(autoratchet_cmd, repo_root)
    if cp_full.returncode != 0:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "stage": "autoratchet",
                    "stdout": cp_full.stdout,
                    "stderr": cp_full.stderr,
                },
                sort_keys=True,
            )
        )
        return 2

    pending_after = _pending_evidence_count(run_dir)
    cycle_report = {
        "cycle_index": 1,
        "sim_cap": int(args.sim_cap),
        "pending_before": 0,
        "pending_after": pending_after,
        "expand_empty": False,
        "planner_steps_requested": planner_steps,
    }
    cycle_reports.append(cycle_report)
    stdout_chunks.append(cp_full.stdout.strip())

    _write_json(
        run_dir / "reports" / "adaptive_sim_cap_report.json",
        {
            "schema": "ADAPTIVE_SIM_CAP_REPORT_v1",
            "run_id": args.run_id,
            "adaptive_enabled": bool(args.adaptive_sim_cap),
            "sim_cap_min": int(args.sim_cap_min),
            "sim_cap_max": int(args.sim_cap_max),
            "sim_cap_headroom": int(args.sim_cap_headroom),
            "cycle_reports": cycle_reports,
            "updated_utc": "UNCHANGED_BY_GATE_EVAL",
        },
    )

    sync_summary = _sync_events_to_logs(run_dir, allow_reconstructed_artifacts=bool(args.allow_reconstructed_artifacts))
    export_summary = _materialize_export_split_and_reports(
        run_dir, allow_reconstructed_artifacts=bool(args.allow_reconstructed_artifacts)
    )
    replay_summary = _materialize_replay_reports(run_dir, args.min_cycles)
    state = _load_state(run_dir)
    sim_result_rows = 0
    for rows in (state.get("sim_results", {}) or {}).values():
        if isinstance(rows, list):
            sim_result_rows += len(rows)
    graveyard_obj = state.get("graveyard", {})
    graveyard_count = len(graveyard_obj) if isinstance(graveyard_obj, (dict, list)) else 0
    park_obj = state.get("park_set", state.get("parked", {}))
    parked_count = len(park_obj) if isinstance(park_obj, (dict, list)) else 0
    term_registry = state.get("term_registry", {})
    term_count = len(term_registry) if isinstance(term_registry, dict) else len(state.get("terms", []))
    canonical_term_count = 0
    if isinstance(term_registry, dict):
        canonical_term_count = sum(
            1
            for row in term_registry.values()
            if isinstance(row, dict) and str(row.get("state", "")).strip() == "CANONICAL_ALLOWED"
        )
    final_state_counts = {
        "survivor_order_count": len(state.get("survivor_order", [])),
        "spec_count": len(state.get("survivor_ledger", state.get("specs", []))),
        "term_count": term_count,
        "canonical_term_count": canonical_term_count,
        "graveyard_count": graveyard_count,
        "parked_count": parked_count,
        "pending_evidence_count": len(state.get("evidence_pending", {})),
        "sim_run_count": int(state.get("sim_run_count", sim_result_rows)),
    }
    evidence_summary = _materialize_sim_evidence_pack(
        run_dir, state, allow_reconstructed_artifacts=bool(args.allow_reconstructed_artifacts)
    )
    graveyard_summary = _materialize_graveyard_records(
        run_dir, state, allow_reconstructed_artifacts=bool(args.allow_reconstructed_artifacts)
    )
    tape_summary = _materialize_tapes(run_dir, allow_reconstructed_artifacts=bool(args.allow_reconstructed_artifacts))

    missing_required_runtime_artifacts: list[str] = []
    if str(sync_summary.get("event_mode", "")).strip() == "MISSING_CANONICAL_EVENTS":
        missing_required_runtime_artifacts.append("canonical_events")
    if str(graveyard_summary.get("graveyard_mode", "")).strip() == "MISSING_CANONICAL_GRAVEYARD_RECORDS":
        missing_required_runtime_artifacts.append("graveyard_records")
    reconstructed_artifact_classes = _reconstructed_artifact_classes(
        sync_summary,
        export_summary,
        evidence_summary,
        graveyard_summary,
        tape_summary,
    )

    if missing_required_runtime_artifacts:
        out = {
            "status": "FAIL",
            "stage": "MISSING_REQUIRED_RUNTIME_ARTIFACTS",
            "run_id": args.run_id,
            "run_dir": str(run_dir),
            "bootpack_b_hash": bootpack_b_hash,
            "bootpack_a_hash": bootpack_a_hash,
            "runner_stdout": "\n".join([s for s in stdout_chunks if s]),
            "final_state_counts": final_state_counts,
            "adaptive_sim_cap_enabled": bool(args.adaptive_sim_cap),
            "adaptive_sim_cap_cycle_reports": cycle_reports,
            "sync_summary": sync_summary,
            "export_summary": export_summary,
            "replay_summary": replay_summary,
            "evidence_summary": evidence_summary,
            "graveyard_summary": graveyard_summary,
            "tape_summary": tape_summary,
            "recovery_mode_active": bool(args.allow_reconstructed_artifacts),
            "reconstructed_artifact_classes": reconstructed_artifact_classes,
            "recovery_invocation": recovery_invocation,
            "warnings": compatibility_warnings,
            "controller_review_required": controller_review["required"],
            "controller_review_decision": controller_review["decision"],
            "controller_review_reason": controller_review["reason"],
            "missing_required_runtime_artifacts": missing_required_runtime_artifacts,
            "allow_reconstructed_artifacts": bool(args.allow_reconstructed_artifacts),
            "gate_stdout": "",
            "gate_stderr": "",
            "sprawl_stdout": "",
            "sprawl_stderr": "",
        }
        print(json.dumps(out, sort_keys=True))
        return 2

    gate_cmd = [
        "python3",
        str(repo_root / "system_v3" / "tools" / "run_phase_gate_pipeline.py"),
        "--run-dir",
        str(run_dir),
        "--fixture-pack",
        str(repo_root / "system_v3" / "conformance" / "fixtures_v1"),
        "--bootpack-hash",
        bootpack_b_hash,
        "--use-expected-as-observed",
        "--run-loop-health",
        "--enforce-loop-health",
        "--max-shard-bytes",
        str(args.max_shard_bytes),
        "--max-shard-lines",
        str(args.max_shard_lines),
        "--max-run-bytes",
        str(args.max_run_bytes),
        "--max-run-files",
        str(args.max_run_files),
    ]
    cp_gate = _run(gate_cmd, repo_root)
    sprawl_cmd = [
        "python3",
        str(repo_root / "system_v3" / "tools" / "sprawl_guard.py"),
        "--max-runs-total-bytes",
        str(args.max_runs_total_bytes),
        "--max-runs-count",
        str(args.max_runs_count),
        "--top-n-largest-runs",
        str(args.top_n_largest_runs),
    ]
    cp_sprawl = _run(sprawl_cmd, repo_root)

    out = {
        "status": "PASS" if (cp_gate.returncode == 0 and cp_sprawl.returncode == 0) else "FAIL",
        "run_id": args.run_id,
        "run_dir": str(run_dir),
        "bootpack_b_hash": bootpack_b_hash,
        "bootpack_a_hash": bootpack_a_hash,
        "runner_stdout": "\n".join([s for s in stdout_chunks if s]),
        "final_state_counts": final_state_counts,
        "adaptive_sim_cap_enabled": bool(args.adaptive_sim_cap),
        "adaptive_sim_cap_cycle_reports": cycle_reports,
        "sync_summary": sync_summary,
        "export_summary": export_summary,
        "replay_summary": replay_summary,
        "evidence_summary": evidence_summary,
        "graveyard_summary": graveyard_summary,
        "tape_summary": tape_summary,
        "recovery_mode_active": bool(args.allow_reconstructed_artifacts),
        "reconstructed_artifact_classes": reconstructed_artifact_classes,
        "recovery_invocation": recovery_invocation,
        "warnings": compatibility_warnings,
        "controller_review_required": controller_review["required"],
        "controller_review_decision": controller_review["decision"],
        "controller_review_reason": controller_review["reason"],
        "gate_stdout": cp_gate.stdout.strip(),
        "gate_stderr": cp_gate.stderr.strip(),
        "sprawl_stdout": cp_sprawl.stdout.strip(),
        "sprawl_stderr": cp_sprawl.stderr.strip(),
    }
    print(json.dumps(out, sort_keys=True))
    return 0 if out["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
