"""Engine v6 — proper multi-qubit (3-8 qubits) with richer features and PROPER multi-qubit inputs.

Fixes v5's bottlenecks:
- Inputs: full N-qubit pure/mixed states (not lifted-from-2d)
- Features: per-qubit Bloch + bipartite entropies + mutual info — uses the full Hilbert space
- Configurable N_QUBITS for scaling study (3, 4, 6, 8)

Tests scaling: does increasing N_QUBITS help or hurt at this param budget?
"""
from __future__ import annotations
import math
import torch, torch.nn as nn
from itertools import combinations

DTYPE = torch.complex64
DTYPE_F = torch.float32


def make_paulis(device='cpu'):
    I = torch.eye(2, dtype=DTYPE, device=device)
    X = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE, device=device)
    Y = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE, device=device)
    Z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE, device=device)
    return dict(I=I, X=X, Y=Y, Z=Z)


def kron_chain(*ops):
    out = ops[0]
    for op in ops[1:]:
        out = torch.kron(out, op)
    return out


def site_op(local_op, n_qubits, site_idx):
    paulis = make_paulis(device=local_op.device)
    factors = [paulis['I']] * n_qubits
    factors[site_idx] = local_op
    return kron_chain(*factors)


def two_site_zz(n_qubits, i, j):
    paulis = make_paulis()
    factors = [paulis['I']] * n_qubits
    factors[i] = paulis['Z']; factors[j] = paulis['Z']
    return kron_chain(*factors)


def normalize_density(rho):
    rho = (rho + rho.conj().transpose(-1, -2)) / 2
    tr = torch.diagonal(rho, dim1=-2, dim2=-1).sum(-1).real
    return rho / tr.unsqueeze(-1).unsqueeze(-1).to(rho.dtype)


def lindblad_diss(rho, L):
    LdL = L.conj().T @ L
    return L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL)


def comm_minus_i(rho, H):
    return -1j * (H @ rho - rho @ H)


def vn_entropy(rho):
    rho_h = (rho + rho.conj().transpose(-1, -2)) / 2
    eigvals = torch.linalg.eigvalsh(rho_h)
    eigvals = torch.clamp(eigvals.real, min=1e-7)
    eigvals = eigvals / eigvals.sum(-1, keepdim=True)
    return -(eigvals * torch.log(eigvals)).sum(-1)


def purity_torch(rho):
    return torch.diagonal(rho @ rho, dim1=-2, dim2=-1).sum(-1).real


def partial_trace(rho, n_qubits, keep_qubits):
    """Partial trace keeping `keep_qubits` (list of indices), tracing out the rest."""
    if rho.dim() == 2:
        rho = rho.unsqueeze(0)
    batch = rho.shape[0]
    keep_qubits = sorted(keep_qubits)
    trace_qubits = [i for i in range(n_qubits) if i not in keep_qubits]

    # Reshape rho to [batch, 2, 2, ..., 2, 2, 2, ..., 2] with 2*n_qubits dims
    shape_2n = [batch] + [2] * (2 * n_qubits)
    rho_2n = rho.reshape(shape_2n)
    # Trace out one qubit at a time (always trace from the end, adjust offsets)
    # Indices: row dim r_i at position 1+i, col dim c_i at position 1+n_qubits+i
    # For each qubit to trace, contract dims at row position and col position
    # After tracing one qubit, all subsequent indices shift down
    for q in sorted(trace_qubits, reverse=True):
        # Number of remaining qubits BEFORE tracing
        n_now = (rho_2n.dim() - 1) // 2
        row_pos = 1 + q
        col_pos = 1 + n_now + q
        rho_2n = torch.diagonal(rho_2n, dim1=row_pos, dim2=col_pos).sum(-1)
    # Reshape final back to 2D
    d = 2 ** len(keep_qubits)
    return rho_2n.reshape(batch, d, d)


def per_qubit_blochs(rho, n_qubits, P):
    """Return [batch, n_qubits, 3] Bloch vectors for each qubit's reduced density."""
    blochs = []
    for q in range(n_qubits):
        rho_q = partial_trace(rho, n_qubits, [q])
        bx = torch.diagonal(P['X'] @ rho_q, dim1=-2, dim2=-1).sum(-1).real.unsqueeze(-1)
        by = torch.diagonal(P['Y'] @ rho_q, dim1=-2, dim2=-1).sum(-1).real.unsqueeze(-1)
        bz = torch.diagonal(P['Z'] @ rho_q, dim1=-2, dim2=-1).sum(-1).real.unsqueeze(-1)
        blochs.append(torch.cat([bx, by, bz], dim=-1))  # [batch, 3]
    return torch.stack(blochs, dim=1)  # [batch, n_qubits, 3]


def bipartite_mutual_info(rho, n_qubits):
    """I(A:B) = S(A) + S(B) - S(AB) for a single half-chain split."""
    half = n_qubits // 2
    rho_A = partial_trace(rho, n_qubits, list(range(half)))
    rho_B = partial_trace(rho, n_qubits, list(range(half, n_qubits)))
    return vn_entropy(rho_A) + vn_entropy(rho_B) - vn_entropy(rho)


class TrainableEngineV6(nn.Module):
    """Multi-qubit engine with rich per-substage features."""
    def __init__(self, engine_type=1, n_qubits=4, dt=0.06, n_steps_per_substage=2, nn_coupling=0.3):
        super().__init__()
        assert engine_type in (1, 2)
        assert n_qubits >= 3, "Per user: minimum 3 qubits for nontrivial multipartite cuts"
        self.engine_type = engine_type
        self.n_qubits = n_qubits
        self.D = 2 ** n_qubits
        self.dt = dt
        self.n_steps = n_steps_per_substage
        self.sign = +1.0 if engine_type == 1 else -1.0

        # Per-terrain learnable coefficients
        self.terrain_coefs = nn.Parameter(torch.tensor([
            [0.5, 0.5, 0.0, 0.0],
            [0.3, 1.0, 0.0, 0.0],
            [0.6, 0.4, 0.0, 0.0],
            [0.0, 0.4, 0.4, 0.4],
        ], dtype=DTYPE_F))

        self.funnel_paulis = nn.Parameter(torch.tensor([0.4, 0.3 * self.sign, 0.5], dtype=DTYPE_F))
        self.vortex_paulis = nn.Parameter(torch.tensor([0.5, 0.5 * self.sign], dtype=DTYPE_F))
        self.h0_n = nn.Parameter(torch.tensor([0.77, 0.13, 0.6], dtype=DTYPE_F))
        self.k_strength = nn.Parameter(torch.tensor(0.5, dtype=DTYPE_F))
        # Per-terrain × per-operator × ±sign angles
        init_angles = torch.zeros(4, 4, 2)
        natives = {0: [0, 2], 1: [1, 3], 2: [1, 3], 3: [0, 2]}
        for t, ops in natives.items():
            for op in range(4):
                init = 0.18 if op in ops else 0.10
                init_angles[t, op, :] = init
        self.op_angles = nn.Parameter(init_angles)
        self.nn_coupling = nn.Parameter(torch.tensor(nn_coupling, dtype=DTYPE_F))

        # Pauli buffers
        for k, v in make_paulis().items():
            self.register_buffer(f"P_{k}", v)
        # Pre-compute multi-qubit operators per site
        for site in range(n_qubits):
            self.register_buffer(f"site_X_{site}", site_op(self.P_X, n_qubits, site))
            self.register_buffer(f"site_Y_{site}", site_op(self.P_Y, n_qubits, site))
            self.register_buffer(f"site_Z_{site}", site_op(self.P_Z, n_qubits, site))
            self.register_buffer(f"site_SP_{site}", 0.5 * (site_op(self.P_X, n_qubits, site) + 1j * site_op(self.P_Y, n_qubits, site)))
            self.register_buffer(f"site_SM_{site}", 0.5 * (site_op(self.P_X, n_qubits, site) - 1j * site_op(self.P_Y, n_qubits, site)))
        # Strata projectors on first qubit
        P_0 = torch.kron(0.5 * (self.P_I + self.P_Z), torch.eye(2 ** (n_qubits - 1), dtype=DTYPE))
        P_1 = torch.kron(0.5 * (self.P_I - self.P_Z), torch.eye(2 ** (n_qubits - 1), dtype=DTYPE))
        P_p = torch.kron(0.5 * (self.P_I + self.P_X), torch.eye(2 ** (n_qubits - 1), dtype=DTYPE))
        P_m = torch.kron(0.5 * (self.P_I - self.P_X), torch.eye(2 ** (n_qubits - 1), dtype=DTYPE))
        self.register_buffer("P_R_UP", P_0); self.register_buffer("P_R_DOWN", P_1)
        self.register_buffer("P_R_PLUS", P_p); self.register_buffer("P_R_MINUS", P_m)
        # NN ZZ Hamiltonian
        H_nn = torch.zeros((self.D, self.D), dtype=DTYPE)
        for i in range(n_qubits - 1):
            H_nn = H_nn + two_site_zz(n_qubits, i, i + 1)
        self.register_buffer("H_nn_zz", H_nn)

    def hamiltonian_H(self):
        H_sum = torch.zeros((self.D, self.D), dtype=DTYPE, device=self.h0_n.device)
        nx, ny, nz = self.h0_n[0].to(DTYPE), self.h0_n[1].to(DTYPE), self.h0_n[2].to(DTYPE)
        for site in range(self.n_qubits):
            H_sum = H_sum + nx * getattr(self, f"site_X_{site}") + ny * getattr(self, f"site_Y_{site}") + nz * getattr(self, f"site_Z_{site}")
        H_sum = H_sum + self.nn_coupling.to(DTYPE) * self.H_nn_zz
        return self.sign * H_sum

    def hamiltonian_K(self):
        K_sum = torch.zeros((self.D, self.D), dtype=DTYPE, device=self.k_strength.device)
        for site in range(self.n_qubits):
            K_sum = K_sum + (getattr(self, f"site_Z_{site}") if self.engine_type == 1 else getattr(self, f"site_X_{site}"))
        return self.k_strength.to(DTYPE) * K_sum

    def funnel_L(self):
        ax, ay, az = self.funnel_paulis[0].to(DTYPE), self.funnel_paulis[1].to(DTYPE), self.funnel_paulis[2].to(DTYPE)
        return ax * self.site_X_0 + ay * self.site_Y_0 + az * self.site_Z_0

    def vortex_M(self):
        ax, ay = self.vortex_paulis[0].to(DTYPE), self.vortex_paulis[1].to(DTYPE)
        return ax * self.site_X_0 + ay * self.site_Y_0

    def terrain_law(self, rho, terrain_idx):
        gamma, eps, k1, k2 = self.terrain_coefs[terrain_idx]
        H = self.hamiltonian_H()
        if terrain_idx == 0:
            return gamma.to(DTYPE) * lindblad_diss(rho, self.funnel_L()) + eps.to(DTYPE) * comm_minus_i(rho, H)
        elif terrain_idx == 1:
            return eps.to(DTYPE) * comm_minus_i(rho, H) + gamma.to(DTYPE) * lindblad_diss(rho, self.vortex_M())
        elif terrain_idx == 2:
            L = self.site_SM_0 if self.engine_type == 1 else self.site_SP_0
            return gamma.to(DTYPE) * lindblad_diss(rho, L) + eps.to(DTYPE) * comm_minus_i(rho, H)
        else:
            K = self.hamiltonian_K()
            projs = [self.P_R_UP, self.P_R_DOWN] if self.engine_type == 1 else [self.P_R_PLUS, self.P_R_MINUS]
            kappas = [k1.to(DTYPE), k2.to(DTYPE)]
            out = eps.to(DTYPE) * comm_minus_i(rho, K)
            for P, k in zip(projs, kappas):
                out = out + k * (P @ rho @ P - 0.5 * (P @ rho + rho @ P))
            return out

    def operator_kick(self, rho, terrain_idx, op_idx, sign):
        op = [self.site_Z_0, self.site_X_0, self.site_X_0, self.site_Y_0][op_idx]
        sign_idx = 0 if sign > 0 else 1
        angle = self.op_angles[terrain_idx, op_idx, sign_idx] * sign
        U = torch.linalg.matrix_exp(-1j * angle.to(DTYPE) * op)
        return U @ rho @ U.conj().transpose(-1, -2)

    def stage_substages(self, terrain_idx):
        return [(0, +1), (1, +1), (2, -1), (3, -1)]

    def stage_sequence(self):
        if self.engine_type == 1:
            return [0, 1, 2, 3, 0, 3, 2, 1]
        else:
            return [0, 3, 2, 1, 0, 1, 2, 3]

    def run_substage(self, rho, terrain_idx, op_idx, sign):
        rho = self.operator_kick(rho, terrain_idx, op_idx, sign)
        for _ in range(self.n_steps):
            drho = self.terrain_law(rho, terrain_idx)
            rho = rho + (self.dt / self.n_steps) * drho
        return normalize_density(rho)

    def trajectory_features(self, rho_init):
        """Rich features per substage:
        - Full state entropy + purity (2)
        - Per-qubit reduced Bloch (n_qubits × 3)
        - Bipartite mutual info I(L:R) for half-chain split (1)
        Total per substage: 2 + 3*n_qubits + 1
        Total over 32 substages: 32 * (3 + 3*n_qubits)
        """
        if rho_init.dim() == 2:
            rho_init = rho_init.unsqueeze(0)
        rho = normalize_density(rho_init.to(DTYPE))
        feats_list = []
        P = make_paulis()
        for terrain_idx in self.stage_sequence():
            for op_idx, sign in self.stage_substages(terrain_idx):
                rho = self.run_substage(rho, terrain_idx, op_idx, sign)
                ent = vn_entropy(rho).unsqueeze(-1)
                pur = purity_torch(rho).unsqueeze(-1)
                blochs = per_qubit_blochs(rho, self.n_qubits, P).reshape(rho.shape[0], -1)  # [batch, 3*n_qubits]
                mi = bipartite_mutual_info(rho, self.n_qubits).unsqueeze(-1)
                feats_list.append(torch.cat([ent, pur, blochs, mi], dim=-1))
        return torch.cat(feats_list, dim=-1)

    def forward(self, rho_init):
        return self.trajectory_features(rho_init)


class TrainablePairedEngineV6(nn.Module):
    def __init__(self, n_classes, n_qubits=4, hidden_dim=128, dt=0.06, n_steps=2):
        super().__init__()
        self.engine_L = TrainableEngineV6(engine_type=1, n_qubits=n_qubits, dt=dt, n_steps_per_substage=n_steps)
        self.engine_R = TrainableEngineV6(engine_type=2, n_qubits=n_qubits, dt=dt, n_steps_per_substage=n_steps)
        feat_dim_per_engine = 32 * (3 + 3 * n_qubits)  # per-substage features × 32 substages
        self.feat_dim = feat_dim_per_engine * 2
        self.readout = nn.Sequential(
            nn.Linear(self.feat_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, n_classes),
        )

    def forward(self, rho_L, rho_R=None):
        if rho_R is None: rho_R = rho_L.clone()
        feats_L = self.engine_L(rho_L)
        feats_R = self.engine_R(rho_R)
        return self.readout(torch.cat([feats_L, feats_R], dim=-1))


def random_pure_nqubit_state(n_qubits, rng=None):
    """Sample a random pure state in 2^n-dim Hilbert space (Haar measure)."""
    generator = rng if isinstance(rng, torch.Generator) else None
    d = 2 ** n_qubits
    psi = torch.randn(d, generator=generator, dtype=DTYPE_F) + 1j * torch.randn(d, generator=generator, dtype=DTYPE_F)
    psi = psi.to(DTYPE)
    psi = psi / torch.linalg.vector_norm(psi)
    return torch.outer(psi, psi.conj())


def random_product_state(n_qubits, rng=None):
    """Sample a random product state |ψ_1⟩⊗|ψ_2⟩⊗...⊗|ψ_n⟩."""
    generator = rng if isinstance(rng, torch.Generator) else None
    factors = []
    for _ in range(n_qubits):
        psi = torch.randn(2, generator=generator, dtype=DTYPE_F) + 1j * torch.randn(2, generator=generator, dtype=DTYPE_F)
        psi = psi.to(DTYPE)
        psi = psi / torch.linalg.vector_norm(psi)
        factors.append(torch.outer(psi, psi.conj()))
    out = factors[0]
    for f in factors[1:]:
        out = torch.kron(out, f)
    return out


def ghz_state(n_qubits):
    """|GHZ_n⟩ = (|0...0⟩ + |1...1⟩)/√2"""
    d = 2 ** n_qubits
    psi = torch.zeros(d, dtype=DTYPE)
    psi[0] = psi[-1] = 1 / math.sqrt(2)
    return torch.outer(psi, psi.conj())


def w_state(n_qubits):
    """|W_n⟩ = sum_i |0...010...0⟩/√n  (single excitation symmetric)"""
    d = 2 ** n_qubits
    psi = torch.zeros(d, dtype=DTYPE)
    for i in range(n_qubits):
        psi[1 << (n_qubits - 1 - i)] = 1.0 / math.sqrt(n_qubits)
    return torch.outer(psi, psi.conj())


if __name__ == "__main__":
    import time
    for nq in [3, 4, 6]:
        eng = TrainablePairedEngineV6(n_classes=8, n_qubits=nq)
        n_params = sum(p.numel() for p in eng.parameters() if p.requires_grad)
        rho_init = random_pure_nqubit_state(nq).unsqueeze(0)
        t0 = time.time()
        logits = eng(rho_init)
        forward_t = time.time() - t0
        loss = logits.sum(); loss.backward()
        print(f"n_qubits={nq}  D={2**nq}  feat_dim={eng.feat_dim}  params={n_params}  forward={forward_t:.2f}s  backprop ✓")
