#!/usr/bin/env python3
"""sim_e3nn_deep_so3_irrep_decomposition_admissibility

Scope: e3nn load-bearing SO(3) irrep decomposition admissibility: a candidate
feature vector x on Irreps('1x0e+1x1o+1x2e') must transform by D(R)x under a
random rotation R. Pass = equivariance residual below tol. Exclusion: feeding a
non-equivariant map (random matrix) breaks the fence.
"""
import os, json, torch
from e3nn.o3 import Irreps, rand_matrix

NAME = "sim_e3nn_deep_so3_irrep_decomposition_admissibility"
SCOPE_NOTE = "SO(3) irrep decomposition admissibility under D(R); non-equivariant map excluded."
TOOL_MANIFEST = {"e3nn": {"tried": True, "used": True,
    "reason": "load-bearing SO(3) Wigner-D representation on Irreps decomposition"},
    "pytorch": {"tried": True, "used": True, "reason": "tensor backend for e3nn"}}
TOOL_INTEGRATION_DEPTH = {"e3nn": "load_bearing", "pytorch": "supportive"}

IRR = Irreps('1x0e+1x1o+1x2e')

def _equiv_residual(map_fn):
    torch.manual_seed(0)
    x = torch.randn(4, IRR.dim)
    R = rand_matrix()
    D = IRR.D_from_matrix(R)
    lhs = map_fn(x @ D.T)
    rhs = map_fn(x) @ D.T
    return (lhs - rhs).abs().max().item()

def run_positive_tests():
    # identity is equivariant
    r = _equiv_residual(lambda x: x)
    return {"identity_equivariant": {"pass": r < 1e-5, "residual": r}}

def run_negative_tests():
    torch.manual_seed(1)
    W = torch.randn(IRR.dim, IRR.dim)  # generic, non-equivariant
    r = _equiv_residual(lambda x: x @ W)
    return {"generic_map_nonequivariant": {"pass": r > 1e-2, "residual": r}}

def run_boundary_tests():
    # scaling is equivariant (commutes with D)
    r = _equiv_residual(lambda x: 2.5 * x)
    return {"scalar_scale_equivariant": {"pass": r < 1e-5, "residual": r}}

if __name__ == "__main__":
    results = {"name": NAME, "scope_note": SCOPE_NOTE, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(), "negative": run_negative_tests(),
        "boundary": run_boundary_tests()}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"Results written to {out}")
