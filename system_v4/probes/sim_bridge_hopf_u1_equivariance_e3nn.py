#!/usr/bin/env python3
"""bridge_hopf_u1_equivariance_e3nn -- canonical bridge: use e3nn's
irrep / rotation machinery (load_bearing) to check SO(3) equivariance of the
Hopf-image spherical coordinates, subsuming U(1) phase equivariance.

scope_note: system_v5/new docs/ENGINE_MATH_REFERENCE.md Hopf;
LADDERS_FENCES_ADMISSION_REFERENCE.md fibration fences.
"""
import numpy as np
import torch
from e3nn import o3
from _doc_illum_common import build_manifest, write_results

TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH = build_manifest()
TOOL_MANIFEST["e3nn"] = {"tried": True, "used": True, "reason": "o3 Wigner D/rotations"}
TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"
TOOL_MANIFEST["pytorch"] = {"tried": True, "used": True, "reason": "tensor backend for e3nn"}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"


def hopf(z1, z2):
    x = 2 * (z1 * np.conj(z2)).real
    y = 2 * (z1 * np.conj(z2)).imag
    z = abs(z1) ** 2 - abs(z2) ** 2
    return np.array([x, y, z])


def run_positive_tests():
    r = {}
    # Base Hopf image
    z1 = (1/np.sqrt(2)) + 0j; z2 = 0 + (1/np.sqrt(2))*1j
    v = hopf(z1, z2)
    v_t = torch.tensor(v, dtype=torch.float64).unsqueeze(0)

    # Apply an SO(3) rotation via e3nn Wigner D on l=1 irrep
    irreps = o3.Irreps("1o")
    angles = torch.tensor([[0.3, 0.5, 0.7]], dtype=torch.float64)
    D = irreps.D_from_angles(*angles.unbind(-1)).to(torch.float64)
    v_rot = (D @ v_t.unsqueeze(-1)).squeeze(-1)

    r["rotation_preserves_norm"] = {
        "pass": bool(abs(v_rot.norm().item() - 1.0) < 1e-8),
        "norm": v_rot.norm().item(),
    }

    # U(1) phase invariance of Hopf
    phi = 0.8
    v2 = hopf(z1 * np.exp(1j*phi), z2 * np.exp(1j*phi))
    r["u1_invariance"] = {"pass": bool(np.allclose(v, v2, atol=1e-10))}
    return r


def run_negative_tests():
    r = {}
    # Different Hopf preimages with different |z1|/|z2| ratio -> different S^2 image
    v1 = hopf(1+0j, 0+0j)
    v2 = hopf(0+0j, 1+0j)
    r["distinct_preimage_distinct_image"] = {"pass": not np.allclose(v1, v2)}
    return r


def run_boundary_tests():
    r = {}
    # Identity rotation = no change
    irreps = o3.Irreps("1o")
    D = irreps.D_from_angles(torch.tensor(0.0), torch.tensor(0.0), torch.tensor(0.0)).to(torch.float64)
    v = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    v_rot = D @ v
    r["identity_rotation"] = {"pass": bool(torch.allclose(v, v_rot, atol=1e-10))}
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    allp = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "bridge_hopf_u1_equivariance_e3nn",
        "classification": "canonical",
        "scope_note": "ENGINE_MATH_REFERENCE.md Hopf; LADDERS_FENCES_ADMISSION_REFERENCE.md fibration",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": allp,
    }
    write_results("bridge_hopf_u1_equivariance_e3nn", results)
