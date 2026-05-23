#!/usr/bin/env python3
"""Source-aligned QIT engine runtime probe.

This formal scout promotes the axis-audit smoke into the formal_scouts surface.
It tests a torch-native one-qubit replacement path for the older
PERCEPTION_L_MATRICES replay boundary.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import torch
import z3

import canonical_qit_engine_specs as old_specs
import qit_engine_runtime as old_runtime
import source_aligned_qit_engine_runtime as rt


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_aligned_qit_engine_runtime_probe_results.json"

NAME = "source_aligned_qit_engine_runtime_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_source_aligned_qit_engine_runtime"
SOURCE_ALIGNMENT_CATEGORY = "axis_corrected_source_aligned_qit_engine_runtime"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: validates a one-qubit torch-native source-aligned QIT "
    "engine runtime with corrected A0/A1/A2 terrain square and A6 chart-role "
    "XOR. It does not admit tensor-network runtime, PEPS/MPDO dynamics, Axis0 "
    "Xi bridge closure, scale-level attractor-basin admission, or canonical "
    "replacement of every older formal scout importer."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density matrices, CPTP stage maps, fixed-point convergence, schedule-order gap, and engine distinction",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion and A6 chart-role/raw-path separation sanity constraints",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive old-boundary comparison for PERCEPTION_L_MATRICES mismatch visibility",
    },
    "qit_engine_runtime": {
        "tried": True,
        "used": True,
        "reason": "supportive older shared-runtime comparison; not used as source truth",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source provenance hashes"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "qit_engine_runtime": "supportive",
    "python_json": "supportive",
    "hashlib": "supportive",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_file(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def matrix_label(matrix: torch.Tensor) -> str:
    m = torch.as_tensor(matrix, dtype=rt.DTYPE)
    checks = {
        "sigma_z": rt.SZ,
        "-sigma_z": -rt.SZ,
        "sigma_plus": rt.SIGMA_PLUS,
        "sigma_minus": rt.SIGMA_MINUS,
        "-i_sigma_y": -1j * rt.SY,
        "i_sigma_y": 1j * rt.SY,
    }
    for name, target in checks.items():
        if torch.allclose(m, target, atol=1e-12):
            return name
    return "unclassified"


def source_expected_terrain_laws() -> dict[str, Any]:
    return {
        "Se": {
            "law": "isotropic_pauli_dissipator_plus_sheet_hamiltonian",
            "T1": "Funnel",
            "T2": "Cannon",
        },
        "Ne": {
            "law": "hamiltonian_circulation_plus_optional_weak_dissipator",
            "T1": "Vortex",
            "T2": "Spiral",
        },
        "Ni": {
            "law": "ladder_dissipator_plus_sheet_hamiltonian",
            "T1": "Pit_sigma_minus_to_z_minus",
            "T2": "Source_sigma_plus_to_z_plus",
        },
        "Si": {
            "law": "commuting_hamiltonian_plus_projector_dephasing",
            "T1": "Hill",
            "T2": "Citadel",
        },
    }


def old_perception_l_table() -> dict[str, str]:
    return {name: matrix_label(matrix) for name, matrix in old_specs.PERCEPTION_L_MATRICES.items()}


def old_runtime_fixed_bloch() -> dict[str, Any]:
    left = old_runtime.fixed_bloch(old_runtime.engine_channel("L"), cycles=120)
    right = old_runtime.fixed_bloch(old_runtime.engine_channel("R"), cycles=120)
    return {"L": left, "R": right}


def fro_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(a - b).item())


def z3_nonpromotion_gate(checks: dict[str, bool], raw_path_witness: bool) -> dict[str, Any]:
    solver = z3.Solver()
    engine_runs = z3.Bool("engine_runs")
    chart_xor_passes = z3.Bool("chart_xor_passes")
    raw_path_is_not_xor_source = z3.Bool("raw_path_is_not_xor_source")
    tensor_network_admitted = z3.Bool("tensor_network_admitted")
    canonical_replacement_admitted = z3.Bool("canonical_replacement_admitted")
    final_admission = z3.Bool("final_admission")

    solver.add(engine_runs == bool(checks["source_aligned_engines_run"]))
    solver.add(chart_xor_passes == bool(checks["a6_chart_role_xor_passes"]))
    solver.add(raw_path_is_not_xor_source == bool(raw_path_witness))
    solver.add(tensor_network_admitted == False)
    solver.add(canonical_replacement_admitted == False)
    solver.add(final_admission == z3.And(engine_runs, chart_xor_passes, raw_path_is_not_xor_source))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    return {
        "status": str(status),
        "engine_runs": bool(model[engine_runs]) if model is not None else None,
        "chart_xor_passes": bool(model[chart_xor_passes]) if model is not None else None,
        "raw_path_is_not_xor_source": bool(model[raw_path_is_not_xor_source]) if model is not None else None,
        "tensor_network_admitted": bool(model[tensor_network_admitted]) if model is not None else None,
        "canonical_replacement_admitted": bool(model[canonical_replacement_admitted]) if model is not None else None,
        "final_admission": bool(model[final_admission]) if model is not None else None,
    }


def main() -> int:
    started = time.time()
    rho0 = rt.rho_from_bloch(0.23, -0.17, 0.41)
    t1 = rt.run_engine("T1", rho0)
    t2 = rt.run_engine("T2", rho0)
    schedule_t1_t2 = rt.run_schedule(["T1", "T2"], rho0)
    schedule_t2_t1 = rt.run_schedule(["T2", "T1"], rho0)

    t_gap = fro_distance(t1["final_density"], t2["final_density"])
    order_gap = fro_distance(schedule_t1_t2["final_density"], schedule_t2_t1["final_density"])
    old_bloch = old_runtime_fixed_bloch()
    old_l_table = old_perception_l_table()
    expected_laws = source_expected_terrain_laws()

    raw_path_witness = bool(t1["all_raw_path_xor_ok"] and not t2["all_raw_path_xor_ok"])
    checks = {
        "source_aligned_engines_run": bool(
            t1["final_valid_density"] and t2["final_valid_density"] and t1["all_stage_valid"] and t2["all_stage_valid"]
        ),
        "source_aligned_engines_converge": bool(t1["last_cycle_drift_fro"] < 1e-3 and t2["last_cycle_drift_fro"] < 1e-3),
        "source_aligned_engines_are_distinct": bool(t_gap > 1e-3),
        "schedule_order_matters": bool(order_gap > 1e-4),
        "a6_chart_role_xor_passes": bool(t1["all_a6_xor_ok"] and t2["all_a6_xor_ok"]),
        "raw_fiber_base_xor_fails_type2_as_expected": raw_path_witness,
        "terrain_realization_count_is_8": bool(
            len(set(t1["terrain_realizations_seen"]) | set(t2["terrain_realizations_seen"])) == 8
        ),
        "old_perception_l_table_is_not_source_terrain_law": bool(
            old_l_table == {
                "Se": "sigma_z",
                "Ne": "sigma_plus",
                "Ni": "-i_sigma_y",
                "Si": "sigma_minus",
            }
        ),
    }
    z3_gate = z3_nonpromotion_gate(checks, raw_path_witness)
    all_pass = all(checks.values()) and z3_gate["status"] == "sat" and z3_gate["final_admission"] is True
    positive = {
        "source_aligned_engines_run": {
            "pass": checks["source_aligned_engines_run"],
            "summary": "both Type 1 and Type 2 source-aligned one-qubit engines produce valid final densities",
        },
        "source_aligned_engines_converge": {
            "pass": checks["source_aligned_engines_converge"],
            "summary": "both engines settle below the finite last-cycle drift threshold",
        },
        "source_aligned_engines_are_distinct": {
            "pass": checks["source_aligned_engines_are_distinct"],
            "T1_T2_final_fro": t_gap,
        },
        "schedule_order_matters": {
            "pass": checks["schedule_order_matters"],
            "schedule_T1T2_vs_T2T1_fro": order_gap,
        },
        "terrain_realization_count_is_8": {
            "pass": checks["terrain_realization_count_is_8"],
            "summary": "the runtime sees all eight sheet-specific terrain realizations",
        },
    }
    graveyard_companions = {
        "old_perception_l_table_not_source_terrain_law": {
            "pass": checks["old_perception_l_table_is_not_source_terrain_law"],
            "old_perception_l_table": old_l_table,
            "summary": "older one-L-matrix-per-perception replay is preserved as boundary evidence, not accepted as source terrain law",
        },
        "raw_fiber_base_xor_killed_for_type2": {
            "pass": checks["raw_fiber_base_xor_fails_type2_as_expected"],
            "summary": "raw geometry path is not the A6 XOR sign source because Type 2 swaps fiber/base chart roles",
        },
    }
    boundary = {
        "a6_chart_role_xor_passes": {
            "pass": checks["a6_chart_role_xor_passes"],
            "summary": "b6=-b0*b3 is evaluated against chart role inner/outer, not raw fiber/base path identity",
        },
        "z3_nonpromotion_gate": {
            "pass": z3_gate["status"] == "sat"
            and z3_gate["tensor_network_admitted"] is False
            and z3_gate["canonical_replacement_admitted"] is False,
            "gate": z3_gate,
        },
        "formal_scout_only": {
            "pass": PROMOTION_ALLOWED is False and "Formal scout only" in CLAIM_CEILING,
            "summary": "does not admit final Axis0, tensor-network runtime, scale-level basin, or canonical replacement claims",
        },
    }

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
        "nearby_variants": {
            "passed": sum(1 for value in checks.values() if value),
            "total": len(checks),
            "items": sorted(checks),
        },
        "why_not_v4_probes": (
            "Earlier v4 and old-runtime probes replayed PERCEPTION_L_MATRICES or "
            "older channel boundaries. This scout runs the source-aligned "
            "A0/A1/A2 terrain square, eight sheet-specific terrain realizations, "
            "and chart-role A6 XOR in a torch-native one-qubit engine runtime."
        ),
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "runtime_seconds": time.time() - started,
        "source_files": {
            "probe": rel(pathlib.Path(__file__).resolve()),
            "source_aligned_runtime": rel(ROOT / "source_aligned_qit_engine_runtime.py"),
            "old_canonical_specs": rel(ROOT / "canonical_qit_engine_specs.py"),
            "old_qit_engine_runtime": rel(ROOT / "qit_engine_runtime.py"),
        },
        "source_hashes": {
            "probe": sha256_file(pathlib.Path(__file__).resolve()),
            "source_aligned_runtime": sha256_file(ROOT / "source_aligned_qit_engine_runtime.py"),
            "old_canonical_specs": sha256_file(ROOT / "canonical_qit_engine_specs.py"),
            "old_qit_engine_runtime": sha256_file(ROOT / "qit_engine_runtime.py"),
        },
        "source_aligned_runtime": {
            "T1": rt.json_slim_engine_result(t1),
            "T2": rt.json_slim_engine_result(t2),
            "distances": {
                "T1_T2_final_fro": t_gap,
                "schedule_T1T2_vs_T2T1_fro": order_gap,
            },
            "schedule_T1T2": {
                "order": schedule_t1_t2["order"],
                "repeats": schedule_t1_t2["repeats"],
                "final_state": rt.jsonable_density(schedule_t1_t2["final_density"]),
            },
            "schedule_T2T1": {
                "order": schedule_t2_t1["order"],
                "repeats": schedule_t2_t1["repeats"],
                "final_state": rt.jsonable_density(schedule_t2_t1["final_density"]),
            },
        },
        "old_boundary_comparison": {
            "old_perception_l_table": old_l_table,
            "source_expected_terrain_laws": expected_laws,
            "old_runtime_fixed_bloch": old_bloch,
            "verdict": "old runtime runs, but its per-perception L table is not the source-aligned terrain law set",
        },
        "a6_xor_resolution": {
            "xor_uses": "A3_chart_role_inner_outer",
            "chart_role_bits": {"outer": +1, "inner": -1},
            "raw_path_bits_diagnostic": {"base": +1, "fiber": -1},
            "T1_raw_path_xor_ok": t1["all_raw_path_xor_ok"],
            "T2_raw_path_xor_ok": t2["all_raw_path_xor_ok"],
            "interpretation": "raw path is the geometry witness; chart role is the sign input to b6=-b0*b3",
        },
        "z3_nonpromotion_gate": z3_gate,
        "divergence_log": [
            {
                "control": "older_PERCEPTION_L_MATRICES_boundary",
                "observation": "old boundary maps four perceptions to one L matrix each; source-aligned runtime uses sheet-specific terrain law families",
                "status": "diverges_from_source_aligned_runtime",
            },
            {
                "control": "raw_fiber_base_xor",
                "observation": "passes Type 1 but fails Type 2 because Type 2 swaps fiber/base chart roles",
                "status": "killed_as_A6_xor_source",
            },
        ],
        "next_required_work": [
            "migrate consumers away from get_lindblad_params when they claim source-aligned terrain laws",
            "decide whether qit_engine_runtime.py should be patched in place or superseded by source_aligned_qit_engine_runtime.py",
            "extend this source-aligned runtime to MPDO/MPS before claiming full tensor-network engine execution",
            "keep Axis0 Xi bridge separate from this one-qubit engine pass",
        ],
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": rel(OUT_PATH), "all_pass": all_pass, "checks": checks}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
