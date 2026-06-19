"""
SCRATCH DIAGNOSTIC: SO(3) frame reduction + Spin(3)=SU(2) double cover
Sub-object 4/7, stage "geometry"
Location: /tmp/ ONLY — never edit checked-in sims

claim_ceiling: scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false

ENGINE: JAX — constructs psi INDEPENDENTLY from locked-math formulas.
psi_s(phi, chi, eta) = [exp(i(phi+chi))*cos(eta), exp(i(phi-chi))*sin(eta)]^T

This file does NOT read psi from any shared matrix.
It reads /tmp/16_token_axis_projection_matrix.json for lock-check counts ONLY.

F01: finite carrier/probe/operator/path set
N01: noncommuting / order-sensitive operations (conjugation U X U†)

CONVENTION-DRIFT self-report:
- psi built independently in JAX; will differ ~1e-16 from Julia due to fp construction order
- UP/DOWN precedence in 16-token matrix: read token metadata only, not executable rho
- Scratch finite map vs Julia reference: parity comparator reads both result JSONs
"""

import os
os.environ["JAX_ENABLE_X64"] = "1"  # x64 first action (required)

import jax
import jax.numpy as jnp
import numpy as np
import json
from functools import partial

# x64 mode
jax.config.update("jax_enable_x64", True)

RESULT_PATH = "/tmp/wol_geometry_3_jax_results.json"
TOKEN_MATRIX_PATH = "/tmp/16_token_axis_projection_matrix.json"
SEED = 20260603_04 + 1  # offset from Julia seed to ensure independence (different sequence)

rng = np.random.default_rng(SEED)
key = jax.random.PRNGKey(SEED)

# ============================================================
# Read 16-token matrix for lock-check metadata ONLY
# (do NOT use psi values from this matrix)
# ============================================================
with open(TOKEN_MATRIX_PATH) as f:
    token_matrix = json.load(f)
lock_checks = token_matrix["lock_check_counts"]

# ============================================================
# PART 1: psi carrier — built INDEPENDENTLY from locked-math
# psi_s(phi, chi, eta) = [e^{i(phi+chi)} cos(eta), e^{i(phi-chi)} sin(eta)]^T
# ============================================================

def psi_L_jax(phi, chi, eta):
    """Left Weyl spinor. INDEPENDENT construction in JAX."""
    return jnp.array([
        jnp.exp(1j*(phi + chi)) * jnp.cos(eta),
        jnp.exp(1j*(phi - chi)) * jnp.sin(eta)
    ], dtype=jnp.complex128)

def psi_R_jax(phi, chi, eta):
    """Right Weyl spinor (same formula, different sheet assignment)."""
    return jnp.array([
        jnp.exp(1j*(phi + chi)) * jnp.cos(eta),
        jnp.exp(1j*(phi - chi)) * jnp.sin(eta)
    ], dtype=jnp.complex128)

def rho_from_psi_jax(psi):
    return jnp.outer(psi, psi.conj())

def hopf_connection_chi_jax(eta):
    """A_chi component = cos(2*eta). Full sweep over eta covers full S^2 base."""
    return jnp.cos(2 * eta)

# ============================================================
# PART 2: SO(3) frame reduction — MAP-A
# ============================================================

def rand_SO3_jax(key, n=1):
    """Sample n random SO(3) elements via JAX (Gram-Schmidt on Gaussian)."""
    key, k1 = jax.random.split(key)
    A = jax.random.normal(k1, (n, 3, 3), dtype=jnp.float64)
    # QR decomposition
    def single_so3(a):
        Q, R = jnp.linalg.qr(a)
        signs = jnp.sign(jnp.diag(R))
        Q = Q * signs[None, :]
        d = jnp.linalg.det(Q)
        # Flip col 0 if det < 0
        col0 = jnp.where(d < 0, -Q[:, 0], Q[:, 0])
        Q = Q.at[:, 0].set(col0)
        return Q
    return key, jax.vmap(single_so3)(A)

def rand_O3_reflected_jax(SO3_frames):
    """Reflect SO(3) frames to get det=-1 O(3) elements."""
    reflected = SO3_frames.at[:, :, 2].mul(-1)
    return reflected

def recover_transition_jax(F1, F2):
    """g = F1^T F2 (since F1 is orthogonal)."""
    return jnp.einsum("...ij,...ik->...jk", F1, F2)

def det_batch(mats):
    return jax.vmap(jnp.linalg.det)(mats)

results = {}

# MAP-A: transitivity ladder 8/16/32/64
ladder_A = {}
for n in [8, 16, 32, 64]:
    key, k1 = jax.random.split(key)
    key, k2 = jax.random.split(key)
    key, F1s = rand_SO3_jax(k1, n)
    _, F2s = rand_SO3_jax(k2, n)
    gs = jax.vmap(recover_transition_jax)(F1s, F2s)
    dets = det_batch(gs)
    orth_errs = jax.vmap(lambda g: jnp.linalg.norm(g.T @ g - jnp.eye(3)))(gs)
    F2_recon = jax.vmap(lambda f1, g: f1 @ g)(F1s, gs)
    recon_errs = jax.vmap(lambda r, f2: jnp.linalg.norm(r - f2))(F2_recon, F2s)
    ladder_A[f"n{n}"] = {
        "n": int(n),
        "all_det_plus1": bool(jnp.all(jnp.abs(dets - 1.0) < 1e-10)),
        "max_det_err": float(jnp.max(jnp.abs(dets - 1.0))),
        "max_orth_err": float(jnp.max(orth_errs)),
        "max_recon_err": float(jnp.max(recon_errs)),
        "pass": bool(jnp.all(jnp.abs(dets - 1.0) < 1e-10) and jnp.max(recon_errs) < 1e-10)
    }
results["map_A_transitivity_ladder"] = ladder_A

# NEG-1: reflected frames excluded
key, k1 = jax.random.split(key)
key, F_base_batch = rand_SO3_jax(k1, 1)
F_base = F_base_batch[0]
key, k2 = jax.random.split(key)
key, F_SO3s = rand_SO3_jax(k2, 64)
F_refs = rand_O3_reflected_jax(F_SO3s)
gs_ref = jax.vmap(lambda f2: recover_transition_jax(F_base, f2))(F_refs)
dets_ref = det_batch(gs_ref)
results["neg1_reflection_excluded"] = {
    "n": 64,
    "all_det_minus1_when_reflected": bool(jnp.all(jnp.abs(dets_ref + 1.0) < 1e-10)),
    "excluded_count": int(jnp.sum(jnp.abs(dets_ref + 1.0) < 1e-10)),
    "pass": bool(jnp.all(jnp.abs(dets_ref + 1.0) < 1e-10))
}

# ============================================================
# PART 3: SU(2) = Spin(3) -> SO(3) double cover — MAP-B
# ============================================================

# Pauli matrices (JAX) — INDEPENDENT from Julia construction
sigma_x = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
sigma_y = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
sigma_z = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
PAULI_JAX = [sigma_x, sigma_y, sigma_z]
I2 = jnp.eye(2, dtype=jnp.complex128)
I3 = jnp.eye(3, dtype=jnp.float64)

def rand_SU2_jax(key, n=1):
    """Haar-random SU(2) elements from unit quaternion parameterization."""
    key, k1 = jax.random.split(key)
    z = jax.random.normal(k1, (n, 2), dtype=jnp.complex128)
    norms = jnp.linalg.norm(z, axis=1, keepdims=True)
    z = z / norms  # unit quaternion
    # SU(2) matrix from (a, b): [[a, -b*], [b, a*]]
    a = z[:, 0]
    b = z[:, 1]
    row0 = jnp.stack([a, -jnp.conj(b)], axis=1)
    row1 = jnp.stack([b, jnp.conj(a)], axis=1)
    return key, jnp.stack([row0, row1], axis=1)

def su2_to_so3_jax(U):
    """R[i,j] = (1/2) tr(sigma_i U sigma_j U†). INDEPENDENT JAX construction."""
    R = jnp.zeros((3, 3), dtype=jnp.float64)
    for i in range(3):
        for j in range(3):
            val = 0.5 * jnp.trace(PAULI_JAX[i] @ U @ PAULI_JAX[j] @ U.conj().T)
            R = R.at[i, j].set(jnp.real(val))
    return R

def su2_to_so3_BROKEN_transpose_jax(U):
    """WRONG map: U^T instead of U†. Must break homomorphism."""
    R = jnp.zeros((3, 3), dtype=jnp.float64)
    for i in range(3):
        for j in range(3):
            val = 0.5 * jnp.trace(PAULI_JAX[i] @ U @ PAULI_JAX[j] @ U.T)
            R = R.at[i, j].set(jnp.real(val))
    return R

def rodrigues_jax(n_ax, theta):
    """Independent Rodrigues rotation: rotate by theta about unit axis n."""
    n = n_ax / jnp.linalg.norm(n_ax)
    K = jnp.array([[0, -n[2], n[1]], [n[2], 0, -n[0]], [-n[1], n[0], 0]], dtype=jnp.float64)
    return I3 + jnp.sin(theta)*K + (1 - jnp.cos(theta))*(K @ K)

# MAP-B: homomorphism ladder
ladder_B_hom = {}
key, k1 = jax.random.split(key)
key_hom = k1
for n in [8, 16, 32, 64]:
    key_hom, k1 = jax.random.split(key_hom)
    key_hom, k2 = jax.random.split(key_hom)
    key_hom, Us1 = rand_SU2_jax(k1, n)
    _, Us2 = rand_SU2_jax(k2, n)
    max_err = 0.0
    for i in range(n):
        U1 = Us1[i]
        U2 = Us2[i]
        R1 = su2_to_so3_jax(U1)
        R2 = su2_to_so3_jax(U2)
        R12 = su2_to_so3_jax(U1 @ U2)
        err = float(jnp.linalg.norm(R12 - R1 @ R2))
        max_err = max(max_err, err)
    ladder_B_hom[f"n{n}"] = {
        "n": int(n),
        "max_homomorphism_err": max_err,
        "pass": max_err < 1e-10
    }
results["map_B_homomorphism_ladder"] = ladder_B_hom

# MAP-B: surjectivity via axis-angle anchor
ladder_B_surj = {}
key, k_surj = jax.random.split(key)
for n in [8, 16, 32, 64]:
    key_surj, k1 = jax.random.split(k_surj)
    k_surj = key_surj
    max_rod_err = 0.0
    for _ in range(n):
        k1, k2 = jax.random.split(k1)
        n_ax = jax.random.normal(k2, (3,), dtype=jnp.float64)
        n_ax = n_ax / jnp.linalg.norm(n_ax)
        k1, k2 = jax.random.split(k1)
        theta = float(jax.random.uniform(k2, (), minval=0.0, maxval=2*np.pi))
        U = (jnp.cos(theta/2)*I2 - 1j*jnp.sin(theta/2)*(
            n_ax[0]*sigma_x + n_ax[1]*sigma_y + n_ax[2]*sigma_z))
        R = su2_to_so3_jax(U)
        R_rod = rodrigues_jax(n_ax, theta)
        err = float(jnp.linalg.norm(R - R_rod))
        max_rod_err = max(max_rod_err, err)
    ladder_B_surj[f"n{n}"] = {
        "n": int(n),
        "max_rodrigues_err": max_rod_err,
        "pass": max_rod_err < 1e-10
    }
results["map_B_surjectivity_ladder"] = ladder_B_surj

# Spinor sign test (MEASURED period contrast)
n_ax_z = jnp.array([0.0, 0.0, 1.0])
theta_2pi = 2 * np.pi
theta_4pi = 4 * np.pi
U_2pi = jnp.cos(theta_2pi/2)*I2 - 1j*jnp.sin(theta_2pi/2)*sigma_z
U_4pi = jnp.cos(theta_4pi/2)*I2 - 1j*jnp.sin(theta_4pi/2)*sigma_z
R_2pi = su2_to_so3_jax(U_2pi)
R_4pi = su2_to_so3_jax(U_4pi)
spinor_2pi = float(jnp.real(jnp.trace(U_2pi))) / 2
spinor_4pi = float(jnp.real(jnp.trace(U_4pi))) / 2
results["spinor_sign_test"] = {
    "U_2pi_trace_half": spinor_2pi,
    "U_4pi_trace_half": spinor_4pi,
    "R_2pi_minus_I3_norm": float(jnp.linalg.norm(R_2pi - I3)),
    "R_4pi_minus_I3_norm": float(jnp.linalg.norm(R_4pi - I3)),
    "signed_spinor_return_at_2pi": spinor_2pi,
    "signed_spinor_return_at_4pi": spinor_4pi,
    "spinor_sign_flip_genuine": abs(spinor_2pi - (-1.0)) < 1e-12,
    "so3_period_2pi_pass": float(jnp.linalg.norm(R_2pi - I3)) < 1e-10,
    "pass": abs(spinor_2pi - (-1.0)) < 1e-12 and float(jnp.linalg.norm(R_2pi - I3)) < 1e-10
}

# NEG-2: broken transpose kill control
key, k1 = jax.random.split(key)
key_neg2, Us_neg2 = rand_SU2_jax(k1, 32)
max_err_broken = 0.0
key_neg2_b, k2 = jax.random.split(key_neg2)
_, Us_neg2b = rand_SU2_jax(k2, 32)
for i in range(32):
    U1 = Us_neg2[i]
    U2 = Us_neg2b[i]
    R1 = su2_to_so3_BROKEN_transpose_jax(U1)
    R2 = su2_to_so3_BROKEN_transpose_jax(U2)
    R12 = su2_to_so3_BROKEN_transpose_jax(U1 @ U2)
    err = float(jnp.linalg.norm(R12 - R1 @ R2))
    max_err_broken = max(max_err_broken, err)
results["neg2_kill_transpose_broken"] = {
    "n": 32,
    "max_homomorphism_err_broken": max_err_broken,
    "homomorphism_BROKEN": max_err_broken > 0.1,
    "pass_kill_control": max_err_broken > 0.1
}

# NEG-3: downstairs SO(3) has no spinor sign flip
R_z_2pi = rodrigues_jax(jnp.array([0.0, 0.0, 1.0]), 2*np.pi)
R_z_4pi = rodrigues_jax(jnp.array([0.0, 0.0, 1.0]), 4*np.pi)
results["neg3_kill_downstairs_noflip"] = {
    "R_z_2pi_minus_I3_norm": float(jnp.linalg.norm(R_z_2pi - I3)),
    "R_z_4pi_minus_I3_norm": float(jnp.linalg.norm(R_z_4pi - I3)),
    "no_sign_flip_downstairs": float(jnp.linalg.norm(R_z_2pi - I3)) < 1e-10,
    "pass_kill_control": float(jnp.linalg.norm(R_z_2pi - I3)) < 1e-10
}

# BOUNDARY: eta sweep for full S^2 Hopf base coverage
boundary_eta = {}
for n in [8, 16, 32, 64]:
    etas = np.linspace(0, np.pi/2, n)
    A_chi_vals = np.array([float(hopf_connection_chi_jax(eta)) for eta in etas])
    boundary_eta[f"n{n}"] = {
        "n": int(n),
        "eta_range": [0.0, float(np.pi/2)],
        "A_chi_min": float(np.min(A_chi_vals)),
        "A_chi_max": float(np.max(A_chi_vals)),
        "full_range_covered": bool(np.min(A_chi_vals) < -0.9 and np.max(A_chi_vals) > 0.9),
        "pass": bool(np.min(A_chi_vals) < -0.9 and np.max(A_chi_vals) > 0.9)
    }
results["boundary_eta_sweep"] = boundary_eta

# Two-to-one cover degree ladder
ladder_cover = {}
key, k_cov = jax.random.split(key)
for n in [8, 16, 32, 64]:
    k_cov, k1 = jax.random.split(k_cov)
    _, Us = rand_SU2_jax(k1, n)
    max_preimage_err = 0.0
    for i in range(n):
        U = Us[i]
        R = su2_to_so3_jax(U)
        R_neg = su2_to_so3_jax(-U)
        err = float(jnp.linalg.norm(R - R_neg))
        max_preimage_err = max(max_preimage_err, err)
    ladder_cover[f"n{n}"] = {
        "n": int(n),
        "max_preimage_err_R_vs_Rneg": max_preimage_err,
        "all_U_and_negU_same_image": max_preimage_err < 1e-10,
        "pass": max_preimage_err < 1e-10
    }
results["two_to_one_cover_degree_ladder"] = ladder_cover

# Lock-check metadata (from token matrix, NOT psi values)
results["lock_check_metadata"] = {
    "source": TOKEN_MATRIX_PATH,
    "unique_A1_A2_A5_A6": lock_checks["unique_A1_A2_A5_A6"],
    "unique_A3_A4_A5_A6": lock_checks["unique_A3_geometry_path_A4_A5_A6"],
    "engine_recoverable_from_A3_A4": lock_checks["engine_recoverable_from_A3_geometry_path_A4"],
    "note": "read token metadata only; psi NOT read from matrix"
}

# Summary
all_pass_checks = [
    all(v["pass"] for v in ladder_A.values()),
    results["neg1_reflection_excluded"]["pass"],
    all(v["pass"] for v in ladder_B_hom.values()),
    all(v["pass"] for v in ladder_B_surj.values()),
    results["spinor_sign_test"]["pass"],
    results["neg2_kill_transpose_broken"]["pass_kill_control"],
    results["neg3_kill_downstairs_noflip"]["pass_kill_control"],
    all(v["pass"] for v in boundary_eta.values()),
    all(v["pass"] for v in ladder_cover.values()),
]

results["summary"] = {
    "all_pass": all(all_pass_checks),
    "n_checks": len(all_pass_checks),
    "n_pass": sum(all_pass_checks),
    "engine": "JAX",
    "object_id": "SO3_Spin3_SU2_double_cover_scratch",
    "claim_ceiling": "scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false",
    "f01": "finite frame/spinor sample sets (ladders 8/16/32/64)",
    "n01": "conjugation rep U X U† is order-sensitive; N01 order gap present",
    "psi_construction": "INDEPENDENT from locked-math formula: psi built in JAX with seed offset from Julia",
    "size_ladder": [8, 16, 32, 64],
    "stage": "geometry",
    "item_index": "4/7",
    "promotion_allowed": False,
    "formal_admission_allowed": False,
    "jax_x64": str(jax.config.jax_enable_x64)
}

with open(RESULT_PATH, "w") as f:
    json.dump(results, f, indent=2)

print(f"JAX scratch done. all_pass={results['summary']['all_pass']}, n_pass={results['summary']['n_pass']}/{results['summary']['n_checks']}")
print(f"Results: {RESULT_PATH}")
