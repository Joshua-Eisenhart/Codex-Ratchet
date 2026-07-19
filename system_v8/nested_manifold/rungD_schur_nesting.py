#!/usr/bin/env python3
"""Nested-manifold runtime — Rung D: Schur-complement nesting witness.

Nesting-matters master witness, computed not asserted. An OUTER layer
(2 auxiliary levels |2>,|3>) encloses an INNER sheet (2 levels |0>,|1>).
The whole 4-level system evolves under one GKSL generator L, written in
Liouville (column-stacked superoperator) form. The Liouville space is
partitioned into the inner block I (matrix elements with both indices on
the inner sheet) and the outer block O (everything touching |2> or |3>).
The enclosing layer is eliminated exactly by the Schur complement

    L_eff = L_II - L_IO  L_OO^{-1}  L_OI

acting on the 4 inner Liouville components. If nesting were decorative,
L_eff would not respond to the outer layer. Every control must fire.

Layers:
  L_outer  2 auxiliary levels with constraint-dependent splittings
           (Delta_2, Delta_3), outer dephasing gph, decay into the sheet.
  L_inner  2-level sheet: splitting omega, coherent drive f, decay k_in.
  Coupling g (|1><2|+h.c.) and g2 (|0><3|+h.c.).

Battery (each control must fire or the rung fails):
  D1 two DIFFERENT outer constraints (A: Delta=1.0/1.5, gph=0.1;
     B: Delta=3.0/0.5, gph=0.8) — same inner layer, same coupling —
     yield DIFFERENT L_eff (Frobenius norm difference > 1e-6);
     both 4x4 L_eff matrices recorded explicitly in the receipt.
  D2 uncoupled control g=g2=0: L_IO L_OO^{-1} L_OI vanishes and
     L_eff = L_II EXACTLY (machine precision), because nothing on the
     inner sheet feeds the outer block (L_OI = 0 exactly).
  D3 the effective inner fixed point (kernel of L_eff, hermitized,
     trace-normalized) MOVES when ONLY the outer layer changes —
     Bures distance witness D_B(rho_A, rho_B) > 1e-6.
  D4 flattening: merging the outer levels into the inner sheet trivially
     (fold |2>->|1>, |3>->|0| applied to every H term and jump operator)
     CHANGES the measured inner entropy production — the steady-state
     entropy flux through the inner decay channel sqrt(k_in)|0><1|
     differs between nested and flattened models by > 1e-6.
  V1 validity cross-check: the Schur-kernel inner state matches the
     inner block of the FULL 16-dim Liouvillian's stationary state
     (exact elimination identity), for both constraints.

Entropy-flux convention: Phi_k = -Tr[D_k(rho_ss) ln rho_ss] per channel
(infinite-temperature-bath entropy-flux form; eigenvalues clipped at
1e-14 before the log; clip magnitude recorded).

Claim ceiling: executed finite instance; scratch_diagnostic;
promotion_allowed=false; no uniqueness or optimality claim.
"""
import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(__file__).resolve().parent / "results" / "rungD"

D4LVL = 4
# inner Liouville components: rho_{ij} with i,j in {0,1}; vec index i + 4j
P_IDX = [i + D4LVL * j for j in (0, 1) for i in (0, 1)]
Q_IDX = [n for n in range(D4LVL * D4LVL) if n not in P_IDX]

# shared parameters (inner layer + coupling identical across constraints)
OMEGA, F_DRIVE, K_IN = 1.0, 0.4, 0.3
G_COUP, G2_COUP, K_OUT = 0.5, 0.35, 0.8
CONSTRAINT_A = {"Delta2": 1.0, "Delta3": 1.5, "gph": 0.1}
CONSTRAINT_B = {"Delta2": 3.0, "Delta3": 0.5, "gph": 0.8}
EIG_CLIP = 1e-14


def ket(i, d=D4LVL):
    v = np.zeros(d, dtype=complex)
    v[i] = 1.0
    return v


def op(i, j, d=D4LVL):
    return np.outer(ket(i, d), ket(j, d).conj())


def hamiltonian_and_jumps(c, g=G_COUP, g2=G2_COUP):
    """4-level nested model: H terms and jump operators as lists."""
    H = (0.5 * OMEGA * (op(0, 0) - op(1, 1))
         + F_DRIVE * (op(0, 1) + op(1, 0))
         + c["Delta2"] * op(2, 2) + c["Delta3"] * op(3, 3)
         + g * (op(1, 2) + op(2, 1)) + g2 * (op(0, 3) + op(3, 0)))
    jumps = [np.sqrt(K_IN) * op(0, 1),            # inner decay
             np.sqrt(K_OUT) * op(0, 2),           # outer -> sheet
             np.sqrt(K_OUT) * op(1, 3),           # outer -> sheet
             np.sqrt(c["gph"]) * (op(2, 2) - op(3, 3))]  # outer dephasing
    return H, jumps


def liouvillian(H, jumps):
    """Column-stacked GKSL superoperator: d vec(rho)/dt = L vec(rho)."""
    d = H.shape[0]
    I = np.eye(d, dtype=complex)
    L = -1j * (np.kron(I, H) - np.kron(H.T, I))
    for K in jumps:
        KdK = K.conj().T @ K
        L += (np.kron(K.conj(), K)
              - 0.5 * np.kron(I, KdK) - 0.5 * np.kron(KdK.T, I))
    return L


def schur_blocks(L):
    L_II = L[np.ix_(P_IDX, P_IDX)]
    L_IO = L[np.ix_(P_IDX, Q_IDX)]
    L_OI = L[np.ix_(Q_IDX, P_IDX)]
    L_OO = L[np.ix_(Q_IDX, Q_IDX)]
    return L_II, L_IO, L_OI, L_OO


def schur_complement(L):
    L_II, L_IO, L_OI, L_OO = schur_blocks(L)
    L_eff = L_II - L_IO @ np.linalg.solve(L_OO, L_OI)
    return L_eff, L_II, L_OI, np.linalg.cond(L_OO)


def kernel_state(M, dim):
    """Smallest right singular vector -> hermitized normalized density."""
    _, s, Vh = np.linalg.svd(M)
    v = Vh[-1].conj()
    rho = v.reshape((dim, dim), order="F")  # column-stacked vec
    rho = 0.5 * (rho + rho.conj().T)
    tr = np.trace(rho).real
    if abs(tr) < 1e-9:
        raise SystemExit("kernel state has vanishing trace")
    rho = rho / tr
    return rho, float(s[-1])


def sqrtm_psd(r):
    w, U = np.linalg.eigh(r)
    w = np.clip(w, 0.0, None)
    return (U * np.sqrt(w)) @ U.conj().T


def bures_distance(r, s):
    sr = sqrtm_psd(r)
    fid = np.trace(sqrtm_psd(sr @ s @ sr)).real ** 2
    return float(np.sqrt(max(0.0, 2.0 * (1.0 - np.sqrt(min(fid, 1.0))))))


def entropy_flux(rho, K):
    """Phi = -Tr[D_K(rho) ln rho], eigenvalues clipped at EIG_CLIP."""
    w, U = np.linalg.eigh(rho)
    w = np.clip(w, EIG_CLIP, None)
    ln_rho = (U * np.log(w)) @ U.conj().T
    KdK = K.conj().T @ K
    Dis = K @ rho @ K.conj().T - 0.5 * (KdK @ rho + rho @ KdK)
    return float(-np.trace(Dis @ ln_rho).real)


def cmat(M):
    return {"re": np.round(M.real, 12).tolist(),
            "im": np.round(M.imag, 12).tolist()}


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")
    OUT.mkdir(parents=True)
    checks, data = {}, {}

    # build both nested Liouvillians (only the outer layer differs)
    L_A = liouvillian(*hamiltonian_and_jumps(CONSTRAINT_A))
    L_B = liouvillian(*hamiltonian_and_jumps(CONSTRAINT_B))
    Leff_A, LII_A, _, cond_A = schur_complement(L_A)
    Leff_B, LII_B, _, cond_B = schur_complement(L_B)
    data["cond_L_OO"] = {"A": float(cond_A), "B": float(cond_B)}

    # sanity: the inner block itself is outer-blind (same L_II both ways)
    lii_same = float(np.abs(LII_A - LII_B).max())
    data["L_II_A_minus_L_II_B_maxabs"] = lii_same

    # D1: different outer constraints -> different L_eff
    d1_norm = float(np.linalg.norm(Leff_A - Leff_B))
    checks["D1_two_outer_constraints_yield_different_Leff"] = \
        d1_norm > 1e-6 and lii_same < 1e-12
    data["Leff_A_minus_Leff_B_frobenius"] = d1_norm
    data["Leff_A"] = cmat(Leff_A)
    data["Leff_B"] = cmat(Leff_B)
    data["L_II"] = cmat(LII_A)

    # D2: uncoupled control g=g2=0 -> L_eff = L_II exactly
    L_unc = liouvillian(*hamiltonian_and_jumps(CONSTRAINT_A, g=0.0, g2=0.0))
    Leff_unc, LII_unc, LOI_unc, _ = schur_complement(L_unc)
    d2_dev = float(np.abs(Leff_unc - LII_unc).max())
    d2_oi = float(np.abs(LOI_unc).max())
    checks["D2_uncoupled_Leff_equals_LII_exactly"] = \
        d2_dev < 1e-12 and d2_oi == 0.0
    data["uncoupled_Leff_minus_LII_maxabs"] = d2_dev
    data["uncoupled_L_OI_maxabs"] = d2_oi

    # D3: effective inner fixed point moves when only the outer changes
    rho_A, sv_A = kernel_state(Leff_A, 2)
    rho_B, sv_B = kernel_state(Leff_B, 2)
    d3_bures = bures_distance(rho_A, rho_B)
    checks["D3_inner_fixed_point_moves_bures"] = d3_bures > 1e-6
    data["bures_inner_fixed_point_A_vs_B"] = d3_bures
    data["inner_fixed_point_A"] = cmat(rho_A)
    data["inner_fixed_point_B"] = cmat(rho_B)
    data["Leff_kernel_singular_values"] = [sv_A, sv_B]

    # V1: exact-elimination cross-check against the FULL 16-dim kernel
    v1 = {}
    for tag, L_full, rho_schur in (("A", L_A, rho_A), ("B", L_B, rho_B)):
        rho_full, sv_full = kernel_state(L_full, 4)
        inner = rho_full[:2, :2]
        inner = 0.5 * (inner + inner.conj().T)
        inner = inner / np.trace(inner).real
        v1[tag] = {"maxabs_diff": float(np.abs(inner - rho_schur).max()),
                   "full_kernel_sv": sv_full,
                   "inner_trace_weight_in_full_ss": float(
                       np.trace(rho_full[:2, :2]).real)}
    checks["V1_schur_kernel_matches_full_ss_inner_block"] = \
        all(v1[t]["maxabs_diff"] < 1e-8 for t in ("A", "B"))
    data["V1_cross_check"] = v1

    # D4: trivial flattening (fold |2>->|1>, |3>->|0>) changes measured
    # inner entropy production (flux through the inner decay channel)
    V = np.zeros((2, 4), dtype=complex)
    V[0, 0] = V[1, 1] = V[1, 2] = V[0, 3] = 1.0
    H_n, jumps_n = hamiltonian_and_jumps(CONSTRAINT_A)
    H_flat = V @ H_n @ V.conj().T
    jumps_flat = [V @ K @ V.conj().T for K in jumps_n]
    L_flat = liouvillian(H_flat, jumps_flat)
    _, sflat, Vh_flat = np.linalg.svd(L_flat)
    v = Vh_flat[-1].conj()
    rho_flat = v.reshape((2, 2), order="F")
    rho_flat = 0.5 * (rho_flat + rho_flat.conj().T)
    rho_flat = rho_flat / np.trace(rho_flat).real
    rho_full_A, _ = kernel_state(L_A, 4)
    K_in_nested = np.sqrt(K_IN) * op(0, 1)
    K_in_flat = np.sqrt(K_IN) * op(0, 1, d=2)
    phi_nested = entropy_flux(rho_full_A, K_in_nested)
    phi_flat = entropy_flux(rho_flat, K_in_flat)
    d4_diff = abs(phi_nested - phi_flat)
    checks["D4_flattening_changes_inner_entropy_production"] = d4_diff > 1e-6
    data["entropy_flux_inner_channel"] = {
        "nested": phi_nested, "flattened": phi_flat, "abs_diff": d4_diff,
        "flat_kernel_sv": float(sflat[-1]), "eig_clip": EIG_CLIP}
    data["flattened_fixed_point"] = cmat(rho_flat)

    receipt = {
        "schema": "ratchet.v8.nested-manifold.rungD.v0",
        "layers_executed": ["L_outer_aux_2level", "L_inner_sheet_2level",
                            "GKSL_liouville_16dim",
                            "schur_complement_elimination"],
        "constraints": {"A": CONSTRAINT_A, "B": CONSTRAINT_B,
                        "shared": {"omega": OMEGA, "f_drive": F_DRIVE,
                                   "k_in": K_IN, "g": G_COUP,
                                   "g2": G2_COUP, "k_out": K_OUT}},
        "checks": {k: bool(v) for k, v in checks.items()}, "data": data,
        "all_pass": bool(all(checks.values())),
        "nesting_matters_witness": (
            "the Schur complement of the enclosing layer reshapes the "
            "inner generator: identical inner blocks (L_II byte-equal "
            "across constraints) acquire DIFFERENT effective dynamics "
            "and DIFFERENT fixed points purely from the outer layer; "
            "cutting the coupling restores L_II exactly; trivially "
            "flattening the outer levels into the sheet changes the "
            "measured inner entropy flux — nesting is load-bearing, "
            "computed"),
        "promotion_allowed": False, "formal_admission_allowed": False,
        "claim_ceiling": ("executed finite instance (one 4-level model, "
                          "two outer constraints); entropy comparison "
                          "uses the infinite-temperature per-channel "
                          "flux convention; no uniqueness/optimality "
                          "claim"),
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"all_pass": receipt["all_pass"],
                      "checks": receipt["checks"]}, indent=2))


if __name__ == "__main__":
    main()
