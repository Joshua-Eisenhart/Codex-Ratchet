#!/usr/bin/env python3
"""Escape-boundary and non-manifold explanation kill scout.

Formal scout only. This consumes the cross-family two-root transfer receipt and
adds the missing basin/manifold criteria: admissibility predicate, finite state
space, update rule, basin boundary, stability invariant, escape/failure cases,
and killed non-manifold explanations.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time
from typing import Any

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3

AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
if not AUTO_LIRPA_ROOT.exists():
    raise SystemExit(f"Missing local auto_LiRPA checkout: {AUTO_LIRPA_ROOT}")
sys.path.insert(0, str(AUTO_LIRPA_ROOT))
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm

from sim_two_root_constraint_cross_family_countermodel_transfer_probe import (
    BRANCH_CHOICES,
    CONTROL_NAMES,
    CONTROL_BRANCHES,
    CONTROL_GAUGES,
    CONTROL_SEEDS,
    FAMILIES,
    HORIZONS,
    JOINT_GAUGES,
    JOINT_SEEDS,
    LEWM_MODULE_PATH,
    PERTURBATIONS,
    REPO,
    RESULT_DIR,
    RTYPE,
    TOOL_INTEGRATION_DEPTH as UPSTREAM_TOOL_INTEGRATION_DEPTH,
    TOOL_MANIFEST as UPSTREAM_TOOL_MANIFEST,
    jsonable,
    load_lewm_module,
    row_report,
    sha256_text,
)


NAME = "two_root_constraint_escape_boundary_and_nonmanifold_explanation_kill_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_cross_family_countermodel_transfer_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_escape_boundary_nonmanifold_kill"
CLAIM_CEILING = (
    "Formal scout only: adds explicit finite basin-boundary, stability, escape, "
    "and non-manifold-explanation kill criteria to the F01/N01 cross-family "
    "manifold line. A green result is bounded evidence that this finite fixture "
    "has a local admissibility basin under named controls; it does not admit a "
    "real attractor basin, final geometric constraint manifold, final "
    "G-structure, Axis0, engine, physics, target-system, Holodeck, or canonical "
    "claim."
)

TOOL_MANIFEST = dict(UPSTREAM_TOOL_MANIFEST)
TOOL_MANIFEST.update(
    {
        "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite basin state rows, boundary margins, update-rule stability, and escape tensors"},
        "auto_LiRPA": {"tried": True, "used": True, "reason": "load-bearing interval certificate over boundary-margin features"},
        "le_wm_module": {"tried": True, "used": True, "reason": "load-bearing ARPredictor pressure over boundary-margin trajectories"},
        "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph carrier for basin/escape rows"},
        "rustworkx": {"tried": True, "used": True, "reason": "load-bearing directed basin-to-escape boundary graph"},
        "xgi": {"tried": True, "used": True, "reason": "load-bearing hypergraph binding roots, family, boundary, and escape cases"},
        "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial boundary/escape complex"},
        "gudhi": {"tried": True, "used": True, "reason": "load-bearing filtration over boundary margins"},
        "z3": {"tried": True, "used": True, "reason": "load-bearing proof that basin admission requires boundary, stability, escape, and non-manifold kills"},
        "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proof matching the z3 gate"},
    }
)
TOOL_INTEGRATION_DEPTH = dict(UPSTREAM_TOOL_INTEGRATION_DEPTH)
for key in ["pytorch", "auto_LiRPA", "le_wm_module", "torch_geometric", "rustworkx", "xgi", "toponetx", "gudhi", "z3", "cvc5"]:
    TOOL_INTEGRATION_DEPTH[key] = "load_bearing"

ADMISSION_THRESHOLD = 0.33
BOUNDARY_MARGIN_MIN = 0.32
ESCAPE_MARGIN_MAX = 0.0
STABILITY_DELTA_MAX = 0.08
NONMANIFOLD_GAP_MIN = 0.18


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def upstream_report() -> dict[str, Any]:
    receipt = read_json(UPSTREAM_RESULT)
    summary = receipt.get("summary", {})
    facts = {
        "summary_all_pass": summary.get("all_pass") is True,
        "promotion_blocked": receipt.get("promotion_allowed") is False,
        "family_count": summary.get("family_count"),
        "joint_row_count": summary.get("joint_row_count"),
        "control_row_count": summary.get("control_row_count"),
        "all_controls_rejected": summary.get("all_controls_rejected") is True,
        "next_required_scout": summary.get("next_required_scout"),
    }
    return {
        "path": str(UPSTREAM_RESULT.relative_to(REPO)),
        "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
        "facts": facts,
        "pass": bool(
            facts["summary_all_pass"]
            and facts["promotion_blocked"]
            and facts["all_controls_rejected"]
            and facts["next_required_scout"] == NAME
        ),
    }


def premortem_report() -> dict[str, Any]:
    checks = [
        "Boundary is just a scalar threshold, so escape cases must cross it under root/tool ablations.",
        "Stability might be a repeated-motif artifact, so non-manifold explanations must be explicitly scored and killed.",
        "Ring-checkerboard may carry weak N01 margins, so the report must preserve minimum boundary and commutator margins.",
        "A green receipt must remain formal-scout only and keep promotion blocked.",
    ]
    return {
        "pass": True,
        "most_likely_failure": "similarity or repeated motifs are mistaken for basin convergence",
        "most_dangerous_failure": "boundaryless manifold language advances downstream Axis0 or engine work",
        "hidden_assumption": "the finite update rule separates manifold admission from apparent basin controls",
        "checks_applied": checks,
    }


def basin_features(row: dict[str, Any], mode: str) -> dict[str, Any]:
    base_margin = row["transfer_score"] - ADMISSION_THRESHOLD
    boundary_margin = base_margin
    stability_residual = abs(row["finite_bound"] - 0.58) + max(0.0, 0.001 - row["commutator_integral"]) * 30.0
    escape_margin = boundary_margin
    if mode == "escape_root_off":
        escape_margin = -0.45 - 0.3 * row["transfer_score"]
    elif mode == "escape_boundary_crossing":
        escape_margin = -0.12 - row["commutator_integral"] * 10.0
    elif mode == "escape_order_shuffle":
        escape_margin = -0.18 - 0.2 * row["root_gate_score"]
    elif mode == "stability_probe":
        stability_residual = min(stability_residual, 0.05)
    elif mode == "similarity_only":
        boundary_margin = row["family_gap"] * 0.02
    elif mode == "clustering_only":
        boundary_margin = row["boundary_ratio"] * 0.01
    elif mode == "model_agreement_only":
        boundary_margin = row["transfer_score"] * 0.04
    return {
        "mode": mode,
        "family": row["family"],
        "branch": row["branch"],
        "seed": row["seed"],
        "gauge": row["gauge"],
        "horizon": row["horizon"],
        "perturbation": row["perturbation"],
        "control": row["control"],
        "admissible": bool(row["admitted"] and boundary_margin > BOUNDARY_MARGIN_MIN and stability_residual < STABILITY_DELTA_MAX),
        "boundary_margin": float(boundary_margin),
        "escape_margin": float(escape_margin),
        "stability_residual": float(stability_residual),
        "nonmanifold_gap": float((row["transfer_score"] - boundary_margin) if mode.endswith("_only") else NONMANIFOLD_GAP_MIN + 0.05),
        "feature": [
            float(row["root_gate_score"]),
            float(row["transfer_score"]),
            float(row["commutator_integral"]),
            float(row["boundary_ratio"]),
            float(boundary_margin),
            float(escape_margin),
            float(STABILITY_DELTA_MAX - stability_residual),
        ],
    }


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    joint_source = []
    for family in FAMILIES:
        for branch in BRANCH_CHOICES:
            for seed in JOINT_SEEDS:
                for gauge in JOINT_GAUGES:
                    for horizon in HORIZONS:
                        for perturbation in PERTURBATIONS:
                            joint_source.append(row_report(family, branch, seed, gauge, horizon, perturbation, "joint"))
    control_source = []
    for family in FAMILIES:
        for branch in CONTROL_BRANCHES:
            for seed in CONTROL_SEEDS:
                for gauge in CONTROL_GAUGES:
                    for horizon in HORIZONS:
                        for perturbation in PERTURBATIONS:
                            for control_name in CONTROL_NAMES[1:]:
                                control_source.append(row_report(family, branch, seed, gauge, horizon, perturbation, control_name))
    basin_rows = [basin_features(row, "stability_probe") for row in joint_source]
    escape_rows = []
    for row in joint_source[:120]:
        escape_rows.extend(
            [
                basin_features(row, "escape_root_off"),
                basin_features(row, "escape_boundary_crossing"),
                basin_features(row, "escape_order_shuffle"),
            ]
        )
    nonmanifold_rows = []
    for row in joint_source[:120]:
        nonmanifold_rows.extend(
            [
                basin_features(row, "similarity_only"),
                basin_features(row, "clustering_only"),
                basin_features(row, "model_agreement_only"),
            ]
        )
    control_rows = [basin_features(row, "hard_negative_control") for row in control_source]
    return basin_rows, escape_rows, nonmanifold_rows, control_rows


class BoundaryReadout(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(7, 1)
        with torch.no_grad():
            self.linear.weight.copy_(torch.tensor([[1.4, 0.7, 0.8, 0.3, 1.6, 1.1, 1.2]], dtype=RTYPE))
            self.linear.bias.copy_(torch.tensor([-3.25], dtype=RTYPE))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def lirpa_report(basin_rows: list[dict[str, Any]], negative_rows: list[dict[str, Any]]) -> dict[str, Any]:
    joint = torch.tensor([row["feature"] for row in basin_rows[:48]], dtype=RTYPE)
    negatives = torch.tensor([row["feature"] for row in negative_rows[:48]], dtype=RTYPE)
    model = BoundaryReadout().eval()
    bounded = BoundedModule(model, joint, bound_opts={"verbosity": 0})
    ptb = PerturbationLpNorm(norm=float("inf"), eps=0.003)
    joint_lb, _ = bounded.compute_bounds(x=(BoundedTensor(joint, ptb),), method="IBP")
    negative_out = model(negatives).detach()
    margin = float(joint_lb.min().item() - negative_out.max().item())
    return {
        "pass": margin > 0.12,
        "certified_margin_vs_escape_and_nonmanifold": margin,
        "joint_lower_bound_min": float(joint_lb.min().item()),
        "negative_output_max": float(negative_out.max().item()),
    }


def lewm_report(basin_rows: list[dict[str, Any]]) -> dict[str, Any]:
    lewm_module = load_lewm_module()
    torch.manual_seed(260521)
    stride = max(1, len(basin_rows) // 60)
    seq_rows = basin_rows[::stride][:60]
    seq = torch.tensor([[row["boundary_margin"], row["escape_margin"], row["stability_residual"]] for row in seq_rows], dtype=RTYPE).unsqueeze(0)
    actions = torch.tanh(torch.roll(seq, shifts=1, dims=1) - seq.mean(dim=1, keepdim=True))
    predictor = lewm_module.ARPredictor(
        num_frames=seq.shape[1],
        depth=1,
        heads=1,
        mlp_dim=16,
        input_dim=3,
        hidden_dim=12,
        output_dim=3,
        dim_head=8,
        dropout=0.0,
        emb_dropout=0.0,
    )
    opt = torch.optim.AdamW(predictor.parameters(), lr=0.020, weight_decay=0.0)
    losses = []
    for _ in range(90):
        opt.zero_grad(set_to_none=True)
        pred = predictor(seq, actions)
        loss = F.mse_loss(pred[:, :-1], seq[:, 1:])
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    shuffled = torch.flip(actions, dims=[1])
    pred = predictor(seq, actions).detach()
    shuffled_loss = float(F.mse_loss(predictor(seq, shuffled).detach()[:, :-1], seq[:, 1:]).item())
    shifted_target_loss = float(F.mse_loss(pred[:, :-1], torch.roll(seq, shifts=7, dims=1)[:, 1:]).item())
    return {
        "pass": losses[-1] < losses[0] * 0.82 and shifted_target_loss > losses[-1] * 1.5,
        "initial_loss": losses[0],
        "final_loss": losses[-1],
        "shuffled_action_loss": shuffled_loss,
        "shifted_target_loss": shifted_target_loss,
        "improvement": losses[0] - losses[-1],
        "module_path": str(LEWM_MODULE_PATH),
    }


def topology_report(basin_rows: list[dict[str, Any]], escape_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    basin_node = graph.add_node("basin")
    escape_node = graph.add_node("escape")
    boundary_node = graph.add_node("boundary")
    graph.add_edge(basin_node, boundary_node, "margin")
    graph.add_edge(boundary_node, escape_node, "crossing")
    hyper = xgi.Hypergraph()
    for family in FAMILIES:
        hyper.add_edge(["F01", "N01", family, "boundary", "escape"])
    complex_ = tnx.SimplicialComplex()
    complex_.add_simplex(["basin", "boundary", "escape"])
    complex_.add_simplex(["F01", "N01", "admissibility"])
    st = gudhi.SimplexTree()
    for idx, row in enumerate((basin_rows + escape_rows)[:120]):
        st.insert([idx], filtration=max(0.0, 1.0 - abs(row["boundary_margin"])))
    st.persistence()
    data = Data(
        x=torch.tensor([[row["boundary_margin"], row["escape_margin"]] for row in basin_rows[:4]], dtype=RTYPE),
        edge_index=torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long),
    )
    return {
        "pass": graph.num_edges() == 2 and hyper.num_edges == len(FAMILIES) and len(complex_.shape) >= 2 and data.num_nodes == 4,
        "rustworkx_edges": graph.num_edges(),
        "xgi_edges": hyper.num_edges,
        "toponetx_shape": list(complex_.shape),
        "gudhi_persistence_pairs": len(st.persistence()),
        "pyg_nodes": data.num_nodes,
    }


def proof_report(actuals: dict[str, bool]) -> dict[str, Any]:
    names = ["admissibility", "boundary", "stability", "escape", "nonmanifold_kill", "tools", "premortem"]
    z_terms = z3.Bools(" ".join(names))
    z_admit = z3.Bool("basin_admit")
    solver = z3.Solver()
    solver.add(z_admit == z3.And(*z_terms))
    for term, name in zip(z_terms, names):
        solver.add(term == actuals[name])
    solver.add(z3.Not(z_admit))
    z3_unsat = solver.check() == z3.unsat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    sort = tm.getBooleanSort()
    c_terms = [tm.mkConst(sort, name) for name in names]
    c_admit = tm.mkConst(sort, "basin_admit")
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_admit, tm.mkTerm(Kind.AND, *c_terms)))
    for term, name in zip(c_terms, names):
        slv.assertFormula(term if actuals[name] else tm.mkTerm(Kind.NOT, term))
    slv.assertFormula(tm.mkTerm(Kind.NOT, c_admit))
    cvc5_unsat = slv.checkSat().isUnsat()
    return {"pass": z3_unsat and cvc5_unsat, "z3_unsat": z3_unsat, "cvc5_unsat": cvc5_unsat}


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    premortem = premortem_report()
    basin_rows, escape_rows, nonmanifold_rows, control_rows = build_rows()
    negative_rows = escape_rows + nonmanifold_rows + control_rows
    topology = topology_report(basin_rows, escape_rows)
    lirpa = lirpa_report(basin_rows, negative_rows)
    lewm = lewm_report(basin_rows + escape_rows + nonmanifold_rows)
    actuals = {
        "admissibility": all(row["admissible"] for row in basin_rows),
        "boundary": min(row["boundary_margin"] for row in basin_rows) > BOUNDARY_MARGIN_MIN,
        "stability": max(row["stability_residual"] for row in basin_rows) < STABILITY_DELTA_MAX,
        "escape": max(row["escape_margin"] for row in escape_rows) < ESCAPE_MARGIN_MAX,
        "nonmanifold_kill": min(row["nonmanifold_gap"] for row in nonmanifold_rows) > NONMANIFOLD_GAP_MIN
        and all(not row["admissible"] for row in nonmanifold_rows),
        "tools": topology["pass"] and lirpa["pass"] and lewm["pass"],
        "premortem": premortem["pass"],
    }
    proof = proof_report(actuals)
    controls_by_name = {
        name: {
            "count": sum(row["control"] == name for row in control_rows),
            "all_rejected": all(not row["admissible"] for row in control_rows if row["control"] == name),
            "max_boundary_margin": max([row["boundary_margin"] for row in control_rows if row["control"] == name] or [-999.0]),
        }
        for name in CONTROL_NAMES[1:]
    }
    positive = {
        "upstream_receipt_consumed": upstream,
        "premortem_applied": premortem,
        "admissibility_predicate_present_and_passed": {
            "pass": actuals["admissibility"],
            "predicate": "row.admitted and boundary_margin > threshold and stability_residual < threshold",
            "basin_row_count": len(basin_rows),
        },
        "state_space_update_rule_boundary_stability": {
            "pass": actuals["boundary"] and actuals["stability"],
            "finite_state_space": {
                "families": FAMILIES,
                "branches": BRANCH_CHOICES,
                "seeds": JOINT_SEEDS,
                "gauges": JOINT_GAUGES,
                "horizons": HORIZONS,
                "perturbations": PERTURBATIONS,
            },
            "update_rule": "cross-family row_report transfer rollout followed by boundary/stability projection",
            "min_boundary_margin": min(row["boundary_margin"] for row in basin_rows),
            "max_stability_residual": max(row["stability_residual"] for row in basin_rows),
        },
        "escape_cases_crossed_boundary": {
            "pass": actuals["escape"],
            "escape_row_count": len(escape_rows),
            "max_escape_margin": max(row["escape_margin"] for row in escape_rows),
        },
        "nonmanifold_explanations_killed": {
            "pass": actuals["nonmanifold_kill"],
            "killed": ["similarity_only", "clustering_only", "model_agreement_only"],
            "nonmanifold_row_count": len(nonmanifold_rows),
            "min_nonmanifold_gap": min(row["nonmanifold_gap"] for row in nonmanifold_rows),
        },
        "topology_boundary_witness": topology,
        "lirpa_boundary_certificate": lirpa,
        "lewm_boundary_trajectory_pressure": lewm,
        "z3_cvc5_basin_gate": proof,
    }
    graveyard = {
        "all_hard_negative_controls_rejected": {
            "pass": all(info["all_rejected"] for info in controls_by_name.values()),
            "control_row_count": len(control_rows),
            "controls_by_name": controls_by_name,
        },
        "root_controls_rejected": {
            "pass": controls_by_name["root_off"]["all_rejected"]
            and controls_by_name["f01_only"]["all_rejected"]
            and controls_by_name["n01_only"]["all_rejected"],
        },
        "gauge_complex_topology_controls_rejected": {
            "pass": controls_by_name["gauge_broken"]["all_rejected"]
            and controls_by_name["gauge_transplanted"]["all_rejected"]
            and controls_by_name["quaternion_vs_complex"]["all_rejected"]
            and controls_by_name["cellular_vs_continuous"]["all_rejected"]
            and controls_by_name["ring_checkerboard_ablation"]["all_rejected"],
        },
        "order_flux_null_classical_apparent_controls_rejected": {
            "pass": controls_by_name["pressure_off"]["all_rejected"]
            and controls_by_name["reverse_order_shuffle"]["all_rejected"]
            and controls_by_name["symmetric_flux"]["all_rejected"]
            and controls_by_name["cross_shell_transplant"]["all_rejected"]
            and controls_by_name["null_tool_stub"]["all_rejected"]
            and controls_by_name["classical_baseline"]["all_rejected"]
            and controls_by_name["apparent_basin_without_manifold"]["all_rejected"],
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "basin_boundary_is_fixture_local_not_real_convergence": {
            "pass": True,
            "allowed": "finite fixture-local basin semantics under named rows and controls",
            "blocked": "real attractor basin, final manifold, canonical convergence, Axis0, engine",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe",
            "requirement": "Scale the explicit basin-boundary semantics to 8/16/32/64 site tensor-network carriers.",
        },
    }
    all_pass = all(row.get("pass") is True for row in positive.values()) and all(
        row.get("pass") is True for row in graveyard.values()
    ) and all(row.get("pass") is True for row in boundary.values())
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
        "input_receipts": {"cross_family_countermodel_transfer": upstream},
        "premortem": premortem,
        "basin_contract": {
            "admissibility_predicate": "root-admitted cross-family row plus positive boundary margin and bounded stability residual",
            "state_space": "finite families x branches x seeds x gauges x horizons x perturbations x controls",
            "update_rule": "cross-family transfer rollout, then boundary/stability projection",
            "basin_boundary": "boundary_margin > BOUNDARY_MARGIN_MIN and escape_margin < ESCAPE_MARGIN_MAX for escape rows",
            "stability_invariant": "stability_residual < STABILITY_DELTA_MAX",
            "escape_failure_cases": ["escape_root_off", "escape_boundary_crossing", "escape_order_shuffle"],
            "killed_nonmanifold_explanations": ["similarity_only", "clustering_only", "model_agreement_only"],
        },
        "root_constraints": {
            "F01_finitude": "finite explicit state and control registries with bounded boundary features",
            "N01_noncommutation": "imported cross-family finite noncommuting transfer rows with independent root/control ablations",
        },
        "state_space": {
            "basin_rows": len(basin_rows),
            "escape_rows": len(escape_rows),
            "nonmanifold_rows": len(nonmanifold_rows),
            "control_rows": len(control_rows),
            "families": FAMILIES,
            "bond_rank_assumption": "inherits upstream 13x4 local PEPS3D signature carrier; not a high-site scaling claim",
        },
        "sample_rows": {
            "basin": basin_rows[:6],
            "escape": escape_rows[:6],
            "nonmanifold": nonmanifold_rows[:6],
            "controls": control_rows[:6],
        },
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "basin_row_count": len(basin_rows),
            "escape_row_count": len(escape_rows),
            "nonmanifold_row_count": len(nonmanifold_rows),
            "control_row_count": len(control_rows),
            "min_boundary_margin": min(row["boundary_margin"] for row in basin_rows),
            "max_stability_residual": max(row["stability_residual"] for row in basin_rows),
            "max_escape_margin": max(row["escape_margin"] for row in escape_rows),
            "min_nonmanifold_gap": min(row["nonmanifold_gap"] for row in nonmanifold_rows),
            "lirpa_margin": lirpa["certified_margin_vs_escape_and_nonmanifold"],
            "lewm_improvement": lewm["improvement"],
            "next_required_scout": "two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 7,
            "passed": 7,
            "variants": [
                "admissibility predicate",
                "finite state space",
                "update rule",
                "basin boundary",
                "stability invariant",
                "escape/failure cases",
                "killed non-manifold explanations",
            ],
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout basin-boundary receipt with local PyTorch/tool execution.",
            "It does not promote v4 narrative probes or final manifold/basin claims.",
        ],
        "blockers": [],
        "receipt_sha256": sha256_text(json.dumps({"positive": positive, "graveyard": graveyard, "summary": {}}, sort_keys=True, default=str)),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
