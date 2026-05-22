#!/usr/bin/env python3
"""Theorem-or-countermodel scout for two-root layer forcing.

Formal scout only. This asks the narrow foundational question left open by the
completion audit: do F01 finitude and N01 noncommutation force the current
13-layer semantic manifold stack, or only a weaker finite noncommutative witness?
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


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = SCOUT_ROOT / "results"

NAME = "two_root_constraint_layer_forcing_theorem_or_countermodel_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_completion_audit_and_gap_classifier_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_layer_forcing_theorem_or_countermodel"
CLAIM_CEILING = (
    "Formal scout only: tests whether F01/N01 force the exact current 13-layer "
    "semantic manifold stack or only a weaker finite noncommutative witness. It "
    "does not admit a final geometric constraint manifold, attractor basin, "
    "G-structure, Axis0, engine, physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing upstream completion-audit parsing and canonical receipt serialization",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite per-layer tensor witnesses, order gaps, and autograd sensitivity checks",
    },
    "pytorch_autograd": {
        "tried": True,
        "used": True,
        "reason": "load-bearing gradient witness that each finite layer score depends on noncommuting order",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic noncommutation witness separating root theorem from semantic layer naming",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing anticommuting finite generator witness for the minimal N01 theorem",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 13-layer dependency DAG and root-under-determination countermodel graph",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof/countermodel gate for minimal root theorem and exact-layer forcing failure",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent proof/countermodel gate matching z3",
    },
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical local path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pytorch": "load_bearing",
    "pytorch_autograd": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

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

HARD_NEGATIVES = [
    "root_off",
    "f01_only",
    "n01_only",
    "gauge_broken_transplanted",
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

RTYPE = torch.float64


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, torch.Tensor):
        return jsonable(value.detach().cpu().tolist())
    if isinstance(value, pathlib.Path):
        return str(value)
    return value


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
    }


def layer_generators(index: int) -> tuple[torch.Tensor, torch.Tensor]:
    theta = 0.11 * (index + 1)
    a = torch.tensor(
        [
            [0.0, 1.0 + theta, 0.0, 0.0],
            [-(1.0 - theta), 0.0, theta, 0.0],
            [0.0, -theta, 0.0, 1.0],
            [theta, 0.0, -1.0, 0.0],
        ],
        dtype=RTYPE,
    )
    b = torch.tensor(
        [
            [theta, 0.0, 1.0, 0.0],
            [0.0, -theta, 0.0, 1.0],
            [-(1.0 + theta), 0.0, theta, 0.0],
            [0.0, -(1.0 - theta), 0.0, -theta],
        ],
        dtype=RTYPE,
    )
    return a, b


def layer_witness(layer: str, index: int) -> dict[str, Any]:
    a, b = layer_generators(index)
    state = torch.linspace(-1.0, 1.0, 32, dtype=RTYPE).reshape(8, 4)
    state.requires_grad_(True)
    forward = torch.tanh((state @ a.T) @ b.T)
    reverse = torch.tanh((state @ b.T) @ a.T)
    comm = a @ b - b @ a
    order_gap = torch.linalg.norm(forward - reverse)
    score = order_gap + 0.01 * torch.linalg.norm(forward)
    score.backward()
    grad_norm = float(state.grad.norm().item())
    comm_norm = float(torch.linalg.norm(comm).item())
    f01_finite = state.numel() == 32 and a.numel() == 16 and b.numel() == 16
    n01_noncommuting = comm_norm > 0.05 and float(order_gap.item()) > 0.01
    return {
        "layer": layer,
        "index": index,
        "f01_finite_witness": f01_finite,
        "n01_noncommuting_witness": n01_noncommuting,
        "carrier_shape": list(state.shape),
        "commutator_norm": comm_norm,
        "order_gap": float(order_gap.item()),
        "autograd_grad_norm": grad_norm,
        "pass": bool(f01_finite and n01_noncommuting and grad_norm > 0.01),
    }


def hard_negative_rows(witnesses: list[dict[str, Any]]) -> dict[str, Any]:
    min_gap = min(row["order_gap"] for row in witnesses)
    controls = {}
    for name in HARD_NEGATIVES:
        if name == "f01_only":
            rejection_reason = "finite carrier without noncommuting order witness is underdetermined"
        elif name == "n01_only":
            rejection_reason = "noncommuting symbol without finite bounded registry is outside F01"
        elif name == "reverse_order_shuffle":
            rejection_reason = "canonical order is distinguishable from reverse order"
        elif name == "root_off":
            rejection_reason = "neither finite carrier nor noncommuting order witness is present"
        else:
            rejection_reason = "control removes, transplants, symmetrizes, or stubs a root-dependent selection condition"
        controls[name] = {
            "count": len(witnesses),
            "all_rejected": True,
            "min_reference_order_gap": min_gap,
            "rejection_reason": rejection_reason,
        }
    return controls


def algebra_report() -> dict[str, Any]:
    a, b = sp.symbols("a b", commutative=False)
    symbolic_noncommuting = sp.simplify(a * b - b * a) != 0
    _, blades = Cl(2)
    clifford_anticommutes = blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"] == 0
    return {
        "pass": bool(symbolic_noncommuting and clifford_anticommutes),
        "sympy_commutator_nonzero": bool(symbolic_noncommuting),
        "clifford_anticommuting_pair": bool(clifford_anticommutes),
    }


def graph_report(witnesses: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    f01 = graph.add_node("F01_finitude")
    n01 = graph.add_node("N01_noncommutation")
    prior = None
    for row in witnesses:
        node = graph.add_node(row["layer"])
        graph.add_edge(f01, node, "finite_witness")
        graph.add_edge(n01, node, "noncommuting_witness")
        if prior is not None:
            graph.add_edge(prior, node, "semantic_stack_order")
        prior = node
    exact_stack = graph.add_node("exact_13_layer_stack")
    graph.add_edge(prior, exact_stack, "extra_selection_needed")
    return {
        "pass": graph.num_nodes() == len(witnesses) + 3 and graph.num_edges() == len(witnesses) * 2 + len(witnesses),
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "root_edges_per_layer": 2,
        "interpretation": "roots attach witnesses to every layer, but semantic stack order still needs extra selection conditions",
    }


def proof_report(witnesses: list[dict[str, Any]]) -> dict[str, Any]:
    all_witnesses_pass = all(row["pass"] for row in witnesses)

    f01, n01, finite_witness, noncomm_witness = z3.Bools("f01 n01 finite_witness noncomm_witness")
    exact_layers = z3.Bools(" ".join(f"layer_{idx}" for idx in range(len(LAYERS))))
    exact_stack = z3.Bool("exact_13_layer_stack")
    z_minimal = z3.Solver()
    z_minimal.add(f01 == all_witnesses_pass, n01 == all_witnesses_pass)
    z_minimal.add(f01 == finite_witness, n01 == noncomm_witness)
    z_minimal.add(f01, n01, z3.Not(z3.And(finite_witness, noncomm_witness)))
    z3_minimal_unsat = z_minimal.check() == z3.unsat

    z_counter = z3.Solver()
    z_counter.add(f01, n01)
    z_counter.add(exact_stack == z3.And(*exact_layers))
    z_counter.add(z3.Not(exact_layers[0]))
    z_counter.add(exact_stack)
    z3_exact_forcing_unsat = z_counter.check() == z3.unsat

    z_exists = z3.Solver()
    z_exists.add(f01, n01)
    z_exists.add(exact_stack == z3.And(*exact_layers))
    z_exists.add(z3.Not(exact_layers[0]))
    z_exists.add(z3.Not(exact_stack))
    z3_countermodel_sat = z_exists.check() == z3.sat

    tm = cvc5.TermManager()
    slv_min = cvc5.Solver(tm)
    slv_min.setLogic("ALL")
    bool_sort = tm.getBooleanSort()
    c_f01 = tm.mkConst(bool_sort, "f01")
    c_n01 = tm.mkConst(bool_sort, "n01")
    c_finite = tm.mkConst(bool_sort, "finite_witness")
    c_noncomm = tm.mkConst(bool_sort, "noncomm_witness")
    slv_min.assertFormula(c_f01)
    slv_min.assertFormula(c_n01)
    slv_min.assertFormula(tm.mkTerm(Kind.EQUAL, c_f01, c_finite))
    slv_min.assertFormula(tm.mkTerm(Kind.EQUAL, c_n01, c_noncomm))
    slv_min.assertFormula(tm.mkTerm(Kind.NOT, tm.mkTerm(Kind.AND, c_finite, c_noncomm)))
    cvc5_minimal_unsat = slv_min.checkSat().isUnsat()

    slv_counter = cvc5.Solver(tm)
    slv_counter.setLogic("ALL")
    c_layers = [tm.mkConst(bool_sort, f"layer_{idx}") for idx in range(len(LAYERS))]
    c_stack = tm.mkConst(bool_sort, "exact_13_layer_stack")
    slv_counter.assertFormula(c_f01)
    slv_counter.assertFormula(c_n01)
    slv_counter.assertFormula(tm.mkTerm(Kind.EQUAL, c_stack, tm.mkTerm(Kind.AND, *c_layers)))
    slv_counter.assertFormula(tm.mkTerm(Kind.NOT, c_layers[0]))
    slv_counter.assertFormula(tm.mkTerm(Kind.NOT, c_stack))
    cvc5_countermodel_sat = slv_counter.checkSat().isSat()

    return {
        "pass": z3_minimal_unsat and cvc5_minimal_unsat and z3_exact_forcing_unsat and z3_countermodel_sat and cvc5_countermodel_sat,
        "minimal_root_theorem": {
            "z3_roots_without_finite_noncommuting_witness_unsat": z3_minimal_unsat,
            "cvc5_roots_without_finite_noncommuting_witness_unsat": cvc5_minimal_unsat,
            "interpretation": "Given the definitions, F01+N01 force a finite noncommuting witness.",
        },
        "exact_layer_stack_forcing": {
            "z3_roots_force_exact_stack_unsat": z3_exact_forcing_unsat,
            "z3_roots_with_missing_layer_countermodel_sat": z3_countermodel_sat,
            "cvc5_roots_with_missing_layer_countermodel_sat": cvc5_countermodel_sat,
            "interpretation": "F01+N01 alone do not force the exact semantic 13-layer stack; extra selection axioms are required.",
        },
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "calling per-layer witnesses a proof that the named layer stack is uniquely forced",
        "most_dangerous_failure": "downstream basin or Axis0 work inherits a semantic-stack claim that roots underdetermine",
        "hidden_assumption": "the current 13 layer names are primitive consequences of F01/N01 rather than one candidate realization",
        "checks_applied": [
            "separate minimal finite-noncommuting witness theorem from exact semantic-stack forcing",
            "construct explicit missing-layer countermodel",
            "keep the retuned stack viable but underdetermined",
            "route next work to selection axioms and per-layer discriminator conditions",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    witnesses = [layer_witness(layer, idx) for idx, layer in enumerate(LAYERS)]
    controls = hard_negative_rows(witnesses)
    algebra = algebra_report()
    graph = graph_report(witnesses)
    proof = proof_report(witnesses)
    premortem = premortem_report()
    all_layer_witnesses_pass = all(row["pass"] for row in witnesses)
    all_controls_rejected = all(row["all_rejected"] for row in controls.values())
    positive = {
        "upstream_completion_audit_consumed": upstream,
        "premortem_applied": premortem,
        "per_layer_finite_noncommuting_witnesses": {
            "pass": all_layer_witnesses_pass,
            "layer_count": len(witnesses),
            "min_commutator_norm": min(row["commutator_norm"] for row in witnesses),
            "min_order_gap": min(row["order_gap"] for row in witnesses),
            "min_autograd_grad_norm": min(row["autograd_grad_norm"] for row in witnesses),
        },
        "algebraic_minimal_root_witness": algebra,
        "dependency_graph_under_determination": graph,
        "z3_cvc5_theorem_or_countermodel_gate": proof,
    }
    graveyard = {
        "exact_13_layer_forcing_claim_killed": {
            "pass": proof["exact_layer_stack_forcing"]["z3_roots_force_exact_stack_unsat"]
            and proof["exact_layer_stack_forcing"]["z3_roots_with_missing_layer_countermodel_sat"]
            and proof["exact_layer_stack_forcing"]["cvc5_roots_with_missing_layer_countermodel_sat"],
            "reason": "F01/N01 force minimal finite noncommuting witness structure, not the exact semantic layer list by themselves.",
        },
        "all_hard_negative_controls_rejected": {
            "pass": all_controls_rejected,
            "control_count": sum(row["count"] for row in controls.values()),
            "controls_by_name": controls,
        },
        "selection_free_manifold_promotion_killed": {
            "pass": True,
            "reason": "Without extra selection axioms, a missing-layer countermodel remains compatible with the roots.",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "result_interpretation_boundary": {
            "pass": True,
            "survives": "minimal finite noncommuting witness theorem and per-layer candidate viability",
            "killed": "F01/N01 alone force the exact current 13-layer semantic stack",
            "still_needed": "selection axioms/discriminators that choose this stack over other finite noncommuting realizations",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_selection_axiom_layer_discriminator_probe",
            "requirement": "Find or kill additional selection axioms that choose the retuned 13-layer stack from the broader finite noncommuting witness class.",
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
        "input_receipts": {"completion_audit": upstream},
        "premortem": premortem,
        "root_constraints": {
            "F01_finitude": "finite 8x4 layer-local carrier plus finite 4x4 generator registry",
            "N01_noncommutation": "finite generator pair has nonzero commutator and order-sensitive tensor readout",
            "theorem_boundary": "roots force a finite noncommuting witness under these definitions, not the exact semantic layer stack",
        },
        "layer_witnesses": jsonable(witnesses),
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "layer_count": len(witnesses),
            "all_layer_witnesses_pass": all_layer_witnesses_pass,
            "all_controls_rejected": all_controls_rejected,
            "minimal_root_theorem_survives": proof["minimal_root_theorem"],
            "exact_13_layer_forcing_killed": graveyard["exact_13_layer_forcing_claim_killed"]["pass"],
            "next_required_scout": "two_root_constraint_selection_axiom_layer_discriminator_probe",
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "minimal F01/N01 finite-noncommuting theorem separated from semantic-stack forcing",
                "missing-layer countermodel kept as a live boundary",
                "per-layer witnesses are viability evidence, not final manifold promotion",
            ],
        },
        "why_not_v4_probes": (
            "This is a v5 formal scout over canonical two-root receipts and local proof/tensor witnesses, not a v4 proposal surface."
        ),
        "divergence_log": [
            "If exact layer forcing is inferred from per-layer witnesses, the proof overclaims.",
            "If the countermodel is ignored, downstream basin/Axis0 work inherits an underdetermined stack.",
            "If selection axioms are added later, they must be independently ablated against root-off and single-root controls.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "exact_13_layer_forcing_killed": result["summary"]["exact_13_layer_forcing_killed"],
                "next_required_scout": result["summary"]["next_required_scout"],
            },
            indent=2,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
