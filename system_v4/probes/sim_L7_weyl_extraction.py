#!/usr/bin/env python3
"""
Layer 7 — Weyl Extraction SIM
==============================
L7 in the 19-layer pre-entropy ladder: left/right spinor extraction from
the same carrier point. Starts from SIM_TEMPLATE.

Weyl projectors on a Hopf-lifted 2-spinor psi in C^2 under the chiral
generator sigma_z:
    P_L = (I - sigma_z)/2   (projects to spin-down / left component)
    P_R = (I + sigma_z)/2   (projects to spin-up  / right component)

Admission claims checked:
  Pos 1: idempotence P_L^2=P_L, P_R^2=P_R (symbolically via sympy)
  Pos 2: orthogonality P_L P_R = 0 (symbolically via sympy)
  Pos 3: completeness P_L + P_R = I (symbolically via sympy)
  Pos 4: for a sampled family of S^3/Hopf points psi,
         ||psi_L||^2 + ||psi_R||^2 == 1  and  <psi_L|psi_R> = 0 (numerical)
  Neg 1: a non-chiral "projector" P_bad = (I - sigma_x)/2 does NOT
         commute with sigma_z -> L/R split not preserved under chirality
  Neg 2: swapping L/R labels breaks completeness: P_L + P_L != I
  Boundary: psi on the chiral poles (|0>, |1>) -> one component is exact
            zero up to float eps.

Classification: canonical (sympy is load_bearing for algebraic identities;
numeric checks are supportive).
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# Imports / try-probe
try:
    import torch  # noqa: F401
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "available but not required for L7 algebra"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
    TOOL_MANIFEST["pyg"]["reason"] = "graph structure not needed at L7 (pointwise spinor extraction)"
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed / not needed"

try:
    import z3  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["reason"] = "not invoked: sympy CAS already closes the 2x2 identities exactly"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "not invoked: sympy closes the identities; z3 is the proof fallback"
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic 2x2 matrix algebra for projector idempotence/orthogonality/completeness"
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "Cl(3) rotor form deferred to L8 chiral density; not needed for extraction identities"
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = "S^3 manifold routines not required; Hopf sampling is a 4-tuple norm"
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
    TOOL_MANIFEST["e3nn"]["reason"] = "SO(3) irreps irrelevant at carrier-level L/R split"
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = "graph tools not required at L7"
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
    TOOL_MANIFEST["xgi"]["reason"] = "hypergraphs not required at L7"
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
    TOOL_MANIFEST["toponetx"]["reason"] = "cell complex gating is L6-side; L7 pointwise"
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = "persistent homology unused at L7"
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def _sympy_projectors():
    I2 = sp.eye(2)
    sz = sp.Matrix([[1, 0], [0, -1]])
    P_L = (I2 - sz) / 2
    P_R = (I2 + sz) / 2
    return I2, sz, P_L, P_R


def run_positive_tests():
    results = {}

    # ---- Symbolic (sympy load-bearing) ----------------------------
    assert sp is not None, "sympy required for L7 canonical proof"
    I2, sz, P_L, P_R = _sympy_projectors()

    idem_L = sp.simplify(P_L * P_L - P_L) == sp.zeros(2, 2)
    idem_R = sp.simplify(P_R * P_R - P_R) == sp.zeros(2, 2)
    ortho  = sp.simplify(P_L * P_R) == sp.zeros(2, 2)
    ortho_sym = sp.simplify(P_R * P_L) == sp.zeros(2, 2)
    complete = sp.simplify(P_L + P_R - I2) == sp.zeros(2, 2)

    results["sym_idempotent_L"] = {"pass": bool(idem_L)}
    results["sym_idempotent_R"] = {"pass": bool(idem_R)}
    results["sym_orthogonal_LR"] = {"pass": bool(ortho)}
    results["sym_orthogonal_RL"] = {"pass": bool(ortho_sym)}
    results["sym_completeness"] = {"pass": bool(complete)}
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

    # ---- Numeric family over Hopf-sampled psi ---------------------
    # Sample psi in C^2 on S^3 (unit norm) via 4 real gaussians normalized.
    rng = np.random.default_rng(20260414)
    N = 128
    sz_n = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    I2_n = np.eye(2, dtype=complex)
    P_L_n = 0.5 * (I2_n - sz_n)
    P_R_n = 0.5 * (I2_n + sz_n)

    norm_errs = []
    cross_errs = []
    for _ in range(N):
        r = rng.standard_normal(4)
        psi = np.array([r[0] + 1j * r[1], r[2] + 1j * r[3]])
        psi /= np.linalg.norm(psi)
        psiL = P_L_n @ psi
        psiR = P_R_n @ psi
        norm_errs.append(abs(np.vdot(psiL, psiL).real + np.vdot(psiR, psiR).real - 1.0))
        cross_errs.append(abs(np.vdot(psiL, psiR)))

    results["num_norm_conservation"] = {
        "pass": max(norm_errs) < 1e-12,
        "max_err": float(max(norm_errs)),
        "n_samples": N,
    }
    results["num_LR_inner_zero"] = {
        "pass": max(cross_errs) < 1e-12,
        "max_err": float(max(cross_errs)),
        "n_samples": N,
    }
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    assert sp is not None

    I2, sz, P_L, P_R = _sympy_projectors()
    sx = sp.Matrix([[0, 1], [1, 0]])
    # A "bad" split that looks like a projector but is orthogonal to sigma_z.
    P_bad = (I2 - sx) / 2

    # Neg 1: [P_bad, sigma_z] != 0 -> not a chirality-preserving split
    comm = sp.simplify(P_bad * sz - sz * P_bad)
    results["neg_bad_projector_nonchiral"] = {
        "pass": comm != sp.zeros(2, 2),  # we WANT it to be nonzero
        "commutator_nonzero": comm != sp.zeros(2, 2),
    }

    # Neg 2: duplicate-L completeness violation: P_L + P_L != I
    bad_complete = sp.simplify(P_L + P_L - I2)
    results["neg_duplicate_L_breaks_completeness"] = {
        "pass": bad_complete != sp.zeros(2, 2),
    }

    # Neg 3: P_L and P_bad not orthogonal (confirms P_bad is the wrong axis)
    bad_ortho = sp.simplify(P_L * P_bad)
    results["neg_bad_not_orthogonal_to_PL"] = {
        "pass": bad_ortho != sp.zeros(2, 2),
    }
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    sz_n = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    I2_n = np.eye(2, dtype=complex)
    P_L_n = 0.5 * (I2_n - sz_n)
    P_R_n = 0.5 * (I2_n + sz_n)

    # Chiral pole |0> = (1, 0): entirely R, zero L.
    psi0 = np.array([1.0 + 0j, 0.0 + 0j])
    psi0_L = P_L_n @ psi0
    psi0_R = P_R_n @ psi0
    results["boundary_pole_up"] = {
        "pass": np.linalg.norm(psi0_L) < 1e-15
                and abs(np.linalg.norm(psi0_R) - 1.0) < 1e-15,
        "L_norm": float(np.linalg.norm(psi0_L)),
        "R_norm": float(np.linalg.norm(psi0_R)),
    }

    # Chiral pole |1> = (0, 1): entirely L, zero R.
    psi1 = np.array([0.0 + 0j, 1.0 + 0j])
    psi1_L = P_L_n @ psi1
    psi1_R = P_R_n @ psi1
    results["boundary_pole_down"] = {
        "pass": np.linalg.norm(psi1_R) < 1e-15
                and abs(np.linalg.norm(psi1_L) - 1.0) < 1e-15,
        "L_norm": float(np.linalg.norm(psi1_L)),
        "R_norm": float(np.linalg.norm(psi1_R)),
    }

    # Equator: (|0>+|1>)/sqrt(2) -> equal split 1/2 each.
    psi_eq = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2)
    eL = np.vdot(P_L_n @ psi_eq, P_L_n @ psi_eq).real
    eR = np.vdot(P_R_n @ psi_eq, P_R_n @ psi_eq).real
    results["boundary_equator_equal_split"] = {
        "pass": abs(eL - 0.5) < 1e-15 and abs(eR - 0.5) < 1e-15,
        "L_weight": float(eL), "R_weight": float(eR),
    }
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = (
        all(v["pass"] for v in pos.values())
        and all(v["pass"] for v in neg.values())
        and all(v["pass"] for v in bnd.values())
    )

    results = {
        "name": "L7_weyl_extraction",
        "layer": 7,
        "classification": "canonical",
        "divergence_log": (
            "L7 carrier-level Weyl L/R projector identities proved symbolically "
            "via sympy (load-bearing) and cross-validated numerically over a "
            "128-sample S^3 family; negatives confirm non-sigma_z splits break "
            "chirality; boundaries confirm pole/equator structure."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "verdict": "PASS" if all_pass else "KILL",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "L7_weyl_extraction_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("=" * 72)
    print("LAYER 7: WEYL EXTRACTION SIM")
    print("=" * 72)
    for section, block in (("POSITIVE", pos), ("NEGATIVE", neg), ("BOUNDARY", bnd)):
        print(f"\n{section}:")
        for k, v in block.items():
            icon = "PASS" if v["pass"] else "KILL"
            print(f"  [{icon}] {k}")
    print("\n" + "=" * 72)
    print(f"  VERDICT: {'PASS' if all_pass else 'KILL'}")
    print(f"  Results: {out_path}")
    print("=" * 72)
