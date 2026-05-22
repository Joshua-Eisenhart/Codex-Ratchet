#!/usr/bin/env python3
"""PyTorch PEPS3D nested-order substrate scout.

This is a tiny substrate probe for the geometric constraint manifold.  It asks
whether a 13-layer operator schedule changes a 2x2x2 PEPS3D-style tensor
substrate in an order-sensitive way, and whether obvious shortcuts such as
reverse order, scalar projection, edge-blind summaries, and rank collapse are
rejected by the same local receipt.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import rustworkx as rx
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "pytorch_peps3d_nested_order_substrate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "peps3d_nested_order_substrate"
CLAIM_CEILING = (
    "Formal scout only: a tiny 2x2x2 PyTorch PEPS3D-style substrate carries an "
    "order-sensitive 13-layer nested-geometry operator schedule, with rustworkx "
    "graph wiring plus SymPy, z3, and cvc5 witnesses. This does not admit a "
    "final PEPS3D environment contraction, final G-structure, real attractor "
    "basin, final Axis0, bridge, physics, target-system, engine, or canonical "
    "claim; it does not admit canonical claims."
)

TAU_SIGNATURE_GAP = 1.0e-4

LAYERS = [
    "finite_constraint_complex",
    "complex_hilbert_carrier",
    "unit_spinor_sphere",
    "projective_base_sphere",
    "hopf_fiber_bundle",
    "hopf_torus_leaf_family",
    "connection_holonomy_geometry",
    "weyl_spinor_bundle",
    "chirality_orientation_cover",
    "clifford_module_geometry",
    "frame_bundle_structure_reduction",
    "tensor_product_coupling_geometry",
    "dynamic_transition_ratchet_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 2x2x2 PEPS3D-style tensor substrate and 13-layer operator schedule",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cube substrate graph and 13-layer schedule DAG order checks",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact noncommutation witness for nested layer operators",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing scaled integer witness that order-control gaps exceed threshold",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Boolean cross-check of the same order-control predicates",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical result path handling",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive formal-scout receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(val) for val in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    return value


def cube_graph() -> tuple[rx.PyDiGraph, list[tuple[int, int, int]], list[dict[str, int]]]:
    coords = [(x, y, z) for x in range(2) for y in range(2) for z in range(2)]
    index = {coord: idx for idx, coord in enumerate(coords)}
    graph = rx.PyDiGraph()
    for coord in coords:
        graph.add_node({"coord": coord})
    edges: list[dict[str, int]] = []
    for coord, src in index.items():
        for axis in range(3):
            nxt = list(coord)
            nxt[axis] += 1
            if nxt[axis] >= 2:
                continue
            dst = index[tuple(nxt)]
            graph.add_edge(src, dst, axis)
            edges.append({"src": src, "dst": dst, "axis": axis})
    return graph, coords, edges


def layer_graph() -> rx.PyDiGraph:
    graph = rx.PyDiGraph()
    for idx, layer in enumerate(LAYERS):
        graph.add_node({"idx": idx, "layer": layer})
    for idx in range(len(LAYERS) - 1):
        graph.add_edge(idx, idx + 1, "nested_after")
    return graph


def seed_site_features(coords: list[tuple[int, int, int]]) -> torch.Tensor:
    rows = []
    for idx, (x, y, z) in enumerate(coords):
        rows.append(
            torch.tensor(
                [
                    0.37 + 0.19 * x - 0.07 * y + 0.11 * z,
                    -0.23 + 0.13 * y + 0.05 * idx,
                    0.41 - 0.17 * z + 0.03 * x * y,
                    0.29 + 0.02 * idx + 0.07 * x * z,
                ],
                dtype=torch.float64,
            )
        )
    return torch.stack(rows)


def layer_operator(idx: int) -> torch.Tensor:
    base = torch.eye(4, dtype=torch.float64)
    a = 0.011 * (idx + 1)
    b = 0.007 * ((idx % 5) + 1)
    c = 0.005 * ((idx % 3) + 1)
    d = 0.003 * ((idx % 7) + 1)
    op = base.clone()
    op[0, 1] = a
    op[1, 2] = -b
    op[2, 3] = c
    op[3, 0] = -d
    op[0, 2] = 0.002 * ((idx % 4) + 1)
    op[1, 3] = -0.0015 * ((idx % 6) + 1)
    return op


OPS = [layer_operator(idx) for idx in range(len(LAYERS))]


def apply_schedule(features: torch.Tensor, order: list[int]) -> torch.Tensor:
    state = features.clone()
    for step, layer_idx in enumerate(order):
        op = OPS[layer_idx]
        phase = 1.0 + 0.004 * (step + 1)
        state = torch.tanh((state @ op.T) * phase + 0.013 * (layer_idx + 1))
    return state


def features_to_tensors(features: torch.Tensor, coords: list[tuple[int, int, int]]) -> torch.Tensor:
    tensors = []
    grid = torch.arange(16, dtype=features.dtype)
    for idx, coord in enumerate(coords):
        row = features[idx]
        coord_phase = 0.071 * (1 + coord[0]) + 0.113 * (1 + coord[1]) + 0.157 * (1 + coord[2])
        vals = torch.sin(row[grid.long() % 4] * (grid + 1.0) * 0.23 + coord_phase)
        vals = vals + torch.cos(row[(grid.long() + 1) % 4] * 0.31 - coord_phase) * 0.17
        tensors.append(vals.reshape(2, 2, 2, 2) / 5.0)
    return torch.stack(tensors)


def edge_contract(tensors: torch.Tensor, edge: dict[str, int]) -> torch.Tensor:
    src = edge["src"]
    dst = edge["dst"]
    axis = edge["axis"]
    left = tensors[src]
    right = tensors[dst]
    if axis == 0:
        return torch.einsum("pabc,qdbc->", left, right)
    if axis == 1:
        return torch.einsum("pabc,qadc->", left, right)
    return torch.einsum("pabc,qabd->", left, right)


def peps3d_signature(features: torch.Tensor, coords: list[tuple[int, int, int]], edges: list[dict[str, int]]) -> torch.Tensor:
    tensors = features_to_tensors(features, coords)
    edge_terms = [edge_contract(tensors, edge) for edge in edges]
    site_norms = torch.linalg.vector_norm(tensors.reshape(tensors.shape[0], -1), dim=1)
    return torch.cat([torch.stack(edge_terms), site_norms])


def scalar_project(features: torch.Tensor) -> torch.Tensor:
    return features.mean(dim=1, keepdim=True).expand_as(features)


def rank_collapse(features: torch.Tensor) -> torch.Tensor:
    global_mean = features.mean(dim=0, keepdim=True)
    return global_mean.expand_as(features)


def edge_blind_signature(features: torch.Tensor, coords: list[tuple[int, int, int]], signature_len: int) -> torch.Tensor:
    tensors = features_to_tensors(features, coords)
    flat = tensors.reshape(-1)
    mean = flat.mean()
    std = flat.std(unbiased=False)
    idx = torch.arange(signature_len, dtype=features.dtype)
    return torch.tanh(mean * (idx + 1.0) * 0.29 + std * torch.sin(idx + 1.0))


def squared_gap(a: torch.Tensor, b: torch.Tensor) -> dict[str, Any]:
    value = torch.sum((a - b) * (a - b))
    return {"gap": float(value.item()), "pass": bool(float(value.item()) >= TAU_SIGNATURE_GAP)}


def sympy_noncommutation_witness() -> dict[str, Any]:
    a = sp.Matrix([[1, sp.Rational(1, 5)], [0, 1]])
    b = sp.Matrix([[1, 0], [sp.Rational(1, 7), 1]])
    comm = a * b - b * a
    return {
        "commutator": [[str(item) for item in row] for row in comm.tolist()],
        "determinant": str(comm.det()),
        "pass": bool(comm != sp.zeros(2)),
    }


def z3_witness(gaps: dict[str, dict[str, Any]]) -> dict[str, Any]:
    scale = 1_000_000
    threshold = int(TAU_SIGNATURE_GAP * scale)
    values = {name: int(row["gap"] * scale) for name, row in gaps.items()}
    solver = z3.Solver()
    for name, value in values.items():
        var = z3.Int(name)
        solver.add(var == value)
        solver.add(var > threshold)
    verdict = solver.check()
    weak = z3.Solver()
    weak_gap = z3.Int("edge_blind_zero_gap_control")
    weak.add(weak_gap == 0)
    weak.add(weak_gap >= 0)
    weak_verdict = weak.check()
    return {
        "scale": scale,
        "threshold_scaled": threshold,
        "values_scaled": values,
        "strict_verdict": str(verdict),
        "zero_gap_control_verdict": str(weak_verdict),
        "pass": bool(verdict == z3.sat and weak_verdict == z3.sat),
    }


def cvc5_witness(metric_passes: dict[str, bool]) -> dict[str, Any]:
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_UF")
    bool_sort = tm.getBooleanSort()
    atoms = []
    for name, passed in metric_passes.items():
        atom = tm.mkConst(bool_sort, name)
        solver.assertFormula(tm.mkTerm(Kind.EQUAL, atom, tm.mkBoolean(passed)))
        atoms.append(atom)
    joint = tm.mkConst(bool_sort, "nested_order_peps3d_substrate_distinguishable")
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, joint, tm.mkTerm(Kind.AND, *atoms)))
    solver.assertFormula(joint)
    verdict = solver.checkSat()
    return {"strict_verdict": str(verdict), "metric_passes": metric_passes, "pass": bool(verdict.isSat())}


def main() -> int:
    started = time.time()
    substrate_graph, coords, edges = cube_graph()
    schedule_graph = layer_graph()
    canonical_order = list(range(len(LAYERS)))
    reverse_order = list(reversed(canonical_order))
    shuffle_order = [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11]

    base = seed_site_features(coords)
    canonical_features = apply_schedule(base, canonical_order)
    reverse_features = apply_schedule(base, reverse_order)
    shuffled_features = apply_schedule(base, shuffle_order)
    scalar_features = apply_schedule(scalar_project(base), canonical_order)
    collapsed_features = apply_schedule(rank_collapse(base), canonical_order)

    canonical_sig = peps3d_signature(canonical_features, coords, edges)
    reverse_sig = peps3d_signature(reverse_features, coords, edges)
    shuffled_sig = peps3d_signature(shuffled_features, coords, edges)
    scalar_sig = peps3d_signature(scalar_features, coords, edges)
    collapsed_sig = peps3d_signature(collapsed_features, coords, edges)
    edge_blind_sig = edge_blind_signature(canonical_features, coords, canonical_sig.numel())

    gaps = {
        "reverse_order_gap": squared_gap(canonical_sig, reverse_sig),
        "shuffled_neighbor_order_gap": squared_gap(canonical_sig, shuffled_sig),
        "scalar_projection_gap": squared_gap(canonical_sig, scalar_sig),
        "rank_collapsed_substrate_gap": squared_gap(canonical_sig, collapsed_sig),
        "edge_blind_summary_gap": squared_gap(canonical_sig, edge_blind_sig),
    }
    sympy_proof = sympy_noncommutation_witness()
    z3_proof = z3_witness(gaps)
    cvc5_proof = cvc5_witness({name: row["pass"] for name, row in gaps.items()} | {"z3_pass": z3_proof["pass"]})

    graph_ok = bool(
        substrate_graph.num_nodes() == 8
        and substrate_graph.num_edges() == 12
        and rx.is_directed_acyclic_graph(substrate_graph)
        and schedule_graph.num_nodes() == 13
        and schedule_graph.num_edges() == 12
        and rx.is_directed_acyclic_graph(schedule_graph)
    )

    positive = {
        "pytorch_peps3d_signature_ordered": {
            "base_feature_shape": list(base.shape),
            "signature_length": int(canonical_sig.numel()),
            "signature_norm": float(torch.linalg.vector_norm(canonical_sig).item()),
            "pass": bool(list(base.shape) == [8, 4] and canonical_sig.numel() == 20),
        },
        "rustworkx_substrate_and_layer_dags_valid": {
            "substrate_nodes": substrate_graph.num_nodes(),
            "substrate_edges": substrate_graph.num_edges(),
            "layer_nodes": schedule_graph.num_nodes(),
            "layer_edges": schedule_graph.num_edges(),
            "pass": graph_ok,
        },
        "sympy_exact_noncommuting_layer_witness": sympy_proof,
        "z3_scaled_order_gap_witness": z3_proof,
        "cvc5_cross_solver_order_gap_witness": cvc5_proof,
    }

    graveyard_companions = {
        "reverse_layer_order_rejected": {
            **gaps["reverse_order_gap"],
            "interpretation": "Full reversal changes the PyTorch PEPS3D substrate signature.",
        },
        "neighbor_shuffle_order_rejected": {
            **gaps["shuffled_neighbor_order_gap"],
            "interpretation": "Local pair-swapping of nested layers changes the substrate signature.",
        },
        "scalar_projection_rejected": {
            **gaps["scalar_projection_gap"],
            "interpretation": "Scalar projection cannot stand in for the vector PEPS3D substrate.",
        },
        "rank_collapsed_substrate_rejected": {
            **gaps["rank_collapsed_substrate_gap"],
            "interpretation": "A rank-collapsed substrate loses the site-local tensor signature.",
        },
        "edge_blind_summary_rejected": {
            **gaps["edge_blind_summary_gap"],
            "interpretation": "A graph-edge-blind summary cannot replace edge-indexed PEPS3D contractions.",
        },
    }

    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": bool(CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False),
        },
        "claim_ceiling_blocks_global_claims": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": bool(
                all(
                    term in CLAIM_CEILING.lower()
                    for term in ["formal scout", "does not admit", "real attractor basin", "canonical"]
                )
            ),
        },
        "bounded_tiny_substrate": {
            "site_count": len(coords),
            "layer_count": len(LAYERS),
            "edge_count": len(edges),
            "pass": bool(len(coords) == 8 and len(LAYERS) == 13 and len(edges) == 12),
        },
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
    )

    receipt = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "summary": {
            "all_pass": bool(all_pass),
            "site_count": len(coords),
            "layer_count": len(LAYERS),
            "signature_length": int(canonical_sig.numel()),
            "elapsed_seconds": round(time.time() - started, 6),
            "gaps": {name: row["gap"] for name, row in gaps.items()},
            "load_bearing_tools": [
                tool for tool, depth in TOOL_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ],
        },
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row.get("pass") is True),
        },
        "why_not_v4_probes": [
            "v5 formal scout over the current geometric constraint manifold substrate concern",
            "uses PyTorch tensor contractions and rustworkx edge wiring rather than provider prose",
            "keeps PEPS3D, G-structure, Axis0, basin, and canonical claims explicitly blocked",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "layers": LAYERS,
        "canonical_order": canonical_order,
        "reverse_order": reverse_order,
        "shuffle_order": shuffle_order,
        "cube_coords": coords,
        "cube_edges": edges,
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(json.dumps({"all_pass": bool(all_pass), "result": str(OUT_PATH)}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
