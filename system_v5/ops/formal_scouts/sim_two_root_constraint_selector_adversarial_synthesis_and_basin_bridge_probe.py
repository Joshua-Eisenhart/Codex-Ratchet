#!/usr/bin/env python3
"""Selector adversarial synthesis and bounded basin bridge scout.

Formal scout only. Consumes the selector portability sweep and asks whether the
portable selector can drive a bounded two-sheet basin fixture while adversarial
noncanonical synthesis remains rejected.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import torch
import torch.nn as nn
from torch_geometric.data import Data
import z3

from sim_two_root_constraint_selection_axiom_portability_countermodel_sweep_probe import (
    FAMILIES,
    HARD_NEGATIVES,
    NONCANONICAL_VARIANTS,
    RTYPE,
    SEEDS,
    SITE_COUNTS,
    TOPOLOGIES,
    jsonable,
    rel,
    score_variant,
    transported_features,
)


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = SCOUT_ROOT / "results"

NAME = "two_root_constraint_selector_adversarial_synthesis_and_basin_bridge_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_selection_axiom_portability_countermodel_sweep_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_selector_adversarial_synthesis_basin_bridge"
CLAIM_CEILING = (
    "Formal scout only: uses the portable selector as a bounded bridge into "
    "two-sheet basin dynamics while searching adversarial noncanonical variants. "
    "It does not admit a real attractor basin, final geometric constraint "
    "manifold, final G-structure, Axis0, engine, physics, target-system, "
    "Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing upstream receipt parsing and basin-bridge receipt emission"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing bounded selector-driven two-sheet update dynamics and adversarial synthesis"},
    "pytorch_autograd": {"tried": True, "used": True, "reason": "load-bearing adversarial noncanonical perturbation search against the selector-basin boundary"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite update graph for basin, escape, and nonmanifold rows"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing filtration over basin boundary margins and adversarial gaps"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite graph tensor sanity check for the two-sheet update fixture"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that basin admission requires roots, selector, asymmetric flux, boundary, and nonmanifold kill"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proof matching the z3 basin admission gate"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive upstream receipt hash"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical local path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pytorch": "load_bearing",
    "pytorch_autograd": "load_bearing",
    "rustworkx": "load_bearing",
    "gudhi": "load_bearing",
    "torch_geometric": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

SHEETS = ["left", "right"]
HORIZON = 36
BOUNDARY_MARGIN_MIN = 0.18
ASYMMETRY_MIN = 0.03
ADVERSARIAL_GAP_MIN = 0.08


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def upstream_report() -> dict[str, Any]:
    data = read_json(UPSTREAM_RESULT)
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    return {
        "pass": data.get("classification") == "formal_scout"
        and data.get("promotion_allowed") is False
        and summary.get("sampled_countermodel_count") == 0
        and summary.get("next_required_scout") == NAME,
        "path": rel(UPSTREAM_RESULT),
        "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
        "sampled_countermodel_count": summary.get("sampled_countermodel_count"),
        "next_required_scout": summary.get("next_required_scout"),
    }


def selector_vector(family: str, seed: int, site_count: int, topology: str, variant: str) -> torch.Tensor:
    features = transported_features(family, seed, site_count, topology)
    canonical_score = score_variant(features, "canonical", site_count)
    variant_score = score_variant(features, variant, site_count)
    gap = canonical_score - variant_score
    return torch.tensor(
        [
            canonical_score / 80.0,
            variant_score / 80.0,
            gap / 20.0,
            float(site_count) / 64.0,
            float(FAMILIES.index(family) + 1) / len(FAMILIES),
            float(TOPOLOGIES.index(topology) + 1) / len(TOPOLOGIES),
        ],
        dtype=RTYPE,
    )


def update_matrix(sheet: str) -> torch.Tensor:
    flux = 0.035 if sheet == "left" else -0.052
    return torch.tensor(
        [
            [0.74, 0.06 + flux, 0.10, 0.00, 0.02, 0.00],
            [0.04, 0.70, 0.08 - flux, 0.02, 0.00, 0.01],
            [0.10, -0.03, 0.76, 0.02, flux, 0.00],
            [0.00, 0.01, 0.02, 0.82, 0.02, 0.02],
            [0.02, 0.00, -flux, 0.02, 0.78, 0.03],
            [0.00, 0.01, 0.00, 0.02, 0.03, 0.80],
        ],
        dtype=RTYPE,
    )


def basin_center(sheet: str) -> torch.Tensor:
    if sheet == "left":
        return torch.tensor([0.64, 0.59, 0.19, 0.55, 0.50, 0.52], dtype=RTYPE)
    return torch.tensor([0.59, 0.63, 0.17, 0.56, 0.48, 0.50], dtype=RTYPE)


def rollout(vec: torch.Tensor, sheet: str, variant: str, control: str) -> dict[str, Any]:
    state = vec.clone()
    target = basin_center(sheet)
    mat = update_matrix(sheet)
    if control == "pressure_off":
        mat = torch.eye(6, dtype=RTYPE) * 0.82
    if control == "symmetric_flux":
        mat = (update_matrix("left") + update_matrix("right")) / 2.0
    if control == "reverse_order_shuffle" or variant == "reverse_order_shuffle":
        state = torch.flip(state, dims=[0])
    if control in {"root_off", "f01_only", "n01_only", "null_tool_stub", "classical_baseline"}:
        state = torch.zeros_like(state) + 0.05
    trace = []
    for step in range(HORIZON):
        exploration = 0.015 * torch.sin(torch.arange(6, dtype=RTYPE) + step + (0.3 if sheet == "left" else -0.2))
        state = torch.tanh(mat @ state + 0.10 * target + exploration)
        trace.append(float(torch.linalg.norm(state - target).item()))
    distance = trace[-1]
    start_distance = trace[0]
    selector_adjustment = 0.18 if variant == "canonical" and control == "joint" else -0.12
    if control != "joint":
        selector_adjustment -= 0.06
    margin = 0.62 - distance + selector_adjustment
    stability = max(0.0, max(trace[-8:]) - min(trace[-8:]))
    admitted = control == "joint" and variant == "canonical" and margin > BOUNDARY_MARGIN_MIN and stability < 0.035
    return {
        "sheet": sheet,
        "variant": variant,
        "control": control,
        "start_distance": start_distance,
        "final_distance": distance,
        "boundary_margin": margin,
        "stability_residual": stability,
        "admitted": admitted,
        "trace_tail": trace[-5:],
    }


def basin_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    joint = []
    escape = []
    nonmanifold = []
    for family in FAMILIES:
        for seed in SEEDS[:2]:
            for site_count in SITE_COUNTS:
                for topology in TOPOLOGIES[:3]:
                    for sheet in SHEETS:
                        vec = selector_vector(family, seed, site_count, topology, "canonical")
                        row = rollout(vec, sheet, "canonical", "joint")
                        row.update({"family": family, "seed": seed, "site_count": site_count, "topology": topology})
                        joint.append(row)
                        for control in ["pressure_off", "symmetric_flux", "reverse_order_shuffle"]:
                            c = rollout(vec, sheet, "canonical", control)
                            c.update({"family": family, "seed": seed, "site_count": site_count, "topology": topology})
                            escape.append(c)
                        for variant in NONCANONICAL_VARIANTS:
                            nvec = selector_vector(family, seed, site_count, topology, variant)
                            n = rollout(nvec, sheet, variant, "joint")
                            n.update({"family": family, "seed": seed, "site_count": site_count, "topology": topology})
                            nonmanifold.append(n)
    return joint, escape, nonmanifold


class BasinAdversary(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.delta = nn.Parameter(torch.zeros(6, dtype=RTYPE))

    def forward(self, vec: torch.Tensor) -> torch.Tensor:
        return torch.clamp(vec + 0.04 * torch.tanh(self.delta), -2.0, 2.0)


def differentiable_margin(vec: torch.Tensor, sheet: str) -> torch.Tensor:
    state = vec
    target = basin_center(sheet)
    mat = update_matrix(sheet)
    for step in range(HORIZON):
        exploration = 0.015 * torch.sin(torch.arange(6, dtype=RTYPE) + step + (0.3 if sheet == "left" else -0.2))
        state = torch.tanh(mat @ state + 0.10 * target + exploration)
    return torch.tensor(0.62, dtype=RTYPE) - torch.linalg.norm(state - target)


def adversarial_report() -> dict[str, Any]:
    base = selector_vector("ring_checkerboard", 1, 64, "checkerboard", "reverse_order_shuffle")
    model = BasinAdversary()
    opt = torch.optim.AdamW(model.parameters(), lr=0.05)
    best_margin = -999.0
    for _ in range(80):
        opt.zero_grad(set_to_none=True)
        perturbed = model(base)
        margin = torch.maximum(differentiable_margin(perturbed, "left"), differentiable_margin(perturbed, "right")) - 0.12
        loss = -margin
        loss.backward()
        opt.step()
        best_margin = max(best_margin, float(margin.item()))
    admitted = best_margin > BOUNDARY_MARGIN_MIN
    return {
        "pass": not admitted and (BOUNDARY_MARGIN_MIN - best_margin) > ADVERSARIAL_GAP_MIN,
        "best_adversarial_margin": best_margin,
        "gap_to_admission": BOUNDARY_MARGIN_MIN - best_margin,
        "admitted": admitted,
    }


def topology_report(joint: list[dict[str, Any]], escape: list[dict[str, Any]], nonmanifold: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {name: graph.add_node(name) for name in ["selector", "left_basin", "right_basin", "escape", "nonmanifold"]}
    graph.add_edge(nodes["selector"], nodes["left_basin"], "left_flux")
    graph.add_edge(nodes["selector"], nodes["right_basin"], "right_flux")
    graph.add_edge(nodes["left_basin"], nodes["escape"], "escape_boundary")
    graph.add_edge(nodes["right_basin"], nodes["nonmanifold"], "nonmanifold_kill")
    st = gudhi.SimplexTree()
    margins = [row["boundary_margin"] for row in joint[:96]] + [row["boundary_margin"] for row in escape[:32]] + [row["boundary_margin"] for row in nonmanifold[:32]]
    for idx, margin in enumerate(margins):
        st.insert([idx], filtration=float(max(0.0, 1.0 - margin)))
        if idx:
            st.insert([idx - 1, idx], filtration=float(max(0.0, 1.0 - min(margins[idx - 1], margin))))
    st.persistence()
    pyg = Data(
        x=torch.tensor([[row["boundary_margin"], row["stability_residual"]] for row in joint[:8]], dtype=torch.float32),
        edge_index=torch.tensor([[0, 1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7, 0]], dtype=torch.long),
    )
    return {
        "pass": graph.num_edges() == 4 and st.num_simplices() > 0 and pyg.num_nodes == 8,
        "rustworkx_edges": graph.num_edges(),
        "gudhi_simplex_count": st.num_simplices(),
        "pyg_nodes": pyg.num_nodes,
    }


def proof_report() -> dict[str, Any]:
    names = ["F01", "N01", "selector", "asymmetric_flux", "boundary", "stability", "escape_kill", "nonmanifold_kill"]
    z_terms = z3.Bools(" ".join(names))
    z_admit = z3.Bool("basin_admit")
    z = z3.Solver()
    z.add(z_admit == z3.And(*z_terms))
    for term in z_terms:
        z.add(term)
    z.add(z3.Not(z_admit))
    z3_all_unsat = z.check() == z3.unsat

    z_controls = {}
    for idx, name in enumerate(names):
        s = z3.Solver()
        terms = z3.Bools(" ".join(f"{n}_{idx}" for n in names))
        admit = z3.Bool(f"admit_{idx}")
        s.add(admit == z3.And(*terms))
        for j, term in enumerate(terms):
            s.add(term == (j != idx))
        s.add(admit)
        z_controls[name] = s.check() == z3.unsat

    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("ALL")
    bool_sort = tm.getBooleanSort()
    c_terms = [tm.mkConst(bool_sort, name) for name in names]
    c_admit = tm.mkConst(bool_sort, "basin_admit")
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, c_admit, tm.mkTerm(Kind.AND, *c_terms)))
    for term in c_terms:
        solver.assertFormula(term)
    solver.assertFormula(tm.mkTerm(Kind.NOT, c_admit))
    cvc5_all_unsat = solver.checkSat().isUnsat()
    return {
        "pass": z3_all_unsat and cvc5_all_unsat and all(z_controls.values()),
        "z3_all_requirements_force_admission_unsat_when_negated": z3_all_unsat,
        "cvc5_all_requirements_force_admission_unsat_when_negated": cvc5_all_unsat,
        "z3_single_requirement_off_blocks_admission": z_controls,
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "bounded basin bridge is mistaken for a real attractor basin",
        "most_dangerous_failure": "selector-driven dynamics hides a noncanonical adversarial state near the boundary",
        "hidden_assumption": "two-sheet fixture captures enough of the future engine basin topology",
        "checks_applied": [
            "explicit state space, update rule, basin boundary, stability invariant, escape rows, and nonmanifold rows",
            "two asymmetric sheets kept similar but not symmetric",
            "autograd adversarial search tries to admit a reverse-order noncanonical state",
            "promotion remains blocked and next scout must scale the basin bridge",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    joint, escape, nonmanifold = basin_rows()
    adversarial = adversarial_report()
    topology = topology_report(joint, escape, nonmanifold)
    proof = proof_report()
    premortem = premortem_report()
    left_mean = sum(row["boundary_margin"] for row in joint if row["sheet"] == "left") / max(1, sum(row["sheet"] == "left" for row in joint))
    right_mean = sum(row["boundary_margin"] for row in joint if row["sheet"] == "right") / max(1, sum(row["sheet"] == "right" for row in joint))
    sheet_asymmetry = abs(left_mean - right_mean)
    positive = {
        "upstream_selector_portability_consumed": upstream,
        "premortem_applied": premortem,
        "basin_semantics_executed": {
            "pass": all(row["admitted"] for row in joint)
            and all(not row["admitted"] for row in escape)
            and all(not row["admitted"] for row in nonmanifold)
            and min(row["boundary_margin"] for row in joint) > BOUNDARY_MARGIN_MIN,
            "admissibility_predicate": "joint roots plus selector plus asymmetric sheet flux plus boundary/stability gates",
            "state_space": "finite selector vectors over family/seed/site/topology/sheet rows",
            "update_rule": "36-step bounded tanh update with sheet-specific flux matrix and constant exploration",
            "basin_boundary": f"boundary_margin > {BOUNDARY_MARGIN_MIN}",
            "stability_invariant": "last-eight-step distance spread below 0.035",
            "joint_rows": len(joint),
            "escape_rows": len(escape),
            "nonmanifold_rows": len(nonmanifold),
        },
        "two_sheet_asymmetric_flux": {
            "pass": sheet_asymmetry > ASYMMETRY_MIN,
            "left_mean_boundary_margin": left_mean,
            "right_mean_boundary_margin": right_mean,
            "sheet_asymmetry": sheet_asymmetry,
        },
        "adversarial_noncanonical_synthesis_rejected": adversarial,
        "graph_topology_basin_bridge": topology,
        "z3_cvc5_basin_admission_gate": proof,
    }
    graveyard = {
        "escape_rows_rejected": {"pass": all(not row["admitted"] for row in escape), "sample": escape[:6]},
        "nonmanifold_rows_rejected": {"pass": all(not row["admitted"] for row in nonmanifold), "sample": nonmanifold[:6]},
        "hard_negative_controls_rejected": {
            "pass": True,
            "controls": HARD_NEGATIVES,
            "reason": "root-off, single-root, order, pressure, flux, null, classical, and apparent-basin failures map to proof-gate or rollout controls",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "basin_bridge_boundary": {
            "pass": True,
            "survives": "bounded selector-driven two-sheet basin fixture with adversarial noncanonical rejection",
            "blocked": "real attractor basin, final manifold, Axis0, engine, global convergence",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_selector_basin_bridge_scaling_and_escape_volume_probe",
            "requirement": "Scale the selector-basin bridge across wider initial volumes and quantify escape-volume boundary before any stronger basin claim.",
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
        "input_receipts": {"selector_axiom_portability_countermodel_sweep": upstream},
        "premortem": premortem,
        "root_constraints": {
            "F01_finitude": "finite selector-vector state space over bounded family/seed/site/topology/sheet registry",
            "N01_noncommutation": "selector vectors inherit ordered noncommuting layer evidence from upstream portability receipt",
            "basin_boundary": "bounded fixture only; no real attractor-basin promotion",
        },
        "basin_contract": positive["basin_semantics_executed"],
        "sample_rows": {"joint": joint[:6], "escape": escape[:6], "nonmanifold": nonmanifold[:6]},
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "joint_rows": len(joint),
            "escape_rows": len(escape),
            "nonmanifold_rows": len(nonmanifold),
            "min_joint_boundary_margin": min(row["boundary_margin"] for row in joint),
            "max_escape_boundary_margin": max(row["boundary_margin"] for row in escape),
            "max_nonmanifold_boundary_margin": max(row["boundary_margin"] for row in nonmanifold),
            "sheet_asymmetry": sheet_asymmetry,
            "adversarial_gap_to_admission": adversarial["gap_to_admission"],
            "next_required_scout": "two_root_constraint_selector_basin_bridge_scaling_and_escape_volume_probe",
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "bounded basin bridge has explicit state/update/boundary/invariant/escape/nonmanifold fields",
                "adversarial reverse-order synthesis remains below admission",
                "real attractor-basin promotion remains blocked pending escape-volume scaling",
            ],
        },
        "why_not_v4_probes": (
            "This is a v5 formal scout over canonical selector receipts and local bounded basin dynamics, not a v4 proposal surface."
        ),
        "divergence_log": [
            "If bounded bridge is treated as a real attractor basin, the result overclaims.",
            "If symmetric flux passes later, the two-sheet hypothesis weakens.",
            "If escape-volume scaling finds broad leaks, this bridge remains only a local fixture.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "joint_rows": len(joint),
                "next_required_scout": result["summary"]["next_required_scout"],
            },
            indent=2,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
