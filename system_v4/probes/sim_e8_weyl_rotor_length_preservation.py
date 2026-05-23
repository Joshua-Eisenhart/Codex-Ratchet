#!/usr/bin/env python3
"""
sim_e8_weyl_rotor_length_preservation.py

Tests whether Weyl rotor (SO(8) orthogonal) action on E8 roots preserves
the length²=2 constraint — G-tower × Weyl geometry coupling probe.

classification: classical_baseline
"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import os

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
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": "load_bearing",
    "rustworkx": None,
    "sympy": "load_bearing",
    "toponetx": None,
    "xgi": None,
    "z3": "load_bearing",
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, Not, And, sat, unsat  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# HELPERS
# =====================================================================

def get_e8_roots_sample(n=20, seed=42):
    """
    Return n E8 roots of type ±e_i ± e_j (i≠j) in R^8.
    All have length² = 2.
    """
    import itertools
    roots = []
    signs = [1, -1]
    for i, j in itertools.combinations(range(8), 2):
        for si in signs:
            for sj in signs:
                r = [0.0] * 8
                r[i] = float(si)
                r[j] = float(sj)
                roots.append(r)
    # There are 112 such roots; sample n of them deterministically
    torch.manual_seed(seed)
    idx = torch.randperm(len(roots))[:n]
    selected = [roots[i] for i in idx.tolist()]
    return torch.tensor(selected, dtype=torch.float64)  # (n, 8)


def random_so8_matrix(seed=0):
    """
    Generate a random SO(8) matrix via matrix exponential of skew-symmetric A.
    """
    torch.manual_seed(seed)
    A = torch.randn(8, 8, dtype=torch.float64)
    A_skew = (A - A.T) / 2.0
    R = torch.linalg.matrix_exp(A_skew)
    return R


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: SO(8) rotation preserves length² = 2 for E8 roots ---
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "torch.linalg.matrix_exp used to generate SO(8) rotations; "
        "torch tensor operations verify length² preservation for E8 roots"
    )

    roots = get_e8_roots_sample(20)
    lengths_sq_before = (roots * roots).sum(dim=1)  # should all be 2.0

    # Use 5 different random SO(8) matrices
    p1_pass = True
    p1_details = []
    for seed in range(5):
        R = random_so8_matrix(seed=seed)
        rotated = roots @ R.T  # (20, 8)
        lengths_sq_after = (rotated * rotated).sum(dim=1)
        max_err = (lengths_sq_after - 2.0).abs().max().item()
        ok = max_err < 1e-6
        p1_details.append({"seed": seed, "max_err": max_err, "pass": ok})
        if not ok:
            p1_pass = False

    results["P1_so8_length_preservation"] = {
        "description": "SO(8) rotation preserves length²=2 for 20 E8 roots",
        "pass": p1_pass,
        "details": p1_details,
    }

    # --- P2: Inner product preservation under SO(8) ---
    root_a = roots[0:1]   # (1, 8)
    root_b = roots[1:2]   # (1, 8)
    ip_before = (root_a * root_b).sum().item()

    p2_pass = True
    p2_details = []
    for seed in range(5):
        R = random_so8_matrix(seed=seed)
        ra = root_a @ R.T
        rb = root_b @ R.T
        ip_after = (ra * rb).sum().item()
        err = abs(ip_after - ip_before)
        ok = err < 1e-6
        p2_details.append({"seed": seed, "ip_before": ip_before, "ip_after": ip_after, "err": err, "pass": ok})
        if not ok:
            p2_pass = False

    results["P2_inner_product_preservation"] = {
        "description": "Inner product ⟨Rr₁,Rr₂⟩ = ⟨r₁,r₂⟩ for SO(8) rotation",
        "pass": p2_pass,
        "details": p2_details,
    }

    # --- P3: z3 tautology: orthogonal R + length²=2 => rotated length²=2 ---
    # We encode symbolically for a 2D slice (tractable for z3).
    # r=(a,b), R orthogonal 2x2: R^T R = I means R = [[c,-s],[s,c]] with c²+s²=1.
    # |r|²=a²+b²=2, |Rr|² = (ca+sb)²+(-sa+cb)² = a²+b² = 2 (always).
    # UNSAT on negation: NOT(|Rr|²=2) given constraints.
    from z3 import Real, Solver, Not, And

    a, b = Real("a"), Real("b")
    c, s = Real("c"), Real("s")

    r_len_sq = a * a + b * b
    ortho_constraint = c * c + s * s == 1
    len_constraint = r_len_sq == 2

    # Rotated components
    r1 = c * a + s * b
    r2 = -s * a + c * b
    rot_len_sq = r1 * r1 + r2 * r2

    # Claim: rotated length² != 2 (negation of what we want to prove)
    negation = Not(rot_len_sq == 2)

    solver = Solver()
    solver.add(ortho_constraint)
    solver.add(len_constraint)
    solver.add(negation)
    result_p3 = solver.check()

    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "z3 UNSAT check: negation of 'orthogonal R preserves length²=2' "
        "is unsatisfiable — proves tautology structurally"
    )

    p3_pass = (result_p3 == unsat)
    results["P3_z3_orthogonal_tautology"] = {
        "description": "z3 UNSAT on: ¬(|Rr|²=2) given ortho R + |r|²=2 — confirms tautology",
        "z3_result": str(result_p3),
        "pass": p3_pass,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: Non-orthogonal scaling R=2I does NOT preserve length² ---
    # z3 UNSAT: claim that 2r has length²=2 when r has length²=2
    from z3 import Real, Solver, And

    a, b = Real("a"), Real("b")
    len_constraint = a * a + b * b == 2

    # R = 2I: rotated = (2a, 2b), length² = 4a²+4b² = 4*2 = 8
    scaled_len_sq = (2 * a) * (2 * a) + (2 * b) * (2 * b)
    claim_preserved = scaled_len_sq == 2

    solver = Solver()
    solver.add(len_constraint)
    solver.add(claim_preserved)
    result_n1 = solver.check()

    # We expect UNSAT: scaling by 2 cannot preserve length²=2
    n1_pass = (result_n1 == unsat)
    results["N1_z3_scaling_breaks_length"] = {
        "description": "z3 UNSAT: R=2I with |r|²=2 cannot give |Rr|²=2 — non-orthogonal breaks constraint",
        "z3_result": str(result_n1),
        "pass": n1_pass,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: Identity rotation leaves all 20 roots unchanged ---
    roots = get_e8_roots_sample(20)
    R_id = torch.eye(8, dtype=torch.float64)
    rotated = roots @ R_id.T
    max_err = (rotated - roots).abs().max().item()
    b1_pass = max_err < 1e-12

    results["B1_identity_rotation"] = {
        "description": "Identity SO(8) matrix leaves all 20 E8 roots unchanged",
        "max_deviation": max_err,
        "pass": b1_pass,
    }

    # --- B2: sympy symbolic confirmation ---
    if sp is not None:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "sympy symbolic algebra confirms |Rr|² = r^T R^T R r = r^T r = 2 "
            "for any orthogonal R and vector with |r|²=2"
        )

        # Symbolic 2D case: r=(a,b), R orthogonal
        a_s, b_s, c_s, s_s = sp.symbols("a b c s", real=True)

        r_vec = sp.Matrix([a_s, b_s])
        R_mat = sp.Matrix([[c_s, -s_s], [s_s, c_s]])

        # Orthogonality assumption: c²+s²=1
        ortho_sub = {c_s**2 + s_s**2: sp.Integer(1)}

        Rr = R_mat * r_vec
        len_sq_Rr = (Rr.T * Rr)[0]
        len_sq_Rr_expanded = sp.expand(len_sq_Rr)

        # Simplify using c²+s²=1
        len_sq_simplified = sp.simplify(
            len_sq_Rr_expanded.subs(c_s**2, 1 - s_s**2)
        )

        # Also apply |r|²=2 assumption
        len_sq_final = sp.simplify(
            len_sq_simplified.subs(a_s**2 + b_s**2, 2)
        )

        b2_pass = (len_sq_final == sp.Integer(2))

        results["B2_sympy_symbolic"] = {
            "description": "sympy confirms |Rr|² = r^T R^T R r = |r|² = 2 for orthogonal R",
            "expression": str(len_sq_final),
            "pass": b2_pass,
        }
    else:
        results["B2_sympy_symbolic"] = {
            "description": "sympy not available",
            "pass": False,
            "note": "sympy not installed",
        }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_tests = list(positive.values()) + list(negative.values()) + list(boundary.values())
    all_pass = all(t.get("pass", False) for t in all_tests)

    results = {
        "name": "sim_e8_weyl_rotor_length_preservation",
        "classification": "classical_baseline",
        "claim": "SO(8)/Weyl rotor action on E8 roots preserves the length²=2 constraint",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
    }

    out_dir = os.path.join(
        os.path.dirname(__file__), "a2_state", "sim_results"
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_e8_weyl_rotor_length_preservation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass = {all_pass}")
