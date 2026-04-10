#!/usr/bin/env python3
"""
Foundation equivariant graph backprop
====================================

Pure-math foundational lego for graph-structured computation on a basic
quantum object.

What this does:
  - builds two-qubit density matrices
  - lifts each state into a tiny graph with local and bridge nodes
  - trains a graph model with torch autograd as the load-bearing mechanism
  - checks swap symmetry between the two qubits
  - checks that message passing matters by comparing against an edge-removed
    ablation

What it predicts:
  - mutual information
  - coherent information A -> B
  - coherent information B -> A

Notes:
  - Pure math only.
  - This is a foundation lego, not a ranking exercise.
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from torch_geometric.data import Batch, Data
from torch_geometric.nn import GCNConv

torch.manual_seed(7)
np.random.seed(7)

DTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-12


# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing autograd, density-matrix computation, and optimization",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "message passing on a tiny quantum-object graph materially changes the computation",
    },
    "z3": {"tried": False, "used": False, "reason": "not needed for this foundation lego"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this foundation lego"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this foundation lego"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this foundation lego"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this foundation lego"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed; the graph layer is sufficient for this lego"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this foundation lego"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this foundation lego"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this foundation lego"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this foundation lego"},
}


# =====================================================================
# BASIC QUANTUM HELPERS
# =====================================================================


I2 = torch.eye(2, dtype=CDTYPE)
I4 = torch.eye(4, dtype=CDTYPE)
SIGMA_X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
SIGMA_Y = torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=CDTYPE)
SIGMA_Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
BELL_PHI_PLUS = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=CDTYPE) / math.sqrt(2.0)
BELL_PSI_MINUS = torch.tensor([0.0, 1.0, -1.0, 0.0], dtype=CDTYPE) / math.sqrt(2.0)


def _hermitian(rho: torch.Tensor) -> torch.Tensor:
    return 0.5 * (rho + rho.conj().T)


def ensure_density(rho: torch.Tensor) -> torch.Tensor:
    rho = _hermitian(rho.to(CDTYPE))
    evals, evecs = torch.linalg.eigh(rho)
    evals = torch.clamp(evals.real, min=0.0)
    if float(evals.sum().item()) <= 0.0:
        if rho.shape == (4, 4):
            return I4 / 4.0
        return I2 / 2.0
    rho = evecs @ torch.diag((evals / evals.sum()).to(CDTYPE)) @ evecs.conj().T
    return _hermitian(rho)


def pure_density(psi: torch.Tensor) -> torch.Tensor:
    psi = psi.to(CDTYPE).reshape(-1, 1)
    return ensure_density(psi @ psi.conj().T)


def entropy_bits(rho: torch.Tensor) -> torch.Tensor:
    rho = ensure_density(rho)
    evals = torch.linalg.eigvalsh(rho).real
    evals = torch.clamp(evals, min=0.0)
    nz = evals[evals > EPS]
    if nz.numel() == 0:
        return torch.tensor(0.0, dtype=DTYPE)
    return -(nz * torch.log2(nz)).sum().to(DTYPE)


def partial_trace_A(rho_ab: torch.Tensor) -> torch.Tensor:
    rho = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("ijik->jk", rho)


def partial_trace_B(rho_ab: torch.Tensor) -> torch.Tensor:
    rho = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("ijkj->ik", rho)


def mutual_information(rho_ab: torch.Tensor) -> torch.Tensor:
    rho_ab = ensure_density(rho_ab)
    return entropy_bits(partial_trace_A(rho_ab)) + entropy_bits(partial_trace_B(rho_ab)) - entropy_bits(rho_ab)


def coherent_information_a_to_b(rho_ab: torch.Tensor) -> torch.Tensor:
    rho_ab = ensure_density(rho_ab)
    return entropy_bits(partial_trace_B(rho_ab)) - entropy_bits(rho_ab)


def coherent_information_b_to_a(rho_ab: torch.Tensor) -> torch.Tensor:
    rho_ab = ensure_density(rho_ab)
    return entropy_bits(partial_trace_A(rho_ab)) - entropy_bits(rho_ab)


def negativity(rho_ab: torch.Tensor) -> torch.Tensor:
    rho = ensure_density(rho_ab)
    pt = rho.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)
    evals = torch.linalg.eigvalsh(_hermitian(pt)).real
    return torch.clamp((torch.sum(torch.abs(evals)) - 1.0) / 2.0, min=0.0).to(DTYPE)


def purity(rho: torch.Tensor) -> torch.Tensor:
    rho = ensure_density(rho)
    return torch.real(torch.trace(rho @ rho)).to(DTYPE)


def bell_phi_plus() -> torch.Tensor:
    return pure_density(BELL_PHI_PLUS)


def bell_psi_minus() -> torch.Tensor:
    return pure_density(BELL_PSI_MINUS)


def ket1(label: str) -> torch.Tensor:
    if label == "0":
        return torch.tensor([1.0, 0.0], dtype=CDTYPE)
    if label == "1":
        return torch.tensor([0.0, 1.0], dtype=CDTYPE)
    if label == "+":
        return torch.tensor([1.0, 1.0], dtype=CDTYPE) / math.sqrt(2.0)
    if label == "-":
        return torch.tensor([1.0, -1.0], dtype=CDTYPE) / math.sqrt(2.0)
    if label == "i+":
        return torch.tensor([1.0, 1j], dtype=CDTYPE) / math.sqrt(2.0)
    if label == "i-":
        return torch.tensor([1.0, -1j], dtype=CDTYPE) / math.sqrt(2.0)
    raise ValueError(f"unknown single-qubit ket label: {label}")


def ket2(bits: str) -> torch.Tensor:
    if len(bits) == 2 and set(bits) <= {"0", "1"}:
        vec = torch.zeros(4, dtype=CDTYPE)
        vec[int(bits, 2)] = 1.0
        return vec
    raise ValueError(f"unknown two-qubit ket label: {bits}")


def product_state(left: str = "0", right: str = "0") -> torch.Tensor:
    psi = torch.kron(ket1(left), ket1(right))
    return pure_density(psi)


def classical_correlated_state(p: float = 0.7) -> torch.Tensor:
    p = float(np.clip(p, 0.0, 1.0))
    diag = torch.diag(torch.tensor([p, (1.0 - p) / 2.0, (1.0 - p) / 2.0, 0.0], dtype=DTYPE)).to(CDTYPE)
    return ensure_density(diag)


def werner_state(p: float) -> torch.Tensor:
    return ensure_density(p * bell_psi_minus() + (1.0 - p) * I4 / 4.0)


def local_dephase(rho_ab: torch.Tensor, p: float = 0.35, on: str = "A") -> torch.Tensor:
    z = SIGMA_Z
    op = torch.kron(z, I2) if on == "A" else torch.kron(I2, z)
    return ensure_density((1.0 - p) * rho_ab + p * (op @ rho_ab @ op.conj().T))


def asymmetric_mix_state() -> torch.Tensor:
    psi = (ket2("00") + ket2("01")) / math.sqrt(2.0)
    return ensure_density(0.65 * bell_phi_plus() + 0.35 * pure_density(psi))


def swap_qubits(rho_ab: torch.Tensor) -> torch.Tensor:
    return ensure_density(rho_ab.reshape(2, 2, 2, 2).permute(1, 0, 3, 2).reshape(4, 4))


def expectation(rho: torch.Tensor, op: torch.Tensor) -> torch.Tensor:
    return torch.real(torch.trace(ensure_density(rho) @ op)).to(DTYPE)


def local_features(rho_ab: torch.Tensor) -> torch.Tensor:
    rho_a = partial_trace_A(rho_ab)
    rho_b = partial_trace_B(rho_ab)
    a = torch.stack(
        [
            expectation(rho_ab, torch.kron(SIGMA_X, I2)),
            expectation(rho_ab, torch.kron(SIGMA_Y, I2)),
            expectation(rho_ab, torch.kron(SIGMA_Z, I2)),
            purity(rho_a),
            torch.tensor(0.0, dtype=DTYPE),
        ]
    )
    b = torch.stack(
        [
            expectation(rho_ab, torch.kron(I2, SIGMA_X)),
            expectation(rho_ab, torch.kron(I2, SIGMA_Y)),
            expectation(rho_ab, torch.kron(I2, SIGMA_Z)),
            purity(rho_b),
            torch.tensor(0.0, dtype=DTYPE),
        ]
    )
    bridge = torch.stack(
        [
            torch.tensor(0.0, dtype=DTYPE),
            torch.tensor(0.0, dtype=DTYPE),
            torch.tensor(0.0, dtype=DTYPE),
            torch.tensor(0.0, dtype=DTYPE),
            torch.tensor(1.0, dtype=DTYPE),
        ]
    )
    return torch.stack([a, b, bridge], dim=0)


def correlation_strength(rho_ab: torch.Tensor) -> torch.Tensor:
    terms = [
        expectation(rho_ab, torch.kron(pa, pb)).abs()
        for pa in (SIGMA_X, SIGMA_Y, SIGMA_Z)
        for pb in (SIGMA_X, SIGMA_Y, SIGMA_Z)
    ]
    return torch.stack(terms).sum().to(DTYPE)


def edge_weights(rho_ab: torch.Tensor) -> torch.Tensor:
    corr = correlation_strength(rho_ab)
    direct = 1.0 + 0.5 * corr
    bridge = 1.0 + corr
    return torch.stack([bridge, bridge, bridge, bridge, direct, direct]).to(DTYPE)


def global_targets(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.stack(
        [
            mutual_information(rho_ab),
            coherent_information_a_to_b(rho_ab),
            coherent_information_b_to_a(rho_ab),
        ],
        dim=0,
    ).to(DTYPE)


# =====================================================================
# GRAPH BUILDERS
# =====================================================================


EDGE_INDEX_FULL = torch.tensor(
    [
        [0, 2, 2, 1, 0, 1],
        [2, 0, 1, 2, 1, 0],
    ],
    dtype=torch.long,
)
EDGE_INDEX_SELF = torch.empty((2, 0), dtype=torch.long)


def make_graph(rho_ab: torch.Tensor, use_edges: bool = True) -> Data:
    x = local_features(rho_ab).to(DTYPE)
    y = global_targets(rho_ab).to(DTYPE)
    return Data(
        x=x,
        edge_index=EDGE_INDEX_FULL.clone() if use_edges else EDGE_INDEX_SELF.clone(),
        edge_weight=edge_weights(rho_ab) if use_edges else None,
        y=y,
    )


def make_graph_pair(rho_ab: torch.Tensor, use_edges: bool = True) -> Tuple[Data, Data]:
    original = make_graph(rho_ab, use_edges=use_edges)
    swapped = make_graph(swap_qubits(rho_ab), use_edges=use_edges)
    return original, swapped


# =====================================================================
# DATASET
# =====================================================================


def build_state_library() -> List[Tuple[str, torch.Tensor]]:
    return [
        ("product_00", product_state("0", "0")),
        ("product_+-", product_state("+", "-")),
        ("classical_corr_70_30", classical_correlated_state(0.7)),
        ("bell_phi_plus", bell_phi_plus()),
        ("bell_psi_minus", bell_psi_minus()),
        ("werner_0p2", werner_state(0.2)),
        ("werner_0p5", werner_state(0.5)),
        ("werner_0p8", werner_state(0.8)),
        ("dephased_bell_A", local_dephase(bell_phi_plus(), p=0.35, on="A")),
        ("dephased_bell_B", local_dephase(bell_phi_plus(), p=0.35, on="B")),
        ("asymmetric_mix", asymmetric_mix_state()),
    ]


def build_graph_sets(use_edges: bool = True) -> Tuple[List[Data], List[Data]]:
    graphs = []
    swapped = []
    for _, rho in build_state_library():
        g, gs = make_graph_pair(rho, use_edges=use_edges)
        graphs.append(g)
        swapped.append(gs)
    return graphs, swapped


def batch_graphs(graphs: List[Data]) -> Batch:
    return Batch.from_data_list(graphs)


# =====================================================================
# MODEL
# =====================================================================


class EquivariantQuantumGraphNet(nn.Module):
    def __init__(self, in_dim: int = 5, hidden_dim: int = 48, out_dim: int = 3):
        super().__init__()
        self.conv1 = GCNConv(in_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, out_dim),
        )

    def forward(self, data: Batch) -> torch.Tensor:
        x = data.x
        edge_index = data.edge_index
        edge_weight = getattr(data, "edge_weight", None)
        x = self.conv1(x, edge_index, edge_weight)
        x = F.silu(x)
        x = self.conv2(x, edge_index, edge_weight)
        x = F.silu(x)
        x = x.view(data.num_graphs, 3, -1)
        bridge = x[:, 2, :]
        return self.head(bridge)


def train_model(
    model: nn.Module,
    train_graphs: List[Data],
    train_swapped: List[Data],
    epochs: int = 350,
    lr: float = 2e-2,
    symmetry_weight: float = 0.35,
) -> Dict[str, object]:
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    mse = nn.MSELoss()
    curve = []
    batch = batch_graphs(train_graphs)
    batch_swap = batch_graphs(train_swapped)
    target = batch.y.view(-1, 3)
    target_swap = batch_swap.y.view(-1, 3)

    for epoch in range(epochs):
        model.train()
        opt.zero_grad()
        pred = model(batch)
        pred_swap = model(batch_swap)
        equiv_pred = pred[:, [0, 2, 1]]
        loss_data = mse(pred, target) + mse(pred_swap, target_swap)
        loss_sym = mse(pred_swap, equiv_pred)
        loss = loss_data + symmetry_weight * loss_sym
        loss.backward()
        opt.step()
        if epoch in {0, 25, 50, 100, 200, epochs - 1}:
            curve.append(
                {
                    "epoch": int(epoch),
                    "loss": float(loss.item()),
                    "data_loss": float(loss_data.item()),
                    "symmetry_loss": float(loss_sym.item()),
                }
            )

    model.eval()
    with torch.no_grad():
        pred = model(batch)
        pred_swap = model(batch_swap)
        equiv_error = torch.mean(torch.abs(pred_swap - pred[:, [0, 2, 1]])).item()
        train_mae = torch.mean(torch.abs(pred - target)).item()
        swap_mae = torch.mean(torch.abs(pred_swap - target_swap)).item()
        full_loss = mse(pred, target).item() + mse(pred_swap, target_swap).item()
    return {
        "curve": curve,
        "train_mae": float(train_mae),
        "swap_mae": float(swap_mae),
        "equivariance_error": float(equiv_error),
        "final_loss": float(full_loss),
    }


def evaluate_model(model: nn.Module, graphs: List[Data], swapped: List[Data]) -> Dict[str, float]:
    model.eval()
    with torch.no_grad():
        batch = batch_graphs(graphs)
        batch_swap = batch_graphs(swapped)
        pred = model(batch)
        pred_swap = model(batch_swap)
        target = batch.y.view(-1, 3)
        target_swap = batch_swap.y.view(-1, 3)
        mse = torch.mean((pred - target) ** 2).item() + torch.mean((pred_swap - target_swap) ** 2).item()
        mae = torch.mean(torch.abs(pred - target)).item()
        sym = torch.mean(torch.abs(pred_swap - pred[:, [0, 2, 1]])).item()
    return {"mse": float(mse), "mae": float(mae), "swap_error": float(sym)}


# =====================================================================
# AUTOGRAD CHECK
# =====================================================================


def mix_state(t: torch.Tensor) -> torch.Tensor:
    bell = bell_phi_plus()
    classical = classical_correlated_state(0.7)
    return ensure_density((1.0 - t) * classical + t * bell)


def graph_from_mix(t: torch.Tensor, use_edges: bool = True) -> Batch:
    rho = mix_state(t)
    graph = make_graph(rho, use_edges=use_edges)
    return batch_graphs([graph])


def gradient_check(model: nn.Module) -> Dict[str, float]:
    t = torch.tensor(0.37, dtype=DTYPE, requires_grad=True)
    batch = graph_from_mix(t, use_edges=True)
    pred = model(batch)[0, 0]
    grad = torch.autograd.grad(pred, t, create_graph=False)[0]
    eps = 1e-4
    with torch.no_grad():
        p_plus = model(graph_from_mix(torch.tensor(0.37 + eps, dtype=DTYPE), use_edges=True))[0, 0]
        p_minus = model(graph_from_mix(torch.tensor(0.37 - eps, dtype=DTYPE), use_edges=True))[0, 0]
    fd = (p_plus - p_minus) / (2.0 * eps)
    return {
        "autograd": float(grad.item()),
        "finite_difference": float(fd.item()),
        "abs_error": float(abs(grad.item() - fd.item())),
        "nonzero": bool(abs(grad.item()) > 1e-6),
    }


def detached_gradient_check(model: nn.Module) -> Dict[str, float]:
    t = torch.tensor(0.37, dtype=DTYPE, requires_grad=True)
    rho = mix_state(t).detach()
    graph = make_graph(rho, use_edges=True)
    batch = batch_graphs([graph])
    pred = model(batch)[0, 0]
    grad = torch.autograd.grad(pred, t, allow_unused=True)[0]
    value = 0.0 if grad is None else float(grad.item())
    return {"detached_autograd": value, "pass": bool(abs(value) < 1e-12)}


# =====================================================================
# EXACT QUANTUM BOUNDARIES
# =====================================================================


def exact_state_report(rho: torch.Tensor) -> Dict[str, float]:
    return {
        "mutual_information": float(mutual_information(rho).item()),
        "coherent_information_a_to_b": float(coherent_information_a_to_b(rho).item()),
        "coherent_information_b_to_a": float(coherent_information_b_to_a(rho).item()),
        "negativity": float(negativity(rho).item()),
        "purity": float(purity(rho).item()),
    }


def swap_exact_report(rho: torch.Tensor) -> Dict[str, float]:
    sw = swap_qubits(rho)
    return {
        "mutual_information": float(mutual_information(sw).item()),
        "coherent_information_a_to_b": float(coherent_information_a_to_b(sw).item()),
        "coherent_information_b_to_a": float(coherent_information_b_to_a(sw).item()),
        "negativity": float(negativity(sw).item()),
        "purity": float(purity(sw).item()),
        "mi_gap": float(abs(mutual_information(rho) - mutual_information(sw)).item()),
        "ic_swap_gap": float(abs(coherent_information_a_to_b(rho) - coherent_information_b_to_a(sw)).item()),
        "ic_reverse_gap": float(abs(coherent_information_b_to_a(rho) - coherent_information_a_to_b(sw)).item()),
        "pass": bool(
            abs(mutual_information(rho) - mutual_information(sw)).item() < 1e-12
            and abs(coherent_information_a_to_b(rho) - coherent_information_b_to_a(sw)).item() < 1e-12
            and abs(coherent_information_b_to_a(rho) - coherent_information_a_to_b(sw)).item() < 1e-12
        ),
    }


# =====================================================================
# TESTS
# =====================================================================


def run_experiments() -> Dict[str, object]:
    train_graphs, train_swapped = build_graph_sets(use_edges=True)
    ablation_graphs, ablation_swapped = build_graph_sets(use_edges=False)

    model = EquivariantQuantumGraphNet().to(DTYPE)
    full_train = train_model(model, train_graphs, train_swapped)
    full_eval = evaluate_model(model, train_graphs, train_swapped)
    grad_check = gradient_check(model)
    detached_check = detached_gradient_check(model)

    ablation_model = EquivariantQuantumGraphNet().to(DTYPE)
    ablation_train = train_model(ablation_model, ablation_graphs, ablation_swapped)
    ablation_eval = evaluate_model(ablation_model, ablation_graphs, ablation_swapped)

    state_reports = {label: exact_state_report(rho) for label, rho in build_state_library()}
    swap_reports = {label: swap_exact_report(rho) for label, rho in build_state_library()}

    return {
        "full_model": {
            "train": full_train,
            "eval": full_eval,
            "gradient_check": grad_check,
            "detached_check": detached_check,
        },
        "ablation_model": {
            "train": ablation_train,
            "eval": ablation_eval,
        },
        "exact_states": state_reports,
        "swap_reports": swap_reports,
    }


def run_positive_tests(experiments: Dict[str, object]) -> Dict[str, object]:
    full_eval = experiments["full_model"]["eval"]
    full_train = experiments["full_model"]["train"]
    grad = experiments["full_model"]["gradient_check"]
    swap_reports = experiments["swap_reports"]
    state_reports = experiments["exact_states"]

    bell = state_reports["bell_phi_plus"]
    product = state_reports["product_00"]
    asym = swap_reports["asymmetric_mix"]

    return {
        "training_curve": full_train["curve"],
        "model_metrics": full_eval,
        "gradient_check": grad,
        "exact_state_reports": state_reports,
        "exact_swap_reports": swap_reports,
        "exact_checks": {
            "loss_is_small": full_eval["mse"] < 1e-1,
            "swap_error_is_small": full_eval["swap_error"] < 2e-3,
            "autograd_matches_finite_difference": grad["abs_error"] < 5e-3 and grad["nonzero"],
            "product_boundary_is_zero": (
                abs(product["mutual_information"]) < 1e-12
                and abs(product["coherent_information_a_to_b"]) < 1e-12
                and abs(product["coherent_information_b_to_a"]) < 1e-12
                and abs(product["negativity"]) < 1e-12
            ),
            "bell_boundary_hits_expected_values": (
                abs(bell["mutual_information"] - 2.0) < 1e-12
                and abs(bell["coherent_information_a_to_b"] - 1.0) < 1e-12
                and abs(bell["coherent_information_b_to_a"] - 1.0) < 1e-12
                and abs(bell["negativity"] - 0.5) < 1e-12
            ),
            "exact_swap_symmetry_is_respected": asym["pass"],
        },
        "pass": bool(
            full_eval["mse"] < 5e-3
            and full_eval["swap_error"] < 2e-3
            and grad["abs_error"] < 5e-3
            and grad["nonzero"]
            and asym["pass"]
        ),
    }


def run_negative_tests(experiments: Dict[str, object]) -> Dict[str, object]:
    full_eval = experiments["full_model"]["eval"]
    ablation_eval = experiments["ablation_model"]["eval"]
    detached = experiments["full_model"]["detached_check"]

    return {
        "edge_removed_ablation_is_worse": {
            "full_mse": full_eval["mse"],
            "ablation_mse": ablation_eval["mse"],
            "pass": bool(ablation_eval["mse"] > full_eval["mse"] + 5e-2),
        },
        "edge_removed_ablation_collapses_to_trivial_swap_symmetry": {
            "full_swap_error": full_eval["swap_error"],
            "ablation_swap_error": ablation_eval["swap_error"],
            "pass": bool(ablation_eval["swap_error"] < full_eval["swap_error"]),
        },
        "detached_path_breaks_gradient_flow": detached,
        "pass": bool(
            ablation_eval["mse"] > full_eval["mse"] + 5e-2
            and ablation_eval["swap_error"] < full_eval["swap_error"]
            and detached["pass"]
        ),
    }


def run_boundary_tests(experiments: Dict[str, object]) -> Dict[str, object]:
    state_reports = experiments["exact_states"]
    swap_reports = experiments["swap_reports"]
    dephased = state_reports["dephased_bell_A"]
    dephased_swap = swap_reports["dephased_bell_A"]
    asym = state_reports["asymmetric_mix"]
    asym_swap = swap_reports["asymmetric_mix"]

    return {
        "asymmetric_state_has_oriented_cuts": {
            "A_to_B": asym["coherent_information_a_to_b"],
            "B_to_A": asym["coherent_information_b_to_a"],
            "swap_exchanges_oriented_components": bool(
                abs(asym["coherent_information_a_to_b"] - asym_swap["coherent_information_b_to_a"]) < 1e-12
                and abs(asym["coherent_information_b_to_a"] - asym_swap["coherent_information_a_to_b"]) < 1e-12
            ),
            "pass": bool(
                abs(asym["coherent_information_a_to_b"] - asym_swap["coherent_information_b_to_a"]) < 1e-12
                and abs(asym["coherent_information_b_to_a"] - asym_swap["coherent_information_a_to_b"]) < 1e-12
            ),
        },
        "swap_of_dephased_state_preserves_mutual_information": {
            "mi_gap": dephased_swap["mi_gap"],
            "pass": bool(dephased_swap["mi_gap"] < 1e-12),
        },
        "bell_and_product_are_swap_symmetric_boundaries": {
            "product_swap_pass": experiments["swap_reports"]["product_00"]["pass"],
            "bell_swap_pass": experiments["swap_reports"]["bell_phi_plus"]["pass"],
            "pass": bool(
                experiments["swap_reports"]["product_00"]["pass"]
                and experiments["swap_reports"]["bell_phi_plus"]["pass"]
            ),
        },
    }


def count_section(section: Dict[str, object]) -> Dict[str, int]:
    total = 0
    passed = 0
    for value in section.values():
        if isinstance(value, dict) and "pass" in value:
            total += 1
            passed += int(bool(value["pass"]))
    return {"passed": passed, "failed": total - passed, "total": total}


def main() -> Dict[str, object]:
    experiments = run_experiments()
    positive = run_positive_tests(experiments)
    negative = run_negative_tests(experiments)
    boundary = run_boundary_tests(experiments)

    pos = count_section(positive)
    neg = count_section(negative)
    bnd = count_section(boundary)
    total_fail = pos["failed"] + neg["failed"] + bnd["failed"]
    overall_pass = bool(
        total_fail == 0
        and positive.get("pass", True)
        and negative.get("pass", True)
        and boundary.get("pass", True)
    )

    results = {
        "name": "foundation_equivariant_graph_backprop",
        "probe": "pure_math_foundation_equivariant_graph_backprop",
        "purpose": (
            "Train a tiny graph-structured model on a two-qubit density matrix with "
            "autograd central and swap symmetry load-bearing."
        ),
        "schema": "foundation_equivariant_graph_backprop/v1",
        "classification": "canonical" if overall_pass else "exploratory_signal",
        "tool_manifest": TOOL_MANIFEST,
        "tools_used": ["torch", "pyg"],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "tests_total": pos["total"] + neg["total"] + bnd["total"],
            "tests_passed": pos["passed"] + neg["passed"] + bnd["passed"],
            "tests_failed": total_fail,
            "all_pass": overall_pass,
            "elapsed_s": None,
            "full_model_mse": experiments["full_model"]["eval"]["mse"],
            "full_model_swap_error": experiments["full_model"]["eval"]["swap_error"],
            "ablation_mse": experiments["ablation_model"]["eval"]["mse"],
            "ablation_swap_error": experiments["ablation_model"]["eval"]["swap_error"],
        },
        "caveat": (
            "This is a foundation lego only. The graph is intentionally tiny; the point is "
            "to make message passing and autograd materially necessary on a basic quantum object."
        ),
    }
    return results


if __name__ == "__main__":
    t0 = time.time()
    results = main()
    results["summary"]["elapsed_s"] = time.time() - t0
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "foundation_equivariant_graph_backprop_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(json.dumps(results["summary"], indent=2))
    print(f"Results written to {out_path}")
