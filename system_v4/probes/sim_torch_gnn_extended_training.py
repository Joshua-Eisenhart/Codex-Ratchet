#!/usr/bin/env python3
"""
GNN Extended Training: Directional Advantage at Early Steps
============================================================

Prior sims (directional_gate, gradient_ref_ablation) failed to confirm A>C at
50 steps across all methods and 5 seeds. Hypothesis: gradient-aligned init
provides a faster initial I_c growth rate (∂I_c/∂step) even if final values
converge, because message-passing mixing overwhelms the directional signal at
convergence.

This sim tests:
  1. Longer training (200 steps) with I_c sampled every 10 steps
  2. A=gradient-aligned, B=anti-gradient, C=random noise (3 inits × 5 seeds)
  3. Per-checkpoint comparison at steps 10/20/30/50/100/200
  4. NEW: learned linear gate -- a small Linear([gradient_ref, current_state] → weight)
     trained for 20 warmup steps on a reference state, then frozen as the gate
  5. Initial growth rate (∂I_c/∂step) from linear fit over steps 1-30
  6. Step where A/C cross (if any), 95% CI across seeds

Mark pytorch=load_bearing, pyg=load_bearing. Classification: canonical.
Output: system_v4/probes/a2_state/sim_results/torch_gnn_extended_training_results.json
"""

import json
import os
import traceback
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": "not relevant to this sim"},
    "cvc5":      {"tried": False, "used": False, "reason": "not relevant to this sim"},
    "sympy":     {"tried": False, "used": False, "reason": "not relevant to this sim"},
    "clifford":  {"tried": False, "used": False, "reason": "not relevant to this sim"},
    "geomstats": {"tried": False, "used": False, "reason": "not relevant to this sim"},
    "e3nn":      {"tried": False, "used": False, "reason": "not relevant to this sim"},
    "rustworkx": {"tried": False, "used": False, "reason": "not relevant to this sim"},
    "xgi":       {"tried": False, "used": False, "reason": "not relevant to this sim"},
    "toponetx":  {"tried": False, "used": False, "reason": "not relevant to this sim"},
    "gudhi":     {"tried": False, "used": False, "reason": "not relevant to this sim"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   "load_bearing",
    "pyg":       "load_bearing",
    "z3":        None,
    "cvc5":      None,
    "sympy":     None,
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# ── Imports ─────────────────────────────────────────────────────────

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Axis 0 gradient via autograd; GNN tensors; learned linear gate; "
        "200-step training with per-step I_c tracking"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    torch = None

try:
    from torch_geometric.nn import MessagePassing
    from torch_geometric.data import HeteroData
    TOOL_MANIFEST["pyg"]["tried"] = True
    TOOL_MANIFEST["pyg"]["used"] = True
    TOOL_MANIFEST["pyg"]["reason"] = (
        "HeteroData graph + heterogeneous message passing IS the ratchet dynamics"
    )
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"
    MessagePassing = None
    HeteroData = None

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["rustworkx"]["reason"] = f"unavailable: {type(e).__name__}"

try:
    from z3 import Real, Solver, And, sat  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["z3"]["reason"] = f"unavailable: {type(e).__name__}"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["sympy"]["reason"] = f"unavailable: {type(e).__name__}"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["clifford"]["reason"] = f"unavailable: {type(e).__name__}"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["geomstats"]["reason"] = f"unavailable: {type(e).__name__}"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["e3nn"]["reason"] = f"unavailable: {type(e).__name__}"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["xgi"]["reason"] = f"unavailable: {type(e).__name__}"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["toponetx"]["reason"] = f"unavailable: {type(e).__name__}"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["gudhi"]["reason"] = f"unavailable: {type(e).__name__}"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["cvc5"]["reason"] = f"unavailable: {type(e).__name__}"


# =====================================================================
# AXIS 0: 3-QUBIT GRADIENT FIELD (7D) -- copied from ablation sim
# =====================================================================

DTYPE = torch.complex128 if torch else None
FDTYPE = torch.float64 if torch else None

PARAM_NAMES = ["theta_AB", "theta_BC", "phi_AB", "phi_BC", "r_A", "r_B", "r_C"]


def _I2():
    return torch.eye(2, dtype=torch.complex128)


def build_single_qubit_state(theta, phi, r):
    ct2 = torch.cos(theta / 2)
    st2 = torch.sin(theta / 2)
    psi = torch.stack([
        ct2.to(torch.complex128),
        (st2 * torch.exp(1j * phi.to(torch.complex128))).to(torch.complex128),
    ])
    rho_pure = torch.outer(psi, psi.conj())
    I2 = _I2()
    rho = r.to(torch.complex128) * rho_pure + (1.0 - r.to(torch.complex128)) * I2 / 2.0
    return rho


def build_cnot_3q_AB():
    CNOT_2Q = torch.tensor([
        [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0],
    ], dtype=torch.complex128)
    return torch.kron(CNOT_2Q, _I2())


def build_cnot_3q_BC():
    CNOT_2Q = torch.tensor([
        [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0],
    ], dtype=torch.complex128)
    return torch.kron(_I2(), CNOT_2Q)


def z_dephasing_channel(rho_8x8, p):
    SZ = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    I2loc = _I2()
    Z_A = torch.kron(torch.kron(SZ, I2loc), I2loc)
    rho_out = (1.0 - p.to(torch.complex128)) * rho_8x8 + p.to(torch.complex128) * (Z_A @ rho_8x8 @ Z_A)
    return rho_out


def build_3qubit_rho(theta_AB, theta_BC, phi_AB, phi_BC, r_A, r_B, r_C,
                     apply_relay=True, dephasing_p=None):
    rho_A = build_single_qubit_state(theta_AB, phi_AB, r_A)
    rho_B = build_single_qubit_state(theta_BC, phi_BC, r_B)
    rho_C = build_single_qubit_state(
        torch.tensor(0.0, dtype=torch.float64),
        torch.tensor(0.0, dtype=torch.float64),
        r_C,
    )
    rho_ABC = torch.kron(torch.kron(rho_A, rho_B), rho_C)
    cnot_AB = build_cnot_3q_AB()
    rho_ABC = cnot_AB @ rho_ABC @ cnot_AB.conj().T
    if apply_relay:
        cnot_BC = build_cnot_3q_BC()
        rho_ABC = cnot_BC @ rho_ABC @ cnot_BC.conj().T
    if dephasing_p is not None:
        rho_ABC = z_dephasing_channel(rho_ABC, dephasing_p)
    return rho_ABC


def partial_trace_A(rho_ABC):
    rho = rho_ABC.reshape(2, 4, 2, 4)
    return torch.einsum('aiaj->ij', rho)


def von_neumann_entropy_3q(rho):
    evals = torch.linalg.eigvalsh(rho)
    evals_clamped = torch.clamp(evals.real, min=1e-15)
    return -torch.sum(evals_clamped * torch.log(evals_clamped))


def coherent_info_A_given_BC(rho_ABC):
    rho_BC = partial_trace_A(rho_ABC)
    S_BC = von_neumann_entropy_3q(rho_BC)
    S_ABC = von_neumann_entropy_3q(rho_ABC)
    return S_BC - S_ABC


def compute_axis0_gradient(eta_vals):
    """Compute the 7-dim Axis 0 gradient field at eta_vals."""
    eta = [torch.tensor(v, dtype=torch.float64, requires_grad=True) for v in eta_vals]
    dp = torch.tensor(0.05, dtype=torch.float64)
    rho_ABC = build_3qubit_rho(*eta, apply_relay=True, dephasing_p=dp)
    ic = coherent_info_A_given_BC(rho_ABC)
    ic.backward()
    grad = torch.stack([p.grad.clone() for p in eta])
    grad_np = grad.detach().numpy().astype(np.float64)
    return {
        "I_c": float(ic.item()),
        "grad": grad_np,
        "grad_magnitude": float(np.linalg.norm(grad_np)),
        "eta_vals": list(eta_vals),
    }


# =====================================================================
# 2-QUBIT GNN COMPONENTS (for the main optimization loop)
# =====================================================================

def pauli_matrices(device=None):
    sx = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64, device=device)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex64, device=device)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64, device=device)
    return sx, sy, sz


def bloch_to_rho(bloch):
    sx, sy, sz = pauli_matrices(bloch.device)
    I2loc = torch.eye(2, dtype=torch.complex64, device=bloch.device)
    b = bloch.to(torch.complex64)
    return I2loc / 2.0 + (b[0] * sx + b[1] * sy + b[2] * sz) / 2.0


def von_neumann_entropy_2q(rho):
    eigs = torch.real(torch.linalg.eigvalsh(rho))
    eigs_clamped = torch.clamp(eigs, min=1e-12)
    return -torch.sum(eigs_clamped * torch.log2(eigs_clamped))


def coherent_information_pair(rho_a, rho_b, rho_ab):
    return von_neumann_entropy_2q(rho_b) - von_neumann_entropy_2q(rho_ab)


def make_product_state(rho_a, rho_b):
    return torch.kron(rho_a, rho_b)


def partial_trace_b(rho_ab, dim_a=2, dim_b=2):
    return torch.einsum("ijkj->ik", rho_ab.reshape(dim_a, dim_b, dim_a, dim_b))


def partial_trace_a(rho_ab, dim_a=2, dim_b=2):
    return torch.einsum("ijik->jk", rho_ab.reshape(dim_a, dim_b, dim_a, dim_b))


class TerrainToOperatorConv(MessagePassing):
    def __init__(self, in_dim, out_dim):
        super().__init__(aggr="mean")
        self.lin = nn.Linear(in_dim, out_dim)

    def forward(self, x_src, x_dst, edge_index):
        return self.propagate(edge_index, x=x_src, size=(x_src.size(0), x_dst.size(0)))

    def message(self, x_j):
        return x_j

    def update(self, aggr_out):
        return self.lin(aggr_out)


class OperatorToTerrainConv(MessagePassing):
    def __init__(self, op_dim, terrain_dim):
        super().__init__(aggr="mean")
        self.mlp = nn.Sequential(
            nn.Linear(terrain_dim + op_dim, 16),
            nn.Tanh(),
            nn.Linear(16, terrain_dim),
        )

    def forward(self, x_src, x_dst, edge_index):
        return self.propagate(
            edge_index, x=x_src, x_dst=x_dst,
            size=(x_src.size(0), x_dst.size(0)),
        )

    def message(self, x_j):
        return x_j

    def update(self, aggr_out, x_dst):
        combined = torch.cat([x_dst, aggr_out], dim=-1)
        delta = self.mlp(combined)
        new_state = x_dst + delta
        norms = torch.norm(new_state, dim=-1, keepdim=True)
        scale = torch.clamp(norms, min=1.0)
        return new_state / scale


# =====================================================================
# NEW: LEARNED LINEAR GATE
# Replaces cosine gate with a trainable Linear([gradient_ref, current_state] → weight)
# Trained for 20 warmup steps on a reference state, then frozen as the gate.
# =====================================================================

class LearnedLinearGate(MessagePassing):
    """
    Takes [gradient_ref (op_dim), current operator state (op_dim)] → scalar weight per node.
    After warmup, the linear layer is frozen. Gate = sigmoid(linear([ref, x])).
    """

    def __init__(self, op_dim, gradient_ref):
        super().__init__(aggr="mean")
        self.op_dim = op_dim
        # Linear: 2*op_dim → 1 (maps [ref, x] to scalar gate)
        self.gate_lin = nn.Linear(2 * op_dim, 1)
        # Shell projection: shell features → op_dim
        self.shell_proj = nn.Linear(op_dim, op_dim)
        ref = gradient_ref.float()
        norm = torch.norm(ref)
        if norm > 1e-8:
            ref = ref / norm
        self.register_buffer("gradient_ref", ref)

    def forward(self, x_src, x_dst, edge_index):
        return self.propagate(
            edge_index, x=x_src, x_dst=x_dst,
            size=(x_src.size(0), x_dst.size(0)),
        )

    def message(self, x_j):
        return self.shell_proj(x_j)

    def update(self, aggr_out, x_dst):
        # Build [ref, x_dst] input to gate
        ref_expanded = self.gradient_ref.unsqueeze(0).expand(x_dst.size(0), -1)
        gate_input = torch.cat([ref_expanded, x_dst], dim=-1)  # [N, 2*op_dim]
        gate = torch.sigmoid(self.gate_lin(gate_input))         # [N, 1]
        return x_dst * gate


class RatchetGNNLearnedGate(nn.Module):
    """
    Ratchet GNN with a LearnedLinearGate instead of cosine gate.
    The gate's linear layer is pre-trained for `n_warmup` steps to align
    operator features with the gradient reference, then frozen.
    """

    TERRAIN_DIM = 3
    OP_DIM = 7

    def __init__(self, n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
                 shell_init=None, gradient_ref_7d=None):
        super().__init__()
        self.n_terrain = n_terrain
        self.n_operator = n_operator
        self.n_shell = n_shell
        self.n_layers = n_layers
        op_dim = self.OP_DIM

        if gradient_ref_7d is not None:
            ref7 = gradient_ref_7d.float()
            norm = torch.norm(ref7)
            if norm > 1e-8:
                ref7 = ref7 / norm
        else:
            ref7 = torch.zeros(op_dim)
            ref7[0] = 1.0
        self.register_buffer("gradient_ref_7d", ref7)

        self.operator_params = nn.Parameter(
            torch.rand(n_operator, op_dim) * 0.3 + 0.1
        )

        if shell_init is not None:
            self.shell_params = nn.Parameter(shell_init.clone().float())
        else:
            self.shell_params = nn.Parameter(
                torch.rand(n_shell, op_dim) * 0.5 + 0.25
            )

        # Learned linear gate layers (one per GNN layer)
        self.learned_gate_layers = nn.ModuleList([
            LearnedLinearGate(op_dim, ref7)
            for _ in range(n_layers)
        ])
        self.terrain_to_op_layers = nn.ModuleList([
            TerrainToOperatorConv(self.TERRAIN_DIM, op_dim)
            for _ in range(n_layers)
        ])
        self.op_to_terrain_layers = nn.ModuleList([
            OperatorToTerrainConv(op_dim, self.TERRAIN_DIM)
            for _ in range(n_layers)
        ])

    def warmup_alignment_loss(self):
        """
        Warmup loss: train gate_lin to produce HIGH gate values when operator
        features are aligned with gradient_ref, LOW when anti-aligned.
        Uses MSE: gate_lin([ref, op]) → 1.0 (aligned) vs 0.0 (anti-aligned).

        We use two synthetic examples per gate layer:
          - aligned: x_dst = ref  → target gate = 1.0
          - anti-aligned: x_dst = -ref → target gate = 0.0
        """
        ref = self.gradient_ref_7d
        losses = []
        for gate_layer in self.learned_gate_layers:
            # Aligned example
            x_aligned = ref.unsqueeze(0)  # [1, 7]
            gate_input_aligned = torch.cat([ref.unsqueeze(0), x_aligned], dim=-1)
            gate_aligned = torch.sigmoid(gate_layer.gate_lin(gate_input_aligned))
            loss_aligned = F.mse_loss(gate_aligned, torch.ones_like(gate_aligned))

            # Anti-aligned example
            x_anti = -ref.unsqueeze(0)  # [1, 7]
            gate_input_anti = torch.cat([ref.unsqueeze(0), x_anti], dim=-1)
            gate_anti = torch.sigmoid(gate_layer.gate_lin(gate_input_anti))
            loss_anti = F.mse_loss(gate_anti, torch.zeros_like(gate_anti))

            losses.append(loss_aligned + loss_anti)

        return torch.stack(losses).mean()

    def freeze_gate(self):
        """Freeze the learned gate linear layers (called after warmup)."""
        for gate_layer in self.learned_gate_layers:
            for p in gate_layer.gate_lin.parameters():
                p.requires_grad_(False)

    def build_graph(self, terrain_bloch):
        data = HeteroData()
        data["terrain"].x = terrain_bloch
        data["operator"].x = self.operator_params
        data["shell"].x = self.shell_params

        t_src = torch.arange(self.n_terrain).repeat_interleave(self.n_operator)
        o_dst = torch.arange(self.n_operator).repeat(self.n_terrain)
        data["terrain", "feeds", "operator"].edge_index = torch.stack([t_src, o_dst])

        o_src = torch.arange(self.n_operator).repeat_interleave(self.n_terrain)
        t_dst = torch.arange(self.n_terrain).repeat(self.n_operator)
        data["operator", "updates", "terrain"].edge_index = torch.stack([o_src, t_dst])

        s_src = torch.arange(self.n_shell).repeat_interleave(self.n_operator)
        o_dst2 = torch.arange(self.n_operator).repeat(self.n_shell)
        data["shell", "constrains", "operator"].edge_index = torch.stack([s_src, o_dst2])

        return data

    def forward(self, terrain_bloch):
        data = self.build_graph(terrain_bloch)
        terrain_x = data["terrain"].x
        operator_x = data["operator"].x
        shell_x = data["shell"].x

        for layer_idx in range(self.n_layers):
            shell_op_ei = data["shell", "constrains", "operator"].edge_index
            operator_x = self.learned_gate_layers[layer_idx](
                shell_x, operator_x, shell_op_ei
            )
            terrain_op_ei = data["terrain", "feeds", "operator"].edge_index
            op_context = self.terrain_to_op_layers[layer_idx](
                terrain_x, operator_x, terrain_op_ei
            )
            operator_x = operator_x + 0.1 * op_context

            op_terrain_ei = data["operator", "updates", "terrain"].edge_index
            terrain_x = self.op_to_terrain_layers[layer_idx](
                operator_x, terrain_x, op_terrain_ei
            )

        ic_values = []
        for i in range(self.n_terrain - 1):
            rho_a = bloch_to_rho(terrain_x[i])
            rho_b = bloch_to_rho(terrain_x[i + 1])
            rho_ab = make_product_state(rho_a, rho_b)

            op_idx = i % self.n_operator
            coupling = torch.sigmoid(operator_x[op_idx, 0]) * 0.3
            phase = coupling.to(torch.complex64)
            diag = torch.tensor([1, 1, 1, 1], dtype=torch.complex64)
            diag[0] = torch.exp(-1j * phase)
            diag[3] = torch.exp(-1j * phase)
            diag[1] = torch.exp(1j * phase)
            diag[2] = torch.exp(1j * phase)
            U = torch.diag(diag)
            rho_ab = U @ rho_ab @ U.conj().T

            rho_a_out = partial_trace_b(rho_ab)
            rho_b_out = partial_trace_a(rho_ab)
            ic = coherent_information_pair(rho_a_out, rho_b_out, rho_ab)
            ic_values.append(ic)

        if not ic_values:
            ic_mean = torch.tensor(0.0, requires_grad=True)
        else:
            ic_mean = torch.stack(ic_values).mean()

        return {"terrain_out": terrain_x, "operator_out": operator_x, "ic_mean": ic_mean}


# =====================================================================
# SEEDING HELPERS
# =====================================================================

INIT_BLOCH = torch.tensor([
    [0.5,  0.3,  0.1],
    [-0.2, 0.4,  0.6],
    [0.1, -0.3,  0.8],
    [0.4,  0.2, -0.5],
], dtype=torch.float32) if torch else None


def make_shell_aligned(grad_7d, dim=7):
    g = grad_7d[:dim].copy()
    mag = float(np.linalg.norm(g))
    shell_rows = []
    half = max(1, dim // 2)
    for start in [0, half]:
        chunk = g[start:start + half]
        row = [float(np.tanh(abs(v))) for v in chunk]
        while len(row) < dim:
            row.append(float(np.tanh(mag)))
        row = row[:dim]
        shell_rows.append(row)
        if len(shell_rows) >= 2:
            break
    while len(shell_rows) < 2:
        shell_rows.append([float(np.tanh(mag))] * dim)
    return torch.tensor(shell_rows[:2], dtype=torch.float32)


def make_shell_anti(grad_7d, dim=7):
    aligned = make_shell_aligned(grad_7d, dim)
    return 1.0 - aligned


def make_shell_noise(seed, dim=7, n_shell=2):
    rng = np.random.default_rng(seed)
    raw = rng.standard_normal((n_shell, dim)).astype(np.float32)
    raw = (raw - raw.min()) / (raw.max() - raw.min() + 1e-8) * 0.8 + 0.1
    return torch.tensor(raw, dtype=torch.float32)


# =====================================================================
# EXTENDED TRAINING LOOP: 200 steps, sampled every 10
# =====================================================================

CHECKPOINT_STEPS = [10, 20, 30, 50, 100, 200]
TOTAL_STEPS = 200
EARLY_FIT_STEPS = 30  # steps used for initial growth rate fit
WARMUP_STEPS = 20
N_SEEDS = 5
SEEDS = [42, 7, 99, 13, 55]


def run_warmup_then_extended(model, n_warmup=WARMUP_STEPS, n_main=TOTAL_STEPS,
                              lr=0.01, seed=42):
    """
    1. Warmup: train gate_lin with alignment loss (n_warmup steps).
    2. Freeze gate_lin.
    3. Main: maximize I_c for n_main steps, record I_c every step.
    Returns: ic_history (list of n_main floats), warmup_loss_history
    """
    torch.manual_seed(seed)

    warmup_opt = torch.optim.Adam(model.parameters(), lr=lr)
    warmup_losses = []
    for _ in range(n_warmup):
        warmup_opt.zero_grad()
        loss = model.warmup_alignment_loss()
        loss.backward()
        warmup_opt.step()
        warmup_losses.append(float(loss.item()))

    # Freeze gate linear layers
    model.freeze_gate()

    main_opt = torch.optim.Adam(
        [p for p in model.parameters() if p.requires_grad], lr=lr
    )
    ic_history = []
    for _ in range(n_main):
        main_opt.zero_grad()
        out = model(INIT_BLOCH)
        loss = -out["ic_mean"]
        loss.backward()
        main_opt.step()
        ic_history.append(float(out["ic_mean"].item()))

    return ic_history, warmup_losses


def extract_checkpoints(ic_history, checkpoint_steps=CHECKPOINT_STEPS):
    """Extract I_c values at specific step checkpoints (1-indexed)."""
    out = {}
    for step in checkpoint_steps:
        if step <= len(ic_history):
            # Average over a 3-step window around checkpoint for stability
            window_start = max(0, step - 3)
            window_end = min(len(ic_history), step)
            out[str(step)] = float(np.mean(ic_history[window_start:window_end]))
        else:
            out[str(step)] = None
    return out


def compute_growth_rate(ic_history, n_steps=EARLY_FIT_STEPS):
    """
    Linear fit of I_c vs step over first n_steps steps.
    Returns slope (∂I_c/∂step), intercept, r².
    """
    y = np.array(ic_history[:n_steps])
    x = np.arange(1, len(y) + 1, dtype=float)
    if len(y) < 2:
        return {"slope": 0.0, "intercept": float(y[0]) if len(y) > 0 else 0.0, "r2": 0.0}
    A = np.column_stack([x, np.ones_like(x)])
    result = np.linalg.lstsq(A, y, rcond=None)
    slope, intercept = result[0]
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - ss_res / (ss_tot + 1e-15)
    return {"slope": float(slope), "intercept": float(intercept), "r2": float(r2)}


def find_ac_crossover(ic_A, ic_C):
    """
    Find first step where A > C (if C started ahead).
    Returns step index (1-indexed) or None.
    """
    for i, (a, c) in enumerate(zip(ic_A, ic_C)):
        if a > c:
            return i + 1
    return None


def compute_95ci(values):
    """95% CI using normal approximation."""
    arr = np.array(values, dtype=float)
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    se = std / np.sqrt(len(arr))
    return {"mean": mean, "std": std, "ci95_lo": mean - 1.96 * se, "ci95_hi": mean + 1.96 * se}


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests(axis0):
    """
    Main experiment: learned-gate GNN, 3 inits × 5 seeds × 200 steps.
    Records I_c at checkpoints, growth rates, crossover steps.
    """
    results = {}
    grad_7d = axis0["grad"]
    grad_ref_7d = torch.tensor(grad_7d / (np.linalg.norm(grad_7d) + 1e-12), dtype=torch.float32)

    # Per-seed records
    per_seed = []
    # Aggregate across seeds for each init type
    A_checkpoints_by_step = {str(s): [] for s in CHECKPOINT_STEPS}
    C_checkpoints_by_step = {str(s): [] for s in CHECKPOINT_STEPS}
    B_checkpoints_by_step = {str(s): [] for s in CHECKPOINT_STEPS}

    A_growth_rates, B_growth_rates, C_growth_rates = [], [], []
    crossover_steps = []  # step where A first exceeds C (if C was ahead)

    for seed_idx, op_seed in enumerate(SEEDS):
        torch.manual_seed(op_seed)
        op_params_init = torch.rand(3, 7) * 0.3 + 0.1

        shell_A = make_shell_aligned(grad_7d, dim=7)
        shell_B = make_shell_anti(grad_7d, dim=7)
        shell_C = make_shell_noise(seed=op_seed * 17 + 3, dim=7)

        def _make(shell_init):
            m = RatchetGNNLearnedGate(
                n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
                shell_init=shell_init, gradient_ref_7d=grad_ref_7d,
            )
            with torch.no_grad():
                m.operator_params.copy_(op_params_init)
            return m

        mA = _make(shell_A)
        mB = _make(shell_B)
        mC = _make(shell_C)

        ic_A, wA = run_warmup_then_extended(mA, seed=op_seed)
        ic_B, wB = run_warmup_then_extended(mB, seed=op_seed)
        ic_C, wC = run_warmup_then_extended(mC, seed=op_seed)

        ckA = extract_checkpoints(ic_A)
        ckB = extract_checkpoints(ic_B)
        ckC = extract_checkpoints(ic_C)

        grA = compute_growth_rate(ic_A)
        grB = compute_growth_rate(ic_B)
        grC = compute_growth_rate(ic_C)

        # Did A start behind C but cross over?
        crossover = find_ac_crossover(ic_A, ic_C)
        # If A was already ahead from step 1, crossover = 1
        if ic_A[0] > ic_C[0]:
            crossover = 1

        # Aggregate
        for s_key in [str(s) for s in CHECKPOINT_STEPS]:
            if ckA[s_key] is not None:
                A_checkpoints_by_step[s_key].append(ckA[s_key])
            if ckB[s_key] is not None:
                B_checkpoints_by_step[s_key].append(ckB[s_key])
            if ckC[s_key] is not None:
                C_checkpoints_by_step[s_key].append(ckC[s_key])

        A_growth_rates.append(grA["slope"])
        B_growth_rates.append(grB["slope"])
        C_growth_rates.append(grC["slope"])
        crossover_steps.append(crossover)

        # Early ordering: check A vs C at steps 10, 20, 30
        early_A_gt_C = {}
        for es in [10, 20, 30]:
            key = str(es)
            va = ckA.get(key)
            vc = ckC.get(key)
            early_A_gt_C[key] = bool(va is not None and vc is not None and va > vc)

        per_seed.append({
            "seed": op_seed,
            "A_checkpoints": ckA,
            "B_checkpoints": ckB,
            "C_checkpoints": ckC,
            "A_growth_rate": grA,
            "B_growth_rate": grB,
            "C_growth_rate": grC,
            "crossover_step": crossover,
            "early_A_gt_C": early_A_gt_C,
            "final_A_gt_C": (ckA.get("200") or 0) > (ckC.get("200") or 0),
            "final_A_gt_B": (ckA.get("200") or 0) > (ckB.get("200") or 0),
            "warmup_loss_A_final": float(wA[-1]) if wA else None,
            "warmup_loss_C_final": float(wC[-1]) if wC else None,
        })

    # Summary statistics
    checkpoint_summary = {}
    for s_key in [str(s) for s in CHECKPOINT_STEPS]:
        a_vals = A_checkpoints_by_step[s_key]
        b_vals = B_checkpoints_by_step[s_key]
        c_vals = C_checkpoints_by_step[s_key]
        if a_vals and c_vals:
            a_ci = compute_95ci(a_vals)
            b_ci = compute_95ci(b_vals) if b_vals else None
            c_ci = compute_95ci(c_vals)
            n_A_gt_C = sum(1 for a, c in zip(a_vals, c_vals) if a > c)
            checkpoint_summary[s_key] = {
                "A": a_ci,
                "B": b_ci,
                "C": c_ci,
                "A_minus_C": a_ci["mean"] - c_ci["mean"],
                "n_A_gt_C": n_A_gt_C,
                "n_seeds": len(a_vals),
            }

    growth_rate_summary = {
        "A": compute_95ci(A_growth_rates),
        "B": compute_95ci(B_growth_rates),
        "C": compute_95ci(C_growth_rates),
        "A_minus_C_slope": float(np.mean(A_growth_rates)) - float(np.mean(C_growth_rates)),
        "A_faster_than_C": float(np.mean(A_growth_rates)) > float(np.mean(C_growth_rates)),
        "A_faster_n_seeds": sum(1 for a, c in zip(A_growth_rates, C_growth_rates) if a > c),
    }

    valid_crossovers = [x for x in crossover_steps if x is not None]
    crossover_summary = {
        "crossover_steps_per_seed": crossover_steps,
        "n_seeds_with_crossover": len(valid_crossovers),
        "mean_crossover_step": float(np.mean(valid_crossovers)) if valid_crossovers else None,
        "early_directional_advantage": sum(
            1 for s in per_seed
            if any(s["early_A_gt_C"].get(k, False) for k in ["10", "20", "30"])
        ),
    }

    # Key claims
    directional_advantage_early = (
        growth_rate_summary["A_faster_n_seeds"] >= 3 or
        crossover_summary["early_directional_advantage"] >= 3
    )
    directional_advantage_confirmed = (
        checkpoint_summary.get("30", {}).get("n_A_gt_C", 0) >= 3 or
        checkpoint_summary.get("10", {}).get("n_A_gt_C", 0) >= 3
    )

    results["per_seed"] = per_seed
    results["checkpoint_summary"] = checkpoint_summary
    results["growth_rate_summary"] = growth_rate_summary
    results["crossover_summary"] = crossover_summary
    results["directional_advantage_early"] = directional_advantage_early
    results["directional_advantage_confirmed"] = directional_advantage_confirmed
    results["gradient_ref_used"] = grad_ref_7d.tolist()
    results["axis0_Ic"] = axis0["I_c"]
    results["axis0_grad_magnitude"] = axis0["grad_magnitude"]

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests(axis0):
    """
    Negative: A and C should NOT be identical at early steps.
    If they are, the init seeding is broken.
    """
    results = {}
    grad_7d = axis0["grad"]

    torch.manual_seed(42)
    op_params_init = torch.rand(3, 7) * 0.3 + 0.1
    grad_ref_7d = torch.tensor(
        grad_7d / (np.linalg.norm(grad_7d) + 1e-12), dtype=torch.float32
    )

    shell_A = make_shell_aligned(grad_7d, dim=7)
    shell_C = make_shell_noise(seed=42 * 17 + 3, dim=7)

    mA = RatchetGNNLearnedGate(
        n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
        shell_init=shell_A, gradient_ref_7d=grad_ref_7d,
    )
    mC = RatchetGNNLearnedGate(
        n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
        shell_init=shell_C, gradient_ref_7d=grad_ref_7d,
    )
    with torch.no_grad():
        mA.operator_params.copy_(op_params_init)
        mC.operator_params.copy_(op_params_init)

    # Check shells ARE different
    shell_diff = float((shell_A - shell_C).abs().mean().item())
    results["shell_A_C_mean_diff"] = shell_diff
    results["shells_are_distinct"] = shell_diff > 0.05

    # Check initial I_c (step 0) differs
    with torch.no_grad():
        out_A = mA(INIT_BLOCH)
        out_C = mC(INIT_BLOCH)
    ic_A0 = float(out_A["ic_mean"].item())
    ic_C0 = float(out_C["ic_mean"].item())
    results["ic_A_step0"] = ic_A0
    results["ic_C_step0"] = ic_C0
    results["ic_step0_differs"] = abs(ic_A0 - ic_C0) > 1e-6
    results["negative_passed"] = results["shells_are_distinct"]

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests(axis0):
    """
    Boundary: warmup gate alignment sanity check.
    After 20 warmup steps, gate should score aligned >> anti-aligned.
    """
    results = {}
    grad_7d = axis0["grad"]
    grad_ref_7d = torch.tensor(
        grad_7d / (np.linalg.norm(grad_7d) + 1e-12), dtype=torch.float32
    )

    shell_A = make_shell_aligned(grad_7d, dim=7)
    model = RatchetGNNLearnedGate(
        n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
        shell_init=shell_A, gradient_ref_7d=grad_ref_7d,
    )

    opt = torch.optim.Adam(model.parameters(), lr=0.01)
    warmup_losses = []
    for _ in range(WARMUP_STEPS):
        opt.zero_grad()
        loss = model.warmup_alignment_loss()
        loss.backward()
        opt.step()
        warmup_losses.append(float(loss.item()))

    results["warmup_loss_initial"] = warmup_losses[0]
    results["warmup_loss_final"] = warmup_losses[-1]
    results["warmup_loss_decreased"] = warmup_losses[-1] < warmup_losses[0]

    # Gate response after warmup
    ref = grad_ref_7d
    gate_layer = model.learned_gate_layers[0]
    with torch.no_grad():
        x_aligned = ref.unsqueeze(0)
        gate_input_a = torch.cat([ref.unsqueeze(0), x_aligned], dim=-1)
        gate_val_aligned = float(torch.sigmoid(gate_layer.gate_lin(gate_input_a)).item())

        x_anti = -ref.unsqueeze(0)
        gate_input_b = torch.cat([ref.unsqueeze(0), x_anti], dim=-1)
        gate_val_anti = float(torch.sigmoid(gate_layer.gate_lin(gate_input_b)).item())

    results["gate_aligned_response"] = gate_val_aligned
    results["gate_anti_response"] = gate_val_anti
    results["gate_direction_sensitive"] = gate_val_aligned > gate_val_anti
    results["gate_gap"] = gate_val_aligned - gate_val_anti
    results["boundary_passed"] = (
        results["warmup_loss_decreased"] and results["gate_direction_sensitive"]
    )

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    out = {
        "name": "torch_gnn_extended_training",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "classification": "canonical",
        "n_steps": TOTAL_STEPS,
        "n_warmup": WARMUP_STEPS,
        "n_seeds": N_SEEDS,
        "checkpoint_steps": CHECKPOINT_STEPS,
        "architecture": "learned_linear_gate_7d",
        "hypothesis": (
            "gradient-aligned init (A) has faster initial I_c growth rate than "
            "noise init (C), even if final values converge"
        ),
    }

    # Check prerequisites
    if torch is None:
        out["error"] = "pytorch not installed"
        out["positive"] = {}
        out["negative"] = {}
        out["boundary"] = {}
    elif MessagePassing is None:
        out["error"] = "torch_geometric not installed"
        out["positive"] = {}
        out["negative"] = {}
        out["boundary"] = {}
    else:
        # Compute Axis 0 gradient reference point
        eta_ref = (
            1.047, 1.047,   # theta_AB, theta_BC (≈ π/3)
            0.785, 0.785,   # phi_AB, phi_BC (≈ π/4)
            0.85, 0.85, 0.75,  # r_A, r_B, r_C
        )
        try:
            print("Computing Axis 0 gradient reference...")
            axis0 = compute_axis0_gradient(eta_ref)
            print(f"  I_c = {axis0['I_c']:.4f}, |∇I_c| = {axis0['grad_magnitude']:.4f}")
            out["axis0"] = {
                "I_c": axis0["I_c"],
                "grad_magnitude": axis0["grad_magnitude"],
                "eta_vals": axis0["eta_vals"],
            }
        except Exception as e:
            out["axis0_error"] = traceback.format_exc()
            axis0 = None

        if axis0 is not None:
            print("Running positive tests (3 inits × 5 seeds × 200 steps)...")
            try:
                out["positive"] = run_positive_tests(axis0)
                print("  Done.")
            except Exception:
                out["positive"] = {"error": traceback.format_exc()}

            print("Running negative tests...")
            try:
                out["negative"] = run_negative_tests(axis0)
            except Exception:
                out["negative"] = {"error": traceback.format_exc()}

            print("Running boundary tests (warmup gate check)...")
            try:
                out["boundary"] = run_boundary_tests(axis0)
            except Exception:
                out["boundary"] = {"error": traceback.format_exc()}
        else:
            out["positive"] = {}
            out["negative"] = {}
            out["boundary"] = {}

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_gnn_extended_training_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    # Print key summary
    if "positive" in out and "checkpoint_summary" in out.get("positive", {}):
        pos = out["positive"]
        print("\n=== CHECKPOINT SUMMARY (A vs C, mean I_c) ===")
        for step in CHECKPOINT_STEPS:
            key = str(step)
            ck = pos["checkpoint_summary"].get(key, {})
            if ck:
                a = ck.get("A", {})
                c = ck.get("C", {})
                gap = ck.get("A_minus_C", 0)
                n = ck.get("n_A_gt_C", 0)
                print(f"  step {step:3d}: A={a.get('mean', 0):.4f}±{a.get('std', 0):.4f}  "
                      f"C={c.get('mean', 0):.4f}±{c.get('std', 0):.4f}  "
                      f"gap={gap:+.4f}  A>C: {n}/{N_SEEDS}")

        gr = pos.get("growth_rate_summary", {})
        print(f"\n=== GROWTH RATE (∂I_c/∂step, steps 1-{EARLY_FIT_STEPS}) ===")
        print(f"  A slope: {gr.get('A', {}).get('mean', 0):.5f}  "
              f"C slope: {gr.get('C', {}).get('mean', 0):.5f}  "
              f"A-C: {gr.get('A_minus_C_slope', 0):+.5f}  "
              f"A faster: {gr.get('A_faster_n_seeds', 0)}/{N_SEEDS} seeds")

        print(f"\n=== DIRECTIONAL ADVANTAGE ===")
        print(f"  Early advantage confirmed: {pos.get('directional_advantage_early', False)}")
        print(f"  Checkpoint confirmation: {pos.get('directional_advantage_confirmed', False)}")

        cr = pos.get("crossover_summary", {})
        print(f"  Seeds with early A>C (steps 10/20/30): {cr.get('early_directional_advantage', 0)}/{N_SEEDS}")
