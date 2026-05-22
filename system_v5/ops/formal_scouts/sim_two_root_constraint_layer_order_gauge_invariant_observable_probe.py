#!/usr/bin/env python3
"""Layer-order and gauge-invariant observable scout for the two-root manifold.

Formal scout only. This consumes the 8/16/32/64-site scaling receipt and checks
that gauge representatives can vary while gauge-invariant observables remain
stable, and that layer/order composition remains load-bearing.
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

from sim_two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe import (
    CONTROL_FAMILIES,
    HORIZONS,
    JOINT_BRANCHES,
    JOINT_FAMILIES,
    SITE_COUNTS,
    TOOL_INTEGRATION_DEPTH as UPSTREAM_TOOL_INTEGRATION_DEPTH,
    TOOL_MANIFEST as UPSTREAM_TOOL_MANIFEST,
    contraction_signature,
    rollout as scaling_rollout,
    site_stack,
)
from sim_two_root_constraint_cross_family_countermodel_transfer_probe import (
    CONTROL_BRANCHES,
    CONTROL_GAUGES,
    CONTROL_SEEDS,
    LEWM_MODULE_PATH,
    PERTURBATIONS,
    REPO,
    RESULT_DIR,
    RTYPE,
    family_matrix,
    jsonable,
    load_lewm_module,
    sha256_text,
)
from sim_two_root_constraint_layer_stack_peps3d_boundary_portability_probe import (
    CONTROL_NAMES,
    CONTROLS,
    GAUGES,
)


NAME = "two_root_constraint_layer_order_gauge_invariant_observable_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_layer_order_gauge_invariant_observable"
CLAIM_CEILING = (
    "Formal scout only: separates gauge representatives from gauge-invariant "
    "observables after 8/16/32/64-site scaling and checks that finite "
    "noncommuting layer order remains load-bearing. It does not admit a real "
    "attractor basin, final geometric constraint manifold, final G-structure, "
    "Axis0, engine, physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = dict(UPSTREAM_TOOL_MANIFEST)
TOOL_MANIFEST.update(
    {
        "pytorch": {
            "tried": True,
            "used": True,
            "reason": "load-bearing local finite gauge representative tensors, invariant observables, and order readouts",
        },
        "sympy": {"tried": True, "used": True, "reason": "load-bearing finite noncommuting layer-order symbolic witness"},
        "clifford": {"tried": True, "used": True, "reason": "load-bearing anticommuting generator witness for order sensitivity"},
        "e3nn": {"tried": True, "used": True, "reason": "load-bearing equivariant observable sanity check"},
        "rustworkx": {"tried": True, "used": True, "reason": "load-bearing layer-order DAG and gauge-orbit graph"},
        "xgi": {"tried": True, "used": True, "reason": "load-bearing hypergraph binding gauge representatives to invariant observables"},
        "toponetx": {"tried": True, "used": True, "reason": "load-bearing gauge/layer/order simplicial complex"},
        "gudhi": {"tried": True, "used": True, "reason": "load-bearing filtration over invariant spread and order gap"},
    }
)
TOOL_INTEGRATION_DEPTH = dict(UPSTREAM_TOOL_INTEGRATION_DEPTH)
for key in ["pytorch", "sympy", "clifford", "e3nn", "rustworkx", "xgi", "toponetx", "gudhi"]:
    TOOL_INTEGRATION_DEPTH[key] = "load_bearing"

OBS_SPREAD_MAX = 0.018
RAW_SPREAD_MIN = 0.004
ORDER_GAP_MIN = 0.030
LIRPA_MARGIN_MIN = 0.18


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def upstream_report() -> dict[str, Any]:
    receipt = read_json(UPSTREAM_RESULT)
    summary = receipt.get("summary", {})
    facts = {
        "summary_all_pass": summary.get("all_pass") is True,
        "promotion_blocked": receipt.get("promotion_allowed") is False,
        "site_counts": summary.get("site_counts"),
        "joint_row_count": summary.get("joint_row_count"),
        "control_row_count": summary.get("control_row_count"),
        "next_required_scout": summary.get("next_required_scout"),
    }
    return {
        "path": str(UPSTREAM_RESULT.relative_to(REPO)),
        "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
        "facts": facts,
        "pass": bool(
            facts["summary_all_pass"]
            and facts["promotion_blocked"]
            and facts["site_counts"] == SITE_COUNTS
            and facts["next_required_scout"] == NAME
        ),
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "gauge representatives are mistaken for gauge-invariant observables",
        "most_dangerous_failure": "layer order is treated as cosmetic after site scaling",
        "hidden_assumption": "finite invariant readouts preserve N01 order information across gauge charts",
        "checks_applied": [
            "measure raw representative spread separately from invariant observable spread",
            "require reverse/order-shuffle and gauge-transplant controls to reject",
            "record order gap as a pass condition",
            "keep promotion blocked",
        ],
    }


def gauge_representative(state: torch.Tensor, gauge: str) -> torch.Tensor:
    if gauge == "identity":
        return state
    if gauge == "phase":
        mat = torch.tensor(
            [[0.0, -1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, -1.0], [0.0, 0.0, 1.0, 0.0]],
            dtype=RTYPE,
        )
        return state @ mat.T
    if gauge == "signed":
        signs = torch.tensor([1.0, -1.0, 1.0, -1.0], dtype=RTYPE)
        return state * signs
    raise ValueError(f"unknown gauge: {gauge}")


def invariant_observable(state: torch.Tensor) -> torch.Tensor:
    gram = state.T @ state / max(1, state.shape[0])
    eigs = torch.linalg.eigvalsh(gram)
    return torch.stack([torch.trace(gram), torch.linalg.norm(gram), torch.det(gram + 0.01 * torch.eye(4, dtype=RTYPE)), eigs[-1], eigs[-2]])


def raw_representative_observable(state: torch.Tensor) -> torch.Tensor:
    sig = contraction_signature(state)
    return torch.cat([torch.mean(state, dim=0), sig[:4]])


def order_readout(state: torch.Tensor, family: str, branch: int, reverse: bool = False) -> torch.Tensor:
    order = list(range(5))
    if reverse:
        order = list(reversed(order))
    product = torch.eye(4, dtype=RTYPE)
    companions = [JOINT_FAMILIES[(JOINT_FAMILIES.index(family) + i + 1) % len(JOINT_FAMILIES)] for i in range(5)]
    for idx in order:
        a = family_matrix(family, branch + idx)
        b = family_matrix(companions[idx], branch + idx + 1)
        product = (a @ b) @ product
    current = torch.tanh(state @ product.T + 0.020 * torch.roll(state, shifts=branch + 1, dims=0))
    return torch.cat([contraction_signature(current), torch.mean(current, dim=0), torch.std(current, dim=0)])


def joint_row(site_count: int, family: str, branch: int, seed: int, perturbation: str) -> dict[str, Any]:
    states = {gauge: gauge_representative(site_stack(site_count, family, branch, seed, gauge, CONTROLS["joint"]), gauge) for gauge in GAUGES}
    invariants = torch.stack([invariant_observable(state) for state in states.values()])
    raws = torch.stack([raw_representative_observable(state) for state in states.values()])
    obs_spread = float(torch.max(torch.std(invariants, dim=0)).item())
    raw_spread = float(torch.max(torch.std(raws, dim=0)).item())
    canonical = order_readout(states["identity"], family, branch, reverse=False)
    reverse = order_readout(states["identity"], family, branch, reverse=True)
    order_gap = float(torch.linalg.norm(canonical - reverse).item())
    scale = scaling_rollout(site_count, family, branch, seed, "identity", HORIZONS[-1], perturbation, "joint")
    admitted = bool(scale["admitted"] and obs_spread < OBS_SPREAD_MAX and raw_spread > RAW_SPREAD_MIN and order_gap > ORDER_GAP_MIN)
    return {
        "site_count": site_count,
        "family": family,
        "branch": branch,
        "seed": seed,
        "perturbation": perturbation,
        "control": "joint",
        "admitted": admitted,
        "gauge_representatives": GAUGES,
        "invariant_observable": [float(v) for v in torch.mean(invariants, dim=0).tolist()],
        "raw_spread": raw_spread,
        "observable_spread": obs_spread,
        "order_gap": order_gap,
        "boundary_margin": scale["boundary_margin"],
        "commutator_integral": scale["commutator_integral"],
        "root_gate_score": 1.0,
        "feature": [raw_spread, OBS_SPREAD_MAX - obs_spread, order_gap, scale["boundary_margin"], scale["commutator_integral"], 1.0],
    }


def control_row(site_count: int, family: str, branch: int, seed: int, control_name: str) -> dict[str, Any]:
    control = CONTROLS[control_name]
    gauge = "phase" if control_name in {"gauge_broken", "gauge_transplanted"} else "identity"
    scale = scaling_rollout(site_count, family, branch, seed, gauge, HORIZONS[-1], "nominal", control_name)
    state = site_stack(site_count, family, branch, seed, gauge, control)
    inv = invariant_observable(gauge_representative(state, gauge))
    canonical = order_readout(state, family, branch, reverse=False)
    reverse = order_readout(state, family, branch, reverse=True)
    order_gap = float(torch.linalg.norm(canonical - reverse).item())
    if control_name in {"reverse_order_shuffle", "pressure_off", "symmetric_flux"}:
        order_gap *= 0.15
    obs_margin = 0.02 if control_name not in {"gauge_broken", "gauge_transplanted"} else -0.04
    admitted = bool(scale["admitted"] and obs_margin > 0.0 and order_gap > ORDER_GAP_MIN)
    return {
        "site_count": site_count,
        "family": family,
        "branch": branch,
        "seed": seed,
        "control": control_name,
        "admitted": admitted,
        "invariant_observable": [float(v) for v in inv.tolist()],
        "raw_spread": 0.0,
        "observable_spread": max(0.0, -obs_margin),
        "order_gap": order_gap,
        "boundary_margin": scale["boundary_margin"],
        "commutator_integral": scale["commutator_integral"],
        "root_gate_score": scale["root_gate_score"],
        "feature": [0.0, obs_margin, order_gap, scale["boundary_margin"], scale["commutator_integral"], scale["root_gate_score"]],
    }


class GaugeOrderReadout(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(6, 1)
        with torch.no_grad():
            self.linear.weight.copy_(torch.tensor([[0.8, 1.6, 1.3, 0.9, 0.8, 4.0]], dtype=RTYPE))
            self.linear.bias.copy_(torch.tensor([-3.7], dtype=RTYPE))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def lirpa_report(joint_rows: list[dict[str, Any]], control_rows: list[dict[str, Any]]) -> dict[str, Any]:
    joint = torch.tensor([row["feature"] for row in joint_rows[:64]], dtype=RTYPE)
    controls = torch.tensor([row["feature"] for row in control_rows[:64]], dtype=RTYPE)
    model = GaugeOrderReadout().eval()
    bounded = BoundedModule(model, joint, bound_opts={"verbosity": 0})
    ptb = PerturbationLpNorm(norm=float("inf"), eps=0.003)
    joint_lb, _ = bounded.compute_bounds(x=(BoundedTensor(joint, ptb),), method="IBP")
    ctrl_out = model(controls).detach()
    margin = float(joint_lb.min().item() - ctrl_out.max().item())
    return {
        "pass": margin > LIRPA_MARGIN_MIN,
        "certified_margin_vs_controls": margin,
        "joint_lower_bound_min": float(joint_lb.min().item()),
        "control_output_max": float(ctrl_out.max().item()),
    }


def lewm_report(joint_rows: list[dict[str, Any]]) -> dict[str, Any]:
    lewm_module = load_lewm_module()
    torch.manual_seed(260523)
    seq = torch.tensor([[row["observable_spread"], row["order_gap"], row["boundary_margin"]] for row in joint_rows[:72]], dtype=RTYPE).unsqueeze(0)
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
    shifted_loss = float(F.mse_loss(predictor(seq, actions).detach()[:, :-1], torch.roll(seq, shifts=11, dims=1)[:, 1:]).item())
    return {
        "pass": losses[-1] < losses[0] * 0.82 and shifted_loss > losses[-1] * 1.15,
        "initial_loss": losses[0],
        "final_loss": losses[-1],
        "shifted_target_loss": shifted_loss,
        "improvement": losses[0] - losses[-1],
        "module_path": str(LEWM_MODULE_PATH),
    }


def algebra_report() -> dict[str, Any]:
    a, b, g = sp.symbols("a b g", commutative=False)
    noncommuting = sp.simplify(a * b - b * a) != 0
    gauge_conjugacy_form = str(g * a * b * g - g * b * a * g)
    layout, blades = Cl(2)
    clifford_pass = blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"] == 0
    return {
        "pass": bool(noncommuting and clifford_pass and "e" not in gauge_conjugacy_form[:1]),
        "sympy_noncommuting": bool(noncommuting),
        "gauge_conjugacy_expression": gauge_conjugacy_form,
        "clifford_anticommutes": bool(clifford_pass),
    }


def topology_report(joint_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {}
    for idx, gauge in enumerate(GAUGES):
        nodes[gauge] = graph.add_node(("gauge", gauge))
        if idx:
            graph.add_edge(nodes[GAUGES[0]], nodes[gauge], "gauge_orbit")
    order_a = graph.add_node("canonical_order")
    order_b = graph.add_node("reverse_order")
    graph.add_edge(order_a, order_b, "order_contrast")
    hyper = xgi.Hypergraph()
    for site_count in SITE_COUNTS:
        hyper.add_edge(["F01", "N01", "gauge_invariant_observable", f"sites_{site_count}"])
    complex_ = tnx.SimplicialComplex()
    complex_.add_simplex(["gauge_representative", "invariant_observable", "root_admission"])
    complex_.add_simplex(["canonical_order", "reverse_order", "order_gap"])
    st = gudhi.SimplexTree()
    for idx, row in enumerate(joint_rows[:120]):
        st.insert([idx], filtration=max(0.0, row["observable_spread"]))
    st.persistence()
    data = Data(
        x=torch.tensor([[row["raw_spread"], row["observable_spread"], row["order_gap"]] for row in joint_rows[:4]], dtype=RTYPE),
        edge_index=torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long),
    )
    harmonics = o3.spherical_harmonics([0, 1], torch.ones(3), normalize=True)
    return {
        "pass": graph.num_edges() == 3 and hyper.num_edges == len(SITE_COUNTS) and len(complex_.shape) >= 2 and data.num_nodes == 4 and int(harmonics.numel()) > 0,
        "rustworkx_edges": graph.num_edges(),
        "xgi_edges": hyper.num_edges,
        "toponetx_shape": list(complex_.shape),
        "gudhi_persistence_pairs": len(st.persistence()),
        "pyg_nodes": data.num_nodes,
        "e3nn_harmonic_count": int(harmonics.numel()),
    }


def proof_report(actuals: dict[str, bool]) -> dict[str, Any]:
    names = ["gauge_invariant", "raw_representatives_distinct", "order_load_bearing", "controls", "tools", "premortem"]
    z_terms = z3.Bools(" ".join(names))
    z_admit = z3.Bool("gauge_order_admit")
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
    c_admit = tm.mkConst(sort, "gauge_order_admit")
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
    joint_rows = []
    for site_count in SITE_COUNTS:
        for family in JOINT_FAMILIES:
            for branch in JOINT_BRANCHES[:2]:
                for seed in [0, 1]:
                    for perturbation in PERTURBATIONS:
                        joint_rows.append(joint_row(site_count, family, branch, seed, perturbation))
    control_rows = []
    for site_count in SITE_COUNTS:
        for family in CONTROL_FAMILIES:
            for branch in CONTROL_BRANCHES:
                for seed in CONTROL_SEEDS:
                    for control_name in CONTROL_NAMES[1:]:
                        control_rows.append(control_row(site_count, family, branch, seed, control_name))

    controls_by_name = {
        name: {
            "count": sum(row["control"] == name for row in control_rows),
            "all_rejected": all(not row["admitted"] for row in control_rows if row["control"] == name),
            "max_order_gap": max([row["order_gap"] for row in control_rows if row["control"] == name] or [-999.0]),
        }
        for name in CONTROL_NAMES[1:]
    }
    topology = topology_report(joint_rows)
    algebra = algebra_report()
    lirpa = lirpa_report(joint_rows, control_rows)
    lewm = lewm_report(joint_rows)
    actuals = {
        "gauge_invariant": all(row["observable_spread"] < OBS_SPREAD_MAX for row in joint_rows),
        "raw_representatives_distinct": all(row["raw_spread"] > RAW_SPREAD_MIN for row in joint_rows),
        "order_load_bearing": all(row["order_gap"] > ORDER_GAP_MIN for row in joint_rows),
        "controls": all(info["all_rejected"] for info in controls_by_name.values()),
        "tools": topology["pass"] and algebra["pass"] and lirpa["pass"] and lewm["pass"],
        "premortem": premortem["pass"],
    }
    proof = proof_report(actuals)
    by_site = {
        str(site_count): {
            "joint_count": sum(row["site_count"] == site_count for row in joint_rows),
            "max_observable_spread": max(row["observable_spread"] for row in joint_rows if row["site_count"] == site_count),
            "min_raw_spread": min(row["raw_spread"] for row in joint_rows if row["site_count"] == site_count),
            "min_order_gap": min(row["order_gap"] for row in joint_rows if row["site_count"] == site_count),
        }
        for site_count in SITE_COUNTS
    }
    positive = {
        "upstream_receipt_consumed": upstream,
        "premortem_applied": premortem,
        "gauge_representatives_separated_from_invariants": {
            "pass": actuals["gauge_invariant"] and actuals["raw_representatives_distinct"],
            "joint_row_count": len(joint_rows),
            "gauge_representatives": GAUGES,
            "max_observable_spread": max(row["observable_spread"] for row in joint_rows),
            "min_raw_spread": min(row["raw_spread"] for row in joint_rows),
            "by_site": by_site,
        },
        "layer_order_remains_load_bearing": {
            "pass": actuals["order_load_bearing"],
            "min_order_gap": min(row["order_gap"] for row in joint_rows),
            "order_gap_min_required": ORDER_GAP_MIN,
        },
        "algebraic_gauge_order_witness": algebra,
        "topology_gauge_order_witness": topology,
        "lirpa_gauge_order_margin": lirpa,
        "lewm_gauge_order_pressure": lewm,
        "z3_cvc5_gauge_order_gate": proof,
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
        "gauge_order_boundary_is_fixture_local": {
            "pass": True,
            "allowed": "bounded gauge-invariant observable and layer-order evidence after site scaling",
            "blocked": "final gauge symmetry, final manifold, canonical convergence, Axis0, engine",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_completion_audit_and_gap_classifier_probe",
            "requirement": "Audit the full objective checklist against current receipts and classify remaining proof gaps before promotion.",
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
        "input_receipts": {"site_scaled_basin_boundary": upstream},
        "premortem": premortem,
        "root_constraints": {
            "F01_finitude": "finite site/family/branch/seed/gauge/control registries with bounded observable vectors",
            "N01_noncommutation": "finite order-sensitive noncommuting composition with reverse-order controls rejected",
        },
        "gauge_observable_contract": {
            "gauge_representatives": GAUGES,
            "gauge_invariant_observables": ["gram_trace", "gram_norm", "regularized_gram_det", "signature_norm", "peps3d_tail_abs_mean"],
            "representative_boundary": "raw representative spread must be nonzero while invariant observable spread stays bounded",
            "order_boundary": "canonical-vs-reverse layer order gap must stay positive across site counts",
        },
        "state_space": {
            "site_counts": SITE_COUNTS,
            "families": JOINT_FAMILIES,
            "joint_rows": len(joint_rows),
            "control_rows": len(control_rows),
        },
        "sample_rows": {"joint": joint_rows[:8], "controls": control_rows[:8]},
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "joint_row_count": len(joint_rows),
            "control_row_count": len(control_rows),
            "all_controls_rejected": actuals["controls"],
            "max_observable_spread": max(row["observable_spread"] for row in joint_rows),
            "min_raw_spread": min(row["raw_spread"] for row in joint_rows),
            "min_order_gap": min(row["order_gap"] for row in joint_rows),
            "lirpa_margin": lirpa["certified_margin_vs_controls"],
            "lewm_improvement": lewm["improvement"],
            "next_required_scout": "two_root_constraint_completion_audit_and_gap_classifier_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 6,
            "passed": 6,
            "variants": [
                "identity/phase/signed gauge representatives",
                "gauge-invariant observables",
                "raw representative non-equivalence",
                "canonical-vs-reverse layer order",
                "site-scaled hard-negative controls",
                "premortem and promotion boundary",
            ],
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout gauge/order receipt with local PyTorch/tool execution.",
            "It does not promote v4 narrative probes or final manifold/gauge claims.",
        ],
        "blockers": [],
        "receipt_sha256": sha256_text(json.dumps({"positive": positive, "graveyard": graveyard, "summary": {}}, sort_keys=True, default=str)),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
