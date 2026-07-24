#!/usr/bin/env python3
"""Test two external claims against the running engine.

CLAIM A (cyclic loops): "Cyclic rotations are the same loop." If true, the doc
deductive order Se->Ne->Ni->Si and the owner-hypothetical Ne->Ni->Si->Se are the
SAME cycle at different starting phase, and their return maps must be CONJUGATE
-- identical Liouvillian spectra, fixed points related by the shifted stage map.
Decisive: conjugate maps have identical eigenvalue spectra.

CLAIM B (products of contractions): "Direct products of contractions remain
contractions." If true, coupling two engines by direct product cannot create
basin structure -- contraction coefficient of the product = max of the parts.

Neither claim is assumed. Both are computed.
classification: tool_lego_fit_probe   promotion_allowed: false
"""
from __future__ import annotations
import itertools, json, sys
from pathlib import Path

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax.scipy.linalg import expm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from engine_as_candidate import (  # noqa: E402
    terrain, operator, I2, SX, SY, SZ, _sup_H, _sup_D, TAU, rho_of, state_of,
)

ORDERS = {
    "doc_deductive_S_to_N":   ["Se", "Ne", "Ni", "Si"],
    "owner_hyp_N_to_S":       ["Ne", "Ni", "Si", "Se"],
    "AR01_pack":              ["Ne", "Si", "Se", "Ni"],
    "reversed_doc":           ["Si", "Ni", "Ne", "Se"],
    "doc_inductive":          ["Se", "Si", "Ni", "Ne"],
}
CELL = {"Se": ("Ti", "UP"), "Ne": ("Ti", "DOWN"), "Ni": ("Fe", "DOWN"), "Si": ("Fe", "UP")}


# ---------------- CLAIM A part 1: pure combinatorics ----------------
def rotations(seq):
    return [tuple(seq[i:] + seq[:i]) for i in range(len(seq))]


def combinatorial_relations():
    rel = {}
    names = list(ORDERS)
    for a, b in itertools.combinations(names, 2):
        A, B = ORDERS[a], ORDERS[b]
        is_rot = tuple(B) in rotations(A)
        is_rev_rot = tuple(B) in rotations(list(reversed(A)))
        rel[f"{a}__vs__{b}"] = {
            "same_cycle_rotation": is_rot,
            "reversed_cycle_rotation": is_rev_rot,
            "distinct_cycle": not (is_rot or is_rev_rot),
        }
    return rel


# ---------------- CLAIM A part 2: superoperator spectra ----------------
def stage_super(terr, op, arrow, s=+1.0):
    """4x4 superoperator for one stage (terrain flow composed with operator)."""
    H_eff, jumps = terrain(terr, s)
    Ls = _sup_H(H_eff)
    for L in jumps:
        Ls = Ls + _sup_D(L)
    T = expm(Ls * TAU)                                  # terrain propagator
    # operator as a superoperator, built by acting on the 4 basis matrices
    cols = []
    for k in range(4):
        E = jnp.zeros((4,), dtype=jnp.complex128).at[k].set(1.0).reshape(2, 2)
        cols.append(operator(op, E).reshape(-1))
    O = jnp.stack(cols, axis=1)
    return T @ O if arrow == "UP" else O @ T


def loop_super(order, s=+1.0):
    M = jnp.eye(4, dtype=jnp.complex128)
    for terr in order:                                   # stage 1 acts first
        op, arrow = CELL[terr]
        M = stage_super(terr, op, arrow, s) @ M
    return M


def spectrum(M):
    ev = jnp.linalg.eigvals(M)
    return sorted([complex(z) for z in ev], key=lambda z: (-abs(z), z.real, z.imag))


def fixed_point(M):
    ev, evec = jnp.linalg.eig(M)
    i = int(jnp.argmin(jnp.abs(ev - 1.0)))
    v = evec[:, i].reshape(2, 2)
    v = 0.5 * (v + v.conj().T)
    return v / jnp.trace(v).real


# ---------------- CLAIM B: product of contractions ----------------
def bloch_affine(M):
    """Return the 3x3 linear part of the induced Bloch map, and its largest
    singular value (the contraction coefficient in trace distance)."""
    paulis = [SX, SY, SZ]
    origin = (M @ (0.5 * I2).reshape(-1)).reshape(2, 2)
    cols = []
    for p in paulis:
        rho = 0.5 * (I2 + p)
        out = (M @ rho.reshape(-1)).reshape(2, 2) - origin
        cols.append(jnp.array([jnp.trace(out @ q).real for q in paulis]))
    A = jnp.stack(cols, axis=1)
    sv = jnp.linalg.svd(A, compute_uv=False)
    return float(sv[0])


def main():
    combi = combinatorial_relations()

    spec = {}
    for name, order in ORDERS.items():
        M = loop_super(order)
        s = spectrum(M)
        fp = fixed_point(M)
        spec[name] = {
            "eigenvalues_abs": [round(abs(z), 12) for z in s],
            "subdominant_modulus": round(abs(s[1]), 12),
            "contraction_coefficient": round(bloch_affine(M), 12),
            "fixed_point_bloch": [round(float(jnp.trace(fp @ p).real), 9) for p in (SX, SY, SZ)],
        }

    # spectra equality test between the pairs the combinatorics called rotations
    spectra_match = {}
    for pair, r in combi.items():
        a, b = pair.split("__vs__")
        ea = spec[a]["eigenvalues_abs"]
        eb = spec[b]["eigenvalues_abs"]
        gap = max(abs(x - y) for x, y in zip(ea, eb))
        spectra_match[pair] = {
            "predicted_same_cycle": r["same_cycle_rotation"],
            "max_spectral_gap": round(gap, 12),
            "spectra_identical_1e_9": gap < 1e-9,
        }

    # CLAIM B: contraction coefficient of a direct product of the two engines
    M1 = loop_super(ORDERS["doc_deductive_S_to_N"], s=+1.0)
    M2 = loop_super(ORDERS["doc_deductive_S_to_N"], s=-1.0)
    c1, c2 = bloch_affine(M1), bloch_affine(M2)
    Mprod = jnp.kron(M1, M2)                     # direct product channel on the pair
    ev = jnp.linalg.eigvals(Mprod)
    mods = sorted([float(abs(z)) for z in ev], reverse=True)
    n_unit = int(sum(1 for m in mods if abs(m - 1.0) < 1e-9))

    out = {
        "sim_id": "rotation_and_product_test_v0",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "claim_A_cyclic_rotation": {
            "combinatorial": combi,
            "per_order": spec,
            "spectra_comparison": spectra_match,
        },
        "claim_B_product_of_contractions": {
            "engine1_contraction": round(c1, 12),
            "engine2_contraction": round(c2, 12),
            "product_eigenvalue_moduli_top4": [round(m, 12) for m in mods[:4]],
            "product_unit_eigenvalue_count": n_unit,
            "product_subdominant_modulus": round(mods[1], 12),
            "product_is_contraction": mods[1] < 1.0 and n_unit == 1,
        },
    }
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "rotation_and_product_test_v0.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
