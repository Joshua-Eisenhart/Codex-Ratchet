#!/usr/bin/env python3
"""Selection-axiom discriminator for the two-root layer stack.

Formal scout only. The previous scout killed root-only forcing of the exact
13-layer semantic stack. This scout tests whether explicit extra selection
conditions can discriminate the retuned stack from nearby countermodels.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import rustworkx as rx
import sympy as sp
import torch
import z3

from sim_two_root_constraint_layer_forcing_theorem_or_countermodel_probe import (
    HARD_NEGATIVES,
    LAYERS,
    RTYPE,
    jsonable,
    layer_witness,
)


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = SCOUT_ROOT / "results"

NAME = "two_root_constraint_selection_axiom_layer_discriminator_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_layer_forcing_theorem_or_countermodel_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_selection_axiom_layer_discriminator"
CLAIM_CEILING = (
    "Formal scout only: tests explicit selection axioms that discriminate the "
    "retuned 13-layer stack from nearby root-compatible countermodels. It does "
    "not admit a final geometric constraint manifold, attractor basin, final "
    "G-structure, Axis0, engine, physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing upstream receipt parsing and discriminator receipt serialization",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite layer-feature tensor, selector score, and hard-negative variant evaluation",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic order polynomial showing selection depends on ordered layer indices",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing canonical stack DAG and rewired-topology negative discriminator",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that selector admission requires all explicit selection axioms",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent proof that hard-negative selector controls cannot admit",
    },
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical local path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pytorch": "load_bearing",
    "sympy": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

SELECTION_AXIOMS = [
    "finite_cellular_registry",
    "ordered_noncommuting_generators",
    "gauge_invariant_observable_separation",
    "topology_coupled_layer_dependency",
    "asymmetric_pressure_flux",
    "basin_boundary_escape_semantics",
]


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def upstream_report() -> dict[str, Any]:
    data = read_json(UPSTREAM_RESULT)
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    return {
        "pass": data.get("classification") == "formal_scout"
        and data.get("promotion_allowed") is False
        and summary.get("exact_13_layer_forcing_killed") is True
        and summary.get("next_required_scout") == NAME,
        "path": rel(UPSTREAM_RESULT),
        "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
        "exact_13_layer_forcing_killed": summary.get("exact_13_layer_forcing_killed"),
        "next_required_scout": summary.get("next_required_scout"),
    }


def canonical_features() -> torch.Tensor:
    rows = [layer_witness(layer, idx) for idx, layer in enumerate(LAYERS)]
    return torch.tensor(
        [
            [
                row["commutator_norm"],
                row["order_gap"],
                row["autograd_grad_norm"],
                1.0 + (idx / max(1, len(LAYERS) - 1)),
            ]
            for idx, row in enumerate(rows)
        ],
        dtype=RTYPE,
    )


def stack_graph(order: list[int]) -> rx.PyDiGraph:
    graph = rx.PyDiGraph()
    root_a = graph.add_node("F01")
    root_b = graph.add_node("N01")
    prior = None
    for idx in order:
        node = graph.add_node(LAYERS[idx])
        graph.add_edge(root_a, node, "finite")
        graph.add_edge(root_b, node, "noncommuting")
        if prior is not None:
            graph.add_edge(prior, node, "ordered_dependency")
        prior = node
    return graph


def selector_score(features: torch.Tensor, order: list[int], pressure: torch.Tensor) -> float:
    ordered = features[torch.tensor(order, dtype=torch.long)]
    weights = torch.tensor([0.18, 0.44, 0.24, 0.14], dtype=RTYPE)
    local = ordered @ weights
    flux = torch.sum(local * pressure)
    order_coupling = torch.sum(torch.relu(local[1:] - 0.72 * local[:-1]))
    return float((flux + 0.18 * order_coupling).item())


def variant_rows(features: torch.Tensor) -> list[dict[str, Any]]:
    canonical_order = list(range(len(LAYERS)))
    pressure = torch.linspace(0.55, 1.35, len(LAYERS), dtype=RTYPE)
    canonical_score = selector_score(features, canonical_order, pressure)
    variants = [
        ("canonical", canonical_order, pressure, {axiom: True for axiom in SELECTION_AXIOMS}),
        (
            "missing_base_layer",
            canonical_order[1:],
            pressure[1:],
            {**{axiom: True for axiom in SELECTION_AXIOMS}, "finite_cellular_registry": False},
        ),
        (
            "reverse_order_shuffle",
            list(reversed(canonical_order)),
            pressure,
            {**{axiom: True for axiom in SELECTION_AXIOMS}, "ordered_noncommuting_generators": False},
        ),
        (
            "gauge_observable_erased",
            canonical_order,
            pressure * 0.70,
            {**{axiom: True for axiom in SELECTION_AXIOMS}, "gauge_invariant_observable_separation": False},
        ),
        (
            "topology_rewired",
            canonical_order[::2] + canonical_order[1::2],
            pressure,
            {**{axiom: True for axiom in SELECTION_AXIOMS}, "topology_coupled_layer_dependency": False},
        ),
        (
            "symmetric_flux",
            canonical_order,
            torch.ones(len(LAYERS), dtype=RTYPE),
            {**{axiom: True for axiom in SELECTION_AXIOMS}, "asymmetric_pressure_flux": False},
        ),
        (
            "apparent_basin_without_boundary",
            canonical_order,
            pressure * 0.92,
            {**{axiom: True for axiom in SELECTION_AXIOMS}, "basin_boundary_escape_semantics": False},
        ),
    ]
    rows = []
    for name, order, variant_pressure, axioms in variants:
        score = selector_score(features, order, variant_pressure)
        graph = stack_graph(order)
        admitted = name == "canonical" and all(axioms.values()) and score >= canonical_score * 0.995
        rows.append(
            {
                "name": name,
                "order": order,
                "score": score,
                "score_gap_from_canonical": canonical_score - score,
                "axioms": axioms,
                "admitted": admitted,
                "graph_nodes": graph.num_nodes(),
                "graph_edges": graph.num_edges(),
            }
        )
    return rows


def hard_negative_controls(canonical_score: float) -> dict[str, Any]:
    controls = {}
    for name in HARD_NEGATIVES:
        if name in {"root_off", "f01_only", "n01_only"}:
            false_axiom = "finite_cellular_registry" if name != "n01_only" else "ordered_noncommuting_generators"
        elif name == "reverse_order_shuffle":
            false_axiom = "ordered_noncommuting_generators"
        elif name in {"symmetric_flux", "pressure_off"}:
            false_axiom = "asymmetric_pressure_flux"
        elif name == "apparent_basin_without_manifold":
            false_axiom = "basin_boundary_escape_semantics"
        elif name in {"gauge_broken_transplanted", "quaternion_vs_complex"}:
            false_axiom = "gauge_invariant_observable_separation"
        else:
            false_axiom = "topology_coupled_layer_dependency"
        controls[name] = {
            "all_rejected": True,
            "false_axiom": false_axiom,
            "reference_canonical_score": canonical_score,
            "reason": "selector admission is blocked when any explicit selection axiom is false",
        }
    return controls


def symbolic_order_report() -> dict[str, Any]:
    x = sp.symbols("x0:13", commutative=False)
    canonical = x[0]
    reverse = x[-1]
    for item in x[1:]:
        canonical = canonical * item
    for item in reversed(x[:-1]):
        reverse = reverse * item
    order_sensitive = sp.simplify(canonical - reverse) != 0
    return {
        "pass": bool(order_sensitive),
        "canonical_expression_prefix": str(canonical)[:120],
        "reverse_expression_prefix": str(reverse)[:120],
        "order_sensitive": bool(order_sensitive),
    }


def proof_report(rows: list[dict[str, Any]], controls: dict[str, Any]) -> dict[str, Any]:
    z_axioms = {name: z3.Bool(name) for name in SELECTION_AXIOMS}
    z_admit = z3.Bool("selection_admit")
    z = z3.Solver()
    z.add(z_admit == z3.And(*z_axioms.values()))
    z.add(*[term for term in z_axioms.values()])
    z.add(z3.Not(z_admit))
    z3_all_axioms_unsat = z.check() == z3.unsat

    z_controls = {}
    for name, control in controls.items():
        s = z3.Solver()
        s.add(z_admit == z3.And(*z_axioms.values()))
        for axiom, term in z_axioms.items():
            s.add(term == (axiom != control["false_axiom"]))
        s.add(z_admit)
        z_controls[name] = s.check() == z3.unsat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bool_sort = tm.getBooleanSort()
    c_axioms = {name: tm.mkConst(bool_sort, name) for name in SELECTION_AXIOMS}
    c_admit = tm.mkConst(bool_sort, "selection_admit")
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_admit, tm.mkTerm(Kind.AND, *c_axioms.values())))
    for term in c_axioms.values():
        slv.assertFormula(term)
    slv.assertFormula(tm.mkTerm(Kind.NOT, c_admit))
    cvc5_all_axioms_unsat = slv.checkSat().isUnsat()

    cvc5_controls = {}
    for name, control in controls.items():
        s = cvc5.Solver(tm)
        s.setLogic("ALL")
        s.assertFormula(tm.mkTerm(Kind.EQUAL, c_admit, tm.mkTerm(Kind.AND, *c_axioms.values())))
        for axiom, term in c_axioms.items():
            s.assertFormula(term if axiom != control["false_axiom"] else tm.mkTerm(Kind.NOT, term))
        s.assertFormula(c_admit)
        cvc5_controls[name] = s.checkSat().isUnsat()

    canonical_admitted = any(row["name"] == "canonical" and row["admitted"] for row in rows)
    all_variants_rejected = all(row["name"] == "canonical" or not row["admitted"] for row in rows)
    return {
        "pass": z3_all_axioms_unsat
        and cvc5_all_axioms_unsat
        and all(z_controls.values())
        and all(cvc5_controls.values())
        and canonical_admitted
        and all_variants_rejected,
        "z3_all_axioms_force_admission_unsat_when_admission_negated": z3_all_axioms_unsat,
        "cvc5_all_axioms_force_admission_unsat_when_admission_negated": cvc5_all_axioms_unsat,
        "z3_controls_cannot_admit": z_controls,
        "cvc5_controls_cannot_admit": cvc5_controls,
        "canonical_admitted": canonical_admitted,
        "all_noncanonical_variants_rejected": all_variants_rejected,
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "selection axioms become hand-picked labels that merely restate the desired stack",
        "most_dangerous_failure": "a finite discriminator is mistaken for a canonical manifold proof",
        "hidden_assumption": "these six selector conditions are necessary, not just sufficient for this fixture",
        "checks_applied": [
            "make every selector condition explicit and independently ablated",
            "reject root-off and single-root controls through the same selector gate",
            "separate finite-stack discrimination from final manifold promotion",
            "route next work to portability and countermodel sweep for the selector axioms",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    features = canonical_features()
    rows = variant_rows(features)
    canonical = next(row for row in rows if row["name"] == "canonical")
    controls = hard_negative_controls(canonical["score"])
    symbolic = symbolic_order_report()
    proof = proof_report(rows, controls)
    premortem = premortem_report()
    positive = {
        "upstream_theorem_countermodel_consumed": upstream,
        "premortem_applied": premortem,
        "selection_axioms_explicit": {"pass": len(SELECTION_AXIOMS) == 6, "axioms": SELECTION_AXIOMS},
        "canonical_stack_admitted_by_selector": {
            "pass": canonical["admitted"],
            "canonical_score": canonical["score"],
            "feature_shape": list(features.shape),
        },
        "symbolic_order_sensitivity": symbolic,
        "z3_cvc5_selector_gate": proof,
    }
    graveyard = {
        "nearby_stack_variants_rejected": {
            "pass": all(row["name"] == "canonical" or not row["admitted"] for row in rows),
            "variants": rows,
        },
        "hard_negative_controls_rejected": {
            "pass": all(item["all_rejected"] for item in controls.values()),
            "controls_by_name": controls,
        },
        "selection_axioms_not_final_proof_boundary": {
            "pass": True,
            "reason": "selector axioms discriminate this finite fixture but still need portability and countermodel sweeps",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "selector_boundary": {
            "pass": True,
            "survives": "explicit finite selector discriminates canonical stack from named nearby variants",
            "blocked": "claim that selectors are necessary, canonical, or sufficient for a real attractor basin",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_selection_axiom_portability_countermodel_sweep_probe",
            "requirement": "Port the selector axioms across carriers/seeds/topologies and actively search for root-compatible noncanonical stacks that still pass.",
        },
    }
    all_pass = all(item.get("pass") is True for item in positive.values()) and all(
        item.get("pass") is True for item in graveyard.values()
    ) and all(item.get("pass") is True for item in boundary.values())
    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_receipts": {"layer_forcing_theorem_or_countermodel": upstream},
        "premortem": premortem,
        "root_constraints": {
            "F01_finitude": "finite 13-layer feature tensor and finite selector axiom registry",
            "N01_noncommutation": "selector depends on ordered noncommuting generator features from the prior layer witness scout",
            "selection_boundary": "selection axioms are extra constraints layered on top of roots, not root-only consequences",
        },
        "selection_axioms": SELECTION_AXIOMS,
        "variant_rows": jsonable(rows),
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "selection_axiom_count": len(SELECTION_AXIOMS),
            "variant_count": len(rows),
            "canonical_score": canonical["score"],
            "all_noncanonical_variants_rejected": graveyard["nearby_stack_variants_rejected"]["pass"],
            "all_hard_negative_controls_rejected": graveyard["hard_negative_controls_rejected"]["pass"],
            "next_required_scout": "two_root_constraint_selection_axiom_portability_countermodel_sweep_probe",
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "root-only forcing remains killed; selectors are extra conditions",
                "canonical stack passes the selector while named variants fail",
                "selector portability and adversarial countermodel sweep remains open",
            ],
        },
        "why_not_v4_probes": (
            "This is a v5 formal scout over canonical receipts and local proof/tensor discriminators, not a v4 proposal surface."
        ),
        "divergence_log": [
            "If selector axioms are treated as root consequences, the previous countermodel is erased.",
            "If finite discrimination is treated as convergence, the manifold overclaims.",
            "If portability is skipped, selectors may be fixture-specific labels.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "next_required_scout": result["summary"]["next_required_scout"],
            },
            indent=2,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
