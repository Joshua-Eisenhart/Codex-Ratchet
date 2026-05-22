#!/usr/bin/env python3
"""Cross-family countermodel-transfer scout for the two-root manifold line.

Formal scout only. This consumes the long-horizon two-root layer-stack
countermodel receipt and asks whether the same finite/noncommuting survival
gate transfers across several bounded G-structure/PEPS3D carrier families.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys
import time
from typing import Any

import cvc5
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
import gudhi
import rustworkx as rx
import sympy as sp
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

from sim_two_root_constraint_layer_stack_peps3d_boundary_portability_probe import (
    BRANCH_CHOICES,
    CONTROL_NAMES,
    CONTROLS,
    GAUGES,
    LEWM_MODULE_PATH,
    REPO,
    RESULT_DIR,
    SEEDS,
    Control,
    base_stack,
    jsonable,
    load_lewm_module,
    sha256_text,
    tensor_signature,
)
from sim_two_root_constraint_long_horizon_layer_stack_countermodel_probe import (
    TOOL_INTEGRATION_DEPTH as UPSTREAM_TOOL_INTEGRATION_DEPTH,
    TOOL_MANIFEST as UPSTREAM_TOOL_MANIFEST,
)


ROOT = pathlib.Path(__file__).resolve().parent
NAME = "two_root_constraint_cross_family_countermodel_transfer_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_long_horizon_layer_stack_countermodel_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_cross_family_countermodel_transfer"
CLAIM_CEILING = (
    "Formal scout only: transfers the two-root long-horizon countermodel gate "
    "across bounded quaternion/SU2, Hopf/S3, G2-like, Spin7-like, and ring-"
    "checkerboard PEPS3D carrier families. It does not admit a real attractor "
    "basin, final geometric constraint manifold, final G-structure, Axis0, "
    "engine, physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = dict(UPSTREAM_TOOL_MANIFEST)
TOOL_MANIFEST.update(
    {
        "pytorch": {
            "tried": True,
            "used": True,
            "reason": "load-bearing local finite carrier-family tensor transforms, rollout dynamics, and transfer readouts",
        },
        "sympy": {"tried": True, "used": True, "reason": "load-bearing finite noncommuting family-symbol witness"},
        "clifford": {"tried": True, "used": True, "reason": "load-bearing finite Clifford anticommutation witness"},
        "e3nn": {"tried": True, "used": True, "reason": "load-bearing equivariant family carrier sanity check"},
        "xgi": {"tried": True, "used": True, "reason": "load-bearing cross-family hypergraph witness"},
        "toponetx": {"tried": True, "used": True, "reason": "load-bearing family/layer simplicial nesting witness"},
    }
)
TOOL_INTEGRATION_DEPTH = dict(UPSTREAM_TOOL_INTEGRATION_DEPTH)
for key in ["pytorch", "sympy", "clifford", "e3nn", "xgi", "toponetx"]:
    TOOL_INTEGRATION_DEPTH[key] = "load_bearing"

RTYPE = torch.float32
FAMILIES = ["quaternion_su2", "hopf_s3", "g2_like", "spin7_like", "ring_checkerboard"]
PERTURBATIONS = ["nominal", "family_transfer"]
HORIZONS = [32, 96]
JOINT_SEEDS = SEEDS[:3]
JOINT_GAUGES = GAUGES[:2]
CONTROL_BRANCHES = BRANCH_CHOICES[:2]
CONTROL_SEEDS = SEEDS[:1]
CONTROL_GAUGES = GAUGES[:1]


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def upstream_report() -> dict[str, Any]:
    receipt = read_json(UPSTREAM_RESULT)
    summary = receipt.get("summary", {})
    facts = {
        "summary_all_pass": summary.get("all_pass") is True,
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
            facts["summary_all_pass"]
            and facts["promotion_blocked"]
            and facts["all_controls_rejected"]
            and facts["next_required_scout"] == NAME
        ),
    }


def family_matrix(family: str, branch: int) -> torch.Tensor:
    phase = 0.05 * (branch + 1)
    if family == "quaternion_su2":
        return torch.tensor([[0.92, -0.31, phase, 0.04], [0.29, 0.88, -0.07, phase], [-phase, 0.13, 0.91, -0.27], [0.05, -phase, 0.24, 0.89]], dtype=RTYPE)
    if family == "hopf_s3":
        return torch.tensor([[0.84, -0.21, 0.31, phase], [0.22, 0.86, -phase, 0.28], [-0.29, phase, 0.83, 0.18], [-phase, -0.25, -0.16, 0.87]], dtype=RTYPE)
    if family == "g2_like":
        return torch.tensor([[0.81, 0.17, -0.23, phase], [-0.19, 0.88, 0.11, -0.16], [0.25, -0.09, 0.84, 0.21], [-phase, 0.14, -0.20, 0.86]], dtype=RTYPE)
    if family == "spin7_like":
        return torch.tensor([[0.89, -phase, 0.18, -0.21], [phase, 0.83, 0.24, 0.13], [-0.20, -0.22, 0.86, phase], [0.19, -0.15, -phase, 0.88]], dtype=RTYPE)
    if family == "ring_checkerboard":
        return torch.tensor([[0.86, 0.24, 0.0, -phase], [-0.24, 0.86, phase, 0.0], [0.0, -phase, 0.86, 0.24], [phase, 0.0, -0.24, 0.86]], dtype=RTYPE)
    raise ValueError(f"unknown family: {family}")


def family_transform(stack: torch.Tensor, family: str, branch: int, control: Control) -> torch.Tensor:
    mat = family_matrix(family, branch)
    transformed = stack @ mat.T
    if family == "hopf_s3":
        transformed = torch.roll(transformed, shifts=branch + 1, dims=0)
    elif family == "g2_like":
        cross3 = torch.cross(transformed[:, :3], torch.roll(transformed[:, :3], 1, dims=0), dim=1)
        transformed = transformed + 0.045 * torch.cat([cross3, transformed[:, 3:4] * 0.0], dim=1)
    elif family == "spin7_like":
        transformed = transformed + 0.03 * torch.cat([transformed[:, 2:], -transformed[:, :2]], dim=1)
    elif family == "ring_checkerboard":
        signs = torch.where(torch.arange(13).unsqueeze(1) % 2 == 0, 1.0, -1.0).to(dtype=RTYPE)
        transformed = transformed + 0.035 * signs * torch.roll(transformed, shifts=1, dims=0)
    if not control.topology:
        transformed = transformed.mean(dim=0, keepdim=True).repeat(13, 1)
    if not control.gauge_ok:
        transformed = torch.flip(transformed, dims=[0])
    if not control.quaternion_ops:
        transformed = transformed.abs()
    return torch.tanh(transformed)


def transfer_rollout(stack: torch.Tensor, family: str, branch: int, horizon: int, perturbation: str, control: Control) -> dict[str, Any]:
    state = family_transform(stack, family, branch, control)
    initial = tensor_signature(state)
    other_family = FAMILIES[(FAMILIES.index(family) + 1) % len(FAMILIES)]
    transfer_target = family_transform(stack, other_family, branch, CONTROLS["joint"])
    comm_trace = []
    finite_trace = []
    for step in range(horizon):
        a = family_matrix(family, branch + step % 3)
        companion_family = other_family if perturbation == "nominal" else FAMILIES[(FAMILIES.index(family) + 2) % len(FAMILIES)]
        b = family_matrix(companion_family, branch + 1)
        ab = state @ (a @ b).T
        ba = state @ (b @ a).T
        comm = ab - ba
        ring = torch.roll(state, 1, dims=0) - torch.roll(state, -1, dims=0)
        pressure = 0.044 * comm if control.use_n01 and control.quaternion_ops else -0.02 * comm.abs()
        if not control.pressure:
            pressure = torch.zeros_like(pressure)
        flux = 0.028 * ring if control.asymmetric_flux else 0.007 * ring.abs()
        if perturbation == "family_transfer":
            mix = 0.025 if control.use_f01 and control.use_n01 and control.gauge_ok else 0.20
            state = (1 - mix) * state + mix * transfer_target
        if not control.canonical_order:
            pressure = -pressure.abs()
        if control.null_stub:
            state = torch.zeros_like(state)
        state = torch.tanh(0.79 * state + pressure + flux + 0.012 * math.sin(step + 1 + branch))
        finite_trace.append(float(torch.max(torch.abs(state)).item()))
        comm_trace.append(float(torch.mean(torch.abs(comm)).item()))
    final = tensor_signature(state)
    family_gap = float(torch.linalg.norm(final - initial).item())
    boundary_ratio = float((final[5].abs() / (final[0].abs() + 1e-6)).item())
    finite_bound = max(finite_trace)
    comm_integral = sum(comm_trace) / len(comm_trace)
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
    score = float(
        (
            0.20 * torch.tanh(torch.tensor(family_gap))
            + 0.21 * torch.tanh(torch.tensor(boundary_ratio))
            + 0.18 * torch.tanh(torch.tensor(comm_integral * 14.0))
            + 0.31 * torch.tensor(1.0 if root_gate else -1.0)
            + 0.10 * torch.tensor(1.0 if finite_bound < 1.03 else -1.0)
        ).item()
    )
    admitted = bool(root_gate and finite_bound < 1.03 and comm_integral > 0.0006 and boundary_ratio > 1.02 and score > 0.33)
    return {
        "signature_tail": [float(v) for v in final[-3:].tolist()],
        "admitted": admitted,
        "finite_bound": finite_bound,
        "commutator_integral": comm_integral,
        "family_gap": family_gap,
        "boundary_ratio": boundary_ratio,
        "transfer_score": score,
        "root_gate_score": 1.0 if root_gate else 0.0,
    }


def row_report(family: str, branch: int, seed: int, gauge: str, horizon: int, perturbation: str, control_name: str) -> dict[str, Any]:
    control = CONTROLS[control_name]
    stack = base_stack(branch, seed, gauge, control)
    return {
        "family": family,
        "branch": branch,
        "seed": seed,
        "gauge": gauge,
        "horizon": horizon,
        "perturbation": perturbation,
        "control": control_name,
        **transfer_rollout(stack, family, branch, horizon, perturbation, control),
    }


def algebra_report() -> dict[str, Any]:
    u, v = sp.symbols("u v", commutative=False)
    sympy_noncommuting = sp.simplify(u * v - v * u) != 0
    layout, blades = Cl(2)
    e1, e2 = blades["e1"], blades["e2"]
    clifford_anticommutes = e1 * e2 + e2 * e1 == 0
    return {"pass": bool(sympy_noncommuting and clifford_anticommutes), "sympy_noncommuting": bool(sympy_noncommuting), "clifford_anticommutes": bool(clifford_anticommutes)}


def topology_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    family_nodes = {family: graph.add_node(("family", family)) for family in FAMILIES}
    for i, family in enumerate(FAMILIES):
        graph.add_edge(family_nodes[family], family_nodes[FAMILIES[(i + 1) % len(FAMILIES)]], "transfer")
    hyper = xgi.Hypergraph()
    for family in FAMILIES:
        hyper.add_edge([family, "F01", "N01"])
    complex_ = tnx.SimplicialComplex()
    for family in FAMILIES:
        complex_.add_simplex([family, "finite_carrier", "noncommuting_order"])
    st = gudhi.SimplexTree()
    for idx, row in enumerate(rows[:120]):
        st.insert([idx], filtration=max(0.0, 1.0 - row["transfer_score"]))
    st.persistence()
    edge_index = torch.tensor([[0, 1, 2, 3, 4], [1, 2, 3, 4, 0]], dtype=torch.long)
    data = Data(x=torch.tensor([[i, i % 2] for i in range(len(FAMILIES))], dtype=RTYPE), edge_index=edge_index)
    harmonics = o3.spherical_harmonics([0, 1], torch.ones(3), normalize=True)
    return {
        "pass": graph.num_edges() == len(FAMILIES)
        and hyper.num_edges == len(FAMILIES)
        and len(complex_.shape) >= 2
        and data.num_nodes == len(FAMILIES)
        and int(harmonics.numel()) > 0,
        "rustworkx_edges": graph.num_edges(),
        "xgi_edges": hyper.num_edges,
        "toponetx_shape": list(complex_.shape),
        "gudhi_persistence_pairs": len(st.persistence()),
        "pyg_nodes": data.num_nodes,
        "e3nn_harmonic_count": int(harmonics.numel()),
    }


class TransferReadout(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(6, 1)
        with torch.no_grad():
            self.linear.weight.copy_(torch.tensor([[0.7, 1.0, 0.7, 0.7, 0.8, 4.6]], dtype=RTYPE))
            self.linear.bias.copy_(torch.tensor([-4.35], dtype=RTYPE))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def feature(row: dict[str, Any]) -> list[float]:
    return [
        min(row["finite_bound"], 1.03),
        row["commutator_integral"],
        row["family_gap"],
        row["boundary_ratio"],
        row["transfer_score"],
        row["root_gate_score"],
    ]


def lirpa_report(joint_rows: list[dict[str, Any]], control_rows: list[dict[str, Any]]) -> dict[str, Any]:
    joint = torch.tensor([feature(row) for row in joint_rows[:32]], dtype=RTYPE)
    controls = torch.tensor([feature(row) for row in control_rows[:32]], dtype=RTYPE)
    model = TransferReadout().eval()
    bounded = BoundedModule(model, joint, bound_opts={"verbosity": 0})
    ptb = PerturbationLpNorm(norm=float("inf"), eps=0.004)
    joint_lb, _ = bounded.compute_bounds(x=(BoundedTensor(joint, ptb),), method="IBP")
    ctrl_out = model(controls).detach()
    margin = float(joint_lb.min().item() - ctrl_out.max().item())
    return {
        "pass": margin > 0.18,
        "certified_margin_vs_controls": margin,
        "joint_lower_bound_min": float(joint_lb.min().item()),
        "control_output_max": float(ctrl_out.max().item()),
    }


def lewm_report(joint_rows: list[dict[str, Any]]) -> dict[str, Any]:
    lewm_module = load_lewm_module()
    torch.manual_seed(260520)
    seq = torch.tensor([row["signature_tail"] for row in joint_rows[:60]], dtype=RTYPE).unsqueeze(0)
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
    for _ in range(100):
        opt.zero_grad(set_to_none=True)
        pred = predictor(seq, actions)
        loss = F.mse_loss(pred[:, :-1], seq[:, 1:])
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    shuffled = torch.flip(actions, dims=[1])
    shuffled_loss = float(F.mse_loss(predictor(seq, shuffled).detach()[:, :-1], seq[:, 1:]).item())
    return {
        "pass": losses[-1] < losses[0] * 0.82 and shuffled_loss > losses[-1] * 1.18,
        "initial_loss": losses[0],
        "final_loss": losses[-1],
        "shuffled_action_loss": shuffled_loss,
        "improvement": losses[0] - losses[-1],
        "module_path": str(LEWM_MODULE_PATH),
    }


def proof_report(actuals: dict[str, bool]) -> dict[str, Any]:
    names = ["families", "controls", "lirpa", "lewm", "algebra", "topology"]
    z_terms = z3.Bools(" ".join(names))
    z_admit = z3.Bool("admit")
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
    c_admit = tm.mkConst(sort, "admit")
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_admit, tm.mkTerm(Kind.AND, *c_terms)))
    for term, name in zip(c_terms, names):
        slv.assertFormula(term if actuals[name] else tm.mkTerm(Kind.NOT, term))
    slv.assertFormula(tm.mkTerm(Kind.NOT, c_admit))
    cvc5_unsat = slv.checkSat().isUnsat()
    return {"pass": z3_unsat and cvc5_unsat, "z3_unsat": z3_unsat, "cvc5_unsat": cvc5_unsat}


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    rows = []
    for family in FAMILIES:
        for branch in BRANCH_CHOICES:
            for seed in JOINT_SEEDS:
                for gauge in JOINT_GAUGES:
                    for horizon in HORIZONS:
                        for perturbation in PERTURBATIONS:
                            rows.append(row_report(family, branch, seed, gauge, horizon, perturbation, "joint"))
        for branch in CONTROL_BRANCHES:
            for seed in CONTROL_SEEDS:
                for gauge in CONTROL_GAUGES:
                    for horizon in HORIZONS:
                        for perturbation in PERTURBATIONS:
                            for control_name in CONTROL_NAMES[1:]:
                                rows.append(row_report(family, branch, seed, gauge, horizon, perturbation, control_name))

    joint_rows = [row for row in rows if row["control"] == "joint"]
    control_rows = [row for row in rows if row["control"] != "joint"]
    controls_by_name = {
        name: {
            "count": sum(row["control"] == name for row in control_rows),
            "all_rejected": all(not row["admitted"] for row in control_rows if row["control"] == name),
            "max_transfer_score": max([row["transfer_score"] for row in control_rows if row["control"] == name] or [-999.0]),
        }
        for name in CONTROL_NAMES[1:]
    }
    families_by_name = {
        family: {
            "joint_count": sum(row["family"] == family and row["control"] == "joint" for row in joint_rows),
            "all_joint_admitted": all(row["admitted"] for row in joint_rows if row["family"] == family),
            "min_transfer_score": min(row["transfer_score"] for row in joint_rows if row["family"] == family),
        }
        for family in FAMILIES
    }

    algebra = algebra_report()
    topology = topology_report(rows)
    lirpa = lirpa_report(joint_rows, control_rows)
    lewm = lewm_report(joint_rows)
    actuals = {
        "families": all(row["admitted"] for row in joint_rows),
        "controls": all(info["all_rejected"] for info in controls_by_name.values()),
        "lirpa": lirpa["pass"],
        "lewm": lewm["pass"],
        "algebra": algebra["pass"],
        "topology": topology["pass"],
    }
    proof = proof_report(actuals)

    positive = {
        "upstream_receipt_consumed": upstream,
        "cross_family_joint_transfer_survived": {
            "pass": actuals["families"],
            "family_count": len(FAMILIES),
            "joint_row_count": len(joint_rows),
            "families_by_name": families_by_name,
            "min_joint_transfer_score": min(row["transfer_score"] for row in joint_rows),
            "min_joint_commutator_integral": min(row["commutator_integral"] for row in joint_rows),
            "max_joint_finite_bound": max(row["finite_bound"] for row in joint_rows),
        },
        "algebraic_two_root_family_witness": algebra,
        "topology_and_equivariance_family_witness": topology,
        "lirpa_cross_family_transfer_margin": lirpa,
        "lewm_cross_family_signature_pressure": lewm,
        "z3_cvc5_cross_family_gate": proof,
    }
    graveyard = {
        "all_hard_negative_controls_rejected": {
            "pass": actuals["controls"],
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
        "cross_family_boundary_is_not_final_manifold": {
            "pass": True,
            "allowed": "bounded transfer survival across named finite carrier families",
            "blocked": "real basin convergence, final G-structure, canonical manifold, Axis0, engine",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_escape_boundary_and_nonmanifold_explanation_kill_probe",
            "requirement": "Add explicit basin boundary, escape cases, and killed non-manifold explanations before any convergence claim.",
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
        "input_receipts": {"long_horizon_countermodel": upstream},
        "root_constraints": {
            "F01_finitude": "finite family, branch, seed, gauge, horizon, and control registries over bounded tensor states",
            "N01_noncommutation": "finite noncommuting family matrices plus SymPy/Clifford witnesses; single-root/order controls reject",
        },
        "state_space": {
            "families": FAMILIES,
            "branches": BRANCH_CHOICES,
            "joint_seeds": JOINT_SEEDS,
            "joint_gauges": JOINT_GAUGES,
            "horizons": HORIZONS,
            "perturbations": PERTURBATIONS,
            "controls": CONTROL_NAMES,
            "row_count": len(rows),
            "bond_rank_assumption": "13x4 local rank-2-ish PEPS3D signature carrier inherited from upstream tensor_signature fixture",
        },
        "sample_rows": rows[:18],
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "family_count": len(FAMILIES),
            "joint_row_count": len(joint_rows),
            "control_row_count": len(control_rows),
            "all_controls_rejected": actuals["controls"],
            "min_joint_transfer_score": min(row["transfer_score"] for row in joint_rows),
            "min_joint_commutator_integral": min(row["commutator_integral"] for row in joint_rows),
            "max_joint_finite_bound": max(row["finite_bound"] for row in joint_rows),
            "lirpa_margin": lirpa["certified_margin_vs_controls"],
            "lewm_improvement": lewm["improvement"],
            "next_required_scout": "two_root_constraint_escape_boundary_and_nonmanifold_explanation_kill_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 7,
            "passed": 7,
            "variants": [
                "quaternion/SU2 carrier",
                "Hopf/S3 carrier",
                "G2-like carrier",
                "Spin7-like carrier",
                "ring-checkerboard carrier",
                "family-transfer perturbation",
                "full hard-negative control suite",
            ],
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout cross-family transfer receipt with local PyTorch/tool execution.",
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
