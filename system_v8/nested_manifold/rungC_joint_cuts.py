#!/usr/bin/env python3
"""Nested-manifold runtime — Rung C: joint-state cuts on the two sheets (L7).

The two chirality sheets from Rung A are promoted to a JOINT quantum state
rho_LR (one qubit per sheet) and every claimed readout is computed from an
explicit cut, never asserted. Everything is finite, executed 4x4 algebra.

L7 joint carrier: rho_LR on C^2 (x) C^2. Declared family:
   entangled |psi(t)> = cos(t)|01> + sin(t)|10|, t in [0, pi/2]
   (endpoints t=0, pi/2 are product states inside the same family),
   plus explicit product / mixed controls (product pure, product of
   maximally mixed marginals, classically correlated mixture,
   asymmetric PRODUCT mixture — (0.75|0><0|+0.25|1><1|) (x) |1><1|,
   which factors, so it sits on the product side of every iff-check).
L7 cut readouts (per state, per cut): S_L, S_R, S_LR (von Neumann, bits),
   mutual information I(L:R) = S_L + S_R - S_LR,
   conditional entropy S(L|R) = S_LR - S_R,
   coherent information I_c = -S(L|R),
   negativity N = sum |negative eigenvalues of rho^{T_R}|,
   chirality split DeltaS = S_L - S_R,
   Phi0 = sum_r w_r I_c(cut_r) over the DECLARED 2-cut family
   {cut_1 = (L|R), cut_2 = (R|L)}, w = (1/2, 1/2).

Cut battery (each control must fire):
  C1 mutual-information iff-product, both directions: every product member
     has I(L:R) = 0; every non-product member has I(L:R) > 0.
  C2 negativity > 0 exactly on the entangled members: interior t of the
     pure family is entangled (N > 0); endpoints and all separable
     controls give N = 0 — including the classically correlated mixture,
     which has I > 0 but N = 0 (correlation is not entanglement).
  C3 Phi0 polarity: Phi0 changes sign across the declared family
     (positive on entangled pure members, negative on the mixed product
     control) — drive-polarity witness.
  C4 marginals cannot reconstruct I(L:R): two joint states constructed
     explicitly with IDENTICAL marginals (Bell t=pi/4 vs the product of
     its own marginals) but different I — the joint cut is load-bearing.
  C5 product_no_entanglement control: replacing an entangled joint by the
     product of its marginals kills negativity AND mutual information
     (both measurably nonzero before, zero after — the control fires).
  C6 chirality split: DeltaS = 0 identically on the pure family (Schmidt
     symmetry — recorded as a structural finding, not weakened), and an
     asymmetric PRODUCT mixture witnesses DeltaS != 0 — the split needs
     no correlation between the sheets (first-run red on C1 caught this
     state misclassified as non-product; the state factors, I = 0).

Claim ceiling: executed finite instance; scratch_diagnostic;
promotion_allowed=false; no uniqueness or optimality claim.
"""
import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(__file__).resolve().parent / "results" / "rungC"

CUT_FAMILY = {"cuts": ["L|R", "R|L"], "weights": [0.5, 0.5]}


def ket(i, j):
    v = np.zeros(4, dtype=complex)
    v[2 * i + j] = 1.0
    return v


def entangled(t):
    psi = np.cos(t) * ket(0, 1) + np.sin(t) * ket(1, 0)
    return np.outer(psi, psi.conj())


def vn_entropy(rho):
    w = np.linalg.eigvalsh(rho)
    w = w[w > 1e-14]
    return float(-(w * np.log2(w)).sum())


def ptrace(rho, keep):
    r = rho.reshape(2, 2, 2, 2)  # indices (l, r, l', r')
    if keep == "L":
        return np.trace(r, axis1=1, axis2=3)
    return np.trace(r, axis1=0, axis2=2)


def negativity(rho):
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    w = np.linalg.eigvalsh(pt)
    return float(-w[w < 0].sum())


def cut_readouts(rho):
    S_L = vn_entropy(ptrace(rho, "L"))
    S_R = vn_entropy(ptrace(rho, "R"))
    S_LR = vn_entropy(rho)
    I = S_L + S_R - S_LR
    S_cond = S_LR - S_R          # S(L|R)
    Ic_LR = -S_cond              # coherent information, cut (L|R)
    Ic_RL = -(S_LR - S_L)        # cut (R|L)
    w1, w2 = CUT_FAMILY["weights"]
    phi0 = w1 * Ic_LR + w2 * Ic_RL
    return {"S_L": S_L, "S_R": S_R, "S_LR": S_LR, "I": I,
            "S_L_given_R": S_cond, "I_c": Ic_LR,
            "negativity": negativity(rho),
            "DeltaS": S_L - S_R, "Phi0": phi0}


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")
    OUT.mkdir(parents=True)
    checks, data = {}, {}

    # Declared family: pure sweep + explicit controls
    ts = np.linspace(0.0, np.pi / 2, 9)
    members = {}
    for t in ts:
        members[f"pure_t={t:.4f}"] = entangled(t)
    members["ctrl_product_pure"] = np.outer(ket(0, 1), ket(0, 1).conj())
    members["ctrl_product_maxmixed"] = np.kron(np.eye(2) / 2, np.eye(2) / 2)
    members["ctrl_classical_corr"] = 0.5 * (
        np.outer(ket(0, 1), ket(0, 1).conj())
        + np.outer(ket(1, 0), ket(1, 0).conj()))
    members["ctrl_asym_mixed"] = (
        0.75 * np.outer(ket(0, 1), ket(0, 1).conj())
        + 0.25 * np.outer(ket(1, 1), ket(1, 1).conj()))

    table = {name: cut_readouts(rho) for name, rho in members.items()}
    data["cut_table"] = table
    data["declared_cut_family"] = CUT_FAMILY

    interior = [f"pure_t={t:.4f}" for t in ts[1:-1]]
    endpoints = [f"pure_t={ts[0]:.4f}", f"pure_t={ts[-1]:.4f}"]
    # ctrl_asym_mixed FACTORS as rho_L (x) |1><1| — it is a product state
    # (first run flagged it red under C1 when misclassified as non-product)
    product_members = endpoints + ["ctrl_product_pure",
                                   "ctrl_product_maxmixed",
                                   "ctrl_asym_mixed"]
    nonproduct_members = interior + ["ctrl_classical_corr"]

    # C1: I(L:R) = 0 iff product — witnessed both directions
    checks["C1_product_implies_I_zero"] = all(
        table[m]["I"] < 1e-9 for m in product_members)
    checks["C1_nonproduct_implies_I_positive"] = all(
        table[m]["I"] > 1e-6 for m in nonproduct_members)

    # C2: negativity > 0 exactly on entangled members
    separable = product_members + ["ctrl_classical_corr", "ctrl_asym_mixed"]
    checks["C2_entangled_have_positive_negativity"] = all(
        table[m]["negativity"] > 1e-6 for m in interior)
    checks["C2_separable_have_zero_negativity"] = all(
        table[m]["negativity"] < 1e-9 for m in separable)
    checks["C2_classical_corr_I_positive_negativity_zero"] = (
        table["ctrl_classical_corr"]["I"] > 0.5
        and table["ctrl_classical_corr"]["negativity"] < 1e-9)

    # C3: Phi0 polarity flips across the declared family
    phi0s = {m: table[m]["Phi0"] for m in table}
    data["phi0_by_member"] = phi0s
    checks["C3_phi0_positive_on_entangled_member"] = \
        max(phi0s.values()) > 1e-3
    checks["C3_phi0_negative_on_mixed_product_control"] = \
        phi0s["ctrl_product_maxmixed"] < -1e-3
    checks["C3_phi0_sign_change_across_family"] = (
        max(phi0s.values()) > 1e-3 and min(phi0s.values()) < -1e-3)

    # C4: marginals alone cannot reconstruct I(L:R) — explicit construction
    bell = entangled(np.pi / 4)
    bell_product = np.kron(ptrace(bell, "L"), ptrace(bell, "R"))
    marg_gap = max(
        float(np.abs(ptrace(bell, "L") - ptrace(bell_product, "L")).max()),
        float(np.abs(ptrace(bell, "R") - ptrace(bell_product, "R")).max()))
    I_bell = cut_readouts(bell)["I"]
    I_prod = cut_readouts(bell_product)["I"]
    checks["C4_same_marginals"] = marg_gap < 1e-12
    checks["C4_different_mutual_information"] = abs(I_bell - I_prod) > 0.5
    data["C4_marginal_gap"] = marg_gap
    data["C4_I_bell_vs_I_product"] = [I_bell, I_prod]

    # C5: product_no_entanglement control fires (before nonzero, after zero)
    t_star = np.pi / 3
    rho_e = entangled(t_star)
    before = cut_readouts(rho_e)
    rho_p = np.kron(ptrace(rho_e, "L"), ptrace(rho_e, "R"))
    after = cut_readouts(rho_p)
    checks["C5_control_before_negativity_and_I_nonzero"] = (
        before["negativity"] > 0.1 and before["I"] > 0.1)
    checks["C5_control_after_negativity_and_I_zero"] = (
        after["negativity"] < 1e-9 and after["I"] < 1e-9)
    data["C5_before_after"] = {"before": before, "after": after}

    # C6: chirality split DeltaS — pure-family Schmidt symmetry + witness
    checks["C6_deltaS_zero_on_pure_family_schmidt"] = all(
        abs(table[f"pure_t={t:.4f}"]["DeltaS"]) < 1e-9 for t in ts)
    checks["C6_deltaS_nonzero_witness_asym_mixed"] = \
        abs(table["ctrl_asym_mixed"]["DeltaS"]) > 0.1
    data["deltaS_asym_mixed"] = table["ctrl_asym_mixed"]["DeltaS"]

    receipt = {
        "schema": "ratchet.v8.nested-manifold.rungC.v0",
        "layers_executed": ["L7_joint_state_rho_LR", "L7_cut_readouts",
                            "L7_phi0_two_cut_family"],
        "checks": {k: bool(v) for k, v in checks.items()}, "data": data,
        "all_pass": bool(all(checks.values())),
        "joint_cut_witness": (
            "I(L:R), negativity and Phi0 are computed from explicit cuts of "
            "rho_LR; two joints with identical marginals and different I "
            "show the joint cut is load-bearing; Phi0 polarity flips only "
            "because the family contains mixed members — on pure states "
            "I_c = S_marginal >= 0 (recorded, not smoothed)"),
        "promotion_allowed": False, "formal_admission_allowed": False,
        "claim_ceiling": ("executed finite instance of joint-state cut "
                          "readouts with control battery; entropies in "
                          "bits; no uniqueness/optimality claim"),
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"all_pass": receipt["all_pass"],
                      "checks": receipt["checks"]}, indent=2))


if __name__ == "__main__":
    main()
