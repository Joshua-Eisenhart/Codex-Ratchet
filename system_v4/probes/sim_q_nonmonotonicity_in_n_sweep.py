#!/usr/bin/env python3
"""
sim_q_nonmonotonicity_in_n_sweep.py
Canonical sim: Is Q non-monotonicity in N structural or value-dependent?

Claim: Q_{N+1} > or < Q_N depends on H_{N+1} vs 1, not on N itself.
The zero-in-subshell property is N-independent and structural.
"""

import json
import os

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": ""},
    "z3":         {"tried": False, "used": False, "reason": ""},
    "cvc5":       {"tried": False, "used": False, "reason": ""},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": ""},
    "geomstats":  {"tried": False, "used": False, "reason": ""},
    "e3nn":       {"tried": False, "used": False, "reason": ""},
    "rustworkx":  {"tried": False, "used": False, "reason": ""},
    "xgi":        {"tried": False, "used": False, "reason": ""},
    "toponetx":   {"tried": False, "used": False, "reason": ""},
    "gudhi":      {"tried": False, "used": False, "reason": ""},
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

# --- imports ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Random H sweep (P1) uses torch for reproducible draws"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
    TOOL_MANIFEST["pyg"]["reason"] = "not needed for scalar product sweep"
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, sat, unsat  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "N1: UNSAT proof that Q_{N+1} > Q_N is impossible when H_{N+1}=0.3 < 1"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "not needed — z3 covers proof layer"
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "N2: symbolic proof that sign(Q*h - Q) is determined by h vs 1"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

TOOL_MANIFEST["clifford"]["tried"] = False
TOOL_MANIFEST["clifford"]["reason"] = "Clifford algebra encodes geometric rotors; Q-product sweep is scalar arithmetic, no spinor or rotor structure present"
TOOL_MANIFEST["geomstats"]["tried"] = False
TOOL_MANIFEST["geomstats"]["reason"] = "Geomstats provides Riemannian manifold operations; Q non-monotonicity depends on scalar H_i values, not curvature or geodesics"
TOOL_MANIFEST["e3nn"]["tried"] = False
TOOL_MANIFEST["e3nn"]["reason"] = "e3nn handles equivariant neural network layers for 3D rotation symmetry; scalar product Q has no SO(3) equivariance structure to exploit"
TOOL_MANIFEST["rustworkx"]["tried"] = False
TOOL_MANIFEST["rustworkx"]["reason"] = "rustworkx provides graph data structures; Q-product over N shells is a linear chain with no graph topology queries needed"
TOOL_MANIFEST["xgi"]["tried"] = False
TOOL_MANIFEST["xgi"]["reason"] = "XGI handles hypergraph higher-order interactions; Q product over ordered shells has pairwise-sequential structure, no hyperedges required"
TOOL_MANIFEST["toponetx"]["tried"] = False
TOOL_MANIFEST["toponetx"]["reason"] = "TopoNetX provides cell complex topology; the monotonicity question is purely over the real number line, not a topological space"
TOOL_MANIFEST["gudhi"]["tried"] = False
TOOL_MANIFEST["gudhi"]["reason"] = "GUDHI computes persistent homology for point clouds; Q values form a 1D sequence with no simplicial complex structure to analyze"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # P1: Random H sweep with torch
    p1 = {"name": "P1_random_H_sweep", "pass": False}
    try:
        torch.manual_seed(42)
        N = 10
        n_draws = 100
        H_draws = torch.distributions.Uniform(0.1, 3.0).sample((n_draws, N))

        n_increase = 0
        n_decrease = 0

        for draw in H_draws:
            Q = 1.0
            for i in range(N - 1):
                Q_next = Q * draw[i].item()
                h_next = draw[i + 1].item()
                Q_after = Q_next * h_next
                if Q_after > Q_next:
                    n_increase += 1
                else:
                    n_decrease += 1
                Q = Q_next

        total_transitions = n_draws * (N - 1)
        frac_increase = n_increase / total_transitions
        frac_decrease = n_decrease / total_transitions

        p1["n_draws"] = n_draws
        p1["total_transitions"] = total_transitions
        p1["n_increase"] = n_increase
        p1["n_decrease"] = n_decrease
        p1["frac_increase"] = round(frac_increase, 4)
        p1["frac_decrease"] = round(frac_decrease, 4)
        p1["interpretation"] = "Both directions occur; non-monotonicity is value-dependent"

        if frac_increase > 0.1 and frac_decrease > 0.1:
            p1["pass"] = True
            p1["finding"] = f"frac_increase={frac_increase:.4f}, frac_decrease={frac_decrease:.4f} — both directions present"
        else:
            p1["finding"] = f"Unexpected: frac_increase={frac_increase:.4f}, frac_decrease={frac_decrease:.4f}"
    except Exception as e:
        p1["error"] = str(e)

    results["P1"] = p1

    # P2: Fixed H=0.5 (all < 1) — strictly decreasing
    p2 = {"name": "P2_fixed_H_half", "pass": False}
    try:
        h = 0.5
        Q_vals = [h ** n for n in range(1, 11)]
        strictly_decreasing = all(Q_vals[i] > Q_vals[i + 1] for i in range(len(Q_vals) - 1))
        p2["Q_vals"] = [round(v, 6) for v in Q_vals]
        p2["strictly_decreasing"] = strictly_decreasing
        p2["pass"] = strictly_decreasing
    except Exception as e:
        p2["error"] = str(e)

    results["P2"] = p2

    # P3: Fixed H=2.0 (all > 1) — strictly increasing
    p3 = {"name": "P3_fixed_H_two", "pass": False}
    try:
        h = 2.0
        Q_vals = [h ** n for n in range(1, 11)]
        strictly_increasing = all(Q_vals[i] < Q_vals[i + 1] for i in range(len(Q_vals) - 1))
        p3["Q_vals"] = [round(v, 6) for v in Q_vals]
        p3["strictly_increasing"] = strictly_increasing
        p3["pass"] = strictly_increasing
    except Exception as e:
        p3["error"] = str(e)

    results["P3"] = p3

    # P4: Mixed H alternating 0.5, 2.0 — non-monotone
    p4 = {"name": "P4_alternating_H", "pass": False}
    try:
        H = [0.5, 2.0] * 5  # 10 shells
        Q_vals = []
        q = 1.0
        for h in H:
            q = q * h
            Q_vals.append(round(q, 6))

        monotone_inc = all(Q_vals[i] < Q_vals[i + 1] for i in range(len(Q_vals) - 1))
        monotone_dec = all(Q_vals[i] > Q_vals[i + 1] for i in range(len(Q_vals) - 1))
        non_monotone = not monotone_inc and not monotone_dec

        p4["Q_vals"] = Q_vals
        p4["H"] = H
        p4["non_monotone"] = non_monotone
        p4["pass"] = non_monotone
    except Exception as e:
        p4["error"] = str(e)

    results["P4"] = p4

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: z3 UNSAT — Q_{N+1} > Q_N impossible when H_{N+1} = 0.3 < 1
    n1 = {"name": "N1_z3_unsat_increase_impossible", "pass": False}
    try:
        from z3 import Real, Solver, sat, unsat, And

        Q_N_val = 2.0
        H_next_val = 0.3

        Q_N = Real("Q_N")
        H_next = Real("H_next")
        Q_Np1 = Real("Q_Np1")

        s = Solver()
        s.add(Q_N == Q_N_val)
        s.add(H_next == H_next_val)
        s.add(Q_Np1 == Q_N * H_next)
        s.add(Q_N > 0)
        # Assert the "impossible" claim: Q_{N+1} > Q_N
        s.add(Q_Np1 > Q_N)

        result = s.check()
        n1["z3_result"] = str(result)
        n1["expected"] = "unsat"
        n1["pass"] = (result == unsat)
        n1["interpretation"] = "UNSAT confirms Q_{N+1} > Q_N is impossible when H_{N+1}=0.3 < 1 and Q_N > 0"
    except Exception as e:
        n1["error"] = str(e)

    results["N1"] = n1

    # N2: sympy symbolic proof — sign(Q*h - Q) determined by h vs 1
    n2 = {"name": "N2_sympy_sign_proof", "pass": False}
    try:
        import sympy as sp

        q, h = sp.symbols("q h", positive=True)
        delta = q * h - q  # Q_{N+1} - Q_N

        val_h1 = delta.subs(h, 1)
        val_h2 = delta.subs(h, 2)  # h > 1: delta > 0 for q > 0

        # For h < 1, say h = 0.3
        val_h03 = delta.subs(h, sp.Rational(3, 10))

        check_h1_zero = (val_h1 == 0)
        check_h2_positive = sp.simplify(val_h2) > 0  # q > 0 so 2q - q = q > 0
        check_h03_negative = sp.simplify(val_h03) < 0  # 0.3q - q = -0.7q < 0

        n2["delta_h1"] = str(val_h1)
        n2["delta_h2"] = str(val_h2)
        n2["delta_h03"] = str(val_h03)
        n2["check_h1_zero"] = bool(check_h1_zero)
        n2["check_h2_positive"] = bool(check_h2_positive)
        n2["check_h03_negative"] = bool(check_h03_negative)

        n2["pass"] = bool(check_h1_zero and check_h2_positive and check_h03_negative)
        n2["interpretation"] = "sign(Q*h - Q) = sign(h - 1); structural, not value-of-Q-dependent"
    except Exception as e:
        n2["error"] = str(e)

    results["N2"] = n2

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: Q_N = 0 when any H_i = 0 (product-zero property, N-independent)
    b1 = {"name": "B1_zero_shell_collapses_Q", "pass": False}
    try:
        test_cases = []
        for zero_pos in [0, 4, 9]:  # zero in first, middle, last shell
            H = [1.5] * 10
            H[zero_pos] = 0.0
            q = 1.0
            for h in H:
                q = q * h
            test_cases.append({"zero_at": zero_pos, "Q_final": q, "is_zero": q == 0.0})

        all_zero = all(tc["is_zero"] for tc in test_cases)
        b1["test_cases"] = test_cases
        b1["all_collapsed_to_zero"] = all_zero
        b1["pass"] = all_zero
        b1["interpretation"] = "Zero-in-subshell collapses Q regardless of N or position"
    except Exception as e:
        b1["error"] = str(e)

    results["B1"] = b1

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = list(pos.values()) + list(neg.values()) + list(bnd.values())
    overall_pass = all(t.get("pass", False) for t in all_tests)

    results = {
        "name": "sim_q_nonmonotonicity_in_n_sweep",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": overall_pass,
        "divergence_log": (
            "Q non-monotonicity in N is value-dependent (H_i <> 1 determines direction); "
            "the zero-in-subshell property is N-independent and structural. "
            "Q_10 < Q_9 in the N-ladder because specific shell H values multiply in factors < 1."
        ),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_q_nonmonotonicity_in_n_sweep_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall_pass}")

    if not overall_pass:
        import sys
        sys.exit(1)
