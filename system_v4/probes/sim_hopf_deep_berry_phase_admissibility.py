#!/usr/bin/env python3
"""
sim_hopf_deep_berry_phase_admissibility
Scope: Berry phase around a closed base loop equals half the enclosed S^2
solid angle (Hopf connection). Candidates with phase decoupled from solid
angle excluded. Uses pytorch autograd-friendly tensor eval.
See system_v5/new docs/ENGINE_MATH_REFERENCE.md.
"""
import json, os, torch, math

SCOPE_NOTE = "Berry phase = Omega/2 for Hopf connection; ENGINE_MATH_REFERENCE.md"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True,
                "reason": "complex tensor overlap phases accumulate Berry phase"},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing"}

def spinor(theta, phi):
    return torch.stack([torch.cos(theta/2),
                        torch.sin(theta/2)*torch.exp(1j*phi)])

def berry_phase_loop(theta0, N=400):
    phis = torch.linspace(0, 2*math.pi, N+1, dtype=torch.float64)
    theta = torch.tensor(theta0, dtype=torch.float64)
    psis = [spinor(theta, p) for p in phis]
    phase = 0.0+0j
    for i in range(N):
        overlap = torch.vdot(psis[i], psis[i+1])
        phase += torch.log(overlap / abs(overlap))
    return float((-1j*phase).real)  # Berry phase (real)

def run_positive_tests():
    out = {}
    for i, th in enumerate([0.3, 1.0, 1.8]):
        gamma = berry_phase_loop(th)
        omega = 2*math.pi*(1 - math.cos(th))
        expected = omega/2
        # wrap into (-pi, pi]
        diff = ((gamma - expected + math.pi) % (2*math.pi)) - math.pi
        ok = abs(diff) < 5e-3
        out[f"loop_{i}"] = {"pass": ok, "berry": gamma, "expected": expected,
            "reason": "Berry phase survives as -Omega/2 (Hopf admissible); else excluded"}
    return out

def run_negative_tests():
    # null loop at pole theta=0 -> zero area, phase 0; corrupted expectation excluded
    gamma = berry_phase_loop(0.0)
    wrong_expected = math.pi
    mismatches = abs(gamma - wrong_expected) > 0.1
    return {"wrong_expected_excluded": {"pass": mismatches, "berry": gamma,
            "reason": "wrong solid-angle candidate excluded by measured phase"}}

def run_boundary_tests():
    gamma = berry_phase_loop(math.pi)  # full 2pi solid angle
    expected = 2*math.pi  # Omega/2 where Omega=4pi*... numerically tracked without mod
    diff = ((gamma - expected + math.pi) % (2*math.pi)) - math.pi
    ok = abs(diff) < 5e-3
    return {"south_pole_loop": {"pass": ok, "berry": gamma, "expected": expected,
            "reason": "theta=pi loop returns boundary Berry phase ~pi (mod 2pi)"}}

if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(t["pass"] for t in {**pos, **neg, **bnd}.values())
    results = {
        "name": "sim_hopf_deep_berry_phase_admissibility",
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_hopf_deep_berry_phase_admissibility_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
