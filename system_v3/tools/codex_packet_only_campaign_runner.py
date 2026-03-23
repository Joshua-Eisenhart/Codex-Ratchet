#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"
A2_STATE_DEFAULT = SYSTEM_V3 / "a2_state"
BOOTPACK = SYSTEM_V3 / "runtime" / "bootpack_b_kernel_v1"
RUNNER = BOOTPACK / "a1_a0_b_sim_runner.py"
PROMPT_TOOL = SYSTEM_V3 / "tools" / "a1_request_to_codex_prompt.py"
PACKET_TOOL = SYSTEM_V3 / "tools" / "codex_json_to_a1_strategy_packet_zip.py"
SEMANTIC_GATE_TOOL = SYSTEM_V3 / "tools" / "run_a1_semantic_and_math_substance_gate.py"


def _run_cmd(cmd: list[str], *, cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=str(cwd), text=True).strip()


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    if path.name == "state.json":
        heavy_path = path.with_name("state.heavy.json")
        if heavy_path.exists():
            heavy = json.loads(heavy_path.read_text(encoding="utf-8"))
            if isinstance(heavy, dict):
                data.update(heavy)
    return data


def _canonical_step_count(state: dict) -> int:
    rows = state.get("canonical_ledger", []) or []
    return len(rows) if isinstance(rows, list) else 0


def _state_metrics(state: dict) -> dict:
    return {
        "canonical_step_count": _canonical_step_count(state),
        "term_registry_count": len(state.get("term_registry", {}) or {}),
        "canonical_term_count": sum(
            1
            for row in (state.get("term_registry", {}) or {}).values()
            if isinstance(row, dict) and str(row.get("state", "")) == "CANONICAL_ALLOWED"
        ),
        "sim_registry_count": len(state.get("sim_registry", {}) or {}),
        "sim_results_count": len(state.get("sim_results", {}) or {}),
        "graveyard_count": len(state.get("graveyard", {}) or {}),
        "kill_log_count": len(state.get("kill_log", []) or []),
        "park_set_count": len(state.get("park_set", {}) or {}),
        "master_sim_status": str((state.get("sim_promotion_status", {}) or {}).get("SIM_MASTER_T6", "")),
    }

def _kill_token_counts(state: dict) -> dict:
    sim_fail = 0
    neg = 0
    for row in (state.get("kill_log", []) or []):
        if not isinstance(row, dict):
            continue
        token = str(row.get("token", "")).strip().upper()
        if token == "SIM_FAIL":
            sim_fail += 1
        if token.startswith("NEG_"):
            neg += 1
    return {"kill_sim_fail_count": sim_fail, "kill_neg_count": neg}


def _has_inbox_packets(run_dir: Path) -> bool:
    return any((run_dir / "a1_inbox").glob("*_A1_TO_A0_STRATEGY_ZIP.zip"))


def _emit_prompt(*, run_id: str, run_dir: Path, fuel_max_bytes: int, cycle: int, runs_root: Path, a2_state_dir: Path) -> Path:
    prompt = _run_cmd(
        [
            "python3",
            str(PROMPT_TOOL),
            "--run-id",
            run_id,
            "--fuel-max-bytes",
            str(int(fuel_max_bytes)),
            "--runs-root",
            str(runs_root),
            "--a2-state-dir",
            str(a2_state_dir),
        ],
        cwd=REPO,
    )
    out = run_dir / "a1_prompt_queue" / f"{cycle:04d}_A1_PROMPT_FOR_CODEX.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(prompt + "\n", encoding="utf-8")
    return out


def _next_strategy_file(drop_dir: Path) -> Path | None:
    if not drop_dir.is_dir():
        return None
    candidates = sorted(
        [
            p
            for p in drop_dir.glob("*.json")
            if p.is_file() and not p.name.startswith(".")
        ],
        key=lambda p: p.name,
    )
    if not candidates:
        return None
    return candidates[0]


def _ingest_strategy(*, run_id: str, strategy_file: Path, runs_root: Path) -> dict:
    raw = _run_cmd(
        [
            "python3",
            str(PACKET_TOOL),
            "--run-id",
            run_id,
            "--runs-root",
            str(runs_root),
            "--strategy-json",
            str(strategy_file),
        ],
        cwd=REPO,
    )
    return json.loads(raw)


def _run_packet_step(*, run_id: str, runs_root: Path, clean: bool = False) -> tuple[dict, dict]:
    cmd = ["python3", str(RUNNER), "--a1-source", "packet", "--run-id", run_id, "--steps", "1", "--runs-root", str(runs_root)]
    if clean:
        cmd.append("--clean")
    _run_cmd(cmd, cwd=BOOTPACK)
    run_dir = runs_root / run_id
    summary = _read_json(run_dir / "summary.json")
    state = _read_json(run_dir / "state.json")
    return summary, state


def _run_semantic_gate(
    *,
    run_dir: Path,
    phase: str,
    min_canonical_terms: int,
    min_graveyard_count: int,
    min_unique_probe_terms: int,
    max_fallback_probe_fraction: float,
    required_probe_terms: tuple[str, ...],
) -> dict:
    cmd = [
        "python3",
        str(SEMANTIC_GATE_TOOL),
        "--run-dir",
        str(run_dir),
        "--phase",
        str(phase),
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
    proc = subprocess.run(cmd, cwd=str(REPO), check=False, capture_output=True, text=True)
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


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Strict packet-only campaign runner for Codex-as-A1. "
            "No planner fallback. Fails closed when no strategy JSON is provided."
        )
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT), help="Override runs root (default: system_v3/runs).")
    ap.add_argument("--a2-state-dir", default=str(A2_STATE_DEFAULT), help="Override A2 state dir used for A1 prompt fuel.")
    ap.add_argument("--target-canonical-steps", type=int, default=5)
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--fuel-max-bytes", type=int, default=60_000)
    ap.add_argument(
        "--strategy-drop-dir",
        default="",
        help="Directory containing schema-valid A1_STRATEGY_v1 JSON files to ingest.",
    )
    ap.add_argument("--max-cycles", type=int, default=200)
    ap.add_argument("--semantic-gate", dest="semantic_gate", action="store_true", default=True)
    ap.add_argument("--no-semantic-gate", dest="semantic_gate", action="store_false")
    ap.add_argument("--semantic-gate-every-cycle", action="store_true")
    ap.add_argument("--semantic-gate-fail-closed", dest="semantic_gate_fail_closed", action="store_true", default=True)
    ap.add_argument("--semantic-gate-soft", dest="semantic_gate_fail_closed", action="store_false")
    ap.add_argument("--semantic-gate-min-canonical-terms", type=int, default=1)
    ap.add_argument("--semantic-gate-min-graveyard-count", type=int, default=1)
    ap.add_argument("--semantic-gate-min-unique-probe-terms", type=int, default=1)
    ap.add_argument("--semantic-gate-max-fallback-probe-fraction", type=float, default=0.25)
    ap.add_argument(
        "--semantic-gate-phase",
        choices=["mixed", "graveyard_fill", "recovery"],
        default="mixed",
        help="Phase passed to semantic gate. Use graveyard_fill for strict fill-first campaigns.",
    )
    ap.add_argument(
        "--semantic-gate-required-probe-terms",
        default="",
        help="Comma-separated probe terms required by semantic gate. Empty means no fixed required terms.",
    )
    ap.add_argument(
        "--require-graveyard-delta-per-cycle",
        type=int,
        default=0,
        help="If >0, each executed packet cycle must increase graveyard_count by at least this delta.",
    )
    ap.add_argument(
        "--require-sim-fail-kills-delta-per-cycle",
        type=int,
        default=0,
        help="If >0, each executed packet cycle must increase SIM_FAIL kill count by at least this delta.",
    )
    ap.add_argument(
        "--require-neg-kills-delta-per-cycle",
        type=int,
        default=0,
        help="If >0, each executed packet cycle must increase NEG_* kill count by at least this delta.",
    )
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    if not run_id:
        raise SystemExit("missing run-id")
    if int(args.target_canonical_steps) <= 0:
        raise SystemExit("target-canonical-steps must be > 0")

    runs_root = Path(args.runs_root).expanduser().resolve()
    a2_state_dir = Path(args.a2_state_dir).expanduser().resolve()
    run_dir = runs_root / run_id
    strategy_drop_dir = (
        Path(args.strategy_drop_dir).expanduser().resolve()
        if str(args.strategy_drop_dir).strip()
        else (run_dir / "a1_manual_strategies")
    )
    consumed_dir = run_dir / "a1_manual_strategies_consumed"
    required_probe_terms = tuple(
        t.strip() for t in str(args.semantic_gate_required_probe_terms).split(",") if t.strip()
    )

    # Bootstrap run surface in strict packet mode.
    _run_packet_step(run_id=run_id, runs_root=runs_root, clean=bool(args.clean))
    consumed_dir.mkdir(parents=True, exist_ok=True)

    state = _read_json(run_dir / "state.json")
    start_steps = _canonical_step_count(state)
    target_steps = start_steps + int(args.target_canonical_steps)

    audit_rows: list[dict] = []
    stop_reason = "MAX_CYCLES_REACHED"
    last_gate_payload: dict = {}
    executed_cycles = 0
    for cycle in range(1, int(args.max_cycles) + 1):
        state = _read_json(run_dir / "state.json")
        before_metrics = _state_metrics(state)
        before_kills = _kill_token_counts(state)
        current_steps = _canonical_step_count(state)
        if current_steps >= target_steps:
            stop_reason = "TARGET_CANONICAL_STEPS_REACHED"
            break

        prompt_path: Path | None = None
        strategy_used: Path | None = None
        packet_result: dict | None = None
        if not _has_inbox_packets(run_dir):
            prompt_path = _emit_prompt(
                run_id=run_id,
                run_dir=run_dir,
                fuel_max_bytes=int(args.fuel_max_bytes),
                cycle=cycle,
                runs_root=runs_root,
                a2_state_dir=a2_state_dir,
            )
            strategy_file = _next_strategy_file(strategy_drop_dir)
            if strategy_file is None:
                stop_reason = "WAITING_FOR_STRATEGY_JSON"
                audit_rows.append(
                    {
                        "cycle": cycle,
                        "status": "WAITING_FOR_STRATEGY_JSON",
                        "prompt_path": str(prompt_path),
                        "state_metrics": _state_metrics(state),
                    }
                )
                break
            packet_result = _ingest_strategy(run_id=run_id, strategy_file=strategy_file, runs_root=runs_root)
            strategy_used = strategy_file
            consumed_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(strategy_file), str(consumed_dir / strategy_file.name))

        summary, state_after = _run_packet_step(run_id=run_id, runs_root=runs_root, clean=False)
        executed_cycles += 1
        after_metrics = _state_metrics(state_after)
        after_kills = _kill_token_counts(state_after)
        delta_graveyard = int(after_metrics.get("graveyard_count", 0)) - int(before_metrics.get("graveyard_count", 0))
        delta_sim_fail = int(after_kills.get("kill_sim_fail_count", 0)) - int(before_kills.get("kill_sim_fail_count", 0))
        delta_neg = int(after_kills.get("kill_neg_count", 0)) - int(before_kills.get("kill_neg_count", 0))
        cycle_hard_gate = {
            "status": "PASS",
            "delta_graveyard": delta_graveyard,
            "delta_kill_sim_fail": delta_sim_fail,
            "delta_kill_neg": delta_neg,
            "require_graveyard_delta": int(args.require_graveyard_delta_per_cycle),
            "require_sim_fail_delta": int(args.require_sim_fail_kills_delta_per_cycle),
            "require_neg_delta": int(args.require_neg_kills_delta_per_cycle),
        }
        if int(args.require_graveyard_delta_per_cycle) > 0 and delta_graveyard < int(args.require_graveyard_delta_per_cycle):
            cycle_hard_gate["status"] = "FAIL"
            cycle_hard_gate["reason"] = "GRAVEYARD_DELTA_BELOW_MIN"
        if int(args.require_sim_fail_kills_delta_per_cycle) > 0 and delta_sim_fail < int(args.require_sim_fail_kills_delta_per_cycle):
            cycle_hard_gate["status"] = "FAIL"
            cycle_hard_gate["reason"] = "SIM_FAIL_DELTA_BELOW_MIN"
        if int(args.require_neg_kills_delta_per_cycle) > 0 and delta_neg < int(args.require_neg_kills_delta_per_cycle):
            cycle_hard_gate["status"] = "FAIL"
            cycle_hard_gate["reason"] = "NEG_KILL_DELTA_BELOW_MIN"
        cycle_gate_payload: dict = {}
        if bool(args.semantic_gate) and bool(args.semantic_gate_every_cycle):
            cycle_gate_payload = _run_semantic_gate(
                run_dir=run_dir,
                phase=str(args.semantic_gate_phase),
                min_canonical_terms=int(args.semantic_gate_min_canonical_terms),
                min_graveyard_count=int(args.semantic_gate_min_graveyard_count),
                min_unique_probe_terms=int(args.semantic_gate_min_unique_probe_terms),
                max_fallback_probe_fraction=float(args.semantic_gate_max_fallback_probe_fraction),
                required_probe_terms=required_probe_terms,
            )
            last_gate_payload = cycle_gate_payload
        audit_rows.append(
            {
                "cycle": cycle,
                "runner_stop_reason": str(summary.get("stop_reason", "")),
                "prompt_path": str(prompt_path) if prompt_path else "",
                "strategy_used": str(strategy_used) if strategy_used else "",
                "packet_result": packet_result or {},
                "state_metrics": after_metrics,
                "cycle_hard_gate": cycle_hard_gate,
                "semantic_gate": cycle_gate_payload,
            }
        )
        if str((cycle_hard_gate or {}).get("status", "FAIL")) != "PASS":
            stop_reason = "CYCLE_HARD_GATE_FAIL"
            break
        if (
            bool(args.semantic_gate)
            and bool(args.semantic_gate_every_cycle)
            and bool(args.semantic_gate_fail_closed)
            and str((cycle_gate_payload or {}).get("status", "FAIL")) != "PASS"
        ):
            stop_reason = "SEMANTIC_GATE_FAIL"
            break

    final_state = _read_json(run_dir / "state.json")
    final_gate_payload: dict = {}
    if bool(args.semantic_gate):
        if executed_cycles <= 0:
            final_gate_payload = {"status": "SKIP", "reason": "NO_EXECUTED_PACKET_CYCLES", "exit_code": 0}
        else:
            if (
                bool(args.semantic_gate_every_cycle)
                and last_gate_payload
                and str(stop_reason) == "SEMANTIC_GATE_FAIL"
            ):
                final_gate_payload = last_gate_payload
            else:
                final_gate_payload = _run_semantic_gate(
                    run_dir=run_dir,
                    phase=str(args.semantic_gate_phase),
                    min_canonical_terms=int(args.semantic_gate_min_canonical_terms),
                    min_graveyard_count=int(args.semantic_gate_min_graveyard_count),
                    min_unique_probe_terms=int(args.semantic_gate_min_unique_probe_terms),
                    max_fallback_probe_fraction=float(args.semantic_gate_max_fallback_probe_fraction),
                    required_probe_terms=required_probe_terms,
                )

    report = {
        "schema": "CODEX_PACKET_ONLY_CAMPAIGN_REPORT_v1",
        "run_id": run_id,
        "target_canonical_steps_delta": int(args.target_canonical_steps),
        "start_canonical_steps": start_steps,
        "end_canonical_steps": _canonical_step_count(final_state),
        "executed_cycles": executed_cycles,
        "stop_reason": stop_reason,
        "cycles_recorded": len(audit_rows),
        "strategy_drop_dir": str(strategy_drop_dir),
        "consumed_dir": str(consumed_dir),
        "final_state_metrics": _state_metrics(final_state),
        "semantic_gate_enabled": bool(args.semantic_gate),
        "semantic_gate_every_cycle": bool(args.semantic_gate_every_cycle),
        "semantic_gate_fail_closed": bool(args.semantic_gate_fail_closed),
        "semantic_gate_thresholds": {
            "phase": str(args.semantic_gate_phase),
            "min_canonical_terms": int(args.semantic_gate_min_canonical_terms),
            "min_graveyard_count": int(args.semantic_gate_min_graveyard_count),
            "min_unique_probe_terms": int(args.semantic_gate_min_unique_probe_terms),
            "max_fallback_probe_fraction": float(args.semantic_gate_max_fallback_probe_fraction),
            "required_probe_terms": list(required_probe_terms),
        },
        "semantic_gate_final": final_gate_payload,
        "cycles": audit_rows,
    }
    out = run_dir / "reports" / "codex_packet_only_campaign_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    root_out = run_dir / "codex_packet_only_campaign_report.json"
    root_out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"schema": report["schema"], "out": str(out), "root_out": str(root_out), "stop_reason": stop_reason},
            sort_keys=True,
        )
    )
    if (
        bool(args.semantic_gate)
        and bool(args.semantic_gate_fail_closed)
        and str((final_gate_payload or {}).get("status", "FAIL")) == "FAIL"
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
