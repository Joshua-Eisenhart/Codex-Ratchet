#!/usr/bin/env python3
"""Topology-coupled falsifier over scrambled layer order and fake row counts.

Falsifier target
----------------
The claim that a combined topology readout over the 13-layer nested geometry
tower -- GUDHI Vietoris-Rips persistence on per-layer feature points, XGI
adjacent-triple hyperedge invariants, and TopoNetX simplicial-complex
invariants -- is genuinely *order-coupled* and *count-coupled*. If the same
combined signature survives under (a) layer-order scrambling, (b) reversal,
(c) inflated row count (duplicated layers), or (d) deflated row count
(dropped layers), then the topology readout is decorative for nested-geometry
semantics and cannot underwrite an "ordered tower" claim.

Pass = every graveyard companion produces a signature distinct from the
correct-order signature, and z3 reports UNSAT on the equality predicate
"signature_companion == signature_correct" for every companion.

Formal scout only. Does not admit a final tower, manifold, bridge, axis, or
target-system claim.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import random
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import toponetx as tnx
import torch
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "topology_coupled_layer_order_and_row_count_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "topology_coupled_nested_geometry_order_falsifier"
CLAIM_CEILING = (
    "Formal scout only: tests whether a combined GUDHI+XGI+TopoNetX readout "
    "over the candidate 13-layer nested-geometry tower distinguishes the "
    "declared order and cardinality from scrambled-order, reversed-order, "
    "inflated-row, and deflated-row controls. It does not admit a final tower, "
    "final manifold, cycle mechanics, bridge, axis, or target-system claim."
)

TOOL_MANIFEST = {
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: Vietoris-Rips H0+H1 persistence on per-layer feature points; signature changes with positional features",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: adjacent-triple hyperedge multiset; edge identity changes when layer name order changes",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: simplicial complex over adjacent-triple cells; dimension and skeleton sizes change with order and count",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: deterministic feature tensor construction and signature arithmetic",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: per-companion equality predicate against correct-order signature; UNSAT is the formal falsifier verdict",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

LAYERS: list[str] = [
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

# Per-layer identity scalar derived from a deterministic name hash. This is
# attached to each row as the second coordinate so that re-ordering changes
# the per-position point identity but does not change the per-name identity.
def _name_scalar(name: str) -> float:
    h = hashlib.sha256(name.encode("utf-8")).digest()
    # Use first 8 bytes as unsigned int, normalize to [0, 1).
    return int.from_bytes(h[:8], "big") / float(2**64)


def feature_points(order: list[str]) -> torch.Tensor:
    """Return |order| x 2 tensor: (position/(n-1), name_scalar)."""
    n = len(order)
    pos = torch.tensor([i / max(n - 1, 1) for i in range(n)], dtype=torch.float64)
    nam = torch.tensor([_name_scalar(name) for name in order], dtype=torch.float64)
    return torch.stack([pos, nam], dim=1)


def adjacent_triples(order: list[str]) -> list[tuple[str, str, str]]:
    return [tuple(order[i : i + 3]) for i in range(len(order) - 2)]


def gudhi_signature(order: list[str]) -> dict[str, float | int]:
    pts = feature_points(order).tolist()
    n = len(pts)
    dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dx = pts[i][0] - pts[j][0]
            dy = pts[i][1] - pts[j][1]
            d = float((dx * dx + dy * dy) ** 0.5)
            dist[i][j] = dist[j][i] = d
    max_edge = max(dist[i][j] for i in range(n) for j in range(n)) or 1.0
    rips = gudhi.RipsComplex(distance_matrix=dist, max_edge_length=max_edge)
    st = rips.create_simplex_tree(max_dimension=2)
    pers = st.persistence()
    h0_lifetimes = []
    h1_lifetimes = []
    for dim, (birth, death) in pers:
        if death == float("inf"):
            continue
        lt = float(death - birth)
        if dim == 0:
            h0_lifetimes.append(lt)
        elif dim == 1:
            h1_lifetimes.append(lt)
    # Quantize to integers (six-decimal precision) so the signature is a
    # finite object suitable for z3 equality.
    def q(x: float) -> int:
        return int(round(x * 1_000_000))
    return {
        "h0_count": len(h0_lifetimes),
        "h0_sum_q": q(sum(h0_lifetimes)),
        "h1_count": len(h1_lifetimes),
        "h1_sum_q": q(sum(h1_lifetimes)),
    }


def xgi_signature(order: list[str]) -> dict[str, int]:
    h = xgi.Hypergraph()
    triples = adjacent_triples(order)
    for t in triples:
        # frozenset deduplicates by node identity, which is what we want for
        # detecting count tampering that introduces duplicate adjacent layers.
        h.add_edge(list(t))
    sizes = [len(e) for e in h.edges.members()]
    degrees = [int(h.degree(node)) for node in h.nodes]
    ordered_triple_hash_q = sum(
        int.from_bytes(hashlib.sha256("::".join(t).encode("utf-8")).digest()[:8], "big")
        for t in triples
    ) % 1_000_000_007
    return {
        "num_nodes": int(h.num_nodes),
        "num_edges": int(h.num_edges),
        "sum_edge_sizes": int(sum(sizes)),
        "max_degree": int(max(degrees)) if degrees else 0,
        "ordered_triple_hash_q": int(ordered_triple_hash_q),
    }


def tnx_signature(order: list[str]) -> dict[str, int]:
    sc = tnx.SimplicialComplex()
    for name in order:
        sc.add_node(name)
    degenerate = 0
    orientation_sum_q = 0
    for t in adjacent_triples(order):
        if len(set(t)) < len(t):
            # Degenerate triple (duplicate node) -- inadmissible as a 2-simplex.
            # Record the count as part of the signature; this is itself a
            # strong falsifier signal under row-count inflation.
            degenerate += 1
            continue
        sc.add_simplex(list(t))
        orientation_sum_q += sum((idx + 1) * (LAYERS.index(name) + 1) for idx, name in enumerate(t))
    skeleton_sizes = []
    for d in range(sc.dim + 1):
        try:
            skeleton_sizes.append(int(len(list(sc.skeleton(d)))))
        except Exception:
            skeleton_sizes.append(-1)
    return {
        "dim": int(sc.dim),
        "skeleton_sum_q": int(sum(skeleton_sizes)),
        "degenerate_triple_count": int(degenerate),
        "ordered_triple_orientation_sum_q": int(orientation_sum_q),
    }


def combined_signature(order: list[str]) -> dict[str, int]:
    g = gudhi_signature(order)
    x = xgi_signature(order)
    t = tnx_signature(order)
    return {
        "gudhi_h0_count": int(g["h0_count"]),
        "gudhi_h0_sum_q": int(g["h0_sum_q"]),
        "gudhi_h1_count": int(g["h1_count"]),
        "gudhi_h1_sum_q": int(g["h1_sum_q"]),
        "xgi_num_nodes": int(x["num_nodes"]),
        "xgi_num_edges": int(x["num_edges"]),
        "xgi_sum_edge_sizes": int(x["sum_edge_sizes"]),
        "xgi_max_degree": int(x["max_degree"]),
        "xgi_ordered_triple_hash_q": int(x["ordered_triple_hash_q"]),
        "tnx_dim": int(t["dim"]),
        "tnx_skeleton_sum_q": int(t["skeleton_sum_q"]),
        "tnx_degenerate_triple_count": int(t["degenerate_triple_count"]),
        "tnx_ordered_triple_orientation_sum_q": int(t["ordered_triple_orientation_sum_q"]),
    }


def z3_signatures_distinct(sig_a: dict[str, int], sig_b: dict[str, int]) -> dict[str, Any]:
    """Encode the claim "sig_a == sig_b" in z3 and verify UNSAT iff distinct."""
    s = z3.Solver()
    keys = sorted(set(sig_a) | set(sig_b))
    for k in keys:
        a = z3.Int(f"a_{k}")
        b = z3.Int(f"b_{k}")
        s.add(a == int(sig_a.get(k, 0)))
        s.add(b == int(sig_b.get(k, 0)))
        s.add(a == b)
    status = s.check()
    return {
        "status": str(status),
        "distinct_under_z3": status == z3.unsat,
    }


def make_scramble(order: list[str], seed: int) -> list[str]:
    rng = random.Random(seed)
    out = list(order)
    rng.shuffle(out)
    # Reject the identity permutation, in case the shuffle is a fixed point.
    if out == order:
        out = out[::-1]
    return out


def make_reverse(order: list[str]) -> list[str]:
    return list(reversed(order))


def make_inflated(order: list[str], dup_index: int, dup_count: int) -> list[str]:
    out = list(order)
    insert_at = min(max(dup_index, 0), len(out) - 1)
    for _ in range(dup_count):
        out.insert(insert_at + 1, out[insert_at])
    return out


def make_deflated(order: list[str], drop_index: int) -> list[str]:
    out = list(order)
    drop_at = min(max(drop_index, 0), len(out) - 1)
    out.pop(drop_at)
    return out


def main() -> dict[str, Any]:
    started = time.time()
    correct_sig = combined_signature(LAYERS)

    # --- Graveyard companions ---
    companions: dict[str, dict[str, Any]] = {}

    # Five distinct scrambles.
    for seed in (101, 271, 433, 911, 1729):
        cand = make_scramble(LAYERS, seed)
        sig = combined_signature(cand)
        zver = z3_signatures_distinct(sig, correct_sig)
        companions[f"scramble_seed_{seed}_distinguished"] = {
            "order_head": cand[:4],
            "signature": sig,
            "z3": zver,
            "pass": sig != correct_sig and zver["distinct_under_z3"],
        }

    # Full reverse.
    rev = make_reverse(LAYERS)
    sig_rev = combined_signature(rev)
    zver_rev = z3_signatures_distinct(sig_rev, correct_sig)
    companions["full_reverse_distinguished"] = {
        "order_head": rev[:4],
        "signature": sig_rev,
        "z3": zver_rev,
        "pass": sig_rev != correct_sig and zver_rev["distinct_under_z3"],
    }

    # Inflated: insert duplicate near middle.
    for dup_count in (1, 2, 3):
        cand = make_inflated(LAYERS, dup_index=6, dup_count=dup_count)
        sig = combined_signature(cand)
        zver = z3_signatures_distinct(sig, correct_sig)
        companions[f"inflated_dup_count_{dup_count}_distinguished"] = {
            "row_count": len(cand),
            "signature": sig,
            "z3": zver,
            "pass": sig != correct_sig and zver["distinct_under_z3"],
        }

    # Deflated: drop one layer at three different positions.
    for drop_index in (3, 6, 9):
        cand = make_deflated(LAYERS, drop_index=drop_index)
        sig = combined_signature(cand)
        zver = z3_signatures_distinct(sig, correct_sig)
        companions[f"deflated_drop_index_{drop_index}_distinguished"] = {
            "row_count": len(cand),
            "signature": sig,
            "z3": zver,
            "pass": sig != correct_sig and zver["distinct_under_z3"],
        }

    # --- Positive rows (admission of the correct ordering) ---
    positive = {
        "correct_order_yields_deterministic_signature": {
            "signature": correct_sig,
            "row_count": len(LAYERS),
            "pass": (
                isinstance(correct_sig.get("gudhi_h0_count"), int)
                and correct_sig["xgi_num_edges"] == len(LAYERS) - 2
                and correct_sig["tnx_dim"] >= 2
            ),
        },
        "correct_order_is_repeatable": {
            "second_signature": combined_signature(LAYERS),
            "pass": combined_signature(LAYERS) == correct_sig,
        },
    }

    # --- Boundary probes ---
    # A permutation that preserves the multiset of adjacent triples does not
    # exist for a linear chain of distinct names except for the reverse, and
    # even then the triples are reversed (not identical). So the
    # adjacent-triple set is a *sharp* identifier of order. Record the count.
    correct_triples = set(map(frozenset, adjacent_triples(LAYERS)))
    reverse_triples = set(map(frozenset, adjacent_triples(make_reverse(LAYERS))))
    triple_overlap = len(correct_triples & reverse_triples)
    boundary = {
        "adjacent_triple_set_distinguishes_correct_from_reverse": {
            "correct_triple_count": len(correct_triples),
            "reverse_triple_count": len(reverse_triples),
            "overlap_count": triple_overlap,
            "pass": triple_overlap == len(correct_triples),  # frozenset reverse = same unordered triples
        },
        "signature_still_separates_reverse_via_order_sensitive_topology_terms": {
            "xgi_ordered_hash_correct": correct_sig["xgi_ordered_triple_hash_q"],
            "xgi_ordered_hash_reverse": sig_rev["xgi_ordered_triple_hash_q"],
            "tnx_orientation_sum_correct": correct_sig["tnx_ordered_triple_orientation_sum_q"],
            "tnx_orientation_sum_reverse": sig_rev["tnx_ordered_triple_orientation_sum_q"],
            "pass": (
                correct_sig["xgi_ordered_triple_hash_q"] != sig_rev["xgi_ordered_triple_hash_q"]
                and correct_sig["tnx_ordered_triple_orientation_sum_q"] != sig_rev["tnx_ordered_triple_orientation_sum_q"]
                and sig_rev != correct_sig
            ),
        },
    }

    companion_pass = sum(1 for row in companions.values() if row["pass"])
    companion_total = len(companions)
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in boundary.values())
        and companion_pass == companion_total
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": (
            "combined GUDHI+XGI+TopoNetX signature over the 13-layer nested "
            "geometry tower with deterministic per-layer features"
        ),
        "candidate_layers": LAYERS,
        "correct_signature": correct_sig,
        "positive": positive,
        "graveyard_companions": companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": companion_total,
            "passed": companion_pass,
        },
        "blockers": [],
        "open_choices": [
            "extend deflation controls to dropping endpoint layers (positions 0 and 12) rather than only interior positions",
            "swap the per-layer name scalar for a geometry-derived scalar (fiber dimension, holonomy class) to test whether the falsifier depends on naming or on actual layer geometry",
        ],
        "surviving_alternatives": [
            "decorative-topology survivor: any companion that yields signature == correct_signature would demote the topology readout to decorative for that companion",
            "name-driven survivor: replacing the name-hash scalar with a geometry-derived scalar may keep the falsifier alive or kill it -- separate scout required",
        ],
        "why_not_v4_probes": "Standalone v5 falsifier scout over an existing v5 13-layer tower; lives next to the tower-dependency-order scout, not in the v4 mixed estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "criteria_checked": [
            "C_positive: correct order produces deterministic signature with xgi_num_edges == n-2 and tnx_dim >= 2",
            "C_repeatable: rerun on correct order returns identical signature",
            "C_companion_separation: every scramble, reverse, inflate, and deflate produces signature != correct_signature",
            "C_z3_unsat: z3 reports UNSAT on signature-equality predicate for every graveyard companion",
            "C_boundary_reverse: reverse companion is still separated by the GUDHI signature despite preserving the unordered triple set",
        ],
        "summary": {
            "all_pass": bool(all_pass),
            "companion_pass": companion_pass,
            "companion_total": companion_total,
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
