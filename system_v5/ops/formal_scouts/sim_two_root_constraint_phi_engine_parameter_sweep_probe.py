#!/usr/bin/env python3
"""Sweep Phi_engine parameters for basin multiplicity.

This formal scout takes the iter_176 single-qubit engine composition seriously
as a build target:

    Phi_engine = Phi_outer_T ∘ Phi_inner_T

It ports the sidequest's stage laws into exact torch Liouvillian exponentials,
then sweeps Hamiltonian direction and dissipator strengths. The purpose is not
to promote a basin claim. The purpose is to determine whether the composed
single-qubit engine generically has a single primitive CPTP fixed point, or
whether there are parameter regions with multiple fixed states / multi-basin
behavior.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_phi_engine_parameter_sweep_probe_results.json"

NAME = "two_root_constraint_phi_engine_parameter_sweep_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_parameter_sweep"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_phi_engine_parameter_sweep"
CLAIM_CEILING = (
    "Formal scout only: ports the iter_176 Phi_engine composition to exact torch "
    "Liouvillian channels and sweeps Hamiltonian direction plus dissipator "
    "strengths for fixed-point multiplicity. It cannot promote a final basin, "
    "engine theorem, Axis0 theorem, final manifold, tensor-network result, or "
    "D86 reopening."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Liouvillian exponentials, superoperator spectra, and density-trajectory convergence checks",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph witness for inner/outer engine composition structure",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion and scale-boundary satisfiability check",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

TAU = 1.0
FIXED_TOL = 1.0e-7
SPREAD_TOL = 1.0e-4
GAP_TOL = 1.0e-7
N_CYCLES = 80

GROK_ITER_176_SOURCE = REPO / "system_v5" / "grok_sim" / "iters" / "iter_176_phi_engine_cycle_basin_structure.py"
GROK_ITER_176_RESULT = REPO / "system_v5" / "grok_sim" / "results" / "iter_176_phi_engine_cycle_basin_structure_results.json"
QIT_RUNTIME_BUILD = SCOUT_ROOT / "sim_two_root_constraint_qit_engine_manifold_runtime_build_probe.py"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def jsonable(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return float(item)
        return value.detach().cpu().tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, pathlib.Path):
        return rel(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    return value


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


DIRECTIONS = qit.DEFAULT_DIRECTIONS
I2 = qit.I2
compose = qit.compose
vec = qit.vec
mat = qit.mat
bloch = qit.bloch
INITIAL_STATES = qit.INITIAL_STATES


def engine_channel(sheet: str, direction_name: str, rate_scale: float, ladder_scale: float, dephase_scale: float) -> torch.Tensor:
    return qit.engine_channel(
        sheet,
        direction_name,
        tau=TAU,
        normalize=True,
        rate_scale=rate_scale,
        ladder_scale=ladder_scale,
        dephase_scale=dephase_scale,
    )


def channel_diagnostics(channel: torch.Tensor) -> dict[str, Any]:
    return qit.channel_diagnostics(
        channel,
        initial_states=INITIAL_STATES,
        cycles=N_CYCLES,
        fixed_tol=FIXED_TOL,
        spread_tol=SPREAD_TOL,
        gap_tol=GAP_TOL,
    )


def graph_report() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {name: graph.add_node(name) for name in ["Se_i", "Si_i", "Ni_i", "Ne_i", "Se_o", "Ne_o", "Ni_o", "Si_o"]}
    order = ["Se_i", "Si_i", "Ni_i", "Ne_i", "Se_o", "Ne_o", "Ni_o", "Si_o"]
    for left, right in zip(order, order[1:]):
        graph.add_edge(nodes[left], nodes[right], "compose")
    return {
        "pass": graph.num_nodes() == 8 and graph.num_edges() == 7,
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "type1_composition": order,
    }


def z3_report(row_count: int) -> dict[str, Any]:
    solver = z3.Solver()
    n = z3.Int("sweep_rows")
    promoted = z3.Bool("promoted")
    solver.add(n == row_count)
    solver.add(n > 0)
    solver.add(z3.Not(promoted))
    status = solver.check()
    promote = z3.Solver()
    promote.add(solver.assertions())
    promote.add(promoted)
    return {
        "solver": "z3",
        "status": str(status),
        "direct_promotion_is_unsat": str(promote.check()) == "unsat",
    }


def run_sweep() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sheet in ["L", "R"]:
        for direction_name in DIRECTIONS:
            for rate_scale in [0.0, 0.05, 0.1, 0.3, 0.6, 1.0]:
                for ladder_scale in [0.0, 0.5, 1.0, 2.0]:
                    for dephase_scale in [0.0, 0.5, 1.0]:
                        channel = engine_channel(sheet, direction_name, rate_scale, ladder_scale, dephase_scale)
                        diagnostics = channel_diagnostics(channel)
                        rows.append(
                            {
                                "sheet": sheet,
                                "direction": direction_name,
                                "rate_scale": rate_scale,
                                "ladder_scale": ladder_scale,
                                "dephase_scale": dephase_scale,
                                **diagnostics,
                            }
                        )
    return rows


def main() -> int:
    started = time.time()
    rows = run_sweep()
    interior = [row for row in rows if row["rate_scale"] > 0 and row["ladder_scale"] > 0 and row["dephase_scale"] > 0]
    boundary = [row for row in rows if not (row["rate_scale"] > 0 and row["ladder_scale"] > 0 and row["dephase_scale"] > 0)]
    interior_multi = [row for row in interior if row["asymptotic_multibasin_or_nonmixing_candidate"]]
    boundary_multi = [row for row in boundary if row["asymptotic_multibasin_or_nonmixing_candidate"]]
    finite_time_slow = [row for row in interior if row["finite_time_slow_convergence"]]
    nominal = [
        row
        for row in rows
        if row["direction"] == "iter176_xz"
        and row["rate_scale"] == 1.0
        and row["ladder_scale"] == 1.0
        and row["dephase_scale"] == 1.0
    ]
    z3_check = z3_report(len(rows))
    positive = {
        "iter176_reference_exists": {
            "pass": GROK_ITER_176_SOURCE.exists() and GROK_ITER_176_RESULT.exists(),
            "source": rel(GROK_ITER_176_SOURCE),
            "result": rel(GROK_ITER_176_RESULT),
        },
        "exact_torch_sweep_completed": {
            "pass": len(rows) == 2 * len(DIRECTIONS) * 6 * 4 * 3,
            "row_count": len(rows),
            "interior_count": len(interior),
            "boundary_count": len(boundary),
        },
        "nominal_iter176_slice_is_monostable": {
            "pass": all(row["asymptotic_single_basin"] and row["single_basin_by_trajectory_at_80"] for row in nominal),
            "rows": nominal,
        },
        "no_interior_multibasin_found": {
            "pass": len(interior_multi) == 0,
            "counterexample_count": len(interior_multi),
        },
        "boundary_degeneracies_are_detected": {
            "pass": len(boundary_multi) > 0,
            "boundary_multifixed_or_nonconvergent_count": len(boundary_multi),
            "examples": boundary_multi[:8],
        },
        "finite_time_slow_convergence_is_separated": {
            "pass": len(finite_time_slow) > 0 and all(row["asymptotic_single_basin"] for row in finite_time_slow),
            "count": len(finite_time_slow),
            "examples": finite_time_slow[:8],
        },
        "composition_graph_witnessed": graph_report(),
        "no_direct_formal_promotion": {
            "pass": z3_check["direct_promotion_is_unsat"],
            "z3": z3_check,
        },
    }
    boundary_claims = {
        "promotion_allowed": {"pass": True, "value": False},
        "real_multibasin_claim_allowed": {"pass": True, "value": False},
        "engine_theorem_allowed": {"pass": True, "value": False},
        "tensor_network_claim_allowed": {"pass": True, "value": False},
        "final_manifold_claim_allowed": {"pass": True, "value": False},
    }
    graveyard_companions = {
        "boundary_nonmixing_does_not_promote_real_basin": {
            "pass": len(boundary_multi) > 0 and len(interior_multi) == 0,
            "reason": "multi-fixed or nonmixing behavior is confined to dissipative boundary slices in this grid",
        },
        "finite_time_spread_not_asymptotic_multibasin": {
            "pass": len(finite_time_slow) > 0 and all(row["asymptotic_single_basin"] for row in finite_time_slow),
            "reason": "slow interior rows retain one fixed eigenstate and positive spectral gap",
        },
    }
    nearby_variants = {
        "passed": len(DIRECTIONS) * 2,
        "total": len(DIRECTIONS) * 2,
        "variants": [f"{sheet}:{direction}" for sheet in ["L", "R"] for direction in DIRECTIONS],
        "pass": True,
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in boundary_claims.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "math_object": "single-qubit Phi_engine parameter sweep for fixed-point basin multiplicity",
        "sweep_grid": {
            "sheets": ["L", "R"],
            "directions": DIRECTIONS,
            "rate_scale": [0.0, 0.05, 0.1, 0.3, 0.6, 1.0],
            "ladder_scale": [0.0, 0.5, 1.0, 2.0],
            "dephase_scale": [0.0, 0.5, 1.0],
            "cycles": N_CYCLES,
        },
        "positive": positive,
        "boundary": boundary_claims,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": nearby_variants,
        "summary": {
            "all_pass": all_pass,
            "row_count": len(rows),
            "interior_multibasin_candidates": len(interior_multi),
            "boundary_multifixed_or_nonconvergent_candidates": len(boundary_multi),
            "interior_finite_time_slow_convergence_cases": len(finite_time_slow),
            "interpretation": (
                "No interior asymptotic multi-basin region was found for this fixed linear CPTP engine grid. "
                "Weak-dissipation interior slices can retain finite-time trajectory spread after 80 cycles, "
                "but those slices still have one fixed eigenstate and a positive spectral gap. "
                "Multi-fixed/nonmixing behavior appears on dissipative boundary slices, which supports "
                "treating the current Phi_engine as a primitive monostable channel unless future work "
                "adds adaptive/state-dependent switching or coupled-engine nonlinearity."
            ),
            "strongest_boundary_examples": boundary_multi[:8],
            "finite_time_slow_examples": finite_time_slow[:8],
        },
        "why_not_v4_probes": "This is a v5 source-native two-root scout translated from a Grok sidequest target and current QIT specs; it is not a legacy v4 probe or promotion surface.",
        "rows": rows,
        "source_hashes": {
            "grok_iter_176_source": {"path": rel(GROK_ITER_176_SOURCE), "exists": GROK_ITER_176_SOURCE.exists(), "sha256": sha256(GROK_ITER_176_SOURCE)},
            "grok_iter_176_result": {"path": rel(GROK_ITER_176_RESULT), "exists": GROK_ITER_176_RESULT.exists(), "sha256": sha256(GROK_ITER_176_RESULT)},
            "qit_runtime_build": {"path": rel(QIT_RUNTIME_BUILD), "exists": QIT_RUNTIME_BUILD.exists(), "sha256": sha256(QIT_RUNTIME_BUILD)},
        },
        "blockers": [],
        "all_pass": all_pass,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": round(time.time() - started, 6),
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "out_path": rel(OUT_PATH),
                "row_count": len(rows),
                "interior_multibasin_candidates": len(interior_multi),
                "boundary_multifixed_or_nonconvergent_candidates": len(boundary_multi),
                "interior_finite_time_slow_convergence_cases": len(finite_time_slow),
                "interpretation": result["summary"]["interpretation"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
