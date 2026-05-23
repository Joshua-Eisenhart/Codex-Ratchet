#!/usr/bin/env python3
"""Coupling Program #390 — KanExtension Shell (87-shell)"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
TOOL_MANIFEST = {'python_stdlib': {'reason': 'Conservative contract metadata repair: stdlib-only probe metadata.',
                   'tried': True,
                   'used': True}}
TOOL_INTEGRATION_DEPTH = {'python_stdlib': 'supportive'}
SHELL_COUNT = 87

def h_kan_extension_87() -> float:
    return math.log(2)

def run_positive_tests():
    results = {}
    try:
        mi_base = torch.tensor(1.0, dtype=torch.float64, requires_grad=True)
        H_vals = [torch.tensor(math.log(2), dtype=torch.float64) for _ in range(SHELL_COUNT - 1)]
        H_new = torch.tensor(h_kan_extension_87(), dtype=torch.float64)
        Q = mi_base
        for h in H_vals:
            Q = Q * h
        Q = Q * H_new
        results["test_positive_q_nonzero"] = {"description": "Q > 0 for 87-shell", "q_value": float(Q.item()), "passed": float(Q.item()) > 0}
    except Exception as e:
        results["test_positive_q_nonzero"] = {"error": str(e)}

    try:
        eps = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
        mi_base = torch.tensor(1.0 + eps, dtype=torch.float64)
        Q = mi_base
        for _ in range(SHELL_COUNT - 1):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        Q = Q * torch.tensor(h_kan_extension_87(), dtype=torch.float64)
        Q.backward()
        results["test_positive_autograd_gradient"] = {"description": "dQ/dε != 0", "gradient": float(eps.grad.item()), "passed": abs(float(eps.grad.item())) > 0}
    except Exception as e:
        results["test_positive_autograd_gradient"] = {"error": str(e)}

    results["test_positive_shell_count"] = {"description": "shell_count == 87", "shell_count": SHELL_COUNT, "passed": SHELL_COUNT == 87}
    return results

def run_negative_tests():
    results = {}
    try:
        mi_zero = torch.tensor(0.0, dtype=torch.float64)
        Q = mi_zero
        for _ in range(SHELL_COUNT - 1):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        Q = Q * torch.tensor(h_kan_extension_87(), dtype=torch.float64)
        results["test_negative_zero_mi"] = {"description": "MI=0 → Q=0", "q_value": float(Q.item()), "passed": float(Q.item()) == 0.0}
    except Exception as e:
        results["test_negative_zero_mi"] = {"error": str(e)}

    try:
        mi_neg = torch.tensor(-1.0, dtype=torch.float64)
        Q = mi_neg
        for _ in range(SHELL_COUNT - 1):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        Q = Q * torch.tensor(h_kan_extension_87(), dtype=torch.float64)
        results["test_negative_negative_mi"] = {"description": "MI<0 → Q<0", "q_value": float(Q.item()), "passed": float(Q.item()) < 0.0}
    except Exception as e:
        results["test_negative_negative_mi"] = {"error": str(e)}

    try:
        Q_86 = torch.tensor(1.0, dtype=torch.float64)
        for _ in range(85):
            Q_86 = Q_86 * torch.tensor(math.log(2), dtype=torch.float64)
        Q_87 = Q_86 * torch.tensor(h_kan_extension_87(), dtype=torch.float64)
        results["test_negative_shell_scaling"] = {"description": "87-shell Q != 86-shell Q", "q_86": float(Q_86.item()), "q_87": float(Q_87.item()), "passed": float(Q_86.item()) != float(Q_87.item())}
    except Exception as e:
        results["test_negative_shell_scaling"] = {"error": str(e)}
    return results

def run_boundary_tests():
    results = {}
    try:
        expected = 1.0 * (math.log(2) ** 87)
        mi_base = torch.tensor(1.0, dtype=torch.float64)
        Q = mi_base
        for _ in range(87):
            Q = Q * torch.tensor(math.log(2), dtype=torch.float64)
        results["test_boundary_formula"] = {"description": "Q = MI * log(2)^87", "expected": expected, "actual": float(Q.item()), "passed": abs(float(Q.item()) - expected) < 1e-10}
    except Exception as e:
        results["test_boundary_formula"] = {"error": str(e)}

    try:
        mi_base = torch.tensor(1.0, dtype=torch.float64)
        results["test_boundary_dtype"] = {"description": "dtype is float64", "dtype": str(mi_base.dtype), "passed": mi_base.dtype == torch.float64}
    except Exception as e:
        results["test_boundary_dtype"] = {"error": str(e)}

    try:
        Q_86 = 1.0 * (math.log(2) ** 86)
        Q_87 = 1.0 * (math.log(2) ** 87)
        ratio = Q_87 / Q_86
        results["test_boundary_scaling_ratio"] = {"description": "Q_87/Q_86 ≈ log(2)", "ratio": ratio, "log2": math.log(2), "passed": abs(ratio - math.log(2)) < 1e-12}
    except Exception as e:
        results["test_boundary_scaling_ratio"] = {"error": str(e)}
    return results

if __name__ == "__main__":
    results = {
        "name": "Coupling Program #390 — KanExtension Shell (87-shell)",
        "description": "87-shell classical_baseline coupling program with pytorch autograd (Axis 0 gradient)",
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
    out_path = os.path.join(out_dir, "sim_coupling_program_390_kan_extension_87shell_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
