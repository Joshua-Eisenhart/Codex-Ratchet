#!/usr/bin/env python3
"""
crl_ratchet_jax.py
JAX audit lane for the cumulative-exclusion ratchet ladder (CRL).
Reads the Julia reference result and independently replicates the L0..L9
finite-map checks for the same carrier pool at dim=4 and dim=8.
Writes /tmp/crl_ratchet_jax_results.json and /tmp/crl_ratchet_parity.json.

claim_ceiling: JAX parity diagnostic only. No layer-completion, manifold
    admission, coupling, bridge, flux, Axis0, basin, or physics claims.
promotion_allowed: false
"""

import json
import datetime
import sys
import os
import math

# ── JAX setup ─────────────────────────────────────────────────────────────────
os.environ["JAX_ENABLE_X64"] = "1"
try:
    import jax
    import jax.numpy as jnp
    from jax import jit
    jax.config.update("jax_enable_x64", True)
except ImportError as e:
    print(f"FATAL: JAX not available: {e}", file=sys.stderr)
    sys.exit(1)

JULIA_RESULT_PATH = (
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/"
    "system_v5/julia_carrier/crl_ratchet_julia_results.json"
)
JAX_RESULT_PATH  = "/tmp/crl_ratchet_jax_results.json"
PARITY_PATH      = "/tmp/crl_ratchet_parity.json"

TOL          = 1e-10
EPS_COMM     = 1e-10
EPS_ENTROPY  = 1e-10
EPS_ORDER    = 1e-10
EPS_INTER    = 1e-10
RNG_SEED     = 20260604
LADDER_DIMS  = [8, 16, 32, 64]

NONCHIRAL_CARRIERS = {
    "vector_dirac_symmetric", "parity_symmetric",
    "real_structure", "order_independent", "generic_random"
}
CHIRAL_CARRIERS = {"weyl_chiral"}

# ── Numpy-backed operators (JAX arrays) ───────────────────────────────────────
I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)

def kron2(a, b): return jnp.kron(a, b)
def kron3(a, b, c): return jnp.kron(jnp.kron(a, b), c)

def comm_norm(A, B):
    return float(jnp.linalg.norm(A @ B - B @ A))

def von_neumann_entropy(rho, tol=1e-14):
    vals = jnp.linalg.eigvalsh((rho + rho.conj().T) / 2)
    vals = jnp.real(vals)
    S = 0.0
    for v in vals.tolist():
        if v > tol:
            S -= v * math.log(v)
    return S

def dephase(rho, Z_op, gamma=0.5):
    return (1.0 - gamma) * rho + gamma * (Z_op @ rho @ Z_op.conj().T)

def random_hermitian_normalized(dim, rng_key):
    k1, k2 = jax.random.split(rng_key)
    real_part = jax.random.normal(k1, (dim, dim))
    imag_part = jax.random.normal(k2, (dim, dim))
    M = real_part + 1j * imag_part
    H = (M + M.conj().T) / 2.0
    return H / jnp.linalg.norm(H)

def random_state_jax(dim, rng_key):
    k1, k2 = jax.random.split(rng_key)
    real_part = jax.random.normal(k1, (dim,))
    imag_part = jax.random.normal(k2, (dim,))
    psi = real_part + 1j * imag_part
    return psi / jnp.linalg.norm(psi)

def pure_density(psi):
    return jnp.outer(psi, psi.conj())

def trace_distance(rho1, rho2):
    diff = rho1 - rho2
    sv = jnp.linalg.svd(diff, compute_uv=False)
    return float(jnp.sum(sv)) / 2.0

def order_gap_on_state(A, B, psi):
    return float(jnp.linalg.norm(A @ (B @ psi) - B @ (A @ psi)))

def unitary_from_hermitian(op):
    """Extract orthonormal basis (unitary) from a Hermitian op via eigendecomposition."""
    vals, vecs = jnp.linalg.eigh((op + op.conj().T) / 2)
    return vecs  # columns are orthonormal

# ── Carrier builders ──────────────────────────────────────────────────────────

def make_pure_rho(psi):
    psi = psi / jnp.linalg.norm(psi)
    return jnp.outer(psi, psi.conj())

def build_weyl_chiral(dim=4):
    if dim == 4:
        H   = kron2(SX, SZ)    # distinct from U and E; non-commuting with both
        U   = kron2(SX, I2)    # entropy-preserving unitary rotation
        E   = kron2(SZ, I2)    # dephasing op
        psi0 = jnp.array([1, 1, 1, 1], dtype=jnp.complex128) / 2.0  # |+,+>
    else:
        H   = kron3(SX, SZ, I2)
        U   = kron3(SX, I2, I2)
        E   = kron3(SZ, I2, I2)
        psi0 = jnp.ones(8, dtype=jnp.complex128) / (2.0 * jnp.sqrt(2.0))
    rho0 = make_pure_rho(psi0)
    return H, U, E, rho0

def build_vector_dirac(dim=4):
    if dim == 4:
        H   = kron2(SX, SZ) + kron2(SZ, SX)   # symmetric under exchange
        U   = kron2(SX, I2) + kron2(I2, SX)
        E   = kron2(SZ, I2) + kron2(I2, SZ)
        psi0 = jnp.array([1, 1, 1, 1], dtype=jnp.complex128) / 2.0
    else:
        H   = kron3(SX, SZ, I2) + kron3(SZ, SX, I2)
        U   = kron3(SX, I2, I2) + kron3(I2, SX, I2)
        E   = kron3(SZ, I2, I2) + kron3(I2, SZ, I2)
        psi0 = jnp.ones(8, dtype=jnp.complex128) / (2.0 * jnp.sqrt(2.0))
    rho0 = make_pure_rho(psi0)
    return H, U, E, rho0

def build_parity_symmetric(dim=4):
    if dim == 4:
        H   = kron2(SX, I2) + kron2(I2, SX)
        U   = kron2(SX, SZ)
        E   = kron2(SZ, I2) + kron2(I2, SZ)
        psi0 = jnp.array([1, 1, 1, 1], dtype=jnp.complex128) / 2.0
    else:
        H   = kron3(SX, I2, I2) + kron3(I2, SX, I2)
        U   = kron3(SX, SZ, I2)
        E   = kron3(SZ, I2, I2) + kron3(I2, SZ, I2)
        psi0 = jnp.ones(8, dtype=jnp.complex128) / (2.0 * jnp.sqrt(2.0))
    rho0 = make_pure_rho(psi0)
    return H, U, E, rho0

def build_real_structure(dim=4):
    if dim == 4:
        H = jnp.array([[0, 1, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0]], dtype=jnp.complex128)
        U = kron2(SX, SZ)
        E = kron2(SZ, I2)
        psi0 = jnp.array([1, 1, 1, 1], dtype=jnp.complex128) / 2.0
    else:
        H4 = jnp.array([[0, 1, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0]], dtype=jnp.complex128)
        U4 = kron2(SX, SZ)
        E4 = kron2(SZ, I2)
        H = kron2(I2, H4)
        U = kron2(I2, U4)
        E = kron2(I2, E4)
        psi0 = jnp.ones(8, dtype=jnp.complex128) / (2.0 * jnp.sqrt(2.0))
    rho0 = make_pure_rho(psi0)
    return H, U, E, rho0

def build_order_independent(dim=4):
    """ALL operators mutually commute — diagonal matrices. Excluded at L1 (N01)."""
    if dim == 4:
        D1 = jnp.diag(jnp.array([1.0, 2.0, 3.0, 4.0], dtype=jnp.complex128))
        D2 = jnp.diag(jnp.array([4.0, 3.0, 2.0, 1.0], dtype=jnp.complex128))
        D3 = jnp.diag(jnp.array([1.0, -1.0, 1.0, -1.0], dtype=jnp.complex128))
        psi0 = jnp.array([1, 1, 1, 1], dtype=jnp.complex128) / 2.0
    else:
        D1 = jnp.diag(jnp.arange(1.0, 9.0, dtype=jnp.complex128))
        D2 = jnp.diag(jnp.arange(8.0, 0.0, -1.0, dtype=jnp.complex128))
        D3 = jnp.diag(jnp.array([1, -1, 1, -1, 1, -1, 1, -1], dtype=jnp.complex128))
        psi0 = jnp.ones(8, dtype=jnp.complex128) / (2.0 * jnp.sqrt(2.0))
    rho0 = make_pure_rho(psi0)
    return D1, D2, D3, rho0

def build_generic_random(dim=4, seed_offset=0):
    key = jax.random.PRNGKey(RNG_SEED + seed_offset + (0 if dim == 4 else 1))
    k1, k2, k3, k4 = jax.random.split(key, 4)
    H   = random_hermitian_normalized(dim, k1)
    U   = random_hermitian_normalized(dim, k2)
    E   = random_hermitian_normalized(dim, k3)
    psi = random_state_jax(dim, k4)
    rho0 = make_pure_rho(psi)
    return H, U, E, rho0

# ── Layer predicates ──────────────────────────────────────────────────────────

def check_L0(H, U, E, rho0, dim):
    finite_dim  = dim >= 2
    finite_size = all(op.shape == (dim, dim) for op in [H, U, E, rho0])
    finite_ent  = all(bool(jnp.all(jnp.isfinite(jnp.real(op)))) and
                      bool(jnp.all(jnp.isfinite(jnp.imag(op)))) for op in [H, U, E, rho0])
    sat = finite_dim and finite_size and finite_ent
    return {
        "layer": 0,
        "sat": sat,
        "reason": f"F01: dim={dim}, size_ok={finite_size}, entries_ok={finite_ent}",
        "measured_value": float(dim),
        "threshold": 2.0,
    }

def check_L1(H, U, E):
    pairs = [(H, U, "H,U"), (H, E, "H,E"), (U, E, "U,E")]
    best = 0.0
    best_pair = "none"
    for A, B, label in pairs:
        cn = comm_norm(A, B)
        if cn > best:
            best = cn
            best_pair = label
    sat = best > EPS_COMM
    return {
        "layer": 1,
        "sat": sat,
        "reason": f"N01: best_comm_norm={best:.6g} pair={best_pair}",
        "measured_value": best,
        "threshold": EPS_COMM,
    }

def check_L2(rho0, E):
    S0   = von_neumann_entropy(rho0)
    rho1 = dephase(rho0, E)
    S1   = von_neumann_entropy(rho1)
    dS   = S1 - S0
    Q    = unitary_from_hermitian(E)
    rho_U = Q @ rho0 @ Q.conj().T
    dS_U  = abs(von_neumann_entropy(rho_U) - S0)
    sat = dS > -EPS_ENTROPY and dS_U < 1e-8 + EPS_ENTROPY
    return {
        "layer": 2,
        "sat": sat,
        "reason": f"Axis0: dS={dS:.6g}, unitary_dS={dS_U:.6g}",
        "measured_value": dS,
        "threshold": -EPS_ENTROPY,
    }

def check_L3(H, U, E, dim):
    key = jax.random.PRNGKey(RNG_SEED + dim + 3000)
    gaps = []
    for i in range(16):
        k_i = jax.random.fold_in(key, i)
        psi = random_state_jax(dim, k_i)
        gaps.append(order_gap_on_state(U, E, psi))
    max_gap = max(gaps)
    sat = max_gap > EPS_ORDER
    return {
        "layer": 3,
        "sat": sat,
        "reason": f"Axis6: max order_gap={max_gap:.6g}",
        "measured_value": max_gap,
        "threshold": EPS_ORDER,
    }

def check_L4(rho0, U, E):
    S0    = von_neumann_entropy(rho0)
    rho_E = dephase(rho0, E)
    dS_E  = von_neumann_entropy(rho_E) - S0
    Q     = unitary_from_hermitian(U)
    rho_U = Q @ rho0 @ Q.conj().T
    dS_U  = abs(von_neumann_entropy(rho_U) - S0)
    sep   = abs(dS_E - dS_U)
    sat   = dS_E > EPS_ENTROPY and dS_U < 1e-8 + EPS_ENTROPY and sep > EPS_ENTROPY
    return {
        "layer": 4,
        "sat": sat,
        "reason": f"Axis5: sep={sep:.6g}, dS_E={dS_E:.6g}, dS_U={dS_U:.6g}",
        "measured_value": sep,
        "threshold": EPS_ENTROPY,
    }

def check_L5(H, U, E, rho0):
    def apply_cycle(rho, ops):
        for op, is_dep in ops:
            if is_dep:
                rho = dephase(rho, op)
            else:
                Q = unitary_from_hermitian(op)
                rho = Q @ rho @ Q.conj().T
        return rho
    rho_c1 = apply_cycle(rho0, [(U, False), (E, True), (U, False), (E, True)])
    rho_c2 = apply_cycle(rho0, [(E, True), (U, False), (E, True), (U, False)])
    S_c1 = von_neumann_entropy(rho_c1)
    S_c2 = von_neumann_entropy(rho_c2)
    sep = abs(S_c1 - S_c2)
    sat = sep > EPS_ENTROPY
    return {
        "layer": 5,
        "sat": sat,
        "reason": f"Axis3: S_c1={S_c1:.6g}, S_c2={S_c2:.6g}, sep={sep:.6g}",
        "measured_value": sep,
        "threshold": EPS_ENTROPY,
    }

def check_L6(H, U, E, rho0, dim):
    Q_U = unitary_from_hermitian(U)
    rho_t1 = Q_U @ rho0 @ Q_U.conj().T
    rho_t1 = dephase(rho_t1, E)
    rho_t2 = dephase(rho0, E)
    rho_t2 = Q_U @ rho_t2 @ Q_U.conj().T
    var_t1 = float(jnp.var(jnp.real(jnp.linalg.eigvalsh((rho_t1 + rho_t1.conj().T) / 2))))
    var_t2 = float(jnp.var(jnp.real(jnp.linalg.eigvalsh((rho_t2 + rho_t2.conj().T) / 2))))
    sep = abs(var_t1 - var_t2)
    sat = sep > EPS_ENTROPY
    return {
        "layer": 6,
        "sat": sat,
        "reason": f"Axis4: var_t1={var_t1:.6g}, var_t2={var_t2:.6g}, sep={sep:.6g}",
        "measured_value": sep,
        "threshold": EPS_ENTROPY,
    }

def check_L7(dim):
    sat = dim >= 2
    return {
        "layer": 7,
        "sat": sat,
        "reason": f"geometry: dim={dim}",
        "measured_value": float(dim),
        "threshold": 2.0,
    }

def check_L8(rho0, dim):
    k1 = jax.random.PRNGKey(RNG_SEED + dim + 8888)
    k2 = jax.random.fold_in(k1, 1)
    psi_A = random_state_jax(dim, k1)
    psi_B = random_state_jax(dim, k2)
    rho_A = pure_density(psi_A)
    rho_B = pure_density(psi_B)
    td = trace_distance(rho_A, rho_B)
    sat = td > EPS_INTER
    return {
        "layer": 8,
        "sat": sat,
        "reason": f"nested_shells: trace_dist={td:.6g}",
        "measured_value": td,
        "threshold": EPS_INTER,
    }

def check_L9(H, U, E, dim):
    key = jax.random.PRNGKey(RNG_SEED + dim + 9999)
    Q_H = unitary_from_hermitian(H)
    Q_U = unitary_from_hermitian(U)
    gaps = []
    for i in range(32):
        k_i = jax.random.fold_in(key, i)
        psi = random_state_jax(dim, k_i)
        rho = pure_density(psi)
        # Forward: H-unitary, U-unitary, E-dephasing
        rho_fwd = Q_H @ rho @ Q_H.conj().T
        rho_fwd = Q_U @ rho_fwd @ Q_U.conj().T
        rho_fwd = dephase(rho_fwd, E)
        # Reversed: E-dephasing, U-unitary, H-unitary
        rho_rev = dephase(rho, E)
        rho_rev = Q_U @ rho_rev @ Q_U.conj().T
        rho_rev = Q_H @ rho_rev @ Q_H.conj().T
        td = trace_distance(rho_fwd, rho_rev)
        gaps.append(td)
    max_gap = max(gaps)
    sat = max_gap > EPS_ORDER
    return {
        "layer": 9,
        "sat": sat,
        "reason": f"L9: stacking-order td={max_gap:.6g}",
        "measured_value": max_gap,
        "threshold": EPS_ORDER,
    }

def run_cumulative_jax(name, H, U, E, rho0, dim, include_L9=True):
    results = []
    def push(r):
        results.append(r)
        return r["sat"]

    if not push(check_L0(H, U, E, rho0, dim)): return results
    if not push(check_L1(H, U, E)):             return results
    if not push(check_L2(rho0, E)):             return results
    if not push(check_L3(H, U, E, dim)):        return results
    if not push(check_L4(rho0, U, E)):          return results
    if not push(check_L5(H, U, E, rho0)):       return results
    if not push(check_L6(H, U, E, rho0, dim)):  return results
    if not push(check_L7(dim)):                 return results
    if not push(check_L8(rho0, dim)):           return results
    if include_L9:
        push(check_L9(H, U, E, dim))
    return results

def carrier_pool_jax(dim):
    return [
        ("weyl_chiral",            *build_weyl_chiral(dim)),
        ("vector_dirac_symmetric", *build_vector_dirac(dim)),
        ("parity_symmetric",       *build_parity_symmetric(dim)),
        ("real_structure",         *build_real_structure(dim)),
        ("order_independent",      *build_order_independent(dim)),
        ("generic_random",         *build_generic_random(dim)),
    ]

def build_jax_survival_table(pool, dim):
    table = {}
    for (name, H, U, E, rho0) in pool:
        results = run_cumulative_jax(name, H, U, E, rho0, dim, include_L9=True)
        layers = {f"L{r['layer']}": r for r in results}
        first_unsat = next((r["layer"] for r in results if not r["sat"]), "none")
        survived_all = len(results) == 10 and all(r["sat"] for r in results)
        table[name] = {
            "name": name,
            "dim": dim,
            "layers": layers,
            "depth_reached": len(results),
            "final_sat": bool(results[-1]["sat"]) if results else False,
            "first_unsat_layer": first_unsat,
            "survived_all_10": survived_all,
        }
    return table

def erased_L9_L8_run(name, H, U, E, rho0, dim):
    """Run L0..L7 only (erase both L8 and L9), mirroring Julia's check_erased_L9."""
    results = []
    def push(r):
        results.append(r)
        return r["sat"]
    if not push(check_L0(H, U, E, rho0, dim)): return results, False
    if not push(check_L1(H, U, E)):             return results, False
    if not push(check_L2(rho0, E)):             return results, False
    if not push(check_L3(H, U, E, dim)):        return results, False
    if not push(check_L4(rho0, U, E)):          return results, False
    if not push(check_L5(H, U, E, rho0)):       return results, False
    if not push(check_L6(H, U, E, rho0, dim)):  return results, False
    if not push(check_L7(dim)):                 return results, False
    survived = len(results) == 8 and all(r["sat"] for r in results)
    return results, survived

def compute_exclusion_depth(table4, table8):
    for k in range(10):
        all_nonchiral_unsat = True
        all_chiral_sat = True
        for table in [table4, table8]:
            for name in NONCHIRAL_CARRIERS:
                if name in table:
                    row = table[name]
                    lkey = f"L{k}"
                    if lkey in row["layers"]:
                        if row["layers"][lkey]["sat"]:
                            all_nonchiral_unsat = False
                    else:
                        fst = row["first_unsat_layer"]
                        if fst == "none" or (isinstance(fst, int) and fst > k):
                            all_nonchiral_unsat = False
            for name in CHIRAL_CARRIERS:
                if name in table:
                    row = table[name]
                    lkey = f"L{k}"
                    if lkey in row["layers"]:
                        if not row["layers"][lkey]["sat"]:
                            all_chiral_sat = False
                    else:
                        fst = row["first_unsat_layer"]
                        if fst != "none" and isinstance(fst, int) and fst <= k:
                            all_chiral_sat = False
        if all_nonchiral_unsat and all_chiral_sat:
            return k
    return "none"

def compute_parity_max_diff(table4, table8):
    chiral_gaps = []
    nonchiral_gaps = []
    for table in [table4, table8]:
        for name in CHIRAL_CARRIERS:
            if name in table and "L9" in table[name]["layers"]:
                chiral_gaps.append(table[name]["layers"]["L9"]["measured_value"])
        for name in NONCHIRAL_CARRIERS:
            if name in table and "L9" in table[name]["layers"]:
                nonchiral_gaps.append(table[name]["layers"]["L9"]["measured_value"])
    if not chiral_gaps or not nonchiral_gaps:
        return "insufficient_data"
    return f"{max(chiral_gaps) - max(nonchiral_gaps):.6g}"

def size_ladder_checks():
    ladder = {}
    for dim in LADDER_DIMS:
        key = jax.random.PRNGKey(RNG_SEED + dim + 54321)
        k1, k2, k3, k4 = jax.random.split(key, 4)
        H  = random_hermitian_normalized(dim, k1)
        U  = random_hermitian_normalized(dim, k2)
        E  = random_hermitian_normalized(dim, k3)
        psi0 = random_state_jax(dim, k4)
        rho0 = pure_density(psi0)
        l0 = check_L0(H, U, E, rho0, dim)
        l1 = check_L1(H, U, E)
        l2 = check_L2(rho0, E)
        l3 = check_L3(H, U, E, dim)
        l9 = check_L9(H, U, E, dim)
        ladder[f"dim_{dim}"] = {
            "dim": dim,
            "L0_sat": l0["sat"],
            "L1_sat": l1["sat"],
            "L1_comm_norm": l1["measured_value"],
            "L2_sat": l2["sat"],
            "L2_dS": l2["measured_value"],
            "L3_sat": l3["sat"],
            "L3_max_gap": l3["measured_value"],
            "L9_sat": l9["sat"],
            "L9_max_td": l9["measured_value"],
            "all_core_sat": l0["sat"] and l1["sat"] and l2["sat"] and l3["sat"],
        }
    return ladder

def main():
    print("CRL JAX parity lane starting...")

    pool4 = carrier_pool_jax(4)
    pool8 = carrier_pool_jax(8)

    print("Building dim=4 survival table...")
    table4 = build_jax_survival_table(pool4, 4)
    print("Building dim=8 survival table...")
    table8 = build_jax_survival_table(pool8, 8)

    print("Computing exclusion depth...")
    excl_depth = compute_exclusion_depth(table4, table8)

    print("Computing parity max diff...")
    parity_diff = compute_parity_max_diff(table4, table8)

    print("Running size-ladder checks...")
    ladder = size_ladder_checks()

    # Summarize per-carrier
    per_carrier = {}
    for name in CHIRAL_CARRIERS | NONCHIRAL_CARRIERS:
        row4 = table4.get(name)
        row8 = table8.get(name)
        per_carrier[name] = {
            "dim4_first_unsat": row4["first_unsat_layer"] if row4 else "not_run",
            "dim4_survived_all": bool(row4["survived_all_10"]) if row4 else False,
            "dim8_first_unsat": row8["first_unsat_layer"] if row8 else "not_run",
            "dim8_survived_all": bool(row8["survived_all_10"]) if row8 else False,
            "is_chiral_carrier": name in CHIRAL_CARRIERS,
        }

    chiral_survived = all(
        per_carrier.get(n, {}).get("dim4_survived_all", False) and
        per_carrier.get(n, {}).get("dim8_survived_all", False)
        for n in CHIRAL_CARRIERS
    )
    nonchiral_excluded = all(
        not per_carrier.get(n, {}).get("dim4_survived_all", True) or
        not per_carrier.get(n, {}).get("dim8_survived_all", True)
        for n in NONCHIRAL_CARRIERS
    )

    # Load-bearing flip
    flip_results = {}
    all_pools = [(name, H, U, E, rho0) for (name, H, U, E, rho0) in pool4 + pool8]
    for (name, H, U, E, rho0) in all_pools:
        dim = H.shape[0]
        full = run_cumulative_jax(name, H, U, E, rho0, dim, include_L9=True)
        full_survived = len(full) == 10 and all(r["sat"] for r in full)
        _, erased_survived = erased_L9_L8_run(name, H, U, E, rho0, dim)
        flipped = full_survived != erased_survived
        flip_results[f"{name}_dim{dim}"] = {
            "name": name,
            "dim": dim,
            "full_survived": full_survived,
            "erased_L9_L8_survived": erased_survived,
            "verdict_flipped": flipped,
            "load_bearing_label": "L9_IS_LOAD_BEARING" if flipped else "L9_NOT_LOAD_BEARING_AT_THIS_DIM",
        }

    lb_flip_summary = (
        "L9_IS_LOAD_BEARING_for_at_least_one_carrier"
        if any(v["verdict_flipped"] for v in flip_results.values())
        else "L9_NOT_LOAD_BEARING_at_tested_dims"
    )

    # Order-independent excluded by order layer
    oi_excluded = "not_checked"
    for table in [table4, table8]:
        if "order_independent" in table:
            row = table["order_independent"]
            if "L9" in row["layers"] and not row["layers"]["L9"]["sat"]:
                oi_excluded = "UNSAT_at_L9"
                break
            elif "L9" in row["layers"] and row["layers"]["L9"]["sat"]:
                oi_excluded = "SAT_at_L9_unexpected"
                break
            fst = row["first_unsat_layer"]
            if fst != "none":
                oi_excluded = f"UNSAT_at_L{fst}_before_L9"
                break

    print("\n=== JAX CRL PARITY SUMMARY ===")
    print(f"exclusion_depth: {excl_depth}")
    print(f"chiral_survived: {chiral_survived}")
    print(f"nonchiral_excluded: {nonchiral_excluded}")
    print(f"order_independent_excluded_by_order_layer: {oi_excluded}")
    print(f"load_bearing_flip: {lb_flip_summary}")
    print(f"parity_max_diff: {parity_diff}")
    for name in sorted(per_carrier):
        v = per_carrier[name]
        print(f"  {name}: dim4={v['dim4_first_unsat']}, dim8={v['dim8_first_unsat']}, "
              f"survived_dim4={v['dim4_survived_all']}, survived_dim8={v['dim8_survived_all']}")
    print("===============================\n")

    result = {
        "object_id": "crl_ratchet_jax_v1",
        "engine": "jax",
        "jax_version": jax.__version__,
        "claim_ceiling": "JAX parity diagnostic only. No layer-completion, manifold, coupling, bridge, flux, or physics.",
        "promotion_allowed": False,
        "classification": "constraint_probe",
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "rng_seed": RNG_SEED,
        "excl_depth": excl_depth,
        "chiral_survived": chiral_survived,
        "nonchiral_excluded": nonchiral_excluded,
        "order_independent_excluded_by_order_layer": oi_excluded,
        "load_bearing_flip": lb_flip_summary,
        "parity_max_diff": parity_diff,
        "per_carrier_summary": per_carrier,
        "per_carrier_survival_dim4": table4,
        "per_carrier_survival_dim8": table8,
        "size_ladder": ladder,
        "load_bearing_flip_detail": flip_results,
        "tool_manifest": {
            "jax": "load-bearing: matrix ops, eigendecomposition, SVD, random state generation",
            "jax.numpy": "load-bearing: all linear algebra",
            "math": "supportive: log in von Neumann entropy",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "math": "supportive",
        },
        "honest_caveat": (
            "JAX parity lane replicates Julia carrier finite maps independently. "
            "Differences are signals for audit. No layer-completion or manifold claim is licensed."
        ),
    }

    with open(JAX_RESULT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote JAX result: {JAX_RESULT_PATH}")

    # ── Parity comparison ─────────────────────────────────────────────────────
    julia_result = None
    if os.path.exists(JULIA_RESULT_PATH):
        with open(JULIA_RESULT_PATH) as f:
            julia_result = json.load(f)
    else:
        print(f"WARN: Julia result not found at {JULIA_RESULT_PATH}; skipping parity comparison")

    parity = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "julia_result_path": JULIA_RESULT_PATH,
        "jax_result_path": JAX_RESULT_PATH,
        "julia_result_found": julia_result is not None,
        "jax_excl_depth": excl_depth,
        "jax_chiral_survived": chiral_survived,
        "jax_nonchiral_excluded": nonchiral_excluded,
        "jax_oi_excluded": oi_excluded,
        "jax_lb_flip": lb_flip_summary,
        "jax_parity_diff": parity_diff,
        "comparison": {},
        "honest_caveat": (
            "Parity comparison checks whether JAX and Julia arrive at the same "
            "exclusion_depth, chiral_survived, nonchiral_excluded, and L9 verdict. "
            "Disagreements are signals, not proof of error. Neither engine alone admits."
        ),
    }

    if julia_result is not None:
        julia_excl = julia_result.get("exclusion_depth", "not_in_result")
        julia_chiral = julia_result.get("chiral_survived", "not_in_result")
        julia_nc = julia_result.get("nonchiral_excluded", "not_in_result")
        julia_oi = julia_result.get("order_independent_excluded_by_order_layer", "not_in_result")
        julia_lb = julia_result.get("load_bearing_flip", "not_in_result")
        julia_pd = julia_result.get("parity_max_diff", "not_in_result")

        parity["comparison"] = {
            "exclusion_depth": {
                "julia": julia_excl,
                "jax": excl_depth,
                "agree": julia_excl == excl_depth,
            },
            "chiral_survived": {
                "julia": julia_chiral,
                "jax": chiral_survived,
                "agree": julia_chiral == chiral_survived,
            },
            "nonchiral_excluded": {
                "julia": julia_nc,
                "jax": nonchiral_excluded,
                "agree": julia_nc == nonchiral_excluded,
            },
            "order_independent_excluded_by_order_layer": {
                "julia": julia_oi,
                "jax": oi_excluded,
                "agree": julia_oi == oi_excluded,
            },
            "load_bearing_flip": {
                "julia": julia_lb,
                "jax": lb_flip_summary,
                "agree": julia_lb == lb_flip_summary,
            },
        }

        all_agree = all(v.get("agree", False) for v in parity["comparison"].values())
        parity["all_top_level_agree"] = all_agree
        parity["parity_verdict"] = "AGREE" if all_agree else "DISAGREE_signals_audit"

        print("\n=== PARITY COMPARISON ===")
        for k, v in parity["comparison"].items():
            status = "AGREE" if v.get("agree") else "DISAGREE"
            print(f"  {k}: julia={v.get('julia')!r} jax={v.get('jax')!r} -> {status}")
        print(f"OVERALL: {parity['parity_verdict']}")
        print("========================\n")

    with open(PARITY_PATH, "w") as f:
        json.dump(parity, f, indent=2)
    print(f"Wrote parity comparison: {PARITY_PATH}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
