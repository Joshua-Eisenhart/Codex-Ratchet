#!/usr/bin/env python3
"""sim_cl3_rotor_product -- Product of rotors in Cl(3,0) is a rotor; R~R = 1."""
import json, os, numpy as np

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "algebraic identity; no autograd"},
    "pyg":       {"tried": False, "used": False, "reason": "no graph"},
    "z3":        {"tried": False, "used": False, "reason": "covered numerically"},
    "cvc5":      {"tried": False, "used": False, "reason": "covered numerically"},
    "sympy":     {"tried": False, "used": False, "reason": "not used here; clifford suffices"},
    "clifford":  {"tried": False, "used": False, "reason": "load_bearing: constructs rotor R=exp(-B/2) and reverse"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi":       {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx":  {"tried": False, "used": False, "reason": "no cells"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from clifford import Cl
TOOL_MANIFEST["clifford"]["tried"] = True
TOOL_MANIFEST["clifford"]["used"] = True
TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
e12, e13, e23 = e1*e2, e1*e3, e2*e3

def rotor(B, theta):
    return np.cos(theta/2) - np.sin(theta/2) * B  # B is unit bivector, B^2=-1

def approx_eq(a, b, tol=1e-10):
    return float(abs((a - b).value).max()) < tol

def run_positive_tests():
    r = {}
    R1 = rotor(e12, np.pi/3)
    R2 = rotor(e23, np.pi/4)
    # R * ~R = 1
    r["R1_unitary"] = approx_eq(R1 * ~R1, 1 + 0*e1)
    r["R2_unitary"] = approx_eq(R2 * ~R2, 1 + 0*e1)
    # product of rotors is a rotor -> still unitary
    R = R1 * R2
    r["product_unitary"] = approx_eq(R * ~R, 1 + 0*e1)
    # rotating e1 by R1 (2*pi rotation identity)
    R_full = rotor(e12, 2*np.pi)
    r["R_2pi_is_minus_one"] = approx_eq(R_full, -1 + 0*e1)  # spinor double cover
    return r

def run_negative_tests():
    r = {}
    # Non-unit bivector -> exponentiated naively is NOT unitary
    B = 2.0 * e12  # not unit
    fake = np.cos(0.5) - np.sin(0.5) * B
    r["nonunit_not_rotor"] = not approx_eq(fake * ~fake, 1 + 0*e1)
    # Sum of two rotors is NOT generally a rotor
    R1 = rotor(e12, 0.3)
    R2 = rotor(e23, 0.4)
    r["sum_not_rotor"] = not approx_eq((R1+R2) * ~(R1+R2), 1 + 0*e1)
    return r

def run_boundary_tests():
    r = {}
    # theta=0 => rotor = 1
    r["theta_zero_is_identity"] = approx_eq(rotor(e12, 0.0), 1 + 0*e1)
    # theta=4pi => rotor = 1 (full spinor cycle)
    r["theta_4pi_is_identity"] = approx_eq(rotor(e12, 4*np.pi), 1 + 0*e1)
    return r

def main():
    results = {
        "name": "sim_cl3_rotor_product",
        "classification": classification,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    all_pass = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    results["pass"] = bool(all_pass)
    out = os.path.join(os.path.dirname(__file__), "results", "sim_cl3_rotor_product.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({"pass": results["pass"], "out": out}))
    return 0 if all_pass else 1

if __name__ == "__main__":
    raise SystemExit(main())
