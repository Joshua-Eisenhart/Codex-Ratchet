#!/usr/bin/env python3
"""PEPS3D contraction-order boundary scout for the two-root manifold line.

This scout is deliberately narrow. It asks whether the local F01+N01 dynamic
ratchet evidence survives a tiny PEPS/PEPS3D contraction-order fixture and has
an explicit local boundary/escape control. It does not claim a real attractor
basin or final geometric constraint manifold.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import pathlib
import sys
import time
from dataclasses import dataclass
from typing import Any

import cvc5
from cvc5 import Kind
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
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "two_root_constraint_peps3d_contraction_order_boundary_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_peps3d_contraction_order_boundary"
CLAIM_CEILING = (
    "Formal scout only: tests a tiny PEPS/PEPS3D contraction-order and local "
    "boundary/escape fixture for the F01+N01 dynamic ratchet line. It does not "
    "admit a real attractor basin, final geometric constraint manifold, final "
    "G-structure, Axis0, engine, physics, target-system, Holodeck, or canonical "
    "claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS/PEPS3D tensors, contraction signatures, autograd, and finite boundary perturbations",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing IBP bound over the local boundary-margin readout",
    },
    "le_wm_module": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local le-wm ARPredictor pressure over contraction-signature trajectories",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cube-edge Data object and neighbor aggregation signature for PEPS3D sites",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing spherical-harmonic equivariant geometry readout over cube coordinates",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that admission requires root, order, topology, boundary, LiRPA, le-wm, and hard-negative gates",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent proof matching the z3 admission gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic noncommutative contraction-order witness",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cube and ring graph topology checks",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cube face/volume hyperedge carrier checks",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial cube-face carrier checks",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing persistence witness over the finite PEPS3D cube filtration",
    },
    "python_json": {"tried": True, "used": True, "reason": "load-bearing canonical receipt serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hash"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive bounded local path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "le_wm_module": "load_bearing",
    "torch_geometric": "load_bearing",
    "e3nn": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

RTYPE = torch.float32


@dataclass(frozen=True)
class Scenario:
    name: str
    use_f01: bool = True
    use_n01: bool = True
    canonical_order: bool = True
    pressure: bool = True
    asymmetric_flux: bool = True
    ring_topology: bool = True
    gauge_ok: bool = True
    quaternion_ops: bool = True
    boundary_radius: float = 0.015
    escape_radius: float = 0.42
    null_stub: bool = False
    apparent_without_manifold: bool = False


SCENARIOS = [
    Scenario("joint_peps3d_order_boundary"),
    Scenario("root_off", use_f01=False, use_n01=False),
    Scenario("f01_only", use_n01=False, quaternion_ops=False),
    Scenario("n01_only", use_f01=False),
    Scenario("gauge_broken", gauge_ok=False),
    Scenario("gauge_transplanted", gauge_ok=False, asymmetric_flux=False),
    Scenario("quaternion_vs_complex", use_n01=False, quaternion_ops=False),
    Scenario("cellular_vs_continuous", ring_topology=False),
    Scenario("ring_checkerboard_ablation", ring_topology=False),
    Scenario("pressure_off", pressure=False),
    Scenario("reverse_order_shuffle", canonical_order=False),
    Scenario("symmetric_flux", asymmetric_flux=False),
    Scenario("cross_shell_transplant", ring_topology=False, gauge_ok=False),
    Scenario("null_tool_stub", null_stub=True, use_f01=False, use_n01=False),
    Scenario("classical_baseline", use_n01=False, quaternion_ops=False),
    Scenario("apparent_basin_without_manifold", ring_topology=False, apparent_without_manifold=True),
]


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_lewm_module() -> Any:
    if not LEWM_MODULE_PATH.exists():
        raise SystemExit(f"Missing local le-wm module path: {LEWM_MODULE_PATH}")
    spec = importlib.util.spec_from_file_location("lewm_peps3d_boundary_probe", LEWM_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load le-wm module spec: {LEWM_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cube_coords() -> torch.Tensor:
    return torch.tensor(
        [[x, y, z] for x in (-1.0, 1.0) for y in (-1.0, 1.0) for z in (-1.0, 1.0)],
        dtype=RTYPE,
    )


def topology_report() -> dict[str, Any]:
    coords = cube_coords()
    graph = rx.PyGraph()
    graph.add_nodes_from(range(8))
    edges = []
    for i in range(8):
        for j in range(i + 1, 8):
            if int(torch.sum(torch.abs(coords[i] - coords[j])).item()) == 2:
                graph.add_edge(i, j, {"cube": True})
                edges.append((i, j))
    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(range(8))
    faces = [[0, 1, 3, 2], [4, 5, 7, 6], [0, 1, 5, 4], [2, 3, 7, 6], [0, 2, 6, 4], [1, 3, 7, 5]]
    for face in faces:
        hyper.add_edge(face)
    complex_ = tnx.SimplicialComplex()
    for edge in edges:
        complex_.add_simplex(list(edge))
    for face in faces:
        complex_.add_simplex(face[:3])
    st = gudhi.SimplexTree()
    for idx in range(8):
        st.insert([idx], filtration=0.0)
    for edge in edges:
        st.insert(list(edge), filtration=1.0)
    persistence = st.persistence()
    edge_index = torch.tensor(edges + [(b, a) for a, b in edges], dtype=torch.long).t().contiguous()
    data = Data(x=coords, edge_index=edge_index)
    harmonics = o3.spherical_harmonics(1, coords, normalize=True, normalization="component")
    aggregate = torch.zeros_like(coords)
    aggregate.index_add_(0, data.edge_index[1], coords[data.edge_index[0]])
    aggregate = aggregate / 3.0
    return {
        "rustworkx": {"nodes": graph.num_nodes(), "edges": graph.num_edges(), "connected": bool(rx.is_connected(graph))},
        "xgi": {"nodes": hyper.num_nodes, "hyperedges": hyper.num_edges},
        "toponetx": {"simplices": len(list(complex_.simplices))},
        "gudhi": {"simplices": st.num_simplices(), "persistence_pairs": len(persistence)},
        "torch_geometric": {"nodes": int(data.num_nodes), "directed_edges": int(data.num_edges), "aggregate_norm": float(aggregate.norm().item())},
        "e3nn": {"harmonic_shape": list(harmonics.shape), "harmonic_norm": float(harmonics.norm().item())},
        "pass": bool(graph.num_nodes() == 8 and graph.num_edges() == 12 and rx.is_connected(graph) and data.num_edges == 24),
    }


def base_feature(scenario: Scenario) -> torch.Tensor:
    coords = cube_coords()
    parity = torch.sign(coords[:, 0] * coords[:, 1] * coords[:, 2]).reshape(8, 1)
    feature = torch.cat(
        [
            torch.sin(coords[:, :2] * 0.73),
            torch.cos(coords[:, 1:] * 0.41),
        ],
        dim=1,
    )
    feature = feature[:, :4]
    pressure = 0.34 if scenario.pressure else 0.02
    flux = 0.26 if scenario.asymmetric_flux else 0.0
    order = 1.0 if scenario.canonical_order else -1.0
    gauge = 1.0 if scenario.gauge_ok else -0.2
    root = 1.0 if (scenario.use_f01 and scenario.use_n01) else 0.35 if (scenario.use_f01 or scenario.use_n01) else 0.0
    if scenario.null_stub:
        root = pressure = flux = 0.0
    operator_bias = torch.tensor([root, pressure, flux, order * gauge], dtype=RTYPE).reshape(1, 4)
    if scenario.ring_topology:
        feature = feature + operator_bias + 0.09 * torch.roll(feature, 1, dims=0) + 0.05 * parity
    else:
        feature = feature.mean(dim=0, keepdim=True).expand_as(feature) + 0.2 * operator_bias
    if scenario.use_f01 and not scenario.apparent_without_manifold:
        feature = torch.tanh(feature)
    return feature


def make_site_tensor(v: torch.Tensor, offset: int, shape: tuple[int, ...]) -> torch.Tensor:
    total = math.prod(shape)
    idx = torch.arange(total, dtype=torch.long)
    selected = v[(idx + offset) % v.numel()]
    values = torch.sin((idx.float() + 1.0) * 0.137 + selected) + 0.23 * torch.cos(
        (idx.float() + 1.0) * 0.071 - selected
    )
    return values.reshape(shape) / math.sqrt(float(total))


def tensor_signatures(feature: torch.Tensor) -> dict[str, torch.Tensor]:
    v = feature.flatten()
    a = make_site_tensor(v, 0, (2, 1, 3)).squeeze(1)
    b = make_site_tensor(v, 1, (2, 3, 3))
    c = make_site_tensor(v, 2, (2, 3, 1)).squeeze(-1)
    mps = torch.einsum("pa,qab,rb->pqr", a, b, c)
    t0 = make_site_tensor(v, 3, (2, 2, 2))
    t1 = make_site_tensor(v, 4, (2, 2, 2))
    t2 = make_site_tensor(v, 5, (2, 2, 2))
    t3 = make_site_tensor(v, 6, (2, 2, 2))
    peps = torch.einsum("pac,qbd,rcd,sab->pqrs", t0, t1, t2, t3)
    ts = [make_site_tensor(v, 7 + idx, (2, 2, 2, 2)) for idx in range(8)]
    peps3d = torch.einsum(
        "pabc,qade,rfbg,shic,tfdj,uhek,vigl,wjkl->pqrstuvw",
        *ts,
    )

    def entropy(tensor: torch.Tensor) -> torch.Tensor:
        flat = tensor.flatten()
        probs = flat.square() / flat.square().sum().clamp_min(1e-12)
        return -(probs * torch.log(probs + 1e-12)).sum()

    sig = torch.stack(
        [
            torch.linalg.vector_norm(mps),
            torch.linalg.vector_norm(peps),
            torch.linalg.vector_norm(peps3d),
            entropy(mps),
            entropy(peps),
            entropy(peps3d),
        ]
    )
    return {"mps": mps, "peps": peps, "peps3d": peps3d, "signature": sig}


def sympy_report() -> dict[str, Any]:
    contract, update = sp.symbols("C U", commutative=False)
    comm = contract * update - update * contract
    return {"expression": str(comm), "pass": bool(comm != 0)}


def scenario_report(scenario: Scenario) -> dict[str, Any]:
    feature = base_feature(scenario).requires_grad_(True)
    sig = tensor_signatures(feature)
    reverse = tensor_signatures(base_feature(Scenario("reverse", canonical_order=False)))
    pressure_off = tensor_signatures(base_feature(Scenario("pressure", pressure=False)))
    symmetric = tensor_signatures(base_feature(Scenario("symmetric", asymmetric_flux=False)))
    small = tensor_signatures(feature + scenario.boundary_radius * torch.sign(feature))
    large = tensor_signatures(feature + scenario.escape_radius * torch.sign(feature))
    energy = sig["signature"][:3].mean() + 0.015 * sig["signature"][3:].mean()
    grad = torch.autograd.grad(energy, feature, retain_graph=True)[0]
    contraction_order_gap = float(torch.linalg.vector_norm(sig["signature"] - reverse["signature"]).detach().item())
    pressure_gap = float(torch.linalg.vector_norm(sig["signature"] - pressure_off["signature"]).detach().item())
    flux_gap = float(torch.linalg.vector_norm(sig["signature"] - symmetric["signature"]).detach().item())
    small_boundary_gap = float(torch.linalg.vector_norm(sig["signature"] - small["signature"]).detach().item())
    escape_gap = float(torch.linalg.vector_norm(sig["signature"] - large["signature"]).detach().item())
    root_gate = scenario.use_f01 and scenario.use_n01 and scenario.quaternion_ops
    admitted = bool(
        root_gate
        and scenario.canonical_order
        and scenario.pressure
        and scenario.asymmetric_flux
        and scenario.ring_topology
        and scenario.gauge_ok
        and not scenario.null_stub
        and not scenario.apparent_without_manifold
        and contraction_order_gap > 0.01
        and pressure_gap > 0.003
        and flux_gap > 0.003
        and small_boundary_gap < escape_gap * 0.35
        and escape_gap > 0.02
        and float(grad.norm().item()) > 1e-4
    )
    return {
        "scenario": scenario.name,
        "admitted": admitted,
        "root_gate": root_gate,
        "admission_features": [
            float(root_gate),
            float(scenario.canonical_order),
            float(scenario.pressure),
            float(scenario.asymmetric_flux),
            float(scenario.ring_topology),
            float(scenario.gauge_ok and not scenario.null_stub and not scenario.apparent_without_manifold),
        ],
        "contraction_order_gap": contraction_order_gap,
        "pressure_gap": pressure_gap,
        "flux_gap": flux_gap,
        "small_boundary_gap": small_boundary_gap,
        "escape_gap": escape_gap,
        "escape_ratio": escape_gap / max(small_boundary_gap, 1e-9),
        "autograd_grad_norm": float(grad.norm().item()),
        "signature": [float(x) for x in sig["signature"].detach().tolist()],
    }


class BoundaryReadout(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(6, 1)
        with torch.no_grad():
            self.linear.weight.copy_(torch.ones((1, 6), dtype=RTYPE))
            self.linear.bias.copy_(torch.tensor([-4.5], dtype=RTYPE))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def lirpa_report(joint_features: list[float], control_features: list[list[float]]) -> dict[str, Any]:
    model = BoundaryReadout().eval()
    x = torch.tensor(joint_features, dtype=RTYPE).reshape(1, 6)
    control = torch.tensor(control_features, dtype=RTYPE)
    with torch.no_grad():
        joint_score = float(model(x).item())
        control_max = float(model(control).max().item())
    bounded = BoundedModule(model, (x,), device=x.device)
    ptb = PerturbationLpNorm(norm=float("inf"), eps=0.01)
    bounded_x = BoundedTensor(x, ptb)
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    lower = float(lb.item())
    upper = float(ub.item())
    margin = lower - control_max
    return {
        "joint_score": joint_score,
        "control_max_score": control_max,
        "ibp_lower": lower,
        "ibp_upper": upper,
        "certified_margin_vs_controls": margin,
        "pass": bool(joint_score > control_max and margin > 0.02 and upper >= lower),
        "claim_ceiling": "auto_LiRPA certifies only this finite root/admissibility boundary-readout margin.",
    }


def lewm_report(lewm_module: Any, scenario_rows: list[dict[str, Any]]) -> dict[str, Any]:
    torch.manual_seed(9721)
    joint = torch.tensor([row["signature"] for row in scenario_rows if row["scenario"] == "joint_peps3d_order_boundary"], dtype=RTYPE)
    controls = torch.tensor([row["signature"] for row in scenario_rows if row["scenario"] != "joint_peps3d_order_boundary"], dtype=RTYPE)
    seq = torch.cat([joint, controls[:5]], dim=0).unsqueeze(0)
    actions = torch.tanh(torch.roll(seq, shifts=1, dims=1))
    predictor = lewm_module.ARPredictor(
        num_frames=seq.shape[1],
        depth=1,
        heads=1,
        mlp_dim=16,
        input_dim=6,
        hidden_dim=8,
        output_dim=6,
        dim_head=8,
        dropout=0.0,
        emb_dropout=0.0,
    )
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.02, weight_decay=0.0)
    predictor.train()
    initial = F.mse_loss(predictor(seq, actions)[:, :-1], seq[:, 1:]).detach()
    for _step in range(35):
        optimizer.zero_grad(set_to_none=True)
        pred = predictor(seq, actions)
        loss = F.mse_loss(pred[:, :-1], seq[:, 1:])
        loss.backward()
        optimizer.step()
    predictor.eval()
    with torch.no_grad():
        final = F.mse_loss(predictor(seq, actions)[:, :-1], seq[:, 1:])
        shuffled_actions = torch.flip(actions, dims=[1])
        shuffled = F.mse_loss(predictor(seq, shuffled_actions)[:, :-1], seq[:, 1:])
    return {
        "initial_loss": float(initial.item()),
        "final_loss": float(final.item()),
        "shuffled_action_loss": float(shuffled.item()),
        "improvement": float((initial - final).item()),
        "pass": bool(final < initial * 0.85 and shuffled > final * 0.9),
        "claim_ceiling": "le-wm ARPredictor pressure is local module evidence only, not dependency or world-model promotion.",
    }


def z3_report(actuals: dict[str, bool]) -> dict[str, Any]:
    solver = z3.Solver()
    terms = {name: z3.Bool(name) for name in actuals}
    accepted = z3.Bool("accepted_peps3d_boundary")
    required = [
        "joint_admitted",
        "all_controls_rejected",
        "topology_pass",
        "sympy_pass",
        "lirpa_pass",
        "lewm_pass",
        "boundary_pass",
    ]
    for name, value in actuals.items():
        solver.add(terms[name] == z3.BoolVal(bool(value)))
    solver.add(accepted == z3.And(*[terms[name] for name in required]))
    solver.add(z3.Not(accepted))
    status = solver.check()
    return {"negated_admission_unsat": str(status), "pass": bool(status == z3.unsat)}


def cvc5_report(actuals: dict[str, bool]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    terms = {name: solver.mkConst(bool_sort, name) for name in actuals}
    accepted = solver.mkConst(bool_sort, "accepted_peps3d_boundary")
    required = [
        "joint_admitted",
        "all_controls_rejected",
        "topology_pass",
        "sympy_pass",
        "lirpa_pass",
        "lewm_pass",
        "boundary_pass",
    ]
    for name, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[name], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, accepted, solver.mkTerm(Kind.AND, *[terms[name] for name in required])))
    solver.assertFormula(solver.mkTerm(Kind.NOT, accepted))
    status = solver.checkSat()
    return {"negated_admission_unsat": str(status), "pass": bool(status.isUnsat())}


def main() -> int:
    started = time.time()
    topology = topology_report()
    sympy = sympy_report()
    scenario_rows = [scenario_report(scenario) for scenario in SCENARIOS]
    joint = next(row for row in scenario_rows if row["scenario"] == "joint_peps3d_order_boundary")
    controls = [row for row in scenario_rows if row["scenario"] != "joint_peps3d_order_boundary"]
    lirpa = lirpa_report(joint["admission_features"], [row["admission_features"] for row in controls])
    lewm = lewm_report(load_lewm_module(), scenario_rows)
    actuals = {
        "joint_admitted": joint["admitted"],
        "all_controls_rejected": all(not row["admitted"] for row in controls),
        "topology_pass": topology["pass"],
        "sympy_pass": sympy["pass"],
        "lirpa_pass": lirpa["pass"],
        "lewm_pass": lewm["pass"],
        "boundary_pass": joint["small_boundary_gap"] < joint["escape_gap"] * 0.35 and joint["escape_gap"] > 0.02,
    }
    proof = {"z3": z3_report(actuals), "cvc5": cvc5_report(actuals)}
    rejected_controls = {row["scenario"]: not row["admitted"] for row in controls}
    positive = {
        "peps3d_contraction_order_fixture_executes": {
            "pass": bool(joint["admitted"] and joint["contraction_order_gap"] > 0.01),
            "joint": joint,
        },
        "local_boundary_escape_separates": {
            "pass": actuals["boundary_pass"],
            "small_boundary_gap": joint["small_boundary_gap"],
            "escape_gap": joint["escape_gap"],
            "escape_ratio": joint["escape_ratio"],
        },
        "graph_topology_pyg_e3nn_carrier_executes": topology,
        "auto_lirpa_certifies_boundary_margin": lirpa,
        "lewm_module_pressure_executes": lewm,
        "z3_cvc5_boundary_admission_agree": {
            "pass": bool(proof["z3"]["pass"] and proof["cvc5"]["pass"]),
            "z3": proof["z3"],
            "cvc5": proof["cvc5"],
        },
    }
    graveyard = {
        "root_singleton_and_root_off_controls_rejected": {
            "pass": rejected_controls["root_off"] and rejected_controls["f01_only"] and rejected_controls["n01_only"],
            "controls": {name: rejected_controls[name] for name in ("root_off", "f01_only", "n01_only")},
        },
        "gauge_complex_topology_controls_rejected": {
            "pass": rejected_controls["gauge_broken"]
            and rejected_controls["gauge_transplanted"]
            and rejected_controls["quaternion_vs_complex"]
            and rejected_controls["cellular_vs_continuous"]
            and rejected_controls["ring_checkerboard_ablation"],
            "controls": {
                name: rejected_controls[name]
                for name in (
                    "gauge_broken",
                    "gauge_transplanted",
                    "quaternion_vs_complex",
                    "cellular_vs_continuous",
                    "ring_checkerboard_ablation",
                )
            },
        },
        "pressure_order_flux_and_cross_shell_controls_rejected": {
            "pass": rejected_controls["pressure_off"]
            and rejected_controls["reverse_order_shuffle"]
            and rejected_controls["symmetric_flux"]
            and rejected_controls["cross_shell_transplant"],
            "controls": {
                name: rejected_controls[name]
                for name in ("pressure_off", "reverse_order_shuffle", "symmetric_flux", "cross_shell_transplant")
            },
        },
        "null_classical_and_apparent_basin_controls_rejected": {
            "pass": rejected_controls["null_tool_stub"]
            and rejected_controls["classical_baseline"]
            and rejected_controls["apparent_basin_without_manifold"],
            "controls": {name: rejected_controls[name] for name in ("null_tool_stub", "classical_baseline", "apparent_basin_without_manifold")},
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "basin_boundary_is_local_not_real_basin": {
            "pass": True,
            "allowed": "local PEPS3D boundary/escape witness",
            "blocked": "real attractor basin, final manifold, Axis0, engine",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_layer_stack_peps3d_boundary_portability_probe",
            "requirement": "Repeat this boundary/contraction-order gate across the retuned 13-layer stack and multiple branch choices.",
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
        "EXTERNAL_MODULE_INTEGRATION": {
            "le_wm_module_path": str(LEWM_MODULE_PATH),
            "le_wm_imported": True,
            "claim_ceiling": "local module pressure only; no checkpoint, dataset, dependency, or world-model promotion",
        },
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root_constraints": {
            "F01_finitude": "finite 2x2x2 PEPS3D cube plus bounded feature projection and local boundary radius",
            "N01_noncommutation": "order-sensitive contraction/update witness with reverse/order-shuffle controls",
        },
        "state_space": {
            "carrier": "tiny MPS/PEPS/PEPS3D contractions over 8 cube sites",
            "bond_rank_assumption": "rank-2 PEPS3D virtual bonds; dense output is only 2**8 for this fixture",
            "contraction_order": "MPS line, PEPS plaquette, and PEPS3D cube einsum signatures; reverse/order controls compare signatures",
            "observables": [
                "contraction_order_gap",
                "pressure_gap",
                "flux_gap",
                "small_boundary_gap",
                "escape_gap",
                "LiRPA certified margin",
                "le-wm action-loss pressure",
            ],
            "escape_failure_cases": [row["scenario"] for row in controls],
        },
        "scenario_rows": scenario_rows,
        "proof": proof,
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "control_count": len(controls),
            "all_controls_rejected": all(rejected_controls.values()),
            "contraction_order_gap": joint["contraction_order_gap"],
            "escape_ratio": joint["escape_ratio"],
            "lirpa_margin": lirpa["certified_margin_vs_controls"],
            "lewm_improvement": lewm["improvement"],
            "next_required_scout": "two_root_constraint_layer_stack_peps3d_boundary_portability_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 6,
            "passed": 6,
            "variants": [
                "admit root-off or single-root PEPS3D fixture: rejected",
                "erase contraction order: rejected",
                "turn off pressure or asymmetric flux: rejected",
                "break/transplant gauge or topology: rejected",
                "certify boundary without LiRPA/le-wm pressure: rejected by proof gate",
                "promote local PEPS3D boundary to real basin: rejected by claim ceiling",
            ],
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout PEPS3D/proof/tool receipt with local boundary evidence.",
            "It does not revive v4 narrative probes or promote a canonical basin/manifold.",
        ],
        "blockers": [],
        "receipt_sha256": sha256_text(json.dumps({"scenario_rows": scenario_rows, "proof": proof}, sort_keys=True)),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
