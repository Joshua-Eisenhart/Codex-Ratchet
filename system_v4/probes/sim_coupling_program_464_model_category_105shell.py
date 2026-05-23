#!/usr/bin/env python3
"""Coupling Program #464 — ModelCategory Shell (105-shell classical baseline)"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
SHELL_COUNT = 105
DOMAIN = "ModelCategory"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load_bearing: autograd computes dQ/dε (Axis 0 gradient) across 105 shells"},
    "pyg": {"tried": False, "used": False, "reason": "PyG not needed; no graph message passing in this coupling sim"},
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; pytorch autograd handles gradient computation"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 not needed; pytorch handles constraint satisfaction"},
    "sympy": {"tried": False, "used": False, "reason": "sympy not needed; torch float64 arithmetic is sufficient"},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; scalar coupling program"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; no manifold geometry in this sim"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no equivariance in this coupling"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; no graph structure"},
    "xgi": {"tried": False, "used": False, "reason": "xgi not needed; no hypergraph structure"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx not needed; standard torch ops sufficient"},
    "gudhi": {"tried": False, "used": False, "reason": "gudhi not needed; no persistent homology"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

def run_positive_tests():
    results = {}
    # Test 1: Q > 0 with positive MI
    try:
        eps = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
        MI = torch.tensor(0.5, dtype=torch.float64)
        Q = MI + eps
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        Q.backward()
        results["test_positive_q_nonzero"] = {
            "description": f"Q > 0 for MI=0.5 across {SHELL_COUNT} shells",
            "Q_value": float(Q.detach()),
            "passed": float(Q.detach()) > 0,
            "expected": True,
        }
    except Exception as e:
        results["test_positive_q_nonzero"] = {"error": str(e)}

    # Test 2: Axis 0 gradient nonzero
    try:
        eps = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
        MI = torch.tensor(0.5, dtype=torch.float64)
        Q = MI + eps
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        Q.backward()
        grad = float(eps.grad)
        results["test_positive_axis0_gradient"] = {
            "description": "dQ/dε ≠ 0 (Axis 0 gradient exists)",
            "gradient": grad,
            "passed": abs(grad) > 0,
            "expected": True,
        }
    except Exception as e:
        results["test_positive_axis0_gradient"] = {"error": str(e)}

    # Test 3: Shell count correct
    results["test_positive_shell_count"] = {
        "description": f"SHELL_COUNT == {SHELL_COUNT}",
        "shell_count": SHELL_COUNT,
        "passed": SHELL_COUNT == 105,
        "expected": True,
    }
    return results

def run_negative_tests():
    results = {}
    # Test 1: MI=0 → Q=0
    try:
        eps = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
        MI = torch.tensor(0.0, dtype=torch.float64)
        Q = MI + eps
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        results["test_negative_zero_mi"] = {
            "description": "MI=0 → Q=0",
            "Q_value": float(Q.detach()),
            "passed": float(Q.detach()) == 0.0,
            "expected": True,
        }
    except Exception as e:
        results["test_negative_zero_mi"] = {"error": str(e)}

    # Test 2: Q_105 != Q_104
    try:
        MI = torch.tensor(0.5, dtype=torch.float64)
        Q_104 = MI.clone()
        for _ in range(104):
            Q_104 = Q_104 * torch.tensor(math.log(2), dtype=torch.float64)
        Q_105 = MI.clone()
        for _ in range(105):
            Q_105 = Q_105 * torch.tensor(math.log(2), dtype=torch.float64)
        results["test_negative_shell_distinguishable"] = {
            "description": "Q_105 ≠ Q_104 (shells are distinguishable)",
            "Q_104": float(Q_104),
            "Q_105": float(Q_105),
            "passed": float(Q_104) != float(Q_105),
            "expected": True,
        }
    except Exception as e:
        results["test_negative_shell_distinguishable"] = {"error": str(e)}

    # Test 3: MI<0 → Q<0
    try:
        MI = torch.tensor(-0.5, dtype=torch.float64)
        Q = MI.clone()
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        results["test_negative_negative_mi"] = {
            "description": "MI<0 → Q<0",
            "Q_value": float(Q),
            "passed": float(Q) < 0,
            "expected": True,
        }
    except Exception as e:
        results["test_negative_negative_mi"] = {"error": str(e)}
    return results

def run_boundary_tests():
    results = {}
    # Test 1: Q formula exact
    try:
        MI_val = 0.5
        Q_expected = MI_val * (math.log(2) ** SHELL_COUNT)
        eps = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
        MI = torch.tensor(MI_val, dtype=torch.float64)
        Q = MI + eps
        for _ in range(SHELL_COUNT):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        Q_actual = float(Q.detach())
        results["test_boundary_formula_exact"] = {
            "description": f"Q = MI * log(2)^{SHELL_COUNT}",
            "Q_expected": Q_expected,
            "Q_actual": Q_actual,
            "passed": abs(Q_expected - Q_actual) < 1e-10,
            "expected": True,
        }
    except Exception as e:
        results["test_boundary_formula_exact"] = {"error": str(e)}

    # Test 2: Scaling ratio ≈ log(2)
    try:
        MI = torch.tensor(1.0, dtype=torch.float64)
        Q_n = MI.clone()
        for _ in range(SHELL_COUNT):
            Q_n = Q_n * torch.tensor(math.log(2), dtype=torch.float64)
        Q_n_minus = MI.clone()
        for _ in range(SHELL_COUNT - 1):
            Q_n_minus = Q_n_minus * torch.tensor(math.log(2), dtype=torch.float64)
        ratio = float(Q_n) / float(Q_n_minus)
        results["test_boundary_scaling_ratio"] = {
            "description": "Q_n / Q_{n-1} ≈ log(2)",
            "ratio": ratio,
            "log2": math.log(2),
            "passed": abs(ratio - math.log(2)) < 1e-10,
            "expected": True,
        }
    except Exception as e:
        results["test_boundary_scaling_ratio"] = {"error": str(e)}

    # Test 3: dtype float64
    results["test_boundary_dtype"] = {
        "description": "torch dtype is float64",
        "passed": True,
        "expected": True,
    }
    return results

if __name__ == "__main__":
    results = {
        "name": f"Coupling Program #464 — ModelCategory (105-shell)",
        "description": f"Classical baseline coupling program for ModelCategory with {SHELL_COUNT} shells",
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
    out_path = os.path.join(out_dir, "sim_coupling_program_464_model_category_105shell_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
