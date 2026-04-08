#!/usr/bin/env python3
"""
GNN Gradient Reference Ablation
================================

Finding: The directional gate sim (torch_gnn_directional_gate) found A > C only
1/5 seeds because the 7D ∇I_c is projected to 3D via a crude first-3-component
slice. The dominant gradient components are r_A (idx 4) and r_B (idx 5), which
are discarded by the 3D slice.

This sim tests THREE gradient reference methods as ablations:

  Method 1 (Full 7D):  Expand OPERATOR_DIM to 7. No projection loss.
  Method 2 (PCA 3D):   Project 7D gradient to 3D via PCA top-3 directions
                        computed over 20 random states.
  Method 3 (Learned):  Warmup phase (20 steps) trains W: R^7 → R^3 to align
                        operator features with gradient direction, then 50-step
                        main optimization with frozen projection.

For each method: 3 seeding conditions (A=gradient-aligned, B=anti-gradient,
C=noise) × 5 seeds each.

Key test: which method gives the largest A - C gap?
Secondary: does any method achieve A > C on 4/5 or 5/5 seeds?

Mark pytorch=load_bearing, pyg=load_bearing.
Output: system_v4/probes/a2_state/sim_results/torch_gnn_gradient_ref_ablation_results.json
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
        "Axis 0 gradient via autograd; GNN tensors; directional gate; PCA; learned projection"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

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
# AXIS 0: 3-QUBIT GRADIENT FIELD (7D)
# =====================================================================

DTYPE = torch.complex128
FDTYPE = torch.float64

I2 = torch.eye(2, dtype=DTYPE)

PARAM_NAMES = ["theta_AB", "theta_BC", "phi_AB", "phi_BC", "r_A", "r_B", "r_C"]


def build_single_qubit_state(theta, phi, r):
    ct2 = torch.cos(theta / 2)
    st2 = torch.sin(theta / 2)
    psi = torch.stack([
        ct2.to(DTYPE),
        (st2 * torch.exp(1j * phi.to(DTYPE))).to(DTYPE),
    ])
    rho_pure = torch.outer(psi, psi.conj())
    rho = r.to(DTYPE) * rho_pure + (1.0 - r.to(DTYPE)) * I2 / 2.0
    return rho


def build_cnot_3q_AB():
    CNOT_2Q = torch.tensor([
        [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0],
    ], dtype=DTYPE)
    return torch.kron(CNOT_2Q, I2)


def build_cnot_3q_BC():
    CNOT_2Q = torch.tensor([
        [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0],
    ], dtype=DTYPE)
    return torch.kron(I2, CNOT_2Q)


def z_dephasing_channel(rho_8x8, p):
    SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    I2loc = torch.eye(2, dtype=DTYPE)
    Z_A = torch.kron(torch.kron(SZ, I2loc), I2loc)
    rho_out = (1.0 - p.to(DTYPE)) * rho_8x8 + p.to(DTYPE) * (Z_A @ rho_8x8 @ Z_A)
    return rho_out


def build_3qubit_rho(theta_AB, theta_BC, phi_AB, phi_BC, r_A, r_B, r_C,
                     apply_relay=True, dephasing_p=None):
    rho_A = build_single_qubit_state(theta_AB, phi_AB, r_A)
    rho_B = build_single_qubit_state(theta_BC, phi_BC, r_B)
    rho_C = build_single_qubit_state(
        torch.tensor(0.0, dtype=FDTYPE),
        torch.tensor(0.0, dtype=FDTYPE),
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
    eta = [torch.tensor(v, dtype=FDTYPE, requires_grad=True) for v in eta_vals]
    dp = torch.tensor(0.05, dtype=FDTYPE)
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


def compute_pca_gradient_basis(n_states=20, seed=0):
    """Compute PCA top-3 directions of ∇I_c across n_states random states.

    Returns: grads_matrix [n_states, 7], pca_components [3, 7]
    """
    rng = np.random.default_rng(seed)
    grads = []
    for _ in range(n_states):
        theta_AB = rng.uniform(0.1, np.pi - 0.1)
        theta_BC = rng.uniform(0.1, np.pi - 0.1)
        phi_AB = rng.uniform(0, 2 * np.pi)
        phi_BC = rng.uniform(0, 2 * np.pi)
        r_A = rng.uniform(0.4, 0.95)
        r_B = rng.uniform(0.4, 0.95)
        r_C = rng.uniform(0.4, 0.95)
        try:
            result = compute_axis0_gradient((theta_AB, theta_BC, phi_AB, phi_BC, r_A, r_B, r_C))
            g = result["grad"]
            if np.linalg.norm(g) > 1e-6:
                grads.append(g)
        except Exception:
            pass

    grads_matrix = np.array(grads)  # [n_valid, 7]
    # Center
    mean_grad = grads_matrix.mean(axis=0)
    centered = grads_matrix - mean_grad
    # SVD for PCA
    _, _, Vt = np.linalg.svd(centered, full_matrices=False)
    # Top-3 principal components (rows of Vt)
    pca_components = Vt[:3]  # [3, 7]
    return pca_components, grads_matrix


# =====================================================================
# GNN COMPONENTS (shared)
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


class DirectionalShellGate(MessagePassing):
    """Cosine-similarity gate between operator features and a fixed gradient reference."""

    def __init__(self, shell_dim, op_dim, gradient_ref):
        super().__init__(aggr="mean")
        self.op_dim = op_dim
        self.shell_proj = nn.Linear(shell_dim, op_dim)
        self.register_buffer("gradient_ref", gradient_ref.float())

    def forward(self, x_src, x_dst, edge_index):
        return self.propagate(
            edge_index, x=x_src, x_dst=x_dst,
            size=(x_src.size(0), x_dst.size(0)),
        )

    def message(self, x_j):
        return self.shell_proj(x_j)

    def update(self, aggr_out, x_dst):
        ref = self.gradient_ref.unsqueeze(0)
        gate = F.cosine_similarity(x_dst, ref, dim=-1)
        gate = (gate * 0.5 + 0.5).unsqueeze(-1)
        return x_dst * gate


# =====================================================================
# RATCHET GNN -- parametric OPERATOR_DIM
# =====================================================================

class RatchetGNNParametric(nn.Module):
    """Ratchet GNN with configurable OPERATOR_DIM and SHELL_DIM.

    Used for Method 1 (Full 7D) and Method 2 (PCA 3D).
    shell_dim and op_dim are both set to match the chosen gradient reference space.
    """

    TERRAIN_DIM = 3

    def __init__(self, n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
                 op_dim=3, shell_dim=3,
                 shell_init=None, gradient_ref=None):
        super().__init__()
        self.n_terrain = n_terrain
        self.n_operator = n_operator
        self.n_shell = n_shell
        self.n_layers = n_layers
        self.op_dim = op_dim
        self.shell_dim = shell_dim

        self.operator_params = nn.Parameter(
            torch.rand(n_operator, op_dim) * 0.3 + 0.1
        )

        if shell_init is not None:
            self.shell_params = nn.Parameter(shell_init.clone().float())
        else:
            self.shell_params = nn.Parameter(
                torch.rand(n_shell, shell_dim) * 0.5 + 0.25
            )

        if gradient_ref is None:
            ref = torch.zeros(op_dim)
            ref[0] = 1.0
        else:
            ref = gradient_ref.float()
            norm = torch.norm(ref)
            if norm > 1e-8:
                ref = ref / norm

        self.directional_gate_layers = nn.ModuleList([
            DirectionalShellGate(shell_dim, op_dim, ref)
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
            operator_x = self.directional_gate_layers[layer_idx](
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
# RATCHET GNN -- Learned projection (Method 3)
# =====================================================================

class RatchetGNNLearnedProj(nn.Module):
    """Method 3: 7D shell/operator + a learned W: R^7 → R^3 projection
    that is trained during a warmup phase to align operators with ∇I_c.

    After warmup, W is frozen and main optimization runs over operator/shell params.
    The gradient reference passed through W becomes the effective 3D reference.
    """

    TERRAIN_DIM = 3
    GRAD_DIM = 7   # full 7D parameter space
    OP_DIM = 3     # projected operator space

    def __init__(self, n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
                 shell_init=None, gradient_ref_7d=None):
        super().__init__()
        self.n_terrain = n_terrain
        self.n_operator = n_operator
        self.n_shell = n_shell
        self.n_layers = n_layers

        # Learned linear projection W: R^7 → R^3
        self.proj = nn.Linear(self.GRAD_DIM, self.OP_DIM, bias=False)
        nn.init.orthogonal_(self.proj.weight)

        # Operator params live in 7D (same space as gradient)
        self.operator_params = nn.Parameter(
            torch.rand(n_operator, self.GRAD_DIM) * 0.3 + 0.1
        )

        if shell_init is not None:
            self.shell_params = nn.Parameter(shell_init.clone().float())
        else:
            self.shell_params = nn.Parameter(
                torch.rand(n_shell, self.GRAD_DIM) * 0.5 + 0.25
            )

        # Store 7D gradient reference for warmup alignment loss
        if gradient_ref_7d is not None:
            ref7 = gradient_ref_7d.float()
            norm = torch.norm(ref7)
            if norm > 1e-8:
                ref7 = ref7 / norm
        else:
            ref7 = torch.zeros(self.GRAD_DIM)
            ref7[0] = 1.0
        self.register_buffer("gradient_ref_7d", ref7)

        # Gate layers use projected 3D space
        self.directional_gate_layers = nn.ModuleList([
            DirectionalShellGate(self.OP_DIM, self.OP_DIM,
                                 torch.zeros(self.OP_DIM))  # placeholder; updated in forward
            for _ in range(n_layers)
        ])
        self.terrain_to_op_layers = nn.ModuleList([
            TerrainToOperatorConv(self.TERRAIN_DIM, self.OP_DIM)
            for _ in range(n_layers)
        ])
        self.op_to_terrain_layers = nn.ModuleList([
            OperatorToTerrainConv(self.OP_DIM, self.TERRAIN_DIM)
            for _ in range(n_layers)
        ])

    def get_projected_ref(self):
        """Project 7D gradient reference through learned W → 3D unit vector."""
        proj_ref = self.proj(self.gradient_ref_7d.unsqueeze(0)).squeeze(0)
        norm = torch.norm(proj_ref)
        if norm > 1e-8:
            proj_ref = proj_ref / norm
        return proj_ref

    def warmup_alignment_loss(self):
        """Loss to align W(operator_params) with W(gradient_ref_7d).
        Maximizes cosine similarity between projected operator features and projected gradient.
        """
        proj_ops = self.proj(self.operator_params)        # [n_op, 3]
        proj_ref = self.get_projected_ref().unsqueeze(0)  # [1, 3]
        cos_sim = F.cosine_similarity(proj_ops, proj_ref.expand_as(proj_ops), dim=-1)
        return -cos_sim.mean()

    def build_graph(self, terrain_bloch, proj_shell, proj_ops):
        data = HeteroData()
        data["terrain"].x = terrain_bloch
        data["operator"].x = proj_ops
        data["shell"].x = proj_shell

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
        # Project operator and shell features to 3D
        proj_ops = self.proj(self.operator_params)    # [n_op, 3]
        proj_shell = self.proj(self.shell_params)     # [n_shell, 3]

        # Update gate buffers with current projected reference
        proj_ref = self.get_projected_ref()
        for gate_layer in self.directional_gate_layers:
            gate_layer.gradient_ref.copy_(proj_ref.detach())

        data = self.build_graph(terrain_bloch, proj_shell, proj_ops)
        terrain_x = data["terrain"].x
        operator_x = data["operator"].x
        shell_x = data["shell"].x

        for layer_idx in range(self.n_layers):
            shell_op_ei = data["shell", "constrains", "operator"].edge_index
            operator_x = self.directional_gate_layers[layer_idx](
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
# SEEDING HELPERS -- unified across methods
# =====================================================================

INIT_BLOCH = torch.tensor([
    [0.5,  0.3,  0.1],
    [-0.2, 0.4,  0.6],
    [0.1, -0.3,  0.8],
    [0.4,  0.2, -0.5],
], dtype=torch.float32)


def make_shell_aligned(grad_7d, dim):
    """Shell features ∝ +∇I_c in `dim` dimensions."""
    if dim == 7:
        g = grad_7d.copy()
    elif dim == 3:
        g = grad_7d[:3].copy()
    else:
        raise ValueError(f"Unsupported dim={dim}")
    mag = float(np.linalg.norm(g))

    shell_rows = []
    for start in range(0, len(g), max(1, len(g) // 2)):
        chunk = g[start:start + len(g) // 2] if len(g) > 1 else g
        row = [float(np.tanh(abs(v))) for v in chunk]
        # pad or trim to dim
        while len(row) < dim:
            row.append(float(np.tanh(mag)))
        row = row[:dim]
        shell_rows.append(row)
        if len(shell_rows) >= 2:
            break
    while len(shell_rows) < 2:
        shell_rows.append([float(np.tanh(mag))] * dim)
    return torch.tensor(shell_rows[:2], dtype=torch.float32)


def make_shell_anti(grad_7d, dim):
    """Shell features ∝ -∇I_c in `dim` dimensions."""
    aligned = make_shell_aligned(grad_7d, dim)
    return 1.0 - aligned


def make_shell_noise(seed, dim, n_shell=2):
    """Shell features = pure Gaussian noise."""
    rng = np.random.default_rng(seed)
    raw = rng.standard_normal((n_shell, dim)).astype(np.float32)
    raw = (raw - raw.min()) / (raw.max() - raw.min() + 1e-8) * 0.8 + 0.1
    return torch.tensor(raw, dtype=torch.float32)


def run_optimization(model, n_steps=50, lr=0.01, seed=42):
    """Run main GNN optimization. Returns I_c history."""
    torch.manual_seed(seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    ic_history = []
    for _ in range(n_steps):
        optimizer.zero_grad()
        out = model(INIT_BLOCH)
        loss = -out["ic_mean"]
        loss.backward()
        optimizer.step()
        ic_history.append(float(out["ic_mean"].item()))
    return ic_history


def run_warmup_then_optimize(model, n_warmup=20, n_main=50, lr=0.01, seed=42):
    """Method 3 protocol: warmup to align W, then freeze W and optimize."""
    torch.manual_seed(seed)

    # Warmup: optimize W (and operator_params) with alignment loss
    warmup_optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    warmup_history = []
    for _ in range(n_warmup):
        warmup_optimizer.zero_grad()
        loss = model.warmup_alignment_loss()
        loss.backward()
        warmup_optimizer.step()
        warmup_history.append(float(loss.item()))

    # Freeze the projection W
    for p in model.proj.parameters():
        p.requires_grad_(False)

    # Main optimization: maximize I_c with frozen W
    main_optimizer = torch.optim.Adam(
        [p for p in model.parameters() if p.requires_grad], lr=lr
    )
    ic_history = []
    for _ in range(n_main):
        main_optimizer.zero_grad()
        out = model(INIT_BLOCH)
        loss = -out["ic_mean"]
        loss.backward()
        main_optimizer.step()
        ic_history.append(float(out["ic_mean"].item()))

    return ic_history, warmup_history


def score_seeds(A_ends, B_ends, C_ends):
    """Compute summary statistics over 5 seeds."""
    mean_A = float(np.mean(A_ends))
    mean_B = float(np.mean(B_ends))
    mean_C = float(np.mean(C_ends))
    n_A_gt_B = sum(1 for a, b in zip(A_ends, B_ends) if a > b)
    n_A_gt_C = sum(1 for a, c in zip(A_ends, C_ends) if a > c)
    n_C_gt_B = sum(1 for c, b in zip(C_ends, B_ends) if c > b)
    n_ordered = sum(
        1 for a, b, c in zip(A_ends, B_ends, C_ends)
        if (a > c) and (c > b)
    )
    return {
        "mean_A": mean_A,
        "mean_B": mean_B,
        "mean_C": mean_C,
        "A_minus_B": mean_A - mean_B,
        "A_minus_C": mean_A - mean_C,
        "C_minus_B": mean_C - mean_B,
        "n_A_gt_B": n_A_gt_B,
        "n_A_gt_C": n_A_gt_C,
        "n_C_gt_B": n_C_gt_B,
        "n_correct_ordering": n_ordered,
        "A_gt_C_4_or_5_seeds": n_A_gt_C >= 4,
    }


# =====================================================================
# METHOD 1: FULL 7D
# =====================================================================

def run_method1_full7d(axis0):
    """Expand OPERATOR_DIM=7. Gradient reference = full normalized 7D ∇I_c."""
    grad_7d = axis0["grad"]
    grad_ref_7d = torch.tensor(grad_7d / (np.linalg.norm(grad_7d) + 1e-12), dtype=torch.float32)

    op_seeds = [42, 7, 99, 13, 55]
    A_ends, B_ends, C_ends = [], [], []
    per_seed = []

    for op_seed in op_seeds:
        torch.manual_seed(op_seed)
        op_params_init = torch.rand(3, 7) * 0.3 + 0.1

        shell_A = make_shell_aligned(grad_7d, dim=7)
        shell_B = make_shell_anti(grad_7d, dim=7)
        shell_C = make_shell_noise(seed=op_seed * 17 + 3, dim=7)

        def _make(shell_init):
            m = RatchetGNNParametric(
                n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
                op_dim=7, shell_dim=7,
                shell_init=shell_init, gradient_ref=grad_ref_7d,
            )
            with torch.no_grad():
                m.operator_params.copy_(op_params_init)
            return m

        mA, mB, mC = _make(shell_A), _make(shell_B), _make(shell_C)
        ic_A = run_optimization(mA, n_steps=50, lr=0.01, seed=op_seed)
        ic_B = run_optimization(mB, n_steps=50, lr=0.01, seed=op_seed)
        ic_C = run_optimization(mC, n_steps=50, lr=0.01, seed=op_seed)

        a_end = float(np.mean(ic_A[-5:]))
        b_end = float(np.mean(ic_B[-5:]))
        c_end = float(np.mean(ic_C[-5:]))
        A_ends.append(a_end)
        B_ends.append(b_end)
        C_ends.append(c_end)

        per_seed.append({
            "op_seed": op_seed,
            "A": a_end, "B": b_end, "C": c_end,
            "A_gt_B": a_end > b_end,
            "A_gt_C": a_end > c_end,
            "C_gt_B": c_end > b_end,
            "ordering_correct": (a_end > c_end) and (c_end > b_end),
        })

    summary = score_seeds(A_ends, B_ends, C_ends)
    summary["per_seed"] = per_seed
    summary["gradient_ref_7d"] = grad_ref_7d.tolist()
    return summary


# =====================================================================
# METHOD 2: PCA PROJECTION 3D
# =====================================================================

def run_method2_pca(axis0, pca_components):
    """Project 7D gradient to 3D using top-3 PCA components."""
    grad_7d = axis0["grad"]

    # PCA-project gradient reference
    grad_ref_7d = grad_7d / (np.linalg.norm(grad_7d) + 1e-12)
    grad_ref_3d = pca_components @ grad_ref_7d  # [3]
    norm_3d = np.linalg.norm(grad_ref_3d)
    if norm_3d > 1e-8:
        grad_ref_3d = grad_ref_3d / norm_3d
    grad_ref_tensor = torch.tensor(grad_ref_3d, dtype=torch.float32)

    # Also project shell init features via PCA
    # Shell features: encode gradient via PCA projection into 3D
    def project_7d_to_3d_shell(shell_7d):
        """Project a [2, 7] shell tensor to [2, 3] via PCA components."""
        shell_np = shell_7d.numpy()  # [2, 7]
        shell_3d = shell_np @ pca_components.T  # [2, 3]
        # Normalize to [0.1, 0.9]
        mn, mx = shell_3d.min(), shell_3d.max()
        shell_3d = (shell_3d - mn) / (mx - mn + 1e-8) * 0.8 + 0.1
        return torch.tensor(shell_3d, dtype=torch.float32)

    op_seeds = [42, 7, 99, 13, 55]
    A_ends, B_ends, C_ends = [], [], []
    per_seed = []

    for op_seed in op_seeds:
        torch.manual_seed(op_seed)
        op_params_init = torch.rand(3, 3) * 0.3 + 0.1

        # Build 7D shells, then PCA-project to 3D
        shell_A_7d = make_shell_aligned(grad_7d, dim=7)
        shell_B_7d = make_shell_anti(grad_7d, dim=7)
        shell_C_7d = make_shell_noise(seed=op_seed * 17 + 3, dim=7)

        shell_A = project_7d_to_3d_shell(shell_A_7d)
        shell_B = project_7d_to_3d_shell(shell_B_7d)
        shell_C = project_7d_to_3d_shell(shell_C_7d)

        def _make(shell_init):
            m = RatchetGNNParametric(
                n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
                op_dim=3, shell_dim=3,
                shell_init=shell_init, gradient_ref=grad_ref_tensor,
            )
            with torch.no_grad():
                m.operator_params.copy_(op_params_init)
            return m

        mA, mB, mC = _make(shell_A), _make(shell_B), _make(shell_C)
        ic_A = run_optimization(mA, n_steps=50, lr=0.01, seed=op_seed)
        ic_B = run_optimization(mB, n_steps=50, lr=0.01, seed=op_seed)
        ic_C = run_optimization(mC, n_steps=50, lr=0.01, seed=op_seed)

        a_end = float(np.mean(ic_A[-5:]))
        b_end = float(np.mean(ic_B[-5:]))
        c_end = float(np.mean(ic_C[-5:]))
        A_ends.append(a_end)
        B_ends.append(b_end)
        C_ends.append(c_end)

        per_seed.append({
            "op_seed": op_seed,
            "A": a_end, "B": b_end, "C": c_end,
            "A_gt_B": a_end > b_end,
            "A_gt_C": a_end > c_end,
            "C_gt_B": c_end > b_end,
            "ordering_correct": (a_end > c_end) and (c_end > b_end),
        })

    summary = score_seeds(A_ends, B_ends, C_ends)
    summary["per_seed"] = per_seed
    summary["pca_components"] = pca_components.tolist()
    summary["grad_ref_3d"] = grad_ref_tensor.tolist()
    return summary


# =====================================================================
# METHOD 3: LEARNED PROJECTION
# =====================================================================

def run_method3_learned(axis0):
    """Warmup trains W: R^7→R^3 to align operators with ∇I_c, then main opt."""
    grad_7d = axis0["grad"]
    grad_ref_7d = torch.tensor(
        grad_7d / (np.linalg.norm(grad_7d) + 1e-12), dtype=torch.float32
    )

    op_seeds = [42, 7, 99, 13, 55]
    A_ends, B_ends, C_ends = [], [], []
    per_seed = []
    warmup_losses_by_seed = {}

    for op_seed in op_seeds:
        torch.manual_seed(op_seed)
        op_params_init = torch.rand(3, 7) * 0.3 + 0.1

        shell_A = make_shell_aligned(grad_7d, dim=7)
        shell_B = make_shell_anti(grad_7d, dim=7)
        shell_C = make_shell_noise(seed=op_seed * 17 + 3, dim=7)

        def _make(shell_init, proj_seed):
            torch.manual_seed(proj_seed)
            m = RatchetGNNLearnedProj(
                n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
                shell_init=shell_init,
                gradient_ref_7d=grad_ref_7d,
            )
            with torch.no_grad():
                m.operator_params.copy_(op_params_init)
            return m

        mA = _make(shell_A, op_seed)
        mB = _make(shell_B, op_seed + 1000)
        mC = _make(shell_C, op_seed + 2000)

        ic_A, wl_A = run_warmup_then_optimize(mA, n_warmup=20, n_main=50, lr=0.01, seed=op_seed)
        ic_B, wl_B = run_warmup_then_optimize(mB, n_warmup=20, n_main=50, lr=0.01, seed=op_seed)
        ic_C, wl_C = run_warmup_then_optimize(mC, n_warmup=20, n_main=50, lr=0.01, seed=op_seed)

        a_end = float(np.mean(ic_A[-5:]))
        b_end = float(np.mean(ic_B[-5:]))
        c_end = float(np.mean(ic_C[-5:]))
        A_ends.append(a_end)
        B_ends.append(b_end)
        C_ends.append(c_end)

        per_seed.append({
            "op_seed": op_seed,
            "A": a_end, "B": b_end, "C": c_end,
            "A_gt_B": a_end > b_end,
            "A_gt_C": a_end > c_end,
            "C_gt_B": c_end > b_end,
            "ordering_correct": (a_end > c_end) and (c_end > b_end),
            "warmup_loss_final_A": float(wl_A[-1]) if wl_A else None,
        })
        warmup_losses_by_seed[str(op_seed)] = {
            "A_warmup_loss_final": float(wl_A[-1]) if wl_A else None,
            "B_warmup_loss_final": float(wl_B[-1]) if wl_B else None,
            "C_warmup_loss_final": float(wl_C[-1]) if wl_C else None,
        }

    summary = score_seeds(A_ends, B_ends, C_ends)
    summary["per_seed"] = per_seed
    summary["warmup_losses_by_seed"] = warmup_losses_by_seed
    return summary


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ── Step 1: Compute Axis 0 gradient ─────────────────────────────
    axis0 = None
    try:
        eta_vals = (np.pi / 3, np.pi / 4, np.pi / 5, np.pi / 6, 0.8, 0.7, 0.6)
        axis0 = compute_axis0_gradient(eta_vals)
        results["axis0_gradient"] = {
            "passed": axis0["grad_magnitude"] > 0.1,
            "I_c": axis0["I_c"],
            "grad_magnitude": axis0["grad_magnitude"],
            "grad_components": {PARAM_NAMES[i]: float(axis0["grad"][i]) for i in range(7)},
            "dominant_indices": sorted(
                range(7), key=lambda i: abs(axis0["grad"][i]), reverse=True
            )[:3],
        }
    except Exception as e:
        results["axis0_gradient"] = {"passed": False, "error": str(e)}
        return results, None, None

    # ── Step 2: Compute PCA basis ────────────────────────────────────
    pca_components = None
    try:
        pca_components, grads_matrix = compute_pca_gradient_basis(n_states=20, seed=0)
        # Variance explained: how much of total gradient variance is in top-3 PCs
        total_var = float(np.var(grads_matrix, axis=0).sum())
        proj_var = float(np.var(grads_matrix @ pca_components.T, axis=0).sum())
        results["pca_basis"] = {
            "passed": pca_components.shape == (3, 7),
            "pca_components_shape": list(pca_components.shape),
            "variance_retained_pct": float(100.0 * proj_var / (total_var + 1e-12)),
            "n_states_used": grads_matrix.shape[0],
        }
    except Exception as e:
        results["pca_basis"] = {"passed": False, "error": str(e), "traceback": traceback.format_exc()}
        pca_components = None

    # ── Step 3: Method 1 — Full 7D ──────────────────────────────────
    try:
        m1 = run_method1_full7d(axis0)
        results["method1_full7d"] = {
            "passed": m1["n_A_gt_C"] >= 3,  # improvement over baseline (1/5)
            **m1,
        }
    except Exception as e:
        results["method1_full7d"] = {"passed": False, "error": str(e), "traceback": traceback.format_exc()}

    # ── Step 4: Method 2 — PCA 3D ───────────────────────────────────
    if pca_components is not None:
        try:
            m2 = run_method2_pca(axis0, pca_components)
            results["method2_pca3d"] = {
                "passed": m2["n_A_gt_C"] >= 3,
                **m2,
            }
        except Exception as e:
            results["method2_pca3d"] = {"passed": False, "error": str(e), "traceback": traceback.format_exc()}
    else:
        results["method2_pca3d"] = {"passed": False, "error": "PCA basis unavailable"}

    # ── Step 5: Method 3 — Learned projection ───────────────────────
    try:
        m3 = run_method3_learned(axis0)
        results["method3_learned"] = {
            "passed": m3["n_A_gt_C"] >= 3,
            **m3,
        }
    except Exception as e:
        results["method3_learned"] = {"passed": False, "error": str(e), "traceback": traceback.format_exc()}

    # ── Step 6: Comparison summary ───────────────────────────────────
    try:
        methods = {}
        for key, label in [
            ("method1_full7d", "Full 7D"),
            ("method2_pca3d", "PCA 3D"),
            ("method3_learned", "Learned proj"),
        ]:
            if "mean_A" in results.get(key, {}):
                r = results[key]
                methods[key] = {
                    "label": label,
                    "mean_A": r["mean_A"],
                    "mean_B": r["mean_B"],
                    "mean_C": r["mean_C"],
                    "A_minus_C": r["A_minus_C"],
                    "n_A_gt_C": r["n_A_gt_C"],
                    "n_correct_ordering": r["n_correct_ordering"],
                    "A_gt_C_4_or_5_seeds": r["A_gt_C_4_or_5_seeds"],
                }

        if methods:
            best_key = max(methods, key=lambda k: methods[k]["A_minus_C"])
            best_win_rate_key = max(methods, key=lambda k: methods[k]["n_A_gt_C"])
            results["comparison_summary"] = {
                "baseline_n_A_gt_C": 1,
                "baseline_A_minus_C": -0.01278,
                "methods": methods,
                "best_A_minus_C_method": methods[best_key]["label"],
                "best_A_minus_C_value": methods[best_key]["A_minus_C"],
                "best_win_rate_method": methods[best_win_rate_key]["label"],
                "best_win_rate_n_A_gt_C": methods[best_win_rate_key]["n_A_gt_C"],
                "any_method_4_or_5_wins": any(
                    m["A_gt_C_4_or_5_seeds"] for m in methods.values()
                ),
            }
    except Exception as e:
        results["comparison_summary"] = {"error": str(e)}

    return results, axis0, pca_components


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests(axis0):
    results = {}

    # Negative: in any method, anti-gradient (B) should not beat gradient (A) on average
    # This tests that the directional gate still functions correctly with expanded refs
    try:
        if axis0 is None:
            raise RuntimeError("No axis0 data")
        grad_7d = axis0["grad"]
        grad_ref_7d = torch.tensor(
            grad_7d / (np.linalg.norm(grad_7d) + 1e-12), dtype=torch.float32
        )

        torch.manual_seed(0)
        shell_A = make_shell_aligned(grad_7d, dim=7)
        shell_B = make_shell_anti(grad_7d, dim=7)

        mA = RatchetGNNParametric(
            n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
            op_dim=7, shell_dim=7,
            shell_init=shell_A, gradient_ref=grad_ref_7d,
        )
        mB = RatchetGNNParametric(
            n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
            op_dim=7, shell_dim=7,
            shell_init=shell_B, gradient_ref=grad_ref_7d,
        )

        ic_A = run_optimization(mA, n_steps=30, lr=0.01, seed=0)
        ic_B = run_optimization(mB, n_steps=30, lr=0.01, seed=0)
        a_end = float(np.mean(ic_A[-5:]))
        b_end = float(np.mean(ic_B[-5:]))

        results["full7d_A_beats_B_single_seed"] = {
            "passed": a_end > b_end,
            "A_ic_end": a_end,
            "B_ic_end": b_end,
            "A_minus_B": a_end - b_end,
        }
    except Exception as e:
        results["full7d_A_beats_B_single_seed"] = {
            "passed": False, "error": str(e), "traceback": traceback.format_exc()
        }

    # Negative: a completely random gradient ref should NOT reliably separate A from B
    try:
        rng = np.random.default_rng(999)
        random_ref_7d = torch.tensor(rng.standard_normal(7).astype(np.float32))
        random_ref_7d = random_ref_7d / torch.norm(random_ref_7d)

        grad_7d = axis0["grad"]
        shell_A = make_shell_aligned(grad_7d, dim=7)
        shell_B = make_shell_anti(grad_7d, dim=7)

        ends_A, ends_B = [], []
        for seed_val in [42, 7, 99]:
            torch.manual_seed(seed_val)
            mA = RatchetGNNParametric(
                n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
                op_dim=7, shell_dim=7,
                shell_init=shell_A, gradient_ref=random_ref_7d,
            )
            mB = RatchetGNNParametric(
                n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
                op_dim=7, shell_dim=7,
                shell_init=shell_B, gradient_ref=random_ref_7d,
            )
            ic_A = run_optimization(mA, n_steps=30, lr=0.01, seed=seed_val)
            ic_B = run_optimization(mB, n_steps=30, lr=0.01, seed=seed_val)
            ends_A.append(float(np.mean(ic_A[-5:])))
            ends_B.append(float(np.mean(ic_B[-5:])))

        n_A_beats_B = sum(1 for a, b in zip(ends_A, ends_B) if a > b)
        results["random_ref_does_not_separate"] = {
            "passed": n_A_beats_B <= 2,  # random ref should not reliably separate
            "n_A_beats_B_out_of_3": n_A_beats_B,
            "mean_A": float(np.mean(ends_A)),
            "mean_B": float(np.mean(ends_B)),
            "interpretation": (
                "Random gradient reference does not reliably separate A from B (expected)"
                if n_A_beats_B <= 2
                else "Random ref unexpectedly separates A from B (check gradient sensitivity)"
            ),
        }
    except Exception as e:
        results["random_ref_does_not_separate"] = {
            "passed": False, "error": str(e), "traceback": traceback.format_exc()
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests(axis0):
    results = {}

    # Boundary: gradient ref with near-zero norm (degenerate case)
    try:
        grad_7d = axis0["grad"] if axis0 else np.zeros(7)
        shell_A = make_shell_aligned(grad_7d, dim=7)
        zero_ref = torch.zeros(7)
        # Should not crash; gate should default gracefully
        mA = RatchetGNNParametric(
            n_terrain=4, n_operator=3, n_shell=2, n_layers=2,
            op_dim=7, shell_dim=7,
            shell_init=shell_A, gradient_ref=zero_ref,
        )
        ic_A = run_optimization(mA, n_steps=5, lr=0.01, seed=0)
        results["zero_gradient_ref_no_crash"] = {
            "passed": len(ic_A) == 5 and all(np.isfinite(v) for v in ic_A),
            "ic_history": ic_A,
        }
    except Exception as e:
        results["zero_gradient_ref_no_crash"] = {
            "passed": False, "error": str(e), "traceback": traceback.format_exc()
        }

    # Boundary: PCA on single-state (degenerate, n_states=1)
    try:
        if axis0 is not None:
            pca_1, _ = compute_pca_gradient_basis(n_states=3, seed=42)
            results["pca_minimal_states"] = {
                "passed": pca_1.shape == (3, 7),
                "pca_shape": list(pca_1.shape),
            }
        else:
            results["pca_minimal_states"] = {"passed": False, "error": "no axis0"}
    except Exception as e:
        results["pca_minimal_states"] = {
            "passed": False, "error": str(e), "traceback": traceback.format_exc()
        }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive, axis0, pca_components = run_positive_tests()
    negative = run_negative_tests(axis0)
    boundary = run_boundary_tests(axis0)

    results = {
        "name": "torch_gnn_gradient_ref_ablation",
        "description": (
            "Ablation of three gradient reference projection methods (Full 7D, PCA 3D, Learned W) "
            "to fix the direction-sensitivity bottleneck from the crude 3D first-component slice. "
            "Tests whether A > C holds more consistently than baseline (1/5 seeds)."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_gnn_gradient_ref_ablation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    # Print summary to stdout
    print("\n=== GRADIENT REF ABLATION SUMMARY ===")
    if "comparison_summary" in positive:
        cs = positive["comparison_summary"]
        print(f"Baseline (3D slice): n_A_gt_C = {cs['baseline_n_A_gt_C']}/5, A-C = {cs['baseline_A_minus_C']:.5f}")
        for key, m in cs["methods"].items():
            print(f"\n{m['label']}:")
            print(f"  mean A={m['mean_A']:.5f}  B={m['mean_B']:.5f}  C={m['mean_C']:.5f}")
            print(f"  A-C gap = {m['A_minus_C']:.5f}  |  n_A_gt_C = {m['n_A_gt_C']}/5")
            print(f"  4/5 or 5/5 wins: {m['A_gt_C_4_or_5_seeds']}")
        print(f"\nBest A-C gap: {cs['best_A_minus_C_method']} ({cs['best_A_minus_C_value']:.5f})")
        print(f"Best win rate: {cs['best_win_rate_method']} ({cs['best_win_rate_n_A_gt_C']}/5 seeds)")
        print(f"Any method 4/5+ wins: {cs['any_method_4_or_5_wins']}")
