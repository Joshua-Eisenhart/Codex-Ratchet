#!/usr/bin/env python3
"""sim_em_classical_fep_mirror_entropy_minimization
Scope: doctrine 'FEP as literal physics mirror' (user_causality_fep_doctrine.md +
user_entropic_monism_doctrine.md). Classical baseline: gradient descent on
variational free energy F = E - S shows entropy minimization of surprisal.
"""
import json, os, numpy as np
SCOPE_NOTE = "Doctrine 'FEP literal physics mirror'. Grad descent on F=E-S; convergence. user_entropic_monism_doctrine.md"
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing variational gradient descent"},
    "pytorch": {"tried": False, "used": False, "reason": "bridge 09 covers autograd"},
    "z3": {"tried": False, "used": False, "reason": "no SMT"},
    "sympy": {"tried": False, "used": False, "reason": "numeric"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def F(q, obs=np.array([0.2, 0.3, 0.5])):
    # q parametrized by softmax(theta); F = -sum q*log p + sum q*log q, p=obs
    qn = q / q.sum()
    return float(-(qn*np.log(obs + 1e-12)).sum() + (qn*np.log(qn + 1e-12)).sum())

def descend(steps=500, lr=0.05):
    q = np.array([1.0, 1.0, 1.0])
    Fs = [F(q)]
    for _ in range(steps):
        grad = np.zeros(3); eps = 1e-5
        for i in range(3):
            d = q.copy(); d[i] += eps
            grad[i] = (F(d) - F(q))/eps
        q = np.maximum(q - lr*grad, 1e-6)
        Fs.append(F(q))
    return np.array(Fs), q/q.sum()

def run_positive_tests():
    Fs, qhat = descend()
    obs = np.array([0.2, 0.3, 0.5])
    return {"F_nonincreasing": {"pass": bool((np.diff(Fs) <= 1e-6).all())},
            "q_matches_p": {"pass": bool(np.allclose(qhat, obs, atol=0.02)), "qhat": qhat.tolist()}}

def run_negative_tests():
    # wrong target: if we 'ascend' F, q moves away from obs
    q = np.array([0.2, 0.3, 0.5])
    F0 = F(q)
    q2 = np.array([1.0, 1.0, 1.0])/3
    return {"uniform_not_optimal": {"pass": bool(F(q2) > F0)}}

def run_boundary_tests():
    # single-step
    Fs, _ = descend(steps=1)
    return {"first_step_finite": {"pass": bool(np.isfinite(Fs).all())}}

if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {"name": "sim_em_classical_fep_mirror_entropy_minimization", "scope_note": SCOPE_NOTE,
               "classification": "classical_baseline", "tool_manifest": TOOL_MANIFEST,
               "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_em_classical_fep_mirror_entropy_minimization_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
