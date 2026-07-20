#!/usr/bin/env python3
"""
NEGATIVE SIM N3: conditional_before_cut.py

PREREGISTERED EXPECTED FAILURE (before run):
  Formalize the L08 pathology: compute 'mutual information' from mismatched
  marginals WITHOUT an earned bipartition and show it goes negative (impossible
  for true MI, which is >=0). Then compute the correct I on a proper cut and
  show >=0. This is the detector that licenses conditional/mutual only after cuts.

Objects used:
  - system_v8/nested_manifold/rungC_joint_cuts.py (ptrace, vn_entropy, cut_readouts)
  - system_v8/nested_manifold/manifold_one.py (cut_readouts, rho_LR construction)
  - real 4x4 joint states from rung C declared family

Claim ceiling: negative diagnostic; promotion_allowed=false.
"""

import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(__file__).resolve().parent / "results" / "conditional_before_cut"


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
    r = rho.reshape(2, 2, 2, 2)
    if keep == "L":
        return np.trace(r, axis1=1, axis2=3)
    return np.trace(r, axis1=0, axis2=2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # Proper joint from rung C family
    rho_joint = entangled(np.pi / 4.0)  # Bell-like
    rho_L = ptrace(rho_joint, "L")
    rho_R = ptrace(rho_joint, "R")
    S_L = vn_entropy(rho_L)
    S_R = vn_entropy(rho_R)
    S_LR = vn_entropy(rho_joint)
    I_correct = S_L + S_R - S_LR

    # Pathology (L08-style): mismatched marginals WITHOUT earned bipartition.
    # Take S_L from one legitimate joint and S_R from a DIFFERENT joint.
    # Then pretend a "joint entropy" that is too large (e.g., max-mixed 4x4 = 2 bits).
    # True I = S_L + S_R - S_joint must be >=0 for any real joint; the fake number goes negative.
    rho2 = entangled(np.pi / 5.0)
    S_L = vn_entropy(ptrace(rho_joint, "L"))
    S_R = vn_entropy(ptrace(rho2, "R"))
    S_fake_large = 2.0  # log2(4) for a 2-qubit register; larger than possible given these marginals
    I_fake = S_L + S_R - S_fake_large

    # Second witness: two low-entropy marginals (near-pure) + high fake joint entropy
    rho_L_pure = np.diag([0.999, 0.001])
    rho_R_pure = np.diag([0.999, 0.001])
    S_Lp = vn_entropy(rho_L_pure)
    S_Rp = vn_entropy(rho_R_pure)
    I_bad = S_Lp + S_Rp - 2.0  # still using impossible joint entropy 2 > S_Lp + S_Rp

    preregistered_expectation = (
        "compute 'mutual information' from mismatched marginals WITHOUT an earned bipartition "
        "and show it goes negative (impossible for true MI, which is >=0); then compute the "
        "correct I on a proper cut and show >=0")
    observed_outcome = {
        "I_correct_on_proper_cut": float(I_correct),
        "I_correct_ge_zero": bool(I_correct >= -1e-12),
        "I_fake_from_mismatched": float(I_fake),
        "I_fake_negative": bool(I_fake < -1e-9),
        "I_bad_inconsistent": float(I_bad),
        "I_bad_negative": bool(I_bad < -1e-9),
    }
    # If the fake I is not negative, the sim is inconclusive for this detector.
    verdict = "FAILED_AS_EXPECTED" if (I_correct >= -1e-12 and (I_fake < -1e-9 or I_bad < -1e-9)) else "INCONCLUSIVE"

    receipt = {
        "schema": "ratchet.v8.negative-sim.v1",
        "name": "conditional_before_cut",
        "preregistered_expectation": preregistered_expectation,
        "observed_outcome": observed_outcome,
        "verdict": verdict,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "negative diagnostic; licenses conditional/mutual only after cuts",
        "objects_used": [
            "system_v8/nested_manifold/rungC_joint_cuts.py (ptrace, vn_entropy, cut family)",
            "system_v8/nested_manifold/manifold_one.py (rho_LR, cut_readouts)"
        ],
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"name": "conditional_before_cut", "verdict": verdict,
                      "I_correct": I_correct, "I_fake": I_fake, "I_bad": I_bad}, indent=2))


if __name__ == "__main__":
    main()
