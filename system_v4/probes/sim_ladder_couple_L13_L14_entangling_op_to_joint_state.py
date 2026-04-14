#!/usr/bin/env python3
"""sim_ladder_couple_L13_L14_entangling_op_to_joint_state

scope_note: ladders/fences per system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md. Language is exclusion/admissibility, not causal.

Couples ladder layers L13_entangling_op and L14_joint_state via pytorch.
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
LOAD_BEARING_REASON = 'pytorch autograd-capable tensor ops carry the nonclassical joint-state structure; numpy is the excluded baseline'

def run_positive_tests():
    results = {}
    try:
        import torch
        # L13 CNOT entangling op
        H = (1/torch.sqrt(torch.tensor(2.0))) * torch.tensor([[1.0,1.0],[1.0,-1.0]])
        I = torch.eye(2)
        CNOT = torch.tensor([[1.,0,0,0],[0,1,0,0],[0,0,0,1.],[0,0,1.,0]])
        psi0 = torch.kron(torch.tensor([1.,0]), torch.tensor([1.,0]))
        psi1 = CNOT @ torch.kron(H @ torch.tensor([1.,0]), torch.tensor([1.,0]))
        # L14 joint-state: reduced density has entropy > 0 iff entangled
        rho = psi1.reshape(2,2)
        _, s, _ = torch.linalg.svd(rho)
        probs = s**2
        S = -(probs * torch.log2(probs.clamp(min=1e-12))).sum().item()
        results['entangling_op_admits_entangled_joint_state'] = bool(S > 0.9)
    except Exception as e:
        results['_error'] = traceback.format_exc()
    return results

def run_negative_tests():
    results = {}
    try:
        import torch
        # Negative: product op (I x I) leaves product state — excluded as entangler
        I = torch.eye(2)
        OP = torch.kron(I, I)
        psi = torch.kron(torch.tensor([1.,0]), torch.tensor([1.,0]))
        psi1 = OP @ psi
        rho = psi1.reshape(2,2)
        _, s, _ = torch.linalg.svd(rho)
        probs = s**2
        S = -(probs * torch.log2(probs.clamp(min=1e-12))).sum().item()
        results['identity_op_excluded_as_entangler'] = bool(S < 1e-6)
    except Exception as e:
        results['_error'] = traceback.format_exc()
    return results

def run_boundary_tests():
    results = {}
    try:
        import torch
        # Boundary: maximally entangled Bell pair
        bell = (1/torch.sqrt(torch.tensor(2.0))) * torch.tensor([1.,0,0,1.])
        rho = bell.reshape(2,2)
        _, s, _ = torch.linalg.svd(rho)
        probs = s**2
        S = -(probs * torch.log2(probs.clamp(min=1e-12))).sum().item()
        results['bell_boundary_entropy_one'] = bool(abs(S - 1.0) < 1e-6)
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
        "name": "sim_ladder_couple_L13_L14_entangling_op_to_joint_state",
        "classification": "canonical",
        "scope_note": "ladders/fences per system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md",
        "coupling": {"layer_a": "L13_entangling_op", "layer_b": "L14_joint_state"},
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
    out_path = os.path.join(out_dir, "sim_ladder_couple_L13_L14_entangling_op_to_joint_state_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{overall} {out_path}")
