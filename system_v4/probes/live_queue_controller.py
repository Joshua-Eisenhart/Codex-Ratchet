#!/usr/bin/env python3
"""
live_queue_controller.py

Minimal on-demand live-queue controller for Telegram/manual runs.
Uses repo control surfaces to choose a bounded batch instead of improvising.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROBES = REPO / "system_v4" / "probes"
RESULTS = PROBES / "a2_state" / "sim_results"
PYTHON = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
MPLCONFIGDIR = "/tmp/codex-mpl"
NUMBA_CACHE_DIR = "/tmp/codex-numba"
STATUS_FILE = "/tmp/codex_live_queue_controller.status"
MAINTENANCE_CLOSURE = PROBES / "maintenance_closure.py"
NONFATAL_EXIT_STEPS = {"weyl_geometry_ladder_audit"}

@dataclass
class Step:
    name: str
    command: list[str]
    result_json: str | None = None
    truth_row: str | None = None
    backlog_row: str | None = None
    registry_row: str | None = None

def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def emit(msg: str) -> None:
    print(msg, flush=True)

def set_status(text: str) -> None:
    Path(STATUS_FILE).write_text(text, encoding="utf-8")

def env() -> dict[str, str]:
    base = os.environ.copy()
    base["MPLCONFIGDIR"] = MPLCONFIGDIR
    base["NUMBA_CACHE_DIR"] = NUMBA_CACHE_DIR
    return base

def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)

def audit_green() -> tuple[bool, bool]:
    truth_ok = False
    controller_ok = False
    truth_path = RESULTS / "probe_truth_audit_results.json"
    controller_path = RESULTS / "controller_alignment_audit_results.json"
    if truth_path.exists():
        try:
            truth_ok = bool(read_json(truth_path).get("summary", {}).get("ok"))
        except Exception:
            truth_ok = False
    if controller_path.exists():
        try:
            controller = read_json(controller_path)
            controller_ok = bool(controller.get("probe_truth_audit", {}).get("ok")) and bool(controller.get("controller_contract_current"))
        except Exception:
            controller_ok = False
    return truth_ok, controller_ok

def run_step(step: Step) -> int:
    set_status(step.name)
    emit(f"RUN-STEP START {now()} {step.name}")
    proc = subprocess.run(step.command, cwd=REPO, env=env(), capture_output=True, text=True, timeout=1800)
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if out:
        emit(out[:4000])
    emit(f"RUN-STEP END {now()} {step.name} exit={proc.returncode}")
    return proc.returncode


def build_closure_command(step: Step) -> list[str] | None:
    if not step.result_json or not any([step.truth_row, step.backlog_row, step.registry_row]):
        return None
    command = [
        PYTHON,
        str(MAINTENANCE_CLOSURE),
        "--result-json",
        str(RESULTS / step.result_json),
    ]
    if step.truth_row:
        command.extend(["--truth-row", step.truth_row])
    if step.backlog_row:
        command.extend(["--backlog-row", step.backlog_row])
    if step.registry_row:
        command.extend(["--registry-row", step.registry_row])
    command.append("--dry-run")
    return command



def run_closure_command(command: list[str]) -> int:
    emit(f"RUN-CLOSURE START {now()} cmd={' '.join(command)}")
    proc = subprocess.run(command, cwd=REPO, env=env(), capture_output=True, text=True, timeout=1800)
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if out:
        emit(out[:4000])
    emit(f"RUN-CLOSURE END {now()} exit={proc.returncode}")
    return proc.returncode



def run_batch_closure(
    steps: list[Step],
    *,
    truth_exit: int | None,
    controller_exit: int | None,
    runner=None,
) -> int:
    if truth_exit != 0 or controller_exit != 0:
        return 0
    runner = runner or run_closure_command
    worst_exit = 0
    for step in steps:
        command = build_closure_command(step)
        if command is None:
            continue
        exit_code = runner(command)
        if exit_code != 0:
            worst_exit = exit_code
    return worst_exit

def batch1() -> list[Step]:
    return [
        Step(
            "carrier_admission_rerun",
            [PYTHON, str(PROBES / "sim_density_hopf_geometry.py")],
            result_json="density_hopf_geometry_results.json",
            truth_row="explicit Hopf-map packet (`hopf_map_s3_to_s2`)",
            backlog_row="B4",
            registry_row="hopf_map_s3_to_s2",
        ),
        Step(
            "same_carrier_geometry_rerun",
            [PYTHON, str(PROBES / "sim_foundation_hopf_torus_geomstats_clifford.py")],
            result_json="foundation_hopf_torus_geomstats_clifford_results.json",
            truth_row="same-carrier geometry anchor",
            backlog_row="B3",
        ),
        Step("truth_audit", [PYTHON, str(PROBES / "probe_truth_audit.py")]),
        Step("controller_alignment", [PYTHON, str(PROBES / "controller_alignment_audit.py")]),
    ]

def batch2() -> list[Step]:
    return [
        Step("weyl_hopf_pauli_composed_stack", [PYTHON, str(PROBES / "sim_weyl_hopf_pauli_composed_stack.py")]),
        Step("pauli_generator_basis", [PYTHON, str(PROBES / "sim_pauli_generator_basis.py")]),
        Step("weyl_geometry_ladder_audit", [PYTHON, str(PROBES / "sim_weyl_geometry_ladder_audit.py")]),
        Step("lego_registry_extract", [PYTHON, str(PROBES / "extract_actual_lego_registry.py")]),
        Step("lego_normalization_queue", [PYTHON, str(PROBES / "actual_lego_normalization_queue.py")]),
        Step("truth_audit", [PYTHON, str(PROBES / "probe_truth_audit.py")]),
        Step("controller_alignment", [PYTHON, str(PROBES / "controller_alignment_audit.py")]),
    ]

def batch3() -> list[Step]:
    return [
        Step("toponetx_state_class_binding", [PYTHON, str(PROBES / "sim_toponetx_state_class_binding.py")]),
        Step("weyl_hypergraph_geometry_bridge", [PYTHON, str(PROBES / "sim_weyl_hypergraph_geometry_bridge.py")]),
        Step("weyl_hypergraph_admission_helper", [PYTHON, str(PROBES / "sim_weyl_hypergraph_admission_helper.py")]),
        Step("truth_audit", [PYTHON, str(PROBES / "probe_truth_audit.py")]),
        Step("controller_alignment", [PYTHON, str(PROBES / "controller_alignment_audit.py")]),
    ]


def batch4() -> list[Step]:
    return [
        Step("sphere_geometry", [PYTHON, str(PROBES / "sim_sphere_geometry.py")]),
        Step("fubini_study_geometry", [PYTHON, str(PROBES / "sim_fubini_study_geometry.py")]),
        Step("trace_distance_geometry", [PYTHON, str(PROBES / "sim_trace_distance_geometry.py")]),
        Step("real_only_geometry_rejection", [PYTHON, str(PROBES / "sim_real_only_geometry_rejection.py")]),
        Step("truth_audit", [PYTHON, str(PROBES / "probe_truth_audit.py")]),
        Step("controller_alignment", [PYTHON, str(PROBES / "controller_alignment_audit.py")]),
    ]


def batch5() -> list[Step]:
    return [
        Step("cross_shell_coupling_cp1_bures", [PYTHON, str(PROBES / "sim_pure_lego_cross_shell_coupling_cp1_bures.py")]),
        Step("pairwise_shell_coupling_cp1", [PYTHON, str(PROBES / "sim_pure_lego_pairwise_shell_coupling_cp1.py")]),
        Step("operator_geometry_compatibility", [PYTHON, str(PROBES / "sim_operator_geometry_compatibility.py")]),
        Step("truth_audit", [PYTHON, str(PROBES / "probe_truth_audit.py")]),
        Step("controller_alignment", [PYTHON, str(PROBES / "controller_alignment_audit.py")]),
    ]


QUEUE = [
    ("batch1", batch1),
    ("batch2", batch2),
    ("batch3", batch3),
    ("batch4", batch4),
    ("batch5", batch5),
]


def enumerate_all_sims() -> list[Path]:
    return sorted(PROBES.glob("sim_*.py"))


def result_path_for(sim: Path) -> Path:
    return RESULTS / f"{sim.stem[4:]}_results.json"


def is_fresh_and_green(sim: Path) -> bool:
    r = result_path_for(sim)
    if not r.exists():
        return False
    if r.stat().st_mtime < sim.stat().st_mtime:
        return False
    try:
        data = json.loads(r.read_text())
    except Exception:
        return False
    summary = data.get("summary") if isinstance(data, dict) else None
    if not isinstance(summary, dict):
        return False
    return summary.get("all_pass") is True


def audit_sim_inventory() -> dict:
    fresh: list[Path] = []
    stale: list[Path] = []
    missing: list[Path] = []
    for sim in enumerate_all_sims():
        r = result_path_for(sim)
        if not r.exists():
            missing.append(sim)
        elif is_fresh_and_green(sim):
            fresh.append(sim)
        else:
            stale.append(sim)
    return {"fresh": fresh, "stale": stale, "missing": missing,
            "total": len(fresh) + len(stale) + len(missing)}


def choose_audit_targets(max_sims: int = 20) -> tuple[str, list[Step]]:
    inv = audit_sim_inventory()
    emit(f"AUDIT-INVENTORY total={inv['total']} fresh={len(inv['fresh'])} "
         f"stale={len(inv['stale'])} missing={len(inv['missing'])}")
    targets = inv["missing"] + inv["stale"]
    if not targets:
        return "audit_all_fresh", [
            Step("truth_audit", [PYTHON, str(PROBES / "probe_truth_audit.py")]),
            Step("controller_alignment", [PYTHON, str(PROBES / "controller_alignment_audit.py")]),
        ]
    chosen = targets[:max_sims]
    steps = [
        Step(sim.stem[4:], [PYTHON, str(sim)], result_json=result_path_for(sim).name)
        for sim in chosen
    ]
    steps.append(Step("truth_audit", [PYTHON, str(PROBES / "probe_truth_audit.py")]))
    steps.append(Step("controller_alignment", [PYTHON, str(PROBES / "controller_alignment_audit.py")]))
    return f"audit_wave[{len(chosen)}]", steps


def choose_batch(previous: str | None = None) -> tuple[str, list[Step]]:
    truth_ok, controller_ok = audit_green()
    if not (truth_ok and controller_ok):
        return "batch1", batch1()

    if previous is None:
        return QUEUE[1][0], QUEUE[1][1]()

    names = [name for name, _ in QUEUE]
    if previous not in names:
        return QUEUE[1][0], QUEUE[1][1]()

    idx = names.index(previous)
    next_idx = min(idx + 1, len(QUEUE) - 1)
    return QUEUE[next_idx][0], QUEUE[next_idx][1]()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=int, default=60)
    parser.add_argument("--audit-first", action="store_true",
                        help="Use full-inventory audit-driven target selection instead of fixed batch rotation")
    parser.add_argument("--max-sims-per-wave", type=int, default=20)
    args = parser.parse_args()
    os.makedirs(MPLCONFIGDIR, exist_ok=True)
    os.makedirs(NUMBA_CACHE_DIR, exist_ok=True)
    deadline = time.time() + max(args.minutes, 1) * 60
    previous_batch = None
    failures = []
    ran_batches = []
    while time.time() < deadline:
        if args.audit_first:
            batch_name, steps = choose_audit_targets(max_sims=args.max_sims_per_wave)
        else:
            batch_name, steps = choose_batch(previous_batch)
        previous_batch = batch_name
        ran_batches.append(batch_name)
        set_status(batch_name)
        emit(f"RUN-HEARTBEAT {now()} health=healthy task={batch_name}")
        emit(f"RUN-PLAN {now()} selected={batch_name} minutes={args.minutes}")
        truth_exit = None
        controller_exit = None
        for step in steps:
            code = run_step(step)
            if step.name == "truth_audit":
                truth_exit = code
            elif step.name == "controller_alignment":
                controller_exit = code
            if code != 0 and step.name not in NONFATAL_EXIT_STEPS:
                failures.append((step.name, code))
            if time.time() >= deadline:
                break
        closure_exit = run_batch_closure(
            steps,
            truth_exit=truth_exit,
            controller_exit=controller_exit,
        )
        if closure_exit != 0:
            failures.append((f"{batch_name}_closure", closure_exit))
    set_status("closeout_pending")
    selected = "+".join(ran_batches) if ran_batches else "none"
    if failures:
        joined = ", ".join(f"{name}:{code}" for name, code in failures)
        emit(f"RUN-DONE {now()} selected={selected} status=degraded failures={joined}")
    else:
        emit(f"RUN-DONE {now()} selected={selected} status=healthy failures=none")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
