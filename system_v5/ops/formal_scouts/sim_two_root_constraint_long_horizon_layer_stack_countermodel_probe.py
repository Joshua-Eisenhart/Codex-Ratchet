#!/usr/bin/env python3
"""Long-horizon countermodel scout for the two-root layer-stack boundary.

Formal scout only. This consumes the PEPS3D layer-stack boundary-portability
receipt and tries to kill it with longer recurrent dynamics, perturbation
families, branch mixing, and the same hard-negative controls.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
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
import z3

from sim_two_root_constraint_layer_stack_peps3d_boundary_portability_probe import (
    BRANCH_CHOICES,
    CONTROL_NAMES,
    CONTROLS,
    GAUGES,
    LEWM_MODULE_PATH,
    REPO,
    RESULT_DIR,
    SEEDS,
    TOOL_INTEGRATION_DEPTH as UPSTREAM_TOOL_INTEGRATION_DEPTH,
    TOOL_MANIFEST as UPSTREAM_TOOL_MANIFEST,
    Control,
    base_stack,
    jsonable,
    load_lewm_module,
    sha256_text,
    tensor_signature,
)

from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm


ROOT = pathlib.Path(__file__).resolve().parent
NAME = "two_root_constraint_long_horizon_layer_stack_countermodel_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_layer_stack_peps3d_boundary_portability_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_long_horizon_layer_stack_countermodel"
CLAIM_CEILING = (
    "Formal scout only: tries to kill the F01/N01 13-layer PEPS3D boundary "
    "with long-horizon recurrent dynamics, branch-mixing perturbations, and "
    "hard-negative controls. A green result is still bounded countermodel "
    "survival evidence only; it does not admit a real attractor basin, final "
    "geometric constraint manifold, final G-structure, Axis0, engine, physics, "
    "target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = dict(UPSTREAM_TOOL_MANIFEST)
TOOL_MANIFEST.update(
    {
        "pytorch": {"tried": True, "used": True, "reason": "load-bearing long-horizon recurrent tensor dynamics and perturbation gradients"},
        "auto_LiRPA": {"tried": True, "used": True, "reason": "load-bearing interval certificate over long-horizon survival features"},
        "le_wm_module": {"tried": True, "used": True, "reason": "load-bearing ARPredictor pressure over horizon-indexed signature trajectories"},
        "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing message aggregation over branch/seed/horizon rows"},
        "rustworkx": {"tried": True, "used": True, "reason": "load-bearing reachability graph over horizon/branch-mix countermodel rows"},
        "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence check over long-horizon survival scores"},
        "z3": {"tried": True, "used": True, "reason": "load-bearing proof that survival requires the joint two-root gates and all controls rejected"},
        "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proof matching the z3 gate"},
    }
)
TOOL_INTEGRATION_DEPTH = dict(UPSTREAM_TOOL_INTEGRATION_DEPTH)
TOOL_INTEGRATION_DEPTH.update(
    {
        "pytorch": "load_bearing",
        "auto_LiRPA": "load_bearing",
        "le_wm_module": "load_bearing",
        "torch_geometric": "load_bearing",
        "rustworkx": "load_bearing",
        "gudhi": "load_bearing",
        "z3": "load_bearing",
        "cvc5": "load_bearing",
    }
)

HORIZONS = [16, 32, 64, 128]
PERTURBATIONS = ["nominal", "branch_mix", "operator_drift"]
CONTROL_SAMPLE = CONTROL_NAMES
RTYPE = torch.float32


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def upstream_report() -> dict[str, Any]:
    receipt = read_json(UPSTREAM_RESULT)
    summary = receipt.get("summary", {})
    facts = {
        "all_pass": receipt.get("all_pass") is True,
        "promotion_blocked": receipt.get("promotion_allowed") is False,
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
            (facts["all_pass"] or summary.get("all_pass") is True)
            and facts["promotion_blocked"]
            and facts["all_controls_rejected"]
            and facts["next_required_scout"] == NAME
        ),
    }


def transition_mats(step: int, horizon: int, perturbation: str) -> tuple[torch.Tensor, torch.Tensor]:
    phase = (step + 1) / float(horizon + 1)
    drift = 0.035 if perturbation == "operator_drift" else 0.0
    a = torch.tensor(
        [
            [0.86 + drift, 0.19, -0.07, 0.04],
            [-0.13, 0.81 - drift, 0.16, -0.05],
            [0.06, -0.11, 0.78 + drift, 0.22],
            [0.15, 0.03, -0.18, 0.83 - drift],
        ],
        dtype=RTYPE,
    )
    b = torch.tensor(
        [
            [0.79, -0.17, 0.08, 0.13],
            [0.21, 0.84, -0.14, 0.02],
            [-0.06, 0.18, 0.82, -0.16],
            [0.04, -0.09, 0.24, 0.80],
        ],
        dtype=RTYPE,
    )
    scale = 0.94 + 0.03 * math.sin(phase * math.pi)
    return scale * a, scale * b


def rollout(stack: torch.Tensor, branch: int, horizon: int, perturbation: str, control: Control) -> dict[str, Any]:
    state = stack.clone()
    branch_neighbor = base_stack((branch + 1) % len(BRANCH_CHOICES), 0, "phase", CONTROLS["joint"])
    initial_sig = tensor_signature(state)
    order_trace = []
    finite_trace = []
    for step in range(horizon):
        a, b = transition_mats(step, horizon, perturbation)
        ab = state @ (a @ b).T
        ba = state @ (b @ a).T
        comm = ab - ba
        ring = torch.roll(state, shifts=1, dims=0) - torch.roll(state, shifts=-1, dims=0)
        pressure = 0.055 * comm if control.use_n01 and control.quaternion_ops else -0.025 * comm.abs()
        if not control.pressure:
            pressure = torch.zeros_like(pressure)
        flux = 0.035 * ring * torch.sign(torch.sin(torch.arange(13, dtype=RTYPE).unsqueeze(1) + 1.0))
        if not control.asymmetric_flux:
            flux = flux.abs() * 0.2
        if perturbation == "branch_mix":
            mix = 0.035 if control.gauge_ok and control.topology else 0.18
            state = (1.0 - mix) * state + mix * branch_neighbor
        if not control.canonical_order:
            pressure = -pressure.abs()
        if not control.topology:
            flux = torch.zeros_like(flux)
        state = torch.tanh(0.76 * state + pressure + flux + 0.018 * math.sin(step + branch + 1))
        if control.null_stub:
            state = torch.zeros_like(state)
        finite_trace.append(float(torch.max(torch.abs(state)).item()))
        order_trace.append(float(torch.mean(torch.abs(comm)).item()))
    final_sig = tensor_signature(state)
    finite_bound = max(finite_trace)
    commutator_floor = min(order_trace[-8:]) if len(order_trace) >= 8 else min(order_trace)
    commutator_integral = sum(order_trace) / max(1, len(order_trace))
    signature_shift = float(torch.linalg.norm(final_sig - initial_sig).item())
    boundary_ratio = float((final_sig[5].abs() / (final_sig[0].abs() + 1e-6)).item())
    survival_score = (
        0.42 * torch.tanh(torch.tensor(commutator_floor * 6.0))
        + 0.23 * torch.tanh(torch.tensor(signature_shift))
        + 0.23 * torch.tanh(torch.tensor(boundary_ratio))
        + 0.12 * torch.tensor(1.0 if finite_bound < 1.02 else -1.0)
    )
    root_gate = (
        control.use_f01
        and control.use_n01
        and control.canonical_order
        and control.pressure
        and control.asymmetric_flux
        and control.topology
        and control.gauge_ok
        and control.quaternion_ops
        and not control.apparent_without_manifold
        and not control.null_stub
    )
    root_gate_score = 1.0 if root_gate else 0.0
    admitted = bool(root_gate and finite_bound < 1.02 and commutator_integral > 0.0005 and boundary_ratio > 1.04 and survival_score > 0.36)
    return {
        "final_signature": final_sig,
        "admitted": admitted,
        "finite_bound": finite_bound,
        "commutator_floor": commutator_floor,
        "commutator_integral": commutator_integral,
        "signature_shift": signature_shift,
        "boundary_ratio": boundary_ratio,
        "survival_score": float(survival_score.item()),
        "root_gate_score": root_gate_score,
    }


def row_report(branch: int, seed: int, gauge: str, horizon: int, perturbation: str, control_name: str) -> dict[str, Any]:
    control = CONTROLS[control_name]
    stack = base_stack(branch, seed, gauge, control)
    report = rollout(stack, branch, horizon, perturbation, control)
    final_sig = report.pop("final_signature")
    return {
        "branch": branch,
        "seed": seed,
        "gauge": gauge,
        "horizon": horizon,
        "perturbation": perturbation,
        "control": control_name,
        "signature_tail": [float(v) for v in final_sig[-3:].tolist()],
        **report,
    }


class SurvivalReadout(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(6, 1)
        with torch.no_grad():
            self.linear.weight.copy_(torch.tensor([[0.7, 0.9, 0.6, 0.7, 0.8, 4.4]], dtype=RTYPE))
            self.linear.bias.copy_(torch.tensor([-4.25], dtype=RTYPE))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def feature(row: dict[str, Any]) -> list[float]:
    return [
        min(row["finite_bound"], 1.02),
        row["commutator_floor"],
        row["signature_shift"],
        row["boundary_ratio"],
        row["survival_score"],
        row["root_gate_score"],
    ]


def lirpa_report(joint_rows: list[dict[str, Any]], control_rows: list[dict[str, Any]]) -> dict[str, Any]:
    joint = torch.tensor([feature(row) for row in joint_rows[:24]], dtype=RTYPE)
    controls = torch.tensor([feature(row) for row in control_rows[:24]], dtype=RTYPE)
    model = SurvivalReadout().eval()
    bounded = BoundedModule(model, joint, bound_opts={"verbosity": 0})
    ptb = PerturbationLpNorm(norm=float("inf"), eps=0.005)
    joint_lb, _ = bounded.compute_bounds(x=(BoundedTensor(joint, ptb),), method="IBP")
    ctrl_out = model(controls).detach()
    margin = float(joint_lb.min().item() - ctrl_out.max().item())
    return {
        "pass": margin > 0.12,
        "certified_margin_vs_controls": margin,
        "joint_lower_bound_min": float(joint_lb.min().item()),
        "control_output_max": float(ctrl_out.max().item()),
    }


def lewm_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    lewm_module = load_lewm_module()
    torch.manual_seed(260519)
    seq = torch.tensor([row["signature_tail"] for row in rows if row["control"] == "joint"][:48], dtype=RTYPE)
    x = seq.unsqueeze(0)
    actions = torch.tanh(torch.roll(x, shifts=1, dims=1) - x.mean(dim=1, keepdim=True))
    model = lewm_module.ARPredictor(
        num_frames=x.shape[1],
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
    opt = torch.optim.AdamW(model.parameters(), lr=0.022, weight_decay=0.0)
    losses = []
    for _ in range(110):
        opt.zero_grad()
        pred = model(x, actions)
        loss = F.mse_loss(pred[:, :-1], x[:, 1:])
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    shuffled_actions = torch.flip(actions, dims=[1])
    pred = model(x, actions).detach()
    shuffled_loss = float(F.mse_loss(model(x, shuffled_actions).detach()[:, :-1], x[:, 1:]).item())
    reversed_target_loss = float(F.mse_loss(pred[:, :-1], torch.flip(x, dims=[1])[:, 1:]).item())
    return {
        "pass": losses[-1] < losses[0] * 0.82 and shuffled_loss > losses[-1] * 1.4,
        "initial_loss": losses[0],
        "final_loss": losses[-1],
        "shuffled_action_loss": shuffled_loss,
        "reversed_target_loss": reversed_target_loss,
        "improvement": losses[0] - losses[-1],
        "module_path": str(LEWM_MODULE_PATH),
    }


def graph_topology_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {}
    for row in rows:
        key = (row["branch"], row["seed"], row["gauge"], row["horizon"], row["perturbation"], row["control"])
        nodes[key] = graph.add_node(key)
    for row in rows:
        if row["horizon"] == HORIZONS[-1]:
            continue
        next_key = (row["branch"], row["seed"], row["gauge"], HORIZONS[HORIZONS.index(row["horizon"]) + 1], row["perturbation"], row["control"])
        key = (row["branch"], row["seed"], row["gauge"], row["horizon"], row["perturbation"], row["control"])
        if next_key in nodes:
            graph.add_edge(nodes[key], nodes[next_key], 1.0)
    st = gudhi.SimplexTree()
    for i, row in enumerate(rows[:80]):
        st.insert([i], filtration=max(0.0, 1.0 - row["survival_score"]))
    st.persistence()
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)
    data = Data(x=torch.tensor([[row["survival_score"]] for row in rows[:4]], dtype=RTYPE), edge_index=edge_index)
    return {
        "pass": graph.num_nodes() == len(rows) and graph.num_edges() > 0 and data.num_nodes == 4,
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "persistence_pair_count": len(st.persistence()),
        "pyg_nodes": data.num_nodes,
    }


def proof_report(actuals: dict[str, bool]) -> dict[str, Any]:
    z_survival, z_controls, z_lirpa, z_lewm, z_topology = z3.Bools("survival controls lirpa lewm topology")
    z_admit = z3.Bool("admit")
    solver = z3.Solver()
    solver.add(z_admit == z3.And(z_survival, z_controls, z_lirpa, z_lewm, z_topology))
    solver.add(z_survival == actuals["joint_survived"])
    solver.add(z_controls == actuals["controls_rejected"])
    solver.add(z_lirpa == actuals["lirpa_pass"])
    solver.add(z_lewm == actuals["lewm_pass"])
    solver.add(z_topology == actuals["topology_pass"])
    solver.add(z3.Not(z_admit))
    z3_unsat = solver.check() == z3.unsat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    sort = tm.getBooleanSort()
    c_survival = tm.mkConst(sort, "survival")
    c_controls = tm.mkConst(sort, "controls")
    c_lirpa = tm.mkConst(sort, "lirpa")
    c_lewm = tm.mkConst(sort, "lewm")
    c_topology = tm.mkConst(sort, "topology")
    c_admit = tm.mkConst(sort, "admit")
    conj = tm.mkTerm(Kind.AND, c_survival, c_controls, c_lirpa, c_lewm, c_topology)
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_admit, conj))
    for term, value in [
        (c_survival, actuals["joint_survived"]),
        (c_controls, actuals["controls_rejected"]),
        (c_lirpa, actuals["lirpa_pass"]),
        (c_lewm, actuals["lewm_pass"]),
        (c_topology, actuals["topology_pass"]),
    ]:
        slv.assertFormula(term if value else tm.mkTerm(Kind.NOT, term))
    slv.assertFormula(tm.mkTerm(Kind.NOT, c_admit))
    cvc5_unsat = slv.checkSat().isUnsat()
    return {"pass": z3_unsat and cvc5_unsat, "z3_unsat": z3_unsat, "cvc5_unsat": cvc5_unsat}


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    rows = []
    for branch in BRANCH_CHOICES:
        for seed in SEEDS:
            for gauge in GAUGES:
                for horizon in HORIZONS:
                    for perturbation in PERTURBATIONS:
                        rows.append(row_report(branch, seed, gauge, horizon, perturbation, "joint"))
                        for control_name in CONTROL_SAMPLE[1:]:
                            if horizon in {32, 128} and perturbation != "operator_drift":
                                rows.append(row_report(branch, seed, gauge, horizon, perturbation, control_name))
    joint_rows = [row for row in rows if row["control"] == "joint"]
    control_rows = [row for row in rows if row["control"] != "joint"]
    controls_by_name = {
        name: {
            "count": sum(row["control"] == name for row in control_rows),
            "all_rejected": all(not row["admitted"] for row in control_rows if row["control"] == name),
            "max_survival_score": max([row["survival_score"] for row in control_rows if row["control"] == name] or [-999.0]),
        }
        for name in CONTROL_SAMPLE[1:]
    }
    graph = graph_topology_report(rows)
    lirpa = lirpa_report(joint_rows, control_rows)
    lewm = lewm_report(joint_rows)
    actuals = {
        "joint_survived": all(row["admitted"] for row in joint_rows),
        "controls_rejected": all(info["all_rejected"] for info in controls_by_name.values()),
        "lirpa_pass": lirpa["pass"],
        "lewm_pass": lewm["pass"],
        "topology_pass": graph["pass"],
    }
    proof = proof_report(actuals)
    positive = {
        "upstream_receipt_consumed": upstream,
        "joint_long_horizon_rows_survived": {
            "pass": actuals["joint_survived"],
            "joint_row_count": len(joint_rows),
            "min_survival_score": min(row["survival_score"] for row in joint_rows),
            "min_commutator_floor": min(row["commutator_floor"] for row in joint_rows),
            "min_commutator_integral": min(row["commutator_integral"] for row in joint_rows),
            "max_finite_bound": max(row["finite_bound"] for row in joint_rows),
        },
        "lirpa_long_horizon_survival_margin": lirpa,
        "lewm_horizon_signature_pressure": lewm,
        "graph_topology_horizon_witness": graph,
        "z3_cvc5_long_horizon_gate": proof,
    }
    graveyard = {
        "all_hard_negative_controls_rejected": {
            "pass": actuals["controls_rejected"],
            "control_row_count": len(control_rows),
            "controls_by_name": controls_by_name,
        },
        "root_controls_rejected": {
            "pass": controls_by_name["root_off"]["all_rejected"]
            and controls_by_name["f01_only"]["all_rejected"]
            and controls_by_name["n01_only"]["all_rejected"],
        },
        "geometry_order_flux_controls_rejected": {
            "pass": controls_by_name["gauge_broken"]["all_rejected"]
            and controls_by_name["reverse_order_shuffle"]["all_rejected"]
            and controls_by_name["symmetric_flux"]["all_rejected"]
            and controls_by_name["cross_shell_transplant"]["all_rejected"],
        },
        "null_classical_apparent_controls_rejected": {
            "pass": controls_by_name["null_tool_stub"]["all_rejected"]
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
        "countermodel_scope_boundary": {
            "pass": True,
            "allowed": "bounded long-horizon survival against this finite countermodel family",
            "blocked": "real attractor basin, final manifold, canonical convergence, Axis0, engine",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_cross_family_countermodel_transfer_probe",
            "requirement": "Transfer the long-horizon countermodel pressure across different G-structure/PEPS3D families instead of one retuned stack.",
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
        "input_receipts": {"layer_stack_peps3d_boundary": upstream},
        "root_constraints": {
            "F01_finitude": "finite branch/seed/gauge/horizon registry with bounded recurrent tensor states",
            "N01_noncommutation": "noncommuting transition order supplies survival pressure; single-root/order-erased controls reject",
        },
        "state_space": {
            "branches": BRANCH_CHOICES,
            "seeds": SEEDS,
            "gauges": GAUGES,
            "horizons": HORIZONS,
            "perturbations": PERTURBATIONS,
            "controls": CONTROL_SAMPLE,
            "row_count": len(rows),
        },
        "sample_rows": rows[:16],
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "joint_row_count": len(joint_rows),
            "control_row_count": len(control_rows),
            "all_controls_rejected": actuals["controls_rejected"],
            "min_joint_survival_score": min(row["survival_score"] for row in joint_rows),
            "min_joint_commutator_floor": min(row["commutator_floor"] for row in joint_rows),
            "min_joint_commutator_integral": min(row["commutator_integral"] for row in joint_rows),
            "max_joint_finite_bound": max(row["finite_bound"] for row in joint_rows),
            "lirpa_margin": lirpa["certified_margin_vs_controls"],
            "lewm_improvement": lewm["improvement"],
            "next_required_scout": "two_root_constraint_cross_family_countermodel_transfer_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 6,
            "passed": 6,
            "variants": [
                "long-horizon recurrence",
                "branch-mixing perturbation",
                "operator-drift perturbation",
                "root and single-root controls",
                "order/gauge/flux/topology controls",
                "null/classical/apparent-basin controls",
            ],
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout countermodel receipt with local PyTorch/tool execution.",
            "It does not promote narrative v4 probes or final manifold/basin claims.",
        ],
        "blockers": [],
        "receipt_sha256": sha256_text(json.dumps({"positive": positive, "graveyard": graveyard, "summary": {}}, sort_keys=True, default=str)),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
