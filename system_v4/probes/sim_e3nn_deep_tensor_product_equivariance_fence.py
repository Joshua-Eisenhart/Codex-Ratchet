#!/usr/bin/env python3
"""sim_e3nn_deep_tensor_product_equivariance_fence

Scope: e3nn load-bearing equivariance fence on FullyConnectedTensorProduct
between 1x1o x 1x1o -> (1x0e+1x1e+1x2e). Pass: TP(Dx, Dy) == D_out TP(x,y).
Negative: a shuffled-output linear perturbation breaks the fence.
"""
import os, json, torch
from e3nn.o3 import Irreps, FullyConnectedTensorProduct, rand_matrix

NAME = "sim_e3nn_deep_tensor_product_equivariance_fence"
SCOPE_NOTE = "TP equivariance on 1o x 1o -> 0e+1e+2e; shuffled perturbation excluded."
TOOL_MANIFEST = {"e3nn": {"tried": True, "used": True,
    "reason": "load-bearing FullyConnectedTensorProduct equivariance check"},
    "pytorch": {"tried": True, "used": True, "reason": "tensor backend"}}
TOOL_INTEGRATION_DEPTH = {"e3nn": "load_bearing", "pytorch": "supportive"}

IRR_IN = Irreps('1x1o')
IRR_OUT = Irreps('1x0e+1x1e+1x2e')

def _residual(perturb=False):
    torch.manual_seed(0)
    tp = FullyConnectedTensorProduct(IRR_IN, IRR_IN, IRR_OUT)
    x = torch.randn(3, IRR_IN.dim)
    y = torch.randn(3, IRR_IN.dim)
    R = rand_matrix()
    Din = IRR_IN.D_from_matrix(R); Dout = IRR_OUT.D_from_matrix(R)
    lhs = tp(x @ Din.T, y @ Din.T)
    rhs = tp(x, y) @ Dout.T
    if perturb:
        # non-equivariant perturbation: permute output columns
        idx = torch.randperm(IRR_OUT.dim)
        lhs = lhs[:, idx]
    return (lhs - rhs).abs().max().item()

def run_positive_tests():
    r = _residual()
    return {"tp_equivariant": {"pass": r < 1e-4, "residual": r}}

def run_negative_tests():
    r = _residual(perturb=True)
    return {"tp_shuffled_excluded": {"pass": r > 1e-3, "residual": r}}

def run_boundary_tests():
    # zero inputs: residual must be zero
    tp = FullyConnectedTensorProduct(IRR_IN, IRR_IN, IRR_OUT)
    x = torch.zeros(1, IRR_IN.dim); y = torch.zeros(1, IRR_IN.dim)
    out = tp(x,y).abs().max().item()
    return {"zero_input_zero_output": {"pass": out < 1e-7, "out": out}}

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
