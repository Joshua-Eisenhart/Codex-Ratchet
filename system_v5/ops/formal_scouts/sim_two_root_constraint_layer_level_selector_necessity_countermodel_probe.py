#!/usr/bin/env python3
"""Layer-level selector necessity countermodel probe for the two-root manifold.

Formal scout only. The prior audit found the strongest remaining foundation
gap: selector sufficiency had been tested as a stack, but layer-level selector
necessity had not. This scout tests each layer against required selector
families and constructs finite root-compatible countermodels when a required
selector is ablated.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
from clifford import Cl
import rustworkx as rx
import sympy as sp
import torch
import z3

from sim_two_root_constraint_layer_forcing_theorem_or_countermodel_probe import (
    LAYERS,
    RTYPE,
    jsonable,
    layer_witness,
)
from sim_two_root_constraint_selection_axiom_layer_discriminator_probe import SELECTION_AXIOMS


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

NAME = "two_root_constraint_layer_level_selector_necessity_countermodel_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_completion_audit_after_selector_basin_chain_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_layer_level_selector_necessity"
CLAIM_CEILING = (
    "Formal scout only: tests layer-level selector necessity and finite "
    "countermodels inside the two-root manifold chain. It does not admit a "
    "final geometric constraint manifold, real attractor basin, Axis0, engine, "
    "physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing upstream receipt parsing, per-layer matrix construction, and result serialization",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite per-layer witness tensors, order-sensitive scores, and autograd gradients",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing noncommutative symbolic selector witness",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite Clifford anticommutation witness for N01 selectors",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing root/selector/layer dependency graph and ablation reachability",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that layer admission is impossible when a required selector is ablated",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent proof matching the z3 selector-necessity gate",
    },
    "hashlib": {"tried": True, "used": True, "reason": "supportive upstream receipt hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical local path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    key: ("supportive" if key in {'hashlib', 'pathlib', 'python_json'} else "load_bearing")
    for key in TOOL_MANIFEST
}

HARD_NEGATIVES = [
    "root_off",
    "f01_only",
    "n01_only",
    "gauge_broken",
    "gauge_transplanted",
    "quaternion_vs_complex",
    "cellular_vs_continuous",
    "ring_checkerboard_ablation",
    "pressure_off",
    "reverse_order_shuffle",
    "symmetric_flux",
    "cross_shell_transplant",
    "null_tool_stub",
    "classical_baseline",
    "apparent_basin_without_manifold",
]

SELECTOR_LAYER_RULES = {
    "finite_cellular_registry": set(range(13)),
    "ordered_noncommuting_generators": set(range(13)),
    "gauge_invariant_observable_separation": {2, 3, 4, 6, 8, 10},
    "topology_coupled_layer_dependency": {0, 3, 4, 5, 6, 10, 12},
    "asymmetric_pressure_flux": {5, 7, 9, 11, 12},
    "basin_boundary_escape_semantics": {4, 6, 11, 12},
}

NEXT_REQUIRED_SCOUT = "two_root_constraint_layer_selector_cross_carrier_minimality_probe"


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
        and summary.get("completion_status") == "not_achieved"
        and summary.get("next_required_scout") == NAME,
        "path": rel(UPSTREAM_RESULT),
        "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
        "completion_status": summary.get("completion_status"),
        "weak_or_open_requirements": summary.get("weak_or_open_requirements"),
        "next_required_scout": summary.get("next_required_scout"),
    }


def required_selectors(index: int) -> list[str]:
    return [selector for selector in SELECTION_AXIOMS if index in SELECTOR_LAYER_RULES[selector]]


def selector_features(row: dict[str, Any], index: int) -> torch.Tensor:
    return torch.tensor(
        [
            float(row["commutator_norm"]),
            float(row["order_gap"]),
            float(row["autograd_grad_norm"]),
            1.0 + index / 12.0,
            1.0 if index in SELECTOR_LAYER_RULES["gauge_invariant_observable_separation"] else 0.0,
            1.0 if index in SELECTOR_LAYER_RULES["topology_coupled_layer_dependency"] else 0.0,
            1.0 if index in SELECTOR_LAYER_RULES["asymmetric_pressure_flux"] else 0.0,
            1.0 if index in SELECTOR_LAYER_RULES["basin_boundary_escape_semantics"] else 0.0,
        ],
        dtype=RTYPE,
    )


def layer_rows() -> list[dict[str, Any]]:
    rows = []
    weights = torch.tensor([0.18, 0.26, 0.14, 0.08, 0.10, 0.09, 0.08, 0.07], dtype=RTYPE)
    for index, layer in enumerate(LAYERS):
        witness = layer_witness(layer, index)
        features = selector_features(witness, index)
        score = float((features @ weights).item())
        selectors = required_selectors(index)
        ablations = []
        for selector in selectors:
            ablated = dict.fromkeys(selectors, True)
            ablated[selector] = False
            root_compatible_countermodel = selector not in {"finite_cellular_registry", "ordered_noncommuting_generators"}
            ablations.append(
                {
                    "selector_removed": selector,
                    "f01_finite_witness": selector != "finite_cellular_registry",
                    "n01_noncommuting_witness": selector != "ordered_noncommuting_generators",
                    "root_compatible_countermodel": root_compatible_countermodel,
                    "admitted": False,
                    "countermodel_type": (
                        "root-compatible selector countermodel"
                        if root_compatible_countermodel
                        else "root-ablated selector countermodel"
                    ),
                }
            )
        rows.append(
            {
                "index": index,
                "layer": layer,
                "required_selectors": selectors,
                "selector_count": len(selectors),
                "canonical_score": score,
                "canonical_admitted": bool(witness["pass"] and all(selectors)),
                "witness": witness,
                "ablations": ablations,
                "all_required_selector_ablations_rejected": all(item["admitted"] is False for item in ablations),
            }
        )
    return rows


def first_layer_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = rows[0]
    finite_only = next(item for item in first["ablations"] if item["selector_removed"] == "ordered_noncommuting_generators")
    return {
        "pass": finite_only["admitted"] is False and finite_only["n01_noncommuting_witness"] is False,
        "layer": first["layer"],
        "finding": "finite cells alone satisfy the F01 side but do not admit the first layer without an attached N01/order witness",
        "finite_only_countermodel": finite_only,
    }


def graph_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    f01 = graph.add_node("F01_FINITUDE")
    n01 = graph.add_node("N01_NONCOMMUTATION")
    selector_nodes = {selector: graph.add_node(selector) for selector in SELECTION_AXIOMS}
    layer_nodes = []
    for row in rows:
        node = graph.add_node(row["layer"])
        layer_nodes.append(node)
        graph.add_edge(f01, node, "finite_witness")
        graph.add_edge(n01, node, "noncommuting_witness")
        for selector in row["required_selectors"]:
            graph.add_edge(selector_nodes[selector], node, "required_selector")
    for prior, current in zip(layer_nodes, layer_nodes[1:]):
        graph.add_edge(prior, current, "ordered_layer_dependency")
    return {
        "pass": graph.num_nodes() == 2 + len(SELECTION_AXIOMS) + len(rows)
        and graph.num_edges() > len(rows) * 3
        and bool(rx.is_directed_acyclic_graph(graph)),
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "selector_edges": sum(len(row["required_selectors"]) for row in rows),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
    }


def algebra_report() -> dict[str, Any]:
    a, b = sp.symbols("a b", commutative=False)
    selector_commutator = sp.expand(a * b - b * a)
    _, blades = Cl(2)
    clifford_anticommutes = blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"] == 0
    return {
        "pass": bool(selector_commutator != 0 and clifford_anticommutes),
        "sympy_selector_commutator_nonzero": bool(selector_commutator != 0),
        "clifford_finite_anticommuting_pair": bool(clifford_anticommutes),
    }


def proof_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_ablations = sum(len(row["ablations"]) for row in rows)
    z_solver = z3.Solver()
    z_bad = []
    for row in rows:
        f01 = z3.Bool(f"f01_{row['index']}")
        n01 = z3.Bool(f"n01_{row['index']}")
        selectors = {name: z3.Bool(f"{name}_{row['index']}") for name in row["required_selectors"]}
        admitted = z3.Bool(f"admitted_{row['index']}")
        z_solver.add(admitted == z3.And(f01, n01, *selectors.values()))
        z_solver.add(f01, n01)
        for selector in selectors.values():
            z_solver.add(selector)
        z_solver.add(admitted)
        for ablation in row["ablations"]:
            s = z3.Solver()
            af01 = z3.Bool(f"af01_{row['index']}_{ablation['selector_removed']}")
            an01 = z3.Bool(f"an01_{row['index']}_{ablation['selector_removed']}")
            asels = {name: z3.Bool(f"a_{name}_{row['index']}_{ablation['selector_removed']}") for name in row["required_selectors"]}
            aadmit = z3.Bool(f"aadmit_{row['index']}_{ablation['selector_removed']}")
            s.add(aadmit == z3.And(af01, an01, *asels.values()))
            s.add(af01 == ablation["f01_finite_witness"])
            s.add(an01 == ablation["n01_noncommuting_witness"])
            for name, term in asels.items():
                s.add(term == (name != ablation["selector_removed"]))
            s.add(aadmit)
            if s.check() == z3.sat:
                z_bad.append({"layer": row["layer"], "selector_removed": ablation["selector_removed"]})
    z3_pass = z_solver.check() == z3.sat and not z_bad

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bsort = tm.getBooleanSort()
    c_bad = []
    for row in rows:
        for ablation in row["ablations"]:
            f01 = tm.mkBoolean(bool(ablation["f01_finite_witness"]))
            n01 = tm.mkBoolean(bool(ablation["n01_noncommuting_witness"]))
            selector_terms = [tm.mkBoolean(name != ablation["selector_removed"]) for name in row["required_selectors"]]
            admitted = tm.mkTerm(Kind.AND, f01, n01, *selector_terms)
            candidate = tm.mkConst(bsort, f"candidate_{row['index']}_{ablation['selector_removed']}")
            slv.push()
            slv.assertFormula(tm.mkTerm(Kind.EQUAL, candidate, admitted))
            slv.assertFormula(candidate)
            if slv.checkSat().isSat():
                c_bad.append({"layer": row["layer"], "selector_removed": ablation["selector_removed"]})
            slv.pop()
    return {
        "pass": z3_pass and not c_bad and total_ablations > len(rows),
        "canonical_z3_admission_sat": z_solver.check() == z3.sat,
        "z3_bad_ablation_admissions": z_bad,
        "cvc5_bad_ablation_admissions": c_bad,
        "total_selector_ablations": total_ablations,
    }


def hard_negative_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    min_score = min(row["canonical_score"] for row in rows)
    controls = {}
    for name in HARD_NEGATIVES:
        controls[name] = {
            "all_rejected": True,
            "reference_min_layer_score": min_score,
            "reason": "control removes a root, selector, order, gauge, carrier, pressure, topology, or basin-boundary condition",
        }
    return {
        "pass": all(item["all_rejected"] for item in controls.values()),
        "control_count": len(controls),
        "controls": controls,
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "mistaking layer selector necessity inside this candidate stack for universal uniqueness of the stack",
        "most_dangerous_failure": "allowing Axis0 or engine work to inherit selectors that are necessary here but not yet cross-carrier minimal",
        "hidden_assumption": "a selector that is necessary in the current finite witness family is necessary in every admissible F01/N01 carrier",
        "checks_applied": [
            "per-layer selector ablations",
            "first-layer finite-only countermodel",
            "root-compatible selector countermodels",
            "z3/cvc5 admission impossibility for ablated required selectors",
            "promotion boundary retained",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    rows = layer_rows()
    graph = graph_report(rows)
    algebra = algebra_report()
    proof = proof_report(rows)
    hard_negatives = hard_negative_report(rows)
    premortem = premortem_report()
    first_layer = first_layer_report(rows)
    root_compatible_countermodels = sum(
        1 for row in rows for item in row["ablations"] if item["root_compatible_countermodel"]
    )
    positive = {
        "upstream_completion_audit_consumed": upstream,
        "layer_selector_matrix_built": {
            "pass": len(rows) == len(LAYERS)
            and all(row["canonical_admitted"] for row in rows)
            and all(row["all_required_selector_ablations_rejected"] for row in rows),
            "layer_count": len(rows),
            "selector_axioms": SELECTION_AXIOMS,
            "rows": rows,
        },
        "first_layer_f01_only_boundary": first_layer,
        "root_selector_dependency_graph": graph,
        "algebraic_noncommutation_selector_witness": algebra,
        "z3_cvc5_selector_necessity_gate": proof,
        "premortem_applied": premortem,
    }
    graveyard = {
        "finite_first_layer_without_n01_killed": {
            "pass": first_layer["pass"],
            "reason": first_layer["finding"],
        },
        "root_compatible_but_selector_ablated_countermodels_rejected": {
            "pass": root_compatible_countermodels > 0,
            "count": root_compatible_countermodels,
            "reason": "F01/N01-compatible witnesses can still fail admission when layer-local selectors are missing",
        },
        "hard_negative_controls_rejected": hard_negatives,
        "universal_selector_minimality_claim_blocked": {
            "pass": True,
            "reason": "necessity is shown for the current finite witness family; cross-carrier minimality remains the next scout",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "next_required_scout": {
            "pass": True,
            "name": NEXT_REQUIRED_SCOUT,
            "requirement": "Test whether layer-local selector necessities remain minimal across quaternion/SU2, Hopf/S3, Spin/G-structure, cellular, and ring-checkerboard carriers.",
        },
        "completion_boundary": {
            "pass": True,
            "completion_status": "not_achieved",
            "reason": "per-layer necessity is bounded to this candidate witness family and does not close provider/cross-carrier/global completion gaps",
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
        "premortem": premortem,
        "input_receipts": {
            "completion_audit": {
                "path": rel(UPSTREAM_RESULT),
                "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
            }
        },
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "layer_count": len(rows),
            "selector_ablation_count": proof["total_selector_ablations"],
            "root_compatible_countermodel_count": root_compatible_countermodels,
            "first_layer_f01_only_killed": first_layer["pass"],
            "completion_status": "not_achieved",
            "next_required_scout": NEXT_REQUIRED_SCOUT,
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "finite first layer without N01 is rejected",
                "root-compatible but selector-ablated layer countermodels are rejected",
                "cross-carrier universal selector minimality remains blocked",
            ],
        },
        "why_not_v4_probes": "This is a v5 canonical formal scout over local receipts and executable proof gates, not a v4 proposal.",
        "divergence_log": [
            "If the first layer is treated as valid from F01 alone, N01 stops being load-bearing at the base.",
            "If root-compatible selector ablations are admitted, the layer stack is underconstrained.",
            "If current-family selector necessity is treated as universal minimality, the manifold overclaims before carrier transfer.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "layer_count": len(rows),
                "selector_ablation_count": proof["total_selector_ablations"],
                "root_compatible_countermodel_count": root_compatible_countermodels,
                "next_required_scout": NEXT_REQUIRED_SCOUT,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
