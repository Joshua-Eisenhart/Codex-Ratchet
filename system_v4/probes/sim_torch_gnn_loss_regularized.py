#!/usr/bin/env python3
"""
sim_torch_gnn_loss_regularized.py
==================================
Tests whether wiring the axis-0 gradient reference directly into the LOSS
as a cosine-alignment regularization term maintains A > C advantage beyond
step 50 (where it previously collapses without regularization).

Loss: L = -I_c + lambda * (1 - cos_sim(operator_params, grad_ref))

Architecture:
  Same GNN as sim_torch_ratchet_gnn.py (3 MessagePassing layers, shell gate,
  HeteroData, TerrainToOperatorConv, OperatorToTerrainConv, ShellToOperatorConv).

Experiment:
  3 conditions (A=gradient-aligned init, B=anti-gradient init, C=noise init)
  × 5 seeds × 200 steps
  Checkpoints: 10, 20, 50, 100, 200
  Lambda sweep: 0.0, 0.01, 0.05, 0.1, 0.5, 1.0

Tests:
  Positive: With optimal lambda, A > C maintained at steps 50, 100, 200
  Negative: lambda=0 reverts to prior behavior (A > C only early, collapses)
  Boundary: lambda=1.0 heavy regularization collapses all three trajectories

Tools: pytorch=load_bearing, pyg=load_bearing
Output: system_v4/probes/a2_state/sim_results/torch_gnn_loss_regularized_results.json
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
    "z3":        "not_applicable",
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
        "Core substrate: tensors, autograd, loss regularization, optimization"
    )
except ImportError:
    pass

try:
    from torch_geometric.nn import MessagePassing
    from torch_geometric.data import HeteroData
    TOOL_MANIFEST["pyg"]["tried"] = True
    TOOL_MANIFEST["pyg"]["used"] = True
    TOOL_MANIFEST["pyg"]["reason"] = (
        "HeteroData graph + 3 MessagePassing layers IS the ratchet dynamics"
    )
except ImportError:
    pass

# =====================================================================
# CONSTANTS
# =====================================================================

SEEDS = [42, 137, 271, 314, 999]
N_STEPS = 200
CHECKPOINT_STEPS = [10, 20, 50, 100, 200]
LAMBDA_SWEEP = [0.0, 0.01, 0.05, 0.1, 0.5, 1.0]
LR = 5e-3

N_TERRAIN  = 4
N_OPERATOR = 3
N_SHELL    = 2
N_LAYERS   = 3
TERRAIN_DIM  = 3
OPERATOR_DIM = 3
SHELL_DIM    = 2

# =====================================================================
# PAULI / DENSITY MATRIX UTILITIES
# =====================================================================

def pauli_matrices(device=None):
    sx = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64, device=device)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex64, device=device)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64, device=device)
    return sx, sy, sz


def bloch_to_rho(bloch):
    sx, sy, sz = pauli_matrices(bloch.device)
    I2 = torch.eye(2, dtype=torch.complex64, device=bloch.device)
    b = bloch.to(torch.complex64)
    return I2 / 2.0 + (b[0] * sx + b[1] * sy + b[2] * sz) / 2.0


def von_neumann_entropy(rho):
    eigs = torch.real(torch.linalg.eigvalsh(rho))
    eigs_clamped = torch.clamp(eigs, min=1e-12)
    return -torch.sum(eigs_clamped * torch.log2(eigs_clamped))


def make_product_state(rho_a, rho_b):
    return torch.kron(rho_a, rho_b)


def partial_trace_b(rho_ab, dim_a=2, dim_b=2):
    return torch.einsum("ijkj->ik", rho_ab.reshape(dim_a, dim_b, dim_a, dim_b))


def partial_trace_a(rho_ab, dim_a=2, dim_b=2):
    return torch.einsum("ijik->jk", rho_ab.reshape(dim_a, dim_b, dim_a, dim_b))


def coherent_information_pair(rho_a, rho_b, rho_ab):
    return von_neumann_entropy(rho_b) - von_neumann_entropy(rho_ab)


# =====================================================================
# MESSAGE PASSING LAYERS (same as sim_torch_ratchet_gnn.py)
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
# RATCHET GNN WITH LOSS REGULARIZATION
# =====================================================================

class RatchetGNNRegularized(nn.Module):
    """Same architecture as RatchetGNN (3 MP layers + shell gate).

    Adds: gradient reference stored for use in regularized loss computation.
    The loss is computed OUTSIDE the forward to keep forward pure.
    """

    def __init__(self, grad_ref_flat, shell_init=None):
        """
        Args:
            grad_ref_flat: 1D tensor [OPERATOR_DIM * N_OPERATOR] — the
                           axis-0 gradient reference, flattened and normalized.
            shell_init: optional [N_SHELL, SHELL_DIM] tensor for initial
                        shell parameters. If None, random.
        """
        super().__init__()
        self.register_buffer("grad_ref", grad_ref_flat)

        # Learnable operator parameters
        self.operator_params = nn.Parameter(
            torch.rand(N_OPERATOR, OPERATOR_DIM) * 0.3 + 0.1
        )

        # Shell parameters
        if shell_init is not None:
            self.shell_params = nn.Parameter(shell_init.clone().detach().float())
        else:
            self.shell_params = nn.Parameter(
                torch.rand(N_SHELL, SHELL_DIM) * 0.5 + 0.25
            )

        # 3 layers of each conv type
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
            # 1. Shell -> Operator: constraint gating
            operator_x = self.shell_to_op_layers[layer_idx](
                shell_x, operator_x, s_to_o
            )
            # 2. Terrain -> Operator: aggregate state info
            op_context = self.terrain_to_op_layers[layer_idx](
                terrain_x, operator_x, t_to_o
            )
            operator_x = operator_x + 0.1 * op_context
            # 3. Operator -> Terrain: apply channels
            terrain_x = self.op_to_terrain_layers[layer_idx](
                operator_x, terrain_x, o_to_t
            )

        # Compute I_c on adjacent terrain pairs
        ic_values = []
        for i in range(N_TERRAIN - 1):
            rho_a  = bloch_to_rho(terrain_x[i])
            rho_b  = bloch_to_rho(terrain_x[i + 1])
            rho_ab = make_product_state(rho_a, rho_b)

            op_idx  = i % N_OPERATOR
            coupling = torch.sigmoid(operator_x[op_idx, 0]) * 0.3
            phase   = coupling.to(torch.complex64)
            diag    = torch.tensor([1, 1, 1, 1], dtype=torch.complex64)
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

        ic_stack = torch.stack(ic_values) if ic_values else torch.tensor([0.0])
        ic_mean  = ic_stack.mean()

        return {
            "terrain_out":  terrain_x,
            "operator_out": operator_x,
            "ic_values":    ic_stack,
            "ic_mean":      ic_mean,
        }

    def regularized_loss(self, ic_mean, lam):
        """L = -I_c + lambda * (1 - cos_sim(operator_params_flat, grad_ref))

        The regularizer penalizes the operator parameters for moving
        anti-gradient relative to the axis-0 reference direction.
        """
        if lam == 0.0:
            return -ic_mean

        op_flat  = self.operator_params.reshape(-1).float()
        grad_ref = self.grad_ref.float()

        # Pad or truncate to match lengths
        min_len = min(op_flat.shape[0], grad_ref.shape[0])
        op_flat  = op_flat[:min_len]
        grad_ref = grad_ref[:min_len]

        cos_sim = F.cosine_similarity(
            op_flat.unsqueeze(0), grad_ref.unsqueeze(0)
        )  # scalar in [-1, 1]

        alignment_penalty = 1.0 - cos_sim  # 0=perfectly aligned, 2=anti-aligned
        return -ic_mean + lam * alignment_penalty


# =====================================================================
# AXIS-0 GRADIENT REFERENCE
# =====================================================================

def build_axis0_grad_ref(seed=42):
    """Construct the axis-0 gradient reference via a single forward pass.

    Mimics the axis-0 operational config: |000> input, Fe bridge pattern,
    3-qubit terrain. Returns normalized flat gradient over operator_params.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    # Spin up a tiny probe model to get a real gradient direction
    probe = RatchetGNNRegularized(
        grad_ref_flat=torch.zeros(N_OPERATOR * OPERATOR_DIM)
    )

    # Initial terrain: ground state Bloch vectors (approx |0>)
    terrain_bloch = torch.zeros(N_TERRAIN, TERRAIN_DIM, requires_grad=False)
    terrain_bloch[:, 2] = 0.95  # near north pole

    out = probe(terrain_bloch)
    ic  = out["ic_mean"]
    ic.backward()

    grad = probe.operator_params.grad
    if grad is None:
        # Fallback: random unit vector
        g = torch.randn(N_OPERATOR * OPERATOR_DIM)
        return g / (g.norm() + 1e-12)

    g = grad.reshape(-1).clone()
    return g / (g.norm() + 1e-12)


# =====================================================================
# INIT HELPERS
# =====================================================================

def make_shell_aligned(grad_ref_flat):
    """Shell params biased toward the gradient direction (projected into shell dim)."""
    g = grad_ref_flat[:N_SHELL * SHELL_DIM].reshape(N_SHELL, SHELL_DIM)
    g_norm = g / (torch.norm(g) + 1e-12)
    base = torch.full((N_SHELL, SHELL_DIM), 0.5)
    return base + 0.2 * g_norm


def make_shell_anti(grad_ref_flat):
    """Shell params biased anti-gradient."""
    g = grad_ref_flat[:N_SHELL * SHELL_DIM].reshape(N_SHELL, SHELL_DIM)
    g_norm = g / (torch.norm(g) + 1e-12)
    base = torch.full((N_SHELL, SHELL_DIM), 0.5)
    return base - 0.2 * g_norm


def make_shell_noise(seed=0):
    """Shell params from random noise."""
    rng = torch.Generator()
    rng.manual_seed(seed)
    return torch.rand(N_SHELL, SHELL_DIM, generator=rng) * 0.5 + 0.25


# =====================================================================
# TRAINING LOOP
# =====================================================================

def run_training(model, lam, seed):
    """Run N_STEPS gradient steps, return I_c history."""
    torch.manual_seed(seed)
    terrain_bloch = torch.zeros(N_TERRAIN, TERRAIN_DIM)
    terrain_bloch[:, 2] = 0.95  # near |0>

    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    ic_history = []

    for step in range(N_STEPS):
        optimizer.zero_grad()
        out  = model(terrain_bloch.detach())
        loss = model.regularized_loss(out["ic_mean"], lam)
        loss.backward()
        optimizer.step()
        ic_history.append(float(out["ic_mean"].detach()))

    return ic_history


def extract_checkpoints(ic_history):
    """Extract I_c values at CHECKPOINT_STEPS (1-indexed)."""
    out = {}
    for s in CHECKPOINT_STEPS:
        idx = s - 1
        out[str(s)] = float(ic_history[idx]) if idx < len(ic_history) else None
    return out


def compute_growth_rate(ic_history, n_steps=None):
    """Linear fit slope over first n_steps."""
    y = np.array(ic_history[:n_steps] if n_steps else ic_history, dtype=float)
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
# CORE EXPERIMENT: one (lambda, conditions A/B/C) run over all seeds
# =====================================================================

def run_one_lambda(lam, grad_ref_flat):
    """Run all seeds for a given lambda value.

    Returns per-condition checkpoint stats and growth rates.
    """
    A_by_step = {str(s): [] for s in CHECKPOINT_STEPS}
    B_by_step = {str(s): [] for s in CHECKPOINT_STEPS}
    C_by_step = {str(s): [] for s in CHECKPOINT_STEPS}

    A_rates, B_rates, C_rates = [], [], []

    for seed_idx, seed in enumerate(SEEDS):
        torch.manual_seed(seed)
        np.random.seed(seed)

        shell_A = make_shell_aligned(grad_ref_flat)
        shell_B = make_shell_anti(grad_ref_flat)
        shell_C = make_shell_noise(seed=seed * 17 + 3)

        # Shared operator init for fair comparison
        op_init = torch.rand(N_OPERATOR, OPERATOR_DIM) * 0.3 + 0.1

        def _make(shell_init):
            m = RatchetGNNRegularized(
                grad_ref_flat=grad_ref_flat,
                shell_init=shell_init,
            )
            with torch.no_grad():
                m.operator_params.copy_(op_init)
            return m

        mA = _make(shell_A)
        mB = _make(shell_B)
        mC = _make(shell_C)

        ic_A = run_training(mA, lam, seed)
        ic_B = run_training(mB, lam, seed)
        ic_C = run_training(mC, lam, seed)

        ckA = extract_checkpoints(ic_A)
        ckB = extract_checkpoints(ic_B)
        ckC = extract_checkpoints(ic_C)

        for s in CHECKPOINT_STEPS:
            key = str(s)
            if ckA[key] is not None: A_by_step[key].append(ckA[key])
            if ckB[key] is not None: B_by_step[key].append(ckB[key])
            if ckC[key] is not None: C_by_step[key].append(ckC[key])

        A_rates.append(compute_growth_rate(ic_A)["slope"])
        B_rates.append(compute_growth_rate(ic_B)["slope"])
        C_rates.append(compute_growth_rate(ic_C)["slope"])

    # Compute mean I_c at each checkpoint
    A_means = {k: float(np.mean(v)) if v else None for k, v in A_by_step.items()}
    B_means = {k: float(np.mean(v)) if v else None for k, v in B_by_step.items()}
    C_means = {k: float(np.mean(v)) if v else None for k, v in C_by_step.items()}

    # A-C gap at each checkpoint
    AC_gap = {}
    for s in CHECKPOINT_STEPS:
        key = str(s)
        a = A_means.get(key)
        c = C_means.get(key)
        AC_gap[key] = float(a - c) if (a is not None and c is not None) else None

    return {
        "lambda": lam,
        "A_mean_by_step": A_means,
        "B_mean_by_step": B_means,
        "C_mean_by_step": C_means,
        "AC_gap_by_step": AC_gap,
        "A_growth_rate":  compute_stats(A_rates),
        "B_growth_rate":  compute_stats(B_rates),
        "C_growth_rate":  compute_stats(C_rates),
        "A_gt_C_at_200":  (A_means.get("200") or 0) > (C_means.get("200") or 0),
        "A_gt_C_at_100":  (A_means.get("100") or 0) > (C_means.get("100") or 0),
        "A_gt_C_at_50":   (A_means.get("50")  or 0) > (C_means.get("50")  or 0),
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests(grad_ref_flat):
    """Lambda sweep: find optimal lambda, test directional advantage persistence."""
    results = {}
    sweep_results = []

    print("  Lambda sweep...")
    for lam in LAMBDA_SWEEP:
        print(f"    lambda={lam}...")
        r = run_one_lambda(lam, grad_ref_flat)
        sweep_results.append(r)

    # Find optimal lambda: highest mean A-C gap at step 200
    best_lam = None
    best_gap = -float("inf")
    for r in sweep_results:
        gap = r["AC_gap_by_step"].get("200")
        if gap is not None and gap > best_gap:
            best_gap = gap
            best_lam = r["lambda"]

    # Pull out lambda=0.0 result for comparison (should replicate prior behavior)
    lam0 = next((r for r in sweep_results if r["lambda"] == 0.0), None)
    lam_opt = next((r for r in sweep_results if r["lambda"] == best_lam), None)

    # Check: with lambda=0, A > C should fail at step 200 (prior behavior)
    lam0_A_gt_C_200 = lam0["A_gt_C_at_200"] if lam0 else None

    # Check: with optimal lambda, A > C should hold at 50, 100, 200
    opt_maintains = (
        lam_opt["A_gt_C_at_50"]
        and lam_opt["A_gt_C_at_100"]
        and lam_opt["A_gt_C_at_200"]
    ) if lam_opt else False

    results["lambda_sweep"]        = sweep_results
    results["optimal_lambda"]      = best_lam
    results["optimal_AC_gap_200"]  = best_gap
    results["lam0_A_gt_C_at_200"]  = lam0_A_gt_C_200
    results["opt_maintains_A_gt_C"] = opt_maintains

    if lam_opt:
        results["optimal_lambda_detail"] = {
            "A_mean_by_step": lam_opt["A_mean_by_step"],
            "C_mean_by_step": lam_opt["C_mean_by_step"],
            "AC_gap_by_step": lam_opt["AC_gap_by_step"],
            "A_growth_rate":  lam_opt["A_growth_rate"],
            "C_growth_rate":  lam_opt["C_growth_rate"],
        }

    # Summary per checkpoint for optimal lambda
    if lam_opt:
        results["summary_optimal"] = {
            "A_C_gap_step_50":  lam_opt["AC_gap_by_step"].get("50"),
            "A_C_gap_step_100": lam_opt["AC_gap_by_step"].get("100"),
            "A_C_gap_step_200": lam_opt["AC_gap_by_step"].get("200"),
            "A_growth_mean":    lam_opt["A_growth_rate"]["mean"],
            "C_growth_mean":    lam_opt["C_growth_rate"]["mean"],
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests(grad_ref_flat):
    """lambda=0.0: no regularization, should revert to prior failure mode
    (A > C only early, collapses at step 50+).
    """
    results = {}
    print("  Negative: lambda=0...")
    r = run_one_lambda(0.0, grad_ref_flat)

    results["lambda_0_result"] = r
    # Prior behavior: A > C at step 10 but NOT at 200
    # (from sim_torch_gnn_extended_training: crossover mean=6.4, noise grows faster)
    a10  = r["A_mean_by_step"].get("10")
    c10  = r["C_mean_by_step"].get("10")
    a200 = r["A_mean_by_step"].get("200")
    c200 = r["C_mean_by_step"].get("200")

    results["A_ahead_at_step_10"]  = bool((a10 or 0) > (c10 or 0))
    results["A_ahead_at_step_200"] = bool((a200 or 0) > (c200 or 0))
    results["revert_confirmed"] = (
        results["A_ahead_at_step_10"] and not results["A_ahead_at_step_200"]
    )
    results["interpretation"] = (
        "lambda=0 reverts to prior behavior (A leads early, C catches up)"
        if results["revert_confirmed"]
        else "lambda=0 does NOT revert to prior behavior — check vs extended training result"
    )

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests(grad_ref_flat):
    """lambda=1.0: heavy regularization may collapse all three to same trajectory."""
    results = {}
    print("  Boundary: lambda=1.0...")
    r = run_one_lambda(1.0, grad_ref_flat)

    results["lambda_1_result"] = r

    a200 = r["A_mean_by_step"].get("200")
    b200 = r["B_mean_by_step"].get("200")
    c200 = r["C_mean_by_step"].get("200")

    if all(v is not None for v in [a200, b200, c200]):
        spread = max(a200, b200, c200) - min(a200, b200, c200)
        results["spread_at_200"] = float(spread)
        results["collapse_observed"] = bool(spread < 0.05)
        results["A_C_gap_200"] = float(a200 - c200)
    else:
        results["spread_at_200"] = None
        results["collapse_observed"] = None
        results["A_C_gap_200"] = None

    results["interpretation"] = (
        "lambda=1.0 collapses all three trajectories (spread < 0.05)"
        if results.get("collapse_observed")
        else "lambda=1.0 does NOT fully collapse trajectories"
    )

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Building axis-0 gradient reference...")
    grad_ref_flat = build_axis0_grad_ref(seed=42)
    print(f"  grad_ref norm={grad_ref_flat.norm().item():.4f}, "
          f"shape={list(grad_ref_flat.shape)}")

    print("Running positive tests (lambda sweep)...")
    pos = {}
    try:
        pos = run_positive_tests(grad_ref_flat)
    except Exception:
        pos["error"] = traceback.format_exc()

    print("Running negative tests (lambda=0)...")
    neg = {}
    try:
        neg = run_negative_tests(grad_ref_flat)
    except Exception:
        neg["error"] = traceback.format_exc()

    print("Running boundary tests (lambda=1.0)...")
    bnd = {}
    try:
        bnd = run_boundary_tests(grad_ref_flat)
    except Exception:
        bnd["error"] = traceback.format_exc()

    # ── Final report ─────────────────────────────────────────────────
    print("\n=== RESULTS SUMMARY ===")
    opt_lam = pos.get("optimal_lambda")
    print(f"Optimal lambda: {opt_lam}")

    if "summary_optimal" in pos:
        s = pos["summary_optimal"]
        print(f"  A-C gap @ step  50: {s.get('A_C_gap_step_50', 'N/A'):.4f}")
        print(f"  A-C gap @ step 100: {s.get('A_C_gap_step_100', 'N/A'):.4f}")
        print(f"  A-C gap @ step 200: {s.get('A_C_gap_step_200', 'N/A'):.4f}")
        print(f"  A growth rate: {s.get('A_growth_mean', 'N/A'):.5f}")
        print(f"  C growth rate: {s.get('C_growth_mean', 'N/A'):.5f}")

    print(f"Regularization maintains A>C: {pos.get('opt_maintains_A_gt_C')}")
    print(f"lambda=0 reverts to prior:    {neg.get('revert_confirmed')}")
    print(f"lambda=1.0 collapses:         {bnd.get('collapse_observed')}")

    results = {
        "name":                  "torch_gnn_loss_regularized",
        "description":           (
            "Loss regularization: L = -I_c + lambda*(1-cos_sim(op_params, grad_ref)). "
            "Tests whether wiring axis-0 gradient into loss maintains A>C beyond step 50."
        ),
        "tool_manifest":         TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive":              pos,
        "negative":              neg,
        "boundary":              bnd,
        "classification":        "canonical",
        "config": {
            "seeds":            SEEDS,
            "n_steps":          N_STEPS,
            "checkpoint_steps": CHECKPOINT_STEPS,
            "lambda_sweep":     LAMBDA_SWEEP,
            "lr":               LR,
            "n_terrain":        N_TERRAIN,
            "n_operator":       N_OPERATOR,
            "n_shell":          N_SHELL,
            "n_layers":         N_LAYERS,
        },
    }

    out_dir  = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_gnn_loss_regularized_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
