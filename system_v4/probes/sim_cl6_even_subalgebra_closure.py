#!/usr/bin/env python3
"""sim_cl6_even_subalgebra_closure -- Cl(6) even subalgebra closed under product.

Even elements (grades 0,2,4,6) form a subalgebra; product of two evens is even
(chirality-preserving). Positive: 100 random even pairs stay even. Negative:
odd*even is odd (leaves subalgebra). Boundary: scalar and pseudoscalar edges.
Ablation: numpy flat vector multiply has no grade structure -- can't detect
chirality preservation.
"""
import json, os, numpy as np

TOOL_MANIFEST = {k:{"tried":False,"used":False,"reason":""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from clifford import Cl
TOOL_MANIFEST["clifford"] = {"tried":True,"used":True,"reason":"Cl(6) geometric product and grade projection are the object under test"}
TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

layout, blades = Cl(6)

def random_even(rng):
    mv = layout.scalar * 0
    for g in (0,2,4,6):
        gb = layout.grade_mask(g)
        coeffs = rng.normal(size=layout.gaDims)
        mv = mv + layout.MultiVector(value=coeffs*gb)
    return mv

def random_odd(rng):
    mv = layout.scalar * 0
    for g in (1,3,5):
        gb = layout.grade_mask(g)
        coeffs = rng.normal(size=layout.gaDims)
        mv = mv + layout.MultiVector(value=coeffs*gb)
    return mv

def is_even(mv, tol=1e-10):
    for g in (1,3,5):
        if np.linalg.norm(mv(g).value) > tol:
            return False
    return True

def is_odd(mv, tol=1e-10):
    for g in (0,2,4,6):
        if np.linalg.norm(mv(g).value) > tol:
            return False
    return True

def run_positive_tests():
    rng = np.random.default_rng(42)
    n = 100; fails = 0; max_odd_leak = 0.0
    for _ in range(n):
        A = random_even(rng); B = random_even(rng)
        C = A*B
        leak = sum(np.linalg.norm(C(g).value) for g in (1,3,5))
        max_odd_leak = max(max_odd_leak, leak)
        if not is_even(C): fails += 1
    return {"n_pairs": n, "failures": fails, "max_odd_grade_leak": float(max_odd_leak),
            "pass": fails==0 and max_odd_leak < 1e-9}

def run_negative_tests():
    rng = np.random.default_rng(7)
    n = 30; odd_eve_stays_odd = 0
    for _ in range(n):
        A = random_odd(rng); B = random_even(rng)
        C = A*B
        if is_odd(C): odd_eve_stays_odd += 1
    return {"n": n, "odd_times_even_is_odd": odd_eve_stays_odd,
            "pass": odd_eve_stays_odd == n}

def run_boundary_tests():
    # scalar * pseudoscalar stays even (both grade 0 and 6)
    s = 3.0 + 0*blades['e1']
    ps = layout.pseudoScalar
    prod = s * ps
    # identity * even = even
    I = 1.0 + 0*blades['e1']
    rng = np.random.default_rng(1)
    E = random_even(rng)
    return {"scalar_times_pseudoscalar_even": is_even(prod),
            "identity_times_even_is_even": is_even(I*E),
            "pseudoscalar_squared_even": is_even(ps*ps),
            "pass": is_even(prod) and is_even(I*E) and is_even(ps*ps)}

def run_ablation():
    # numpy-only: using outer product of coefficient vectors (no Cayley table)
    # cannot tell you the grade of the result. We feed a mixed A (even) and
    # B (even) and check whether a naive outer-product-sum into a 64-dim result
    # (without the clifford multiplication table) preserves even-grade structure.
    rng = np.random.default_rng(11)
    A = random_even(rng); B = random_even(rng)
    C_correct = A*B
    correct_odd_leak = sum(np.linalg.norm(C_correct(g).value) for g in (1,3,5))
    # Naive: sum of outer products with index-addition mod dim -- random-ish
    # target indices, which will land in odd grades with high probability.
    naive = np.zeros(layout.gaDims)
    N = layout.gaDims
    for i in range(N):
        for j in range(N):
            # index-sum modulo dim is a structurally wrong "product"
            k = (i + j) % N
            naive[k] += A.value[i] * B.value[j]
    naive_mv = layout.MultiVector(value=naive)
    naive_odd_leak = sum(np.linalg.norm(naive_mv(g).value) for g in (1,3,5))
    return {"numpy_indexsum_odd_leak": float(naive_odd_leak),
            "clifford_geoprod_odd_leak": float(correct_odd_leak),
            "ablation_shows_numpy_insufficient": bool(naive_odd_leak > 1e-6 and correct_odd_leak < 1e-9)}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ab = run_ablation()
    results = {
        "name": "sim_cl6_even_subalgebra_closure",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "ablation": ab,
        "classification": "canonical",
        "overall_pass": pos["pass"] and neg["pass"] and bnd["pass"] and ab["ablation_shows_numpy_insufficient"],
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cl6_even_subalgebra_closure_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
