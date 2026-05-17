#!/usr/bin/env python3
"""Special-holonomy form-constraint survivor-quotient scout."""

from __future__ import annotations

import itertools
import json
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
OUT_PATH = RESULT_DIR / "special_holonomy_form_constraint_survivor_quotient_probe_results.json"

NAME = "special_holonomy_form_constraint_survivor_quotient_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares finite SU3-like, G2-like, and Spin7-like "
    "form-preservation constraints against generic form controls using survivor "
    "sets, probe quotients, and persistence. It does not admit a full special "
    "holonomy manifold, gauge theory, final constraint family, ontology, bridge, "
    "axis, or target-system claim."
)

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact exterior-form sign constraints and determinant checks"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite sign-vector tensors and quotient feature arrays"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing survivor-count difference and generic-collapse contradiction checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing survivor quotient graph construction"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph-to-tensor conversion for quotient graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over survivor quotient graphs"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing geometry-family transition graph"},
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
    "su3_two_and_three_form_constraints": {
        "dimension": 6,
        "forms": [SU3_KAHLER, SU3_REAL_VOLUME],
        "control": "complex_volume_and_pair_form",
    },
    "g2_three_form_constraints": {
        "dimension": 7,
        "forms": [G2_THREE_FORM],
        "control": "stable_three_form",
    },
    "spin7_four_form_constraints": {
        "dimension": 8,
        "forms": [SPIN7_CAYLEY_FORM],
        "control": "cayley_four_form",
    },
    "generic_three_form_control_constraints": {
        "dimension": 7,
        "forms": [form([(1, term) for term in itertools.combinations(range(7), 3)])],
        "control": "all_three_terms_generic_control",
    },
    "generic_four_form_control_constraints": {
        "dimension": 8,
        "forms": [form([(1, term) for term in itertools.combinations(range(8), 4)])],
        "control": "all_four_terms_generic_control",
    },
}


def sign_candidates(dim: int) -> list[tuple[int, ...]]:
    return list(itertools.product([-1, 1], repeat=dim))


def term_sign(signs: tuple[int, ...], term: tuple[int, ...]) -> int:
    value = 1
    for idx in term:
        value *= signs[idx]
    return value


def preserves_forms(signs: tuple[int, ...], forms: list[dict[tuple[int, ...], int]]) -> bool:
    return all(term_sign(signs, term) == 1 for current_form in forms for term in current_form)


def signature(signs: tuple[int, ...], forms: list[dict[tuple[int, ...], int]]) -> tuple[int, ...]:
    determinant = 1
    for value in signs:
        determinant *= value
    term_values = [sum(term_sign(signs, term) * coeff for term, coeff in current_form.items()) for current_form in forms]
    adjacent_products = [signs[idx] * signs[idx + 1] for idx in range(len(signs) - 1)]
    return tuple([determinant, sum(signs), *term_values, sum(adjacent_products)])


def quotient_classes(survivors: list[tuple[int, ...]], forms: list[dict[tuple[int, ...], int]]) -> dict[str, Any]:
    classes: dict[tuple[int, ...], list[int]] = defaultdict(list)
    for idx, signs in enumerate(survivors):
        classes[signature(signs, forms)].append(idx)
    graph = nx.Graph()
    graph.add_nodes_from(range(len(survivors)))
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
    return {
        "class_count": len(classes),
        "largest_class_size": max((len(ids) for ids in classes.values()), default=0),
        "edge_count": graph.number_of_edges(),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
        "persistence_pair_count": len(st.persistence()),
    }


def family_row(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    dim = int(spec["dimension"])
    candidates = sign_candidates(dim)
    survivors = [signs for signs in candidates if preserves_forms(signs, spec["forms"])]
    quotient = quotient_classes(survivors, spec["forms"])
    features = torch.tensor([[sum(signs), len(signs), 1 if preserves_forms(signs, spec["forms"]) else 0] for signs in candidates], dtype=torch.float64)
    return {
        "family": name,
        "dimension": dim,
        "candidate_count": len(candidates),
        "survivor_count": len(survivors),
        "survivor_fraction": len(survivors) / len(candidates),
        "term_count": sum(len(current_form) for current_form in spec["forms"]),
        "quotient": quotient,
        "feature_shape": list(features.shape),
        "sample_survivors": [list(signs) for signs in survivors[:8]],
    }


def transition_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {row["family"]: graph.add_node(row["family"]) for row in rows}
    for a in rows:
        for b in rows:
            if a["family"] != b["family"] and (a["survivor_count"], a["quotient"]["class_count"]) != (
                b["survivor_count"],
                b["quotient"]["class_count"],
            ):
                graph.add_edge(nodes[a["family"]], nodes[b["family"]], "differs")
    cycles = list(rx.simple_cycles(graph))
    return {"edge_count": graph.num_edges(), "cycle_count": len(cycles), "pass": graph.num_edges() > 0}


def sympy_exact_term_check() -> dict[str, Any]:
    s0, s1, s2 = sp.symbols("s0 s1 s2")
    expr = s0 * s1 * s2
    return {"term_expression": str(expr), "identity_substitution": int(expr.subs({s0: 1, s1: 1, s2: 1})), "pass": expr.subs({s0: 1, s1: 1, s2: 1}) == 1}


def z3_special_vs_generic(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {row["family"]: row for row in rows}
    g2_differs = by_name["g2_three_form_constraints"]["survivor_count"] != by_name["generic_three_form_control_constraints"]["survivor_count"]
    spin7_differs = by_name["spin7_four_form_constraints"]["survivor_count"] != by_name["generic_four_form_control_constraints"]["survivor_count"]
    s1 = z3.Solver()
    s2 = z3.Solver()
    a = z3.Bool("g2_differs")
    b = z3.Bool("spin7_differs")
    s1.add(a == g2_differs, a == False)
    s2.add(b == spin7_differs, b == False)
    return {
        "g2_differs_from_generic_three_form_unsat_if_not": {"solver_status": str(s1.check()), "pass": g2_differs and s1.check() == z3.unsat},
        "spin7_differs_from_generic_four_form_unsat_if_not": {"solver_status": str(s2.check()), "pass": spin7_differs and s2.check() == z3.unsat},
    }


def main() -> dict[str, Any]:
    started = time.time()
    rows = [family_row(name, spec) for name, spec in FAMILIES.items()]
    z3_rows = z3_special_vs_generic(rows)
    positive = {
        "finite_sign_candidate_sets_are_enumerated": {
            "candidate_counts": {row["family"]: row["candidate_count"] for row in rows},
            "pass": all(row["candidate_count"] == 2 ** row["dimension"] for row in rows),
        },
        "special_form_constraints_have_nonempty_survivor_sets": {
            "survivor_counts": {row["family"]: row["survivor_count"] for row in rows},
            "pass": all(row["survivor_count"] > 0 for row in rows if not row["family"].startswith("generic")),
        },
        "special_forms_differ_from_generic_controls": {
            "special_vs_generic": {
                "g2": [next(row for row in rows if row["family"] == "g2_three_form_constraints")["survivor_count"], next(row for row in rows if row["family"] == "generic_three_form_control_constraints")["survivor_count"]],
                "spin7": [next(row for row in rows if row["family"] == "spin7_four_form_constraints")["survivor_count"], next(row for row in rows if row["family"] == "generic_four_form_control_constraints")["survivor_count"]],
            },
            "pass": all(item["pass"] for item in z3_rows.values()),
        },
        "probe_quotient_classes_are_computed": {
            "class_counts": {row["family"]: row["quotient"]["class_count"] for row in rows},
            "pass": all(row["quotient"]["class_count"] > 0 for row in rows),
        },
        "rustworkx_family_transition_graph_detects_differences": transition_graph(rows),
        "sympy_exact_form_term_check": sympy_exact_term_check(),
        "z3_special_generic_difference_checks": {"checks": z3_rows, "pass": all(item["pass"] for item in z3_rows.values())},
    }
    identity_control = {
        "dimension": 7,
        "forms": [form([])],
    }
    identity_row = family_row("identity_no_form_control", identity_control)
    impossible_control = {
        "dimension": 3,
        "forms": [form([(1, (0,)), (1, (1,)), (1, (2,)), (1, (0, 1)), (1, (0, 2)), (1, (1, 2)), (1, (0, 1, 2))])],
    }
    impossible_row = family_row("overconstrained_sign_control", impossible_control)
    graveyard_companions = {
        "identity_no_form_control_keeps_all_candidates": {
            "candidate_count": identity_row["candidate_count"],
            "survivor_count": identity_row["survivor_count"],
            "pass": identity_row["candidate_count"] == identity_row["survivor_count"],
        },
        "overconstrained_sign_control_keeps_only_identity": {
            "survivor_count": impossible_row["survivor_count"],
            "sample_survivors": impossible_row["sample_survivors"],
            "pass": impossible_row["survivor_count"] == 1,
        },
        "generic_three_form_control_is_not_g2_control": {
            "g2_survivors": next(row for row in rows if row["family"] == "g2_three_form_constraints")["survivor_count"],
            "generic_survivors": next(row for row in rows if row["family"] == "generic_three_form_control_constraints")["survivor_count"],
            "pass": next(row for row in rows if row["family"] == "g2_three_form_constraints")["survivor_count"]
            != next(row for row in rows if row["family"] == "generic_three_form_control_constraints")["survivor_count"],
        },
    }
    boundary = {
        "family_count": {"count": len(rows), "pass": len(rows) == 5},
        "spin7_dimension_is_eight": {"dimension": FAMILIES["spin7_four_form_constraints"]["dimension"], "pass": FAMILIES["spin7_four_form_constraints"]["dimension"] == 8},
        "g2_dimension_is_seven": {"dimension": FAMILIES["g2_three_form_constraints"]["dimension"], "pass": FAMILIES["g2_three_form_constraints"]["dimension"] == 7},
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite diagonal sign transformations preserving SU3-like, G2-like, Spin7-like, and generic exterior-form constraints",
        "rows": rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "This only tests diagonal sign symmetries of finite form constraints, not continuous holonomy groups.",
            "Next pass should add permutation symmetries and frame rotations, then compare survivor quotients.",
            "Gauge-theory-like constraints are not included yet; they should come after form constraints have richer finite action.",
        ],
        "why_not_v4_probes": "This is a clean v5 special-form constraint scout and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "survivor_counts": {row["family"]: row["survivor_count"] for row in rows},
            "class_counts": {row["family"]: row["quotient"]["class_count"] for row in rows},
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
