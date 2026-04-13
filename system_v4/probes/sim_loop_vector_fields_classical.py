#!/usr/bin/env python3
"""Classical baseline: loop_vector_fields.
Curl/divergence of 2D vector fields on closed loops (circle). Tests:
- Stokes: line integral of F around loop = integral of curl over enclosed area
- Divergence-free rotational field has zero line integral of dot-normal (flux)
- Curl of gradient = 0"""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"
NAME = "loop_vector_fields"

def loop(R=1.0, n=2000):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    x = R * np.cos(t); y = R * np.sin(t)
    dx = -R * np.sin(t) * (2*np.pi/n); dy = R * np.cos(t) * (2*np.pi/n)
    return x, y, dx, dy

def line_integral(Fx, Fy, x, y, dx, dy):
    return np.sum(Fx(x, y) * dx + Fy(x, y) * dy)

def flux_integral(Fx, Fy, R=1.0, n=2000):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    x = R * np.cos(t); y = R * np.sin(t)
    nx = np.cos(t); ny = np.sin(t)
    ds = (2 * np.pi * R / n)
    return np.sum((Fx(x, y) * nx + Fy(x, y) * ny) * ds)

def run_positive_tests():
    r = {}
    # F = (-y, x): constant curl = 2, line integral = 2 * area
    Fx = lambda x, y: -y; Fy = lambda x, y: x
    for R in (1.0, 2.0, 0.5):
        x, y, dx, dy = loop(R=R, n=4000)
        li = line_integral(Fx, Fy, x, y, dx, dy)
        expected = 2 * np.pi * R**2  # curl*area
        r[f"stokes_rot_R{R}"] = bool(abs(li - expected) < 1e-3)
    # F = grad(x^2+y^2) = (2x, 2y): curl = 0, line integral over closed loop = 0
    Fx = lambda x, y: 2*x; Fy = lambda x, y: 2*y
    x, y, dx, dy = loop()
    r["curl_grad_zero"] = bool(abs(line_integral(Fx, Fy, x, y, dx, dy)) < 1e-6)
    # divergence-free rotational: outward flux = 0
    Fx = lambda x, y: -y; Fy = lambda x, y: x
    r["rot_flux_zero"] = bool(abs(flux_integral(Fx, Fy)) < 1e-6)
    # radial field F=(x,y): div=2, flux=2*area
    Fx = lambda x, y: x; Fy = lambda x, y: y
    r["radial_flux"] = bool(abs(flux_integral(Fx, Fy) - 2 * np.pi) < 1e-3)
    return r

def run_negative_tests():
    r = {}
    # non-conservative field has nonzero closed line integral
    Fx = lambda x, y: -y; Fy = lambda x, y: x
    x, y, dx, dy = loop()
    r["nonconservative_nonzero"] = bool(abs(line_integral(Fx, Fy, x, y, dx, dy)) > 1.0)
    # radial field has nonzero flux
    Fx = lambda x, y: x; Fy = lambda x, y: y
    r["radial_nonzero_flux"] = bool(abs(flux_integral(Fx, Fy)) > 1.0)
    return r

def run_boundary_tests():
    r = {}
    # tiny loop -> tiny line integral
    Fx = lambda x, y: -y; Fy = lambda x, y: x
    x, y, dx, dy = loop(R=1e-3, n=1000)
    li = line_integral(Fx, Fy, x, y, dx, dy)
    r["tiny_loop_small"] = bool(abs(li) < 1e-4)
    # zero field
    Fx = lambda x, y: 0*x; Fy = lambda x, y: 0*y
    x, y, dx, dy = loop()
    r["zero_field_zero_integral"] = bool(abs(line_integral(Fx, Fy, x, y, dx, dy)) < 1e-12)
    return r

if __name__ == "__main__":
    results = {"name": NAME, "classification": "classical_baseline",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(),
               "boundary": run_boundary_tests(),
               "classical_captured": "Stokes theorem, curl/div identities on closed 2D loops",
               "innately_missing": "nonclassical holonomy / Berry phase on constraint manifold loops"}
    results["all_pass"] = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", f"{NAME}_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={results['all_pass']} -> {out}")
