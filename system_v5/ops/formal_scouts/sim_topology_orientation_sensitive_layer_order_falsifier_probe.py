#!/usr/bin/env python3
"""Orientation-sensitive repair for the symmetric topology layer-order scout.

The older topology_coupled_layer_order_and_row_count_falsifier intentionally
stays red: its GUDHI/XGI/TopoNetX readout erases orientation and cannot
distinguish a full reversal of the 13-layer tower.

This scout keeps the same narrow formal-scout boundary but adds
geometry-derived, directed, orientation-sensitive transition features. It
checks that full reversal is distinguishable while label renaming and storage
reindex/restoration remain no-ops. It also records an orientation-erased
readout control that reproduces the old full-reversal blindness.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "topology_orientation_sensitive_layer_order_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "orientation_sensitive_topology_layer_order_falsifier"
CLAIM_CEILING = (
    "Formal scout only: repairs the prior symmetric topology readout by adding "
    "geometry-derived directed/oriented transition features that distinguish "
    "full layer reversal. It does not admit a final layer order, final "
    "topology, final manifold, bridge, axis, or target-system claim."
)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: constructs geometry feature tensors and signed orientation/transition checksums",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing control: orientation-erased Vietoris-Rips persistence reproduces the old reversal-blind readout",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing control: unordered adjacent-triple hypergraph records the reversal-erased topology surface",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing control: unordered simplicial complex records row-count and degenerate-triple controls",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: directed path graph records source/sink and directed edge checksum",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: proves signature equality is UNSAT for reversal/count controls and SAT for no-op controls",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: symbolic determinant identity verifies that reversing an oriented triple negates its signed volume",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


@dataclass(frozen=True)
class LayerGeometry:
    label: str
    sequence_index: int
    carrier_rank: float
    fiber_rank: float
    holonomy_turn: float
    chirality_charge: float
    coupling_degree: float
    constraint_depth: float


LAYERS: list[LayerGeometry] = [
    LayerGeometry("finite_constraint_complex", 0, 1.0, 0.0, 0.00, 0.0, 0.0, 1.0),
    LayerGeometry("complex_hilbert_carrier", 1, 2.0, 0.0, 0.08, 0.0, 0.5, 1.5),
    LayerGeometry("unit_spinor_sphere", 2, 2.0, 1.0, 0.21, 1.0, 0.8, 2.0),
    LayerGeometry("projective_base_sphere", 3, 3.0, 1.0, 0.34, 0.5, 1.0, 2.3),
    LayerGeometry("hopf_fiber_bundle", 4, 3.0, 2.0, 0.55, 1.0, 1.4, 2.8),
    LayerGeometry("hopf_torus_leaf_family", 5, 4.0, 2.0, 0.89, -0.5, 1.7, 3.1),
    LayerGeometry("connection_holonomy_geometry", 6, 4.0, 3.0, 1.44, 1.0, 2.1, 3.6),
    LayerGeometry("weyl_spinor_bundle", 7, 5.0, 3.0, 2.33, -1.0, 2.4, 4.0),
    LayerGeometry("chirality_orientation_cover", 8, 5.0, 4.0, 3.77, 1.0, 2.9, 4.6),
    LayerGeometry("clifford_module_geometry", 9, 6.0, 4.0, 6.10, -1.0, 3.5, 5.1),
    LayerGeometry("frame_bundle_structure_reduction", 10, 6.0, 5.0, 9.87, 0.5, 4.2, 5.8),
    LayerGeometry("tensor_product_coupling_geometry", 11, 7.0, 5.0, 15.97, -0.5, 5.0, 6.4),
    LayerGeometry("dynamic_transition_ratchet_geometry", 12, 8.0, 6.0, 25.84, 1.0, 6.0, 7.2),
]


def q(value: float) -> int:
    return int(round(float(value) * 1_000_000))


def feature_tensor(order: list[LayerGeometry]) -> torch.Tensor:
    rows = [
        [
            layer.carrier_rank,
            layer.fiber_rank,
            layer.holonomy_turn,
            layer.chirality_charge,
            layer.coupling_degree,
            layer.constraint_depth,
        ]
        for layer in order
    ]
    return torch.tensor(rows, dtype=torch.float64)


def adjacent_triples(order: list[LayerGeometry]) -> list[tuple[int, int, int]]:
    return [
        (
            order[i].sequence_index,
            order[i + 1].sequence_index,
            order[i + 2].sequence_index,
        )
        for i in range(len(order) - 2)
    ]


def gudhi_erased_signature(order: list[LayerGeometry]) -> dict[str, int]:
    points = feature_tensor(order)[:, :4].tolist()
    if len(points) < 2:
        return {"gudhi_h0_count": 0, "gudhi_h0_sum_q": 0, "gudhi_h1_count": 0, "gudhi_h1_sum_q": 0}
    rips = gudhi.RipsComplex(points=points)
    st = rips.create_simplex_tree(max_dimension=2)
    st.persistence()
    h0: list[float] = []
    h1: list[float] = []
    for dim, (birth, death) in st.persistence():
        if death == float("inf"):
            continue
        lifetime = float(death - birth)
        if dim == 0:
            h0.append(lifetime)
        elif dim == 1:
            h1.append(lifetime)
    return {
        "gudhi_h0_count": len(h0),
        "gudhi_h0_sum_q": q(sum(h0)),
        "gudhi_h1_count": len(h1),
        "gudhi_h1_sum_q": q(sum(h1)),
    }


def xgi_erased_signature(order: list[LayerGeometry]) -> dict[str, int]:
    hypergraph = xgi.Hypergraph()
    degenerate = 0
    for triple in adjacent_triples(order):
        if len(set(triple)) < 3:
            degenerate += 1
        hypergraph.add_edge(list(triple))
    degrees = [int(hypergraph.degree(node)) for node in hypergraph.nodes]
    return {
        "xgi_num_nodes": int(hypergraph.num_nodes),
        "xgi_num_edges": int(hypergraph.num_edges),
        "xgi_degree_sum": int(sum(degrees)),
        "xgi_max_degree": int(max(degrees)) if degrees else 0,
        "xgi_degenerate_triples": degenerate,
    }


def tnx_erased_signature(order: list[LayerGeometry]) -> dict[str, int]:
    complex_ = tnx.SimplicialComplex()
    for layer in order:
        complex_.add_node(layer.sequence_index)
    degenerate = 0
    for triple in adjacent_triples(order):
        if len(set(triple)) < 3:
            degenerate += 1
            continue
        complex_.add_simplex(list(triple))
    skeleton_sizes = []
    for dim in range(complex_.dim + 1):
        skeleton_sizes.append(int(len(list(complex_.skeleton(dim)))))
    return {
        "tnx_dim": int(complex_.dim),
        "tnx_skeleton_sum": int(sum(skeleton_sizes)),
        "tnx_degenerate_triples": degenerate,
    }


def rustworkx_directed_signature(order: list[LayerGeometry]) -> dict[str, int]:
    graph = rx.PyDiGraph()
    node_ids = [
        graph.add_node((layer.sequence_index, layer.carrier_rank, layer.fiber_rank))
        for layer in order
    ]
    features = feature_tensor(order)
    weights = torch.tensor([0.11, -0.17, 0.23, 0.31, -0.07, 0.13], dtype=torch.float64)
    checksum = 0.0
    for pos in range(len(order) - 1):
        delta = features[pos + 1] - features[pos]
        edge_weight = float(torch.dot(delta, weights).item())
        src_idx = order[pos].sequence_index
        dst_idx = order[pos + 1].sequence_index
        checksum += (pos + 1) * edge_weight + 0.001 * (src_idx - dst_idx)
        graph.add_edge(node_ids[pos], node_ids[pos + 1], edge_weight)
    topo = [order[idx].sequence_index for idx in rx.topological_sort(graph)]
    return {
        "rx_num_nodes": int(graph.num_nodes()),
        "rx_num_edges": int(graph.num_edges()),
        "rx_is_dag": int(rx.is_directed_acyclic_graph(graph)),
        "rx_source_sequence_index": int(order[0].sequence_index) if order else -1,
        "rx_sink_sequence_index": int(order[-1].sequence_index) if order else -1,
        "rx_topological_checksum": int(sum((i + 1) * node for i, node in enumerate(topo))),
        "rx_directed_edge_checksum_q": q(checksum),
    }


def orientation_tensor_signature(order: list[LayerGeometry]) -> dict[str, int]:
    features = feature_tensor(order)
    if features.shape[0] < 3:
        return {
            "oriented_triple_count": 0,
            "signed_volume_sum_q": 0,
            "signed_chirality_flux_q": 0,
            "signed_depth_flux_q": 0,
        }
    signed_volume_sum = 0.0
    signed_chirality_flux = 0.0
    signed_depth_flux = 0.0
    for pos in range(features.shape[0] - 2):
        triple = torch.stack(
            [
                features[pos, [0, 2, 5]],
                features[pos + 1, [0, 2, 5]],
                features[pos + 2, [0, 2, 5]],
            ]
        )
        signed_volume_sum += float(torch.linalg.det(triple).item())
        signed_chirality_flux += float(
            features[pos, 3] * features[pos + 1, 2]
            - features[pos + 1, 3] * features[pos, 2]
        )
        signed_depth_flux += float(
            features[pos, 5] * features[pos + 2, 4]
            - features[pos + 2, 5] * features[pos, 4]
        )
    return {
        "oriented_triple_count": int(features.shape[0] - 2),
        "signed_volume_sum_q": q(signed_volume_sum),
        "signed_chirality_flux_q": q(signed_chirality_flux),
        "signed_depth_flux_q": q(signed_depth_flux),
    }


def orientation_erased_signature(order: list[LayerGeometry]) -> dict[str, int]:
    signature: dict[str, int] = {"row_count": len(order)}
    signature.update(gudhi_erased_signature(order))
    signature.update(xgi_erased_signature(order))
    signature.update(tnx_erased_signature(order))
    return signature


def orientation_sensitive_signature(order: list[LayerGeometry]) -> dict[str, int]:
    signature = orientation_erased_signature(order)
    signature.update(orientation_tensor_signature(order))
    signature.update(rustworkx_directed_signature(order))
    return signature


def z3_equality(sig_a: dict[str, int], sig_b: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    for key in sorted(set(sig_a) | set(sig_b)):
        left = z3.Int(f"left_{key}")
        right = z3.Int(f"right_{key}")
        solver.add(left == int(sig_a.get(key, 0)))
        solver.add(right == int(sig_b.get(key, 0)))
        solver.add(left == right)
    status = solver.check()
    return {
        "status": str(status),
        "equal_under_z3": status == z3.sat,
        "distinct_under_z3": status == z3.unsat,
    }


def sympy_reverse_determinant_identity() -> dict[str, Any]:
    a1, a2, a3, b1, b2, b3, c1, c2, c3 = sp.symbols("a1 a2 a3 b1 b2 b3 c1 c2 c3")
    forward = sp.Matrix([[a1, a2, a3], [b1, b2, b3], [c1, c2, c3]]).det()
    reversed_ = sp.Matrix([[c1, c2, c3], [b1, b2, b3], [a1, a2, a3]]).det()
    identity = sp.simplify(forward + reversed_)
    return {
        "identity": "det(a,b,c) + det(c,b,a) == 0",
        "sympy_simplified": str(identity),
        "pass": identity == 0,
    }


def make_inflated(order: list[LayerGeometry], dup_index: int) -> list[LayerGeometry]:
    out = list(order)
    out.insert(dup_index + 1, order[dup_index])
    return out


def make_deflated(order: list[LayerGeometry], drop_index: int) -> list[LayerGeometry]:
    out = list(order)
    out.pop(drop_index)
    return out


def make_label_renamed(order: list[LayerGeometry]) -> list[LayerGeometry]:
    return [replace(layer, label=f"renamed_layer_{i:02d}") for i, layer in enumerate(order)]


def make_storage_reindexed_restored(order: list[LayerGeometry]) -> list[LayerGeometry]:
    stored_backwards = list(reversed(order))
    return sorted(stored_backwards, key=lambda layer: layer.sequence_index)


def expected_distinct(
    label: str,
    candidate: list[LayerGeometry],
    correct_signature: dict[str, int],
) -> dict[str, Any]:
    sig = orientation_sensitive_signature(candidate)
    z3_result = z3_equality(sig, correct_signature)
    return {
        "label": label,
        "row_count": len(candidate),
        "order_sequence_head": [layer.sequence_index for layer in candidate[:5]],
        "signature": sig,
        "z3": z3_result,
        "pass": sig != correct_signature and z3_result["distinct_under_z3"],
    }


def expected_noop(
    label: str,
    candidate: list[LayerGeometry],
    correct_signature: dict[str, int],
) -> dict[str, Any]:
    sig = orientation_sensitive_signature(candidate)
    z3_result = z3_equality(sig, correct_signature)
    return {
        "label": label,
        "row_count": len(candidate),
        "order_sequence_head": [layer.sequence_index for layer in candidate[:5]],
        "signature": sig,
        "z3": z3_result,
        "pass": sig == correct_signature and z3_result["equal_under_z3"],
    }


def main() -> dict[str, Any]:
    started = time.time()
    correct_signature = orientation_sensitive_signature(LAYERS)
    correct_erased_signature = orientation_erased_signature(LAYERS)
    reversed_layers = list(reversed(LAYERS))
    reverse_sensitive_signature = orientation_sensitive_signature(reversed_layers)
    reverse_erased_signature = orientation_erased_signature(reversed_layers)

    positive = {
        "correct_order_has_deterministic_orientation_sensitive_signature": {
            "signature": correct_signature,
            "repeat_signature": orientation_sensitive_signature(LAYERS),
            "pass": orientation_sensitive_signature(LAYERS) == correct_signature,
        },
        "orientation_signal_is_nonzero": {
            "signed_volume_sum_q": correct_signature["signed_volume_sum_q"],
            "signed_chirality_flux_q": correct_signature["signed_chirality_flux_q"],
            "signed_depth_flux_q": correct_signature["signed_depth_flux_q"],
            "pass": any(
                correct_signature[key] != 0
                for key in (
                    "signed_volume_sum_q",
                    "signed_chirality_flux_q",
                    "signed_depth_flux_q",
                )
            ),
        },
    }

    graveyard_companions: dict[str, dict[str, Any]] = {
        "full_reverse_distinguished_by_orientation_sensitive_readout": expected_distinct(
            "full_reverse", reversed_layers, correct_signature
        ),
        "row_count_inflated_middle_duplicate_distinguished": expected_distinct(
            "row_count_inflated_middle_duplicate",
            make_inflated(LAYERS, dup_index=6),
            correct_signature,
        ),
        "row_count_deflated_left_interior_distinguished": expected_distinct(
            "row_count_deflated_left_interior",
            make_deflated(LAYERS, drop_index=3),
            correct_signature,
        ),
        "row_count_deflated_right_interior_distinguished": expected_distinct(
            "row_count_deflated_right_interior",
            make_deflated(LAYERS, drop_index=9),
            correct_signature,
        ),
        "storage_reindex_restored_noop": expected_noop(
            "storage_reindex_restored",
            make_storage_reindexed_restored(LAYERS),
            correct_signature,
        ),
        "label_rename_noop": expected_noop(
            "label_rename_noop",
            make_label_renamed(LAYERS),
            correct_signature,
        ),
        "orientation_erased_readout_full_reverse_noop": {
            "label": "orientation_erased_full_reverse",
            "correct_erased_signature": correct_erased_signature,
            "reverse_erased_signature": reverse_erased_signature,
            "z3": z3_equality(reverse_erased_signature, correct_erased_signature),
            "pass": reverse_erased_signature == correct_erased_signature
            and z3_equality(reverse_erased_signature, correct_erased_signature)["equal_under_z3"],
        },
    }

    reverse_z3 = z3_equality(reverse_sensitive_signature, correct_signature)
    sympy_identity = sympy_reverse_determinant_identity()
    boundary = {
        "full_reverse_equality_unsat_after_orientation_repair": {
            "z3": reverse_z3,
            "correct_signed_volume_sum_q": correct_signature["signed_volume_sum_q"],
            "reverse_signed_volume_sum_q": reverse_sensitive_signature["signed_volume_sum_q"],
            "pass": reverse_z3["distinct_under_z3"],
        },
        "orientation_erased_readout_reproduces_old_reversal_blindness": {
            "correct_erased_signature": correct_erased_signature,
            "reverse_erased_signature": reverse_erased_signature,
            "pass": correct_erased_signature == reverse_erased_signature,
        },
        "sympy_oriented_triple_reversal_negates_signed_volume": sympy_identity,
        "promotion_boundary_remains_formal_scout_only": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
    }

    companion_total = len(graveyard_companions)
    companion_passed = sum(1 for row in graveyard_companions.values() if row["pass"])
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_boundary": "formal_scout only; no final topology/manifold/layer-order promotion",
        "promotion_condition": "blocked until independent admitted receipts test the layer geometry under real downstream consumers",
        "math_object": "13-row geometry-derived directed layer path with orientation-sensitive transition readout",
        "candidate_layers": [layer.label for layer in LAYERS],
        "geometry_feature_columns": [
            "carrier_rank",
            "fiber_rank",
            "holonomy_turn",
            "chirality_charge",
            "coupling_degree",
            "constraint_depth",
        ],
        "correct_signature": correct_signature,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": companion_total,
            "passed": companion_passed,
            "variants": sorted(graveyard_companions),
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout repair probe, not a v4 canonical sim receipt.",
            "The green result only repairs one geometric readout blocker: full reversal distinguishability.",
            "The orientation-erased control remains reversal-blind, so topology/manifold promotion is explicitly blocked.",
        ],
        "nearby_variant_boundaries": [
            "Label renaming is a no-op because labels are not part of the repaired signature.",
            "Storage reindex/restoration is a no-op because sequence_index restores the same geometry path.",
            "Inflation/deflation are distinguished as row-count and degenerate-triple controls.",
        ],
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": bool(all_pass),
        "summary": {
            "all_pass": bool(all_pass),
            "companion_passed": companion_passed,
            "companion_total": companion_total,
            "full_reverse_distinguished": graveyard_companions[
                "full_reverse_distinguished_by_orientation_sensitive_readout"
            ]["pass"],
            "orientation_erased_reverse_blind": graveyard_companions[
                "orientation_erased_readout_full_reverse_noop"
            ]["pass"],
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
