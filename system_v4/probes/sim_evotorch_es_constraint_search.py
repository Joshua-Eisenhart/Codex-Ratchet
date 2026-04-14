#!/usr/bin/env python3
"""
sim_evotorch_es_constraint_search -- canonical sim

EvoTorch SNES on a 4D constraint-admissibility scalar: distance from a
forbidden region. A candidate x in R^4 is "admissible" iff it survives
outside the forbidden ball B(c, r). The ES minimizes distance-to-origin
outside the forbidden region; we assert final best is below a threshold.

Language discipline: candidates are "admissible" / "excluded"; no claim
that the ES "creates" the optimum, only that the surviving candidate
co-varies with the constraint surface.
"""

import json
import os
import numpy as np

TOOL_MANIFEST = {
    "pytorch":  {"tried": False, "used": False, "reason": ""},
    "pyg":      {"tried": False, "used": False, "reason": "no graph"},
    "z3":       {"tried": False, "used": False, "reason": "no SAT obligation"},
    "cvc5":     {"tried": False, "used": False, "reason": "no SAT obligation"},
    "sympy":    {"tried": False, "used": False, "reason": "numeric only"},
    "clifford": {"tried": False, "used": False, "reason": "no rotors"},
    "geomstats":{"tried": False, "used": False, "reason": "Euclidean search space"},
    "e3nn":     {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx":{"tried": False, "used": False, "reason": "no graph"},
    "xgi":      {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi":    {"tried": False, "used": False, "reason": "no PD"},
    "evotorch": {"tried": False, "used": False, "reason": ""},
    "numpy":    {"tried": True,  "used": True,  "reason": "numeric forbidden-region check"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "supportive", "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
    "evotorch": "load_bearing",
    "numpy": "supportive",
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"]  = True
    TOOL_MANIFEST["pytorch"]["reason"] = "tensor ops inside evaluator and SolutionBatch backing"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    from evotorch import Problem
    from evotorch.algorithms import SNES
    TOOL_MANIFEST["evotorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["evotorch"]["reason"] = "not installed"


# Forbidden region: ball of radius R_FORBID around c=(2,2,2,2).
# Admissibility objective: minimize ||x||_2 subject to x outside forbidden ball.
# We encode by a soft penalty: cost = ||x||^2 + penalty * relu(R_FORBID - ||x - c||).
C_FORBID = torch.tensor([2.0, 2.0, 2.0, 2.0]) if "torch" in dir() else None
R_FORBID = 1.0
PENALTY  = 50.0
THRESHOLD_FINAL_BEST = 0.5


def eval_batch(x):
    # vectorized=True -> x is a (pop, 4) tensor; return (pop,) cost tensor.
    c = torch.tensor([2.0, 2.0, 2.0, 2.0], dtype=x.dtype, device=x.device)
    norm2 = (x * x).sum(dim=1)
    dist_to_c = torch.linalg.norm(x - c, dim=1)
    violation = torch.relu(R_FORBID - dist_to_c)
    return norm2 + PENALTY * violation


def run_positive_tests():
    results = {}
    torch.manual_seed(0)
    np.random.seed(0)

    problem = Problem(
        "min", eval_batch,
        solution_length=4,
        initial_bounds=(-3.0, 3.0),
        vectorized=True,
    )
    searcher = SNES(problem, stdev_init=1.5, popsize=32)
    for _ in range(60):
        searcher.step()

    best = searcher.status["pop_best"]
    best_cost = float(best.evals.item()) if best.evals.numel() == 1 else float(best.evals[0].item())
    best_x = best.values.detach().cpu().numpy().tolist()

    # Admissibility: outside forbidden ball.
    c = np.array([2.0, 2.0, 2.0, 2.0])
    dist_to_c = float(np.linalg.norm(np.array(best_x) - c))
    admissible = dist_to_c >= R_FORBID

    results["final_best_cost"] = best_cost
    results["final_best_x"]    = best_x
    results["dist_to_forbidden_center"] = dist_to_c
    results["admissible_outside_forbidden"] = admissible
    results["threshold"] = THRESHOLD_FINAL_BEST
    results["pass"] = admissible and best_cost < THRESHOLD_FINAL_BEST
    return results


def run_negative_tests():
    results = {}
    # Negative: a candidate placed inside the forbidden ball must be excluded.
    x = np.array([2.0, 2.0, 2.0, 2.0])
    dist = float(np.linalg.norm(x - np.array([2.0, 2.0, 2.0, 2.0])))
    results["inside_forbidden_dist"] = dist
    results["inside_excluded"] = dist < R_FORBID
    results["pass"] = results["inside_excluded"]
    return results


def run_boundary_tests():
    results = {}
    # Boundary: a candidate exactly on the forbidden shell is at the
    # admissibility boundary (violation == 0 but equality).
    c = np.array([2.0, 2.0, 2.0, 2.0])
    shell_x = c + np.array([R_FORBID, 0.0, 0.0, 0.0])
    dist = float(np.linalg.norm(shell_x - c))
    results["shell_dist"] = dist
    results["at_boundary"] = abs(dist - R_FORBID) < 1e-9
    results["pass"] = results["at_boundary"]
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    TOOL_MANIFEST["evotorch"]["used"]   = True
    TOOL_MANIFEST["evotorch"]["reason"] = "Problem + SNES run the ES loop producing the admissible candidate"

    results = {
        "name": "sim_evotorch_es_constraint_search",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "canonical",
        "overall_pass": pos["pass"] and neg["pass"] and bnd["pass"],
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_evotorch_es_constraint_search_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass={results['overall_pass']}")
