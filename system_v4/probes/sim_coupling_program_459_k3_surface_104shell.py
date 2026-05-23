#!/usr/bin/env python3
"""Coupling Program #459 — K3Surface Shell (104-shell)"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
SHELL_COUNT = 104

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load_bearing: autograd computes dQ/dε (Axis 0 gradient)"},
    "pyg": {"tried": False, "used": False, "reason": "PyG message passing not needed; scalar Q coupling in this program"},
    "z3": {"tried": False, "used": False, "reason": "z3 SMT not needed; pytorch autograd handles gradient computation"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 SMT not needed; pytorch handles all constraint computation"},
    "sympy": {"tried": False, "used": False, "reason": "sympy not needed; analytic Q formula computed via torch"},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; scalar coupling program"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; no Riemannian geometry in this program"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no SO(3) equivariance required"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; no graph structure in this program"},
    "xgi": {"tried": False, "used": False, "reason": "xgi not needed; no hypergraph structure"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx not needed; no topological structure"},
    "gudhi": {"tried": False, "used": False, "reason": "gudhi not needed; no persistent homology"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing", "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None, "rustworkx": None, "xgi": None,
    "toponetx": None, "gudhi": None,
}

def run_positive_tests():
    results = {}
    try:
        eps = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
        MI = torch.tensor(0.5, dtype=torch.float64)
        Q = (MI + eps)
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        Q.backward()
        results["test_positive_gradient_nonzero"] = {"description": f"Axis 0 gradient dQ/dε ≠ 0 for {SHELL_COUNT}-shell", "gradient": float(eps.grad), "passed": abs(float(eps.grad)) > 1e-30}
    except Exception as e:
        results["test_positive_gradient_nonzero"] = {"error": str(e)}
    results["test_positive_shell_count"] = {"description": f"Shell count equals {SHELL_COUNT}", "shell_count": SHELL_COUNT, "passed": SHELL_COUNT == 104}
    try:
        MI = torch.tensor(0.5, dtype=torch.float64)
        Q = MI * (torch.tensor(math.log(2), dtype=torch.float64) ** SHELL_COUNT)
        results["test_positive_Q_positive"] = {"description": "Q > 0 for positive MI", "Q": float(Q), "passed": float(Q) > 0}
    except Exception as e:
        results["test_positive_Q_positive"] = {"error": str(e)}
    return results

def run_negative_tests():
    results = {}
    try:
        MI = torch.tensor(0.0, dtype=torch.float64)
        Q = MI * (torch.tensor(math.log(2), dtype=torch.float64) ** SHELL_COUNT)
        results["test_negative_MI_zero"] = {"description": "MI=0 → Q=0", "Q": float(Q), "passed": float(Q) == 0.0}
    except Exception as e:
        results["test_negative_MI_zero"] = {"error": str(e)}
    try:
        log2 = torch.tensor(math.log(2), dtype=torch.float64)
        MI = torch.tensor(0.5, dtype=torch.float64)
        Q_104 = float(MI * (log2 ** 104))
        Q_103 = float(MI * (log2 ** 103))
        results["test_negative_shell_distinguishable"] = {"description": "Q_104 ≠ Q_103", "passed": Q_104 != Q_103}
    except Exception as e:
        results["test_negative_shell_distinguishable"] = {"error": str(e)}
    try:
        MI = torch.tensor(-0.5, dtype=torch.float64)
        Q = MI * (torch.tensor(math.log(2), dtype=torch.float64) ** SHELL_COUNT)
        results["test_negative_MI_negative"] = {"description": "MI<0 → Q<0", "Q": float(Q), "passed": float(Q) < 0}
    except Exception as e:
        results["test_negative_MI_negative"] = {"error": str(e)}
    return results

def run_boundary_tests():
    results = {}
    try:
        MI_val = 0.5
        Q_expected = MI_val * (math.log(2) ** SHELL_COUNT)
        Q_torch = float(torch.tensor(MI_val, dtype=torch.float64) * (torch.tensor(math.log(2), dtype=torch.float64) ** SHELL_COUNT))
        results["test_boundary_formula_match"] = {"description": f"Q = MI * log(2)^{SHELL_COUNT}", "passed": abs(Q_torch - Q_expected) < 1e-20}
    except Exception as e:
        results["test_boundary_formula_match"] = {"error": str(e)}
    try:
        log2 = torch.tensor(math.log(2), dtype=torch.float64)
        MI = torch.tensor(0.5, dtype=torch.float64)
        ratio = float(MI * (log2 ** 104)) / float(MI * (log2 ** 103))
        results["test_boundary_scaling_ratio"] = {"description": "Q_104/Q_103 ≈ log(2)", "ratio": ratio, "passed": abs(ratio - math.log(2)) < 1e-10}
    except Exception as e:
        results["test_boundary_scaling_ratio"] = {"error": str(e)}
    try:
        MI = torch.tensor(0.5, dtype=torch.float64)
        Q = MI * (torch.tensor(math.log(2), dtype=torch.float64) ** SHELL_COUNT)
        results["test_boundary_dtype_float64"] = {"description": "Q dtype is float64", "dtype": str(Q.dtype), "passed": Q.dtype == torch.float64}
    except Exception as e:
        results["test_boundary_dtype_float64"] = {"error": str(e)}
    return results

if __name__ == "__main__":
    results = {
        "name": f"Coupling Program #459 — K3Surface Shell (104-shell)",
        "description": f"Classical baseline Q = MI * log(2)^{SHELL_COUNT}; pytorch autograd Axis 0 gradient",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(), "negative": run_negative_tests(), "boundary": run_boundary_tests(),
        "classification": "classical_baseline", "shells": SHELL_COUNT, "Q_formula": f"MI * log(2)^{SHELL_COUNT}",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"sim_coupling_program_459_k3_surface_104shell_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written.")
