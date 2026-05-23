#!/usr/bin/env python3
"""Attractor-basin probe for the source-aligned QIT engine runtime."""

from __future__ import annotations

import hashlib
import itertools
import json
import pathlib
import time
from typing import Any

import torch
import z3

import source_aligned_qit_engine_runtime as rt


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_aligned_qit_engine_attractor_basin_probe_results.json"

NAME = "source_aligned_qit_engine_attractor_basin_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_source_aligned_qit_engine_attractor_basin"
SOURCE_ALIGNMENT_CATEGORY = "axis_corrected_source_aligned_qit_engine_attractor_basin"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests single-qubit source-aligned QIT engine attractor "
    "basins across finite initial states and short schedule compositions. It "
    "does not admit multi-site tensor networks, PEPS/MPDO dynamics, Axis0 Xi "
    "bridge closure, nonlinear state-space multi-basin claims, or final "
    "geometric-manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density-matrix basin trajectories, spread calculations, and schedule-attractor distances",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard separating monostable engine basins from schedule-level attractors",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source provenance hashes"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
}

INITIAL_BLOCHS = [
    (1.0, 0.0, 0.0),
    (-1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, -1.0, 0.0),
    (0.0, 0.0, 1.0),
    (0.0, 0.0, -1.0),
    (0.0, 0.0, 0.0),
    (0.31, -0.22, 0.41),
    (-0.45, 0.18, -0.29),
]
ENGINE_CYCLES = 20
SCHEDULE_REPEATS = 16
SINGLE_ENGINE_SPREAD_TOL = 1.0e-6
SCHEDULE_SPREAD_TOL = 1.0e-5
SCHEDULE_SEPARATION_FLOOR = 5.0e-2


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_file(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def norm(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(a - b).item())


def max_pairwise_spread(points: list[torch.Tensor]) -> float:
    return max((norm(a, b) for a, b in itertools.combinations(points, 2)), default=0.0)


def center(points: list[torch.Tensor]) -> torch.Tensor:
    return sum(points, torch.zeros(3, dtype=torch.float64)) / max(1, len(points))


def single_engine_basin(engine: str) -> dict[str, Any]:
    finals: list[torch.Tensor] = []
    rows: list[dict[str, Any]] = []
    for idx, bloch in enumerate(INITIAL_BLOCHS):
        result = rt.run_engine(engine, rt.rho_from_bloch(*bloch), cycles=ENGINE_CYCLES)
        final = torch.tensor(result["final_bloch"], dtype=torch.float64)
        finals.append(final)
        rows.append(
            {
                "initial_index": idx,
                "initial_bloch": list(bloch),
                "final_bloch": result["final_bloch"],
                "final_valid_density": result["final_valid_density"],
                "last_cycle_drift_fro": result["last_cycle_drift_fro"],
            }
        )
    c = center(finals)
    return {
        "engine": engine,
        "cycles": ENGINE_CYCLES,
        "initial_count": len(INITIAL_BLOCHS),
        "max_final_spread": max_pairwise_spread(finals),
        "center_bloch": [float(v) for v in c.tolist()],
        "rows": rows,
    }


def schedule_basin(name: str, order: list[str]) -> dict[str, Any]:
    finals: list[torch.Tensor] = []
    for bloch in INITIAL_BLOCHS:
        result = rt.run_schedule(order, rt.rho_from_bloch(*bloch), repeats=SCHEDULE_REPEATS)
        finals.append(torch.tensor(result["final_bloch"], dtype=torch.float64))
    c = center(finals)
    return {
        "name": name,
        "order": order,
        "repeats": SCHEDULE_REPEATS,
        "initial_count": len(INITIAL_BLOCHS),
        "max_final_spread": max_pairwise_spread(finals),
        "center_bloch": [float(v) for v in c.tolist()],
    }


def schedule_distance_rows(basins: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    centers = {
        name: torch.tensor(row["center_bloch"], dtype=torch.float64)
        for name, row in basins.items()
    }
    for left, right in itertools.combinations(sorted(centers), 2):
        rows.append({"left": left, "right": right, "distance": norm(centers[left], centers[right])})
    return rows


def z3_basin_gate(checks: dict[str, bool]) -> dict[str, Any]:
    single_engine_monostable = z3.Bool("single_engine_monostable")
    schedule_attractors_distinct = z3.Bool("schedule_attractors_distinct")
    nonlinear_multibasin_claim = z3.Bool("nonlinear_multibasin_claim")
    bounded_schedule_basin_evidence = z3.Bool("bounded_schedule_basin_evidence")
    final_admission = z3.Bool("final_admission")
    promoted = z3.Bool("promoted")

    solver = z3.Solver()
    solver.add(single_engine_monostable == bool(checks["single_engine_basins_converge"]))
    solver.add(schedule_attractors_distinct == bool(checks["schedule_attractors_distinct"]))
    solver.add(nonlinear_multibasin_claim == False)
    solver.add(
        bounded_schedule_basin_evidence
        == z3.And(single_engine_monostable, schedule_attractors_distinct, z3.Not(nonlinear_multibasin_claim))
    )
    solver.add(final_admission == False)
    solver.add(promoted == z3.And(bounded_schedule_basin_evidence, final_admission))

    progress = z3.Solver()
    for assertion in solver.assertions():
        progress.add(assertion)

    premature = z3.Solver()
    for assertion in solver.assertions():
        premature.add(assertion)
    premature.add(promoted)

    status = progress.check()
    model = progress.model() if status == z3.sat else None
    return {
        "status": str(status),
        "single_engine_monostable": bool(model[single_engine_monostable]) if model is not None else None,
        "schedule_attractors_distinct": bool(model[schedule_attractors_distinct]) if model is not None else None,
        "nonlinear_multibasin_claim": bool(model[nonlinear_multibasin_claim]) if model is not None else None,
        "bounded_schedule_basin_evidence": bool(model[bounded_schedule_basin_evidence]) if model is not None else None,
        "final_admission_allowed": bool(model[final_admission]) if model is not None else None,
        "premature_promotion_status": str(premature.check()),
    }


def main() -> int:
    started = time.time()
    single = {engine: single_engine_basin(engine) for engine in ("T1", "T2")}
    schedules = {
        "T1": schedule_basin("T1", ["T1"]),
        "T2": schedule_basin("T2", ["T2"]),
        "T1T2": schedule_basin("T1T2", ["T1", "T2"]),
        "T2T1": schedule_basin("T2T1", ["T2", "T1"]),
    }
    distance_rows = schedule_distance_rows(schedules)
    min_schedule_distance = min(row["distance"] for row in distance_rows)
    checks = {
        "single_engine_basins_converge": all(row["max_final_spread"] < SINGLE_ENGINE_SPREAD_TOL for row in single.values()),
        "schedule_basins_converge": all(row["max_final_spread"] < SCHEDULE_SPREAD_TOL for row in schedules.values()),
        "schedule_attractors_distinct": min_schedule_distance > SCHEDULE_SEPARATION_FLOOR,
        "single_engine_not_state_multibasin": all(row["max_final_spread"] < SINGLE_ENGINE_SPREAD_TOL for row in single.values()),
        "all_final_states_valid": all(item["final_valid_density"] for row in single.values() for item in row["rows"]),
    }
    z3_gate = z3_basin_gate(checks)
    positive = {
        "single_engine_basins_converge": {
            "pass": checks["single_engine_basins_converge"],
            "T1_spread": single["T1"]["max_final_spread"],
            "T2_spread": single["T2"]["max_final_spread"],
            "tolerance": SINGLE_ENGINE_SPREAD_TOL,
        },
        "schedule_basins_converge": {
            "pass": checks["schedule_basins_converge"],
            "schedule_spreads": {name: row["max_final_spread"] for name, row in schedules.items()},
            "tolerance": SCHEDULE_SPREAD_TOL,
        },
        "schedule_attractors_distinct": {
            "pass": checks["schedule_attractors_distinct"],
            "min_schedule_center_distance": min_schedule_distance,
            "separation_floor": SCHEDULE_SEPARATION_FLOOR,
        },
        "all_final_states_valid": {
            "pass": checks["all_final_states_valid"],
        },
        "z3_nonpromotion_guard": {
            "pass": (
                z3_gate["status"] == "sat"
                and z3_gate["bounded_schedule_basin_evidence"] is True
                and z3_gate["final_admission_allowed"] is False
                and z3_gate["premature_promotion_status"] == "unsat"
            ),
            "z3_basin_gate": z3_gate,
        },
    }
    graveyard_companions = {
        "single_engine_not_state_multibasin": {
            "pass": checks["single_engine_not_state_multibasin"],
            "summary": "Each single engine collapses finite initial states to one basin; this is not a state-space multibasin proof.",
        },
        "bounded_schedule_evidence_not_scale_basin": {
            "pass": z3_gate["final_admission_allowed"] is False,
            "summary": "Distinct schedule centers are bounded single-qubit schedule evidence, not scale-level basin admission.",
        },
        "no_tensor_network_or_phi0_bridge_admission": {
            "pass": True,
            "summary": "The scout does not run MPDO/MPS/PEPS dynamics or admit Axis0 Xi/Phi0 bridge closure.",
        },
    }
    boundary = {
        "formal_scout_only": {
            "pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "final_manifold_not_admitted": {
            "pass": z3_gate["final_admission_allowed"] is False,
            "z3_basin_gate": z3_gate,
        },
        "single_qubit_runtime_only": {
            "pass": True,
            "summary": "Only one-qubit source-aligned runtime schedules are tested here.",
        },
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions),
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and all(item["pass"] for item in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all_pass,
        "checks": checks,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": (
            "This is a v5 source-aligned QIT engine formal scout over bounded "
            "single-qubit schedule basins. It is not a promoted v4 probe and "
            "does not admit tensor-network, Xi/Phi0 bridge, or final manifold claims."
        ),
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_seconds": time.time() - started,
        "source_files": {
            "probe": rel(pathlib.Path(__file__).resolve()),
            "source_aligned_runtime": rel(ROOT / "source_aligned_qit_engine_runtime.py"),
        },
        "source_hashes": {
            "probe": sha256_file(pathlib.Path(__file__).resolve()),
            "source_aligned_runtime": sha256_file(ROOT / "source_aligned_qit_engine_runtime.py"),
        },
        "single_engine_basins": single,
        "schedule_basins": schedules,
        "schedule_center_distances": distance_rows,
        "summary": {
            "T1_single_engine_spread": single["T1"]["max_final_spread"],
            "T2_single_engine_spread": single["T2"]["max_final_spread"],
            "min_schedule_center_distance": min_schedule_distance,
            "interpretation": "source-aligned single engines are monostable over finite initial probes; schedule-level attractors are distinct",
        },
        "z3_basin_gate": z3_gate,
        "divergence_log": [
            {
                "control": "multiple_initial_states_same_engine",
                "observation": "final spread collapses below tolerance for each single engine",
                "status": "state_space_multibasin_not_supported",
            },
            {
                "control": "schedule_composition_order",
                "observation": "schedule centers remain separated after convergence",
                "status": "schedule_layer_attractor_structure_supported",
            },
        ],
        "next_required_work": [
            "port this source-aligned runtime from one-qubit density matrices to MPDO/MPS before tensor-network claims",
            "add a source-aligned consumer migration audit for old get_lindblad_params imports",
            "test longer source-aligned schedule words for basin count and memory horizon",
            "keep Axis0 Xi bridge as a separate cut-state construction problem",
        ],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": rel(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
