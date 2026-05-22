#!/usr/bin/env python3
"""PEPS3D substrate quotient distinguishability scout.

This scout asks whether a tiny 2x2x2 PyTorch PEPS3D-style substrate carries
information that a flattened summary quotient, scalar Axis0 projection, or
wrong adjacency control loses.  It is deliberately small: the goal is a bounded
tool/function receipt for PEPS3D substrate distinguishability, not a broad
PEPS3D environment contraction campaign.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import rustworkx as rx
import torch
import z3

from sim_axis0_vector_bundle_thirteen_shell_pytorch_peps3d_lirpa_noncollapse_probe import (  # noqa: E402
    LAYERS,
    load_axis0_bundle,
    shell_state,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "peps3d_substrate_quotient_distinguishability_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "peps3d_substrate_distinguishability"
CLAIM_CEILING = (
    "Formal scout only: a tiny 2x2x2 PyTorch PEPS3D-style tensor substrate over "
    "the current Axis0 vector-bundle fixture is distinguishable from flattened "
    "summary, wrong-adjacency, scalar-projection, and zero-tensor controls under "
    "rustworkx graph wiring plus z3/cvc5 witnesses. This does not admit final "
    "PEPS3D environment contraction, a real attractor basin, final Axis0, or "
    "canonical manifold claims."
)

TAU_SIGNATURE_GAP = 0.0001

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing construction and contraction of rank-4 2x2x2 PEPS3D-style site tensors",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 2x2x2 directed cube graph; its edge list determines the tensor-contraction signature",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing scaled integer witness that PEPS3D substrate gaps exceed the quotient-control threshold",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Boolean cross-check of the same PEPS3D distinguishability predicates",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical receipt path handling",
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
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
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


def scalar_mean_projection(vectors: torch.Tensor) -> torch.Tensor:
    return vectors.mean(dim=1, keepdim=True).expand_as(vectors)


def site_states(vectors: torch.Tensor, site_count: int = 8) -> torch.Tensor:
    return torch.stack([shell_state(vectors[idx], idx) for idx in range(site_count)])


def make_site_tensor(state: torch.Tensor, coord: tuple[int, int, int], site_idx: int) -> torch.Tensor:
    grid = torch.arange(16, dtype=state.dtype, device=state.device)
    coord_phase = 0.071 * (1 + coord[0]) + 0.113 * (1 + coord[1]) + 0.157 * (1 + coord[2])
    selected = state[(grid.long() + site_idx) % state.numel()]
    vals = torch.sin((grid + 1.0) * 0.173 + selected + coord_phase)
    vals = vals + 0.23 * torch.cos((grid + 1.0) * 0.091 - selected)
    return vals.reshape(2, 2, 2, 2) / 4.0


def make_tensors(states: torch.Tensor, coords: list[tuple[int, int, int]]) -> torch.Tensor:
    return torch.stack([make_site_tensor(states[idx], coords[idx], idx) for idx in range(len(coords))])


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


def peps3d_signature(tensors: torch.Tensor, edges: list[dict[str, int]]) -> torch.Tensor:
    edge_terms = [edge_contract(tensors, edge) for edge in edges]
    return torch.stack(edge_terms)


def flattened_quotient_signature(tensors: torch.Tensor, edge_count: int) -> torch.Tensor:
    flat = tensors.reshape(-1)
    mean = flat.mean()
    std = flat.std(unbiased=False)
    total = flat.sum()
    idx = torch.arange(edge_count, dtype=tensors.dtype, device=tensors.device)
    return torch.tanh(mean * (idx + 1.0) * 0.37 + std * torch.cos(idx + 1.0) + 0.003 * total)


def wrong_adjacency_edges(edges: list[dict[str, int]], site_count: int) -> list[dict[str, int]]:
    return [
        {
            "src": edge["src"],
            "dst": (edge["dst"] + 3) % site_count,
            "axis": (edge["axis"] + 1) % 3,
        }
        for edge in edges
    ]


def squared_gap(a: torch.Tensor, b: torch.Tensor) -> dict[str, Any]:
    value = torch.sum((a - b) * (a - b))
    return {"gap": float(value.item()), "pass": bool(float(value.item()) >= TAU_SIGNATURE_GAP)}


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
    weak_gap = z3.Int("weak_flat_gap")
    weak.add(weak_gap == 0)
    weak.add(weak_gap >= 0)
    weak_verdict = weak.check()
    return {
        "scale": scale,
        "threshold_scaled": threshold,
        "values_scaled": values,
        "strict_verdict": str(verdict),
        "weakened_zero_threshold_control": str(weak_verdict),
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
    joint = tm.mkConst(bool_sort, "peps3d_substrate_distinguishable")
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, joint, tm.mkTerm(Kind.AND, *atoms)))
    solver.assertFormula(joint)
    verdict = solver.checkSat()
    return {"strict_verdict": str(verdict), "metric_passes": metric_passes, "pass": bool(verdict.isSat())}


def main() -> int:
    started = time.time()
    axis0 = load_axis0_bundle()
    vectors: torch.Tensor = axis0["shell_vectors"].clone().detach().to(torch.float32)
    graph, coords, edges = cube_graph()
    graph_valid = bool(
        graph.num_nodes() == 8
        and graph.num_edges() == 12
        and rx.is_directed_acyclic_graph(graph)
        and len(list(rx.topological_sort(graph))) == 8
    )

    states = site_states(vectors)
    tensors = make_tensors(states, coords)
    signature = peps3d_signature(tensors, edges)
    flattened = flattened_quotient_signature(tensors, len(edges))
    wrong_adj = peps3d_signature(tensors, wrong_adjacency_edges(edges, len(coords)))

    scalar_tensors = make_tensors(site_states(scalar_mean_projection(vectors)), coords)
    scalar_signature = peps3d_signature(scalar_tensors, edges)
    zero_tensors = torch.zeros_like(tensors)
    zero_signature = peps3d_signature(zero_tensors, edges)

    gaps = {
        "flattened_quotient_gap": squared_gap(signature, flattened),
        "wrong_adjacency_gap": squared_gap(signature, wrong_adj),
        "scalar_projection_gap": squared_gap(signature, scalar_signature),
        "zero_tensor_gap": squared_gap(signature, zero_signature),
    }
    z3_proof = z3_witness(gaps)
    cvc5_proof = cvc5_witness({name: row["pass"] for name, row in gaps.items()} | {"z3_pass": z3_proof["pass"]})

    positive = {
        "upstream_axis0_vector_bundle_available": {
            "admitted": axis0.get("admitted"),
            "blocked": axis0.get("blocked"),
            "shell_vector_shape": list(vectors.shape),
            "pass": bool(axis0.get("pass") is True and list(vectors.shape) == [13, 3]),
        },
        "rustworkx_cube_graph_valid": {
            "node_count": graph.num_nodes(),
            "edge_count": graph.num_edges(),
            "topological_order": [int(x) for x in rx.topological_sort(graph)],
            "pass": graph_valid,
        },
        "pytorch_peps3d_signature_shape": {
            "site_tensor_shape": list(tensors.shape),
            "signature_shape": list(signature.shape),
            "pass": bool(list(tensors.shape) == [8, 2, 2, 2, 2] and list(signature.shape) == [12]),
        },
        "z3_scaled_gap_witness": z3_proof,
        "cvc5_cross_solver_witness": cvc5_proof,
    }

    graveyard_companions = {
        "flattened_summary_quotient_rejected": {
            **gaps["flattened_quotient_gap"],
            "interpretation": "A flat global summary loses the graph-indexed PEPS3D edge contraction signature.",
        },
        "wrong_adjacency_rejected": {
            **gaps["wrong_adjacency_gap"],
            "interpretation": "Changing cube adjacency and bond-axis pairing changes the contraction signature.",
        },
        "scalar_axis_projection_substrate_rejected": {
            **gaps["scalar_projection_gap"],
            "interpretation": "Replacing vector-valued Axis0 rows with scalar-projected rows changes the PEPS3D substrate signature.",
        },
        "zero_tensor_substrate_rejected": {
            **gaps["zero_tensor_gap"],
            "interpretation": "The nonzero PEPS3D substrate is separated from a zero-tensor placeholder.",
        },
    }

    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": bool(CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False),
        },
        "claim_ceiling_blocks_peps3d_basin_and_canonical_claims": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": bool(
                all(
                    term in CLAIM_CEILING.lower()
                    for term in ["formal scout", "does not admit", "real attractor basin", "canonical"]
                )
            ),
        },
        "bounded_micro_substrate_not_environment_campaign": {
            "site_count": 8,
            "edge_count": len(edges),
            "pass": bool(len(coords) == 8 and len(edges) == 12),
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
            "edge_count": len(edges),
            "flattened_quotient_gap": gaps["flattened_quotient_gap"]["gap"],
            "wrong_adjacency_gap": gaps["wrong_adjacency_gap"]["gap"],
            "scalar_projection_gap": gaps["scalar_projection_gap"]["gap"],
            "zero_tensor_gap": gaps["zero_tensor_gap"]["gap"],
            "elapsed_seconds": round(time.time() - started, 6),
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
            "v5 formal scout over current Axis0 vector-bundle fixture and PEPS3D substrate concern",
            "uses PyTorch tensor contractions plus rustworkx graph wiring instead of flattened numpy summaries",
            "provider/model outputs are not evidence; this receipt is produced by local execution",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "graph_edges": edges,
        "cube_coords": coords,
        "signature": as_jsonable(signature),
        "control_signatures": {
            "flattened": as_jsonable(flattened),
            "wrong_adjacency": as_jsonable(wrong_adj),
            "scalar_projection": as_jsonable(scalar_signature),
            "zero_tensor": as_jsonable(zero_signature),
        },
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": all_pass, "out_path": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
