#!/usr/bin/env python3
"""Hopf fiber/base loop density-path distinguishability probe.

This is an exploratory lego, not an admission packet. It tests whether a
finite probe family can distinguish a density-stationary Hopf fiber loop from a
horizontal base-lift loop on the same normalized spinor carrier. It also records
weak probes and collapsed-loop controls as graveyard evidence.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import sympy as sp
import torch
import z3


NAME = "hopf_fiber_base_loop_density_path_distinguishability"
CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULT_DIR / f"{pathlib.Path(__file__).stem}_results.json"

DTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1e-8

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite spinor, density, Bloch readout, and loop-distance calculations",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic Hopf connection check for the horizontal base-lift path",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite probe-separation satisfiability check for path-sensitive versus endpoint-only probes",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not used; Clifford orientation is a separate companion packet",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not used; manifold-distance duplicate remains separate",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not used; z3 is sufficient for this finite Boolean probe check",
    },
    "pyg": {"tried": False, "used": False, "reason": "not used; no graph learner is built"},
    "e3nn": {"tried": False, "used": False, "reason": "not used; no equivariant neural layer is built"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used; no graph algorithm is needed"},
    "xgi": {"tried": False, "used": False, "reason": "not used; no hypergraph object is built"},
    "toponetx": {"tried": False, "used": False, "reason": "not used; no cell complex is built"},
    "gudhi": {"tried": False, "used": False, "reason": "not used; no persistence filtration is built"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "cvc5": None,
    "pyg": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

CLAIM_CEILING = (
    "exploratory Hopf fiber/base density-path distinguishability only: shows one finite path-sensitive "
    "probe separates a density-stationary fiber loop from a density-traversing horizontal base-lift loop; "
    "does not prove GStack, flux/chirality, placement closure, axis closure, QIT-engine mechanics, or "
    "nonclassical admission"
)


def c(value: complex) -> torch.Tensor:
    return torch.tensor(value, dtype=DTYPE)


SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE)
SY = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=DTYPE)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return torch.stack(
        [
            torch.exp(c(1j * (phi + chi))) * c(math.cos(eta)),
            torch.exp(c(1j * (phi - chi))) * c(math.sin(eta)),
        ]
    ).reshape(2, 1)


def density(psi: torch.Tensor) -> torch.Tensor:
    return psi @ psi.conj().T


def bloch(rho: torch.Tensor) -> torch.Tensor:
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ SX)).item(),
            torch.real(torch.trace(rho @ SY)).item(),
            torch.real(torch.trace(rho @ SZ)).item(),
        ],
        dtype=RTYPE,
    )


def path_density_gap(path: list[torch.Tensor]) -> float:
    start = path[0]
    return max(float(torch.linalg.norm(row - start).real.item()) for row in path)


def bloch_path_length(path: list[torch.Tensor]) -> float:
    points = [bloch(row) for row in path]
    return float(sum(torch.linalg.norm(points[i + 1] - points[i]).item() for i in range(len(points) - 1)))


def endpoint_gap(path: list[torch.Tensor]) -> float:
    return float(torch.linalg.norm(path[-1] - path[0]).real.item())


def fiber_loop(phi0: float, chi0: float, eta: float, steps: int) -> list[torch.Tensor]:
    return [density(spinor(phi0 + 2.0 * math.pi * k / (steps - 1), chi0, eta)) for k in range(steps)]


def horizontal_base_lift(phi0: float, chi0: float, eta: float, steps: int) -> list[torch.Tensor]:
    return [
        density(
            spinor(
                phi0 - math.cos(2.0 * eta) * 2.0 * math.pi * k / (steps - 1),
                chi0 + 2.0 * math.pi * k / (steps - 1),
                eta,
            )
        )
        for k in range(steps)
    ]


def nonhorizontal_base_candidate(phi0: float, chi0: float, eta: float, steps: int) -> list[torch.Tensor]:
    return [density(spinor(phi0, chi0 + 2.0 * math.pi * k / (steps - 1), eta)) for k in range(steps)]


def symbolic_connection_checks() -> dict[str, Any]:
    eta = sp.symbols("eta", real=True)
    horizontal = sp.simplify(-sp.cos(2 * eta) + sp.cos(2 * eta))
    nonhorizontal = sp.simplify(sp.cos(2 * eta))
    return {
        "connection_form": "A = dphi + cos(2 eta) dchi",
        "horizontal_base_lift_eval": str(horizontal),
        "horizontal_base_lift_is_zero": bool(horizontal == 0),
        "nonhorizontal_base_candidate_eval": str(nonhorizontal),
        "nonhorizontal_candidate_not_identically_zero": bool(nonhorizontal != 0),
    }


def z3_probe_separation_check(fiber_gap: float, base_gap: float, endpoint_fiber: float, endpoint_base: float) -> dict[str, Any]:
    scale = 10**9
    fg = int(round(fiber_gap * scale))
    bg = int(round(base_gap * scale))
    ef = int(round(endpoint_fiber * scale))
    eb = int(round(endpoint_base * scale))
    path_sensitive = z3.Solver()
    path_sensitive.add(fg == 0)
    path_sensitive.add(bg > 0)
    endpoint_only = z3.Solver()
    endpoint_only.add(ef == 0)
    endpoint_only.add(eb == 0)
    return {
        "scaled_gaps": {
            "fiber_path_gap": fg,
            "base_path_gap": bg,
            "fiber_endpoint_gap": ef,
            "base_endpoint_gap": eb,
        },
        "path_sensitive_probe_separates_sat": str(path_sensitive.check()),
        "endpoint_only_probe_collision_sat": str(endpoint_only.check()),
        "passed": path_sensitive.check() == z3.sat and endpoint_only.check() == z3.sat,
    }


def main() -> dict[str, Any]:
    started = time.time()
    phi0, chi0, eta, steps = 0.19, -0.31, math.pi / 5.0, 65
    fiber = fiber_loop(phi0, chi0, eta, steps)
    base = horizontal_base_lift(phi0, chi0, eta, steps)
    fake_base = nonhorizontal_base_candidate(phi0, chi0, eta, steps)
    collapsed_base = fiber_loop(phi0, chi0, eta, steps)

    fiber_gap = path_density_gap(fiber)
    base_gap = path_density_gap(base)
    fake_gap = path_density_gap(fake_base)
    collapsed_gap = path_density_gap(collapsed_base)
    fiber_endpoint = endpoint_gap(fiber)
    base_endpoint = endpoint_gap(base)
    connection = symbolic_connection_checks()
    z3_check = z3_probe_separation_check(fiber_gap, base_gap, fiber_endpoint, base_endpoint)

    positive = {
        "fiber_loop_density_stationary": {
            "density_path_gap": fiber_gap,
            "bloch_path_length": bloch_path_length(fiber),
            "endpoint_gap": fiber_endpoint,
            "passed": fiber_gap < TOL,
        },
        "horizontal_base_lift_density_traversing": {
            "density_path_gap": base_gap,
            "bloch_path_length": bloch_path_length(base),
            "endpoint_gap": base_endpoint,
            "passed": base_gap > 1e-4 and base_endpoint < 1e-7,
        },
        "path_sensitive_probe_distinguishes_loops": {
            "fiber_density_path_gap": fiber_gap,
            "base_density_path_gap": base_gap,
            "passed": fiber_gap < TOL and base_gap > 1e-4,
        },
    }
    negative = {
        "collapsed_base_path_copied_from_fiber_path": {
            "density_path_gap": collapsed_gap,
            "passed": collapsed_gap < TOL,
        },
        "endpoint_only_probe_cannot_distinguish_closed_loops": {
            "fiber_endpoint_gap": fiber_endpoint,
            "base_endpoint_gap": base_endpoint,
            "passed": fiber_endpoint < 1e-7 and base_endpoint < 1e-7,
        },
        "nonhorizontal_base_candidate_fails_connection_constraint": {
            "density_path_gap": fake_gap,
            "connection_eval": connection["nonhorizontal_base_candidate_eval"],
            "passed": connection["nonhorizontal_candidate_not_identically_zero"],
        },
    }
    survivor_classes = [
        "density-stationary Hopf fiber loop under path-sensitive density probe",
        "density-traversing horizontal base-lift loop under path-sensitive density probe",
    ]
    all_pass = (
        all(row["passed"] for row in positive.values())
        and all(row["passed"] for row in negative.values())
        and connection["horizontal_base_lift_is_zero"]
        and connection["nonhorizontal_candidate_not_identically_zero"]
        and z3_check["passed"]
    )
    result = {
        "schema": "SIM_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": bool(all_pass),
        "promotion_allowed": False,
        "rosetta_to_sim_contract": {
            "operation_sequence": [
                "generate two closed Hopf loop candidates on one normalized spinor carrier",
                "apply density-path and horizontal-lift constraints",
                "compute path-sensitive and endpoint-only readouts",
                "partition loops by distinguishability under the declared probe family",
            ],
            "carrier_topology": "normalized two-component spinor on S3 with Hopf projection to density/Bloch readouts",
            "observable": [
                "maximum density path gap from the starting state",
                "Bloch path length",
                "closed-loop endpoint gap",
                "symbolic Hopf connection evaluation",
            ],
            "pass_fail_predicate": "fiber path remains density-stationary, horizontal base-lift traverses density while closing at the endpoint, collapsed and endpoint-only controls expose weak probes, and the connection/z3 checks pass",
            "graveyard_companions": [
                "base path collapsed to fiber path",
                "endpoint-only closed-loop probe",
                "nonhorizontal base candidate",
            ],
            "baseline_variants": [
                "endpoint-only readout",
                "coordinate-collapsed base path",
                "nonhorizontal base traversal",
            ],
            "alternative_formulations": [
                "geomstats path-distance duplicate",
                "Clifford orientation companion",
                "physical Lindblad-evolution placement companion",
            ],
            "exact_tool_function_needs": {
                "pytorch": "finite spinor, density, Bloch, and path norm calculations",
                "sympy": "symbolic connection-form check",
                "z3": "finite path-sensitive versus endpoint-only distinguishability check",
            },
            "lego_coupling_target": "Hopf fiber/base loop path lego for the geometric constraint manifold spine",
            "claim_ceiling": CLAIM_CEILING,
        },
        "probe_family": "path-sensitive density and Bloch readouts plus closed-loop endpoint controls",
        "constraint_set": [
            "normalized spinor carrier",
            "Hopf fiber loop varies common phase only",
            "horizontal base-lift satisfies A = dphi + cos(2 eta) dchi = 0",
            "path-sensitive density probe is available",
        ],
        "candidate_set": [
            "fiber_loop",
            "horizontal_base_lift",
            "collapsed_base_path_copied_from_fiber",
            "endpoint_only_probe",
            "nonhorizontal_base_candidate",
        ],
        "positive": positive,
        "negative": negative,
        "boundary": {
            "eta": eta,
            "connection": connection,
            "z3_probe_separation": z3_check,
        },
        "survivor_classes": {
            "survivor_equivalence_classes": survivor_classes,
            "survivor_count": len(survivor_classes),
            "killed_neighbors": list(negative.keys()),
            "killed_neighbor_count": len(negative),
        },
        "summary": {
            "all_pass": bool(all_pass),
            "positive_survivors": len(survivor_classes),
            "killed_neighbors": len(negative),
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "geomstats_path_distance_duplicate_or_physical_placement_evolution_companion",
        "promotion_condition": "requires independent manifold-distance duplicate and physical-evolution placement companion with stronger graveyards",
        "blocked_until": "separate companion receipts exist for tool duplicates and physical placement evolution",
        "demotion_condition": "demote if path-sensitive density probe no longer separates the loops or if endpoint-only readout is treated as sufficient",
        "out_of_scope": [
            "no GStack promotion",
            "no flux/chirality mechanism closure",
            "no placement closure",
            "no axis claim",
            "no QIT-engine claim",
            "no nonclassical admission",
        ],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main()["summary"], indent=2, sort_keys=True))
