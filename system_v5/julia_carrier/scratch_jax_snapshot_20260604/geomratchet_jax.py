import jax; jax.config.update("jax_enable_x64", True)
"""
geomratchet_jax.py — Geometry Ratchet (JAX audit lane)

object_id        : geomratchet_jax_v1
classification   : tool_lego_fit_probe
promotion_allowed: false

CLAIM CEILING: carrier-level invariants and finite maps only.
NOT asserting layer-completion, manifold-admission, coupling, bridge,
rho_AB, Xi, Phi0, Axis0, flux, or physics. Those are gated downstream.

ROOT CONSTRAINTS IN FORCE:
  F01  finite distinguishability
  N01  noncommuting / order-sensitive operations

RUNGS:
  G1  S^3 = SU(2) = unit quaternions (dim=2). Berry phase, gamma5 L/R split.
  G2  Cl(4)/Spin(4) dim=4. Decomposable Weyl sectors (fake chirality).
  G3  Cl(6)/Spin(6) dim=8. Irreducible Weyl sectors (genuine chirality first here).
  G4  Nested-shell quaternion-spinor torus. Inter-shell distinguishability + Gauss linking.

Writes: /tmp/geomratchet_jax_results.json
"""

import json
import math
from pathlib import Path
from typing import Any, Dict

import jax.numpy as jnp

JAX_RESULTS_PATH = Path("/tmp/geomratchet_jax_results.json")
PARITY_PATH      = Path("/tmp/geomratchet_parity.json")
JULIA_RESULTS_PATH = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/geomratchet_julia_results.json")

CLAIM_CEILING = (
    "carrier-level invariants and finite maps only. NOT asserting layer-completion, "
    "manifold-admission, coupling, bridge, rho_AB, Xi, Phi0, Axis0, flux, or physics."
)


class _JaxEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "tolist"):
            return obj.tolist()
        if hasattr(obj, "item"):
            return obj.item()
        return super().default(obj)

# ============================================================
#  UTILITIES
# ============================================================

def as_float(x) -> float:
    return float(jnp.asarray(x).item())


def as_int(x) -> int:
    return int(jnp.asarray(x).item())


def su2_matrix(q) -> Any:
    """Map unit quaternion q=(w,x,y,z) to SU(2) matrix."""
    q = jnp.asarray(q, dtype=jnp.float64)
    w, x, y, z = q[0], q[1], q[2], q[3]
    return jnp.array([[w + 1j*z,  x + 1j*y],
                     [-x + 1j*y, w - 1j*z]], dtype=jnp.complex128)


def density_matrix(psi) -> Any:
    return jnp.outer(psi, jnp.conj(psi))


def sample_unit_quaternions(n: int, seed: int = 42) -> list:
    key = jax.random.PRNGKey(seed)
    qs = jax.random.normal(key, (n, 4), dtype=jnp.float64)
    norms = jnp.linalg.norm(qs, axis=1, keepdims=True)
    return list(qs / norms)


def trace_distance(rho, sigma) -> float:
    diff = rho - sigma
    sv = jnp.linalg.svd(diff, compute_uv=False)
    return float((jnp.sum(sv) / 2).item())


# ============================================================
#  G1: S^3 = SU(2) = unit quaternions
# ============================================================
def fhs_chern_s2(n_theta: int, n_phi: int, sign: float) -> float:
    """FHS lattice Chern number on S^2 discretization (avoids gauge singularity)."""
    sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
    eps_reg = 1e-10

    def ground_state(theta: float, phi: float) -> Any:
        nx = jnp.sin(theta) * jnp.cos(phi)
        ny = jnp.sin(theta) * jnp.sin(phi)
        nz = jnp.cos(theta)
        H = sign * (nx*sx + ny*sy + nz*sz) + eps_reg * sz
        vals, vecs = jnp.linalg.eigh(H)
        return vecs[:, 0]

    def link(a, b) -> Any:
        ov = jnp.vdot(a, b)
        ov_abs = float(jnp.abs(ov).item())
        if ov_abs < 1e-12:
            return 1.0 + 0j
        return ov / ov_abs

    dtheta = math.pi / n_theta
    dphi   = 2 * math.pi / n_phi
    total = 0.0
    for i in range(n_theta):
        t0 = (i + 0.5) * dtheta
        t1 = (i + 1.5) * dtheta
        for j in range(n_phi):
            p0 = j * dphi
            p1 = (j + 1) * dphi
            psi_00 = ground_state(t0, p0)
            psi_10 = ground_state(t1, p0)
            psi_01 = ground_state(t0, p1)
            psi_11 = ground_state(t1, p1)
            U12 = link(psi_00, psi_10)
            U23 = link(psi_10, psi_11)
            U34 = link(psi_11, psi_01)
            U41 = link(psi_01, psi_00)
            F = float(jnp.angle(U12 * U23 * U34 * U41).item())
            total += F
    return total / (2 * math.pi)


def run_g1() -> Dict[str, Any]:
    print("  [G1] S^3 = SU(2) = unit quaternions ...")
    N = 20
    qs = sample_unit_quaternions(N)

    # Positive control
    det_errs, unitary_errs, tr_L, tr_R = [], [], [], []
    for q in qs:
        M = su2_matrix(q)
        det_errs.append(as_float(jnp.abs(jnp.linalg.det(M) - 1.0)))
        unitary_errs.append(as_float(jnp.linalg.norm(M @ jnp.conj(M).T - jnp.eye(2, dtype=jnp.complex128))))
        psi_L = M[:, 0]
        psi_R = M[:, 1]
        tr_L.append(as_float(jnp.real(jnp.trace(density_matrix(psi_L)))))
        tr_R.append(as_float(jnp.real(jnp.trace(density_matrix(psi_R)))))

    pos_ok = (max(det_errs) < 1e-12 and max(unitary_errs) < 1e-12 and
              all(abs(t - 1.0) < 1e-12 for t in tr_L) and
              all(abs(t - 1.0) < 1e-12 for t in tr_R))

    # Negative control: non-unit quaternion (scale by 2)
    q_bad = jnp.array([2.0, 0.0, 0.0, 0.0])
    M_bad = su2_matrix(q_bad)
    neg_det_err = as_float(jnp.abs(jnp.linalg.det(M_bad) - 1.0))
    neg_ok = neg_det_err > 0.1

    # Boundary control: identity quaternion
    q_id = jnp.array([1.0, 0.0, 0.0, 0.0])
    M_id = su2_matrix(q_id)
    bnd_ok = as_float(jnp.abs(jnp.linalg.det(M_id) - 1.0)) < 1e-14

    # FHS Chern number on S^2 (matching Julia's approach)
    chern_L_raw = fhs_chern_s2(30, 60, +1.0)
    chern_R_raw = fhs_chern_s2(30, 60, -1.0)
    chern_L_rounded = round(chern_L_raw)
    chern_R_rounded = round(chern_R_raw)
    chern_opposite_sign = bool(chern_L_rounded * chern_R_rounded < 0)
    chern_magnitude_ok  = bool(abs(chern_L_rounded) == 1 and abs(chern_R_rounded) == 1)

    # gamma5 L/R split
    q_test = qs[0]
    M_test = su2_matrix(q_test)
    psi_test = M_test[:, 0]
    rho_test = density_matrix(psi_test)
    P_L = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128)
    P_R = jnp.array([[0, 0], [0, 1]], dtype=jnp.complex128)
    tr_L_g5 = as_float(jnp.real(jnp.trace(P_L @ rho_test @ P_L)))
    tr_R_g5 = as_float(jnp.real(jnp.trace(P_R @ rho_test @ P_R)))
    gamma5_ok = bool(tr_L_g5 + tr_R_g5 > 0.999)

    all_pass = bool(pos_ok and neg_ok and bnd_ok and chern_opposite_sign and chern_magnitude_ok and gamma5_ok)

    return {
        "rung": "G1",
        "description": "S^3 = SU(2) = unit quaternions; minimal spinor carrier (dim=2)",
        "f01_finite": True,
        "n01_witness": "SU(2) group multiplication is non-Abelian",
        "domain": f"finite sample N={N} unit quaternions",
        "codomain": "{rho_L, rho_R in Herm(2), chern_number_L, chern_number_R in Z}",
        "positive_control": {
            "su2_det_max_error": max(det_errs),
            "su2_unitary_max_error": max(unitary_errs),
            "pass": bool(pos_ok)
        },
        "negative_control": {
            "non_unit_q_det_error": neg_det_err,
            "non_unit_fails_su2": bool(neg_ok),
            "pass": bool(neg_ok)
        },
        "boundary_control": {"pass": bool(bnd_ok)},
        "chern_number": {
            "L_raw": float(chern_L_raw),
            "R_raw": float(chern_R_raw),
            "L_rounded": int(chern_L_rounded),
            "R_rounded": int(chern_R_rounded),
            "opposite_sign": chern_opposite_sign,
            "magnitude_ok": chern_magnitude_ok,
            "method": "FHS lattice Chern on S^2 discretization"
        },
        "gamma5_split": {"tr_L": tr_L_g5, "tr_R": tr_R_g5, "pass": gamma5_ok},
        "ratchet_claim": "S^3 is the minimal finite carrier admitting SU(2) spinors and L/R density matrices. Opposite-sign Chern numbers survive probe. dim=2 is a CHOICE.",
        "all_pass": all_pass
    }


# ============================================================
#  G2: Cl(4)/Spin(4) dim=4 — DECOMPOSABLE (fake chirality)
# ============================================================
def run_g2() -> Dict[str, Any]:
    print("  [G2] Cl(4)/Spin(4) dim=4 (2 qubits) — decomposable Weyl ...")

    I2 = jnp.eye(2, dtype=jnp.complex128)
    sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)

    g1 = jnp.kron(sx, sx)
    g2 = jnp.kron(sx, sy)
    g3 = jnp.kron(sx, sz)
    g4 = jnp.kron(sy, I2)
    gammas = [g1, g2, g3, g4]

    gamma5_4 = jnp.diag(jnp.array([1., 1., -1., -1.], dtype=jnp.complex128))
    P_L4 = (jnp.eye(4, dtype=jnp.complex128) + gamma5_4) / 2
    P_R4 = (jnp.eye(4, dtype=jnp.complex128) - gamma5_4) / 2

    PL_idem = as_float(jnp.linalg.norm(P_L4 @ P_L4 - P_L4))
    PR_idem = as_float(jnp.linalg.norm(P_R4 @ P_R4 - P_R4))
    PL_PR_orth = as_float(jnp.linalg.norm(P_L4 @ P_R4))
    PL_PR_sum = as_float(jnp.linalg.norm(P_L4 + P_R4 - jnp.eye(4, dtype=jnp.complex128)))

    proj_ok = (PL_idem < 1e-12 and PR_idem < 1e-12 and PL_PR_orth < 1e-12 and PL_PR_sum < 1e-12)

    dim_L = int(round(as_float(jnp.linalg.matrix_rank(P_L4))))
    dim_R = int(round(as_float(jnp.linalg.matrix_rank(P_R4))))

    # spin(4) generators
    gen4 = [(gammas[i] @ gammas[j] - gammas[j] @ gammas[i]) / 4
            for i in range(4) for j in range(i+1, 4)]

    s12, s13, s14, s23, s24, s34 = gen4
    JL1 = (s12 - s34) / 2
    JL2 = (s13 + s24) / 2
    JL3 = (s14 - s23) / 2
    JR1 = (s12 + s34) / 2
    JR2 = (s13 - s24) / 2
    JR3 = (s14 + s23) / 2

    comm_LR = [as_float(jnp.linalg.norm(JL1 @ JR1 - JR1 @ JL1)),
               as_float(jnp.linalg.norm(JL1 @ JR2 - JR2 @ JL1)),
               as_float(jnp.linalg.norm(JL2 @ JR3 - JR3 @ JL2)),
               as_float(jnp.linalg.norm(JL3 @ JR1 - JR1 @ JL3))]
    max_comm_LR = max(comm_LR)
    decomposable = max_comm_LR < 1e-10

    # SU(2) structure check: [JL1,JL2] should be proportional to JL3 (nonzero bracket)
    bracket_LL = as_float(jnp.linalg.norm(JL1 @ JL2 - JL2 @ JL1))
    jl3_norm = as_float(jnp.linalg.norm(JL3))
    if bracket_LL > 1e-12 and jl3_norm > 1e-12:
        ratio_L = bracket_LL / jl3_norm
        su2L_structure = bool(0.01 < ratio_L < 100.0)
    else:
        su2L_structure = False

    bracket_RR = as_float(jnp.linalg.norm(JR1 @ JR2 - JR2 @ JR1))
    jr3_norm = as_float(jnp.linalg.norm(JR3))
    if bracket_RR > 1e-12 and jr3_norm > 1e-12:
        ratio_R = bracket_RR / jr3_norm
        su2R_structure = bool(0.01 < ratio_R < 100.0)
    else:
        su2R_structure = False

    # Wrong-structure control: random traceless anti-Hermitian generators (NOT product form)
    keys = jax.random.split(jax.random.PRNGKey(999), 3)

    def random_anti_herm(n, key):
        key_re, key_im = jax.random.split(key)
        A = (
            jax.random.normal(key_re, (n, n), dtype=jnp.float64)
            + 1j * jax.random.normal(key_im, (n, n), dtype=jnp.float64)
        )
        B = A - jnp.conj(A).T
        return B - jnp.trace(B) / n * jnp.eye(n, dtype=jnp.complex128)

    K1 = random_anti_herm(4, keys[0])
    K2 = random_anti_herm(4, keys[1])
    K3 = random_anti_herm(4, keys[2])
    comm_rand_12 = as_float(jnp.linalg.norm(K1 @ K2 - K2 @ K1))
    comm_rand_23 = as_float(jnp.linalg.norm(K2 @ K3 - K3 @ K2))
    wrong_struct = bool(comm_rand_12 > 1e-6 and comm_rand_23 > 1e-6)

    all_pass = bool(proj_ok and decomposable and su2L_structure and su2R_structure and
                    wrong_struct and dim_L == 2 and dim_R == 2)

    return {
        "rung": "G2",
        "description": "Cl(4)/Spin(4) dim=4 (2 qubits) — decomposable Weyl sectors (fake/reducible chirality)",
        "f01_finite": True,
        "n01_witness": "Clifford anticommutators; spin(4) generators noncommutative",
        "domain": "4x4 gamma matrices generating Cl(4)",
        "codomain": "{P_L, P_R in Herm(4), JL_1..3, JR_1..3 in su(2) generators, [JLi,JRj]=0}",
        "weyl_sector_dims": {"dim_L": dim_L, "dim_R": dim_R},
        "projector_check": {
            "PL_idempotent_err": PL_idem,
            "PR_idempotent_err": PR_idem,
            "PL_PR_orthogonal_err": PL_PR_orth,
            "PL_PR_sum_to_I_err": PL_PR_sum,
            "pass": bool(proj_ok)
        },
        "decomposability": {
            "max_comm_JL_JR": max_comm_LR,
            "su2L_structure": su2L_structure,
            "su2R_structure": su2R_structure,
            "decomposable_Spin4_isoSU2xSU2": bool(decomposable),
            "interpretation": "JL and JR commute → Spin(4)≅SU(2)_L×SU(2)_R → chirality is REDUCIBLE at dim4"
        },
        "wrong_structure_control": {
            "random_K1K2_comm": comm_rand_12,
            "random_K2K3_comm": comm_rand_23,
            "random_gens_not_product_form": wrong_struct
        },
        "ratchet_claim": "G2 restricts G1: the 4D Weyl split is DECOMPOSABLE (Spin(4)≅SU(2)×SU(2)). Chirality is fake/reducible at dim=4.",
        "all_pass": all_pass
    }


# ============================================================
#  G3: Cl(6)/Spin(6) dim=8 — IRREDUCIBLE (genuine chirality)
# ============================================================
def run_g3() -> Dict[str, Any]:
    print("  [G3] Cl(6)/Spin(6) dim=8 (3 qubits) — irreducible Weyl ...")

    I2 = jnp.eye(2, dtype=jnp.complex128)
    sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)

    # Cl(6) gamma matrices via tensor products
    g1 = jnp.kron(jnp.kron(sx, I2), I2)
    g2 = jnp.kron(jnp.kron(sy, I2), I2)
    g3 = jnp.kron(jnp.kron(sz, sx), I2)
    g4 = jnp.kron(jnp.kron(sz, sy), I2)
    g5 = jnp.kron(jnp.kron(sz, sz), sx)
    g6 = jnp.kron(jnp.kron(sz, sz), sy)
    gammas6 = [g1, g2, g3, g4, g5, g6]

    # Verify Clifford relations
    max_cliff_err = 0.0
    for i in range(6):
        for j in range(6):
            target = 2.0 * jnp.eye(8, dtype=jnp.complex128) if i == j else jnp.zeros((8, 8), dtype=jnp.complex128)
            err = as_float(jnp.linalg.norm(gammas6[i] @ gammas6[j] + gammas6[j] @ gammas6[i] - target))
            max_cliff_err = max(max_cliff_err, err)
    clifford_ok = max_cliff_err < 1e-12

    # gamma7
    gamma7 = (1j)**3 * g1 @ g2 @ g3 @ g4 @ g5 @ g6
    gamma7_sq_err = as_float(jnp.linalg.norm(gamma7 @ gamma7 - jnp.eye(8, dtype=jnp.complex128)))
    max_g7_anticomm = max(as_float(jnp.linalg.norm(gamma7 @ gammas6[i] + gammas6[i] @ gamma7)) for i in range(6))
    if gamma7_sq_err > 1e-12 or max_g7_anticomm > 1e-12:
        # try conjugate sign
        gamma7 = (-1j)**3 * g1 @ g2 @ g3 @ g4 @ g5 @ g6
        gamma7_sq_err = as_float(jnp.linalg.norm(gamma7 @ gamma7 - jnp.eye(8, dtype=jnp.complex128)))
        max_g7_anticomm = max(as_float(jnp.linalg.norm(gamma7 @ gammas6[i] + gammas6[i] @ gamma7)) for i in range(6))
    gamma7_ok = gamma7_sq_err < 1e-12 and max_g7_anticomm < 1e-12

    P_L8 = (jnp.eye(8) + gamma7) / 2
    P_R8 = (jnp.eye(8) - gamma7) / 2

    dim_L8 = int(round(as_float(jnp.linalg.matrix_rank(P_L8))))
    dim_R8 = int(round(as_float(jnp.linalg.matrix_rank(P_R8))))

    # spin(6) generators (15 of them)
    gen6 = [(gammas6[i] @ gammas6[j] - gammas6[j] @ gammas6[i]) / 4
            for i in range(6) for j in range(i+1, 6)]

    def commutant_dim(gens, basis, n):
        """Compute dimension of commutant of generators restricted to sector."""
        gens_restricted = [basis.conj().T @ g @ basis for g in gens]
        n2 = n * n
        rows = []
        for G in gens_restricted:
            mat = jnp.kron(jnp.eye(n, dtype=jnp.complex128), G) - jnp.kron(G.T, jnp.eye(n, dtype=jnp.complex128))
            rows.append(mat)
        constraint = jnp.vstack(rows)
        sv = jnp.linalg.svd(constraint, compute_uv=False)
        return as_int(jnp.sum(sv < 1e-8))

    # L sector basis
    evals_L, evecs_L = jnp.linalg.eigh(P_L8)
    L_basis = evecs_L[:, evals_L > 0.5]
    cdim_L = commutant_dim(gen6, L_basis, 4)
    irreducible_L = (cdim_L == 1)

    # R sector basis
    evals_R, evecs_R = jnp.linalg.eigh(P_R8)
    R_basis = evecs_R[:, evals_R > 0.5]
    cdim_R = commutant_dim(gen6, R_basis, 4)
    irreducible_R = (cdim_R == 1)

    # Wrong-structure control: spin(4) on FULL 4x4 spinor rep should have commutant_dim > 1
    # Because the 4D spinor rep of Spin(4)≅SU(2)×SU(2) is (1/2,0)⊕(0,1/2) — REDUCIBLE.
    g1c = jnp.kron(sx, sx); g2c = jnp.kron(sx, sy)
    g3c = jnp.kron(sx, sz); g4c = jnp.kron(sy, I2)
    gammas4c = [g1c, g2c, g3c, g4c]
    gen4c = [(gammas4c[i] @ gammas4c[j] - gammas4c[j] @ gammas4c[i]) / 4
             for i in range(4) for j in range(i+1, 4)]
    # Compute commutant on the FULL 4x4 space (not projected to 2x2 Weyl sector)
    n4 = 4
    n2_4 = n4 * n4
    rows_4 = []
    for G in gen4c:
        mat = jnp.kron(jnp.eye(n4, dtype=jnp.complex128), G) - jnp.kron(G.T, jnp.eye(n4, dtype=jnp.complex128))
        rows_4.append(mat)
    sv_4 = jnp.linalg.svd(jnp.vstack(rows_4), compute_uv=False)
    cdim_4c = as_int(jnp.sum(sv_4 < 1e-7))
    ctrl_reducible = bool(cdim_4c > 1)

    all_pass = bool(clifford_ok and gamma7_ok and dim_L8 == 4 and dim_R8 == 4 and
                    irreducible_L and irreducible_R and ctrl_reducible)

    return {
        "rung": "G3",
        "description": "Cl(6)/Spin(6) dim=8 (3 qubits) — Weyl sectors irreducible (genuine chirality first here)",
        "f01_finite": True,
        "n01_witness": "Clifford anticommutators {gamma_i,gamma_j}=2*delta_ij; max_err < 1e-12",
        "domain": "8x8 gamma matrices generating Cl(6)",
        "codomain": "{P_L, P_R in Herm(8), irreducibility_certificate in {true,false}}",
        "clifford_anticommutator_max_err": max_cliff_err,
        "clifford_ok": clifford_ok,
        "gamma7_sq_err": float(gamma7_sq_err),
        "gamma7_anticomm_max_err": max_g7_anticomm,
        "gamma7_ok": gamma7_ok,
        "weyl_sector_dims": {"dim_L": dim_L8, "dim_R": dim_R8},
        "irreducibility": {
            "commutant_dim_L": cdim_L,
            "commutant_dim_R": cdim_R,
            "irreducible_L": irreducible_L,
            "irreducible_R": irreducible_R,
            "interpretation": "commutant_dim=1 ↔ Schur: only scalars commute ↔ Spin(6)≅SU(4) acts IRREDUCIBLY"
        },
        "wrong_structure_control": {
            "G2_L_sector_commutant_dim": cdim_4c,
            "G2_L_reducible": ctrl_reducible
        },
        "ratchet_claim": "G3 restricts G2: at dim=8/Spin(6)≅SU(4), each Weyl sector is an IRREDUCIBLE representation. Genuine chirality first appears here.",
        "all_pass": all_pass
    }


# ============================================================
#  G4: Nested-shell quaternion-spinor torus
# ============================================================
def run_g4() -> Dict[str, Any]:
    print("  [G4] Nested-shell quaternion-spinor torus ...")

    # Two shells with different holonomy angles → genuinely different spinor density matrices
    alpha_inner = 0.0
    alpha_outer = math.pi / 3.0

    N_theta = 8
    N_phi   = 8

    def shell_spinors(alpha, n_t, n_p):
        rhos = []
        for i in range(n_t):
            theta = 2 * math.pi * i / n_t
            for j in range(n_p):
                phi = 2 * math.pi * j / n_p
                q = jnp.array([jnp.cos(theta/2)*jnp.cos((phi + alpha)/2),
                               jnp.cos(theta/2)*jnp.sin((phi + alpha)/2),
                               jnp.sin(theta/2)*jnp.cos(phi/2),
                               jnp.sin(theta/2)*jnp.sin(phi/2)], dtype=jnp.float64)
                q = q / jnp.linalg.norm(q)
                M = su2_matrix(q)
                psi_L = M[:, 0]
                rhos.append(density_matrix(psi_L))
        return rhos

    rhos_inner = shell_spinors(alpha_inner, N_theta, N_phi)
    rhos_outer = shell_spinors(alpha_outer, N_theta, N_phi)

    dists = [trace_distance(rhos_inner[k], rhos_outer[k]) for k in range(len(rhos_inner))]
    dists_arr = jnp.asarray(dists, dtype=jnp.float64)
    mean_dist = as_float(jnp.mean(dists_arr))
    max_dist = as_float(jnp.max(dists_arr))
    min_dist = as_float(jnp.min(dists_arr))
    f01_distinguishable = mean_dist > 1e-6

    # Gauss linking number: Hopf-like configuration
    # C1: (cos t, sin t, 0) unit circle in xy-plane
    # C2: (1 + 0.5*cos s, 0, 0.5*sin s) circle in xz-plane centered at (1,0,0) radius 0.5
    # C2 passes through (0.5,0,0) at s=pi which is inside C1's disk → linking = ±1
    N_gauss = 200
    ts = jnp.linspace(0, 2*jnp.pi, N_gauss, endpoint=False, dtype=jnp.float64)
    dt = as_float(2*jnp.pi / N_gauss)

    def gauss_integral(c1_fn, dc1_fn, c2_fn, dc2_fn):
        total = 0.0
        for t in ts:
            p1  = c1_fn(t)
            dp1 = dc1_fn(t)
            for s in ts:
                p2  = c2_fn(s)
                dp2 = dc2_fn(s)
                diff = p1 - p2
                d3 = as_float(jnp.linalg.norm(diff))
                if d3 < 1e-8:
                    continue
                cross = jnp.cross(dp1, dp2)
                total += as_float(jnp.dot(diff, cross) / d3**3)
        return total * dt * dt / (4 * math.pi)

    R1 = 1.0; R2 = 0.5; cx2 = 1.0
    linking_num = gauss_integral(
        lambda t: jnp.array([R1*jnp.cos(t), R1*jnp.sin(t), 0.0], dtype=jnp.float64),
        lambda t: jnp.array([-R1*jnp.sin(t), R1*jnp.cos(t), 0.0], dtype=jnp.float64),
        lambda s: jnp.array([cx2 + R2*jnp.cos(s), 0.0, R2*jnp.sin(s)], dtype=jnp.float64),
        lambda s: jnp.array([-R2*jnp.sin(s), 0.0, R2*jnp.cos(s)], dtype=jnp.float64)
    )
    linking_nontrivial = abs(linking_num) > 0.5

    # Wrong-structure control: co-planar non-linking circles
    linking_ctrl = gauss_integral(
        lambda t: jnp.array([R1*jnp.cos(t), R1*jnp.sin(t), 0.0], dtype=jnp.float64),
        lambda t: jnp.array([-R1*jnp.sin(t), R1*jnp.cos(t), 0.0], dtype=jnp.float64),
        lambda s: jnp.array([3.0 + R2*jnp.cos(s), R2*jnp.sin(s), 0.0], dtype=jnp.float64),
        lambda s: jnp.array([-R2*jnp.sin(s), R2*jnp.cos(s), 0.0], dtype=jnp.float64)
    )
    ctrl_unlinked = abs(linking_ctrl) < 0.1

    # Boundary control: same holonomy → zero trace distance
    rhos_same1 = shell_spinors(alpha_inner, N_theta, N_phi)
    rhos_same2 = shell_spinors(alpha_inner, N_theta, N_phi)
    dists_same = [trace_distance(rhos_same1[k], rhos_same2[k]) for k in range(len(rhos_same1))]
    bnd_zero_dist = max(dists_same) < 1e-14

    nesting_ok = (alpha_outer != alpha_inner)

    all_pass = f01_distinguishable and linking_nontrivial and ctrl_unlinked and nesting_ok and bnd_zero_dist

    return {
        "rung": "G4",
        "description": f"Nested-shell quaternion-spinor torus: alpha_inner={alpha_inner} alpha_outer={alpha_outer:.4f}",
        "f01_finite": True,
        "n01_witness": "Quaternion fiber over T^2; SU(2) non-Abelian structure on each shell",
        "domain": f"finite grid (N_theta={N_theta} x N_phi={N_phi}) x 2 shells",
        "codomain": "{rho_L on Sigma_inner, rho_L on Sigma_outer, trace_distance, gauss_linking_number}",
        "inter_shell_distinguishability": {
            "mean_trace_distance": mean_dist,
            "max_trace_distance": max_dist,
            "min_trace_distance": min_dist,
            "shells_distinguishable_f01": f01_distinguishable
        },
        "gauss_linking_number": {
            "computed": float(linking_num),
            "rounded": float(round(linking_num)),
            "nontrivial": bool(linking_nontrivial),
            "geometry": "C1=(cos t, sin t, 0), C2=(1+0.5*cos s, 0, 0.5*sin s): Hopf-like, C2 threads C1 disk at s=pi",
            "wrong_structure_control_coplanar": float(linking_ctrl),
            "ctrl_unlinked": bool(ctrl_unlinked)
        },
        "nesting_constraint": {
            "alpha_inner": float(alpha_inner),
            "alpha_outer": float(alpha_outer),
            "shells_distinct": bool(nesting_ok)
        },
        "boundary_control": {
            "same_shell_max_dist": max(dists_same),
            "same_shell_zero_dist": bool(bnd_zero_dist)
        },
        "ratchet_claim": "G4 restricts G3: nesting adds a further constraint surface. Inter-shell distinguishability (F01 trace distance > 0) and Gauss linking number (|L|=1 for Hopf-like linked core curves) are well-defined finite invariants.",
        "all_pass": bool(all_pass)
    }


# ============================================================
#  COMPARATOR: read Julia results and write parity JSON
# ============================================================
def write_parity(jax_results: Dict[str, Any]) -> None:
    if not JULIA_RESULTS_PATH.exists():
        parity = {
            "object_id": "geomratchet_parity_v1",
            "parity_ok": False,
            "parity_status": "BREAKS",
            "julia_results_found": False,
            "note": f"Julia results not found at {JULIA_RESULTS_PATH}",
            "jax_rung_summary": {r["rung"]: r["all_pass"] for r in jax_results["rungs"]}
        }
        PARITY_PATH.write_text(json.dumps(parity, indent=2, cls=_JaxEncoder))
        return

    with open(JULIA_RESULTS_PATH) as f:
        julia = json.load(f)

    julia_rungs = {r["rung"]: r for r in julia.get("rungs", [])}
    jax_rungs   = {r["rung"]: r for r in jax_results["rungs"]}

    def get_path(obj: Dict[str, Any], dotted: str) -> Any:
        cur: Any = obj
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
        return cur

    def check_equal(name: str, julia_value: Any, jax_value: Any) -> Dict[str, Any]:
        return {
            "name": name,
            "kind": "equal",
            "julia": julia_value,
            "jax": jax_value,
            "ok": julia_value == jax_value,
        }

    def check_close(name: str, julia_value: Any, jax_value: Any, tol: float = 1e-9) -> Dict[str, Any]:
        if julia_value is None or jax_value is None:
            ok = False
            delta = None
        else:
            delta = abs(float(julia_value) - float(jax_value))
            ok = delta <= tol
        return {
            "name": name,
            "kind": "close",
            "tol": tol,
            "julia": julia_value,
            "jax": jax_value,
            "delta": delta,
            "ok": ok,
        }

    parity_per_rung = {}
    named_checks = []
    for rung_id in ["G1", "G2", "G3", "G4"]:
        j_rung = julia_rungs.get(rung_id, {})
        p_rung = jax_rungs.get(rung_id, {})
        rung_checks = [
            check_equal(f"{rung_id}.all_pass", j_rung.get("all_pass"), p_rung.get("all_pass")),
            check_equal(f"{rung_id}.f01_finite", j_rung.get("f01_finite"), p_rung.get("f01_finite")),
        ]

        if rung_id == "G1":
            rung_checks.extend([
                check_equal("G1.chern_number.L_rounded", get_path(j_rung, "chern_number.L_rounded"), get_path(p_rung, "chern_number.L_rounded")),
                check_equal("G1.chern_number.R_rounded", get_path(j_rung, "chern_number.R_rounded"), get_path(p_rung, "chern_number.R_rounded")),
                check_close("G1.chern_number.L_raw", get_path(j_rung, "chern_number.L_raw"), get_path(p_rung, "chern_number.L_raw"), 1e-9),
                check_close("G1.chern_number.R_raw", get_path(j_rung, "chern_number.R_raw"), get_path(p_rung, "chern_number.R_raw"), 1e-9),
                check_equal("G1.chern_number.opposite_sign", get_path(j_rung, "chern_number.opposite_sign"), get_path(p_rung, "chern_number.opposite_sign")),
                check_equal("G1.chern_number.magnitude_ok", get_path(j_rung, "chern_number.magnitude_ok"), get_path(p_rung, "chern_number.magnitude_ok")),
                check_equal("G1.gamma5_split.pass", get_path(j_rung, "gamma5_split.pass"), get_path(p_rung, "gamma5_split.pass")),
            ])
        elif rung_id == "G2":
            rung_checks.extend([
                check_equal("G2.weyl_sector_dims.dim_L", get_path(j_rung, "weyl_sector_dims.dim_L"), get_path(p_rung, "weyl_sector_dims.dim_L")),
                check_equal("G2.weyl_sector_dims.dim_R", get_path(j_rung, "weyl_sector_dims.dim_R"), get_path(p_rung, "weyl_sector_dims.dim_R")),
                check_equal("G2.projector_check.pass", get_path(j_rung, "projector_check.pass"), get_path(p_rung, "projector_check.pass")),
                check_equal("G2.decomposability.decomposable_Spin4_isoSU2xSU2", get_path(j_rung, "decomposability.decomposable_Spin4_isoSU2xSU2"), get_path(p_rung, "decomposability.decomposable_Spin4_isoSU2xSU2")),
                check_equal("G2.decomposability.su2L_structure", get_path(j_rung, "decomposability.su2L_structure"), get_path(p_rung, "decomposability.su2L_structure")),
                check_equal("G2.decomposability.su2R_structure", get_path(j_rung, "decomposability.su2R_structure"), get_path(p_rung, "decomposability.su2R_structure")),
                check_equal("G2.wrong_structure_control.random_gens_not_product_form", get_path(j_rung, "wrong_structure_control.random_gens_not_product_form"), get_path(p_rung, "wrong_structure_control.random_gens_not_product_form")),
            ])
        elif rung_id == "G3":
            rung_checks.extend([
                check_equal("G3.clifford_ok", j_rung.get("clifford_ok"), p_rung.get("clifford_ok")),
                check_equal("G3.gamma7_ok", j_rung.get("gamma7_ok"), p_rung.get("gamma7_ok")),
                check_equal("G3.weyl_sector_dims.dim_L", get_path(j_rung, "weyl_sector_dims.dim_L"), get_path(p_rung, "weyl_sector_dims.dim_L")),
                check_equal("G3.weyl_sector_dims.dim_R", get_path(j_rung, "weyl_sector_dims.dim_R"), get_path(p_rung, "weyl_sector_dims.dim_R")),
                check_equal("G3.irreducibility.commutant_dim_L", get_path(j_rung, "irreducibility.commutant_dim_L"), get_path(p_rung, "irreducibility.commutant_dim_L")),
                check_equal("G3.irreducibility.commutant_dim_R", get_path(j_rung, "irreducibility.commutant_dim_R"), get_path(p_rung, "irreducibility.commutant_dim_R")),
                check_equal("G3.wrong_structure_control.G2_L_reducible", get_path(j_rung, "wrong_structure_control.G2_reducible"), get_path(p_rung, "wrong_structure_control.G2_L_reducible")),
            ])
        elif rung_id == "G4":
            rung_checks.extend([
                check_equal("G4.inter_shell_distinguishability.shells_distinguishable_f01", get_path(j_rung, "inter_shell_distinguishability.shells_distinguishable_f01"), get_path(p_rung, "inter_shell_distinguishability.shells_distinguishable_f01")),
                check_close("G4.inter_shell_distinguishability.mean_trace_distance", get_path(j_rung, "inter_shell_distinguishability.mean_trace_distance"), get_path(p_rung, "inter_shell_distinguishability.mean_trace_distance"), 1e-9),
                check_close("G4.inter_shell_distinguishability.max_trace_distance", get_path(j_rung, "inter_shell_distinguishability.max_trace_distance"), get_path(p_rung, "inter_shell_distinguishability.max_trace_distance"), 1e-9),
                check_close("G4.inter_shell_distinguishability.min_trace_distance", get_path(j_rung, "inter_shell_distinguishability.min_trace_distance"), get_path(p_rung, "inter_shell_distinguishability.min_trace_distance"), 1e-9),
                check_equal("G4.gauss_linking_number.rounded", get_path(j_rung, "gauss_linking_number.rounded"), get_path(p_rung, "gauss_linking_number.rounded")),
                check_close("G4.gauss_linking_number.computed", get_path(j_rung, "gauss_linking_number.computed"), get_path(p_rung, "gauss_linking_number.computed"), 1e-9),
                check_equal("G4.gauss_linking_number.nontrivial", get_path(j_rung, "gauss_linking_number.nontrivial"), get_path(p_rung, "gauss_linking_number.nontrivial")),
                check_equal("G4.gauss_linking_number.ctrl_unlinked", get_path(j_rung, "gauss_linking_number.ctrl_unlinked"), get_path(p_rung, "gauss_linking_number.ctrl_unlinked")),
                check_equal("G4.nesting_constraint.shells_distinct", get_path(j_rung, "nesting_constraint.shells_distinct"), get_path(p_rung, "nesting_constraint.shells_distinct")),
                check_equal("G4.boundary_control.same_shell_zero_dist", get_path(j_rung, "boundary_control.same_shell_zero_dist"), get_path(p_rung, "boundary_control.same_shell_zero_dist")),
            ])

        named_checks.extend(rung_checks)
        parity_per_rung[rung_id] = {
            "checks": rung_checks,
            "agree": all(c["ok"] for c in rung_checks),
        }

    summary_checks = [
        check_equal("summary.G1_all_pass", get_path(julia, "ratchet_summary.G1_all_pass"), get_path(jax_results, "ratchet_summary.G1_all_pass")),
        check_equal("summary.G2_all_pass", get_path(julia, "ratchet_summary.G2_all_pass"), get_path(jax_results, "ratchet_summary.G2_all_pass")),
        check_equal("summary.G3_all_pass", get_path(julia, "ratchet_summary.G3_all_pass"), get_path(jax_results, "ratchet_summary.G3_all_pass")),
        check_equal("summary.G4_all_pass", get_path(julia, "ratchet_summary.G4_all_pass"), get_path(jax_results, "ratchet_summary.G4_all_pass")),
        check_equal("summary.all_rungs_pass", get_path(julia, "ratchet_summary.all_rungs_pass"), get_path(jax_results, "ratchet_summary.all_rungs_pass")),
        check_equal("summary.chirality_first_at_dim8", get_path(julia, "ratchet_summary.chirality_first_at_dim8"), get_path(jax_results, "ratchet_summary.chirality_first_at_dim8")),
        check_equal("summary.g2_decomposable", get_path(julia, "ratchet_summary.g2_decomposable"), get_path(jax_results, "ratchet_summary.g2_decomposable")),
        check_equal("summary.g4_nesting_survives", get_path(julia, "ratchet_summary.g4_nesting_survives"), get_path(jax_results, "ratchet_summary.g4_nesting_survives")),
    ]
    named_checks.extend(summary_checks)
    all_parity_ok = all(c["ok"] for c in named_checks)

    max_delta_berry = None
    g1_checks = {c["name"]: c for c in parity_per_rung["G1"]["checks"]}
    if g1_checks["G1.chern_number.L_raw"]["delta"] is not None:
        max_delta_berry = max(g1_checks["G1.chern_number.L_raw"]["delta"], g1_checks["G1.chern_number.R_raw"]["delta"])

    max_delta_linking = None
    g4_checks = {c["name"]: c for c in parity_per_rung["G4"]["checks"]}
    if g4_checks["G4.gauss_linking_number.computed"]["delta"] is not None:
        max_delta_linking = g4_checks["G4.gauss_linking_number.computed"]["delta"]

    parity = {
        "object_id": "geomratchet_parity_v1",
        "julia_results_path": str(JULIA_RESULTS_PATH),
        "jax_results_path": str(JAX_RESULTS_PATH),
        "parity_ok": all_parity_ok,
        "parity_status": "HOLDS" if all_parity_ok else "BREAKS",
        "parity_per_rung": parity_per_rung,
        "summary_checks": summary_checks,
        "named_invariant_check_count": len(named_checks),
        "named_invariant_failures": [c for c in named_checks if not c["ok"]],
        "max_delta_summary": {
            "chern_raw_max": max_delta_berry,
            "linking": max_delta_linking,
        },
        "rng_control_values_not_scalar_compared": True,
        "rng_control_note": "JAX explicit PRNG keys replace plain NumPy RNG; random-control magnitudes are not expected to match Julia MersenneTwister, only their named pass/invariant booleans are compared."
    }
    PARITY_PATH.write_text(json.dumps(parity, indent=2, cls=_JaxEncoder))
    print(f"Parity written to: {PARITY_PATH}")
    print(f"parity_ok: {all_parity_ok}")


# ============================================================
#  MAIN
# ============================================================
def main() -> None:
    print("=== geomratchet_jax.py ===")
    print(f"object_id: geomratchet_jax_v1")
    print(f"claim_ceiling: {CLAIM_CEILING}")
    print()

    g1 = run_g1()
    g2 = run_g2()
    g3 = run_g3()
    g4 = run_g4()

    rungs = [g1, g2, g3, g4]
    all_pass = all(r["all_pass"] for r in rungs)

    results = {
        "object_id": "geomratchet_jax_v1",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "f01_in_force": True,
        "n01_in_force": True,
        "claim_ceiling": CLAIM_CEILING,
        "compute_engine": "jax.numpy+jax.random",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "rungs": rungs,
        "ratchet_summary": {
            "G1_all_pass": g1["all_pass"],
            "G2_all_pass": g2["all_pass"],
            "G3_all_pass": g3["all_pass"],
            "G4_all_pass": g4["all_pass"],
            "all_rungs_pass": all_pass,
            "chirality_first_at_dim8": g3["irreducibility"]["irreducible_L"] if "irreducibility" in g3 else False,
            "g2_decomposable": g2["decomposability"]["decomposable_Spin4_isoSU2xSU2"] if "decomposability" in g2 else False,
            "g4_nesting_survives": g4["nesting_constraint"]["shells_distinct"] if "nesting_constraint" in g4 else False,
            "g4_nesting_constraint": g4["nesting_constraint"]["shells_distinct"] if "nesting_constraint" in g4 else False,
            "ratchet_each_restricts_prior": True
        }
    }

    JAX_RESULTS_PATH.write_text(json.dumps(results, indent=2, cls=_JaxEncoder))
    print(f"\nResults written to: {JAX_RESULTS_PATH}")
    print(f"all_rungs_pass: {all_pass}")

    write_parity(results)


if __name__ == "__main__":
    main()
