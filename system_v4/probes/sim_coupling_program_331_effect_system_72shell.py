#!/usr/bin/env python3
"""Coupling Program #331 — EffectSystem Shell (72-shell)

Classical baseline: pytorch autograd computes dQ/dε where Q = MI * log(2)^72.
"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
SHELL_COUNT = 72

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load_bearing: autograd computes dQ/dε for Q = MI * log(2)^72"},
    "pyg": {"tried": False, "used": False, "reason": "PyG message passing not needed; scalar Q formula sufficient"},
    "z3": {"tried": False, "used": False, "reason": "z3 SMT not needed; pytorch autograd handles gradient computation"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 SMT not needed; classical baseline uses pytorch only"},
    "sympy": {"tried": False, "used": False, "reason": "sympy not needed; Q formula is direct numerical computation"},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; scalar coupling formula"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; no differential geometry in coupling scaffold"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no SO(3) equivariance in coupling scaffold"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; no graph structure in coupling scaffold"},
    "xgi": {"tried": False, "used": False, "reason": "xgi not needed; no hypergraph structure in coupling scaffold"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx not needed; no topological network in coupling scaffold"},
    "gudhi": {"tried": False, "used": False, "reason": "gudhi not needed; no persistent homology in coupling scaffold"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

def run_positive_tests():
    results = {}
    # Test 1: gradient nonzero
    try:
        eps = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
        MI = torch.tensor(0.5, dtype=torch.float64)
        Q = (MI + eps)
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        Q.backward()
        results["test_positive_gradient_nonzero"] = {
            "description": "dQ/dε ≠ 0 for 72-shell Q",
            "gradient": float(eps.grad),
            "passed": float(eps.grad) != 0.0,
        }
    except Exception as e:
        results["test_positive_gradient_nonzero"] = {"error": str(e)}

    # Test 2: shell count correct
    try:
        results["test_positive_shell_count"] = {
            "description": "SHELL_COUNT == 72",
            "shell_count": SHELL_COUNT,
            "passed": SHELL_COUNT == 72,
        }
    except Exception as e:
        results["test_positive_shell_count"] = {"error": str(e)}

    # Test 3: Q positive for positive MI
    try:
        eps = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
        MI = torch.tensor(1.0, dtype=torch.float64)
        Q = (MI + eps)
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        results["test_positive_Q_positive"] = {
            "description": "Q > 0 for MI = 1.0",
            "Q_value": float(Q.detach()),
            "passed": float(Q.detach()) > 0.0,
        }
    except Exception as e:
        results["test_positive_Q_positive"] = {"error": str(e)}

    return results

def run_negative_tests():
    results = {}
    # Test 1: MI=0 → Q=0
    try:
        eps = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
        MI = torch.tensor(0.0, dtype=torch.float64)
        Q = (MI + eps)
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        results["test_negative_MI_zero"] = {
            "description": "MI=0 → Q=0",
            "Q_value": float(Q.detach()),
            "passed": abs(float(Q.detach())) < 1e-10,
        }
    except Exception as e:
        results["test_negative_MI_zero"] = {"error": str(e)}

    # Test 2: 72-shell Q ≠ 71-shell Q
    try:
        MI = torch.tensor(1.0, dtype=torch.float64)
        Q_72 = MI.clone()
        for _ in range(72):
            Q_72 = Q_72 * torch.tensor(math.log(2), dtype=torch.float64)
        Q_71 = MI.clone()
        for _ in range(71):
            Q_71 = Q_71 * torch.tensor(math.log(2), dtype=torch.float64)
        results["test_negative_shell_count_differs"] = {
            "description": "Q_72 ≠ Q_71",
            "Q_72": float(Q_72),
            "Q_71": float(Q_71),
            "passed": float(Q_72) != float(Q_71),
        }
    except Exception as e:
        results["test_negative_shell_count_differs"] = {"error": str(e)}

    # Test 3: negative MI → negative Q
    try:
        MI = torch.tensor(-1.0, dtype=torch.float64)
        Q = MI.clone()
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        results["test_negative_MI_negative"] = {
            "description": "MI<0 → Q<0",
            "Q_value": float(Q),
            "passed": float(Q) < 0.0,
        }
    except Exception as e:
        results["test_negative_MI_negative"] = {"error": str(e)}

    return results

def run_boundary_tests():
    results = {}
    # Test 1: Q formula matches MI * log(2)^72
    try:
        MI_val = 1.0
        expected = MI_val * (math.log(2) ** SHELL_COUNT)
        MI = torch.tensor(MI_val, dtype=torch.float64)
        Q = MI.clone()
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        results["test_boundary_formula_correct"] = {
            "description": "Q == MI * log(2)^72",
            "computed": float(Q),
            "expected": expected,
            "passed": abs(float(Q) - expected) < 1e-10,
        }
    except Exception as e:
        results["test_boundary_formula_correct"] = {"error": str(e)}

    # Test 2: scaling ratio Q_72/Q_71 ≈ log(2)
    try:
        MI = torch.tensor(1.0, dtype=torch.float64)
        Q_72 = MI.clone()
        for _ in range(72):
            Q_72 = Q_72 * torch.tensor(math.log(2), dtype=torch.float64)
        Q_71 = MI.clone()
        for _ in range(71):
            Q_71 = Q_71 * torch.tensor(math.log(2), dtype=torch.float64)
        ratio = float(Q_72) / float(Q_71)
        results["test_boundary_scaling_ratio"] = {
            "description": "Q_72/Q_71 ≈ log(2)",
            "ratio": ratio,
            "log2": math.log(2),
            "passed": abs(ratio - math.log(2)) < 1e-10,
        }
    except Exception as e:
        results["test_boundary_scaling_ratio"] = {"error": str(e)}

    # Test 3: dtype float64 preserved
    try:
        eps = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
        MI = torch.tensor(0.5, dtype=torch.float64)
        Q = (MI + eps)
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        results["test_boundary_dtype_float64"] = {
            "description": "Q dtype is float64",
            "dtype": str(Q.dtype),
            "passed": Q.dtype == torch.float64,
        }
    except Exception as e:
        results["test_boundary_dtype_float64"] = {"error": str(e)}

    return results


if __name__ == "__main__":
    results = {
        "name": "Coupling Program #331 — EffectSystem Shell (72-shell)",
        "description": "Classical baseline coupling program: Q = MI * log(2)^72 with pytorch autograd",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
        "shells": SHELL_COUNT,
        "Q_formula": f"MI * log(2)^{SHELL_COUNT}",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_coupling_program_331_effect_system_72shell_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
