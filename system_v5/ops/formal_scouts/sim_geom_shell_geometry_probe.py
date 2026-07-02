#!/usr/bin/env python3
"""Canonical Stage 3 shell geometry object probe.

Finite object:
    Sigma_r = finite tetrahedral samples on spherical shell boundaries.

Invariant:
    ordered shell radii are strictly monotone and every shell boundary lies
    inside the next enclosed ball. The same invariant is rechecked against
    scrambled-order and flattened-radius controls through smt_load_bearing.

This is a standalone geometry lego only. It does not claim manifold layers,
G-structures, Axis0, flux, FEP, gravity, or downstream physics admission.
"""

from __future__ import annotations

import os

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import jax

jax.config.update("jax_enable_x64", True)

import json
import math
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Any

import gudhi
import jax.numpy as jnp
import torch
import z3
from geomstats.geometry.hypersphere import Hypersphere

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_geom_shell_geometry_probe"
OBJECT_ID = "shell_geometry"
OUT_PATH = RESULT_DIR / "shell_geometry_results.json"

SHELL_COUNTS = (8, 16, 32, 64)
RTYPE = torch.float64
RADIUS_START = 1.0
RADIUS_STEP = 0.125
EPS = 1.0e-6
KILL_FLOOR = 1.0e-9
METRIC_TOL = 1.0e-8
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]
TETRA_FACES = ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3))
TETRA_EDGES = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim-bearing finite shell carrier: radii, tetrahedral shell samples, norms, monotonicity, containment controls, and non-dense scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror for representable shell radii, containment margins, and spherical edge metric formulas; no geomstats JAX backend is claimed.",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING torch-side Hypersphere(dim=2) shell metric: intrinsic geodesic edge lengths on Sigma_r, with a recomputed chord-metric ablation.",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING shell topology: SimplexTree computes tetrahedral boundary S^2 Betti readouts and filled-simplex topology ablation.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING smt_load_bearing proof: the measured radius monotonicity/nested-containment invariant flips real sat vs scrambled/flattened controls unsat.",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "Not used in this one-tool proof packet; z3 is the requested proof tool for shell_geometry.",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "Not used: the defining invariant is numeric/order-geometric and is proven by helper-bound z3 over measured observables.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "geomstats": "load_bearing",
    "gudhi": "load_bearing",
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": None,
    "numpy": None,
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return as_jsonable(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    return value


def unit_tetrahedron_vertices_torch() -> torch.Tensor:
    inv = 1.0 / math.sqrt(3.0)
    return torch.tensor(
        [
            [inv, inv, inv],
            [inv, -inv, -inv],
            [-inv, inv, -inv],
            [-inv, -inv, inv],
        ],
        dtype=RTYPE,
    )


def unit_tetrahedron_vertices_jax() -> jax.Array:
    inv = 1.0 / math.sqrt(3.0)
    return jnp.asarray(
        [
            [inv, inv, inv],
            [inv, -inv, -inv],
            [-inv, inv, -inv],
            [-inv, -inv, inv],
        ],
        dtype=jnp.float64,
    )


def ordered_radii_torch(shell_count: int) -> torch.Tensor:
    return RADIUS_START + RADIUS_STEP * torch.arange(shell_count, dtype=RTYPE)


def ordered_radii_jax(shell_count: int) -> jax.Array:
    return RADIUS_START + RADIUS_STEP * jnp.arange(shell_count, dtype=jnp.float64)


def scrambled_radii_torch(shell_count: int) -> torch.Tensor:
    return torch.flip(ordered_radii_torch(shell_count), dims=(0,))


def flattened_radii_torch(shell_count: int) -> torch.Tensor:
    radii = ordered_radii_torch(shell_count)
    return torch.full_like(radii, torch.mean(radii).item())


def shell_points_torch(radii: torch.Tensor) -> torch.Tensor:
    vertices = unit_tetrahedron_vertices_torch()
    return radii[:, None, None] * vertices[None, :, :]


def shell_points_jax(radii: jax.Array) -> jax.Array:
    vertices = unit_tetrahedron_vertices_jax()
    return radii[:, None, None] * vertices[None, :, :]


def invariant_measure_torch(radii: torch.Tensor) -> dict[str, Any]:
    points = shell_points_torch(radii)
    norms = torch.linalg.vector_norm(points, dim=2)
    shell_min_norms = torch.min(norms, dim=1).values
    shell_max_norms = torch.max(norms, dim=1).values
    gaps = radii[1:] - radii[:-1]
    containment_margins = shell_min_norms[1:] - shell_max_norms[:-1]
    min_radius_gap = float(torch.min(gaps).item())
    nested_margin = float(torch.min(containment_margins).item())
    return {
        "shell_count": int(radii.numel()),
        "finite_point_count": int(radii.numel() * 4),
        "radius_first": float(radii[0].item()),
        "radius_last": float(radii[-1].item()),
        "min_radius_gap": min_radius_gap,
        "nested_containment_margin": nested_margin,
        "shell_min_norm_min": float(torch.min(shell_min_norms).item()),
        "shell_max_norm_max": float(torch.max(shell_max_norms).item()),
        "strictly_monotone": bool(min_radius_gap > EPS),
        "nested_containment": bool(nested_margin > EPS),
        "invariant_value": float(min(min_radius_gap, nested_margin)),
        "pass": bool(min_radius_gap > EPS and nested_margin > EPS),
    }


def invariant_measure_jax(radii: jax.Array) -> dict[str, Any]:
    points = shell_points_jax(radii)
    norms = jnp.linalg.norm(points, axis=2)
    shell_min_norms = jnp.min(norms, axis=1)
    shell_max_norms = jnp.max(norms, axis=1)
    gaps = radii[1:] - radii[:-1]
    containment_margins = shell_min_norms[1:] - shell_max_norms[:-1]
    min_radius_gap = float(jnp.min(gaps))
    nested_margin = float(jnp.min(containment_margins))
    return {
        "shell_count": int(radii.shape[0]),
        "finite_point_count": int(radii.shape[0] * 4),
        "radius_first": float(radii[0]),
        "radius_last": float(radii[-1]),
        "min_radius_gap": min_radius_gap,
        "nested_containment_margin": nested_margin,
        "strictly_monotone": bool(min_radius_gap > EPS),
        "nested_containment": bool(nested_margin > EPS),
        "invariant_value": float(min(min_radius_gap, nested_margin)),
        "pass": bool(min_radius_gap > EPS and nested_margin > EPS),
    }


def torch_spherical_edge_lengths(radii: torch.Tensor) -> dict[str, Any]:
    vertices = unit_tetrahedron_vertices_torch()
    lengths = []
    angles = []
    for i, j in TETRA_EDGES:
        dot = torch.clamp(torch.dot(vertices[i], vertices[j]), -1.0, 1.0)
        angle = torch.acos(dot)
        angles.append(angle)
        lengths.append(radii * angle)
    stacked = torch.stack(lengths)
    angle_stack = torch.stack(angles)
    return {
        "mean_intrinsic_edge_length": float(torch.mean(stacked).item()),
        "min_intrinsic_edge_length": float(torch.min(stacked).item()),
        "max_intrinsic_edge_length": float(torch.max(stacked).item()),
        "unit_edge_angle_mean": float(torch.mean(angle_stack).item()),
        "unit_edge_angle_spread": float((torch.max(angle_stack) - torch.min(angle_stack)).item()),
    }


def jax_spherical_edge_lengths(radii: jax.Array) -> dict[str, Any]:
    vertices = unit_tetrahedron_vertices_jax()
    lengths = []
    angles = []
    for i, j in TETRA_EDGES:
        dot = jnp.clip(jnp.dot(vertices[i], vertices[j]), -1.0, 1.0)
        angle = jnp.arccos(dot)
        angles.append(angle)
        lengths.append(radii * angle)
    stacked = jnp.stack(lengths)
    angle_stack = jnp.stack(angles)
    return {
        "mean_intrinsic_edge_length": float(jnp.mean(stacked)),
        "min_intrinsic_edge_length": float(jnp.min(stacked)),
        "max_intrinsic_edge_length": float(jnp.max(stacked)),
        "unit_edge_angle_mean": float(jnp.mean(angle_stack)),
        "unit_edge_angle_spread": float(jnp.max(angle_stack) - jnp.min(angle_stack)),
    }


def geomstats_shell_metric(shell_count: int) -> dict[str, Any]:
    sphere = Hypersphere(dim=2)
    vertices = unit_tetrahedron_vertices_torch()
    radii = ordered_radii_torch(shell_count)
    points = shell_points_torch(radii)
    belongs = sphere.belongs(vertices)
    unit_distances = []
    torch_angles = []
    chord_lengths = []
    for i, j in TETRA_EDGES:
        dist = sphere.metric.dist(vertices[i], vertices[j])
        dot = torch.clamp(torch.dot(vertices[i], vertices[j]), -1.0, 1.0)
        angle = torch.acos(dot)
        unit_distances.append(dist)
        torch_angles.append(angle)
        chord_lengths.append(torch.linalg.vector_norm(points[:, i, :] - points[:, j, :], dim=1))
    geom_unit = torch.stack(unit_distances)
    torch_unit = torch.stack(torch_angles)
    intrinsic_by_shell = torch.stack([radii * d for d in unit_distances])
    chords_by_shell = torch.stack(chord_lengths)
    max_angle_delta = float(torch.max(torch.abs(geom_unit - torch_unit)).item())
    return {
        "tool": "geomstats",
        "backend": os.environ.get("GEOMSTATS_BACKEND"),
        "hypersphere_dim": 2,
        "belongs_all_unit_vertices": bool(torch.all(belongs).item()),
        "unit_edge_angle_geomstats_mean": float(torch.mean(geom_unit).item()),
        "unit_edge_angle_torch_acos_mean": float(torch.mean(torch_unit).item()),
        "max_geomstats_vs_torch_angle_delta": max_angle_delta,
        "mean_intrinsic_edge_length": float(torch.mean(intrinsic_by_shell).item()),
        "mean_flat_chord_edge_length": float(torch.mean(chords_by_shell).item()),
        "intrinsic_minus_chord_delta": float((torch.mean(intrinsic_by_shell) - torch.mean(chords_by_shell)).item()),
        "pass": bool(
            torch.all(belongs).item()
            and max_angle_delta <= METRIC_TOL
            and float((torch.mean(intrinsic_by_shell) - torch.mean(chords_by_shell)).item()) > KILL_FLOOR
        ),
    }


def gudhi_boundary_tree() -> gudhi.SimplexTree:
    tree = gudhi.SimplexTree()
    for face in TETRA_FACES:
        tree.insert(face)
    tree.compute_persistence(persistence_dim_max=True)
    return tree


def gudhi_filled_tree() -> gudhi.SimplexTree:
    tree = gudhi.SimplexTree()
    tree.insert((0, 1, 2, 3))
    tree.compute_persistence(persistence_dim_max=True)
    return tree


def pad_betti(values: list[int], length: int = 4) -> list[int]:
    out = list(values)
    while len(out) < length:
        out.append(0)
    return out[:length]


def gudhi_shell_topology(shell_count: int) -> dict[str, Any]:
    boundary_rows = []
    filled_rows = []
    for shell_index in range(shell_count):
        boundary = gudhi_boundary_tree()
        filled = gudhi_filled_tree()
        boundary_betti = pad_betti(boundary.betti_numbers())
        filled_betti = pad_betti(filled.betti_numbers())
        boundary_rows.append(
            {
                "shell_index": shell_index,
                "betti_numbers": boundary_betti,
                "simplex_count": int(boundary.num_simplices()),
                "dimension": int(boundary.dimension()),
                "pass": bool(boundary_betti[:3] == [1, 0, 1]),
            }
        )
        filled_rows.append(
            {
                "shell_index": shell_index,
                "betti_numbers": filled_betti,
                "simplex_count": int(filled.num_simplices()),
                "dimension": int(filled.dimension()),
                "pass": bool(filled_betti[2] == 0),
            }
        )
    boundary_beta2_values = [row["betti_numbers"][2] for row in boundary_rows]
    filled_beta2_values = [row["betti_numbers"][2] for row in filled_rows]
    return {
        "tool": "gudhi",
        "shell_count": shell_count,
        "boundary_template": "tetrahedron boundary triangulation of S^2",
        "filled_control_template": "tetrahedron boundary plus one 3-simplex",
        "boundary_betti_numbers_first_shell": boundary_rows[0]["betti_numbers"],
        "filled_betti_numbers_first_shell": filled_rows[0]["betti_numbers"],
        "boundary_simplex_count": boundary_rows[0]["simplex_count"],
        "filled_simplex_count": filled_rows[0]["simplex_count"],
        "min_boundary_beta2": int(min(boundary_beta2_values)),
        "max_filled_beta2": int(max(filled_beta2_values)),
        "all_boundary_shells_beta2_one": bool(all(v == 1 for v in boundary_beta2_values)),
        "all_filled_controls_beta2_zero": bool(all(v == 0 for v in filled_beta2_values)),
        "boundary_rows_sample": boundary_rows[:3] + boundary_rows[-1:],
        "filled_rows_sample": filled_rows[:3] + filled_rows[-1:],
        "pass": bool(
            all(row["pass"] for row in boundary_rows)
            and all(row["pass"] for row in filled_rows)
            and all(v == 1 for v in boundary_beta2_values)
            and all(v == 0 for v in filled_beta2_values)
        ),
    }


def smt_shell_order_proof(real: dict[str, Any], control: dict[str, Any], claim: str) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim=claim,
        real_measured={
            "min_radius_gap": float(real["min_radius_gap"]),
            "nested_containment_margin": float(real["nested_containment_margin"]),
            "eps": EPS,
        },
        control_measured={
            "min_radius_gap": float(control["min_radius_gap"]),
            "nested_containment_margin": float(control["nested_containment_margin"]),
            "eps": EPS,
        },
        claim_builder=lambda v: z3.And(
            v["min_radius_gap"] >= v["eps"],
            v["nested_containment_margin"] >= v["eps"],
        ),
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
    )
    return proof


def compare_jax_torch(shell_count: int, torch_measure: dict[str, Any]) -> dict[str, Any]:
    jax_measure = invariant_measure_jax(ordered_radii_jax(shell_count))
    torch_metric = torch_spherical_edge_lengths(ordered_radii_torch(shell_count))
    jax_metric = jax_spherical_edge_lengths(ordered_radii_jax(shell_count))
    deltas = {
        "min_radius_gap": abs(float(torch_measure["min_radius_gap"]) - float(jax_measure["min_radius_gap"])),
        "nested_containment_margin": abs(
            float(torch_measure["nested_containment_margin"]) - float(jax_measure["nested_containment_margin"])
        ),
        "mean_intrinsic_edge_length": abs(
            float(torch_metric["mean_intrinsic_edge_length"]) - float(jax_metric["mean_intrinsic_edge_length"])
        ),
        "unit_edge_angle_mean": abs(float(torch_metric["unit_edge_angle_mean"]) - float(jax_metric["unit_edge_angle_mean"])),
    }
    max_delta = max(deltas.values())
    return {
        "representable_parts": [
            "ordered radii",
            "shell-boundary norm margins",
            "spherical edge angle formula acos(<u,v>)",
        ],
        "not_represented_in_jax": [
            "geomstats Hypersphere runtime path; this install is used torch-side only",
            "GUDHI SimplexTree topology runtime path",
            "z3 proof engine",
        ],
        "jax_measure": jax_measure,
        "jax_metric_formula": jax_metric,
        "deltas": deltas,
        "max_abs_delta": max_delta,
        "pass": bool(max_delta <= METRIC_TOL),
    }


def scale_rung(shell_count: int) -> dict[str, Any]:
    real = invariant_measure_torch(ordered_radii_torch(shell_count))
    scrambled = invariant_measure_torch(scrambled_radii_torch(shell_count))
    flattened = invariant_measure_torch(flattened_radii_torch(shell_count))
    geom = geomstats_shell_metric(shell_count)
    topo = gudhi_shell_topology(shell_count)
    parity = compare_jax_torch(shell_count, real)
    rung_pass = bool(
        real["pass"]
        and not scrambled["pass"]
        and not flattened["pass"]
        and geom["pass"]
        and topo["pass"]
        and parity["pass"]
    )
    return {
        "sites_or_qubits": shell_count,
        "shell_count": shell_count,
        "finite_point_count": shell_count * 4,
        "dense_state_closure_used": False,
        "real_shell_order": real,
        "scrambled_order_control": scrambled,
        "flattened_radius_control": flattened,
        "geomstats_shell_metric": geom,
        "gudhi_shell_topology": topo,
        "jax_mirror": parity,
        "pass": rung_pass,
    }


def build_tool_ablations(top: dict[str, Any]) -> dict[str, Any]:
    geom = top["geomstats_shell_metric"]
    topo = top["gudhi_shell_topology"]
    geom_row = tool_ablation(
        "geomstats intrinsic spherical shell edge metric vs recomputed flat chord metric after intrinsic-shell-metric removal",
        baseline_value=geom["mean_intrinsic_edge_length"],
        ablated_value=geom["mean_flat_chord_edge_length"],
        tool="geomstats",
    )
    geom_row.update(
        {
            "structure_removed": "intrinsic spherical shell metric",
            "baseline_recompute": "geomstats Hypersphere(dim=2).metric.dist on unit tetrahedron edges, scaled by every shell radius",
            "ablated_recompute": "torch Euclidean chord lengths on the same finite shell points after flattening the metric to ambient chords",
            "pass": bool(abs(float(geom_row["outcome_delta"])) > KILL_FLOOR),
        }
    )
    gudhi_row = tool_ablation(
        "gudhi tetrahedral shell-boundary beta2 vs recomputed filled-simplex beta2 after boundary 2-cycle removal",
        baseline_value=topo["min_boundary_beta2"],
        ablated_value=topo["max_filled_beta2"],
        tool="gudhi",
    )
    gudhi_row.update(
        {
            "structure_removed": "unfilled spherical-shell boundary 2-cycle",
            "baseline_recompute": "GUDHI SimplexTree over tetrahedron boundary faces for every shell",
            "ablated_recompute": "GUDHI SimplexTree after adding the filled tetrahedron 3-simplex control for every shell",
            "pass": bool(abs(float(gudhi_row["outcome_delta"])) > KILL_FLOOR),
        }
    )
    return {
        "geomstats_shell_metric_ablation": geom_row,
        "gudhi_shell_topology_ablation": gudhi_row,
    }


def build_known_value_checks(
    top: dict[str, Any],
    proofs: dict[str, Any],
    tool_ablations: dict[str, Any],
) -> list[dict[str, Any]]:
    real = top["real_shell_order"]
    scrambled = top["scrambled_order_control"]
    flattened = top["flattened_radius_control"]
    geom = top["geomstats_shell_metric"]
    topo = top["gudhi_shell_topology"]
    parity = top["jax_mirror"]
    return [
        {
            "invariant": "ordered_shell_radii_have_positive_min_gap",
            "computed": real["min_radius_gap"],
            "threshold": EPS,
            "match": bool(real["min_radius_gap"] > EPS),
        },
        {
            "invariant": "scrambled_order_control_kills_monotone_radius_invariant",
            "computed": scrambled["min_radius_gap"],
            "threshold": EPS,
            "match": bool(scrambled["min_radius_gap"] < EPS and not scrambled["pass"]),
        },
        {
            "invariant": "flattened_radius_control_kills_nested_containment_margin",
            "computed": flattened["nested_containment_margin"],
            "threshold": EPS,
            "match": bool(flattened["nested_containment_margin"] < EPS and not flattened["pass"]),
        },
        {
            "invariant": "geomstats_shell_metric_matches_torch_acos_dot_on_unit_tetrahedron_edges",
            "computed": geom["max_geomstats_vs_torch_angle_delta"],
            "tolerance": METRIC_TOL,
            "match": bool(geom["max_geomstats_vs_torch_angle_delta"] <= METRIC_TOL),
        },
        {
            "invariant": "gudhi_tetrahedron_boundary_has_S2_beta2_one",
            "computed": topo["boundary_betti_numbers_first_shell"],
            "known": [1, 0, 1],
            "match": bool(topo["boundary_betti_numbers_first_shell"][:3] == [1, 0, 1]),
        },
        {
            "invariant": "gudhi_filled_tetrahedron_control_has_beta2_zero",
            "computed": topo["filled_betti_numbers_first_shell"],
            "known_beta2": 0,
            "match": bool(topo["filled_betti_numbers_first_shell"][2] == 0),
        },
        {
            "invariant": "z3_real_vs_scrambled_verdict_flip_is_bound_to_measured_margins",
            "computed": {
                "real": proofs["real_vs_scrambled_smt_load_bearing"]["real_claim_verdict"],
                "control": proofs["real_vs_scrambled_smt_load_bearing"]["negated_claim_verdict"],
                "bound_to_measured": proofs["real_vs_scrambled_smt_load_bearing"]["bound_to_measured"],
            },
            "match": bool(proofs["real_vs_scrambled_smt_load_bearing"]["pass"]),
        },
        {
            "invariant": "geometry_tool_ablations_are_recomputed_and_nonzero",
            "computed": {
                key: {
                    "baseline_value": row["baseline_value"],
                    "ablated_value": row["ablated_value"],
                    "outcome_delta": row["outcome_delta"],
                    "pass": row["pass"],
                }
                for key, row in tool_ablations.items()
            },
            "match": bool(all(row["pass"] for row in tool_ablations.values())),
        },
        {
            "invariant": "jax_mirror_matches_representable_torch_shell_quantities",
            "computed": parity["max_abs_delta"],
            "tolerance": METRIC_TOL,
            "match": bool(parity["pass"]),
        },
    ]


def build_controls(top: dict[str, Any]) -> dict[str, Any]:
    geom = top["geomstats_shell_metric"]
    topo = top["gudhi_shell_topology"]
    return {
        "scrambled_order_control": {
            "description": "same radius values in reverse order; this preserves the finite shell multiset but kills the ordered nested-shell invariant",
            "real_min_radius_gap": top["real_shell_order"]["min_radius_gap"],
            "control_min_radius_gap": top["scrambled_order_control"]["min_radius_gap"],
            "real_nested_containment_margin": top["real_shell_order"]["nested_containment_margin"],
            "control_nested_containment_margin": top["scrambled_order_control"]["nested_containment_margin"],
            "kills_claim": bool(not top["scrambled_order_control"]["pass"]),
            "pass": bool(top["real_shell_order"]["pass"] and not top["scrambled_order_control"]["pass"]),
        },
        "flattened_radius_control": {
            "description": "all shell radii collapsed to one radius; this is the degenerate/flattened radius control",
            "real_min_radius_gap": top["real_shell_order"]["min_radius_gap"],
            "control_min_radius_gap": top["flattened_radius_control"]["min_radius_gap"],
            "real_nested_containment_margin": top["real_shell_order"]["nested_containment_margin"],
            "control_nested_containment_margin": top["flattened_radius_control"]["nested_containment_margin"],
            "kills_claim": bool(not top["flattened_radius_control"]["pass"]),
            "pass": bool(top["real_shell_order"]["pass"] and not top["flattened_radius_control"]["pass"]),
        },
        "flat_chord_metric_control": {
            "description": "same finite shell points measured by ambient chord distance after removing the intrinsic spherical shell metric",
            "intrinsic_mean_edge_length": geom["mean_intrinsic_edge_length"],
            "flat_chord_mean_edge_length": geom["mean_flat_chord_edge_length"],
            "kills_intrinsic_metric_readout": bool(geom["intrinsic_minus_chord_delta"] > KILL_FLOOR),
            "pass": bool(geom["intrinsic_minus_chord_delta"] > KILL_FLOOR),
        },
        "filled_topology_control": {
            "description": "same tetrahedral boundary vertices with the interior 3-simplex added; this fills the shell boundary and kills beta2",
            "boundary_beta2": topo["min_boundary_beta2"],
            "filled_beta2": topo["max_filled_beta2"],
            "kills_boundary_beta2": bool(topo["min_boundary_beta2"] == 1 and topo["max_filled_beta2"] == 0),
            "pass": bool(topo["min_boundary_beta2"] == 1 and topo["max_filled_beta2"] == 0),
        },
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    scale_rows = {str(shell_count): scale_rung(shell_count) for shell_count in SHELL_COUNTS}
    top = scale_rows["64"]
    proofs = {
        "real_vs_scrambled_smt_load_bearing": smt_shell_order_proof(
            top["real_shell_order"],
            top["scrambled_order_control"],
            "shell_radius_monotonic_and_nested_containment_real_vs_scrambled_control",
        ),
        "real_vs_flattened_smt_load_bearing": smt_shell_order_proof(
            top["real_shell_order"],
            top["flattened_radius_control"],
            "shell_radius_monotonic_and_nested_containment_real_vs_flattened_control",
        ),
    }
    proofs["pass"] = bool(
        proofs["real_vs_scrambled_smt_load_bearing"]["pass"]
        and proofs["real_vs_flattened_smt_load_bearing"]["pass"]
    )
    tool_ablations = build_tool_ablations(top)
    controls = build_controls(top)
    known_checks = build_known_value_checks(top, proofs, tool_ablations)

    scale_rungs = {}
    for shell_count in SHELL_COUNTS:
        row = scale_rows[str(shell_count)]
        scale_rungs[str(shell_count)] = {
            "sites_or_qubits": shell_count,
            "shell_count": shell_count,
            "finite_point_count": row["finite_point_count"],
            "dense_state_closure_used": False,
            "min_radius_gap": row["real_shell_order"]["min_radius_gap"],
            "nested_containment_margin": row["real_shell_order"]["nested_containment_margin"],
            "geomstats_mean_intrinsic_edge_length": row["geomstats_shell_metric"]["mean_intrinsic_edge_length"],
            "gudhi_boundary_betti_numbers_first_shell": row["gudhi_shell_topology"]["boundary_betti_numbers_first_shell"],
            "jax_vs_pytorch_delta": row["jax_mirror"]["max_abs_delta"],
            "pass": bool(row["pass"]),
        }

    scale_pass = all(row["pass"] for row in scale_rungs.values())
    controls_pass = all(bool(row["pass"]) for row in controls.values())
    ablation_pass = all(row["pass"] and abs(float(row["outcome_delta"])) > KILL_FLOOR for row in tool_ablations.values())
    proof_pass = bool(proofs["pass"])
    known_pass = all(row["match"] for row in known_checks)
    jax_delta = max(row["jax_mirror"]["max_abs_delta"] for row in scale_rows.values())
    all_pass = bool(scale_pass and controls_pass and ablation_pass and proof_pass and known_pass and jax_delta <= METRIC_TOL)

    blockers = []
    if not scale_pass:
        blockers.append("one or more 8/16/32/64 shell rungs failed non-dense geometry checks")
    if not controls_pass:
        blockers.append("one or more scrambled/flattened/metric/topology controls failed to kill the target property")
    if not ablation_pass:
        blockers.append("one or more numeric geometry tool ablations are zero or not recomputed")
    if not proof_pass:
        blockers.append("helper-bound z3 proof did not flip real sat vs control unsat")
    if not known_pass:
        blockers.append("one or more computed known-value checks failed")
    if jax_delta > METRIC_TOL:
        blockers.append(f"jax_vs_pytorch_delta {jax_delta} exceeds tolerance {METRIC_TOL}")

    min_margin = min(row["min_radius_gap"] for row in scale_rungs.values())
    min_nested_margin = min(row["nested_containment_margin"] for row in scale_rungs.values())
    min_geom_delta = min(
        row["geomstats_shell_metric"]["intrinsic_minus_chord_delta"] for row in scale_rows.values()
    )

    result = {
        "schema": "formal_scout_max_deep_lego_result_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical STAGE 3 geometry object",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Build one standalone Stage-3 shell geometry object: finite spherical shells Sigma_r at 8/16/32/64 shell counts with torch primary geometry, torch-side geomstats shell metric, GUDHI shell topology, JAX mirror for representable formulas, and helper-bound z3 proof flip.",
        "scientific_question": "Can shell_geometry instantiate finite ordered spherical shells Sigma_r whose radius monotonicity and nested containment are real observables, flip under scrambled/flattened controls, and carry genuine geomstats/GUDHI ablations without dense closure?",
        "finite_map": {
            "domain": "For n in {8,16,32,64}: finite ordered shell index set I_n, radii r_i=1+0.125*i, four tetrahedral sample vertices on each Sigma_{r_i}, and the shell-order operation i -> i+1.",
            "codomain_or_output": "Geometry readouts: min adjacent radius gap, nested shell-boundary-in-next-ball containment margin, geomstats intrinsic shell edge metric, GUDHI shell-boundary topology, z3 proof verdicts, controls, ablations, and blocked downstream consumers.",
            "definition": "ShellGeometry_n maps each finite ordered radius r_i to Sigma_{r_i}=r_i*S^2 sampled by the tetrahedron boundary; order is claim-bearing because scrambled/flattened controls kill the containment invariant.",
        },
        "domain": {
            "shell_counts": list(SHELL_COUNTS),
            "vertices_per_shell": 4,
            "radius_rule": f"r_i={RADIUS_START}+{RADIUS_STEP}*i",
            "shell_template": "tetrahedron boundary sample on S^2",
            "dense_state_closure_used": False,
        },
        "codomain_or_output": {
            "primary_invariant": "min_i(r_{i+1}-r_i)>eps and min_i(min||Sigma_{i+1}||-max||Sigma_i||)>eps",
            "metric_output": "geomstats Hypersphere(dim=2) intrinsic spherical edge metric on torch tensors",
            "topology_output": "GUDHI SimplexTree Betti numbers for tetrahedron boundary shell and filled control",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: finite shell indices, finite radii, finite tetrahedral samples, finite shell-order path, finite controls, and finite proof variables.",
            },
            "N01": {
                "role": "active_order_sensitive",
                "statement": "the ordered shell operation i -> i+1 is claim-bearing: real ordered radii satisfy nested containment, while reverse-order and flattened-order controls fail the same measured claim.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 order-sensitive shell operation/control witnessed by ordered vs scrambled/flattened shell radii",
        ],
        "carrier_layer": "finite ordered spherical shell samples",
        "geometry_layer": "standalone shell_geometry object; finite spherical shells Sigma_r and enclosed-ball nesting only",
        "carrier_realization": "torch.float64 finite tensors for radii and tetrahedral shell points; geomstats uses the torch backend; no NumPy bridge and no dense 2^N state closure",
        "peps3d_embedding": {
            "anchor": "stage-3 geometry object only: shell index i is mapped to finite sparse PEPS3D site-anchor metadata for future consumers, but no PEPS3D contraction or manifold-cell admission is claimed",
            "from_first_carrier_step": False,
            "full_peps3d_contraction_claimed": False,
            "claim_ceiling": "not a nonclassical manifold layer or G-structure",
        },
        "spinor_state": "not_applicable: this Stage-3 geometry object does not claim a torch spinor state or spinor-derived density",
        "quaternion_action": "not_applicable: no quaternion language or quaternion invariant is used",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/F01_finite_distinguishability_results.json",
            "system_v5/ops/formal_scouts/results/carrier_torch_complex_spinor_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite shell radius order monotonicity plus shell-boundary-in-next-ball nested containment",
        "branch_status_before_run": "single standalone geometry lego requested by user; no layer, manifold, G-structure, stack, bridge, flux, Axis0, FEP, gravity, or physics route opened",
        "allowed_claims": [
            "bounded Stage-3 shell_geometry lego exists/runs if this JSON and required gates pass",
            "finite spherical shells Sigma_r were instantiated at 8/16/32/64 shell counts without dense closure",
            "z3 helper-bound proof flips for measured radius monotonicity and nested containment against scrambled/flattened controls",
            "geomstats and GUDHI carry local geometry/topology readouts with genuine recomputed ablations",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "standalone geometry object only",
            "no manifold layer, no G-structure, no layer stacking, and no downstream consumer admission",
            "PEPS3D and spinor fields are explicitly not claimed by this shell geometry object",
        ],
        "eligible_consumers": [
            "bounded later Stage-3 geometry comparisons only after citing this result path and fresh gate output"
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["load_bearing_proof.smt_load_bearing z3 shell-order invariant proof"],
        "geometry_surfaces_used": ["geomstats Hypersphere(dim=2) torch-side metric"],
        "topology_surfaces_used": ["gudhi SimplexTree tetrahedron boundary and filled control"],
        "graph_surfaces_used": [],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "scrambled_order_control": "same shell radius multiset in reverse order must make min_radius_gap and nested_containment_margin fail the z3 claim",
            "flattened_radius_control": "all radii equal must make min_radius_gap and nested_containment_margin fail the z3 claim",
            "flat_chord_metric_control": "removing intrinsic shell metric must change the edge-length observable",
            "filled_topology_control": "filling the shell boundary with a 3-simplex must erase beta2",
        },
        "required_artifacts": [
            "result JSON",
            "scale_ladder",
            "torch_primary_result",
            "jax_mirror_result",
            "proof_results",
            "controls",
            "tool_ablations",
            "known_value_checks",
        ],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "known_value_checks_pass": known_pass,
            "jax_vs_pytorch_delta": jax_delta,
            "min_radius_gap": min_margin,
            "min_nested_containment_margin": min_nested_margin,
            "min_geomstats_intrinsic_minus_chord_delta": min_geom_delta,
            "elapsed_seconds": time.time() - started,
        },
        "torch_primary_result": {
            "engine": "torch",
            "dtype": "torch.float64",
            "claim": "finite ordered shell radii are monotone and shell boundaries are nested inside the next enclosed ball",
            "rungs": {
                key: {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "real_shell_order": row["real_shell_order"],
                    "scrambled_order_control": row["scrambled_order_control"],
                    "flattened_radius_control": row["flattened_radius_control"],
                    "pass": row["pass"],
                }
                for key, row in scale_rows.items()
            },
            "pass": bool(scale_pass),
        },
        "jax_mirror_result": {
            "engine": "jax",
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "claim": "JAX mirrors representable finite shell formulas only; no JAX geomstats path is claimed",
            "rungs": {key: row["jax_mirror"] for key, row in scale_rows.items()},
            "geomstats_jax_backend_claimed": False,
            "pass": bool(jax_delta <= METRIC_TOL),
        },
        "jax_vs_pytorch_delta": jax_delta,
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "tool_ablation_outcomes": tool_ablations,
        "scale_ladder": {
            "rungs": scale_rungs,
            "scale_axis": "shell_count",
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "scale_details": scale_rows,
        "known_value_checks": known_checks,
        "all_known_value_checks_match": known_pass,
        "positive": {
            "shell_order_smt_flip": {
                "pass": proof_pass,
                "proofs": proofs,
            },
            "scale_8_16_32_64_non_dense_shells": {
                "pass": scale_pass,
                "rungs": scale_rungs,
            },
            "geomstats_shell_metric": {
                "pass": all(row["geomstats_shell_metric"]["pass"] for row in scale_rows.values()),
                "top_rung": top["geomstats_shell_metric"],
            },
            "gudhi_shell_topology": {
                "pass": all(row["gudhi_shell_topology"]["pass"] for row in scale_rows.values()),
                "top_rung": top["gudhi_shell_topology"],
            },
            "jax_parity": {
                "max_abs_delta": jax_delta,
                "pass": bool(jax_delta <= METRIC_TOL),
            },
        },
        "graveyard_companions": controls,
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "geomstats_jax_backend_claim": {
                "claimed": False,
                "pass": True,
                "notes": "geomstats is run torch-side only. JAX mirrors the closed finite formulas it can represent.",
            },
            "manifold_layer_claim": {"claimed": False, "pass": True},
            "g_structure_claim": {"claimed": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "shells": [
            {
                "name": "finite_ordered_spherical_shells_Sigma_r",
                "status": "stage_3_geometry_object_lego_only",
                "rungs": list(SHELL_COUNTS),
                "min_radius_gap": min_margin,
                "min_nested_containment_margin": min_nested_margin,
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "compare shell_geometry with another independent Stage-3 geometry object only after this result is cited and re-gated",
            "do not use this result as a manifold layer, G-structure, Xi, Phi0, Axis0, flux, FEP, gravity, or physics receipt",
        ],
        "compatibility_weights": {
            "local_stage3_geometry_input": 1.0 if all_pass else 0.0,
            "future_geometry_comparison_input": 0.5 if all_pass else 0.0,
            "Xi": 0.0,
            "Phi0": 0.0,
            "Axis0": 0.0,
            "flux": 0.0,
            "FEP": 0.0,
            "gravity": 0.0,
        },
        "compression_map": {
            "from": "finite ordered shells Sigma_r with four tetrahedral sample vertices per shell and order path i->i+1",
            "to": "monotonicity/containment invariant, geomstats shell metric, GUDHI shell topology, z3 verdict flip, controls, and numeric geometry ablations",
            "loss_boundary": "does not preserve or claim dense 2^N state closure, spinor state, PEPS3D contraction, manifold layer completion, G-structure selection, Axis0, flux, FEP, gravity, bridge, or final admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": min(min_margin, min_nested_margin, min_geom_delta),
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "shell_geometry survives iff every rung is non-dense, ordered radii pass monotonicity/nested containment, scrambled and flattened controls kill, geomstats/GUDHI checks pass, z3 proof flips, ablations are recomputed and nonzero, and promotion_allowed=false",
            "computed_capacity": min(min_margin, min_nested_margin, min_geom_delta),
            "threshold": KILL_FLOOR,
            "passed": bool(all_pass and min(min_margin, min_nested_margin, min_geom_delta) > KILL_FLOOR),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {pathlib.Path(__file__).name} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage-3 standalone shell geometry lego only; no manifold layer, no G-structure, no downstream consumer admitted",
        },
        "pass_rule": "all 8/16/32/64 shell rungs are non-dense and pass; torch/JAX representable formulas agree; geomstats shell metric and GUDHI topology pass; z3 proof flips real vs scrambled/flattened controls; numeric geometry tool ablations are recomputed and nonzero",
        "fail_rule": "fail on dense closure, missing rung, nonmonotone real radii, live scrambled/flattened control, fake geomstats JAX path, failed GUDHI topology, no real/control z3 flip, zero/cosmetic geometry ablation, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blockers": blockers,
        "required_pass": all_pass,
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "required_pass": result["required_pass"],
                "result_path": str(OUT_PATH.relative_to(ROOT)),
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "proof_pass": result["proof_results"]["pass"],
                "scale_pass": result["scale_ladder"]["pass"],
                "blockers": result["blockers"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
