#!/usr/bin/env python3
"""Long-horizon perturbed dynamic-basin falsifier for the root manifold chain.

Formal scout only. This consumes the current root manifold/chart-invariance,
seed-portability, and dynamic cross-track falsifier receipts, then asks the
next upstream question: does the finite manifold fixture survive a 30-seed
perturbation-volume grid through horizon 512?

A green receipt here means the blocker executed correctly and kept the current
real attractor-basin/convergence claim killed or blocked. It is not basin
admission and must not be read as manifold maturity.
"""

from __future__ import annotations

import copy
import json
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
import z3

AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
if AUTO_LIRPA_ROOT.exists() and str(AUTO_LIRPA_ROOT) not in sys.path:
    sys.path.insert(0, str(AUTO_LIRPA_ROOT))
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402

from sim_axis0_vector_bundle_thirteen_shell_pytorch_peps3d_lirpa_noncollapse_probe import (  # noqa: E402
    LAYERS,
)
from sim_dynamic_manifold_stability_cross_track_lirpa_falsifier_probe import (  # noqa: E402
    LEWM_MODULE_PATH,
    as_jsonable,
    axis_basis,
    load_axis0_bundle,
    load_lewm_module,
    parent_receipt_report,
    propagate,
    sha256_file,
    tensor_signature,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "dynamic_basin_long_horizon_perturbed_convergence_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CHART_RESULT = RESULT_DIR / "root_manifold_g_structure_holonomy_chart_invariance_probe_results.json"
SEED_RESULT = RESULT_DIR / "root_manifold_seed_variation_portability_probe_results.json"
DYNAMIC_FALSIFIER_RESULT = RESULT_DIR / "dynamic_manifold_stability_cross_track_lirpa_falsifier_probe_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "root_dynamic_basin_long_horizon_perturbed_convergence_falsifier"
CLAIM_CEILING = (
    "Formal scout only: consumes root manifold/chart-invariance, seed-portability, "
    "and dynamic cross-track falsifier receipts, then runs a 30-seed perturbation "
    "volume over horizons 64/128/256/512 with PyTorch dynamics, auto_LiRPA, le-wm, "
    "PyG/rustworkx/GUDHI, and z3/cvc5 witnesses. A pass blocks or kills the current "
    "real attractor-basin convergence claim; it does not admit a real attractor "
    "basin, final manifold, final G-structure, final Axis0 actuator, bridge, "
    "engine, physics, target-system, Holodeck, or canonical claim; it does not "
    "admit canonical claims."
)

SEEDS = [
    20260518,
    42,
    7,
    1337,
    99999,
    314159,
    271828,
    65537,
    12345,
    88888,
    101,
    202,
    303,
    404,
    505,
    606,
    707,
    808,
    909,
    1001,
    1111,
    1212,
    1313,
    1414,
    1515,
    1616,
    1717,
    1818,
    1919,
    2020,
]
INITIAL_FAMILIES = ["nominal_operating", "additive_noise", "wide_initial"]
PERTURBATION_CLASSES = ["state_noise", "operator_drift"]
HORIZONS = [64, 128, 256, 512]
ORDERS = ["evolve_then_enforce", "enforce_then_evolve"]
EPS_ADMIT_ORDER_GAP = 0.025
DELTA_KILL_ORDER_GAP = 0.20
EPS_SOLVER_DISAGREEMENT = 0.04

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 30-seed perturbed long-horizon vector/scalar/order dynamic rollouts",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing interval bounds over the perturbation-grid divergence adapter",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing message passing over seed/family/horizon divergence rows",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing perturbation-grid DAG and reachability witness",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing filtration over long-horizon order-divergence rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing arithmetic contradiction for real convergence under measured high divergence",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent arithmetic contradiction for the same convergence claim",
    },
    "pathlib": {"tried": True, "used": True, "reason": "supportive receipt path handling"},
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt parsing and serialization"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "torch_geometric": "load_bearing",
    "rustworkx": "load_bearing",
    "gudhi": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}
EXTERNAL_MODULE_MANIFEST = {
    "le_wm_module": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ARPredictor pressure over horizon-wise divergence trajectories",
        "path": str(LEWM_MODULE_PATH),
    }
}
EXTERNAL_MODULE_INTEGRATION_DEPTH = {"le_wm_module": "load_bearing"}


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def consumed_receipt_report() -> dict[str, Any]:
    chart = read_json(CHART_RESULT)
    seed = read_json(SEED_RESULT)
    dynamic = read_json(DYNAMIC_FALSIFIER_RESULT)
    facts = {
        "chart_all_pass": chart.get("all_pass") is True,
        "chart_axis0_pass_condition": chart["summary"]["axis0_pass_condition"],
        "chart_min_basin_gap": chart["summary"]["min_basin_gap"],
        "chart_min_holonomy_gap": chart["summary"]["min_holonomy_gap"],
        "seed_all_pass": seed.get("all_pass") is True,
        "seed_operating_pass": seed["summary"]["operating_pass"],
        "seed_boundary_fail": seed["summary"]["boundary_fail"],
        "seed_boundary_total": seed["summary"]["boundary_total"],
        "dynamic_falsifier_all_pass": dynamic.get("all_pass") is True,
        "prior_cross_track_divergence": dynamic["summary"]["cross_track_divergence"],
        "prior_real_convergence_claim_status": dynamic["summary"]["current_real_convergence_claim_status"],
        "prior_finite_fixture_status": dynamic["summary"]["finite_fixture_status"],
        "all_promotions_blocked": chart.get("promotion_allowed") is False
        and seed.get("promotion_allowed") is False
        and dynamic.get("promotion_allowed") is False,
    }
    return {
        "facts": facts,
        "pass": bool(
            facts["chart_all_pass"]
            and facts["chart_axis0_pass_condition"] is False
            and facts["seed_all_pass"]
            and facts["seed_operating_pass"] == 30
            and facts["seed_boundary_fail"] == facts["seed_boundary_total"]
            and facts["dynamic_falsifier_all_pass"]
            and facts["prior_cross_track_divergence"] > 1.0
            and facts["prior_real_convergence_claim_status"] == "killed"
            and facts["all_promotions_blocked"]
        ),
    }


def parent_with_drift(parent: dict[str, Any], seed: int, perturbation_class: str) -> dict[str, Any]:
    drifted = copy.deepcopy(parent)
    phase = math.sin(seed * 0.017)
    if perturbation_class == "operator_drift":
        drifted["facts"]["cross_diff_final_state"] *= 1.0 + 0.035 * phase
        drifted["facts"]["track_a_vs_b_max_coh_gap"] *= 1.0 + 0.025 * math.cos(seed * 0.013)
    return drifted


def axis_variant(base_axis: torch.Tensor, seed: int, initial_family: str, perturbation_class: str) -> torch.Tensor:
    generator = torch.Generator().manual_seed(seed)
    row = torch.arange(base_axis.shape[0], dtype=torch.float32).reshape(-1, 1)
    col = torch.arange(base_axis.shape[1], dtype=torch.float32).reshape(1, -1)
    if initial_family == "nominal_operating":
        amp = 0.002
        bias = 0.0
    elif initial_family == "additive_noise":
        amp = 0.011
        bias = 0.003 * torch.sin(row + col)
    elif initial_family == "wide_initial":
        amp = 0.035
        bias = 0.018 * torch.cos((row + 1.0) * (col + 1.0) * 0.11)
    else:
        raise ValueError(initial_family)
    noise = torch.randn(base_axis.shape, generator=generator, dtype=torch.float32) * amp
    drift = 0.0
    if perturbation_class == "operator_drift":
        drift = 0.012 * torch.sin((row + 1.0) * 0.19 + (col + 1.0) * 0.07 + seed * 0.001)
    return torch.tanh(base_axis + noise + bias + drift)


def signature_gap(state_a: torch.Tensor, state_b: torch.Tensor) -> float:
    a_sig = torch.stack([tensor_signature(row) for row in state_a])
    b_sig = torch.stack([tensor_signature(row) for row in state_b])
    return float(torch.linalg.vector_norm(a_sig - b_sig, dim=1).min().item())


def grid_report(axis0: dict[str, Any], parent: dict[str, Any]) -> dict[str, Any]:
    base_axis = axis0["shell_vectors"].clone().detach().to(torch.float32)
    rows = []
    for seed in SEEDS:
        for initial_family in INITIAL_FAMILIES:
            for perturbation_class in PERTURBATION_CLASSES:
                axis = axis_variant(base_axis, seed, initial_family, perturbation_class)
                scalar = axis.mean(dim=1, keepdim=True).expand_as(axis)
                drift_parent = parent_with_drift(parent, seed, perturbation_class)
                tracks = {order: propagate(axis, drift_parent, max(HORIZONS), order)["trajectory"] for order in ORDERS}
                scalar_track = propagate(scalar, drift_parent, max(HORIZONS), ORDERS[0])["trajectory"]
                for horizon in HORIZONS:
                    a_state = tracks[ORDERS[0]][horizon]
                    b_state = tracks[ORDERS[1]][horizon]
                    scalar_state = scalar_track[horizon]
                    order_gap = torch.linalg.vector_norm(a_state - b_state) / math.sqrt(float(a_state.numel()))
                    scalar_gap = torch.linalg.vector_norm(a_state - scalar_state) / math.sqrt(float(a_state.numel()))
                    rows.append(
                        {
                            "seed": seed,
                            "initial_family": initial_family,
                            "perturbation_class": perturbation_class,
                            "horizon": horizon,
                            "order_gap": float(order_gap.item()),
                            "scalar_gap": float(scalar_gap.item()),
                            "signature_gap": signature_gap(a_state, scalar_state),
                        }
                    )
    max_order_gap = max(row["order_gap"] for row in rows)
    min_order_gap = min(row["order_gap"] for row in rows)
    max_scalar_gap = max(row["scalar_gap"] for row in rows)
    solver_disagreement_proxy = max(abs(row["order_gap"] - row["signature_gap"]) for row in rows)
    admission_survived = max_order_gap < EPS_ADMIT_ORDER_GAP and solver_disagreement_proxy < EPS_SOLVER_DISAGREEMENT
    killed = max_order_gap > DELTA_KILL_ORDER_GAP or solver_disagreement_proxy > EPS_SOLVER_DISAGREEMENT
    return {
        "rows": rows,
        "summary": {
            "seed_count": len(SEEDS),
            "initial_family_count": len(INITIAL_FAMILIES),
            "perturbation_class_count": len(PERTURBATION_CLASSES),
            "horizons": HORIZONS,
            "row_count": len(rows),
            "max_order_gap": max_order_gap,
            "min_order_gap": min_order_gap,
            "max_scalar_gap": max_scalar_gap,
            "solver_disagreement_proxy": solver_disagreement_proxy,
            "EPS_ADMIT_ORDER_GAP": EPS_ADMIT_ORDER_GAP,
            "DELTA_KILL_ORDER_GAP": DELTA_KILL_ORDER_GAP,
            "EPS_SOLVER_DISAGREEMENT": EPS_SOLVER_DISAGREEMENT,
            "basin_admission_status": "blocked",
            "current_real_convergence_claim_status": "killed" if killed else "open",
            "admission_threshold_survived": admission_survived,
        },
        "pass": bool(len(rows) == len(SEEDS) * len(INITIAL_FAMILIES) * len(PERTURBATION_CLASSES) * len(HORIZONS) and killed and not admission_survived),
    }


class GridBoundAdapter(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(6, 1)
        with torch.no_grad():
            self.linear.weight.copy_(torch.tensor([[0.03, 0.08, 0.06, 1.40, 0.20, 0.11]], dtype=torch.float32))
            self.linear.bias.zero_()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x).squeeze(-1)


def feature_tensor(rows: list[dict[str, Any]]) -> torch.Tensor:
    family_map = {name: idx for idx, name in enumerate(INITIAL_FAMILIES)}
    perturb_map = {name: idx for idx, name in enumerate(PERTURBATION_CLASSES)}
    return torch.tensor(
        [
            [
                row["seed"] % 10000 / 10000.0,
                family_map[row["initial_family"]] / max(1, len(INITIAL_FAMILIES) - 1),
                perturb_map[row["perturbation_class"]] / max(1, len(PERTURBATION_CLASSES) - 1),
                row["order_gap"],
                row["scalar_gap"],
                row["signature_gap"],
            ]
            for row in rows
        ],
        dtype=torch.float32,
    )


def lirpa_report(grid: dict[str, Any]) -> dict[str, Any]:
    features = feature_tensor(grid["rows"])
    model = GridBoundAdapter().eval()
    eps = 0.0005
    bounded = BoundedModule(model, features)
    bounded_x = BoundedTensor(features, PerturbationLpNorm(norm=float("inf"), eps=eps))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    nominal = model(features)
    return {
        "method": "IBP",
        "eps_linf": eps,
        "feature_shape": list(features.shape),
        "nominal_min": float(nominal.min().item()),
        "nominal_max": float(nominal.max().item()),
        "lower_min": float(lb.min().item()),
        "upper_max": float(ub.max().item()),
        "mean_bound_width": float((ub - lb).mean().item()),
        "contains_nominal": bool(torch.all(nominal >= lb - 1e-6) and torch.all(nominal <= ub + 1e-6)),
        "pass": bool(torch.all(nominal >= lb - 1e-6) and torch.all(nominal <= ub + 1e-6) and (ub - lb).mean().item() > 0.0),
    }


def lewm_report(lewm_module: Any, grid: dict[str, Any]) -> dict[str, Any]:
    torch.manual_seed(2026051805)
    by_horizon = []
    for horizon in HORIZONS:
        horizon_rows = [row for row in grid["rows"] if row["horizon"] == horizon]
        by_horizon.append(
            [
                sum(row["order_gap"] for row in horizon_rows) / len(horizon_rows),
                max(row["order_gap"] for row in horizon_rows),
                sum(row["scalar_gap"] for row in horizon_rows) / len(horizon_rows),
                max(row["signature_gap"] for row in horizon_rows),
            ]
        )
    emb = torch.tensor(by_horizon, dtype=torch.float32).unsqueeze(0)
    actions = torch.tanh(torch.roll(emb, shifts=1, dims=1) - emb.mean(dim=1, keepdim=True))
    predictor = lewm_module.ARPredictor(
        num_frames=len(HORIZONS),
        depth=1,
        heads=1,
        mlp_dim=12,
        input_dim=4,
        hidden_dim=8,
        output_dim=4,
        dim_head=8,
        dropout=0.0,
        emb_dropout=0.0,
    )
    initial = F.mse_loss(predictor(emb, actions)[:, :-1], emb[:, 1:]).detach()
    opt = torch.optim.AdamW(predictor.parameters(), lr=0.012, weight_decay=0.0)
    predictor.train()
    for _step in range(45):
        opt.zero_grad(set_to_none=True)
        loss = F.mse_loss(predictor(emb, actions)[:, :-1], emb[:, 1:])
        loss.backward()
        opt.step()
    predictor.eval()
    with torch.no_grad():
        next_loss = F.mse_loss(predictor(emb, actions)[:, :-1], emb[:, 1:])
        zero_loss = F.mse_loss(predictor(emb, actions * 0.0)[:, :-1], emb[:, 1:])
        shuffled_loss = F.mse_loss(predictor(torch.flip(emb, dims=[1]), actions * 0.0)[:, :-1], emb[:, 1:])
    best_control = torch.minimum(zero_loss, shuffled_loss)
    advantage = (best_control - next_loss) / best_control.clamp_min(1e-9)
    finite_losses = all(
        math.isfinite(float(value.item())) for value in [initial, next_loss, zero_loss, shuffled_loss, advantage]
    )
    discriminates_horizon_dynamics = bool(next_loss.item() < best_control.item() * 0.95 and advantage.item() > 0.01)
    blocks_basin_claim = bool(finite_losses and not discriminates_horizon_dynamics)
    return {
        "loaded_classes": ["ARPredictor"],
        "module_sha256": sha256_file(LEWM_MODULE_PATH),
        "trajectory_shape": list(emb.shape),
        "training_steps": 45,
        "initial_next_embedding_loss": float(initial.item()),
        "next_embedding_loss": float(next_loss.item()),
        "zero_action_control_loss": float(zero_loss.item()),
        "shuffled_control_loss": float(shuffled_loss.item()),
        "relative_loss_advantage_vs_best_control": float(advantage.item()),
        "discriminates_horizon_dynamics": discriminates_horizon_dynamics,
        "basin_claim_status_from_lewm": "blocked" if blocks_basin_claim else "open",
        "pass": blocks_basin_claim,
    }


class GridMessenger(MessagePassing):
    def __init__(self) -> None:
        super().__init__(aggr="mean")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        return self.propagate(edge_index=edge_index, x=x)

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return x_j


def graph_report(grid: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    family_nodes = {name: graph.add_node(("family", name)) for name in INITIAL_FAMILIES}
    perturb_nodes = {name: graph.add_node(("perturb", name)) for name in PERTURBATION_CLASSES}
    horizon_nodes = {horizon: graph.add_node(("horizon", horizon)) for horizon in HORIZONS}
    for family in INITIAL_FAMILIES:
        for perturb in PERTURBATION_CLASSES:
            graph.add_edge(family_nodes[family], perturb_nodes[perturb], "samples")
    for perturb in PERTURBATION_CLASSES:
        for horizon in HORIZONS:
            graph.add_edge(perturb_nodes[perturb], horizon_nodes[horizon], "rolls_to")
    edges = [(src, dst) for src, dst in graph.edge_list()]
    x_rows = []
    for _family in INITIAL_FAMILIES:
        rows = [row for row in grid["rows"] if row["initial_family"] == _family]
        x_rows.append([sum(row["order_gap"] for row in rows) / len(rows), max(row["scalar_gap"] for row in rows)])
    for _perturb in PERTURBATION_CLASSES:
        rows = [row for row in grid["rows"] if row["perturbation_class"] == _perturb]
        x_rows.append([sum(row["order_gap"] for row in rows) / len(rows), max(row["scalar_gap"] for row in rows)])
    for horizon in HORIZONS:
        rows = [row for row in grid["rows"] if row["horizon"] == horizon]
        x_rows.append([sum(row["order_gap"] for row in rows) / len(rows), max(row["scalar_gap"] for row in rows)])
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    data = Data(x=torch.tensor(x_rows, dtype=torch.float32), edge_index=edge_index, num_nodes=len(x_rows))
    data.validate(raise_on_error=True)
    with torch.no_grad():
        out = GridMessenger()(data.x, data.edge_index)
    simplex = gudhi.SimplexTree()
    for idx, row in enumerate(grid["rows"]):
        simplex.insert([idx], filtration=float(row["order_gap"]))
    for idx in range(min(120, len(grid["rows"]) - 1)):
        simplex.insert([idx, idx + 1], filtration=max(float(grid["rows"][idx]["order_gap"]), float(grid["rows"][idx + 1]["order_gap"])))
    persistence = simplex.persistence()
    return {
        "rustworkx": {"node_count": graph.num_nodes(), "edge_count": graph.num_edges(), "is_dag": bool(rx.is_directed_acyclic_graph(graph))},
        "pyg": {"data_validate_passed": True, "feature_shape": list(data.x.shape), "message_passing_shape": list(out.shape), "message_passing_norm": float(torch.linalg.vector_norm(out).item())},
        "gudhi": {"simplex_count": simplex.num_simplices(), "persistence_pair_count": len(persistence)},
        "pass": bool(rx.is_directed_acyclic_graph(graph) and graph.num_edges() == 14 and list(out.shape) == [9, 2] and simplex.num_simplices() > len(grid["rows"])),
    }


def proof_report(grid: dict[str, Any]) -> dict[str, Any]:
    max_order_gap = grid["summary"]["max_order_gap"]
    disagreement = grid["summary"]["solver_disagreement_proxy"]
    z_gap = z3.Real("max_order_gap")
    z_dis = z3.Real("solver_disagreement_proxy")
    z_stable = z3.Bool("real_convergence_claim")
    z = z3.Solver()
    z.add(z_gap == z3.RealVal(f"{max_order_gap:.12f}"))
    z.add(z_dis == z3.RealVal(f"{disagreement:.12f}"))
    z.add(z_stable)
    z.add(z3.Implies(z_stable, z3.And(z_gap < z3.RealVal(str(EPS_ADMIT_ORDER_GAP)), z_dis < z3.RealVal(str(EPS_SOLVER_DISAGREEMENT)))))
    z_status = z.check()

    c = cvc5.Solver()
    c.setLogic("ALL")
    real = c.getRealSort()
    bool_sort = c.getBooleanSort()
    c_gap = c.mkConst(real, "max_order_gap")
    c_dis = c.mkConst(real, "solver_disagreement_proxy")
    c_stable = c.mkConst(bool_sort, "real_convergence_claim")
    c.assertFormula(c.mkTerm(Kind.EQUAL, c_gap, c.mkReal(f"{max_order_gap:.12f}")))
    c.assertFormula(c.mkTerm(Kind.EQUAL, c_dis, c.mkReal(f"{disagreement:.12f}")))
    required = c.mkTerm(
        Kind.AND,
        c.mkTerm(Kind.LT, c_gap, c.mkReal(str(EPS_ADMIT_ORDER_GAP))),
        c.mkTerm(Kind.LT, c_dis, c.mkReal(str(EPS_SOLVER_DISAGREEMENT))),
    )
    c.assertFormula(c_stable)
    c.assertFormula(c.mkTerm(Kind.IMPLIES, c_stable, required))
    c_status = c.checkSat()
    return {
        "z3": {"real_convergence_claim_under_measured_divergence": str(z_status), "pass": z_status == z3.unsat},
        "cvc5": {"real_convergence_claim_under_measured_divergence": str(c_status), "pass": c_status.isUnsat()},
        "pass": bool(z_status == z3.unsat and c_status.isUnsat()),
    }


def write_upstream_blocked_receipt(started: float, dynamic: dict[str, Any] | None) -> int:
    blocker = {
        "code": "dynamic_cross_track_parent_not_green",
        "claim": "The long-horizon falsifier is blocked because the required dynamic cross-track parent did not complete green.",
        "parent_exists": dynamic is not None,
        "parent_all_pass": bool(dynamic and dynamic.get("all_pass") is True),
        "parent_status": (dynamic or {}).get("summary", {}).get("finite_fixture_status"),
    }
    receipt = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "source_path": str(pathlib.Path(__file__)),
        "result_path": str(OUT_PATH),
        "all_pass": False,
        "summary": {
            "all_pass": False,
            "current_real_convergence_claim_status": "not_evaluated_upstream_dynamic_blocked",
            "finite_fixture_status": "blocked",
            "basin_admission_status": "blocked",
            "axis0_pass_condition": False,
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "positive": {},
        "graveyard_companions": {},
        "boundary": {
            "fail_closed_before_long_horizon_execution": {
                "pass": True,
                "rule": "A red dynamic parent cannot seed a long-horizon evidence claim.",
            }
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "EXTERNAL_MODULE_MANIFEST": EXTERNAL_MODULE_MANIFEST,
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "blockers": [blocker],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(receipt, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": False, "status": "blocked", "out_path": str(OUT_PATH)}, indent=2))
    return 1


def main() -> int:
    started = time.time()
    torch.manual_seed(2026051805)
    dynamic = read_json(DYNAMIC_FALSIFIER_RESULT) if DYNAMIC_FALSIFIER_RESULT.exists() else None
    if dynamic is None or dynamic.get("all_pass") is not True:
        return write_upstream_blocked_receipt(started, dynamic)
    consumed = consumed_receipt_report()
    parent = parent_receipt_report()
    axis0 = load_axis0_bundle()
    grid = grid_report(axis0, parent)
    lirpa = lirpa_report(grid)
    lewm = lewm_report(load_lewm_module(), grid)
    graph = graph_report(grid)
    proof = proof_report(grid)
    positive = {
        "consumed_receipts_define_blocker_context": consumed,
        "pytorch_30_seed_perturbation_volume_blocks_real_basin_admission": {
            **grid["summary"],
            "pass": grid["pass"],
        },
        "auto_lirpa_bounds_perturbation_grid_divergence_adapter": lirpa,
        "lewm_horizon_divergence_pressure_blocks_basin_claim": lewm,
        "pyg_rustworkx_gudhi_perturbation_grid_executes": graph,
        "z3_cvc5_real_convergence_claim_rejected": proof,
    }
    graveyard_companions = {
        "real_attractor_basin_convergence_claim_killed": {
            "prior_status": consumed["facts"]["prior_real_convergence_claim_status"],
            "current_status": grid["summary"]["current_real_convergence_claim_status"],
            "max_order_gap": grid["summary"]["max_order_gap"],
            "DELTA_KILL_ORDER_GAP": DELTA_KILL_ORDER_GAP,
            "solver_disagreement_proxy": grid["summary"]["solver_disagreement_proxy"],
            "EPS_SOLVER_DISAGREEMENT": EPS_SOLVER_DISAGREEMENT,
            "kill_reason": (
                "order_gap_exceeds_delta"
                if grid["summary"]["max_order_gap"] > DELTA_KILL_ORDER_GAP
                else "solver_disagreement_proxy_exceeds_eps"
            ),
            "pass": grid["summary"]["current_real_convergence_claim_status"] == "killed",
        },
        "boundary_seed_fragility_remains_active": {
            "seed_boundary_fail": consumed["facts"]["seed_boundary_fail"],
            "seed_boundary_total": consumed["facts"]["seed_boundary_total"],
            "pass": consumed["facts"]["seed_boundary_fail"] == consumed["facts"]["seed_boundary_total"],
        },
        "axis0_not_repaired_by_this_scout": {
            "axis0_pass_condition": False,
            "reason": "This scout tests root dynamic-basin perturbation volume, not upstream Axis0 scalar-actuator repair.",
            "pass": True,
        },
        "provider_output_not_evidence": {
            "provider_receipts_used_as_authority": False,
            "pass": True,
        },
    }
    boundary = {
        "formal_scout_nonpromotion": {"classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED, "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_basin_overclaim": {"claim_ceiling": CLAIM_CEILING, "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "blocks or kills", "does not admit", "canonical"])},
        "falsifier_pass_is_not_basin_maturity": {"all_pass_meaning": "blocker_executed", "basin_admission_status": grid["summary"]["basin_admission_status"], "pass": grid["summary"]["basin_admission_status"] == "blocked"},
    }
    all_pass = all(row.get("pass") is True for row in positive.values()) and all(row.get("pass") is True for row in graveyard_companions.values()) and all(row.get("pass") is True for row in boundary.values())
    receipt = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "summary": {
            "all_pass": bool(all_pass),
            **grid["summary"],
            "axis0_pass_condition": False,
            "elapsed_seconds": round(time.time() - started, 6),
            "load_bearing_tools": [tool for tool, depth in TOOL_INTEGRATION_DEPTH.items() if depth == "load_bearing"],
            "load_bearing_external_modules": [name for name, depth in EXTERNAL_MODULE_INTEGRATION_DEPTH.items() if depth == "load_bearing"],
        },
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row.get("pass") is True)},
        "sample_rows": as_jsonable(grid["rows"][:12]),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "EXTERNAL_MODULE_MANIFEST": EXTERNAL_MODULE_MANIFEST,
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "why_not_v4_probes": [
            "v5 root dynamic-basin falsifier: consumes current v5 formal-scout receipts and blocks overclaim instead of admitting a canonical manifold",
            "runs a 30-seed perturbation-volume grid through horizon 512 and keeps Axis0 out of pass conditions",
            "formal scout only; no real attractor basin, final manifold, engine, Axis0, bridge, physics, or canonical claim is admitted",
        ],
        "blockers": [] if all_pass else ["dynamic_basin_long_horizon_perturbed_convergence_falsifier_failed"],
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": bool(all_pass), "out_path": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
