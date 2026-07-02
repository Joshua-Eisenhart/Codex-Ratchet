import jax; jax.config.update("jax_enable_x64", True)
"""
JAX Audit Lane - G3 Basis-Independence Falsifier
================================================
object_id: wb_g3_basis_independence
item:       g3_basis_independence

Read-only relative to the Julia carrier result. This script recomputes the same
finite map in JAX:

1. Build Cl(6,0) 8x8 gamma matrices.
2. Derive gamma7 from the product of all six gammas.
3. Measure Spin(6) Weyl-sector commutant_dim at identity.
4. Run N=50 random SO(8) basis rotations using jax.random + QR.
5. Run the wrong-structure gamma7=g1*g2 negative control.
6. Compare named invariants against the untouched Julia result JSON.

promotion_allowed: false
classification: tool_lego_fit_probe
"""

import json
import os
import sys

import jax.numpy as jnp
from jax import random

JULIA_RESULTS = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/wb_g3_basis_independence_julia_results.json"
PARITY_OUT = "/tmp/wb_g3_basis_independence_parity.json"
N_ROTATIONS = 50
SEED = 20260604
TOL = 1e-8


def as_py_scalar(x):
    if hasattr(x, "item"):
        return x.item()
    return x


def as_bool(x):
    return bool(as_py_scalar(x))


def as_float(x):
    return float(as_py_scalar(x))


def as_int(x):
    return int(as_py_scalar(x))


def to_jsonable(value):
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "item"):
        return value.item()
    return value


# =============================================================================
# SECTION 1: Build faithful 8x8 Cl(6,0) gamma matrices in JAX
# =============================================================================
I2 = jnp.eye(2, dtype=jnp.complex128)
s1 = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
s2 = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
s3 = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)


def kron3(A, B, C):
    return jnp.kron(A, jnp.kron(B, C))


GAMMAS_RAW = [
    kron3(s1, I2, I2),
    kron3(s2, I2, I2),
    kron3(s3, s1, I2),
    kron3(s3, s2, I2),
    kron3(s3, s3, s1),
    kron3(s3, s3, s2),
]
I8 = jnp.eye(8, dtype=jnp.complex128)


def verify_gamma_algebra(gammas):
    sq_ok = all(as_float(jnp.linalg.norm(g @ g - I8)) < 1e-12 for g in gammas)
    anticomm_ok = all(
        as_float(jnp.linalg.norm(gammas[i] @ gammas[j] + gammas[j] @ gammas[i])) < 1e-12
        for i in range(len(gammas))
        for j in range(len(gammas))
        if i != j
    )
    return sq_ok, anticomm_ok


algebra_gamma_sq_ok, algebra_anticomm_ok = verify_gamma_algebra(GAMMAS_RAW)


# =============================================================================
# SECTION 2: Derive gamma7 from product
# =============================================================================
def make_gamma7_from_product(gammas):
    prod = gammas[0]
    for g in gammas[1:]:
        prod = prod @ g
    prod2 = prod @ prod
    lam = prod2[0, 0]
    phase = 1.0 / jnp.sqrt(lam)
    return phase * prod, lam


gamma7, gamma7_raw_sq = make_gamma7_from_product(GAMMAS_RAW)
gamma7_sq_error = as_float(jnp.linalg.norm(gamma7 @ gamma7 - I8))
gamma7_sq_ok = gamma7_sq_error < 1e-10
gamma7_anticomm_ok = all(
    as_float(jnp.linalg.norm(gamma7 @ g + g @ gamma7)) < 1e-10
    for g in GAMMAS_RAW
)

P_L = (I8 - gamma7) / 2
P_R = (I8 + gamma7) / 2
PL_idem_err = as_float(jnp.linalg.norm(P_L @ P_L - P_L))
PR_idem_err = as_float(jnp.linalg.norm(P_R @ P_R - P_R))
P_sum_err = as_float(jnp.linalg.norm(P_L + P_R - I8))
P_orth_err = as_float(jnp.linalg.norm(P_L @ P_R))
projectors_ok = (
    PL_idem_err < 1e-10
    and PR_idem_err < 1e-10
    and P_sum_err < 1e-10
    and P_orth_err < 1e-10
)
weyl_sector_rank_L = as_int(jnp.rint(jnp.real(jnp.trace(P_L))))
weyl_sector_rank_R = as_int(jnp.rint(jnp.real(jnp.trace(P_R))))


# =============================================================================
# SECTION 3: Spin(6) generators
# =============================================================================
def spin6_generators(gammas):
    gens = []
    for mu in range(len(gammas)):
        for nu in range(mu + 1, len(gammas)):
            gens.append((gammas[mu] @ gammas[nu] - gammas[nu] @ gammas[mu]) / 4)
    return gens


SPIN6_GENS = spin6_generators(GAMMAS_RAW)
assert len(SPIN6_GENS) == 15, f"Expected 15 Spin(6) generators, got {len(SPIN6_GENS)}"


# =============================================================================
# SECTION 4: Commutant dimension measurement
# =============================================================================
def subspace_basis(P, tol=TOL):
    U, s, _ = jnp.linalg.svd(P, full_matrices=True)
    idx = jnp.where(s > tol, size=P.shape[0])[0]
    rank = as_int(jnp.sum(s > tol))
    return U[:, idx[:rank]]


def restrict_to_subspace(M, V):
    return V.conj().T @ M @ V


def commutant_dim_of_generators(gens_restricted, tol=TOL):
    if not gens_restricted:
        return 0
    d = gens_restricted[0].shape[0]
    Id = jnp.eye(d, dtype=jnp.complex128)
    rows = []
    for A in gens_restricted:
        superop = jnp.kron(Id, A) - jnp.kron(A.T, Id)
        rows.append(superop)
    mat = jnp.vstack(rows)
    svs = jnp.linalg.svd(mat, compute_uv=False)
    return as_int(jnp.sum(svs < tol))


def measure_commutant_dim_both_sectors(gammas, g7):
    n = gammas[0].shape[0]
    In = jnp.eye(n, dtype=jnp.complex128)
    PL = (In - g7) / 2
    PR = (In + g7) / 2
    gens = spin6_generators(gammas)
    VL = subspace_basis(PL)
    VR = subspace_basis(PR)
    gens_L = [restrict_to_subspace(S, VL) for S in gens]
    gens_R = [restrict_to_subspace(S, VR) for S in gens]
    return (
        commutant_dim_of_generators(gens_L),
        commutant_dim_of_generators(gens_R),
        VL.shape[1],
        VR.shape[1],
    )


# =============================================================================
# SECTION 5: Random SO(8) rotation sampler
# =============================================================================
def random_so8(key):
    A = random.normal(key, (8, 8), dtype=jnp.float64)
    Q, _ = jnp.linalg.qr(A)
    det = jnp.linalg.det(Q)
    first_col = jnp.where(det < 0, -Q[:, 0], Q[:, 0])
    return Q.at[:, 0].set(first_col)


def rotate_gammas(gammas, O):
    Oc = O.astype(jnp.complex128)
    return [Oc @ g @ Oc.conj().T for g in gammas]


def gamma7_from_gammas(gammas):
    g7, _ = make_gamma7_from_product(gammas)
    return g7


# =============================================================================
# SECTION 6: Boundary check and random rotation sweep
# =============================================================================
print("=== G3 BASIS-INDEPENDENCE FALSIFIER (JAX) ===")
print(f"x64_enabled = {jax.config.jax_enable_x64}")
print(f"F01: finite 8x8 matrices, 6 gammas, 15 Spin(6) gens, N={N_ROTATIONS} rotations")
print("N01: Spin(6) gens noncommuting; commutant sensitive to noncommutativity")
print()

O_id = jnp.eye(8, dtype=jnp.float64)
gammas_id = rotate_gammas(GAMMAS_RAW, O_id)
g7_id = gamma7_from_gammas(gammas_id)
cd_L_id, cd_R_id, rkL_id, rkR_id = measure_commutant_dim_both_sectors(gammas_id, g7_id)
identity_rotation_check_pass = cd_L_id == 1 and cd_R_id == 1
print(
    "BOUNDARY (O=I): "
    f"commutant_dim_L={cd_L_id}, commutant_dim_R={cd_R_id}, "
    f"sector_dim_L={rkL_id}, sector_dim_R={rkR_id}"
)
print(f"  identity_rotation_check_pass = {identity_rotation_check_pass}")

print()
print(f"=== RANDOM ROTATION SWEEP (N={N_ROTATIONS}) ===")

key = random.PRNGKey(SEED)
rotation_keys = random.split(key, N_ROTATIONS)
commutant_dim_L_all_rotations = []
commutant_dim_R_all_rotations = []

for i, rot_key in enumerate(rotation_keys, start=1):
    O = random_so8(rot_key)
    gammas_rot = rotate_gammas(GAMMAS_RAW, O)
    g7_rot = gamma7_from_gammas(gammas_rot)
    cd_L, cd_R, _, _ = measure_commutant_dim_both_sectors(gammas_rot, g7_rot)
    commutant_dim_L_all_rotations.append(cd_L)
    commutant_dim_R_all_rotations.append(cd_R)
    if i <= 5 or cd_L != 1 or cd_R != 1:
        print(f"  rotation {i}: commutant_dim_L={cd_L}, commutant_dim_R={cd_R}")

all_L_one = all(d == 1 for d in commutant_dim_L_all_rotations)
all_R_one = all(d == 1 for d in commutant_dim_R_all_rotations)
basis_independence_survived = all_L_one and all_R_one

print()
print("POSITIVE CHECK RESULT:")
print(f"  all commutant_dim_L == 1: {all_L_one}")
print(f"  all commutant_dim_R == 1: {all_R_one}")
print(f"  basis_independence_survived = {basis_independence_survived}")


# =============================================================================
# SECTION 7: Negative control
# =============================================================================
print()
print("=== NEGATIVE CONTROL (wrong-structure gamma7 = g1*g2 only) ===")

gamma7_wrong = GAMMAS_RAW[0] @ GAMMAS_RAW[1]
g7w_sq_err = as_float(jnp.linalg.norm(gamma7_wrong @ gamma7_wrong - I8))
wrong_structure_gamma7_sq_to_neg_I_err = as_float(
    jnp.linalg.norm(gamma7_wrong @ gamma7_wrong + I8)
)
print(
    "  gamma7_wrong^2 + I error: "
    f"{wrong_structure_gamma7_sq_to_neg_I_err}  (should be ~0)"
)
print(f"  gamma7_wrong^2 - I error: {g7w_sq_err}  (should be large)")

evals_wrong, evecs_wrong = jnp.linalg.eig(gamma7_wrong)
idx_pos = jnp.where(jnp.imag(evals_wrong) > 0, size=gamma7_wrong.shape[0])[0]
idx_neg = jnp.where(jnp.imag(evals_wrong) < 0, size=gamma7_wrong.shape[0])[0]
rank_pos = as_int(jnp.sum(jnp.imag(evals_wrong) > 0))
rank_neg = as_int(jnp.sum(jnp.imag(evals_wrong) < 0))
V_wrong_L = evecs_wrong[:, idx_neg[:rank_neg]]
V_wrong_R = evecs_wrong[:, idx_pos[:rank_pos]]

gens_wrong_L = [restrict_to_subspace(S, V_wrong_L) for S in SPIN6_GENS]
gens_wrong_R = [restrict_to_subspace(S, V_wrong_R) for S in SPIN6_GENS]
wrong_structure_commutant_dim_L = commutant_dim_of_generators(gens_wrong_L)
wrong_structure_commutant_dim_R = commutant_dim_of_generators(gens_wrong_R)
wrong_structure_control_flips_verdict = (
    wrong_structure_commutant_dim_L > 1 or wrong_structure_commutant_dim_R > 1
)
print(f"  wrong_structure commutant_dim_L = {wrong_structure_commutant_dim_L}")
print(f"  wrong_structure commutant_dim_R = {wrong_structure_commutant_dim_R}")
print(
    "  wrong_structure_control_flips_verdict = "
    f"{wrong_structure_control_flips_verdict}"
)


# =============================================================================
# SECTION 8: Result and Julia parity
# =============================================================================
all_pass = (
    algebra_gamma_sq_ok
    and algebra_anticomm_ok
    and gamma7_sq_ok
    and gamma7_anticomm_ok
    and projectors_ok
    and weyl_sector_rank_L == 4
    and weyl_sector_rank_R == 4
    and identity_rotation_check_pass
    and basis_independence_survived
    and wrong_structure_control_flips_verdict
)

jax_result = {
    "object_id": "wb_g3_basis_independence",
    "item": "g3_basis_independence",
    "claim": "Cl(6)/Spin(6) Weyl commutant_dim=1 is basis-independent under SO(8) rotations",
    "classification": "tool_lego_fit_probe",
    "promotion_allowed": False,
    "f01_satisfied": True,
    "f01_evidence": f"finite 8x8 matrices, 6 generators, 15 Spin(6) gens, N={N_ROTATIONS} SO(8) rotations",
    "n01_satisfied": True,
    "n01_evidence": "Spin(6) generators noncommuting; commutant measurement sensitive to noncommutativity structure",
    "algebra_gamma_sq_ok": algebra_gamma_sq_ok,
    "algebra_anticomm_ok": algebra_anticomm_ok,
    "gamma7_sq_error": gamma7_sq_error,
    "gamma7_sq_ok": gamma7_sq_ok,
    "gamma7_anticomm_ok": gamma7_anticomm_ok,
    "projectors_ok": projectors_ok,
    "weyl_sector_rank_L": weyl_sector_rank_L,
    "weyl_sector_rank_R": weyl_sector_rank_R,
    "n_rotations": N_ROTATIONS,
    "seed": SEED,
    "identity_rotation_commutant_dim_L": cd_L_id,
    "identity_rotation_commutant_dim_R": cd_R_id,
    "identity_rotation_check_pass": identity_rotation_check_pass,
    "commutant_dim_L_all_rotations": commutant_dim_L_all_rotations,
    "commutant_dim_R_all_rotations": commutant_dim_R_all_rotations,
    "commutant_dim_L_min": min(commutant_dim_L_all_rotations),
    "commutant_dim_L_max": max(commutant_dim_L_all_rotations),
    "commutant_dim_R_min": min(commutant_dim_R_all_rotations),
    "commutant_dim_R_max": max(commutant_dim_R_all_rotations),
    "basis_independence_survived": basis_independence_survived,
    "wrong_structure_gamma7": "g1*g2 only (partial product, squares to -I not +I)",
    "wrong_structure_gamma7_sq_to_neg_I_err": wrong_structure_gamma7_sq_to_neg_I_err,
    "wrong_structure_commutant_dim_L": wrong_structure_commutant_dim_L,
    "wrong_structure_commutant_dim_R": wrong_structure_commutant_dim_R,
    "wrong_structure_control_flips_verdict": wrong_structure_control_flips_verdict,
    "all_pass": all_pass,
    "claim_ceiling": {
        "layer_completion": False,
        "manifold_admission": False,
        "coupling": False,
        "bridge": False,
        "physics": False,
        "promotion_allowed": False,
        "verdict": f"irreducibility SURVIVED N={N_ROTATIONS} random SO(8) basis changes; consistent with basis-independence under F01+N01",
    },
    "compute_engine": "jax+jax.numpy",
    "x64_enabled": bool(jax.config.jax_enable_x64),
}

with open(JULIA_RESULTS, "r") as f:
    julia_result = json.load(f)

parity_keys = [
    "object_id",
    "item",
    "classification",
    "promotion_allowed",
    "f01_satisfied",
    "n01_satisfied",
    "algebra_gamma_sq_ok",
    "algebra_anticomm_ok",
    "gamma7_sq_ok",
    "gamma7_anticomm_ok",
    "projectors_ok",
    "weyl_sector_rank_L",
    "weyl_sector_rank_R",
    "n_rotations",
    "seed",
    "identity_rotation_commutant_dim_L",
    "identity_rotation_commutant_dim_R",
    "identity_rotation_check_pass",
    "commutant_dim_L_all_rotations",
    "commutant_dim_R_all_rotations",
    "commutant_dim_L_min",
    "commutant_dim_L_max",
    "commutant_dim_R_min",
    "commutant_dim_R_max",
    "basis_independence_survived",
    "wrong_structure_commutant_dim_L",
    "wrong_structure_commutant_dim_R",
    "wrong_structure_control_flips_verdict",
    "wrong_structure_gamma7",
    "all_pass",
]

numeric_tolerance_keys = {
    "gamma7_sq_error": 1e-10,
    "wrong_structure_gamma7_sq_to_neg_I_err": 1e-10,
}

parity_mismatches = {}
for key_name in parity_keys:
    if jax_result.get(key_name) != julia_result.get(key_name):
        parity_mismatches[key_name] = {
            "jax": jax_result.get(key_name),
            "julia": julia_result.get(key_name),
        }

for key_name, tol in numeric_tolerance_keys.items():
    jax_value = jax_result.get(key_name)
    julia_value = julia_result.get(key_name)
    diff = abs(float(jax_value) - float(julia_value))
    if diff > tol:
        parity_mismatches[key_name] = {
            "jax": jax_value,
            "julia": julia_value,
            "abs_diff": diff,
            "tol": tol,
        }

identity_diff_L = abs(cd_L_id - julia_result.get("identity_rotation_commutant_dim_L", 10**9))
identity_diff_R = abs(cd_R_id - julia_result.get("identity_rotation_commutant_dim_R", 10**9))
parity_max_diff = float(max(identity_diff_L, identity_diff_R))
parity_match = not parity_mismatches
parity_status = "HOLDS" if parity_match else "BREAKS"

parity = {
    "object_id": "wb_g3_basis_independence",
    "item": "g3_basis_independence",
    "promotion_allowed": False,
    "classification": "tool_lego_fit_probe",
    "compute_engine": "jax+jax.numpy",
    "x64_enabled": bool(jax.config.jax_enable_x64),
    "jax_result": jax_result,
    "julia_reference_path": JULIA_RESULTS,
    "julia_read_ok": True,
    "parity_keys_compared": parity_keys + sorted(numeric_tolerance_keys),
    "parity_mismatches": parity_mismatches,
    "parity_match": parity_match,
    "parity_status": parity_status,
    "parity_max_diff": parity_max_diff,
    "jax_commutant_dim_L_identity": cd_L_id,
    "jax_commutant_dim_R_identity": cd_R_id,
    "julia_commutant_dim_L_identity": julia_result.get("identity_rotation_commutant_dim_L"),
    "julia_commutant_dim_R_identity": julia_result.get("identity_rotation_commutant_dim_R"),
    "note": (
        "JAX recomputes the Cl(6)/Spin(6) finite map, 50 SO(8) rotations, "
        "identity boundary, and wrong-structure control. parity_status=HOLDS "
        "means named invariants matched the untouched Julia JSON."
    ),
}

with open(PARITY_OUT, "w") as f:
    json.dump(to_jsonable(parity), f, indent=2)

print()
print("=== FINAL RESULT ===")
print(f"  all_pass = {all_pass}")
print(f"  parity_status = {parity_status}")
print(f"  parity_match = {parity_match}")
print(f"  parity_max_diff = {parity_max_diff}")
print(f"  parity_mismatches = {json.dumps(to_jsonable(parity_mismatches), sort_keys=True)}")
print(f"  Written to: {PARITY_OUT}")

if not parity_match:
    print("PARITY MISMATCH: JAX and Julia disagree on one or more named invariants.")
    sys.exit(1)

print("JAX audit lane: COMPLETE")
