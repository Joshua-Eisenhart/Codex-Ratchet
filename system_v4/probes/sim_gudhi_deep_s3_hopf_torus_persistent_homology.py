#!/usr/bin/env python3
"""
sim_gudhi_deep_s3_hopf_torus_persistent_homology.py

Deep gudhi exercise: sample point clouds from candidate carrier manifolds
(S^3 in R^4, Hopf torus T^2 embedded in S^3 -> R^4, and a flat torus in R^4),
compute persistent homology via Vietoris-Rips -> SimplexTree -> persistence,
and verify that the persistent Betti numbers at a plateau filtration value
match topological expectation.

Expected Betti signatures (mod-2 coefficients, gudhi default):
  S^3           : (b0, b1, b2, b3) = (1, 0, 0, 1)
  Torus T^2     : (b0, b1, b2)     = (1, 2, 1)

Gudhi is load-bearing: SimplexTree construction, persistence computation,
and persistent_betti_numbers() are the decisive calls. No fallback.
"""

import json
import os
import numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        None,
    "cvc5":      None,
    "sympy":     None,
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# Import attempts
try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError as e:
    TOOL_MANIFEST["gudhi"]["reason"] = f"not installed: {e}"
    raise SystemExit("BLOCKER: gudhi not importable; cannot run load-bearing TDA sim")

try:
    import numpy as _np  # already imported
    TOOL_MANIFEST["pytorch"]["reason"] = "not needed; sampling is numpy-only"
    TOOL_MANIFEST["pyg"]["reason"] = "not needed; no graph msg-passing in this sim"
    TOOL_MANIFEST["z3"]["reason"] = "not needed; Betti numbers are numeric not SAT"
    TOOL_MANIFEST["cvc5"]["reason"] = "not needed; no SMT constraint here"
    TOOL_MANIFEST["sympy"]["reason"] = "not needed; numeric sampling"
    TOOL_MANIFEST["clifford"]["reason"] = "not needed; Hopf param given explicitly"
    TOOL_MANIFEST["geomstats"]["reason"] = "not needed; S^3 sampled via Gaussian-normalize"
    TOOL_MANIFEST["e3nn"]["reason"] = "not needed; no equivariant layer"
    TOOL_MANIFEST["rustworkx"]["reason"] = "not needed; simplex adjacency via gudhi"
    TOOL_MANIFEST["xgi"]["reason"] = "not needed; not a hypergraph problem"
    TOOL_MANIFEST["toponetx"]["reason"] = "not needed; gudhi handles simplicial complex"
except Exception:
    pass


# =====================================================================
# SAMPLERS
# =====================================================================

def sample_sphere(n, dim, rng):
    """Uniform sample on S^{dim} in R^{dim+1}."""
    x = rng.standard_normal((n, dim + 1))
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    return x


def sample_hopf_torus(n, rng, theta0=np.pi / 4):
    """
    Hopf torus = preimage under Hopf map of a latitude circle on S^2.
    Param: (phi, psi) in [0,2pi)^2, with fixed polar angle theta0.
    Embed S^3 in R^4 as:
        z1 = cos(theta0/2) * exp(i*(phi+psi)/2) ... etc.
    We use the standard Clifford-torus-like Hopf lift:
        x = (cos(a) cos(phi), cos(a) sin(phi), sin(a) cos(psi), sin(a) sin(psi))
    with a = theta0/2 fixed.  This gives a flat torus T^2 embedded in S^3.
    """
    a = theta0 / 2.0
    phi = rng.uniform(0, 2 * np.pi, n)
    psi = rng.uniform(0, 2 * np.pi, n)
    ca, sa = np.cos(a), np.sin(a)
    x = np.stack(
        [ca * np.cos(phi), ca * np.sin(phi), sa * np.cos(psi), sa * np.sin(psi)],
        axis=1,
    )
    return x


def sample_flat_torus(n, rng, R=2.0, r=1.0):
    """Standard torus in R^3 (padded to R^4 with a zero column)."""
    u = rng.uniform(0, 2 * np.pi, n)
    v = rng.uniform(0, 2 * np.pi, n)
    x = np.stack(
        [(R + r * np.cos(v)) * np.cos(u),
         (R + r * np.cos(v)) * np.sin(u),
          r * np.sin(v),
          np.zeros(n)],
        axis=1,
    )
    return x


def sample_two_blobs(n, rng):
    """Two well-separated Gaussian blobs -- should give b0=2, b1=b2=0."""
    half = n // 2
    a = rng.standard_normal((half, 3)) * 0.1 + np.array([0, 0, 0])
    b = rng.standard_normal((n - half, 3)) * 0.1 + np.array([10, 0, 0])
    x = np.vstack([a, b])
    return np.hstack([x, np.zeros((n, 1))])


# =====================================================================
# PERSISTENT BETTI via gudhi
# =====================================================================

def persistent_betti(points, max_edge_length, max_dim, plateau):
    """
    Build Vietoris-Rips SimplexTree, compute persistence, return
    persistent Betti numbers at filtration value `plateau`.

    gudhi-load-bearing calls:
        gudhi.RipsComplex             -> VR complex
        RipsComplex.create_simplex_tree(max_dimension=...)
        SimplexTree.persistence(...)
        SimplexTree.persistent_betti_numbers(from_value, to_value)
        SimplexTree.betti_numbers()   -- cross-check
    """
    TOOL_MANIFEST["gudhi"]["used"] = True
    rips = gudhi.RipsComplex(points=points, max_edge_length=max_edge_length)
    st = rips.create_simplex_tree(max_dimension=max_dim + 1)
    # Sanity: must be a SimplexTree
    assert isinstance(st, gudhi.SimplexTree), "gudhi did not return SimplexTree"
    st.compute_persistence(homology_coeff_field=2, min_persistence=0.0)
    # Persistent Betti numbers at the plateau (interval [plateau, plateau]).
    pbetti = st.persistent_betti_numbers(from_value=plateau, to_value=plateau)
    # Unreduced Betti on the final complex (cross-check)
    fbetti = st.betti_numbers()
    # Pad to max_dim
    while len(pbetti) <= max_dim:
        pbetti.append(0)
    while len(fbetti) <= max_dim:
        fbetti.append(0)
    return pbetti[: max_dim + 1], fbetti[: max_dim + 1], st.num_simplices()


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    rng = np.random.default_rng(20260414)

    # --- Torus T^2 (flat, in R^4) -> expect (1,2,1) ---
    pts = sample_flat_torus(300, rng)
    pbetti, fbetti, nsimp = persistent_betti(
        pts, max_edge_length=1.5, max_dim=2, plateau=0.9
    )
    ok_torus = (pbetti[0] == 1 and pbetti[1] == 2 and pbetti[2] == 1)
    results["torus_T2"] = {
        "n_points": 300,
        "persistent_betti_at_plateau": pbetti,
        "final_betti": fbetti,
        "num_simplices": nsimp,
        "expected": [1, 2, 1],
        "plateau": 0.9,
        "pass": bool(ok_torus),
    }

    # --- S^3 -> expect (1,0,0,1) ---
    pts = sample_sphere(250, dim=3, rng=rng)
    pbetti, fbetti, nsimp = persistent_betti(
        pts, max_edge_length=1.2, max_dim=3, plateau=0.7
    )
    ok_s3 = (pbetti[0] == 1 and pbetti[1] == 0 and pbetti[2] == 0 and pbetti[3] == 1)
    results["S3"] = {
        "n_points": 250,
        "persistent_betti_at_plateau": pbetti,
        "final_betti": fbetti,
        "num_simplices": nsimp,
        "expected": [1, 0, 0, 1],
        "plateau": 0.7,
        "pass": bool(ok_s3),
    }

    # --- Hopf torus (T^2 in S^3) -> expect (1,2,1) ---
    pts = sample_hopf_torus(300, rng, theta0=np.pi / 2)  # Clifford torus
    pbetti, fbetti, nsimp = persistent_betti(
        pts, max_edge_length=0.8, max_dim=2, plateau=0.5
    )
    ok_hopf = (pbetti[0] == 1 and pbetti[1] == 2 and pbetti[2] == 1)
    results["hopf_torus"] = {
        "n_points": 300,
        "persistent_betti_at_plateau": pbetti,
        "final_betti": fbetti,
        "num_simplices": nsimp,
        "expected": [1, 2, 1],
        "plateau": 0.5,
        "pass": bool(ok_hopf),
    }

    results["all_pass"] = bool(ok_torus and ok_s3 and ok_hopf)
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """Two disjoint blobs must NOT give b0=1; must give b0=2, b1=b2=0."""
    results = {}
    rng = np.random.default_rng(7)
    pts = sample_two_blobs(120, rng)
    pbetti, fbetti, nsimp = persistent_betti(
        pts, max_edge_length=1.0, max_dim=2, plateau=0.5
    )
    # Negative: expecting (2,0,0). If we ever see b0=1, topology is wrong.
    not_connected = (pbetti[0] == 2)
    no_loops = (pbetti[1] == 0)
    no_voids = (pbetti[2] == 0)
    # Also confirm that torus_expected_signature would NOT spuriously match blobs.
    does_not_look_like_torus = not (pbetti[0] == 1 and pbetti[1] == 2 and pbetti[2] == 1)
    results["two_blobs"] = {
        "persistent_betti": pbetti,
        "final_betti": fbetti,
        "num_simplices": nsimp,
        "expected": [2, 0, 0],
        "pass": bool(not_connected and no_loops and no_voids and does_not_look_like_torus),
    }
    results["all_pass"] = bool(results["two_blobs"]["pass"])
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Degenerate inputs: single point, tiny radius, too-large radius."""
    results = {}
    rng = np.random.default_rng(11)

    # Single point: b0=1, all else 0
    pts = np.array([[0.0, 0.0, 0.0, 0.0]])
    pbetti, fbetti, nsimp = persistent_betti(pts, 0.1, 2, plateau=0.0)
    results["single_point"] = {
        "persistent_betti": pbetti,
        "pass": bool(pbetti[0] == 1 and pbetti[1] == 0 and pbetti[2] == 0),
    }

    # Torus with tiny edge length -> no loops captured, b0 = n_points
    pts = sample_flat_torus(50, rng)
    pbetti, _, _ = persistent_betti(pts, max_edge_length=0.01, max_dim=2, plateau=0.005)
    results["torus_tiny_radius"] = {
        "persistent_betti": pbetti,
        "expected_b0": 50,
        "pass": bool(pbetti[0] == 50 and pbetti[1] == 0 and pbetti[2] == 0),
    }

    # Torus with oversized edge -> complex collapses to a simplex, b0=1, bk=0 for k>=1
    pts = sample_flat_torus(40, rng)
    pbetti, _, _ = persistent_betti(pts, max_edge_length=100.0, max_dim=2, plateau=50.0)
    results["torus_oversized_radius"] = {
        "persistent_betti": pbetti,
        "pass": bool(pbetti[0] == 1 and pbetti[1] == 0 and pbetti[2] == 0),
    }

    results["all_pass"] = bool(
        results["single_point"]["pass"]
        and results["torus_tiny_radius"]["pass"]
        and results["torus_oversized_radius"]["pass"]
    )
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # gudhi was actually called -- record reason
    TOOL_MANIFEST["gudhi"]["used"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = (
        "load-bearing: RipsComplex.create_simplex_tree, "
        "SimplexTree.compute_persistence, persistent_betti_numbers, "
        "betti_numbers are the decisive calls producing Betti signatures"
    )
    TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"

    all_pass = bool(pos["all_pass"] and neg["all_pass"] and bnd["all_pass"])

    results = {
        "name": "sim_gudhi_deep_s3_hopf_torus_persistent_homology",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
        "betti_signature_summary": {
            "S3":         pos["S3"]["persistent_betti_at_plateau"],
            "hopf_torus": pos["hopf_torus"]["persistent_betti_at_plateau"],
            "torus_T2":   pos["torus_T2"]["persistent_betti_at_plateau"],
            "two_blobs_negative": neg["two_blobs"]["persistent_betti"],
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir, "sim_gudhi_deep_s3_hopf_torus_persistent_homology_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"ALL_PASS={all_pass}")
    print(f"BETTI: S^3={results['betti_signature_summary']['S3']} "
          f"Hopf={results['betti_signature_summary']['hopf_torus']} "
          f"T^2={results['betti_signature_summary']['torus_T2']} "
          f"blobs={results['betti_signature_summary']['two_blobs_negative']}")
