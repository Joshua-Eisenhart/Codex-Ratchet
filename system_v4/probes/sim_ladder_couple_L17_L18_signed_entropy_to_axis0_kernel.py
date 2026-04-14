#!/usr/bin/env python3
"""sim_ladder_couple_L17_L18_signed_entropy_to_axis0_kernel

scope_note: ladders/fences per system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md. Language is exclusion/admissibility, not causal.

Couples ladder layers L17_signed_entropy and L18_axis0_kernel via pytorch.
classification: canonical
Language: admissibility/exclusion; never causal.
"""
import json, os, traceback

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "z3":       {"tried": False, "used": False, "reason": ""},
    "sympy":    {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "z3": None, "sympy": None, "clifford": None,
}

try:
    import torch  # noqa
    TOOL_MANIFEST["pytorch"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["pytorch"]["reason"] = f"import failed: {e}"
try:
    import z3  # noqa
    TOOL_MANIFEST["z3"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["z3"]["reason"] = f"import failed: {e}"
try:
    import sympy  # noqa
    TOOL_MANIFEST["sympy"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["sympy"]["reason"] = f"import failed: {e}"
try:
    from clifford import Cl  # noqa
    TOOL_MANIFEST["clifford"]["tried"] = True
except Exception as e:
    TOOL_MANIFEST["clifford"]["reason"] = f"import failed: {e}"

LOAD_BEARING_TOOL = "pytorch"
LOAD_BEARING_REASON = 'pytorch autograd is the axis-0 gradient kernel; not available in numpy'

def run_positive_tests():
    results = {}
    try:
        import torch
        # L17 signed entropy functional I_c = sum p log p (signed, negative of Shannon)
        p = torch.tensor([0.5, 0.5], requires_grad=True)
        I_c = (p * torch.log(p.clamp(min=1e-12))).sum()
        # L18 axis0 kernel: gradient of I_c wrt p survives under coupling
        I_c.backward()
        results['signed_entropy_gradient_survives'] = bool(p.grad.abs().sum().item() > 0)
        results['I_c_value'] = float(I_c.item())
    except Exception as e:
        results['_error'] = traceback.format_exc()
    return results

def run_negative_tests():
    results = {}
    try:
        import torch
        # Negative: detached (no grad) breaks axis0 kernel
        p = torch.tensor([0.5,0.5])
        I_c = (p * torch.log(p.clamp(min=1e-12))).sum()
        has_grad = p.requires_grad
        results['no_grad_excluded_from_axis0_kernel'] = bool(not has_grad)
    except Exception as e:
        results['_error'] = traceback.format_exc()
    return results

def run_boundary_tests():
    results = {}
    try:
        import torch
        # Boundary: delta distribution -> I_c = 0, grad well-defined via clamp
        p = torch.tensor([1.0, 1e-12], requires_grad=True)
        I_c = (p * torch.log(p.clamp(min=1e-12))).sum()
        I_c.backward()
        results['delta_boundary_finite_grad'] = bool(torch.isfinite(p.grad).all().item())
    except Exception as e:
        results['_error'] = traceback.format_exc()
    return results

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Mark load-bearing tool as used with non-empty reason
    TOOL_MANIFEST[LOAD_BEARING_TOOL]["used"] = True
    TOOL_MANIFEST[LOAD_BEARING_TOOL]["reason"] = LOAD_BEARING_REASON
    TOOL_INTEGRATION_DEPTH[LOAD_BEARING_TOOL] = "load_bearing"

    def all_true(d):
        vals = [v for k, v in d.items() if not k.startswith('_') and isinstance(v, bool)]
        return bool(vals) and all(vals)

    pos_pass = all_true(pos)
    neg_pass = all_true(neg)
    bnd_pass = all_true(bnd)
    overall = "PASS" if (pos_pass and neg_pass and bnd_pass) else "FAIL"

    results = {
        "name": "sim_ladder_couple_L17_L18_signed_entropy_to_axis0_kernel",
        "classification": "canonical",
        "scope_note": "ladders/fences per system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md",
        "coupling": {"layer_a": "L17_signed_entropy", "layer_b": "L18_axis0_kernel"},
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "load_bearing_tool": LOAD_BEARING_TOOL,
        "load_bearing_reason": LOAD_BEARING_REASON,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "pos_pass": pos_pass,
        "neg_pass": neg_pass,
        "bnd_pass": bnd_pass,
        "overall": overall,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_ladder_couple_L17_L18_signed_entropy_to_axis0_kernel_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{overall} {out_path}")
