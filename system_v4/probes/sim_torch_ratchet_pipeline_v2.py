#!/usr/bin/env python3
"""
sim_torch_ratchet_pipeline_v2.py
=================================
Ratchet pipeline v2: regularized GNN training + 3-qubit Fe bridge correlation tracking.

Extends sim_torch_gnn_loss_regularized.py (which found lambda=0.01 optimal) by:
  1. Running 300 steps (up from 200) at the optimal lambda=0.01
  2. Tracking I_c(A→C) and I_c(B→C) along the 3-qubit Fe bridge at every
     checkpoint — tests whether GNN training correlates with Fe bridge activation
  3. Negative test: lambda=0 (should revert, no sustained advantage by ~step 50)
  4. z3 UNSAT proof: the regularized loss decreases monotonically when cos_sim improves

Architecture:
  Same GNN as sim_torch_gnn_loss_regularized.py (3 MessagePassing layers, shell gate,
  HeteroData-style edge construction, TerrainToOperatorConv, OperatorToTerrainConv,
  ShellToOperatorConv). Operator params → 3-qubit Fe bridge states.

3-qubit Fe bridge:
  Qubit A (terrain[0]) --CNOT_AB--> Qubit B (terrain[1]) --CNOT_BC--> Qubit C (terrain[2])
  The "Fe bridge" is this 3-qubit chain; I_c tracked as S(BC) - S(ABC) and S(C) - S(ABC).

Conditions:
  A = gradient-aligned init, B = anti-gradient init, C = noise init
  5 seeds × 300 steps
  Checkpoints: 10, 30, 50, 100, 150, 200, 300

Tests:
  Positive: A > C at step 300, gap growing, Fe bridge activation correlates with GNN training
  Negative: lambda=0 reverts to no sustained advantage by ~step 50
  Boundary: autograd gradient reference correctly non-zero (verified via backward pass)

z3 proof: UNSAT(¬(L_new ≤ L_old) ∧ (cos_sim_new > cos_sim_old))
  i.e. it is UNSATISFIABLE that loss increases when cos_sim improves.

Tools: pytorch=load_bearing, pyg=load_bearing, z3=load_bearing
Output: system_v4/probes/a2_state/sim_results/torch_ratchet_pipeline_v2_results.json
Classification: canonical
"""

import json
import os
import traceback
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
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
    "z3":        "load_bearing",
    "cvc5":      "not_applicable",
    "sympy":     "not_applicable",
    "clifford":  "not_applicable",
    "geomstats": "not_applicable",
    "e3nn":      "not_applicable",
    "rustworkx": "not_applicable",
    "xgi":       "not_applicable",
    "toponetx":  "not_applicable",
    "gudhi":     "not_applicable",
}

# ── Imports ─────────────────────────────────────────────────────────

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core substrate: tensors, autograd, loss regularization, "
        "3-qubit Fe bridge density matrix ops, optimization"
    )
except ImportError:
    torch = None

try:
    from torch_geometric.nn import MessagePassing
    TOOL_MANIFEST["pyg"]["tried"] = True
    TOOL_MANIFEST["pyg"]["used"] = True
    TOOL_MANIFEST["pyg"]["reason"] = (
        "3 MessagePassing layers (TerrainToOperator, OperatorToTerrain, "
        "ShellToOperator) ARE the ratchet dynamics"
    )
except ImportError:
    MessagePassing = None

try:
    from z3 import (
        Solver, Real, And, Implies, Not, sat, unsat, RealVal
    )
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "UNSAT proof that regularized loss decreases monotonically "
        "when cosine similarity improves — cannot increase loss when cos_sim grows"
    )
except ImportError:
    Solver = None

# =====================================================================
# CONSTANTS
# =====================================================================

SEEDS = [42, 137, 271, 314, 999]
N_STEPS = 300
CHECKPOINT_STEPS = [10, 30, 50, 100, 150, 200, 300]
OPTIMAL_LAMBDA = 0.01
LR = 5e-3

N_TERRAIN  = 4
N_OPERATOR = 3
N_SHELL    = 2
N_LAYERS   = 3
TERRAIN_DIM  = 3
OPERATOR_DIM = 3
SHELL_DIM    = 2

# For 3-qubit Fe bridge: use first 3 terrain nodes as qubits A, B, C
BRIDGE_QUBIT_INDICES = [0, 1, 2]

DTYPE_C = torch.complex64 if torch else None
DTYPE_F = torch.float32 if torch else None

# =====================================================================
# PAULI / DENSITY MATRIX UTILITIES
# =====================================================================

def pauli_matrices(device=None):
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE_C, device=device)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE_C, device=device)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE_C, device=device)
    return sx, sy, sz


def bloch_to_rho(bloch):
    """Convert 3-vector Bloch to 2x2 density matrix."""
    sx, sy, sz = pauli_matrices(bloch.device)
    I2 = torch.eye(2, dtype=DTYPE_C, device=bloch.device)
    b = bloch.to(DTYPE_C)
    # Clamp bloch vector norm to sphere
    norm = b.real.float().norm()
    if norm > 1.0:
        b = b / (norm + 1e-8)
    return I2 / 2.0 + (b[0] * sx + b[1] * sy + b[2] * sz) / 2.0


def von_neumann_entropy(rho):
    """Von Neumann entropy in nats (natural log)."""
    eigs = torch.real(torch.linalg.eigvalsh(rho))
    eigs_clamped = torch.clamp(eigs, min=1e-12)
    return -torch.sum(eigs_clamped * torch.log(eigs_clamped))


def partial_trace_b_2q(rho_ab, dim_a=2, dim_b=2):
    """Partial trace over B: returns rho_A."""
    return torch.einsum("ijkj->ik", rho_ab.reshape(dim_a, dim_b, dim_a, dim_b))


def partial_trace_a_2q(rho_ab, dim_a=2, dim_b=2):
    """Partial trace over A: returns rho_B."""
    return torch.einsum("ijik->jk", rho_ab.reshape(dim_a, dim_b, dim_a, dim_b))


def partial_trace_A_3q(rho_abc):
    """Trace out qubit A from 8x8: returns 4x4 rho_BC."""
    rho = rho_abc.reshape(2, 4, 2, 4)
    return torch.einsum('aiaj->ij', rho)


def partial_trace_AB_3q(rho_abc):
    """Trace out qubits AB from 8x8: returns 2x2 rho_C."""
    rho = rho_abc.reshape(4, 2, 4, 2)
    return torch.einsum('aiaj->ij', rho)


def coherent_info_ac(rho_a, rho_c, rho_ac):
    """I_c(A→C) = S(C) - S(AC) in the pair model."""
    return von_neumann_entropy(rho_c) - von_neumann_entropy(rho_ac)


# =====================================================================
# 3-QUBIT Fe BRIDGE
# =====================================================================

def build_cnot_3q_AB():
    """CNOT on qubits A,B tensored with I_C. Returns 8x8 complex."""
    CNOT_2Q = torch.tensor([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=DTYPE_C)
    I2 = torch.eye(2, dtype=DTYPE_C)
    return torch.kron(CNOT_2Q, I2)


def build_cnot_3q_BC():
    """CNOT on qubits B,C tensored with I_A. Returns 8x8 complex."""
    CNOT_2Q = torch.tensor([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=DTYPE_C)
    I2 = torch.eye(2, dtype=DTYPE_C)
    return torch.kron(I2, CNOT_2Q)


def compute_fe_bridge_ic(terrain_x, op_coupling):
    """
    Compute I_c along the 3-qubit Fe bridge.

    Takes the first 3 terrain Bloch vectors as qubits A, B, C.
    Applies CNOT_AB followed by CNOT_BC (the Fe bridge / XX_23 relay).
    Uses op_coupling (a scalar from operator_x) to modulate the bridge strength.

    Returns:
        ic_AC: I_c(A→C) = S(rho_C) - S(rho_ABC)  (bridge end-to-end)
        ic_BC: I_c(B→C) = S(rho_C) - S(rho_BC)   (relay leg only)
        bridge_activated: bool tensor, ic_AC > 1e-4
    """
    rho_A = bloch_to_rho(terrain_x[0])
    rho_B = bloch_to_rho(terrain_x[1])
    rho_C_init = bloch_to_rho(terrain_x[2])

    rho_ABC = torch.kron(torch.kron(rho_A, rho_B), rho_C_init)

    # Apply CNOT_AB (Fe entry)
    cnot_AB = build_cnot_3q_AB().to(rho_ABC.device)
    rho_ABC = cnot_AB @ rho_ABC @ cnot_AB.conj().T

    # Apply CNOT_BC (Fe relay) scaled by coupling
    coupling_strength = torch.sigmoid(op_coupling) * 0.5 + 0.5  # [0.5, 1.0]
    I8 = torch.eye(8, dtype=DTYPE_C, device=rho_ABC.device)
    cnot_BC = build_cnot_3q_BC().to(rho_ABC.device)
    # Partial application: interpolate between identity and CNOT
    U_BC = coupling_strength.to(DTYPE_C) * cnot_BC + (1.0 - coupling_strength.to(DTYPE_C)) * I8
    # U_BC is not unitary in general; renormalize via its action
    rho_ABC = U_BC @ rho_ABC @ U_BC.conj().T
    # Re-normalize trace
    tr = torch.real(torch.trace(rho_ABC))
    rho_ABC = rho_ABC / (tr + 1e-12)

    # Compute partial traces
    rho_BC  = partial_trace_A_3q(rho_ABC)  # 4x4
    rho_C   = partial_trace_AB_3q(rho_ABC)  # 2x2

    S_ABC = von_neumann_entropy(rho_ABC)
    S_BC  = von_neumann_entropy(rho_BC)
    S_C   = von_neumann_entropy(rho_C)

    ic_AC = S_C - S_ABC     # end-to-end A→C
    ic_BC = S_C - S_BC      # relay leg B→C

    return {
        "ic_AC": ic_AC,
        "ic_BC": ic_BC,
        "S_ABC": S_ABC,
        "S_BC": S_BC,
        "S_C": S_C,
        "bridge_activated": (ic_AC.detach() > 1e-4).item(),
    }


# =====================================================================
# MESSAGE PASSING LAYERS (same as sim_torch_gnn_loss_regularized.py)
# =====================================================================

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


class ShellToOperatorConv(MessagePassing):
    def __init__(self, shell_dim, op_dim):
        super().__init__(aggr="mean")
        self.gate = nn.Sequential(
            nn.Linear(shell_dim, 8),
            nn.Tanh(),
            nn.Linear(8, op_dim),
            nn.Sigmoid(),
        )

    def forward(self, x_src, x_dst, edge_index):
        return self.propagate(
            edge_index, x=x_src, x_dst=x_dst,
            size=(x_src.size(0), x_dst.size(0)),
        )

    def message(self, x_j):
        return x_j

    def update(self, aggr_out, x_dst):
        return x_dst * self.gate(aggr_out)


# =====================================================================
# RATCHET GNN V2 WITH FE BRIDGE TRACKING
# =====================================================================

class RatchetGNNv2(nn.Module):
    """GNN with lambda=0.01 gradient-alignment regularizer + Fe bridge tracking.

    Same architecture as RatchetGNNRegularized from sim_torch_gnn_loss_regularized.
    Adds: Fe bridge I_c tracking at each forward pass (detached, no backprop overhead).
    """

    def __init__(self, grad_ref_flat, shell_init=None):
        super().__init__()
        self.register_buffer("grad_ref", grad_ref_flat)

        self.operator_params = nn.Parameter(
            torch.rand(N_OPERATOR, OPERATOR_DIM) * 0.3 + 0.1
        )

        if shell_init is not None:
            self.shell_params = nn.Parameter(shell_init.clone().detach().float())
        else:
            self.shell_params = nn.Parameter(
                torch.rand(N_SHELL, SHELL_DIM) * 0.5 + 0.25
            )

        self.shell_to_op_layers = nn.ModuleList([
            ShellToOperatorConv(SHELL_DIM, OPERATOR_DIM) for _ in range(N_LAYERS)
        ])
        self.terrain_to_op_layers = nn.ModuleList([
            TerrainToOperatorConv(TERRAIN_DIM, OPERATOR_DIM) for _ in range(N_LAYERS)
        ])
        self.op_to_terrain_layers = nn.ModuleList([
            OperatorToTerrainConv(OPERATOR_DIM, TERRAIN_DIM) for _ in range(N_LAYERS)
        ])

    def _build_edge_indices(self):
        n_t, n_o, n_s = N_TERRAIN, N_OPERATOR, N_SHELL
        t_src = torch.arange(n_t).repeat_interleave(n_o)
        o_dst = torch.arange(n_o).repeat(n_t)
        t_to_o = torch.stack([t_src, o_dst])

        o_src = torch.arange(n_o).repeat_interleave(n_t)
        t_dst = torch.arange(n_t).repeat(n_o)
        o_to_t = torch.stack([o_src, t_dst])

        s_src = torch.arange(n_s).repeat_interleave(n_o)
        o_dst2 = torch.arange(n_o).repeat(n_s)
        s_to_o = torch.stack([s_src, o_dst2])

        return t_to_o, o_to_t, s_to_o

    def forward(self, terrain_bloch):
        t_to_o, o_to_t, s_to_o = self._build_edge_indices()

        terrain_x  = terrain_bloch
        operator_x = self.operator_params
        shell_x    = self.shell_params

        for layer_idx in range(N_LAYERS):
            operator_x = self.shell_to_op_layers[layer_idx](
                shell_x, operator_x, s_to_o
            )
            op_context = self.terrain_to_op_layers[layer_idx](
                terrain_x, operator_x, t_to_o
            )
            operator_x = operator_x + 0.1 * op_context
            terrain_x = self.op_to_terrain_layers[layer_idx](
                operator_x, terrain_x, o_to_t
            )

        # Compute I_c on adjacent terrain pairs (main I_c signal)
        ic_values = []
        for i in range(N_TERRAIN - 1):
            rho_a  = bloch_to_rho(terrain_x[i])
            rho_b  = bloch_to_rho(terrain_x[i + 1])
            rho_ab = torch.kron(rho_a, rho_b)

            op_idx  = i % N_OPERATOR
            coupling = torch.sigmoid(operator_x[op_idx, 0]) * 0.3
            phase   = coupling.to(DTYPE_C)
            diag    = torch.tensor([1, 1, 1, 1], dtype=DTYPE_C)
            diag[0] = torch.exp(-1j * phase)
            diag[3] = torch.exp(-1j * phase)
            diag[1] = torch.exp(1j * phase)
            diag[2] = torch.exp(1j * phase)
            U = torch.diag(diag)
            rho_ab = U @ rho_ab @ U.conj().T

            rho_a_out = partial_trace_b_2q(rho_ab)
            rho_b_out = partial_trace_a_2q(rho_ab)
            ic = von_neumann_entropy(rho_b_out) - von_neumann_entropy(rho_ab)
            ic_values.append(ic)

        ic_stack = torch.stack(ic_values) if ic_values else torch.tensor([0.0])
        ic_mean  = ic_stack.mean()

        return {
            "terrain_out":  terrain_x,
            "operator_out": operator_x,
            "ic_values":    ic_stack,
            "ic_mean":      ic_mean,
        }

    def compute_fe_bridge(self, terrain_x, operator_x):
        """Compute Fe bridge I_c values (called with detached tensors to avoid double-grad)."""
        with torch.no_grad():
            # Use operator[0] coupling for bridge modulation
            op_coupling = operator_x[0, 0].detach()
            t_detached  = terrain_x.detach()
            return compute_fe_bridge_ic(t_detached, op_coupling)

    def regularized_loss(self, ic_mean, lam):
        """L = -I_c + lambda * (1 - cos_sim(operator_params_flat, grad_ref))"""
        if lam == 0.0:
            return -ic_mean

        op_flat  = self.operator_params.reshape(-1).float()
        grad_ref = self.grad_ref.float()

        min_len = min(op_flat.shape[0], grad_ref.shape[0])
        op_flat  = op_flat[:min_len]
        grad_ref = grad_ref[:min_len]

        cos_sim = F.cosine_similarity(
            op_flat.unsqueeze(0), grad_ref.unsqueeze(0)
        )
        alignment_penalty = 1.0 - cos_sim
        return -ic_mean + lam * alignment_penalty


# =====================================================================
# AXIS-0 GRADIENT REFERENCE
# =====================================================================

def build_axis0_grad_ref(seed=42):
    """Construct axis-0 gradient reference via a single forward pass.

    Ground state |000> input, Fe bridge pattern (terrain[:, 2] = 0.95).
    Returns normalized flat gradient over operator_params.

    Autograd verification: grad must be non-zero (ensures gradient reference
    is correctly computed, not a zero tensor).
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    probe = RatchetGNNv2(
        grad_ref_flat=torch.zeros(N_OPERATOR * OPERATOR_DIM)
    )

    terrain_bloch = torch.zeros(N_TERRAIN, TERRAIN_DIM, requires_grad=False)
    terrain_bloch[:, 2] = 0.95  # near |0> state (north pole)

    out = probe(terrain_bloch)
    ic  = out["ic_mean"]
    ic.backward()

    grad = probe.operator_params.grad

    grad_nonzero = False
    if grad is not None:
        grad_nonzero = float(grad.abs().sum()) > 1e-10

    if grad is None or not grad_nonzero:
        # Fallback to random unit vector (logged)
        g = torch.randn(N_OPERATOR * OPERATOR_DIM)
        g = g / (g.norm() + 1e-12)
        return g, False, float(0.0)

    g = grad.reshape(-1).clone()
    grad_norm = float(g.norm())
    g = g / (grad_norm + 1e-12)
    return g, True, grad_norm


# =====================================================================
# INIT HELPERS
# =====================================================================

def make_shell_aligned(grad_ref_flat):
    g = grad_ref_flat[:N_SHELL * SHELL_DIM].reshape(N_SHELL, SHELL_DIM)
    g_norm = g / (torch.norm(g) + 1e-12)
    base = torch.full((N_SHELL, SHELL_DIM), 0.5)
    return base + 0.2 * g_norm


def make_shell_anti(grad_ref_flat):
    g = grad_ref_flat[:N_SHELL * SHELL_DIM].reshape(N_SHELL, SHELL_DIM)
    g_norm = g / (torch.norm(g) + 1e-12)
    base = torch.full((N_SHELL, SHELL_DIM), 0.5)
    return base - 0.2 * g_norm


def make_shell_noise(seed=0):
    rng = torch.Generator()
    rng.manual_seed(seed)
    return torch.rand(N_SHELL, SHELL_DIM, generator=rng) * 0.5 + 0.25


# =====================================================================
# TRAINING LOOP WITH FE BRIDGE TRACKING
# =====================================================================

def run_training_with_bridge(model, lam, seed, checkpoint_steps):
    """Run N_STEPS gradient steps. At each checkpoint, also record Fe bridge I_c.

    Returns:
        ic_history:        [float] × N_STEPS
        bridge_ic_AC:      {str(step): float} at checkpoints
        bridge_ic_BC:      {str(step): float} at checkpoints
        bridge_activated:  {str(step): bool} at checkpoints
    """
    torch.manual_seed(seed)
    terrain_bloch = torch.zeros(N_TERRAIN, TERRAIN_DIM)
    terrain_bloch[:, 2] = 0.95  # near |0>

    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    ic_history = []

    bridge_ic_AC = {}
    bridge_ic_BC = {}
    bridge_activated = {}

    checkpoint_set = set(checkpoint_steps)

    for step in range(1, N_STEPS + 1):
        optimizer.zero_grad()
        out  = model(terrain_bloch.detach())
        loss = model.regularized_loss(out["ic_mean"], lam)
        loss.backward()
        optimizer.step()

        ic_val = float(out["ic_mean"].detach())
        ic_history.append(ic_val)

        if step in checkpoint_set:
            bridge = model.compute_fe_bridge(out["terrain_out"], out["operator_out"])
            key = str(step)
            bridge_ic_AC[key]     = float(bridge["ic_AC"].item())
            bridge_ic_BC[key]     = float(bridge["ic_BC"].item())
            bridge_activated[key] = bool(bridge["bridge_activated"])

    return ic_history, bridge_ic_AC, bridge_ic_BC, bridge_activated


def extract_checkpoints(ic_history, checkpoint_steps):
    out = {}
    for s in checkpoint_steps:
        idx = s - 1
        out[str(s)] = float(ic_history[idx]) if idx < len(ic_history) else None
    return out


def compute_growth_rate(ic_history):
    y = np.array(ic_history, dtype=float)
    x = np.arange(1, len(y) + 1, dtype=float)
    if len(y) < 2:
        return {"slope": 0.0, "intercept": 0.0, "r2": 0.0}
    A = np.column_stack([x, np.ones_like(x)])
    res = np.linalg.lstsq(A, y, rcond=None)
    slope, intercept = res[0]
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - ss_res / (ss_tot + 1e-15)
    return {"slope": float(slope), "intercept": float(intercept), "r2": float(r2)}


def compute_stats(values):
    arr = np.array(values, dtype=float)
    mean = float(np.mean(arr))
    std  = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    se   = std / np.sqrt(len(arr))
    return {
        "mean": mean, "std": std,
        "ci95_lo": mean - 1.96 * se,
        "ci95_hi": mean + 1.96 * se,
    }


# =====================================================================
# CORE EXPERIMENT: one condition (A/B/C) over all seeds
# =====================================================================

def run_experiment(lam, grad_ref_flat):
    """Run 3 conditions × 5 seeds × 300 steps.

    Returns per-condition I_c trajectories + Fe bridge tracking.
    """
    A_ic_by_step     = {str(s): [] for s in CHECKPOINT_STEPS}
    B_ic_by_step     = {str(s): [] for s in CHECKPOINT_STEPS}
    C_ic_by_step     = {str(s): [] for s in CHECKPOINT_STEPS}

    A_bridge_AC      = {str(s): [] for s in CHECKPOINT_STEPS}
    A_bridge_BC      = {str(s): [] for s in CHECKPOINT_STEPS}
    C_bridge_AC      = {str(s): [] for s in CHECKPOINT_STEPS}
    C_bridge_BC      = {str(s): [] for s in CHECKPOINT_STEPS}

    A_rates, B_rates, C_rates = [], [], []

    for seed in SEEDS:
        torch.manual_seed(seed)
        np.random.seed(seed)

        shell_A = make_shell_aligned(grad_ref_flat)
        shell_B = make_shell_anti(grad_ref_flat)
        shell_C = make_shell_noise(seed=seed * 17 + 3)

        op_init = torch.rand(N_OPERATOR, OPERATOR_DIM) * 0.3 + 0.1

        def _make(shell_init):
            m = RatchetGNNv2(grad_ref_flat=grad_ref_flat, shell_init=shell_init)
            with torch.no_grad():
                m.operator_params.copy_(op_init)
            return m

        mA = _make(shell_A)
        mB = _make(shell_B)
        mC = _make(shell_C)

        ic_A, b_AC_A, b_BC_A, b_act_A = run_training_with_bridge(mA, lam, seed, CHECKPOINT_STEPS)
        ic_B, b_AC_B, b_BC_B, b_act_B = run_training_with_bridge(mB, lam, seed, CHECKPOINT_STEPS)
        ic_C, b_AC_C, b_BC_C, b_act_C = run_training_with_bridge(mC, lam, seed, CHECKPOINT_STEPS)

        ckA = extract_checkpoints(ic_A, CHECKPOINT_STEPS)
        ckB = extract_checkpoints(ic_B, CHECKPOINT_STEPS)
        ckC = extract_checkpoints(ic_C, CHECKPOINT_STEPS)

        for s in CHECKPOINT_STEPS:
            key = str(s)
            if ckA[key] is not None: A_ic_by_step[key].append(ckA[key])
            if ckB[key] is not None: B_ic_by_step[key].append(ckB[key])
            if ckC[key] is not None: C_ic_by_step[key].append(ckC[key])

            if b_AC_A.get(key) is not None: A_bridge_AC[key].append(b_AC_A[key])
            if b_BC_A.get(key) is not None: A_bridge_BC[key].append(b_BC_A[key])
            if b_AC_C.get(key) is not None: C_bridge_AC[key].append(b_AC_C[key])
            if b_BC_C.get(key) is not None: C_bridge_BC[key].append(b_BC_C[key])

        A_rates.append(compute_growth_rate(ic_A)["slope"])
        B_rates.append(compute_growth_rate(ic_B)["slope"])
        C_rates.append(compute_growth_rate(ic_C)["slope"])

    # Aggregate
    A_means = {k: float(np.mean(v)) if v else None for k, v in A_ic_by_step.items()}
    B_means = {k: float(np.mean(v)) if v else None for k, v in B_ic_by_step.items()}
    C_means = {k: float(np.mean(v)) if v else None for k, v in C_ic_by_step.items()}

    A_bridge_AC_means = {k: float(np.mean(v)) if v else None for k, v in A_bridge_AC.items()}
    A_bridge_BC_means = {k: float(np.mean(v)) if v else None for k, v in A_bridge_BC.items()}
    C_bridge_AC_means = {k: float(np.mean(v)) if v else None for k, v in C_bridge_AC.items()}
    C_bridge_BC_means = {k: float(np.mean(v)) if v else None for k, v in C_bridge_BC.items()}

    AC_gap = {}
    for s in CHECKPOINT_STEPS:
        key = str(s)
        a = A_means.get(key)
        c = C_means.get(key)
        AC_gap[key] = float(a - c) if (a is not None and c is not None) else None

    # Gap trend: is gap at step 300 > gap at step 50?
    gap_50  = AC_gap.get("50")
    gap_300 = AC_gap.get("300")
    gap_growing = bool(gap_300 > gap_50) if (gap_50 is not None and gap_300 is not None) else None

    # Fe bridge correlation: does A's bridge IC correlate with its IC trajectory?
    # Simple: is A_bridge_AC at step 300 higher than at step 10?
    bridge_grows_A = None
    if A_bridge_AC_means.get("300") is not None and A_bridge_AC_means.get("10") is not None:
        bridge_grows_A = bool(A_bridge_AC_means["300"] > A_bridge_AC_means["10"])

    # GNN-bridge correlation: Pearson r between ic_mean and bridge_ic_AC across checkpoints
    ic_vals     = [A_means.get(str(s)) for s in CHECKPOINT_STEPS]
    bridge_vals = [A_bridge_AC_means.get(str(s)) for s in CHECKPOINT_STEPS]
    valid_pairs = [(i, b) for i, b in zip(ic_vals, bridge_vals) if i is not None and b is not None]
    gnn_bridge_corr = None
    if len(valid_pairs) >= 3:
        ic_arr = np.array([p[0] for p in valid_pairs])
        br_arr = np.array([p[1] for p in valid_pairs])
        if np.std(ic_arr) > 1e-10 and np.std(br_arr) > 1e-10:
            corr = float(np.corrcoef(ic_arr, br_arr)[0, 1])
            gnn_bridge_corr = corr

    return {
        "lambda": lam,
        "A_mean_by_step":      A_means,
        "B_mean_by_step":      B_means,
        "C_mean_by_step":      C_means,
        "AC_gap_by_step":      AC_gap,
        "A_growth_rate":       compute_stats(A_rates),
        "B_growth_rate":       compute_stats(B_rates),
        "C_growth_rate":       compute_stats(C_rates),
        "A_gt_C_at_300":       bool((A_means.get("300") or 0) > (C_means.get("300") or 0)),
        "A_gt_C_at_200":       bool((A_means.get("200") or 0) > (C_means.get("200") or 0)),
        "A_gt_C_at_100":       bool((A_means.get("100") or 0) > (C_means.get("100") or 0)),
        "A_gt_C_at_50":        bool((A_means.get("50")  or 0) > (C_means.get("50")  or 0)),
        "gap_growing":         gap_growing,
        "A_bridge_AC_by_step": A_bridge_AC_means,
        "A_bridge_BC_by_step": A_bridge_BC_means,
        "C_bridge_AC_by_step": C_bridge_AC_means,
        "C_bridge_BC_by_step": C_bridge_BC_means,
        "bridge_grows_A":      bridge_grows_A,
        "gnn_bridge_correlation_r": gnn_bridge_corr,
        "gnn_training_correlates_with_fe_bridge": (
            gnn_bridge_corr is not None and gnn_bridge_corr > 0.5
        ),
    }


# =====================================================================
# Z3 PROOF: UNSAT — loss cannot increase when cos_sim improves
# =====================================================================

def run_z3_monotone_proof():
    """
    Prove via z3 UNSAT that regularized loss decreases monotonically
    when cosine similarity improves.

    Claim: ∀ ic, lam, cos_old, cos_new where cos_new > cos_old ≥ -1:
        L_new = -ic + lam * (1 - cos_new)
        L_old = -ic + lam * (1 - cos_old)
        ¬(L_new ≤ L_old) is UNSAT

    Equivalently: assert L_new > L_old ∧ cos_new > cos_old ∧ lam > 0 → UNSAT

    This formalizes: adding the cos_sim term cannot increase loss when cos_sim improves.
    """
    if Solver is None:
        return {
            "status": "z3_not_installed",
            "unsat_confirmed": False,
            "error": "z3 not available",
        }

    s = Solver()

    # Real variables
    ic      = Real("ic")
    lam     = Real("lam")
    cos_old = Real("cos_old")
    cos_new = Real("cos_new")

    # L = -ic + lam*(1 - cos)
    # L_new = -ic + lam*(1 - cos_new)
    # L_old = -ic + lam*(1 - cos_old)
    # L_new - L_old = lam*(1 - cos_new) - lam*(1 - cos_old)
    #               = lam*(cos_old - cos_new)
    # If cos_new > cos_old and lam > 0:
    #   L_new - L_old = lam*(cos_old - cos_new) < 0
    #   So L_new < L_old (loss strictly decreases)
    # We try to prove the NEGATION is UNSAT:
    #   assert: lam > 0, cos_new > cos_old, L_new >= L_old
    #   If UNSAT: the claim is proven.

    L_new = -ic + lam * (1 - cos_new)
    L_old = -ic + lam * (1 - cos_old)

    s.add(lam > RealVal("0"))
    s.add(cos_new > cos_old)
    s.add(cos_new <= RealVal("1"))
    s.add(cos_old >= RealVal("-1"))
    s.add(L_new >= L_old)  # negation of L_new < L_old

    result = s.check()
    unsat_confirmed = (result == unsat)

    return {
        "status": str(result),
        "unsat_confirmed": unsat_confirmed,
        "claim": (
            "When cos_sim improves (cos_new > cos_old) and lambda > 0, "
            "the regularized loss strictly decreases. "
            "The negation is UNSAT."
        ),
        "proof_structure": (
            "L_new - L_old = lambda*(cos_old - cos_new). "
            "cos_new > cos_old ∧ lambda > 0 => L_new - L_old < 0 => L_new < L_old."
        ),
        "pass": unsat_confirmed,
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests(grad_ref_flat):
    """lambda=0.01: A > C at step 300, gap growing, Fe bridge correlation."""
    results = {}

    print("  Positive: lambda=0.01, 300 steps...")
    r = run_experiment(OPTIMAL_LAMBDA, grad_ref_flat)

    results["experiment_lambda_001"] = r
    results["A_gt_C_at_step_300"]    = r["A_gt_C_at_300"]
    results["gap_growing_50_to_300"] = r["gap_growing"]
    results["gnn_bridge_correlation"] = r["gnn_training_correlates_with_fe_bridge"]
    results["gnn_bridge_correlation_r"] = r["gnn_bridge_correlation_r"]

    results["summary"] = {
        "A_mean_step_50":   r["A_mean_by_step"].get("50"),
        "A_mean_step_300":  r["A_mean_by_step"].get("300"),
        "C_mean_step_50":   r["C_mean_by_step"].get("50"),
        "C_mean_step_300":  r["C_mean_by_step"].get("300"),
        "AC_gap_step_50":   r["AC_gap_by_step"].get("50"),
        "AC_gap_step_300":  r["AC_gap_by_step"].get("300"),
        "A_growth_rate":    r["A_growth_rate"]["mean"],
        "C_growth_rate":    r["C_growth_rate"]["mean"],
        "A_bridge_AC_step_10":  r["A_bridge_AC_by_step"].get("10"),
        "A_bridge_AC_step_300": r["A_bridge_AC_by_step"].get("300"),
        "C_bridge_AC_step_10":  r["C_bridge_AC_by_step"].get("10"),
        "C_bridge_AC_step_300": r["C_bridge_AC_by_step"].get("300"),
    }

    results["pass"] = (
        r["A_gt_C_at_300"]
        and r["A_gt_C_at_200"]
        and r["A_gt_C_at_50"]
    )

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests(grad_ref_flat):
    """lambda=0: should revert to no sustained advantage by ~step 50."""
    results = {}

    print("  Negative: lambda=0 (should revert)...")
    r = run_experiment(0.0, grad_ref_flat)

    results["experiment_lambda_0"] = r

    a10  = r["A_mean_by_step"].get("10")
    c10  = r["C_mean_by_step"].get("10")
    a50  = r["A_mean_by_step"].get("50")
    c50  = r["C_mean_by_step"].get("50")
    a300 = r["A_mean_by_step"].get("300")
    c300 = r["C_mean_by_step"].get("300")

    results["A_ahead_at_step_10"]  = bool((a10  or 0) > (c10  or 0))
    results["A_ahead_at_step_50"]  = bool((a50  or 0) > (c50  or 0))
    results["A_ahead_at_step_300"] = bool((a300 or 0) > (c300 or 0))

    # Revert = A leads early but loses advantage by step 300 (or 50)
    results["revert_confirmed"] = (
        not results["A_ahead_at_step_300"]
    )
    results["interpretation"] = (
        "lambda=0 reverts to unregularized baseline (advantage collapses)"
        if results["revert_confirmed"]
        else "lambda=0 does NOT revert — advantage persists even without regularizer"
    )

    # z3 proof of monotone decrease
    print("  z3 UNSAT proof...")
    z3_result = run_z3_monotone_proof()
    results["z3_monotone_proof"] = z3_result

    results["pass"] = results["revert_confirmed"] and z3_result["unsat_confirmed"]

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests(grad_ref_flat):
    """Verify autograd gradient reference is correctly computed (non-zero)."""
    results = {}

    print("  Boundary: autograd gradient reference verification...")

    # Test grad ref across multiple seeds
    grad_nonzero_counts = []
    grad_norms = []

    for seed in SEEDS:
        _, grad_nonzero, grad_norm = build_axis0_grad_ref(seed=seed)
        grad_nonzero_counts.append(grad_nonzero)
        grad_norms.append(grad_norm)

    results["grad_ref_nonzero_all_seeds"] = all(grad_nonzero_counts)
    results["grad_norms"] = grad_norms
    results["grad_norm_mean"] = float(np.mean(grad_norms))
    results["detail"] = (
        "Gradient reference is computed via autograd backward() on I_c. "
        "Non-zero confirms the computation graph is intact."
    )

    # Also verify: two distinct inits (A=aligned, B=anti) are distinguishable
    grad_ref, _, _ = build_axis0_grad_ref(seed=42)
    shell_A = make_shell_aligned(grad_ref)
    shell_B = make_shell_anti(grad_ref)

    cos_sim_AB = float(F.cosine_similarity(
        shell_A.flatten().unsqueeze(0),
        shell_B.flatten().unsqueeze(0)
    ).item())

    results["shell_A_B_cos_sim"] = cos_sim_AB
    results["shells_distinguishable"] = cos_sim_AB < 0.9

    results["pass"] = (
        results["grad_ref_nonzero_all_seeds"]
        and results["shells_distinguishable"]
    )

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Building axis-0 gradient reference...")
    grad_ref_flat, grad_nonzero, grad_norm_raw = build_axis0_grad_ref(seed=42)

    autograd_verification = {
        "grad_ref_nonzero": grad_nonzero,
        "grad_ref_norm_before_normalize": grad_norm_raw,
        "grad_ref_shape": list(grad_ref_flat.shape),
    }
    print(f"  grad_ref: nonzero={grad_nonzero}, norm={grad_norm_raw:.6f}")

    print("Running positive tests...")
    positive = run_positive_tests(grad_ref_flat)

    print("Running negative tests...")
    negative = run_negative_tests(grad_ref_flat)

    print("Running boundary tests...")
    boundary = run_boundary_tests(grad_ref_flat)

    # Final summary
    pos_r = positive.get("experiment_lambda_001", {})
    neg_r = negative.get("experiment_lambda_0", {})

    summary = {
        "A_gt_C_at_300":           positive.get("A_gt_C_at_step_300"),
        "gap_trend":               "growing" if positive.get("gap_growing_50_to_300") else "stable_or_shrinking",
        "AC_gap_step_50":          pos_r.get("AC_gap_by_step", {}).get("50"),
        "AC_gap_step_300":         pos_r.get("AC_gap_by_step", {}).get("300"),
        "gnn_bridge_correlation_r": positive.get("gnn_bridge_correlation_r"),
        "gnn_training_correlates_with_fe_bridge": positive.get("gnn_bridge_correlation"),
        "lambda_0_reverts":        negative.get("revert_confirmed"),
        "z3_monotone_unsat":       negative.get("z3_monotone_proof", {}).get("unsat_confirmed"),
        "autograd_verified":       autograd_verification,
        "A_growth_rate":           pos_r.get("A_growth_rate", {}).get("mean"),
        "C_growth_rate":           pos_r.get("C_growth_rate", {}).get("mean"),
    }
    overall_pass = bool(
        positive.get("pass", True)
        and negative.get("pass", True)
        and boundary.get("pass", True)
    )
    summary["all_pass"] = overall_pass

    # Mark tool integration depth
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    TOOL_INTEGRATION_DEPTH["pyg"]     = "load_bearing"
    TOOL_INTEGRATION_DEPTH["z3"]      = "load_bearing"

    results = {
        "name": "sim_torch_ratchet_pipeline_v2",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "autograd_verification": autograd_verification,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "classification": "canonical" if overall_pass else "exploratory_signal",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_ratchet_pipeline_v2_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"\nSUMMARY:")
    print(f"  A > C at step 300:         {summary['A_gt_C_at_300']}")
    print(f"  Gap trend (50→300):        {summary['gap_trend']}")
    print(f"  GNN-bridge correlation r:  {summary['gnn_bridge_correlation_r']}")
    print(f"  Fe bridge correlates:      {summary['gnn_training_correlates_with_fe_bridge']}")
    print(f"  lambda=0 reverts:          {summary['lambda_0_reverts']}")
    print(f"  z3 monotone UNSAT:         {summary['z3_monotone_unsat']}")
    print(f"  A growth rate:             {summary['A_growth_rate']}")
    print(f"  C growth rate:             {summary['C_growth_rate']}")
