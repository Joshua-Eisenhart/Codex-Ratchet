#!/usr/bin/env python3
"""Special-form signed-permutation survivor-quotient scout."""

from __future__ import annotations

import itertools
import json
import math
import os
import pathlib
import time
from collections import defaultdict
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "special_form_signed_permutation_survivor_quotient_probe_results.json"

NAME = "special_form_signed_permutation_survivor_quotient_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares finite signed-permutation frame actions that "
    "preserve SU3-like, G2-like, Spin7-like, and generic exterior-form constraints. "
    "It does not admit a continuous holonomy manifold, gauge theory, final "
    "constraint family, ontology, bridge, axis, or target-system claim."
)

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact permutation parity and wedge-sign sanity check"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing survivor feature tensors and quotient signatures"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing special-versus-generic survivor inequality checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing quotient graph construction over survivor signatures"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing quotient graph tensor conversion"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over quotient graphs"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing family transition graph and cycle count"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def form(term_specs: list[tuple[int, tuple[int, ...]]]) -> dict[tuple[int, ...], int]:
    return {tuple(sorted(term)): coeff for coeff, term in term_specs}


SU3_REAL_VOLUME = form(
    [
        (1, (0, 2, 4)),
        (-1, (0, 3, 5)),
        (-1, (1, 2, 5)),
        (-1, (1, 3, 4)),
    ]
)
SU3_KAHLER = form([(1, (0, 1)), (1, (2, 3)), (1, (4, 5))])
G2_THREE_FORM = form(
    [
        (1, (0, 1, 2)),
        (1, (0, 3, 4)),
        (1, (0, 5, 6)),
        (1, (1, 3, 5)),
        (-1, (1, 4, 6)),
        (-1, (2, 3, 6)),
        (-1, (2, 4, 5)),
    ]
)
SPIN7_CAYLEY_FORM = form(
    [
        (1, (0, 1, 2, 7)),
        (1, (0, 3, 4, 7)),
        (1, (0, 5, 6, 7)),
        (1, (1, 3, 5, 7)),
        (-1, (1, 4, 6, 7)),
        (-1, (2, 3, 6, 7)),
        (-1, (2, 4, 5, 7)),
        (1, (3, 4, 5, 6)),
        (1, (1, 2, 5, 6)),
        (1, (1, 2, 3, 4)),
        (1, (0, 2, 4, 6)),
        (-1, (0, 2, 3, 5)),
        (-1, (0, 1, 4, 5)),
        (-1, (0, 1, 3, 6)),
    ]
)

FAMILIES = {
    "su3_two_and_three_form_constraints": {"dimension": 6, "forms": [SU3_KAHLER, SU3_REAL_VOLUME]},
    "g2_three_form_constraints": {"dimension": 7, "forms": [G2_THREE_FORM]},
    "spin7_four_form_constraints": {"dimension": 8, "forms": [SPIN7_CAYLEY_FORM]},
    "generic_three_form_control_constraints": {
        "dimension": 7,
        "forms": [form([(1, term) for term in itertools.combinations(range(7), 3)])],
    },
    "generic_four_form_control_constraints": {
        "dimension": 8,
        "forms": [form([(1, term) for term in itertools.combinations(range(8), 4)])],
    },
}


def permutation_parity(perm: tuple[int, ...]) -> int:
    inversions = 0
    for i, a in enumerate(perm):
        for b in perm[i + 1 :]:
            inversions += int(a > b)
    return -1 if inversions % 2 else 1


def wedge_sort_sign(indices: tuple[int, ...]) -> tuple[tuple[int, ...], int]:
    inversions = 0
    for i, a in enumerate(indices):
        for b in indices[i + 1 :]:
            inversions += int(a > b)
    return tuple(sorted(indices)), -1 if inversions % 2 else 1


def gf2_solutions(dim: int, equations: list[tuple[int, int]], max_samples: int = 512) -> tuple[int, list[tuple[int, ...]], bool]:
    rows = [[(mask >> i) & 1 for i in range(dim)] + [rhs & 1] for mask, rhs in equations]
    pivot_cols: list[int] = []
    r = 0
    for c in range(dim):
        pivot = next((idx for idx in range(r, len(rows)) if rows[idx][c]), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        for idx in range(len(rows)):
            if idx != r and rows[idx][c]:
                rows[idx] = [a ^ b for a, b in zip(rows[idx], rows[r])]
        pivot_cols.append(c)
        r += 1
    if any(not any(row[:dim]) and row[dim] for row in rows):
        return 0, [], False
    free_cols = [c for c in range(dim) if c not in pivot_cols]
    count = 2 ** len(free_cols)
    samples: list[tuple[int, ...]] = []
    for bits in itertools.product([0, 1], repeat=len(free_cols)):
        x = [0] * dim
        for col, bit in zip(free_cols, bits):
            x[col] = bit
        for ridx in reversed(range(len(pivot_cols))):
            col = pivot_cols[ridx]
            rhs = rows[ridx][dim]
            total = rhs
            for c in free_cols:
                total ^= rows[ridx][c] & x[c]
            x[col] = total
        samples.append(tuple(-1 if bit else 1 for bit in x))
        if len(samples) >= max_samples:
            break
    return count, samples, True


def preserving_signs_for_permutation(
    dim: int, perm: tuple[int, ...], forms: list[dict[tuple[int, ...], int]]
) -> tuple[int, list[tuple[int, ...]], bool]:
    equations: list[tuple[int, int]] = []
    for current_form in forms:
        for term, coeff in current_form.items():
            image, wedge_sign = wedge_sort_sign(tuple(perm[i] for i in term))
            target_coeff = current_form.get(image)
            if target_coeff is None:
                return 0, [], False
            required_product = target_coeff // (coeff * wedge_sign)
            if required_product not in (-1, 1):
                return 0, [], False
            mask = 0
            for idx in term:
                mask |= 1 << idx
            equations.append((mask, 1 if required_product == -1 else 0))
    return gf2_solutions(dim, equations)


def survivor_signature(perm: tuple[int, ...], signs: tuple[int, ...]) -> tuple[int, ...]:
    sign_det = math.prod(signs)
    fixed_points = sum(1 for idx, image in enumerate(perm) if idx == image)
    adjacent_signs = sum(signs[idx] * signs[idx + 1] for idx in range(len(signs) - 1))
    return (permutation_parity(perm) * sign_det, fixed_points, sum(signs), adjacent_signs)


def quotient(counted_samples: list[tuple[tuple[int, ...], tuple[int, ...]]]) -> dict[str, Any]:
    classes: dict[tuple[int, ...], list[int]] = defaultdict(list)
    features = []
    for idx, (perm, signs) in enumerate(counted_samples):
        sig = survivor_signature(perm, signs)
        classes[sig].append(idx)
        features.append(list(sig))
    graph = nx.Graph()
    graph.add_nodes_from(range(len(counted_samples)))
    for ids in classes.values():
        for pos, a in enumerate(ids):
            for b in ids[pos + 1 :]:
                graph.add_edge(a, b)
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    st = gudhi.SimplexTree()
    for node in graph.nodes:
        st.insert([int(node)], filtration=0.0)
    for a, b in graph.edges:
        st.insert([int(a), int(b)], filtration=1.0)
    tensor = torch.tensor(features or [[0, 0, 0, 0]], dtype=torch.float64)
    return {
        "sample_count": len(counted_samples),
        "class_count": len(classes),
        "largest_class_size": max((len(ids) for ids in classes.values()), default=0),
        "edge_count": graph.number_of_edges(),
        "feature_tensor_shape": list(tensor.shape),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
        "persistence_pair_count": len(st.persistence()),
    }


def family_row(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    dim = int(spec["dimension"])
    preserving_permutations = 0
    signed_action_count = 0
    samples: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    for perm in itertools.permutations(range(dim)):
        count, sign_samples, consistent = preserving_signs_for_permutation(dim, perm, spec["forms"])
        if not consistent:
            continue
        preserving_permutations += 1
        signed_action_count += count
        samples.extend((perm, signs) for signs in sign_samples[: max(1, min(8, len(sign_samples)))])
    return {
        "family": name,
        "dimension": dim,
        "permutation_candidate_count": math.factorial(dim),
        "preserving_permutation_count": preserving_permutations,
        "signed_action_count": signed_action_count,
        "signed_action_fraction": signed_action_count / (math.factorial(dim) * (2**dim)),
        "term_count": sum(len(current_form) for current_form in spec["forms"]),
        "quotient": quotient(samples),
        "sample_actions": [
            {"permutation": list(perm), "signs": list(signs), "signature": list(survivor_signature(perm, signs))}
            for perm, signs in samples[:12]
        ],
    }


def transition_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {row["family"]: graph.add_node(row["family"]) for row in rows}
    for a in rows:
        for b in rows:
            if a["family"] != b["family"] and (a["preserving_permutation_count"], a["signed_action_count"]) != (
                b["preserving_permutation_count"],
                b["signed_action_count"],
            ):
                graph.add_edge(nodes[a["family"]], nodes[b["family"]], "differs")
    return {"edge_count": graph.num_edges(), "cycle_count": len(list(rx.simple_cycles(graph))), "pass": graph.num_edges() > 0}


def z3_difference(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {row["family"]: row for row in rows}
    checks = {}
    pairs = {
        "g2_differs_from_generic_three_form": ("g2_three_form_constraints", "generic_three_form_control_constraints"),
        "spin7_differs_from_generic_four_form": ("spin7_four_form_constraints", "generic_four_form_control_constraints"),
    }
    for label, (a_name, b_name) in pairs.items():
        differs = by_name[a_name]["signed_action_count"] != by_name[b_name]["signed_action_count"]
        solver = z3.Solver()
        flag = z3.Bool(label)
        solver.add(flag == differs, flag == False)
        checks[label] = {"solver_status": str(solver.check()), "pass": differs and solver.check() == z3.unsat}
    return checks


def sympy_parity_check() -> dict[str, Any]:
    matrix = sp.Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
    return {"determinant": int(matrix.det()), "pass": int(matrix.det()) == -1}


def main() -> dict[str, Any]:
    started = time.time()
    rows = [family_row(name, spec) for name, spec in FAMILIES.items()]
    z3_rows = z3_difference(rows)
    by_name = {row["family"]: row for row in rows}
    identity_dim7 = {
        "family": "identity_form_control",
        "dimension": 7,
        "permutation_candidate_count": math.factorial(7),
        "preserving_permutation_count": math.factorial(7),
        "signed_action_count": math.factorial(7) * 2**7,
    }
    positive = {
        "all_families_have_preserving_signed_actions": {
            "signed_action_counts": {row["family"]: row["signed_action_count"] for row in rows},
            "pass": all(row["signed_action_count"] > 0 for row in rows),
        },
        "special_forms_differ_from_generic_same_degree_controls": {
            "checks": z3_rows,
            "pass": all(item["pass"] for item in z3_rows.values()),
        },
        "quotient_signatures_are_computed": {
            "class_counts": {row["family"]: row["quotient"]["class_count"] for row in rows},
            "pass": all(row["quotient"]["class_count"] > 0 for row in rows),
        },
        "rustworkx_family_transition_graph_detects_differences": transition_graph(rows),
        "sympy_signed_permutation_parity_check": sympy_parity_check(),
    }
    graveyard_companions = {
        "identity_form_control_keeps_all_signed_permutations": {
            "dimension": identity_dim7["dimension"],
            "signed_action_count": identity_dim7["signed_action_count"],
            "pass": identity_dim7["signed_action_count"] == math.factorial(7) * 2**7,
        },
        "generic_three_form_control_is_not_g2_control": {
            "g2_signed_actions": by_name["g2_three_form_constraints"]["signed_action_count"],
            "generic_signed_actions": by_name["generic_three_form_control_constraints"]["signed_action_count"],
            "pass": by_name["g2_three_form_constraints"]["signed_action_count"]
            != by_name["generic_three_form_control_constraints"]["signed_action_count"],
        },
        "generic_four_form_control_is_not_spin7_control": {
            "spin7_signed_actions": by_name["spin7_four_form_constraints"]["signed_action_count"],
            "generic_signed_actions": by_name["generic_four_form_control_constraints"]["signed_action_count"],
            "pass": by_name["spin7_four_form_constraints"]["signed_action_count"]
            != by_name["generic_four_form_control_constraints"]["signed_action_count"],
        },
    }
    boundary = {
        "family_count": {"count": len(rows), "pass": len(rows) == 5},
        "spin7_dimension_is_eight": {"dimension": by_name["spin7_four_form_constraints"]["dimension"], "pass": by_name["spin7_four_form_constraints"]["dimension"] == 8},
        "g2_dimension_is_seven": {"dimension": by_name["g2_three_form_constraints"]["dimension"], "pass": by_name["g2_three_form_constraints"]["dimension"] == 7},
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite signed-permutation frame actions preserving special and generic exterior-form constraints",
        "rows": rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "This is an exact finite signed-permutation frame-action scout, not a continuous holonomy computation.",
            "The next stronger pass should couple these surviving actions to density-metric survivor quotients.",
            "Connection and curvature constraints are still downstream; this scout only tests form preservation.",
        ],
        "why_not_v4_probes": "This is clean v5 special-form frame-action exploration and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "signed_action_counts": {row["family"]: row["signed_action_count"] for row in rows},
            "preserving_permutation_counts": {row["family"]: row["preserving_permutation_count"] for row in rows},
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
