#!/usr/bin/env python3
"""Non-commutativity: e3nn irrep rotations compose order-dependently for l>=1."""
import json, os, torch
from e3nn import o3

TOOL_MANIFEST = {
    "e3nn": {"tried": True, "used": True,
             "reason": "Wigner-D matrices for l>=1 irreps of SO(3) are order-dependent; e3nn's exact D-matrix construction is load-bearing because a naive cartesian matmul cannot certify the irrep structure preserved by the composition."},
    "pytorch": {"tried": True, "used": True,
                "reason": "tensor framework e3nn builds upon; needed to evaluate D-matrix products on probe vectors."},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"e3nn": "load_bearing", "pytorch": "supportive",
                         "clifford": None, "z3": None, "sympy": None}

def run_positive_tests():
    irrep = o3.Irrep("1o")
    a = torch.tensor([0.3, 0.7, 0.1])
    b = torch.tensor([1.1, 0.2, 0.5])
    Da = irrep.D_from_angles(a[0], a[1], a[2])
    Db = irrep.D_from_angles(b[0], b[1], b[2])
    v = torch.tensor([1.0, 0.0, 0.0])
    ab = Da @ Db @ v
    ba = Db @ Da @ v
    nz = torch.linalg.norm(ab - ba).item() > 1e-6
    return {"irrep_l1_order_matters": nz,
            "note": "order swap excludes irrep-coherent witness", "pass": nz}

def run_negative_tests():
    # l=0 irrep (scalar): trivially commutes
    irrep = o3.Irrep("0e")
    a = torch.tensor([0.3, 0.7, 0.1])
    b = torch.tensor([1.1, 0.2, 0.5])
    Da = irrep.D_from_angles(a[0], a[1], a[2])
    Db = irrep.D_from_angles(b[0], b[1], b[2])
    v = torch.tensor([1.0])
    commutes = torch.linalg.norm(Da@Db@v - Db@Da@v).item() < 1e-10
    return {"l0_scalar_commutes_control": commutes, "pass": commutes}

def run_boundary_tests():
    # Same-axis rotations commute for l=1
    irrep = o3.Irrep("1o")
    Da = irrep.D_from_angles(torch.tensor(0.0), torch.tensor(0.5), torch.tensor(0.0))
    Db = irrep.D_from_angles(torch.tensor(0.0), torch.tensor(1.2), torch.tensor(0.0))
    v = torch.tensor([1.0, 0.0, 0.0])
    eq = torch.linalg.norm(Da@Db@v - Db@Da@v).item() < 1e-8
    return {"same_axis_commutes": eq, "pass": eq}

if __name__ == "__main__":
    results = {"name": "sim_geom_noncomm_e3nn_irrep_compose_order",
               "classification": "canonical",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(), "boundary": run_boundary_tests()}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_noncomm_e3nn_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    ap = all(r.get("pass") for r in [results["positive"], results["negative"], results["boundary"]])
    print(f"PASS={ap} -> {out_path}")
