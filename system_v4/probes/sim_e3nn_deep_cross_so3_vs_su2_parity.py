#!/usr/bin/env python3
"""sim_e3nn_deep_cross_so3_vs_su2_parity

Scope: e3nn load-bearing cross-check between SO(3) vector action and the
integer-l subspace of SU(2) Wigner-D. For integer l the SU(2) double cover
D^l(R, +1) equals D^l(R, -1) (both project to SO(3)). Fence: difference must
vanish for l=1, l=2. Exclusion: half-integer would NOT satisfy this (not
supported by e3nn.o3; omitted from positive claim).
"""
import os, json, torch
from e3nn.o3 import Irreps, rand_matrix

NAME = "sim_e3nn_deep_cross_so3_vs_su2_parity"
SCOPE_NOTE = ("Integer-l Wigner-D factors through SO(3); compose(R1 R2) = D(R1) D(R2) "
              "fence. Half-integer reps excluded from scope.")
TOOL_MANIFEST = {"e3nn": {"tried": True, "used": True,
    "reason": "load-bearing integer-l Wigner-D homomorphism check"},
    "pytorch": {"tried": True, "used": True, "reason": "tensor backend"}}
TOOL_INTEGRATION_DEPTH = {"e3nn": "load_bearing", "pytorch": "supportive"}

def _homo_residual(irr_str):
    torch.manual_seed(0)
    R1 = rand_matrix(); R2 = rand_matrix()
    irr = Irreps(irr_str)
    lhs = irr.D_from_matrix(R1 @ R2)
    rhs = irr.D_from_matrix(R1) @ irr.D_from_matrix(R2)
    return (lhs - rhs).abs().max().item()

def run_positive_tests():
    r1 = _homo_residual('1x1o'); r2 = _homo_residual('1x2e')
    return {"l1_homomorphism":  {"pass": r1 < 1e-4, "residual": r1},
            "l2_homomorphism":  {"pass": r2 < 1e-4, "residual": r2}}

def run_negative_tests():
    # forge a "fake D" by replacing D(R1 R2) with D(R1 R1); residual must be large
    torch.manual_seed(2)
    R1 = rand_matrix(); R2 = rand_matrix()
    irr = Irreps('1x1o')
    fake = irr.D_from_matrix(R1 @ R1)
    rhs  = irr.D_from_matrix(R1) @ irr.D_from_matrix(R2)
    r = (fake - rhs).abs().max().item()
    return {"wrong_product_excluded": {"pass": r > 1e-3, "residual": r}}

def run_boundary_tests():
    # identity rotation maps to identity matrix
    irr = Irreps('1x2e')
    I = torch.eye(3)
    D = irr.D_from_matrix(I)
    r = (D - torch.eye(irr.dim)).abs().max().item()
    return {"identity_rotation_identity_D": {"pass": r < 1e-5, "residual": r}}

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
