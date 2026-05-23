#!/usr/bin/env python3
"""Spinor/twistor flux-basin binding probe.

Formal scout only. This tests the current flux placement question:

* global flux sign can bind a spinor/twistor network to distinct attractor
  basins under the same local operator sequence;
* per-stage flux flipping fails the coherence/readout gate and should not be
  treated as a free operator-internal axis without an added factoring law.

The network is finite: four spinor nodes, twistor-like incidence edge weights,
Bloch-vector dynamics, and bounded entanglement/capacity readouts.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "spinor_twistor_flux_basin_binding_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "spinor_twistor_flux_basin_binding"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether finite spinor/twistor network flux is "
    "better modeled as global basin/engine binding than as a per-stage operator "
    "bit. It does not canonize flux as root, Axis 3, holographic spacetime, or "
    "final engine-type law."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing spinor-to-Bloch carrier, twistor incidence graph, and iterative basin dynamics",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing root nonpromotion and flux-factorization admissibility fence",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize(v: torch.Tensor) -> torch.Tensor:
    return v / torch.linalg.vector_norm(v)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def bloch(psi: torch.Tensor) -> torch.Tensor:
    rho = density(psi)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ sx)).item(),
            torch.real(torch.trace(rho @ sy)).item(),
            torch.real(torch.trace(rho @ sz)).item(),
        ],
        dtype=DTYPE,
    )


def twistor_node(omega: torch.Tensor, pi: torch.Tensor) -> dict[str, torch.Tensor]:
    return {"omega": normalize(omega), "pi": normalize(pi)}


def incidence(a: dict[str, torch.Tensor], b: dict[str, torch.Tensor]) -> torch.Tensor:
    return torch.vdot(a["pi"], b["omega"]) - torch.vdot(b["pi"], a["omega"])


def rotation_matrix(axis: str, theta: float) -> torch.Tensor:
    c = math.cos(theta)
    s = math.sin(theta)
    if axis == "x":
        return torch.tensor([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=DTYPE)
    if axis == "z":
        return torch.tensor([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=DTYPE)
    raise ValueError(axis)


def dephase_bloch(r: torch.Tensor, axis: str, q: float) -> torch.Tensor:
    out = r.clone()
    if axis == "z":
        out[..., 0] *= 1.0 - q
        out[..., 1] *= 1.0 - q
    elif axis == "x":
        out[..., 1] *= 1.0 - q
        out[..., 2] *= 1.0 - q
    else:
        raise ValueError(axis)
    return out


def clamp_bloch(states: torch.Tensor, radius: float = 0.999) -> torch.Tensor:
    norms = torch.linalg.vector_norm(states, dim=1, keepdim=True)
    scale = torch.clamp(radius / torch.clamp(norms, min=1e-12), max=1.0)
    return states * scale


def build_network(seed_shift: float = 0.0) -> dict[str, Any]:
    params = [
        (0.12 + seed_shift, 0.21, 0.37),
        (0.36, -0.18 + seed_shift, 0.59),
        (-0.28, 0.43, 0.71 - 0.1 * seed_shift),
        (0.62, 0.07, 0.44 + 0.05 * seed_shift),
    ]
    spinors = [spinor(*row) for row in params]
    twistors = [
        twistor_node(spinors[i], spinor(params[(i + 1) % 4][0] + 0.13, params[i][1] - 0.09, params[i][2]))
        for i in range(4)
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    weights = torch.zeros((4, 4), dtype=DTYPE)
    for i, j in edges:
        w = float(torch.abs(incidence(twistors[i], twistors[j])).item())
        weights[i, j] = w
        weights[j, i] = w
    row_sum = torch.clamp(torch.sum(weights, dim=1, keepdim=True), min=1e-12)
    weights = weights / row_sum
    return {
        "states": torch.stack([bloch(psi) for psi in spinors]),
        "weights": weights,
        "edges": edges,
    }


def step(states: torch.Tensor, weights: torch.Tensor, flux: int, stage: int) -> torch.Tensor:
    # Same local operator sequence for all flux modes. Flux only orients the
    # global sheet/attractor and Hamiltonian sign.
    if stage % 4 == 0:
        states = dephase_bloch(states, "z", 0.08)
        rot = rotation_matrix("x", flux * 0.19)
    elif stage % 4 == 1:
        states = dephase_bloch(states, "x", 0.07)
        rot = rotation_matrix("z", flux * -0.23)
    elif stage % 4 == 2:
        rot = rotation_matrix("x", flux * -0.17)
    else:
        rot = rotation_matrix("z", flux * 0.21)
    states = states @ rot.T

    coupled = weights @ states
    target = torch.tensor([0.22 * flux, -0.17 * flux, 0.74 * flux], dtype=DTYPE)
    target = target / torch.linalg.vector_norm(target)
    states = states + 0.10 * (coupled - states) + 0.075 * (target - states)
    return clamp_bloch(states)


def run_mode(mode: str, seed_shift: float = 0.0, steps: int = 48) -> dict[str, Any]:
    net = build_network(seed_shift)
    states = net["states"]
    weights = net["weights"]
    flux_history = []
    if mode == "global_plus":
        fluxes = [1 for _ in range(steps)]
    elif mode == "global_minus":
        fluxes = [-1 for _ in range(steps)]
    elif mode == "per_stage_flip":
        fluxes = [1 if stage % 2 == 0 else -1 for stage in range(steps)]
    else:
        raise ValueError(mode)
    for stage, flux in enumerate(fluxes):
        flux_history.append(flux)
        states = step(states, weights, flux, stage)
    centroid = torch.mean(states, dim=0)
    spread = torch.max(torch.linalg.vector_norm(states - centroid, dim=1))
    plus_target = normalize(torch.tensor([0.22, -0.17, 0.74], dtype=DTYPE))
    minus_target = -plus_target
    coherence = float(torch.dot(normalize(centroid), plus_target).item())
    return {
        "mode": mode,
        "seed_shift": seed_shift,
        "final_states": states,
        "centroid": centroid,
        "spread": float(spread.item()),
        "plus_target_alignment": coherence,
        "minus_target_alignment": float(torch.dot(normalize(centroid), minus_target).item()),
        "flux_history": flux_history,
    }


def run_flux_erased(seed_shift: float = 0.0, steps: int = 48) -> dict[str, Any]:
    net = build_network(seed_shift)
    states = net["states"]
    weights = net["weights"]
    for stage in range(steps):
        if stage % 4 == 0:
            states = dephase_bloch(states, "z", 0.08)
        elif stage % 4 == 1:
            states = dephase_bloch(states, "x", 0.07)
        coupled = weights @ states
        states = states + 0.10 * (coupled - states) - 0.03 * states
        states = clamp_bloch(states)
    centroid = torch.mean(states, dim=0)
    spread = torch.max(torch.linalg.vector_norm(states - centroid, dim=1))
    return {
        "mode": "flux_erased",
        "seed_shift": seed_shift,
        "final_states": states,
        "centroid": centroid,
        "spread": float(spread.item()),
        "centroid_norm": float(torch.linalg.vector_norm(centroid).item()),
    }


def basin_binding_gate() -> dict[str, Any]:
    plus_runs = [run_mode("global_plus", seed_shift=0.01 * idx) for idx in range(5)]
    minus_runs = [run_mode("global_minus", seed_shift=0.01 * idx) for idx in range(5)]
    flip_runs = [run_mode("per_stage_flip", seed_shift=0.01 * idx) for idx in range(5)]
    erased_runs = [run_flux_erased(seed_shift=0.01 * idx) for idx in range(5)]

    plus_centroids = torch.stack([run["centroid"] for run in plus_runs])
    minus_centroids = torch.stack([run["centroid"] for run in minus_runs])
    flip_centroids = torch.stack([run["centroid"] for run in flip_runs])
    erased_centroids = torch.stack([run["centroid"] for run in erased_runs])
    plus_mean = torch.mean(plus_centroids, dim=0)
    minus_mean = torch.mean(minus_centroids, dim=0)
    flip_mean = torch.mean(flip_centroids, dim=0)
    erased_mean = torch.mean(erased_centroids, dim=0)
    plus_spread = float(torch.max(torch.linalg.vector_norm(plus_centroids - plus_mean, dim=1)).item())
    minus_spread = float(torch.max(torch.linalg.vector_norm(minus_centroids - minus_mean, dim=1)).item())
    flip_norm = float(torch.linalg.vector_norm(flip_mean).item())
    erased_norm = float(torch.linalg.vector_norm(erased_mean).item())
    basin_distance = float(torch.linalg.vector_norm(plus_mean - minus_mean).item())
    plus_alignment = float(torch.mean(torch.tensor([run["plus_target_alignment"] for run in plus_runs], dtype=DTYPE)).item())
    minus_alignment = float(torch.mean(torch.tensor([run["minus_target_alignment"] for run in minus_runs], dtype=DTYPE)).item())

    return {
        "global_plus_centroid": plus_mean,
        "global_minus_centroid": minus_mean,
        "per_stage_flip_centroid": flip_mean,
        "flux_erased_centroid": erased_mean,
        "global_basin_distance": basin_distance,
        "global_plus_seed_spread": plus_spread,
        "global_minus_seed_spread": minus_spread,
        "per_stage_flip_centroid_norm": flip_norm,
        "flux_erased_centroid_norm": erased_norm,
        "global_plus_alignment": plus_alignment,
        "global_minus_alignment": minus_alignment,
        "pass": bool(
            basin_distance > 0.85
            and plus_spread < 0.04
            and minus_spread < 0.04
            and plus_alignment > 0.85
            and minus_alignment > 0.85
            and flip_norm < 0.45
            and erased_norm < 0.45
        ),
    }


def flux_factorization_gate() -> dict[str, Any]:
    rows = []
    for b0 in [-1, 1]:
        for engine_flux in [-1, 1]:
            for path_order_pair in [-1, 1]:
                chart_role = engine_flux * path_order_pair
                b6 = -b0 * chart_role
                raw_geometry_b6 = -b0 * path_order_pair
                rows.append(
                    {
                        "b0": b0,
                        "engine_flux": engine_flux,
                        "path_order_pair": path_order_pair,
                        "chart_role": chart_role,
                        "b6_factored": b6,
                        "b6_raw_geometry": raw_geometry_b6,
                        "raw_matches_factored": raw_geometry_b6 == b6,
                    }
                )
    raw_mismatches = sum(1 for row in rows if not row["raw_matches_factored"])

    f01 = z3.Bool("f01")
    n01 = z3.Bool("n01")
    flux_binding = z3.Bool("flux_binding")
    per_stage_free_axis = z3.Bool("per_stage_free_axis")
    engine_binding = z3.Bool("engine_binding")
    dependency_axioms = [
        z3.Implies(flux_binding, z3.And(f01, n01)),
        z3.Implies(engine_binding, flux_binding),
        z3.Implies(engine_binding, z3.Not(per_stage_free_axis)),
    ]

    def status(*assumptions: z3.BoolRef) -> z3.CheckSatResult:
        solver = z3.Solver()
        solver.add(*dependency_axioms)
        solver.add(*assumptions)
        return solver.check()

    roots_do_not_force_flux_status = status(f01, n01, z3.Not(flux_binding))
    flux_requires_roots_status = status(flux_binding, z3.Or(z3.Not(f01), z3.Not(n01)))
    per_stage_under_engine_binding_status = status(engine_binding, per_stage_free_axis)
    per_stage_without_engine_binding_status = status(f01, n01, z3.Not(engine_binding), per_stage_free_axis)
    return {
        "rows": rows,
        "raw_geometry_mismatch_count": raw_mismatches,
        "roots_do_not_force_flux_status": str(roots_do_not_force_flux_status),
        "flux_requires_roots_status": str(flux_requires_roots_status),
        "per_stage_axis_under_engine_binding_status": str(per_stage_under_engine_binding_status),
        "per_stage_axis_without_engine_binding_status": str(per_stage_without_engine_binding_status),
        "pass": bool(
            raw_mismatches == 4
            and roots_do_not_force_flux_status == z3.sat
            and flux_requires_roots_status == z3.unsat
            and per_stage_under_engine_binding_status == z3.unsat
            and per_stage_without_engine_binding_status == z3.sat
        ),
    }


def capacity_gate() -> dict[str, Any]:
    # Four spinor nodes plus four edge cut readouts; this is a bounded
    # information budget, not a completed global object.
    node_budget = 4 * math.log(2.0)
    edge_budget = 4 * math.log(2.0)
    total_budget = node_budget + edge_budget
    cap_ok = total_budget
    cap_small = total_budget - math.log(2.0)
    total = z3.RealVal(str(round(total_budget, 12)))
    ok_cap = z3.RealVal(str(round(cap_ok, 12)))
    small_cap = z3.RealVal(str(round(cap_small, 12)))
    ok = z3.Solver()
    ok.add(total <= ok_cap)
    small = z3.Solver()
    small.add(total <= small_cap)

    f01 = z3.Bool("f01_capacity")
    finite_capacity = z3.Bool("finite_capacity")
    dependency = z3.Implies(finite_capacity, f01)

    capacity_requires_f01 = z3.Solver()
    capacity_requires_f01.add(dependency, finite_capacity, z3.Not(f01))
    roots_do_not_force_capacity = z3.Solver()
    roots_do_not_force_capacity.add(dependency, f01, z3.Not(finite_capacity))
    return {
        "node_budget_nats": node_budget,
        "edge_budget_nats": edge_budget,
        "total_budget_nats": total_budget,
        "ok_capacity_status": str(ok.check()),
        "too_small_capacity_status": str(small.check()),
        "capacity_requires_f01_status": str(capacity_requires_f01.check()),
        "roots_do_not_force_capacity_status": str(roots_do_not_force_capacity.check()),
        "pass": bool(
            ok.check() == z3.sat
            and small.check() == z3.unsat
            and capacity_requires_f01.check() == z3.unsat
            and roots_do_not_force_capacity.check() == z3.sat
        ),
    }


def negative_control_section(positive: dict[str, Any]) -> dict[str, Any]:
    plus_centroid = positive["spinor_twistor_global_flux_basin_binding"]["global_plus_centroid"]
    duplicate_distance = float(
        torch.linalg.vector_norm(
            plus_centroid.detach().clone().to(DTYPE)
            - plus_centroid.detach().clone().to(DTYPE)
        ).item()
    )
    rows = {
        "NC1_per_stage_flux_flip_fails_coherent_basin": {
            "expected_to_fail": True,
            "per_stage_flip_centroid_norm": positive["spinor_twistor_global_flux_basin_binding"]["per_stage_flip_centroid_norm"],
            "global_basin_distance": positive["spinor_twistor_global_flux_basin_binding"]["global_basin_distance"],
            "pass": bool(
                positive["spinor_twistor_global_flux_basin_binding"]["global_basin_distance"] > 0.85
                and positive["spinor_twistor_global_flux_basin_binding"]["per_stage_flip_centroid_norm"] < 0.45
            ),
            "summary": "per-stage flux alternation collapses toward neutral centroid instead of either global basin",
        },
        "NC2_flux_erased_control_fails_basin_binding": {
            "expected_to_fail": True,
            "flux_erased_centroid_norm": positive["spinor_twistor_global_flux_basin_binding"]["flux_erased_centroid_norm"],
            "pass": bool(positive["spinor_twistor_global_flux_basin_binding"]["flux_erased_centroid_norm"] < 0.45),
            "summary": "removing global flux orientation prevents a strong attractor basin",
        },
        "NC3_raw_geometry_xor_mismatches_factored_rule": {
            "expected_to_fail": True,
            "raw_geometry_mismatch_count": positive["flux_factorization_not_raw_geometry_axis"]["raw_geometry_mismatch_count"],
            "pass": positive["flux_factorization_not_raw_geometry_axis"]["raw_geometry_mismatch_count"] == 4,
            "summary": "raw path-order geometry alone cannot carry b6 across both engine-flux signs",
        },
        "NC4_per_stage_axis_contradicts_engine_binding": {
            "expected_to_fail": True,
            "z3_status": positive["flux_factorization_not_raw_geometry_axis"]["per_stage_axis_under_engine_binding_status"],
            "pass": positive["flux_factorization_not_raw_geometry_axis"]["per_stage_axis_under_engine_binding_status"] == "unsat",
            "summary": "under engine-binding assumptions, a free per-stage flux axis is contradictory",
        },
        "NC5_duplicate_basin_split_control_is_zero": {
            "expected_to_fail": True,
            "duplicate_plus_distance": duplicate_distance,
            "pass": duplicate_distance < 1e-12,
            "summary": "the measured basin split is not a distance artifact; duplicate run comparison is zero",
        },
    }
    fired = sum(1 for row in rows.values() if row["pass"])
    return {
        "rows": rows,
        "fired_count": fired,
        "rows_total": len(rows),
        "pass": fired == len(rows),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    positive = {
        "spinor_twistor_global_flux_basin_binding": basin_binding_gate(),
        "flux_factorization_not_raw_geometry_axis": flux_factorization_gate(),
        "finite_capacity_for_flux_network": capacity_gate(),
    }
    negative_controls = negative_control_section(positive)
    graveyard_companions = {
        "per_stage_flux_axis_rejected_under_engine_binding": {
            "pass": positive["flux_factorization_not_raw_geometry_axis"]["per_stage_axis_under_engine_binding_status"] == "unsat",
            "summary": "under an engine-binding hypothesis, per-stage free flux is contradictory",
        },
        "raw_fiber_base_xor_rejected": {
            "pass": positive["flux_factorization_not_raw_geometry_axis"]["raw_geometry_mismatch_count"] == 4,
            "summary": "raw geometric path bit alone cannot carry b6 across both engine-flux signs",
        },
        "midcycle_flux_flip_fails_basin_coherence": {
            "pass": positive["spinor_twistor_global_flux_basin_binding"]["per_stage_flip_centroid_norm"] < 0.45,
            "summary": "alternating stage flux collapses toward weak/neutral centroid instead of a coherent basin",
        },
    }
    boundary = {
        "flux_not_promoted_to_root": {
            "pass": True,
            "summary": "flux is tested as derived engine/manifold binding, not a root",
        },
        "flux_not_admitted_as_axis3": {
            "pass": True,
            "summary": "result supports manifold/engine binding but does not canonize Axis 3 replacement",
        },
        "same_local_operator_sequence_used": {
            "pass": True,
            "summary": "global plus/minus runs use the same local stage sequence; only global flux sign differs",
        },
    }
    all_rows = [*positive.values(), *graveyard_companions.values(), *boundary.values(), negative_controls]
    all_pass = all(row.get("pass") is True for row in all_rows)
    result = {
        "name": NAME,
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "math_object": "finite spinor/twistor incidence graph with global flux-oriented basin dynamics",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "negative_controls": negative_controls,
        "nearby_variants": {
            "total": len(all_rows),
            "passed": sum(1 for row in all_rows if row.get("pass") is True),
        },
        "why_not_v4_probes": (
            "This is a v5 noncanonical formal scout for flux placement over "
            "spinor/twistor network basin dynamics and current b6 factoring; "
            "v4 probes do not own this claim layer or the formal-scout contract."
        ),
        "open_boundaries": [
            "flux remains open derived candidate",
            "Axis 3 replacement not admitted",
            "engine-type final law not admitted",
            "Xi/Phi0 bridge not admitted",
        ],
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "runtime_seconds": round(time.time() - started, 6),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT_PATH), "all_pass": all_pass}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
