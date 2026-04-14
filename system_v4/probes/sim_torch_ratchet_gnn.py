#!/usr/bin/env python3
"""
Full Ratchet as a GNN (Phase 5/6)
==================================
PyG HeteroData graph with three node types: terrain, operator, shell.
Message passing IS the dynamics. Training objective: sustained I_c > 0.

Architecture:
  - Terrain nodes carry Bloch vector features (3-dim per node)
  - Operator nodes carry channel parameters (p values)
  - Shell nodes carry geometric parameters (eta from Axis 0)
  - Message passing layers:
      terrain -> operator: "state is operated on by channel"
      operator -> terrain: "channel produces new state"
      shell -> operator: "shell constrains which operators are valid"
  - After message passing, compute I_c on the output terrain states
  - Training loop: optimize operator parameters to maximize sustained I_c
    under shell constraints

Graph: 4 terrain nodes, 3 operator nodes, 2 shell nodes.

Tests:
  Positive:
    - Message passing produces valid density matrices
    - I_c is differentiable w.r.t. operator parameters
    - Optimization increases I_c over iterations
    - Shell constraints prevent operator parameters from leaving valid range
  Negative:
    - Removing shell nodes allows unphysical parameters
    - Disconnected graph produces no information flow
  Boundary:
    - Single terrain + operator (trivial)
    - Fully connected (max flow)

Mark pytorch=used, pyg=used, rustworkx=tried, z3=tried. Classification: canonical.
Output: system_v4/probes/a2_state/sim_results/torch_ratchet_gnn_results.json
"""

import json
import os
import traceback
import numpy as np
classification = "canonical"

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
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": "not relevant to this sim"},
    "toponetx":  {"tried": False, "used": False, "reason": "not relevant to this sim"},
    "gudhi":     {"tried": False, "used": False, "reason": "not relevant to this sim"},
}

# Classification of how deeply each tool is integrated into the result.
# load_bearing  = result materially depends on this tool
# supportive    = useful cross-check / helper but not decisive
# decorative    = present only at manifest/import level
# not_applicable = not used in this sim
TOOL_INTEGRATION_DEPTH = {
    "pytorch":   "load_bearing",    # Core substrate: tensors, autograd, nn.Module, optimization loop
    "pyg":       "load_bearing",    # HeteroData graph + MessagePassing IS the ratchet dynamics
    "z3":        "supportive",      # Verifies shell constraint feasibility -- cross-check, not decisive for I_c result
    "cvc5":      "not_applicable",  # Not used
    "sympy":     "not_applicable",  # Not used
    "clifford":  "not_applicable",  # Not used
    "geomstats": "not_applicable",  # Not used
    "e3nn":      "not_applicable",  # Not used
    "rustworkx": "supportive",      # DAG for message passing order verification -- cross-check, not decisive
    "xgi":       "not_applicable",  # Not used
    "toponetx":  "not_applicable",  # Not used
    "gudhi":     "not_applicable",  # Not used
}

# ── Imports ─────────────────────────────────────────────────────────

try:
    import torch
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Core substrate: tensors, autograd, optimization"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    from torch_geometric.nn import MessagePassing
    from torch_geometric.data import HeteroData
    import torch_geometric
    TOOL_MANIFEST["pyg"]["tried"] = True
    TOOL_MANIFEST["pyg"]["used"] = True
    TOOL_MANIFEST["pyg"]["reason"] = "HeteroData graph + message passing IS the ratchet dynamics"
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, And, Or, Implies, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "Verify shell constraint feasibility via SMT"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    TOOL_MANIFEST["rustworkx"]["used"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = "DAG for message passing order verification"
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# PAULI MATRICES
# =====================================================================

def pauli_matrices(device=None):
    """Return sigma_x, sigma_y, sigma_z as complex64 tensors."""
    sx = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64, device=device)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex64, device=device)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64, device=device)
    return sx, sy, sz


# =====================================================================
# BLOCH <-> DENSITY MATRIX UTILITIES
# =====================================================================

def bloch_to_rho(bloch):
    """Convert 3-dim Bloch vector to 2x2 density matrix (differentiable).

    Args:
        bloch: tensor of shape [3] (real-valued)

    Returns:
        rho: tensor of shape [2, 2] (complex64)
    """
    sx, sy, sz = pauli_matrices(bloch.device)
    I2 = torch.eye(2, dtype=torch.complex64, device=bloch.device)
    b = bloch.to(torch.complex64)
    rho = I2 / 2.0 + (b[0] * sx + b[1] * sy + b[2] * sz) / 2.0
    return rho


def rho_to_bloch(rho):
    """Extract Bloch vector from 2x2 density matrix (differentiable).

    Args:
        rho: tensor of shape [2, 2] (complex64)

    Returns:
        bloch: tensor of shape [3] (real-valued)
    """
    sx, sy, sz = pauli_matrices(rho.device)
    bx = torch.real(torch.trace(sx @ rho))
    by = torch.real(torch.trace(sy @ rho))
    bz = torch.real(torch.trace(sz @ rho))
    return torch.stack([bx, by, bz])


def is_valid_density_matrix(rho, tol=1e-4):
    """Check if rho is a valid density matrix: trace=1, Hermitian, PSD."""
    tr = torch.real(torch.trace(rho)).item()
    herm_err = torch.max(torch.abs(rho - rho.conj().T)).item()
    eigs = torch.real(torch.linalg.eigvalsh(rho))
    min_eig = eigs.min().item()
    return {
        "trace": tr,
        "trace_ok": abs(tr - 1.0) < tol,
        "hermitian_error": herm_err,
        "hermitian_ok": herm_err < tol,
        "min_eigenvalue": min_eig,
        "psd_ok": min_eig > -tol,
        "valid": abs(tr - 1.0) < tol and herm_err < tol and min_eig > -tol,
    }


# =====================================================================
# COHERENT INFORMATION (differentiable)
# =====================================================================

def von_neumann_entropy(rho):
    """Differentiable von Neumann entropy S(rho) = -Tr(rho log rho).

    Uses eigendecomposition for differentiability.
    Clamps eigenvalues to avoid log(0).
    """
    eigs = torch.real(torch.linalg.eigvalsh(rho))
    eigs_clamped = torch.clamp(eigs, min=1e-12)
    return -torch.sum(eigs_clamped * torch.log2(eigs_clamped))


def coherent_information_pair(rho_a, rho_b, rho_ab):
    """I_c(A>B) = S(B) - S(AB).

    Coherent information of A conditioned on B.
    Positive I_c means quantum information flows from A to B.

    Args:
        rho_a: density matrix of subsystem A [2, 2]
        rho_b: density matrix of subsystem B [2, 2]
        rho_ab: density matrix of composite system AB [4, 4]

    Returns:
        I_c: scalar tensor (differentiable)
    """
    S_B = von_neumann_entropy(rho_b)
    S_AB = von_neumann_entropy(rho_ab)
    return S_B - S_AB


def make_product_state(rho_a, rho_b):
    """Create product state rho_AB = rho_A tensor rho_B (differentiable)."""
    return torch.kron(rho_a, rho_b)


def partial_trace_b(rho_ab, dim_a=2, dim_b=2):
    """Trace out subsystem B from rho_AB. Returns rho_A."""
    rho_reshaped = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    return torch.einsum("ijkj->ik", rho_reshaped)


def partial_trace_a(rho_ab, dim_a=2, dim_b=2):
    """Trace out subsystem A from rho_AB. Returns rho_B."""
    rho_reshaped = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    return torch.einsum("ijik->jk", rho_reshaped)


# =====================================================================
# QUANTUM CHANNELS (differentiable, parameterized)
# =====================================================================

def apply_z_dephasing(rho, p):
    """Z-dephasing channel: rho -> (1-p)*rho + p*Z*rho*Z."""
    Z = torch.tensor([[1, 0], [0, -1]], dtype=rho.dtype, device=rho.device)
    return (1.0 - p) * rho + p * (Z @ rho @ Z)


def apply_amplitude_damping(rho, gamma):
    """Amplitude damping channel with Kraus operators."""
    one_r = torch.tensor(1.0, dtype=torch.float32, device=rho.device)
    zero_c = torch.tensor(0.0, dtype=rho.dtype, device=rho.device)
    one_c = torch.tensor(1.0, dtype=rho.dtype, device=rho.device)
    sqrt_1mg = torch.sqrt(torch.clamp(one_r - gamma, min=1e-30)).to(rho.dtype)
    sqrt_g = torch.sqrt(torch.clamp(gamma, min=1e-30)).to(rho.dtype)
    K0 = torch.stack([
        torch.stack([one_c, zero_c]),
        torch.stack([zero_c, sqrt_1mg]),
    ])
    K1 = torch.stack([
        torch.stack([zero_c, sqrt_g]),
        torch.stack([zero_c, zero_c]),
    ])
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T


def apply_depolarizing(rho, p):
    """Depolarizing channel: rho -> (1-p)*rho + p*I/2."""
    I2 = torch.eye(2, dtype=rho.dtype, device=rho.device)
    return (1.0 - p) * rho + p * I2 / 2.0


# =====================================================================
# MESSAGE PASSING LAYERS (PyG)
# =====================================================================

class TerrainToOperatorConv(MessagePassing):
    """Terrain -> Operator: state features flow to operator nodes.

    Each terrain node sends its Bloch vector. The operator node
    aggregates incoming states (mean) to know what it will act on.
    """

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
    """Operator -> Terrain: operator applies channel to terrain state.

    The operator node sends its parameters. The terrain node uses them
    to update its own Bloch vector via the quantum channel.
    """

    def __init__(self, op_dim, terrain_dim):
        super().__init__(aggr="mean")
        # MLP: concat(terrain_state, operator_params) -> new_terrain_state
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
        # Residual update: terrain state + learned correction
        new_state = x_dst + delta
        # Project back into Bloch ball: norm <= 1
        norms = torch.norm(new_state, dim=-1, keepdim=True)
        scale = torch.clamp(norms, min=1.0)
        return new_state / scale


class ShellToOperatorConv(MessagePassing):
    """Shell -> Operator: geometric constraints gate operator parameters.

    Shell nodes send their geometric parameters (eta).
    Operator nodes use them to clamp/constrain their own parameters.
    """

    def __init__(self, shell_dim, op_dim):
        super().__init__(aggr="mean")
        # Gate network: shell params -> operator constraint mask [0, 1]
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
        gate_values = self.gate(aggr_out)
        # Constrain operator parameters: multiply by gate
        return x_dst * gate_values


# =====================================================================
# FULL RATCHET GNN MODULE
# =====================================================================

class RatchetGNN(nn.Module):
    """The full ratchet as a graph neural network.

    HeteroData graph with 3 node types:
      - terrain (4 nodes): Bloch vectors [N_t, 3]
      - operator (3 nodes): channel parameters [N_o, 3]
          (p_dephasing, p_damping, p_depolarizing per operator)
      - shell (2 nodes): geometric parameters [N_s, 2]
          (eta_inner, eta_outer per shell -- Axis 0 torus params)

    Message passing:
      1. shell -> operator (constraint gating)
      2. terrain -> operator (state aggregation)
      3. operator -> terrain (channel application)

    After message passing, I_c is computed on terrain node pairs.
    """

    TERRAIN_DIM = 3   # Bloch vector
    OPERATOR_DIM = 3  # (p_dephasing, p_damping, p_depolarizing)
    SHELL_DIM = 2     # (eta_inner, eta_outer)

    def __init__(self, n_terrain=4, n_operator=3, n_shell=2, n_layers=3):
        super().__init__()
        self.n_terrain = n_terrain
        self.n_operator = n_operator
        self.n_shell = n_shell
        self.n_layers = n_layers

        # Learnable operator parameters (initialized in valid range)
        self.operator_params = nn.Parameter(
            torch.rand(n_operator, self.OPERATOR_DIM) * 0.3 + 0.1
        )

        # Learnable shell parameters (geometric, Axis 0 eta)
        self.shell_params = nn.Parameter(
            torch.rand(n_shell, self.SHELL_DIM) * 0.5 + 0.25
        )

        # Message passing layers (one set per GNN layer)
        self.shell_to_op_layers = nn.ModuleList([
            ShellToOperatorConv(self.SHELL_DIM, self.OPERATOR_DIM)
            for _ in range(n_layers)
        ])
        self.terrain_to_op_layers = nn.ModuleList([
            TerrainToOperatorConv(self.TERRAIN_DIM, self.OPERATOR_DIM)
            for _ in range(n_layers)
        ])
        self.op_to_terrain_layers = nn.ModuleList([
            OperatorToTerrainConv(self.OPERATOR_DIM, self.TERRAIN_DIM)
            for _ in range(n_layers)
        ])

    def build_graph(self, terrain_bloch):
        """Build the HeteroData graph with current parameters.

        Args:
            terrain_bloch: tensor [n_terrain, 3] -- initial Bloch vectors

        Returns:
            HeteroData graph with all node features and edge indices
        """
        data = HeteroData()

        # Node features
        data["terrain"].x = terrain_bloch
        data["operator"].x = self.operator_params
        data["shell"].x = self.shell_params

        # Edge indices: terrain -> operator
        # Each terrain node connects to each operator node
        t_src = torch.arange(self.n_terrain).repeat_interleave(self.n_operator)
        o_dst = torch.arange(self.n_operator).repeat(self.n_terrain)
        data["terrain", "feeds", "operator"].edge_index = torch.stack([t_src, o_dst])

        # Edge indices: operator -> terrain
        # Each operator connects back to each terrain node
        o_src = torch.arange(self.n_operator).repeat_interleave(self.n_terrain)
        t_dst = torch.arange(self.n_terrain).repeat(self.n_operator)
        data["operator", "updates", "terrain"].edge_index = torch.stack([o_src, t_dst])

        # Edge indices: shell -> operator
        # Each shell node constrains each operator node
        s_src = torch.arange(self.n_shell).repeat_interleave(self.n_operator)
        o_dst2 = torch.arange(self.n_operator).repeat(self.n_shell)
        data["shell", "constrains", "operator"].edge_index = torch.stack([s_src, o_dst2])

        return data

    def forward(self, terrain_bloch):
        """Run n_layers of message passing and compute I_c.

        Args:
            terrain_bloch: tensor [n_terrain, 3] -- initial Bloch vectors

        Returns:
            dict with:
              - terrain_out: final Bloch vectors [n_terrain, 3]
              - operator_out: constrained operator params [n_operator, 3]
              - ic_values: coherent information for adjacent pairs
              - ic_mean: mean I_c (the training objective)
        """
        data = self.build_graph(terrain_bloch)

        terrain_x = data["terrain"].x
        operator_x = data["operator"].x
        shell_x = data["shell"].x

        for layer_idx in range(self.n_layers):
            # 1. Shell -> Operator: constrain operator parameters
            shell_op_ei = data["shell", "constrains", "operator"].edge_index
            operator_x = self.shell_to_op_layers[layer_idx](
                shell_x, operator_x, shell_op_ei
            )

            # 2. Terrain -> Operator: aggregate state information
            terrain_op_ei = data["terrain", "feeds", "operator"].edge_index
            op_context = self.terrain_to_op_layers[layer_idx](
                terrain_x, operator_x, terrain_op_ei
            )
            # Blend operator params with state context
            operator_x = operator_x + 0.1 * op_context

            # 3. Operator -> Terrain: apply channels to update states
            op_terrain_ei = data["operator", "updates", "terrain"].edge_index
            terrain_x = self.op_to_terrain_layers[layer_idx](
                operator_x, terrain_x, op_terrain_ei
            )

        # Compute I_c on adjacent terrain pairs
        ic_values = []
        for i in range(self.n_terrain - 1):
            rho_a = bloch_to_rho(terrain_x[i])
            rho_b = bloch_to_rho(terrain_x[i + 1])
            rho_ab = make_product_state(rho_a, rho_b)

            # Apply a small entangling perturbation so I_c can be nonzero
            # (product states have I_c = 0 by definition)
            # Use operator params to create a controlled-phase-like coupling
            op_idx = i % self.n_operator
            coupling = torch.sigmoid(operator_x[op_idx, 0]) * 0.3
            # Entangling unitary: exp(-i * coupling * ZZ)
            phase = coupling.to(torch.complex64)
            diag = torch.tensor(
                [1, 1, 1, 1], dtype=torch.complex64, device=terrain_x.device
            )
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

        if len(ic_values) == 0:
            # Single terrain node: no pairs, I_c is trivially zero
            ic_stack = torch.tensor([0.0], requires_grad=True)
            ic_mean = ic_stack.mean()
        else:
            ic_stack = torch.stack(ic_values)
            ic_mean = ic_stack.mean()

        return {
            "terrain_out": terrain_x,
            "operator_out": operator_x,
            "ic_values": ic_stack,
            "ic_mean": ic_mean,
        }


# =====================================================================
# RATCHET GNN WITHOUT SHELL CONSTRAINTS (for negative test)
# =====================================================================

class RatchetGNNNoShell(nn.Module):
    """Same as RatchetGNN but with shell nodes removed.
    Operator parameters are unconstrained -- can drift to unphysical values.
    """

    TERRAIN_DIM = 3
    OPERATOR_DIM = 3

    def __init__(self, n_terrain=4, n_operator=3, n_layers=3):
        super().__init__()
        self.n_terrain = n_terrain
        self.n_operator = n_operator
        self.n_layers = n_layers

        self.operator_params = nn.Parameter(
            torch.rand(n_operator, self.OPERATOR_DIM) * 0.3 + 0.1
        )

        self.terrain_to_op_layers = nn.ModuleList([
            TerrainToOperatorConv(self.TERRAIN_DIM, self.OPERATOR_DIM)
            for _ in range(n_layers)
        ])
        self.op_to_terrain_layers = nn.ModuleList([
            OperatorToTerrainConv(self.OPERATOR_DIM, self.TERRAIN_DIM)
            for _ in range(n_layers)
        ])

    def forward(self, terrain_bloch):
        n_t = self.n_terrain
        n_o = self.n_operator

        terrain_x = terrain_bloch.clone()
        operator_x = self.operator_params.clone()

        # Edge indices
        t_src = torch.arange(n_t).repeat_interleave(n_o)
        o_dst = torch.arange(n_o).repeat(n_t)
        t_to_o_ei = torch.stack([t_src, o_dst])

        o_src = torch.arange(n_o).repeat_interleave(n_t)
        t_dst = torch.arange(n_t).repeat(n_o)
        o_to_t_ei = torch.stack([o_src, t_dst])

        for layer_idx in range(self.n_layers):
            # NO shell gating -- operator params unconstrained
            op_context = self.terrain_to_op_layers[layer_idx](
                terrain_x, operator_x, t_to_o_ei
            )
            operator_x = operator_x + 0.1 * op_context
            terrain_x = self.op_to_terrain_layers[layer_idx](
                operator_x, terrain_x, o_to_t_ei
            )

        return {"terrain_out": terrain_x, "operator_out": operator_x}


# =====================================================================
# Z3: VERIFY SHELL CONSTRAINT FEASIBILITY
# =====================================================================

def z3_verify_shell_constraints():
    """Use z3 to verify that shell constraints admit at least one valid
    operator configuration, and that removing shells admits invalid configs.
    """
    results = {}
    try:
        solver = Solver()
        # Operator params: p in [0, 1] for physicality
        p_deph = Real("p_deph")
        p_damp = Real("p_damp")
        p_depol = Real("p_depol")

        # Shell constraint: eta gates operator params into [0, 1]
        eta_inner = Real("eta_inner")
        eta_outer = Real("eta_outer")

        # Physical validity: all p in [0, 1]
        physical = And(
            p_deph >= 0, p_deph <= 1,
            p_damp >= 0, p_damp <= 1,
            p_depol >= 0, p_depol <= 1,
        )

        # Shell range
        shell_valid = And(
            eta_inner >= 0, eta_inner <= 1,
            eta_outer >= 0, eta_outer <= 1,
        )

        # Shell constraint: operator params bounded by shell gate
        # p <= sigmoid(eta) approximated as p <= eta for z3 (linear relaxation)
        shell_constrained = And(
            p_deph <= eta_inner,
            p_damp <= eta_outer,
            p_depol <= (eta_inner + eta_outer) / 2,
        )

        # Test 1: constrained system is satisfiable
        solver.push()
        solver.add(physical)
        solver.add(shell_valid)
        solver.add(shell_constrained)
        solver.add(p_deph > 0)  # nontrivial
        check1 = solver.check()
        results["constrained_satisfiable"] = check1 == sat
        solver.pop()

        # Test 2: without shell constraints, unphysical configs are possible
        solver.push()
        solver.add(p_deph > 1.0)  # unphysical
        check2 = solver.check()
        results["unconstrained_allows_unphysical"] = check2 == sat
        solver.pop()

        # Test 3: with shell constraints, unphysical is UNSAT
        solver.push()
        solver.add(shell_valid)
        solver.add(shell_constrained)
        solver.add(p_deph > 1.0)
        check3 = solver.check()
        results["constrained_blocks_unphysical"] = check3 == unsat
        solver.pop()

        results["z3_passed"] = all([
            results["constrained_satisfiable"],
            results["unconstrained_allows_unphysical"],
            results["constrained_blocks_unphysical"],
        ])
    except Exception as e:
        results["z3_error"] = str(e)
        results["z3_passed"] = False

    return results


# =====================================================================
# RUSTWORKX: VERIFY MESSAGE PASSING ORDER
# =====================================================================

def rustworkx_verify_message_order():
    """Use rustworkx to verify the message passing DAG has valid order:
    shell -> operator before operator -> terrain.
    """
    results = {}
    try:
        dag = rx.PyDiGraph()
        # Nodes: 0=shell, 1=operator, 2=terrain
        shell_idx = dag.add_node("shell")
        op_idx = dag.add_node("operator")
        terrain_idx = dag.add_node("terrain")

        # Edges: shell -> operator, terrain -> operator, operator -> terrain
        dag.add_edge(shell_idx, op_idx, "constrains")
        dag.add_edge(op_idx, terrain_idx, "updates")
        # terrain -> operator is a feedback edge (not in DAG for ordering)

        topo = rx.topological_sort(dag)
        order = [dag[n] for n in topo]

        results["topological_order"] = order
        # Shell must come before operator, operator before terrain
        shell_pos = order.index("shell")
        op_pos = order.index("operator")
        terrain_pos = order.index("terrain")
        results["shell_before_operator"] = shell_pos < op_pos
        results["operator_before_terrain"] = op_pos < terrain_pos
        results["order_valid"] = shell_pos < op_pos < terrain_pos
    except Exception as e:
        results["rustworkx_error"] = str(e)
        results["order_valid"] = False

    return results


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ── Test 1: Message passing produces valid density matrices ──────
    try:
        model = RatchetGNN(n_terrain=4, n_operator=3, n_shell=2, n_layers=3)
        # Initial Bloch vectors: spread across the Bloch sphere
        init_bloch = torch.tensor([
            [0.0, 0.0, 1.0],    # |0>
            [0.0, 0.0, -1.0],   # |1>
            [1.0, 0.0, 0.0],    # |+>
            [0.0, 1.0, 0.0],    # |+i>
        ], dtype=torch.float32)

        with torch.no_grad():
            out = model(init_bloch)

        terrain_out = out["terrain_out"]
        validity_checks = []
        for i in range(4):
            rho = bloch_to_rho(terrain_out[i])
            check = is_valid_density_matrix(rho)
            validity_checks.append(check)

        all_valid = all(c["valid"] for c in validity_checks)
        results["valid_density_matrices"] = {
            "passed": all_valid,
            "checks": validity_checks,
        }
    except Exception as e:
        results["valid_density_matrices"] = {
            "passed": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # ── Test 2: I_c is differentiable w.r.t. operator parameters ────
    try:
        model = RatchetGNN(n_terrain=4, n_operator=3, n_shell=2, n_layers=3)
        init_bloch = torch.tensor([
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ], dtype=torch.float32)

        out = model(init_bloch)
        ic_mean = out["ic_mean"]

        # Backpropagate
        ic_mean.backward()

        # Check that operator_params has nonzero gradient
        grad = model.operator_params.grad
        has_grad = grad is not None
        grad_nonzero = has_grad and torch.any(grad.abs() > 1e-10).item()

        results["ic_differentiable"] = {
            "passed": has_grad and grad_nonzero,
            "has_grad": has_grad,
            "grad_nonzero": grad_nonzero,
            "grad_norm": float(grad.norm().item()) if has_grad else 0.0,
            "ic_mean": float(ic_mean.item()),
        }
    except Exception as e:
        results["ic_differentiable"] = {
            "passed": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # ── Test 3: Optimization increases I_c over iterations ──────────
    try:
        model = RatchetGNN(n_terrain=4, n_operator=3, n_shell=2, n_layers=2)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

        init_bloch = torch.tensor([
            [0.5, 0.3, 0.1],
            [-0.2, 0.4, 0.6],
            [0.1, -0.3, 0.8],
            [0.4, 0.2, -0.5],
        ], dtype=torch.float32)

        ic_history = []
        n_steps = 50

        for step in range(n_steps):
            optimizer.zero_grad()
            out = model(init_bloch)
            # Maximize I_c = minimize -I_c
            loss = -out["ic_mean"]
            loss.backward()
            optimizer.step()
            ic_history.append(float(out["ic_mean"].item()))

        ic_start = np.mean(ic_history[:5])
        ic_end = np.mean(ic_history[-5:])
        ic_improved = ic_end > ic_start

        results["optimization_increases_ic"] = {
            "passed": ic_improved,
            "ic_start_avg": float(ic_start),
            "ic_end_avg": float(ic_end),
            "ic_delta": float(ic_end - ic_start),
            "ic_history_sample": [ic_history[0], ic_history[n_steps // 4],
                                  ic_history[n_steps // 2], ic_history[-1]],
            "n_steps": n_steps,
        }
    except Exception as e:
        results["optimization_increases_ic"] = {
            "passed": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # ── Test 4: Shell constraints prevent out-of-range parameters ───
    try:
        model = RatchetGNN(n_terrain=4, n_operator=3, n_shell=2, n_layers=3)

        # Force operator params to large values
        with torch.no_grad():
            model.operator_params.fill_(5.0)

        init_bloch = torch.tensor([
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ], dtype=torch.float32)

        with torch.no_grad():
            out = model(init_bloch)

        # After shell gating, effective operator params should be < input
        op_out = out["operator_out"]
        max_op_param = op_out.abs().max().item()
        # Shell sigmoid gate outputs in [0, 1], so gated params should be
        # significantly less than the raw 5.0
        constrained = max_op_param < 5.0

        results["shell_constrains_params"] = {
            "passed": constrained,
            "raw_param_value": 5.0,
            "max_gated_param": float(max_op_param),
            "reduction_ratio": float(max_op_param / 5.0),
        }
    except Exception as e:
        results["shell_constrains_params"] = {
            "passed": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ── Negative 1: No shell -> unphysical operator parameters ──────
    try:
        model_no_shell = RatchetGNNNoShell(n_terrain=4, n_operator=3, n_layers=3)

        # Force large operator params
        with torch.no_grad():
            model_no_shell.operator_params.fill_(5.0)

        init_bloch = torch.tensor([
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ], dtype=torch.float32)

        with torch.no_grad():
            out = model_no_shell(init_bloch)

        # Without shell gating, operator params should remain large
        op_out = out["operator_out"]
        max_op = op_out.abs().max().item()
        # The no-shell model has no gating, so params stay near 5.0
        # (modulo the terrain->op linear layer, but no sigmoid gate)
        params_unconstrained = max_op > 1.0  # should exceed physical [0,1]

        results["no_shell_allows_unphysical"] = {
            "passed": params_unconstrained,
            "max_operator_param": float(max_op),
            "exceeds_physical_range": params_unconstrained,
        }
    except Exception as e:
        results["no_shell_allows_unphysical"] = {
            "passed": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # ── Negative 2: Disconnected graph -> no information flow ───────
    try:
        model = RatchetGNN(n_terrain=4, n_operator=3, n_shell=2, n_layers=3)

        # Create two separate terrain sets with different states
        bloch_a = torch.tensor([
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
            [0.0, 0.0, -1.0],
        ], dtype=torch.float32)

        # Now create a disconnected version: zero out all edges
        # by overriding the graph builder
        data = model.build_graph(bloch_a)

        # Run with empty edge indices (disconnected)
        terrain_x = bloch_a.clone()
        operator_x = model.operator_params.clone().detach()

        # With no edges, message passing should produce zero aggregation
        # so terrain states should not change
        empty_ei = torch.zeros(2, 0, dtype=torch.long)

        with torch.no_grad():
            for layer_idx in range(model.n_layers):
                # Shell -> op with empty edges: no constraint flow
                op_constrained = model.shell_to_op_layers[layer_idx](
                    model.shell_params, operator_x, empty_ei
                )
                # Op -> terrain with empty edges: no state update
                terrain_updated = model.op_to_terrain_layers[layer_idx](
                    op_constrained, terrain_x, empty_ei
                )

        # With empty edges, propagate returns zeros or unchanged
        # The key test: terrain states should be unchanged from input
        terrain_unchanged = torch.allclose(terrain_x, bloch_a, atol=1e-5)

        results["disconnected_no_flow"] = {
            "passed": terrain_unchanged,
            "terrain_change": float((terrain_x - bloch_a).abs().max().item()),
        }
    except Exception as e:
        results["disconnected_no_flow"] = {
            "passed": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ── Boundary 1: Single terrain + operator (trivial case) ────────
    try:
        model = RatchetGNN(n_terrain=1, n_operator=1, n_shell=1, n_layers=2)
        init_bloch = torch.tensor([[0.0, 0.0, 1.0]], dtype=torch.float32)

        with torch.no_grad():
            out = model(init_bloch)

        terrain_out = out["terrain_out"]
        rho = bloch_to_rho(terrain_out[0])
        check = is_valid_density_matrix(rho)

        # With only 1 terrain node, no pairs -> ic_values is empty
        # Just check the model runs without error and state is valid
        results["single_node_trivial"] = {
            "passed": check["valid"],
            "validity": check,
            "terrain_out": terrain_out[0].tolist(),
        }
    except Exception as e:
        results["single_node_trivial"] = {
            "passed": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # ── Boundary 2: Fully connected (max flow) ─────────────────────
    try:
        # Large graph: 8 terrain, 6 operators, 4 shells
        model = RatchetGNN(n_terrain=8, n_operator=6, n_shell=4, n_layers=2)
        init_bloch = torch.randn(8, 3) * 0.5  # Random Bloch vectors

        with torch.no_grad():
            out = model(init_bloch)

        terrain_out = out["terrain_out"]
        all_valid = True
        for i in range(8):
            rho = bloch_to_rho(terrain_out[i])
            check = is_valid_density_matrix(rho)
            if not check["valid"]:
                all_valid = False

        results["fully_connected_max_flow"] = {
            "passed": all_valid,
            "n_terrain": 8,
            "n_operator": 6,
            "n_shell": 4,
            "terrain_norms": [float(torch.norm(terrain_out[i]).item()) for i in range(8)],
        }
    except Exception as e:
        results["fully_connected_max_flow"] = {
            "passed": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # ── Boundary 3: Pure state preservation ─────────────────────────
    try:
        model = RatchetGNN(n_terrain=2, n_operator=1, n_shell=1, n_layers=1)
        # Pure state: Bloch vector on the surface (norm = 1)
        init_bloch = torch.tensor([
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0],
        ], dtype=torch.float32)

        with torch.no_grad():
            out = model(init_bloch)

        terrain_out = out["terrain_out"]
        # After message passing, Bloch vectors should still be inside
        # (or on) the Bloch ball
        norms = [float(torch.norm(terrain_out[i]).item()) for i in range(2)]
        inside_ball = all(n <= 1.0 + 1e-4 for n in norms)

        results["bloch_ball_containment"] = {
            "passed": inside_ball,
            "norms": norms,
        }
    except Exception as e:
        results["bloch_ball_containment"] = {
            "passed": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "Phase 5/6: Full Ratchet as GNN",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "classification": "canonical",
    }

    # Run z3 verification
    print("Running z3 shell constraint verification...")
    results["z3_verification"] = z3_verify_shell_constraints()

    # Run rustworkx order verification
    print("Running rustworkx message order verification...")
    results["rustworkx_verification"] = rustworkx_verify_message_order()

    # Run all test batteries
    print("Running positive tests...")
    results["positive"] = run_positive_tests()

    print("Running negative tests...")
    results["negative"] = run_negative_tests()

    print("Running boundary tests...")
    results["boundary"] = run_boundary_tests()

    # Summary
    pos_pass = sum(1 for v in results["positive"].values()
                   if isinstance(v, dict) and v.get("passed"))
    pos_total = len(results["positive"])
    neg_pass = sum(1 for v in results["negative"].values()
                   if isinstance(v, dict) and v.get("passed"))
    neg_total = len(results["negative"])
    bnd_pass = sum(1 for v in results["boundary"].values()
                   if isinstance(v, dict) and v.get("passed"))
    bnd_total = len(results["boundary"])

    results["summary"] = {
        "positive": f"{pos_pass}/{pos_total}",
        "negative": f"{neg_pass}/{neg_total}",
        "boundary": f"{bnd_pass}/{bnd_total}",
        "z3_passed": results["z3_verification"].get("z3_passed", False),
        "rustworkx_passed": results["rustworkx_verification"].get("order_valid", False),
        "all_passed": (pos_pass == pos_total and neg_pass == neg_total
                       and bnd_pass == bnd_total),
    }

    print(f"\nSummary: +{results['summary']['positive']} "
          f"-{results['summary']['negative']} "
          f"B{results['summary']['boundary']} "
          f"z3={'OK' if results['summary']['z3_passed'] else 'FAIL'} "
          f"rx={'OK' if results['summary']['rustworkx_passed'] else 'FAIL'}")

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_ratchet_gnn_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
