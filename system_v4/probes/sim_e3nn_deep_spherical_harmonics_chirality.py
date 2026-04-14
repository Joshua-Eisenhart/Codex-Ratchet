#!/usr/bin/env python3
"""sim_e3nn_deep_spherical_harmonics_chirality

Scope: e3nn load-bearing chirality/parity fence on spherical harmonics. Odd-l
harmonics (Y^1) must flip sign under inversion r -> -r; even-l (Y^0, Y^2) must
not. Exclusion: treating Y^1 as even parity is excluded by the residual.
"""
import os, json, torch
from e3nn.o3 import Irreps, spherical_harmonics

NAME = "sim_e3nn_deep_spherical_harmonics_chirality"
SCOPE_NOTE = "Y^l parity: odd-l flip under inversion; even-l invariant; chirality fence."
TOOL_MANIFEST = {"e3nn": {"tried": True, "used": True,
    "reason": "load-bearing spherical_harmonics evaluation for parity fence"},
    "pytorch": {"tried": True, "used": True, "reason": "tensor backend"}}
TOOL_INTEGRATION_DEPTH = {"e3nn": "load_bearing", "pytorch": "supportive"}

def _sh(irr, r):
    return spherical_harmonics(Irreps(irr), r, normalize=True, normalization="component")

def run_positive_tests():
    torch.manual_seed(0)
    r = torch.randn(16, 3)
    y1_plus  = _sh('1x1o', r)
    y1_minus = _sh('1x1o', -r)
    flip = (y1_plus + y1_minus).abs().max().item()
    return {"y1o_flips_under_inversion": {"pass": flip < 1e-5, "residual": flip}}

def run_negative_tests():
    torch.manual_seed(0)
    r = torch.randn(16, 3)
    y2_plus  = _sh('1x2e', r)
    y2_minus = _sh('1x2e', -r)
    # even-l invariant: difference (not sum) must be small
    diff = (y2_plus - y2_minus).abs().max().item()
    # Exclusion: if we mistakenly summed (treat as odd), residual would be large
    mistaken = (y2_plus + y2_minus).abs().max().item()
    return {"y2e_invariant_under_inversion":
            {"pass": diff < 1e-5 and mistaken > 1e-3,
             "invariant_diff": diff, "mistaken_sum": mistaken}}

def run_boundary_tests():
    # scalar (l=0) is invariant
    r = torch.randn(4, 3)
    y0p = _sh('1x0e', r); y0m = _sh('1x0e', -r)
    return {"y0e_invariant": {"pass": (y0p - y0m).abs().max().item() < 1e-6}}

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
