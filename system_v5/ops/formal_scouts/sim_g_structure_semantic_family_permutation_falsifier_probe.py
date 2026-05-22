#!/usr/bin/env python3
"""Semantic-family permutation falsifier for nested G-structure order.

Formal scout only. This probe tests whether a thirteen-layer nested
G-structure carrier is sensitive to semantic family swaps rather than display
labels, storage order, layer row count, or raw index position.
"""

from __future__ import annotations

import hashlib
import json
import math
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

NAME = "g_structure_semantic_family_permutation_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "root_manifold_g_structure_semantic_family_permutation_falsifier"
CLAIM_CEILING = (
    "Formal scout only: finite PyTorch/rustworkx/z3/cvc5 check that a "
    "thirteen-layer nested G-structure carrier distinguishes semantic-family "
    "swaps from label, storage, row-count, and index-only controls. It does "
    "not admit a final G-structure, root manifold, engine, Axis0, basin, "
    "bridge, physics, target-system, or canonical claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing noncommuting tensor-network carrier and semantic-family swap gap measurements",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing semantic dependency DAG and semantic-order digest checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing admission gate for label/storage invariance, family distinction, and row-count graveyard checks",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent cross-solver check of the same semantic-family predicates",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive exact commutator witness for inter-family noncommutation",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive semantic graph digest recording",
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
    "sympy": "supportive",
    "hashlib": "supportive",
    "python_json": "supportive",
}

EPS_INVARIANT = 1e-11
EPS_INTER_FAMILY = 1e-3
EPS_FAMILY_DISTINCTION = 5e-4
DTYPE = torch.complex128


LAYERS: list[dict[str, Any]] = [
    {"role_id": "density_carrier_trace", "family": "carrier", "angle": 0.13},
    {"role_id": "complex_structure_J", "family": "complex_symplectic", "angle": 0.19},
    {"role_id": "symplectic_pairing", "family": "complex_symplectic", "angle": 0.23},
    {"role_id": "chirality_orientation_split", "family": "orientation_spin", "angle": 0.17},
    {"role_id": "spin_lift_double_cover", "family": "orientation_spin", "angle": 0.29},
    {"role_id": "line_splitting_e0", "family": "line_boundary", "angle": 0.11},
    {"role_id": "tilted_line_split", "family": "line_boundary", "angle": 0.31},
    {"role_id": "curvature_connection", "family": "connection_holonomy", "angle": 0.37},
    {"role_id": "holonomy_closure", "family": "connection_holonomy", "angle": 0.41},
    {"role_id": "tensor_coupling", "family": "tensor_entropy", "angle": 0.27},
    {"role_id": "entropy_gradient_flow", "family": "tensor_entropy", "angle": 0.33},
    {"role_id": "boundary_projection", "family": "line_boundary", "angle": 0.21},
    {"role_id": "frame_normalization", "family": "carrier", "angle": 0.15},
]


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def pauli() -> dict[str, torch.Tensor]:
    return {
        "I": torch.eye(2, dtype=DTYPE),
        "X": torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE),
        "Y": torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=DTYPE),
        "Z": torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE),
    }


P = pauli()


def kron(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return torch.kron(left, right)


FAMILY_GENERATORS = {
    "carrier": 0.62 * kron(P["Z"], P["I"]) + 0.18 * kron(P["I"], P["Z"]),
    "complex_symplectic": 0.57 * kron(P["X"], P["I"]) + 0.24 * kron(P["Y"], P["Y"]),
    "orientation_spin": 0.49 * kron(P["Y"], P["X"]) - 0.32 * kron(P["X"], P["Y"]),
    "line_boundary": 0.53 * kron(P["Z"], P["X"]) + 0.21 * kron(P["X"], P["Z"]),
    "connection_holonomy": 0.46 * kron(P["X"], P["X"]) + 0.35 * kron(P["Z"], P["Y"]),
    "tensor_entropy": 0.51 * kron(P["Y"], P["Z"]) + 0.28 * kron(P["I"], P["Y"]),
}


def canonical_layers() -> list[dict[str, Any]]:
    rows = []
    for idx, layer in enumerate(LAYERS):
        rows.append(
            {
                **layer,
                "semantic_position": idx,
                "display_label": f"L{idx:02d}_{layer['role_id']}",
                "storage_index": idx,
            }
        )
    return rows


def clone_layers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def swap_positions(rows: list[dict[str, Any]], left_role: str, right_role: str) -> list[dict[str, Any]]:
    out = clone_layers(rows)
    left = next(row for row in out if row["role_id"] == left_role)
    right = next(row for row in out if row["role_id"] == right_role)
    left["semantic_position"], right["semantic_position"] = right["semantic_position"], left["semantic_position"]
    return out


def label_scrambled(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = clone_layers(rows)
    labels = [row["display_label"] for row in out]
    rotated = labels[3:] + labels[:3]
    for row, label in zip(out, rotated):
        row["display_label"] = label
    return out


def storage_reindexed(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = list(reversed(clone_layers(rows)))
    for idx, row in enumerate(out):
        row["storage_index"] = idx
    return out


def unitary_for(row: dict[str, Any]) -> torch.Tensor:
    generator = FAMILY_GENERATORS[str(row["family"])]
    angle = float(row["angle"])
    return torch.matrix_exp(-1j * angle * generator)


def compose(rows: list[dict[str, Any]]) -> torch.Tensor:
    ordered = sorted(rows, key=lambda row: int(row["semantic_position"]))
    state = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j], dtype=DTYPE)
    unitary = torch.eye(4, dtype=DTYPE)
    for row in ordered:
        unitary = unitary_for(row) @ unitary
    return unitary @ state


def distance(left: torch.Tensor, right: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(left - right).real.item())


def semantic_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    ordered = sorted(rows, key=lambda row: int(row["semantic_position"]))
    node_ids = {}
    for row in ordered:
        node_ids[str(row["role_id"])] = graph.add_node(
            {
                "role_id": row["role_id"],
                "family": row["family"],
                "semantic_position": int(row["semantic_position"]),
                "display_label": row["display_label"],
                "storage_index": int(row["storage_index"]),
            }
        )
    for src, dst in zip(ordered, ordered[1:]):
        graph.add_edge(node_ids[str(src["role_id"])], node_ids[str(dst["role_id"])], "semantic_precedes")
    topo = [graph[idx] for idx in rx.topological_sort(graph)]
    semantic_payload = [
        {"role_id": row["role_id"], "family": row["family"], "semantic_position": row["semantic_position"]}
        for row in topo
    ]
    display_payload = [{"role_id": row["role_id"], "display_label": row["display_label"]} for row in topo]
    storage_payload = [{"role_id": row["role_id"], "storage_index": row["storage_index"]} for row in topo]
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "topological_role_ids": [str(row["role_id"]) for row in topo],
        "topological_families": [str(row["family"]) for row in topo],
        "semantic_digest": stable_hash(semantic_payload),
        "display_digest": stable_hash(display_payload),
        "storage_digest": stable_hash(storage_payload),
    }


def variant_suite() -> dict[str, Any]:
    baseline_rows = canonical_layers()
    baseline_output = compose(baseline_rows)
    baseline_graph = semantic_graph(baseline_rows)
    variants = {
        "label_scramble": label_scrambled(baseline_rows),
        "storage_reindex": storage_reindexed(baseline_rows),
        "intra_family_line_swap": swap_positions(baseline_rows, "line_splitting_e0", "tilted_line_split"),
        "intra_family_connection_swap": swap_positions(baseline_rows, "curvature_connection", "holonomy_closure"),
        "inter_family_complex_boundary_swap": swap_positions(baseline_rows, "complex_structure_J", "boundary_projection"),
        "inter_family_carrier_entropy_swap": swap_positions(baseline_rows, "density_carrier_trace", "entropy_gradient_flow"),
    }
    rows = {}
    for name, variant_rows in variants.items():
        output = compose(variant_rows)
        graph = semantic_graph(variant_rows)
        rows[name] = {
            "output_gap": distance(baseline_output, output),
            "row_count_signature": {
                "node_count": graph["node_count"],
                "edge_count": graph["edge_count"],
            },
            "semantic_digest_matches_baseline": graph["semantic_digest"] == baseline_graph["semantic_digest"],
            "display_digest_matches_baseline": graph["display_digest"] == baseline_graph["display_digest"],
            "storage_digest_matches_baseline": graph["storage_digest"] == baseline_graph["storage_digest"],
            "topological_role_ids": graph["topological_role_ids"],
            "topological_families": graph["topological_families"],
            "graph": graph,
        }
    intra_gaps = [rows["intra_family_line_swap"]["output_gap"], rows["intra_family_connection_swap"]["output_gap"]]
    inter_gaps = [
        rows["inter_family_complex_boundary_swap"]["output_gap"],
        rows["inter_family_carrier_entropy_swap"]["output_gap"],
    ]
    return {
        "baseline": {
            "graph": baseline_graph,
            "output_norm": float(torch.linalg.vector_norm(baseline_output).real.item()),
        },
        "variants": rows,
        "max_intra_family_gap": max(intra_gaps),
        "min_inter_family_gap": min(inter_gaps),
        "semantic_family_distinction_gap": min(inter_gaps) - max(intra_gaps),
    }


def sympy_commutator_witness() -> dict[str, Any]:
    x = sp.Matrix([[0, 1], [1, 0]])
    y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    z = sp.Matrix([[1, 0], [0, -1]])
    i2 = sp.eye(2)
    carrier = sp.kronecker_product(z, i2)
    complex_symplectic = sp.kronecker_product(x, i2)
    line_boundary = sp.kronecker_product(z, x)
    tensor_entropy = sp.kronecker_product(y, z)
    carrier_tensor_comm = carrier * tensor_entropy - tensor_entropy * carrier
    complex_line_comm = complex_symplectic * line_boundary - line_boundary * complex_symplectic
    return {
        "carrier_tensor_commutator_nonzero": bool(carrier_tensor_comm != sp.zeros(4)),
        "complex_line_commutator_nonzero": bool(complex_line_comm != sp.zeros(4)),
        "carrier_tensor_frobenius_squared": str(sum(value * sp.conjugate(value) for value in carrier_tensor_comm)),
        "complex_line_frobenius_squared": str(sum(value * sp.conjugate(value) for value in complex_line_comm)),
        "pass": bool(carrier_tensor_comm != sp.zeros(4) and complex_line_comm != sp.zeros(4)),
    }


def z3_admission(predicates: dict[str, bool]) -> dict[str, Any]:
    solver = z3.Solver()
    terms = {key: z3.Bool(key) for key in predicates}
    for key, value in predicates.items():
        solver.add(terms[key] == z3.BoolVal(value))
    solver.add(z3.And(*terms.values()))
    status = solver.check()
    return {"solver": "z3", "status": str(status), "joint_sat": status == z3.sat, "pass": status == z3.sat}


def cvc5_admission(predicates: dict[str, bool]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    terms = []
    for key, value in predicates.items():
        term = solver.mkConst(bool_sort, key)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(value)))
        terms.append(term)
    solver.assertFormula(solver.mkTerm(Kind.AND, *terms))
    status = solver.checkSat()
    return {"solver": "cvc5", "status": str(status), "joint_sat": status.isSat(), "pass": status.isSat()}


def main() -> int:
    started = time.time()
    suite = variant_suite()
    variants = suite["variants"]
    sympy_witness = sympy_commutator_witness()

    label_invariant = bool(
        variants["label_scramble"]["output_gap"] <= EPS_INVARIANT
        and variants["label_scramble"]["semantic_digest_matches_baseline"]
    )
    storage_invariant = bool(
        variants["storage_reindex"]["output_gap"] <= EPS_INVARIANT
        and variants["storage_reindex"]["semantic_digest_matches_baseline"]
    )
    intra_family_small = bool(suite["max_intra_family_gap"] <= EPS_INVARIANT)
    inter_family_variant = bool(suite["min_inter_family_gap"] > EPS_INTER_FAMILY)
    semantic_family_distinguished = bool(suite["semantic_family_distinction_gap"] > EPS_FAMILY_DISTINCTION)
    row_count_only_killed = bool(
        variants["inter_family_complex_boundary_swap"]["row_count_signature"]
        == variants["label_scramble"]["row_count_signature"]
        and variants["inter_family_complex_boundary_swap"]["output_gap"] > EPS_INTER_FAMILY
    )
    index_only_claim_killed = bool(
        variants["label_scramble"]["display_digest_matches_baseline"] is False
        and variants["label_scramble"]["output_gap"] <= EPS_INVARIANT
        and variants["storage_reindex"]["storage_digest_matches_baseline"] is False
        and variants["storage_reindex"]["output_gap"] <= EPS_INVARIANT
    )
    semantic_graph_variant = bool(
        not variants["inter_family_complex_boundary_swap"]["semantic_digest_matches_baseline"]
        and not variants["inter_family_carrier_entropy_swap"]["semantic_digest_matches_baseline"]
    )

    predicates = {
        "label_scramble_invariant": label_invariant,
        "storage_reindex_invariant": storage_invariant,
        "intra_family_permutation_low_or_noop": intra_family_small,
        "inter_family_permutation_variant": inter_family_variant,
        "semantic_family_distinction_gap_positive": semantic_family_distinguished,
        "row_count_only_killed": row_count_only_killed,
        "index_only_claim_killed": index_only_claim_killed,
        "semantic_graph_digest_variant_for_inter_family_swap": semantic_graph_variant,
        "sympy_inter_family_commutator_nonzero": bool(sympy_witness["pass"]),
        "promotion_disabled": PROMOTION_ALLOWED is False,
    }
    z3_receipt = z3_admission(predicates)
    cvc5_receipt = cvc5_admission(predicates)

    positive = {
        "semantic_family_gap_detected": {
            "min_inter_family_gap": suite["min_inter_family_gap"],
            "max_intra_family_gap": suite["max_intra_family_gap"],
            "semantic_family_distinction_gap": suite["semantic_family_distinction_gap"],
            "pass": semantic_family_distinguished,
        },
        "pytorch_family_order_carrier_executes": {
            "baseline_output_norm": suite["baseline"]["output_norm"],
            "layer_count": len(LAYERS),
            "family_count": len({row["family"] for row in LAYERS}),
            "pass": bool(math.isfinite(suite["baseline"]["output_norm"]) and len(LAYERS) == 13),
        },
        "rustworkx_semantic_graph_distinguishes_inter_family_swaps": {
            "baseline_digest": suite["baseline"]["graph"]["semantic_digest"],
            "inter_family_digest": variants["inter_family_complex_boundary_swap"]["graph"]["semantic_digest"],
            "pass": semantic_graph_variant,
        },
        "z3_cvc5_cross_solver_admission": {
            "z3": z3_receipt,
            "cvc5": cvc5_receipt,
            "pass": z3_receipt["pass"] and cvc5_receipt["pass"],
        },
    }
    graveyards = {
        "label_scramble_not_semantic_evidence": {
            "output_gap": variants["label_scramble"]["output_gap"],
            "semantic_digest_matches_baseline": variants["label_scramble"]["semantic_digest_matches_baseline"],
            "display_digest_matches_baseline": variants["label_scramble"]["display_digest_matches_baseline"],
            "pass": label_invariant,
        },
        "storage_reindex_not_semantic_evidence": {
            "output_gap": variants["storage_reindex"]["output_gap"],
            "semantic_digest_matches_baseline": variants["storage_reindex"]["semantic_digest_matches_baseline"],
            "storage_digest_matches_baseline": variants["storage_reindex"]["storage_digest_matches_baseline"],
            "pass": storage_invariant,
        },
        "row_count_only_evidence_killed": {
            "baseline_row_count": suite["baseline"]["graph"]["node_count"],
            "inter_family_row_count": variants["inter_family_complex_boundary_swap"]["row_count_signature"]["node_count"],
            "inter_family_gap": variants["inter_family_complex_boundary_swap"]["output_gap"],
            "pass": row_count_only_killed,
        },
        "index_only_layer_order_claim_killed": {
            "label_scramble_gap": variants["label_scramble"]["output_gap"],
            "storage_reindex_gap": variants["storage_reindex"]["output_gap"],
            "pass": index_only_claim_killed,
        },
    }
    boundary = {
        "sympy_inter_family_noncommutation_support": sympy_witness,
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_final_g_structure": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": "does not admit a final G-structure" in CLAIM_CEILING,
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
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
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "Bounded formal scout only; not a promoted G-structure or manifold proof.",
            "Finite 13-layer semantic-family permutation witness only.",
            "Does not admit Axis0, engine, basin, bridge, physics, or canonical claims.",
        ],
        "variant_suite": suite,
        "predicates": predicates,
        "provider_prompt_evidence": {
            "used_as_authority": False,
            "wave": "wave5_no_claude_20260519T050653Z",
            "summary": (
                "Grok/Gemini provider audits converged on semantic-family/layer-operator "
                "permutation as a next executable scout; local formal-scout receipt remains authority."
            ),
        },
        "all_pass": bool(all_pass),
        "runtime_seconds": time.time() - started,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
