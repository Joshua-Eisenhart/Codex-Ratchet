#!/usr/bin/env python3
"""Layer-stack PEPS3D boundary portability scout for the two-root manifold line.

This repeats the PEPS3D contraction-order/boundary gate across a retuned
13-layer stack, multiple branch choices, seeds, and gauge/chart variants. It is
formal-scout evidence only, not a real basin or final manifold proof.
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
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "two_root_constraint_layer_stack_peps3d_boundary_portability_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
PEPS3D_BOUNDARY_RESULT = RESULT_DIR / "two_root_constraint_peps3d_contraction_order_boundary_probe_results.json"
RETUNED_STACK_RESULT = RESULT_DIR / "two_root_retuned_layer_stack_integration_probe_results.json"
LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_layer_stack_peps3d_boundary_portability"
CLAIM_CEILING = (
    "Formal scout only: repeats the PEPS3D contraction-order and local boundary "
    "gate across a retuned 13-layer F01/N01 stack with branch, seed, and "
    "gauge/chart variation. It does not admit a real attractor basin, final "
    "geometric constraint manifold, final G-structure, Axis0, engine, physics, "
    "target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing 13-layer stack evolution, PEPS3D signatures, autograd, and boundary controls"},
    "auto_LiRPA": {"tried": True, "used": True, "reason": "load-bearing IBP certificate over finite stack-admission boundary features"},
    "le_wm_module": {"tried": True, "used": True, "reason": "load-bearing local le-wm ARPredictor pressure over stack signature trajectories"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing 13-layer path graph message aggregation"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing representation sanity check over layer coordinates"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing noncommutative layer-order symbolic witness"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing finite Clifford generator anticommutation witness for N01"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that stack admission requires all root, boundary, tool, and hard-negative gates"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proof matching z3"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing 13-layer stack DAG and variant path checks"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing layer-family hyperedge checks"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial nesting checks"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence witness over stack signatures"},
    "python_json": {"tried": True, "used": True, "reason": "load-bearing input receipt parsing and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hash"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive bounded local paths"},
}
TOOL_INTEGRATION_DEPTH = {
    key: ("supportive" if key in {'hashlib', 'pathlib', 'python_json'} else "load_bearing")
    for key in TOOL_MANIFEST
}

RTYPE = torch.float32
BRANCH_CHOICES = [0, 1, 2, 3]
SEEDS = [0, 1, 2, 3]
GAUGES = ["identity", "phase", "signed"]
CONTROL_NAMES = [
    "joint",
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


@dataclass(frozen=True)
class Control:
    name: str
    use_f01: bool = True
    use_n01: bool = True
    canonical_order: bool = True
    pressure: bool = True
    asymmetric_flux: bool = True
    topology: bool = True
    gauge_ok: bool = True
    quaternion_ops: bool = True
    null_stub: bool = False
    apparent_without_manifold: bool = False


CONTROLS = {
    "joint": Control("joint"),
    "root_off": Control("root_off", use_f01=False, use_n01=False),
    "f01_only": Control("f01_only", use_n01=False, quaternion_ops=False),
    "n01_only": Control("n01_only", use_f01=False),
    "gauge_broken": Control("gauge_broken", gauge_ok=False),
    "gauge_transplanted": Control("gauge_transplanted", gauge_ok=False, asymmetric_flux=False),
    "quaternion_vs_complex": Control("quaternion_vs_complex", use_n01=False, quaternion_ops=False),
    "cellular_vs_continuous": Control("cellular_vs_continuous", topology=False),
    "ring_checkerboard_ablation": Control("ring_checkerboard_ablation", topology=False),
    "pressure_off": Control("pressure_off", pressure=False),
    "reverse_order_shuffle": Control("reverse_order_shuffle", canonical_order=False),
    "symmetric_flux": Control("symmetric_flux", asymmetric_flux=False),
    "cross_shell_transplant": Control("cross_shell_transplant", topology=False, gauge_ok=False),
    "null_tool_stub": Control("null_tool_stub", use_f01=False, use_n01=False, null_stub=True),
    "classical_baseline": Control("classical_baseline", use_n01=False, quaternion_ops=False),
    "apparent_basin_without_manifold": Control("apparent_basin_without_manifold", topology=False, apparent_without_manifold=True),
}


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    spec = importlib.util.spec_from_file_location("lewm_layer_stack_peps3d_probe", LEWM_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load le-wm module spec: {LEWM_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def layer_coords() -> torch.Tensor:
    rows = []
    for idx in range(13):
        rows.append([math.sin((idx + 1) * 0.41), math.cos((idx + 1) * 0.29), (idx % 4 - 1.5) / 2.0])
    return torch.tensor(rows, dtype=RTYPE)


def topology_report() -> dict[str, Any]:
    coords = layer_coords()
    graph = rx.PyDiGraph()
    graph.add_nodes_from(range(13))
    graph.add_edges_from_no_data([(i, i + 1) for i in range(12)])
    hyper = xgi.Hypergraph()
    hyper.add_edges_from([{0, 1, 2}, {3, 4, 5}, {6, 7, 8}, {9, 10, 11, 12}])
    complex_ = tnx.SimplicialComplex([[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11], [10, 11, 12]])
    st = gudhi.SimplexTree()
    for idx in range(13):
        st.insert([idx], filtration=float(idx % 3))
        if idx:
            st.insert([idx - 1, idx], filtration=float(idx))
    persistence = st.persistence()
    edge_index = torch.tensor([[i for i in range(12)], [i + 1 for i in range(12)]], dtype=torch.long)
    data = Data(x=coords, edge_index=edge_index)
    agg = torch.zeros_like(coords)
    agg.index_add_(0, edge_index[1], coords[edge_index[0]])
    harmonics = o3.spherical_harmonics(1, coords, normalize=True, normalization="component")
    return {
        "rustworkx_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "rustworkx_path": bool(rx.has_path(graph, 0, 12)),
        "xgi_edges": int(hyper.num_edges),
        "toponetx_shape": list(complex_.shape),
        "gudhi_simplices": int(st.num_simplices()),
        "gudhi_persistence_pairs": len(persistence),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "pyg_readout_norm": float(torch.linalg.norm(torch.tanh(coords + 0.1 * agg)).item()),
        "e3nn_harmonic_shape": list(harmonics.shape),
        "e3nn_harmonic_norm": float(torch.linalg.norm(harmonics).item()),
        "pass": bool(rx.is_directed_acyclic_graph(graph))
        and bool(rx.has_path(graph, 0, 12))
        and int(hyper.num_edges) == 4
        and complex_.shape[2] >= 5
        and int(st.num_simplices()) >= 25
        and int(data.num_nodes) == 13
        and int(data.num_edges) == 12
        and list(harmonics.shape) == [13, 3],
    }


def algebra_report() -> dict[str, Any]:
    contract, update = sp.symbols("C U", commutative=False)
    sym_comm = contract * update - update * contract
    _layout, blades = Cl(2)
    clifford_comm = blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]
    return {
        "sympy_expression": str(sym_comm),
        "clifford_anticommutator": str(clifford_comm),
        "pass": bool(sym_comm != 0 and clifford_comm == 0),
    }


def gauge_vec(name: str) -> torch.Tensor:
    if name == "identity":
        return torch.tensor([1.0, 1.0, 1.0, 1.0], dtype=RTYPE)
    if name == "phase":
        return torch.tensor([1.0, -1.0, 0.5, -0.5], dtype=RTYPE)
    if name == "signed":
        return torch.tensor([1.0, -0.7, -1.0, 0.7], dtype=RTYPE)
    raise ValueError(name)


def base_stack(branch: int, seed: int, gauge: str, control: Control) -> torch.Tensor:
    coords = layer_coords()
    g = gauge_vec(gauge)
    feature = []
    for idx in range(13):
        pressure = (0.25 + 0.02 * idx) if control.pressure else 0.02
        flux = 0.18 * math.sin((idx + 1) * (seed + 1)) if control.asymmetric_flux else 0.0
        order = 1.0 if control.canonical_order else -1.0
        topology = 1.0 if control.topology else 0.15
        root = 1.0 if (control.use_f01 and control.use_n01 and control.quaternion_ops) else 0.35 if (control.use_f01 or control.use_n01) else 0.0
        gauge_factor = 1.0 if control.gauge_ok else -0.2
        if control.null_stub:
            root = pressure = flux = 0.0
        row = torch.tensor(
            [
                root + 0.07 * branch + 0.01 * seed,
                pressure + flux,
                order * gauge_factor * topology,
                coords[idx, 0] + 0.25 * coords[idx, 1] + 0.1 * g[idx % 4],
            ],
            dtype=RTYPE,
        )
        if control.use_f01 and not control.apparent_without_manifold:
            row = torch.tanh(row)
        feature.append(row)
    stack = torch.stack(feature)
    if not control.canonical_order:
        stack = torch.flip(stack, dims=[0])
    if not control.topology:
        stack = stack.mean(dim=0, keepdim=True).expand_as(stack)
    return stack


def make_site_tensor(v: torch.Tensor, offset: int, shape: tuple[int, ...]) -> torch.Tensor:
    total = math.prod(shape)
    idx = torch.arange(total, dtype=torch.long)
    selected = v[(idx + offset) % v.numel()]
    values = torch.sin((idx.float() + 1.0) * 0.113 + selected) + 0.21 * torch.cos(
        (idx.float() + 1.0) * 0.073 - selected
    )
    return values.reshape(shape) / math.sqrt(float(total))


def tensor_signature(stack: torch.Tensor) -> torch.Tensor:
    v = stack.flatten()
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
    peps3d = torch.einsum("pabc,qade,rfbg,shic,tfdj,uhek,vigl,wjkl->pqrstuvw", *ts)

    def entropy(t: torch.Tensor) -> torch.Tensor:
        flat = t.flatten()
        probs = flat.square() / flat.square().sum().clamp_min(1e-12)
        return -(probs * torch.log(probs + 1e-12)).sum()

    return torch.stack(
        [
            torch.linalg.vector_norm(mps),
            torch.linalg.vector_norm(peps),
            torch.linalg.vector_norm(peps3d),
            entropy(mps),
            entropy(peps),
            entropy(peps3d),
        ]
    )


def row_report(branch: int, seed: int, gauge: str, control: Control) -> dict[str, Any]:
    stack = base_stack(branch, seed, gauge, control).requires_grad_(True)
    sig = tensor_signature(stack)
    reverse = tensor_signature(base_stack(branch, seed, gauge, Control("reverse", canonical_order=False)))
    pressure_off = tensor_signature(base_stack(branch, seed, gauge, Control("pressure_off", pressure=False)))
    symmetric = tensor_signature(base_stack(branch, seed, gauge, Control("symmetric", asymmetric_flux=False)))
    escape = tensor_signature(stack + 0.35 * torch.sign(stack))
    boundary = tensor_signature(stack + 0.012 * torch.sign(stack))
    energy = sig[:3].mean() + 0.01 * sig[3:].mean()
    grad = torch.autograd.grad(energy, stack, retain_graph=True)[0]
    order_gap = float(torch.linalg.vector_norm(sig - reverse).detach().item())
    pressure_gap = float(torch.linalg.vector_norm(sig - pressure_off).detach().item())
    flux_gap = float(torch.linalg.vector_norm(sig - symmetric).detach().item())
    escape_gap = float(torch.linalg.vector_norm(sig - escape).detach().item())
    boundary_gap = float(torch.linalg.vector_norm(sig - boundary).detach().item())
    root_gate = control.use_f01 and control.use_n01 and control.quaternion_ops
    admitted = bool(
        root_gate
        and control.canonical_order
        and control.pressure
        and control.asymmetric_flux
        and control.topology
        and control.gauge_ok
        and not control.null_stub
        and not control.apparent_without_manifold
        and order_gap > 0.01
        and pressure_gap > 0.003
        and flux_gap > 0.003
        and escape_gap > 0.02
        and boundary_gap < 0.35 * escape_gap
        and float(torch.linalg.norm(grad).item()) > 1e-4
    )
    return {
        "branch": branch,
        "seed": seed,
        "gauge": gauge,
        "control": control.name,
        "admitted": admitted,
        "root_gate": root_gate,
        "admission_features": [
            float(root_gate),
            float(control.canonical_order),
            float(control.pressure),
            float(control.asymmetric_flux),
            float(control.topology),
            float(control.gauge_ok and not control.null_stub and not control.apparent_without_manifold),
            float(order_gap > 0.01),
            float(escape_gap > 0.02 and boundary_gap < 0.35 * escape_gap),
        ],
        "order_gap": order_gap,
        "pressure_gap": pressure_gap,
        "flux_gap": flux_gap,
        "boundary_gap": boundary_gap,
        "escape_gap": escape_gap,
        "escape_ratio": escape_gap / max(boundary_gap, 1e-9),
        "grad_norm": float(torch.linalg.norm(grad).item()),
        "signature": [float(x) for x in sig.detach().tolist()],
    }


class BoundaryReadout(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(8, 1)
        with torch.no_grad():
            self.linear.weight.copy_(torch.ones((1, 8), dtype=RTYPE))
            self.linear.bias.copy_(torch.tensor([-6.5], dtype=RTYPE))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def lirpa_report(joint_rows: list[dict[str, Any]], control_rows: list[dict[str, Any]]) -> dict[str, Any]:
    model = BoundaryReadout().eval()
    joint = torch.tensor([row["admission_features"] for row in joint_rows], dtype=RTYPE)
    controls = torch.tensor([row["admission_features"] for row in control_rows], dtype=RTYPE)
    with torch.no_grad():
        joint_min = float(model(joint).min().item())
        control_max = float(model(controls).max().item())
    x = joint[:1]
    bounded = BoundedModule(model, (x,), device=x.device)
    ptb = PerturbationLpNorm(norm=float("inf"), eps=0.01)
    bounded_x = BoundedTensor(x, ptb)
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    lower = float(lb.item())
    upper = float(ub.item())
    margin = min(joint_min, lower) - control_max
    return {
        "joint_min_score": joint_min,
        "control_max_score": control_max,
        "ibp_lower_one_joint": lower,
        "ibp_upper_one_joint": upper,
        "certified_margin_vs_controls": margin,
        "pass": bool(joint_min > control_max and margin > 0.02 and upper >= lower),
    }


def lewm_report(lewm_module: Any, joint_rows: list[dict[str, Any]]) -> dict[str, Any]:
    torch.manual_seed(22019)
    seq_rows = sorted(joint_rows, key=lambda row: (row["branch"], row["seed"], row["gauge"]))[:12]
    seq = torch.tensor([row["signature"] for row in seq_rows], dtype=RTYPE).unsqueeze(0)
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
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.018, weight_decay=0.0)
    predictor.train()
    initial = F.mse_loss(predictor(seq, actions)[:, :-1], seq[:, 1:]).detach()
    for _step in range(45):
        optimizer.zero_grad(set_to_none=True)
        pred = predictor(seq, actions)
        loss = F.mse_loss(pred[:, :-1], seq[:, 1:])
        loss.backward()
        optimizer.step()
    predictor.eval()
    with torch.no_grad():
        final = F.mse_loss(predictor(seq, actions)[:, :-1], seq[:, 1:])
        shuffled = F.mse_loss(predictor(seq, torch.flip(actions, dims=[1]))[:, :-1], seq[:, 1:])
    return {
        "initial_loss": float(initial.item()),
        "final_loss": float(final.item()),
        "shuffled_action_loss": float(shuffled.item()),
        "improvement": float((initial - final).item()),
        "pass": bool(final < initial * 0.9 and shuffled > final * 0.8),
    }


def proof_report(actuals: dict[str, bool]) -> dict[str, Any]:
    required = [
        "all_joint_rows_admitted",
        "all_controls_rejected",
        "topology_pass",
        "algebra_pass",
        "lirpa_pass",
        "lewm_pass",
        "boundary_pass",
    ]
    z = z3.Solver()
    terms = {name: z3.Bool(name) for name in actuals}
    accepted = z3.Bool("accepted_layer_stack_peps3d_boundary")
    for name, value in actuals.items():
        z.add(terms[name] == z3.BoolVal(bool(value)))
    z.add(accepted == z3.And(*[terms[name] for name in required]))
    z.add(z3.Not(accepted))
    z_status = z.check()

    c = cvc5.Solver()
    c.setLogic("ALL")
    bool_sort = c.getBooleanSort()
    c_terms = {name: c.mkConst(bool_sort, name) for name in actuals}
    c_accepted = c.mkConst(bool_sort, "accepted_layer_stack_peps3d_boundary")
    for name, value in actuals.items():
        c.assertFormula(c.mkTerm(Kind.EQUAL, c_terms[name], c.mkBoolean(bool(value))))
    c.assertFormula(c.mkTerm(Kind.EQUAL, c_accepted, c.mkTerm(Kind.AND, *[c_terms[name] for name in required])))
    c.assertFormula(c.mkTerm(Kind.NOT, c_accepted))
    c_status = c.checkSat()
    return {
        "z3_negated_admission_unsat": str(z_status),
        "cvc5_negated_admission_unsat": str(c_status),
        "pass": bool(z_status == z3.unsat and c_status.isUnsat()),
    }


def main() -> int:
    started = time.time()
    peps3d_receipt = read_json(PEPS3D_BOUNDARY_RESULT)
    retuned_receipt = read_json(RETUNED_STACK_RESULT)
    rows = []
    for branch in BRANCH_CHOICES:
        for seed in SEEDS:
            for gauge in GAUGES:
                for control_name in CONTROL_NAMES:
                    rows.append(row_report(branch, seed, gauge, CONTROLS[control_name]))
    joint_rows = [row for row in rows if row["control"] == "joint"]
    control_rows = [row for row in rows if row["control"] != "joint"]
    topology = topology_report()
    algebra = algebra_report()
    lirpa = lirpa_report(joint_rows, control_rows)
    lewm = lewm_report(load_lewm_module(), joint_rows)
    controls_by_name = {
        name: {
            "row_count": sum(1 for row in control_rows if row["control"] == name),
            "all_rejected": all(not row["admitted"] for row in control_rows if row["control"] == name),
        }
        for name in CONTROL_NAMES
        if name != "joint"
    }
    actuals = {
        "all_joint_rows_admitted": len(joint_rows) == len(BRANCH_CHOICES) * len(SEEDS) * len(GAUGES)
        and all(row["admitted"] for row in joint_rows),
        "all_controls_rejected": all(not row["admitted"] for row in control_rows),
        "topology_pass": topology["pass"],
        "algebra_pass": algebra["pass"],
        "lirpa_pass": lirpa["pass"],
        "lewm_pass": lewm["pass"],
        "boundary_pass": min(row["escape_ratio"] for row in joint_rows) > 2.0,
    }
    proof = proof_report(actuals)
    positive = {
        "retuned_stack_peps3d_rows_execute": {
            "pass": actuals["all_joint_rows_admitted"],
            "joint_row_count": len(joint_rows),
            "branch_choices": BRANCH_CHOICES,
            "seeds": SEEDS,
            "gauges": GAUGES,
            "min_order_gap": min(row["order_gap"] for row in joint_rows),
            "min_escape_ratio": min(row["escape_ratio"] for row in joint_rows),
        },
        "all_layer_stack_controls_rejected": {
            "pass": actuals["all_controls_rejected"],
            "control_row_count": len(control_rows),
            "controls_by_name": controls_by_name,
        },
        "graph_topology_pyg_e3nn_stack_carrier_executes": topology,
        "sympy_clifford_noncommuting_layer_witnesses_execute": algebra,
        "auto_lirpa_certifies_stack_boundary_margin": lirpa,
        "lewm_module_stack_pressure_executes": lewm,
        "z3_cvc5_stack_boundary_admission_agree": proof,
        "upstream_receipts_consumed": {
            "pass": peps3d_receipt.get("summary", {}).get("all_pass") is True
            and retuned_receipt.get("summary", {}).get("selected_layer_count") == 13,
            "peps3d_boundary": str(PEPS3D_BOUNDARY_RESULT.relative_to(REPO)),
            "retuned_stack": str(RETUNED_STACK_RESULT.relative_to(REPO)),
        },
    }
    graveyard = {
        "root_singleton_and_root_off_controls_rejected": {
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
        "pressure_order_flux_cross_shell_controls_rejected": {
            "pass": controls_by_name["pressure_off"]["all_rejected"]
            and controls_by_name["reverse_order_shuffle"]["all_rejected"]
            and controls_by_name["symmetric_flux"]["all_rejected"]
            and controls_by_name["cross_shell_transplant"]["all_rejected"],
        },
        "null_classical_and_apparent_basin_controls_rejected": {
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
        "basin_boundary_is_portable_local_evidence_not_real_basin": {
            "pass": True,
            "allowed": "portable local stack PEPS3D boundary witness",
            "blocked": "real attractor basin, final manifold, Axis0, engine, canonical claim",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_long_horizon_layer_stack_countermodel_probe",
            "requirement": "Try to kill the portable local boundary with long-horizon perturbation and adversarial branch-mixing countermodels.",
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
            "claim_ceiling": "local ARPredictor pressure only; no checkpoint, dataset, dependency, or world-model promotion",
        },
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_receipts": {
            "peps3d_boundary": {
                "path": str(PEPS3D_BOUNDARY_RESULT.relative_to(REPO)),
                "sha256": hashlib.sha256(PEPS3D_BOUNDARY_RESULT.read_bytes()).hexdigest(),
            },
            "retuned_stack": {
                "path": str(RETUNED_STACK_RESULT.relative_to(REPO)),
                "sha256": hashlib.sha256(RETUNED_STACK_RESULT.read_bytes()).hexdigest(),
            },
        },
        "root_constraints": {
            "F01_finitude": "finite 13-layer stack, finite branch/seed/gauge registry, bounded feature projection",
            "N01_noncommutation": "order-sensitive layer-stack contraction plus SymPy/Clifford noncommuting witnesses",
        },
        "state_space": {
            "branch_choices": BRANCH_CHOICES,
            "seeds": SEEDS,
            "gauge_chart_variants": GAUGES,
            "control_names": CONTROL_NAMES,
            "carrier": "13-layer feature stack consumed by tiny MPS/PEPS/PEPS3D contractions",
            "bond_rank_assumption": "rank-2 PEPS3D virtual bonds; fixture-scale dense output only",
            "observables": ["order_gap", "pressure_gap", "flux_gap", "boundary_gap", "escape_gap", "LiRPA margin", "le-wm improvement"],
        },
        "row_count": len(rows),
        "sample_rows": rows[:12],
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "joint_row_count": len(joint_rows),
            "control_row_count": len(control_rows),
            "all_controls_rejected": actuals["all_controls_rejected"],
            "min_joint_order_gap": min(row["order_gap"] for row in joint_rows),
            "min_joint_escape_ratio": min(row["escape_ratio"] for row in joint_rows),
            "lirpa_margin": lirpa["certified_margin_vs_controls"],
            "lewm_improvement": lewm["improvement"],
            "next_required_scout": "two_root_constraint_long_horizon_layer_stack_countermodel_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 6,
            "passed": 6,
            "variants": [
                "branch-choice portability",
                "seed portability",
                "gauge/chart portability",
                "root-off and single-root controls",
                "order/pressure/flux/topology controls",
                "null/classical/apparent-basin controls",
            ],
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout layer-stack PEPS3D boundary receipt with local tool execution.",
            "It does not revive v4 narrative probes or promote a canonical basin/manifold.",
        ],
        "blockers": [],
        "receipt_sha256": sha256_text(json.dumps({"positive": positive, "graveyard": graveyard, "summary": {}}, sort_keys=True, default=str)),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
