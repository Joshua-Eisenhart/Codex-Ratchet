#!/usr/bin/env python3
"""A1 wiggle autopilot (deterministic)

This is the missing "basic batches that actually move the ratchet" path when
you don't want to rely on a chat model to author a full A1_STRATEGY_v1.

What it does
------------
- Creates (or resumes) a normal packet-mode run under system_v3/runs/<RUN_ID>/
- For each cycle:
  1) reads the current run state.json
  2) generates ONE inbound A1 packet using the bootpack deterministic planner
     (a1_adaptive_ratchet_planner.py)
  3) runs exactly one kernel step (a1_a0_b_sim_runner.py --steps 1)

Why this matters
----------------
The "ratchet" only moves when SIMs produce EVIDENCE_SIGNAL and/or KILL_SIGNAL,
which changes evidence_tokens, term_registry states, and the graveyard.

This tool forces that evolutionary loop to actually run (branch → test →
kill/canonize → repeat), without depending on Codex to understand a giant prompt.

Notes
-----
- This tool is intentionally deterministic given the same state.json and
  sequence number.
- It uses the *existing* bootpack planner (tools/a1_adaptive_ratchet_planner.py)
  so the strategy schema exactly matches the known-good emitter.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"

BOOTPACK = SYSTEM_V3 / "runtime" / "bootpack_b_kernel_v1"
RUNNER = BOOTPACK / "a1_a0_b_sim_runner.py"
PLANNER = BOOTPACK / "tools" / "a1_adaptive_ratchet_planner.py"
BUILD_PROJECT_SAVE_DOC = SYSTEM_V3 / "tools" / "build_project_save_doc.py"
AUDIT_PROJECT_SAVE_DOC = SYSTEM_V3 / "tools" / "audit_project_save_doc.py"


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    if path.name == "state.json":
        heavy_path = path.with_name("state.heavy.json")
        if heavy_path.exists():
            try:
                heavy = json.loads(heavy_path.read_text(encoding="utf-8"))
            except Exception:
                heavy = {}
            if isinstance(heavy, dict):
                data.update(heavy)
    return data


def _next_inbox_sequence(run_dir: Path, run_id: str) -> int:
    """Next expected inbound A1 packet sequence.

    Mirrors logic from tools/codex_json_to_a1_strategy_packet_zip.py
    but kept local to avoid import coupling.
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
            if last >= 0:
                return last + 1

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
            max_seen = max(max_seen, seq)

    return (max_seen + 1) if max_seen > 0 else 1


def _state_metrics(state: dict) -> dict:
    term_registry = state.get("term_registry", {}) if isinstance(state.get("term_registry", {}), dict) else {}
    canonical_term_count = sum(
        1
        for row in term_registry.values()
        if isinstance(row, dict) and str(row.get("state", "")) == "CANONICAL_ALLOWED"
    )
    return {
        "survivor_count": len(state.get("survivor_ledger", {}) or {}),
        "park_count": len(state.get("park_set", {}) or {}),
        "graveyard_count": len(state.get("graveyard", {}) or {}),
        "evidence_token_count": len(state.get("evidence_tokens", []) or []),
        "evidence_pending_count": len(state.get("evidence_pending", {}) or {}),
        "term_registry_count": len(term_registry),
        "canonical_term_count": canonical_term_count,
        "sim_registry_count": len(state.get("sim_registry", {}) or {}),
    }


def _dir_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for item in path.rglob("*"):
        if not item.is_file():
            continue
        try:
            total += item.stat().st_size
        except OSError:
            continue
    return int(total)


def _meaningful_progress(before: dict, after: dict) -> list[str]:
    progress_keys: list[str] = []
    for key in (
        "canonical_term_count",
        "evidence_token_count",
        "graveyard_count",
        "survivor_count",
        "sim_registry_count",
        "term_registry_count",
    ):
        before_value = int(before.get(key, 0) or 0)
        after_value = int(after.get(key, 0) or 0)
        if after_value > before_value:
            progress_keys.append(key)
    for key, progress_name in (
        ("park_count", "park_count_reduced"),
        ("evidence_pending_count", "evidence_pending_count_reduced"),
    ):
        before_value = int(before.get(key, 0) or 0)
        after_value = int(after.get(key, 0) or 0)
        if after_value < before_value:
            progress_keys.append(progress_name)
    return progress_keys


def _build_project_save_checkpoint(*, run_dir: Path, sequence: int) -> dict:
    checkpoint_dir = run_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    save_doc_path = checkpoint_dir / f"{int(sequence):06d}__PROJECT_SAVE_DOC_v1.json"
    audit_path = checkpoint_dir / f"{int(sequence):06d}__AUDIT_PROJECT_SAVE_DOC_REPORT_v1.json"

    build_proc = _run(
        [
            "python3",
            str(BUILD_PROJECT_SAVE_DOC),
            "--repo-root",
            str(REPO),
            "--run-dir",
            str(run_dir),
            "--out-json",
            str(save_doc_path),
        ],
        cwd=REPO,
    )
    if build_proc.returncode != 0 or not save_doc_path.exists():
        return {
            "checkpoint_status": "BUILD_FAILED",
            "project_save_doc_path": str(save_doc_path),
            "checkpoint_failure_summary": (build_proc.stderr or build_proc.stdout or "").strip()[-400:],
        }

    audit_proc = _run(
        [
            "python3",
            str(AUDIT_PROJECT_SAVE_DOC),
            "--doc-json",
            str(save_doc_path),
            "--out-json",
            str(audit_path),
        ],
        cwd=REPO,
    )
    audit_status = "PASS" if audit_proc.returncode == 0 and audit_path.exists() else "AUDIT_FAILED"
    out = {
        "checkpoint_status": audit_status,
        "project_save_doc_path": str(save_doc_path),
        "project_save_doc_audit_path": str(audit_path),
    }
    if audit_status != "PASS":
        out["checkpoint_failure_summary"] = (audit_proc.stderr or audit_proc.stdout or "").strip()[-400:]
    return out


def _append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _jsonl_line_size(payload: dict) -> int:
    return len((json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"))


def _apply_cycle_guards(
    row: dict,
    *,
    run_dir_bytes: int,
    checkpoint_status: str,
    stall_streak: int,
    stall_limit_cycles: int,
    max_run_bytes: int,
) -> tuple[dict, list[str]]:
    out = dict(row)
    out["run_dir_bytes"] = int(run_dir_bytes)
    stop_reasons: list[str] = []

    if checkpoint_status and checkpoint_status != "PASS":
        stop_reasons.append("PROJECT_SAVE_CHECKPOINT_FAILED")

    if stall_limit_cycles > 0 and stall_streak >= stall_limit_cycles:
        stop_reasons.append("STALL_LIMIT_REACHED")
        out["stall_limit_cycles"] = int(stall_limit_cycles)

    def projected_bytes(candidate_stop_reasons: list[str]) -> int:
        preview = dict(out)
        if candidate_stop_reasons:
            preview["autopilot_stop_reason"] = str(candidate_stop_reasons[0])
            if len(candidate_stop_reasons) > 1:
                preview["autopilot_stop_reasons"] = list(candidate_stop_reasons)
        if "RUN_DIR_BYTES_LIMIT" in candidate_stop_reasons:
            preview["max_run_bytes"] = int(max_run_bytes)
        return int(run_dir_bytes) + _jsonl_line_size(preview)

    projected_run_dir_bytes = projected_bytes(stop_reasons)
    if max_run_bytes > 0 and projected_run_dir_bytes > max_run_bytes:
        stop_reasons.append("RUN_DIR_BYTES_LIMIT")
        out["max_run_bytes"] = int(max_run_bytes)
        projected_run_dir_bytes = projected_bytes(stop_reasons)

    out["projected_run_dir_bytes"] = int(projected_run_dir_bytes)
    if stop_reasons:
        out["autopilot_stop_reason"] = str(stop_reasons[0])
        if len(stop_reasons) > 1:
            out["autopilot_stop_reasons"] = list(stop_reasons)
    return out, stop_reasons


def _ensure_run_exists(run_id: str, runs_root: Path, *, clean: bool) -> Path:
    """Ensure run_dir exists and contains state.json.

    If missing, invoke the runner for 1 step (packet mode). If the inbox is
    empty (expected), the runner will stop with A1_NEEDS_EXTERNAL_STRATEGY but
    still writes state.json and the A0->A1 request packet.
    """

    run_dir = runs_root / run_id
    state_path = run_dir / "state.json"
    if state_path.exists() and not clean:
        return run_dir

    cmd = [
        "python3",
        str(RUNNER),
        "--a1-source",
        "packet",
        "--run-id",
        run_id,
        "--runs-root",
        str(runs_root),
        "--steps",
        "1",
    ]
    if clean:
        cmd.append("--clean")

    proc = _run(cmd, cwd=BOOTPACK)
    if proc.returncode != 0:
        raise SystemExit("failed to initialize run:\n" + proc.stdout + "\n--- STDERR ---\n" + proc.stderr)

    if not state_path.exists():
        raise SystemExit(f"runner did not write state.json at: {state_path}")

    return run_dir


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Deterministic A1 wiggle autopilot: repeatedly generate inbound A1 packets "
            "(via a1_adaptive_ratchet_planner.py) and run one packet step at a time."
        )
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT))
    ap.add_argument("--cycles", type=int, default=10, help="How many (packet+step) cycles to execute.")
    ap.add_argument(
        "--stall-limit-cycles",
        type=int,
        default=0,
        help="Stop after this many consecutive cycles with no meaningful ratchet progress. 0 disables.",
    )
    ap.add_argument(
        "--max-run-bytes",
        type=int,
        default=0,
        help="Hard stop if the run directory exceeds this many bytes. 0 disables.",
    )
    ap.add_argument(
        "--project-save-every-cycles",
        type=int,
        default=0,
        help="Emit and audit PROJECT_SAVE_DOC checkpoints every N cycles. 0 disables.",
    )
    ap.add_argument(
        "--goal-profile",
        choices=["core", "extended", "physics", "toolkit", "refined_fuel"],
        default="refined_fuel",
        help="Goal set used by the deterministic planner.",
    )
    ap.add_argument(
        "--goal-selection",
        choices=["interleaved", "closure_first"],
        default="interleaved",
        help="Planner goal ordering policy.",
    )
    ap.add_argument(
        "--debate-mode",
        choices=["balanced", "graveyard_first", "graveyard_recovery"],
        default="graveyard_recovery",
        help="Planner branching policy (controls adversarial surface + rescue usage).",
    )
    ap.add_argument("--clean", action="store_true", help="Start a fresh run (delete existing run dir).")
    ap.add_argument("--quiet", action="store_true", help="Only print final JSON (default prints per cycle).")
    ap.add_argument(
        "--retain-diagnostics",
        action="store_true",
        help="Write duplicate human-readable artifacts (reports/, outbox/, a1_strategies/, soak_report.md).",
    )
    ap.add_argument(
        "--retain-snapshots",
        action="store_true",
        help="Also write snapshot_*.txt to runs/<RUN_ID>/snapshots (duplicates B snapshot ZIP payload).",
    )
    ap.add_argument(
        "--retain-sim-text",
        action="store_true",
        help="Also write sim_evidence_*.txt to runs/<RUN_ID>/sim (duplicates SIM ZIP payload).",
    )
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    if not run_id:
        raise SystemExit("missing run-id")

    cycles = max(0, int(args.cycles))
    runs_root = Path(args.runs_root).expanduser().resolve()

    run_dir = _ensure_run_exists(run_id, runs_root, clean=bool(args.clean))
    inbox = run_dir / "a1_inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    autopilot_log_path = run_dir / "logs" / "a1_wiggle_autopilot.000.jsonl"

    cycle_rows: list[dict] = []
    stall_limit_cycles = max(0, int(args.stall_limit_cycles))
    max_run_bytes = max(0, int(args.max_run_bytes))
    project_save_every_cycles = max(0, int(args.project_save_every_cycles))
    stall_streak = 0
    autopilot_stop_reason = ""
    autopilot_stop_reasons: list[str] = []
    cycles_with_progress = 0
    cycles_without_progress = 0
    checkpoint_pass_count = 0
    checkpoint_fail_count = 0
    max_run_dir_bytes_seen = 0

    for _ in range(cycles):
        state_path = run_dir / "state.json"
        state = _read_json(state_path)
        before = _state_metrics(state)

        seq = _next_inbox_sequence(run_dir, run_id)
        out_zip = inbox / f"{seq:06d}_A1_TO_A0_STRATEGY_ZIP.zip"

        plan_cmd = [
            "python3",
            str(PLANNER),
            "--out",
            str(out_zip),
            "--run-id",
            run_id,
            "--sequence",
            str(seq),
            "--state-json",
            str(state_path),
            "--goal-profile",
            str(args.goal_profile),
            "--goal-selection",
            str(args.goal_selection),
            "--debate-mode",
            str(args.debate_mode),
        ]
        plan_proc = _run(plan_cmd, cwd=BOOTPACK)
        if plan_proc.returncode != 0 or not out_zip.exists():
            raise SystemExit("planner failed:\n" + plan_proc.stdout + "\n--- STDERR ---\n" + plan_proc.stderr)

        step_cmd = [
            "python3",
            str(RUNNER),
            "--a1-source",
            "packet",
            "--run-id",
            run_id,
            "--runs-root",
            str(runs_root),
            "--steps",
            "1",
        ]
        if bool(args.retain_diagnostics):
            step_cmd.append("--retain-diagnostics")
        if bool(args.retain_snapshots):
            step_cmd.append("--retain-snapshots")
        if bool(args.retain_sim_text):
            step_cmd.append("--retain-sim-text")
        step_proc = _run(step_cmd, cwd=BOOTPACK)
        if step_proc.returncode != 0:
            raise SystemExit("runner step failed:\n" + step_proc.stdout + "\n--- STDERR ---\n" + step_proc.stderr)

        state_after = _read_json(state_path)
        after = _state_metrics(state_after)
        summary = _read_json(run_dir / "summary.json")
        progress_keys = _meaningful_progress(before, after)
        if progress_keys:
            stall_streak = 0
        else:
            stall_streak += 1
        checkpoint_result: dict = {}
        if project_save_every_cycles > 0 and (len(cycle_rows) + 1) % project_save_every_cycles == 0:
            checkpoint_result = _build_project_save_checkpoint(run_dir=run_dir, sequence=seq)
            if str(checkpoint_result.get("checkpoint_status", "")) == "PASS":
                checkpoint_pass_count += 1
            else:
                checkpoint_fail_count += 1
        run_dir_bytes = _dir_size_bytes(run_dir)
        max_run_dir_bytes_seen = max(max_run_dir_bytes_seen, int(run_dir_bytes))

        row = {
            "schema": "A1_WIGGLE_AUTOPILOT_CYCLE_v1",
            "run_id": run_id,
            "inbox_sequence": seq,
            "planner": {
                "goal_profile": str(args.goal_profile),
                "goal_selection": str(args.goal_selection),
                "debate_mode": str(args.debate_mode),
            },
            "before": before,
            "after": after,
            "meaningful_progress": bool(progress_keys),
            "progress_keys": list(progress_keys),
            "stall_streak": int(stall_streak),
            "runner_stop_reason": str(summary.get("stop_reason", "")),
            "runner_accepted_total": int(summary.get("accepted_total", 0) or 0),
            "runner_parked_total": int(summary.get("parked_total", 0) or 0),
            "runner_rejected_total": int(summary.get("rejected_total", 0) or 0),
            "final_state_hash": str(summary.get("final_state_hash", "")),
        }
        if progress_keys:
            cycles_with_progress += 1
        else:
            cycles_without_progress += 1
        if checkpoint_result:
            row.update(checkpoint_result)
        row, stop_reasons = _apply_cycle_guards(
            row,
            run_dir_bytes=run_dir_bytes,
            checkpoint_status=str(checkpoint_result.get("checkpoint_status", "")),
            stall_streak=stall_streak,
            stall_limit_cycles=stall_limit_cycles,
            max_run_bytes=max_run_bytes,
        )
        if stop_reasons:
            autopilot_stop_reason = str(stop_reasons[0])
            autopilot_stop_reasons = list(stop_reasons)
        cycle_rows.append(row)
        _append_jsonl(autopilot_log_path, row)
        if not bool(args.quiet):
            print(json.dumps(row, sort_keys=True))
        if autopilot_stop_reason:
            break

    final = {
        "schema": "A1_WIGGLE_AUTOPILOT_RESULT_v1",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "cycles_requested": int(cycles),
        "cycles_completed": int(len(cycle_rows)),
        "autopilot_stop_reason": autopilot_stop_reason,
        "autopilot_stop_reasons": list(autopilot_stop_reasons),
        "stall_limit_cycles": int(stall_limit_cycles),
        "max_run_bytes": int(max_run_bytes),
        "project_save_every_cycles": int(project_save_every_cycles),
        "cycles_with_progress": int(cycles_with_progress),
        "cycles_without_progress": int(cycles_without_progress),
        "checkpoint_pass_count": int(checkpoint_pass_count),
        "checkpoint_fail_count": int(checkpoint_fail_count),
        "max_run_dir_bytes_seen": int(max_run_dir_bytes_seen),
        "autopilot_log_path": str(autopilot_log_path),
        "last_cycle": cycle_rows[-1] if cycle_rows else {},
    }
    _append_jsonl(autopilot_log_path, final)
    print(json.dumps(final, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(sys.argv[1:])))
