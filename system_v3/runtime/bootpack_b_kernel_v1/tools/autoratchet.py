#!/usr/bin/env python3
"""
Autonomous local loop (no external LLM) for packet-mode runs:
  - generates 1 A1_TO_A0_STRATEGY_ZIP using the deterministic planner
  - runs 1 step of a1_a0_b_sim_runner.py in packet mode
  - repeats for N steps

This is an execution discipline harness: run -> audit -> adjust -> run.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from a1_adaptive_ratchet_planner import (
    _compatibility_scaffold_terms_for_profile,
    _goals_from_family_slice,
    _load_family_slice,
)

BASE = Path(__file__).resolve().parents[1]
# BASE = .../<repo_root>/system_v3/runtime/bootpack_b_kernel_v1
# repo root = .../<repo_root>
#
# NOTE:
# This tool is sometimes executed from inside a packaged `system_v3/` tree
# (for example, a standalone zip used for portability testing). In that case the
# resolved path still ends with `/system_v3/runtime/bootpack_b_kernel_v1`, but the
# repo root is one level *above* `system_v3/`.
#
# The original implementation used `BASE.parents[2]`, which resolves to the
# `system_v3/` directory (not the repo root) and breaks all calls that expect
# `<repo_root>/system_v3/...`.
def _infer_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(10):
        if (cur / "system_v3").is_dir():
            return cur
        cur = cur.parent
    # Fallback: historical layout assumption.
    return start.resolve().parents[3]


REPO_ROOT = _infer_repo_root(BASE)


def _a2_tick(
    *,
    run_id: str,
    label: str,
    write_latest_zip: bool,
    max_memory_bytes: int,
    retain_shards: int,
    a2_state_dir: str | None,
) -> dict:
    """
    Persist A2 brain as append + bounded sharding.

    A2 is not "saved via snapshots" as an authority mechanism. A2 persistence is:
    - append-only `system_v3/a2_state/memory.jsonl`
    - deterministic sharding/retention for bounded growth

    This tick is campaign-boundary bookkeeping: it must not affect A0/B/SIM
    determinism. It only updates outer-brain persistence so a saved system image
    can recover intent/context explicitly.
    """
    script = (REPO_ROOT / "system_v3" / "tools" / "a2_state_persist_tick.py").resolve()
    resolved_a2_dir = (
        Path(str(a2_state_dir)).expanduser().resolve()
        if a2_state_dir and str(a2_state_dir).strip()
        else (REPO_ROOT / "system_v3" / "a2_state").resolve()
    )

    cmd = [
        "python3",
        str(script),
        "--a2-state-dir",
        str(resolved_a2_dir),
        "--max-memory-bytes",
        str(int(max_memory_bytes)),
        "--retain-shards",
        str(int(retain_shards)),
    ]
    if write_latest_zip:
        cmd.append("--write-latest-zip")

    out = subprocess.check_output(cmd, text=True).strip()
    j = json.loads(out)
    return {
        "label": label,
        "run_id": run_id,
        "a2_state_dir": str(resolved_a2_dir),
        "tick_seq": int(j.get("seq", 0)),
        "manifest_sha256": str(j.get("manifest_sha256", "")),
        "write_latest_zip": bool(write_latest_zip),
        "max_memory_bytes": int(max_memory_bytes),
        "retain_shards": int(retain_shards),
    }


def _read_state_hash(run_dir: Path) -> str:
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        return ""
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return str(summary.get("final_state_hash", "") or "")


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


def _goal_terms_complete(run_dir: Path, goal_terms: tuple[str, ...]) -> bool:
    state = _load_state(run_dir)
    term_registry = state.get("term_registry", {}) or {}
    for term in goal_terms:
        entry = term_registry.get(term)
        if not isinstance(entry, dict):
            return False
        if str(entry.get("state", "")) != "CANONICAL_ALLOWED":
            return False
    return True


def _canonical_terms(run_dir: Path) -> list[str]:
    state = _load_state(run_dir)
    term_registry = state.get("term_registry", {}) or {}
    out: list[str] = []
    for term, entry in term_registry.items():
        if isinstance(entry, dict) and str(entry.get("state", "")) == "CANONICAL_ALLOWED":
            out.append(str(term))
    return sorted(out)


def _state_metrics(run_dir: Path) -> dict:
    state = _load_state(run_dir)
    if not state:
        return {}
    survivors = state.get("survivor_ledger", {}) or {}
    park_set = state.get("park_set", {}) or {}
    kill_log = state.get("kill_log", []) or []
    sim_registry = state.get("sim_registry", {}) or {}
    term_registry = state.get("term_registry", {}) or {}
    canon_terms = [
        term
        for term, entry in term_registry.items()
        if isinstance(entry, dict) and str(entry.get("state", "")) == "CANONICAL_ALLOWED"
    ]
    killed_ids = {str(row.get("id", "")).strip() for row in kill_log if isinstance(row, dict) and str(row.get("id", "")).strip()}
    return {
        "survivor_count": len(survivors),
        "park_count": len(park_set),
        "kill_log_count": len(kill_log),
        "killed_unique_count": len(killed_ids),
        "sim_registry_count": len(sim_registry),
        "canonical_term_count": len(canon_terms),
    }


def _run_semantic_gate(
    *,
    run_dir: Path,
    min_canonical_terms: int,
    min_graveyard_count: int,
    min_unique_probe_terms: int,
    max_fallback_probe_fraction: float,
    required_probe_terms: tuple[str, ...],
) -> dict:
    gate_script = (REPO_ROOT / "system_v3" / "tools" / "run_a1_semantic_and_math_substance_gate.py").resolve()
    cmd = [
        "python3",
        str(gate_script),
        "--run-dir",
        str(run_dir),
        "--min-canonical-terms",
        str(int(min_canonical_terms)),
        "--min-graveyard-count",
        str(int(min_graveyard_count)),
        "--min-unique-probe-terms",
        str(int(min_unique_probe_terms)),
        "--max-fallback-probe-fraction",
        str(float(max_fallback_probe_fraction)),
        "--required-probe-terms",
        ",".join(required_probe_terms),
    ]
    proc = subprocess.run(cmd, check=False, cwd=str(REPO_ROOT), capture_output=True, text=True)
    payload: dict = {"status": "FAIL", "raw_stdout": proc.stdout.strip(), "raw_stderr": proc.stderr.strip()}
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout.strip().splitlines()[-1])
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            pass
    payload["exit_code"] = int(proc.returncode)
    report_path_raw = str(payload.get("report_path", "")).strip()
    if report_path_raw:
        report_path = Path(report_path_raw)
        if report_path.exists():
            try:
                report_obj = json.loads(report_path.read_text(encoding="utf-8"))
                if isinstance(report_obj, dict):
                    payload["report"] = report_obj
            except json.JSONDecodeError:
                pass
    return payload


def _required_probe_terms_for_profile(goal_profile: str) -> tuple[str, ...]:
    return _compatibility_scaffold_terms_for_profile(goal_profile)


def _required_probe_terms_for_family_slice(family_slice: dict) -> tuple[str, ...]:
    return tuple(
        str(x).strip()
        for x in (((family_slice.get("sim_hooks", {}) or {}).get("required_probe_terms", []) or []))
        if str(x).strip()
    )


def _resolve_debate_strategy_from_family_slice(family_slice: dict, requested_strategy: str) -> str:
    run_mode = str(family_slice.get("run_mode", "")).strip()
    strategy = str(requested_strategy).strip()
    if run_mode == "SCAFFOLD_PROOF":
        return "balanced"
    if run_mode == "GRAVEYARD_VALIDITY" and strategy == "balanced":
        return "graveyard_first_then_recovery"
    return strategy


def _compatibility_goal_terms_for_profile(goal_profile: str) -> tuple[str, ...]:
    return _compatibility_scaffold_terms_for_profile(goal_profile)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument(
        "--runs-root",
        default=None,
        help="Override runs root dir. Default is system_v3/runs. Useful for sandbox test runs under work/.",
    )
    parser.add_argument(
        "--goal-profile",
        choices=["core", "extended", "physics", "toolkit", "refined_fuel", "entropy_bridge", "entropy_bookkeeping_bridge"],
        default="core",
    )
    parser.add_argument(
        "--family-slice-json",
        default=None,
        help="Optional bounded A2-derived family-slice JSON. When present, it outranks goal-profile and semantic-gate profile expectations.",
    )
    parser.add_argument(
        "--allow-legacy-goal-profile-mode",
        action="store_true",
        help="Compatibility override for hardcoded profile-ladder autoratchet execution. Without this override, --family-slice-json is required.",
    )
    parser.add_argument("--goal-selection", choices=["interleaved", "closure_first"], default="closure_first")
    parser.add_argument(
        "--a2-brain",
        choices=["none", "start_end_tick"],
        default="start_end_tick",
        help="Persist A2 brain at campaign boundaries (START/END) via a2_state_persist_tick.py.",
    )
    parser.add_argument(
        "--a2-state-dir",
        default=None,
        help="Override A2 state dir for ticks. Default is system_v3/a2_state. Useful for sandbox test runs under work/.",
    )
    parser.add_argument(
        "--a2-write-latest-zip",
        action="store_true",
        help="Also write deterministic a2_state_snapshot_latest.zip during A2 tick (debug transport only; not authoritative).",
    )
    parser.add_argument("--a2-max-memory-bytes", type=int, default=1_000_000)
    parser.add_argument("--a2-retain-shards", type=int, default=64)
    parser.add_argument(
        "--debate-strategy",
        choices=["balanced", "graveyard_first_then_recovery"],
        default="graveyard_first_then_recovery",
    )
    parser.add_argument("--graveyard-fill-steps", type=int, default=6)
    parser.add_argument("--semantic-gate-min-canonical-terms", type=int, default=10)
    parser.add_argument("--semantic-gate-min-graveyard-count", type=int, default=10)
    parser.add_argument("--semantic-gate-min-unique-probe-terms", type=int, default=8)
    parser.add_argument("--semantic-gate-max-fallback-probe-fraction", type=float, default=0.10)
    parser.add_argument(
        "--verbose-subprocess",
        action="store_true",
        help="Stream child process stdout/stderr (very noisy). Default is quiet mode.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume an existing run by starting from the next unused A1 packet sequence.",
    )
    args = parser.parse_args()

    run_id = str(args.run_id)
    steps = int(args.steps)
    family_slice = None
    family_slice_path = None
    runs_root = (
        Path(str(args.runs_root)).expanduser().resolve()
        if args.runs_root and str(args.runs_root).strip()
        else (REPO_ROOT / "system_v3" / "runs")
    )
    runs_root.mkdir(parents=True, exist_ok=True)
    resolved_debate_strategy = str(args.debate_strategy)
    if args.family_slice_json and str(args.family_slice_json).strip():
        family_slice_path = Path(str(args.family_slice_json)).expanduser().resolve()
        family_slice = _load_family_slice(family_slice_path)
        goal_terms = tuple(goal.term for goal in _goals_from_family_slice(family_slice))
        resolved_debate_strategy = _resolve_debate_strategy_from_family_slice(family_slice, resolved_debate_strategy)
    else:
        if not bool(args.allow_legacy_goal_profile_mode):
            raise SystemExit("family_slice_json_required_unless_allow_legacy_goal_profile_mode")
        goal_terms = _compatibility_goal_terms_for_profile(str(args.goal_profile))

    boot = BASE
    runner = boot / "a1_a0_b_sim_runner.py"
    planner = boot / "tools" / "a1_adaptive_ratchet_planner.py"

    def _run_quiet(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        """Run a child process.

        Default behavior is quiet (capture output) to avoid runaway stdout during long
        campaigns; pass --verbose-subprocess to stream child output.
        """
        if args.verbose_subprocess:
            return subprocess.run(cmd, check=False, cwd=str(cwd), text=True)
        return subprocess.run(cmd, check=False, cwd=str(cwd), capture_output=True, text=True)

    def _check_ok(proc: subprocess.CompletedProcess[str], *, label: str, cmd: list[str]) -> None:
        if proc.returncode == 0:
            return
        stdout_tail = "\n".join((proc.stdout or "").splitlines()[-40:])
        stderr_tail = "\n".join((proc.stderr or "").splitlines()[-80:])
        raise RuntimeError(
            "\n".join(
                [
                    f"{label}:subprocess_failed exit_code={proc.returncode}",
                    f"cmd={' '.join(cmd)}",
                    "--- stdout (tail) ---",
                    stdout_tail,
                    "--- stderr (tail) ---",
                    stderr_tail,
                ]
            )
        )

    run_dir = runs_root / run_id
    inbox = run_dir / "a1_inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    # Initialize run dir via runner (creates a1_inbox and emits SAVE zip if empty).
    #
    # NOTE: When resuming, we *skip* init to preserve monotone packet sequences.
    if args.clean or not (run_dir / "state.json").exists():
        init_cmd = ["python3", str(runner), "--a1-source", "packet", "--run-id", run_id, "--steps", "1"]
        if args.clean:
            init_cmd.append("--clean")
        init_cmd.extend(["--runs-root", str(runs_root)])
        init_proc = _run_quiet(init_cmd, cwd=boot)
        _check_ok(init_proc, label="init", cmd=init_cmd)

        # Runner clean/init may have removed and recreated the run surface.
        inbox.mkdir(parents=True, exist_ok=True)

    a2_ticks: list[dict] = []
    a2_ref_path = run_dir / "a2_brain" / "A2_BRAIN_TICKS_v1.json"
    if args.a2_brain == "start_end_tick":
        a2_ticks.append(
            _a2_tick(
                run_id=run_id,
                label="START",
                write_latest_zip=bool(args.a2_write_latest_zip),
                max_memory_bytes=int(args.a2_max_memory_bytes),
                retain_shards=int(args.a2_retain_shards),
                a2_state_dir=str(args.a2_state_dir) if args.a2_state_dir else None,
            )
        )
        a2_ref_path.parent.mkdir(parents=True, exist_ok=True)
        a2_ref_path.write_text(
            json.dumps({"schema": "A2_BRAIN_TICKS_v1", "run_id": run_id, "ticks": a2_ticks}, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    executed_seq = 0
    halt_reason = "MAX_STEPS_REACHED"

    start_seq = 1
    if args.resume and (inbox / "sequence_state.json").exists():
        try:
            raw = json.loads((inbox / "sequence_state.json").read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                last_seq = int(raw.get(f"{run_id}|A1", 0) or 0)
                if last_seq > 0:
                    start_seq = last_seq + 1
        except Exception:
            start_seq = 1
    try:
        for seq in range(start_seq, steps + 1):
            if _goal_terms_complete(run_dir, goal_terms=goal_terms):
                halt_reason = "GOALS_COMPLETE"
                print(f"halt=GOALS_COMPLETE at_seq={seq-1}", flush=True)
                break
            state_json = run_dir / "state.json"
            if not state_json.exists():
                raise RuntimeError(f"missing state.json at {state_json}")
            packet_path = inbox / f"{seq:06d}_A1_TO_A0_STRATEGY_ZIP.zip"
            planner_cmd = [
                "python3",
                str(planner),
                "--out",
                str(packet_path),
                "--run-id",
                run_id,
                "--sequence",
                str(seq),
                "--state-json",
                str(state_json),
                "--goal-profile",
                str(args.goal_profile),
                "--goal-selection",
                str(args.goal_selection),
                "--debate-mode",
                (
                    "graveyard_first"
                    if str(resolved_debate_strategy) == "graveyard_first_then_recovery" and seq <= int(args.graveyard_fill_steps)
                    else ("graveyard_recovery" if str(resolved_debate_strategy) == "graveyard_first_then_recovery" else "balanced")
                ),
            ]
            if family_slice_path is not None:
                planner_cmd.extend(["--family-slice-json", str(family_slice_path)])
            elif bool(args.allow_legacy_goal_profile_mode):
                planner_cmd.append("--allow-legacy-goal-profile-mode")
            planner_proc = _run_quiet(planner_cmd, cwd=boot)
            _check_ok(planner_proc, label=f"planner_seq_{seq}", cmd=planner_cmd)

            runner_cmd = [
                "python3",
                str(runner),
                "--a1-source",
                "packet",
                "--run-id",
                run_id,
                "--steps",
                "1",
                "--runs-root",
                str(runs_root),
            ]
            runner_proc = _run_quiet(runner_cmd, cwd=boot)
            _check_ok(runner_proc, label=f"runner_seq_{seq}", cmd=runner_cmd)

            executed_seq = seq
            metrics = _state_metrics(run_dir)
            canon_terms = int(metrics.get("canonical_term_count", 0) or 0)
            survivors = int(metrics.get("survivor_count", 0) or 0)
            kills = int(metrics.get("kill_log_count", 0) or 0)
            print(
                f"seq={seq} state_hash={_read_state_hash(run_dir)} canon_terms={canon_terms} survivors={survivors} kills={kills}",
                flush=True,
            )
        else:
            halt_reason = "MAX_STEPS_REACHED"
    finally:
        if args.a2_brain == "start_end_tick":
            a2_ticks.append(
                _a2_tick(
                    run_id=run_id,
                    label="END",
                    write_latest_zip=bool(args.a2_write_latest_zip),
                    max_memory_bytes=int(args.a2_max_memory_bytes),
                    retain_shards=int(args.a2_retain_shards),
                    a2_state_dir=str(args.a2_state_dir) if args.a2_state_dir else None,
                )
            )
            a2_ref_path.parent.mkdir(parents=True, exist_ok=True)
            a2_ref_path.write_text(
                json.dumps({"schema": "A2_BRAIN_TICKS_v1", "run_id": run_id, "ticks": a2_ticks}, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
        campaign_summary = {
            "schema": "AUTORATCHET_CAMPAIGN_SUMMARY_v1",
            "run_id": run_id,
            "steps_requested": steps,
            "steps_executed": executed_seq,
            "halt_reason": halt_reason,
            "final_state_hash": _read_state_hash(run_dir),
            "goal_profile": str(args.goal_profile),
            "goal_source": "family_slice" if family_slice else "goal_profile",
            "planning_mode": "family_slice_controlled" if family_slice else "compatibility_profile_scaffold",
            "legacy_goal_profile_mode": not bool(family_slice),
            "compatibility_goal_profile": "" if family_slice else str(args.goal_profile),
            "goal_terms": list(goal_terms),
            "canonical_terms": _canonical_terms(run_dir),
            "a2_brain_mode": args.a2_brain,
            "a2_ticks": a2_ticks,
            "debate_strategy": str(resolved_debate_strategy),
            "graveyard_fill_steps": int(args.graveyard_fill_steps),
            "state_metrics": _state_metrics(run_dir),
            "family_slice_id": str((family_slice or {}).get("slice_id", "") or ""),
            "family_slice_json": str(family_slice_path) if family_slice_path is not None else "",
        }

        # Gate thresholds are tuned for substantive campaigns; for very small goal
        # profiles (e.g. `core`) we clamp the minimums so a fully completed goal-set
        # can still pass the gate without manual flag overrides.
        min_canon = min(int(args.semantic_gate_min_canonical_terms), max(1, len(goal_terms)))
        min_unique_probe = min(int(args.semantic_gate_min_unique_probe_terms), max(1, len(goal_terms)))
        campaign_summary["a1_semantic_gate"] = _run_semantic_gate(
            run_dir=run_dir,
            min_canonical_terms=min_canon,
            min_graveyard_count=int(args.semantic_gate_min_graveyard_count),
            min_unique_probe_terms=min_unique_probe,
            max_fallback_probe_fraction=float(args.semantic_gate_max_fallback_probe_fraction),
            required_probe_terms=(
                _required_probe_terms_for_family_slice(family_slice)
                if family_slice
                else _required_probe_terms_for_profile(str(args.goal_profile))
            ),
        )
        summary_path = run_dir / "reports" / "autoratchet_campaign_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(campaign_summary, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        (run_dir / "campaign_summary.json").write_text(
            json.dumps(campaign_summary, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
