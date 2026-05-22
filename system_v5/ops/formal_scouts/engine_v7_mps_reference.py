"""Engine v7 — MPS-based engine for 12-32 qubit scaling.

Custom PyTorch MPS implementation (not quimb — bypasses its gate API issues at our version).
Each MPS site has shape [d=2, chi_L, chi_R].
2-site gates applied via SVD with bond dim cap.

Architecture:
- N_QUBITS configurable (12, 16, 24, 32+)
- Same 8 terrain laws + 5 generators conceptually, but applied as LOCAL operations
- Operators: single-site Pauli rotations (Ti/Te/Fi/Fe per terrain)
- Lindblad evolution: small-step Trotterization (treats Lindblad terms as local 2-site gates)
- Strata projectors: per-site Z eigenstate projectors (local)
- Bipartite features: half-chain entropy via Schmidt decomposition (cheap)

Designed to be NON-trainable initially (functional reservoir test only).
"""
from __future__ import annotations
import torch, math
from typing import Optional

DTYPE = torch.complex64
DTYPE_F = torch.float32

# Pauli matrices
def paulis():
    I = torch.eye(2, dtype=DTYPE)
    X = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    Y = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    Z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    return I, X, Y, Z

I2, SX, SY, SZ = paulis()
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)


class MPS:
    """Simple MPS: list of [d=2, chi_L, chi_R] tensors. Open boundary."""
    def __init__(self, tensors: list[torch.Tensor]):
        self.tensors = tensors
        self.N = len(tensors)

    @classmethod
    def random(cls, N: int, chi: int = 4, seed: int = 0):
        """Random pure-state MPS with bond dimension chi."""
        g = torch.Generator().manual_seed(seed)
        tensors = []
        for i in range(N):
            cL = 1 if i == 0 else chi
            cR = 1 if i == N - 1 else chi
            t = torch.randn(2, cL, cR, generator=g, dtype=torch.float32) + 1j * torch.randn(2, cL, cR, generator=g, dtype=torch.float32)
            tensors.append(t.to(DTYPE))
        mps = cls(tensors)
        mps.normalize_()
        return mps

    @classmethod
    def product(cls, vecs: list[torch.Tensor]):
        """Product state from list of N single-qubit complex vectors."""
        tensors = [v.reshape(2, 1, 1).to(DTYPE) for v in vecs]
        return cls(tensors)

    def copy(self):
        return MPS([t.clone() for t in self.tensors])

    def normalize_(self):
        """Normalize the MPS by dividing the leftmost tensor by total norm."""
        # Compute norm via right-to-left contraction
        env = torch.eye(self.tensors[-1].shape[-1], dtype=DTYPE)
        for i in range(self.N - 1, -1, -1):
            t = self.tensors[i]
            env = torch.einsum('dij,dkl,jl->ik', t, t.conj(), env)
        norm_sq = env.real.item()
        if norm_sq < 1e-30: return
        self.tensors[0] = self.tensors[0] / math.sqrt(norm_sq)

    def apply_single(self, op: torch.Tensor, site: int):
        """Apply single-site operator: t -> einsum('ab,bij->aij', op, t)"""
        t = self.tensors[site]
        self.tensors[site] = torch.einsum('ab,bij->aij', op.to(DTYPE), t)

    def apply_two(self, op: torch.Tensor, site: int, max_bond: int = 8):
        """Apply 2-site gate (4x4 op reshaped to 2x2x2x2) on (site, site+1) with SVD truncation."""
        if op.dim() == 2:
            op = op.reshape(2, 2, 2, 2)
        op = op.to(DTYPE)
        tL, tR = self.tensors[site], self.tensors[site + 1]
        # Contract: tL[d1, cL, c_mid] tR[d2, c_mid, cR] -> theta[d1, d2, cL, cR]
        theta = torch.einsum('aci,bdj,ij->abcd', tL, tR.permute(0, 2, 1), torch.eye(tL.shape[2], dtype=DTYPE))
        # Wait — better:
        # tL: [d1, cL, c_mid], tR: [d2, c_mid, cR]
        # theta = tL @ tR contracted on c_mid
        theta = torch.einsum('aci,bid->abcd', tL, tR)  # [d1, d2, cL, cR]
        # Apply gate: theta'[d1', d2', cL, cR] = sum_{d1,d2} op[d1', d2', d1, d2] theta[d1, d2, cL, cR]
        theta = torch.einsum('eDab,abcd->eDcd', op, theta).contiguous()
        # SVD: reshape to (d1*cL, d2*cR), SVD, truncate
        d1, d2, cL, cR = theta.shape
        mat = theta.permute(0, 2, 1, 3).reshape(d1 * cL, d2 * cR)
        U, S, Vh = torch.linalg.svd(mat, full_matrices=False)
        # Truncate to max_bond
        chi_new = min(max_bond, S.numel())
        U = U[:, :chi_new]; S = S[:chi_new]; Vh = Vh[:chi_new, :]
        # Re-form tL_new[d1, cL, chi_new] and tR_new[d2, chi_new, cR]
        new_tL = (U * S.unsqueeze(0)).reshape(d1, cL, chi_new)
        new_tR = Vh.reshape(chi_new, d2, cR).permute(1, 0, 2)
        self.tensors[site] = new_tL
        self.tensors[site + 1] = new_tR

    def schmidt_entropy(self, cut: int):
        """Schmidt entropy at cut between sites cut-1 and cut."""
        if cut == 0 or cut >= self.N: return torch.tensor(0.0)
        # Bring to canonical form at cut: just compute via SVD of contracted left half
        # Cheaper: use right-canonical from right + take SVD of leftmost remaining
        # Simple: compute reduced density of left half via contraction (expensive but correct)
        # Use power method on reduced density via direct SVD of contracted MPS
        with torch.no_grad():
            # Right-canonicalize from right to cut
            t = self.tensors[cut]
            for i in range(self.N - 1, cut, -1):
                t_curr = self.tensors[i]
                d, cL, cR = t_curr.shape
                mat = t_curr.permute(1, 0, 2).reshape(cL, d * cR)
                Q, R = torch.linalg.qr(mat.conj().transpose(0, 1))
                Q = Q.conj().transpose(0, 1)  # [cL, d*cR]
                self.tensors[i] = Q.reshape(cL, d, cR).permute(1, 0, 2)
                # Absorb R into previous
                t_prev = self.tensors[i - 1]
                self.tensors[i - 1] = torch.einsum('aij,kj->aik', t_prev, R.transpose(0, 1).conj())
            # Now SVD at cut
            t = self.tensors[cut]
            d, cL, cR = t.shape
            mat = t.reshape(d * cL, cR) if False else t.permute(1, 0, 2).reshape(cL, d * cR)
            U, S, Vh = torch.linalg.svd(mat, full_matrices=False)
            S = S.real
            S = S / max(S.sum().item(), 1e-12)
            S = torch.clamp(S, min=1e-12)
            return -(S * torch.log(S)).sum()

    def reduced_single(self, site: int):
        """Reduced density matrix on a single site: 2x2 complex matrix."""
        # Contract everything except site, get 2x2 reduced density
        # Approach: contract from both ends towards site
        # Left environment: shape [chi_L]
        env_L = torch.tensor([[1.0+0j]])  # 1x1
        for i in range(site):
            t = self.tensors[i]
            # env_L: [cL_i, cL_i_conj], t: [d, cL_i, cR_i]
            env_L = torch.einsum('ij,dik,djl->kl', env_L, t, t.conj())
        env_R = torch.tensor([[1.0+0j]])
        for i in range(self.N - 1, site, -1):
            t = self.tensors[i]
            env_R = torch.einsum('ij,dki,dlj->kl', env_R, t, t.conj())
        t_site = self.tensors[site]  # [2, cL, cR]
        # rho[d, d'] = sum env_L[a, a'] t_site[d, a, b] t_site[d', a', b'] env_R[b, b']
        rho = torch.einsum('aA,dab,DAB,bB->dD', env_L, t_site, t_site.conj(), env_R)
        return rho


def random_pure_nqubit_mps(n_qubits: int, chi: int = 4, seed: int = 0):
    """Random pure state encoded as MPS with bond dim chi."""
    return MPS.random(n_qubits, chi=chi, seed=seed)


def ghz_mps(n_qubits: int):
    """GHZ state |0...0> + |1...1> as bond-dim 2 MPS."""
    tensors = []
    for i in range(n_qubits):
        if i == 0:
            t = torch.zeros(2, 1, 2, dtype=DTYPE)
            t[0, 0, 0] = 1 / math.sqrt(2)
            t[1, 0, 1] = 1 / math.sqrt(2)
        elif i == n_qubits - 1:
            t = torch.zeros(2, 2, 1, dtype=DTYPE)
            t[0, 0, 0] = 1
            t[1, 1, 0] = 1
        else:
            t = torch.zeros(2, 2, 2, dtype=DTYPE)
            t[0, 0, 0] = 1
            t[1, 1, 1] = 1
        tensors.append(t)
    return MPS(tensors)


def w_mps(n_qubits: int):
    """W state Σ_i |0...010...0>/√n  as bond-dim 2 MPS."""
    tensors = []
    for i in range(n_qubits):
        if i == 0:
            t = torch.zeros(2, 1, 2, dtype=DTYPE)
            t[0, 0, 0] = 1
            t[1, 0, 1] = 1 / math.sqrt(n_qubits)
        elif i == n_qubits - 1:
            t = torch.zeros(2, 2, 1, dtype=DTYPE)
            t[0, 1, 0] = 1
            t[1, 0, 0] = 1
        else:
            t = torch.zeros(2, 2, 2, dtype=DTYPE)
            t[0, 0, 0] = 1
            t[0, 1, 1] = 1
            t[1, 0, 1] = 1
        tensors.append(t)
    return MPS(tensors)


def product_random_mps(n_qubits: int, seed: int = 0):
    """Product state with random single-qubit states."""
    g = torch.Generator().manual_seed(seed)
    vecs = []
    for _ in range(n_qubits):
        v = torch.randn(2, generator=g, dtype=torch.float32) + 1j * torch.randn(2, generator=g, dtype=torch.float32)
        v = v / torch.norm(v)
        vecs.append(v.to(DTYPE))
    return MPS.product(vecs)


# === Engine: applies terrain laws as 2-site Trotter gates ===
class MPSEngineV7:
    """Reservoir engine on MPS. Applies 8 terrain laws as combinations of 1-site and 2-site gates.
    NOT trainable (no PyTorch nn.Module). Used as fixed reservoir."""

    def __init__(self, engine_type: int = 1, chi_max: int = 8, dt: float = 0.06):
        self.engine_type = engine_type
        self.chi_max = chi_max
        self.dt = dt
        self.sign = +1.0 if engine_type == 1 else -1.0
        # Precompute gates (small dt expansions of Hamiltonians + dissipators)
        self._build_gates()

    def _build_gates(self):
        # Single-qubit operator gates (used per terrain × per substage)
        h_unit = 0.77 * SX + 0.13 * SY + 0.6 * SZ
        # Time-evolution gates per Hamiltonian
        self.U_H_local = torch.linalg.matrix_exp(-1j * self.dt * 0.5 * self.sign * h_unit).to(DTYPE)
        # K Hamiltonian (diagonal in Z or X)
        if self.engine_type == 1:
            self.U_K_local = torch.linalg.matrix_exp(-1j * self.dt * 0.5 * SZ).to(DTYPE)
            self.proj_a = (0.5 * (I2 + SZ)).to(DTYPE)
            self.proj_b = (0.5 * (I2 - SZ)).to(DTYPE)
        else:
            self.U_K_local = torch.linalg.matrix_exp(-1j * self.dt * 0.5 * SX).to(DTYPE)
            self.proj_a = (0.5 * (I2 + SX)).to(DTYPE)
            self.proj_b = (0.5 * (I2 - SX)).to(DTYPE)
        # ZZ 2-site gate
        H_zz = torch.kron(SZ, SZ)
        self.U_ZZ = torch.linalg.matrix_exp(-1j * self.dt * 0.3 * H_zz).reshape(2, 2, 2, 2).to(DTYPE)
        # Dissipator approximations as small unitary (Trotter trick — single-site sigma_+- as unitary kick toward target)
        # σ_- pulls toward |0>, σ_+ pulls toward |1>
        gamma = 0.3
        # Approximate Lindblad effect as unitary kick (rough approximation)
        self.U_diss_minus = torch.linalg.matrix_exp(-self.dt * gamma * (SM.conj().T @ SM / 2)).to(DTYPE)
        self.U_diss_plus = torch.linalg.matrix_exp(-self.dt * gamma * (SP.conj().T @ SP / 2)).to(DTYPE)

    def apply_terrain(self, mps: MPS, terrain_idx: int):
        """Apply one stage of terrain dynamics. Acts on every site."""
        N = mps.N
        # 4 terrains (0=Funnel/Cannon, 1=Vortex/Spiral, 2=Pit/Source, 3=Hill/Citadel)
        if terrain_idx == 0:  # Funnel/Cannon: single-site H + multi-Pauli kick
            for i in range(N):
                mps.apply_single(self.U_H_local, i)
        elif terrain_idx == 1:  # Vortex/Spiral: H + ZZ
            for i in range(N):
                mps.apply_single(self.U_H_local, i)
            for i in range(0, N - 1, 2):
                mps.apply_two(self.U_ZZ, i, max_bond=self.chi_max)
        elif terrain_idx == 2:  # Pit/Source: dissipator + H
            U_d = self.U_diss_minus if self.engine_type == 1 else self.U_diss_plus
            for i in range(N):
                mps.apply_single(U_d, i)
                mps.apply_single(self.U_H_local, i)
        else:  # Hill/Citadel: K + strata pinching (project then renormalize)
            for i in range(N):
                mps.apply_single(self.U_K_local, i)

    def operator_kick(self, mps: MPS, op_idx: int, sign: int):
        """Single-qubit kick on site 0 (could extend to all sites)."""
        op = [SZ, SX, SX, SY][op_idx]
        angle = 0.18 * sign
        U = torch.linalg.matrix_exp(-1j * angle * op).to(DTYPE)
        mps.apply_single(U, 0)

    def stage_substages(self, terrain_idx):
        # 4 substages: 4 operators with mixed signs
        return [(0, +1), (1, +1), (2, -1), (3, -1)]

    def stage_sequence(self):
        if self.engine_type == 1:
            return [0, 1, 2, 3, 0, 3, 2, 1]
        else:
            return [0, 3, 2, 1, 0, 1, 2, 3]

    def trajectory_features(self, mps: MPS, n_features_per_substage: int = 5):
        """Run full 32-substage cycle. Extract per-substage features (reliable):
        - Per-site reduced entropy at sites 0, N//2, N-1 (3 features)
        - Bloch z and x at site 0 (2 features)
        Total: 5 features × 32 substages = 160 dims."""
        feats = []
        mps_now = mps.copy()
        for terrain_idx in self.stage_sequence():
            for op_idx, sign in self.stage_substages(terrain_idx):
                self.operator_kick(mps_now, op_idx, sign)
                self.apply_terrain(mps_now, terrain_idx)
                mps_now.normalize_()
                # Single-site reduced densities — reliable
                rho_0 = mps_now.reduced_single(0)
                rho_mid = mps_now.reduced_single(mps_now.N // 2)
                rho_last = mps_now.reduced_single(mps_now.N - 1)
                # Single-site entropies (via 2x2 eigvalsh)
                def site_ent(rho):
                    rho_h = (rho + rho.conj().transpose(-1, -2)) / 2
                    eigs = torch.linalg.eigvalsh(rho_h).real
                    eigs = torch.clamp(eigs, min=1e-9)
                    eigs = eigs / eigs.sum()
                    return -(eigs * torch.log(eigs)).sum().item()
                e0 = site_ent(rho_0); e_mid = site_ent(rho_mid); e_last = site_ent(rho_last)
                bz_0 = (SZ @ rho_0).diag().sum().real.item()
                bx_0 = (SX @ rho_0).diag().sum().real.item()
                feats.append([e0, e_mid, e_last, bz_0, bx_0])
        return torch.tensor(feats, dtype=DTYPE_F).flatten()


if __name__ == "__main__":
    import time
    print("=== v7 MPS engine smoke ===")
    for N in [12, 16, 24, 32]:
        eng = MPSEngineV7(engine_type=1, chi_max=8)
        psi = ghz_mps(N)
        t0 = time.time()
        feats = eng.trajectory_features(psi)
        print(f"  N={N:2d}, chi=8, GHZ → 32 substages: {time.time()-t0:.2f}s, feats shape={feats.shape}")
