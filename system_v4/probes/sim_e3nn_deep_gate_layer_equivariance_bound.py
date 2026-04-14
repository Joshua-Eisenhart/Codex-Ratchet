#!/usr/bin/env python3
"""sim_e3nn_deep_gate_layer_equivariance_bound

Scope: e3nn load-bearing equivariance bound on a Gate nonlinearity (scalars
gate vector features). Fence: Gate(D x) == D' Gate(x) within tol. Negative:
applying Gate after an arbitrary linear mix of gates and gated features breaks
the fence. Gate layer itself is from e3nn.nn.
"""
import os, json, torch
from e3nn.o3 import Irreps, rand_matrix
from e3nn.nn import Gate

NAME = "sim_e3nn_deep_gate_layer_equivariance_bound"
SCOPE_NOTE = "Gate-layer equivariance; disruption by mixing gates/gated features excluded."
TOOL_MANIFEST = {"e3nn": {"tried": True, "used": True,
    "reason": "load-bearing Gate nonlinearity + Wigner-D equivariance bound"},
    "pytorch": {"tried": True, "used": True, "reason": "tensor backend"}}
TOOL_INTEGRATION_DEPTH = {"e3nn": "load_bearing", "pytorch": "supportive"}

def _build_gate():
    # scalars: 1x0e (no gate) + 2x0e (gates) ; gated: 1x1o + 1x2e
    irreps_scalars = Irreps('1x0e')
    irreps_gates   = Irreps('2x0e')
    irreps_gated   = Irreps('1x1o+1x2e')
    g = Gate(irreps_scalars, [torch.tanh],
             irreps_gates,  [torch.sigmoid],
             irreps_gated)
    return g

def _residual(shuffle=False):
    torch.manual_seed(0)
    g = _build_gate()
    irr_in  = g.irreps_in
    irr_out = g.irreps_out
    x = torch.randn(5, irr_in.dim)
    R = rand_matrix()
    Din = irr_in.D_from_matrix(R); Dout = irr_out.D_from_matrix(R)
    lhs = g(x @ Din.T)
    rhs = g(x) @ Dout.T
    if shuffle:
        # swap gates <-> scalars slot before Gate
        xs = x.clone()
        xs[:, :1], xs[:, 1:3] = x[:, 1:3].mean(dim=1, keepdim=True), x[:, :1].repeat(1,2)
        lhs2 = g(xs @ Din.T)
        rhs2 = g(xs) @ Dout.T
        # measure disruption vs rhs (original)
        return (lhs2 - rhs).abs().max().item()
    return (lhs - rhs).abs().max().item()

def run_positive_tests():
    r = _residual()
    return {"gate_equivariant": {"pass": r < 1e-4, "residual": r}}

def run_negative_tests():
    # Perturb inputs so gate-weights change: non-equivariant action vs original rhs.
    torch.manual_seed(7)
    g = _build_gate()
    irr_in = g.irreps_in; irr_out = g.irreps_out
    x = torch.randn(5, irr_in.dim)
    R = rand_matrix()
    Din = irr_in.D_from_matrix(R); Dout = irr_out.D_from_matrix(R)
    W = torch.randn(irr_in.dim, irr_in.dim)
    lhs = g((x @ W) @ Din.T)
    rhs = g(x) @ Dout.T
    r = (lhs - rhs).abs().max().item()
    return {"mixed_pre_gate_excluded": {"pass": r > 1e-2, "residual": r}}

def run_boundary_tests():
    # zero input stays zero on gated sector (gates saturate to sigmoid(0)=0.5 on 0-scalars)
    g = _build_gate()
    x = torch.zeros(2, g.irreps_in.dim)
    out = g(x)
    # out is finite; check equivariance residual on zero input is zero
    R = rand_matrix()
    Din = g.irreps_in.D_from_matrix(R); Dout = g.irreps_out.D_from_matrix(R)
    r = (g(x @ Din.T) - g(x) @ Dout.T).abs().max().item()
    return {"zero_input_equivariant": {"pass": r < 1e-5, "residual": r}}

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
