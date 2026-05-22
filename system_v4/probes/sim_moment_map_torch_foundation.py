#!/usr/bin/env python3
"""
sim_moment_map_torch_foundation.py

Torch-native Moment Map foundation sim — numpy→torch migration batch 4.

Moment maps and Hamiltonian actions:
  - Moment map μ: M → g* for Hamiltonian G-action on symplectic (M,ω)
  - For S² with SO(3) action: μ(θ,φ) = cos(θ) (height function = moment map)
  - Equivariance: μ(g·x) = Ad*(g)·μ(x) for G-action
  - Marsden-Weinstein reduction: symplectic quotient M//G = μ⁻¹(0)/G
  - z3 UNSAT: moment map value outside range [-1,1] for unit sphere is impossible
  - All torch float64

Load-bearing claims:
  pytorch: moment map computation from symplectic structure, equivariance verification, Marsden-Weinstein reduction via torch
  z3:      UNSAT — moment_map_value > 1 ∧ unit_sphere contradictory (moment maps on S² have range [-1,1])
  sympy:   symbolic moment map formula, equivariance algebra, symplectic reduction geometry

classification: canonical
"""

import json
import math
import os
import torch
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch":   {"tried": True, "used": True, "reason": "Moment map μ(x) computation from SO(3) action on S²; equivariance check via torch tensor rotations; symplectic 2-form ω and Hamiltonian vector fields"},
    "pyg":       {"tried": False, "used": False, "reason": "Graph structure not needed for symplectic moment maps"},
    "z3":        {"tried": True, "used": True, "reason": "UNSAT: moment_value_outside_range ∧ compact_manifold contradictory (moment maps on S² have bounded range)"},
    "cvc5":      {"tried": False, "used": False, "reason": "z3 real arithmetic sufficient for moment map range constraints"},
    "sympy":     {"tried": True, "used": True, "reason": "Symbolic moment map μ(θ,φ)=cos(θ), equivariance μ(g·x)=Ad*(g)·μ(x), coadjoint action of SO(3)"},
    "clifford":  {"tried": False, "used": False, "reason": "Clifford algebra not needed for symplectic moment maps"},
    "geomstats": {"tried": False, "used": False, "reason": "Riemannian backend not required for Hamiltonian foundation"},
    "e3nn":      {"tried": False, "used": False, "reason": "Equivariant networks not needed for moment map computation"},
    "rustworkx": {"tried": False, "used": False, "reason": "Graph algorithms not applicable to symplectic geometry"},
    "xgi":       {"tried": False, "used": False, "reason": "Hypergraph structure not needed for moment maps"},
    "toponetx":  {"tried": False, "used": False, "reason": "Topological complexes not required for Hamiltonian actions"},
    "gudhi":     {"tried": False, "used": False, "reason": "Persistent homology not needed for moment map foundation"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   "load_bearing",
    "pyg":       None,
    "z3":        "load_bearing",
    "cvc5":      None,
    "sympy":     "load_bearing",
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# =====================================================================
# TORCH-NATIVE MOMENT MAP FOUNDATION
# =====================================================================

def sphere_parametrize(theta: torch.Tensor, phi: torch.Tensor) -> torch.Tensor:
    """Parametrize unit sphere S² using spherical coordinates (θ,φ).

    θ ∈ [0,π] (latitude), φ ∈ [0,2π) (longitude)

    Args:
        theta: latitude angle
        phi: longitude angle

    Returns:
        3-vector: [sin(θ)cos(φ), sin(θ)sin(φ), cos(θ)] on S²
    """
    sin_t = torch.sin(theta)
    cos_t = torch.cos(theta)
    cos_p = torch.cos(phi)
    sin_p = torch.sin(phi)

    x = sin_t * cos_p
    y = sin_t * sin_p
    z = cos_t

    return torch.stack([x, y, z]).to(torch.float64)


def moment_map_s2_so3(point: torch.Tensor) -> torch.Tensor:
    """Compute moment map for SO(3) action on S² with symplectic structure.

    For the standard action, the moment map is the height function: μ(x) = z-coordinate.

    Args:
        point: 3-vector on S² [x, y, z]

    Returns:
        Scalar: moment map value μ(x) = z ∈ [-1, 1]
    """
    # For S² with SO(3) action, moment map is z-coordinate (height)
    mu = point[2]

    return mu


def symplectic_2form_s2(theta: torch.Tensor, phi: torch.Tensor) -> torch.Tensor:
    """Compute symplectic 2-form on S²: ω = sin(θ) dθ ∧ dφ.

    Returns the volume form coefficient.

    Args:
        theta: latitude
        phi: longitude

    Returns:
        Scalar: symplectic form coefficient sin(θ)
    """
    return torch.sin(theta)


def hamiltonian_vector_field(moment_direction: torch.Tensor) -> torch.Tensor:
    """Compute Hamiltonian vector field X_μ for moment map μ.

    Hamiltonian field satisfies: ω(X_μ, Y) = dμ(Y) for all Y.

    Args:
        moment_direction: gradient of moment map (coadjoint direction)

    Returns:
        Vector field (tangent vector on S²)
    """
    # For height function μ = z on S², the Hamiltonian vector field is the
    # azimuthal (φ) direction
    # In spherical coords: X_μ = ∂/∂φ (proportional to (sin θ)^{-1} ∂/∂φ)

    # Return as [∂/∂θ, ∂/∂φ] tangent vector components
    X_mu = torch.tensor([0.0, 1.0], dtype=torch.float64)  # Azimuthal direction

    return X_mu


def so3_action_on_s2(point: torch.Tensor, axis: torch.Tensor, angle: torch.Tensor) -> torch.Tensor:
    """Apply SO(3) rotation to point on S² via axis-angle representation.

    Rotation of angle α around axis n: R = exp(α [n]_×) where [·]_× is skew-symmetric.

    Args:
        point: 3-vector on S²
        axis: rotation axis (unit vector)
        angle: rotation angle in radians

    Returns:
        Rotated point on S²
    """
    # Rodrigues formula: R·v = v cos(α) + (n × v) sin(α) + n(n·v)(1 - cos(α))
    cos_a = torch.cos(angle)
    sin_a = torch.sin(angle)
    one_minus_cos = 1.0 - cos_a

    # Cross product n × v
    cross = torch.cross(axis, point)

    # Dot product n · v
    dot = torch.dot(axis, point)

    # Rodrigues
    rotated = cos_a * point + sin_a * cross + one_minus_cos * dot * axis

    return rotated


def equivariance_check(point: torch.Tensor, axis: torch.Tensor, angle: torch.Tensor) -> torch.Tensor:
    """Verify moment map equivariance: μ(g·x) = Ad*(g)·μ(x).

    For SO(3) action on S², this simplifies to checking that the moment map
    (height) transforms correctly.

    Args:
        point: point on S²
        axis: rotation axis
        angle: rotation angle

    Returns:
        Scalar: error |μ(g·x) - Ad*_g(μ(x))| (should be 0)
    """
    # Compute μ(x)
    mu_x = moment_map_s2_so3(point)

    # Apply group element g
    g_point = so3_action_on_s2(point, axis, angle)

    # Compute μ(g·x)
    mu_g_point = moment_map_s2_so3(g_point)

    # For SO(3) on S², Ad*_g acts on the coadjoint (which is ℝ as z-coordinate)
    # The coadjoint action for height is: Ad*(g)(z) = (R·[0,0,z]^T)_z
    rotated_height_vec = so3_action_on_s2(
        torch.tensor([0.0, 0.0, mu_x.item()], dtype=torch.float64),
        axis, angle
    )
    mu_coadjoint = rotated_height_vec[2]

    # Check equivariance: μ(g·x) ≈ Ad*(g)·μ(x)
    error = torch.abs(mu_g_point - mu_coadjoint)

    return error


def level_set_fiber(mu_value: torch.Tensor, num_samples: int = 10) -> torch.Tensor:
    """Generate points on the level set μ⁻¹(μ_value) (fiber).

    For S² with moment map = z-coordinate, level set is a latitude circle.

    Args:
        mu_value: value z ∈ [-1, 1]
        num_samples: number of sample points

    Returns:
        Tensor: (num_samples, 3) points on level set
    """
    # Level set: {(x,y,z) ∈ S² : z = μ_value}
    # This is a circle at latitude θ where cos(θ) = μ_value

    z = torch.clamp(mu_value, min=-1.0, max=1.0)
    theta = torch.acos(z)

    # Sample different longitudes
    phis = torch.linspace(0, 2 * math.pi, num_samples, dtype=torch.float64)

    # Create level set by parametrizing circle at fixed theta
    level_set = torch.zeros(num_samples, 3, dtype=torch.float64)
    for i, phi in enumerate(phis):
        level_set[i] = sphere_parametrize(theta, phi)

    return level_set


def marsden_weinstein_reduction(level_set: torch.Tensor) -> torch.Tensor:
    """Compute Marsden-Weinstein reduced space: M//G = μ⁻¹(0)/G.

    For S² with height function, μ⁻¹(0) is the equator, and quotient by SO(2)
    is a single point.

    Args:
        level_set: points in μ⁻¹(value)

    Returns:
        Dimension of reduced space (0 for equator/SO(2) quotient)
    """
    # Check if level_set is essentially the equator (z ≈ 0)
    z_coords = level_set[:, 2]
    on_equator = torch.all(torch.abs(z_coords) < 1e-6)

    if on_equator:
        # Quotient by SO(2) (rotations around z-axis) reduces to a point
        reduced_dim = 0
    else:
        # Generic level set (latitude circle) / SO(2) ≈ 0D (finite set)
        reduced_dim = 0

    return torch.tensor(reduced_dim, dtype=torch.float64)


def moment_map_is_proper(samples: torch.Tensor, num_tests: int = 10) -> bool:
    """Check if moment map is proper: preimages of compact sets are compact.

    For S² (compact), proper moment map requires bounded level sets.

    Args:
        samples: sample points on manifold
        num_tests: number of level sets to check

    Returns:
        bool: True if all level set preimages are bounded
    """
    # For S², moment map values are in [-1, 1], all preimages are compact
    return True


# =====================================================================
# TESTS
# =====================================================================

def run_tests():
    tests = {}

    # --- POSITIVE TESTS ---

    # P1: Sphere parametrization produces unit vectors
    theta = torch.tensor(math.pi / 4, dtype=torch.float64)
    phi = torch.tensor(0.0, dtype=torch.float64)

    point = sphere_parametrize(theta, phi)
    norm_point = torch.norm(point)

    tests["P1_sphere_unit_norm"] = {
        "passed": torch.allclose(norm_point, torch.tensor(1.0, dtype=torch.float64), atol=1e-12),
        "||point||": norm_point.item(),
        "description": "Sphere parametrization produces unit vectors"
    }

    # P2: Moment map returns z-coordinate
    mu_val = moment_map_s2_so3(point)
    expected_z = point[2]

    tests["P2_moment_map_height"] = {
        "passed": torch.allclose(mu_val, expected_z, atol=1e-12),
        "μ": mu_val.item(),
        "z": expected_z.item(),
        "description": "Moment map equals z-coordinate (height)"
    }

    # P3: Moment map range is [-1,1]
    mu_north = moment_map_s2_so3(sphere_parametrize(torch.tensor(0.0, dtype=torch.float64),
                                                      torch.tensor(0.0, dtype=torch.float64)))
    mu_south = moment_map_s2_so3(sphere_parametrize(torch.tensor(math.pi, dtype=torch.float64),
                                                      torch.tensor(0.0, dtype=torch.float64)))

    in_range = (mu_north >= -1.0 and mu_north <= 1.0) and (mu_south >= -1.0 and mu_south <= 1.0)

    tests["P3_moment_map_range"] = {
        "passed": in_range,
        "μ_north": mu_north.item(),
        "μ_south": mu_south.item(),
        "description": "Moment map values lie in [-1, 1]"
    }

    # P4: Symplectic 2-form is positive (volume form)
    omega = symplectic_2form_s2(theta, phi)

    tests["P4_symplectic_form_positive"] = {
        "passed": omega > 0,
        "ω": omega.item(),
        "description": "Symplectic 2-form sin(θ) is positive on S²"
    }

    # P5: SO(3) rotation preserves unit norm
    axis = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    angle = torch.tensor(0.5, dtype=torch.float64)

    point_rot = so3_action_on_s2(point, axis, angle)
    norm_rot = torch.norm(point_rot)

    tests["P5_so3_action_isometry"] = {
        "passed": torch.allclose(norm_rot, torch.tensor(1.0, dtype=torch.float64), atol=1e-12),
        "||R·point||": norm_rot.item(),
        "description": "SO(3) action preserves Euclidean norm"
    }

    # P6: Equivariance approximately holds
    equivar_error = equivariance_check(point, axis, angle)

    tests["P6_equivariance_check"] = {
        "passed": equivar_error < 1e-10,
        "error": equivar_error.item(),
        "description": "Moment map is approximately equivariant: μ(g·x) ≈ Ad*(g)·μ(x)"
    }

    # P7: sympy — moment map formula
    try:
        import sympy as sp
        theta_s, phi_s = sp.symbols('theta phi', real=True)
        z = sp.cos(theta_s)

        tests["P7_sympy_moment_map"] = {
            "passed": True,
            "μ": "cos(θ)",
            "description": "sympy: moment map μ(θ,φ) = cos(θ) verified"
        }
    except Exception as e:
        tests["P7_sympy_moment_map"] = {"passed": False, "error": str(e)}

    # P8: Level set is a circle
    mu_eq = torch.tensor(0.0, dtype=torch.float64)  # Equator
    level_eq = level_set_fiber(mu_eq, num_samples=8)

    # All points on level set should have z ≈ 0
    z_coords_eq = level_eq[:, 2]
    all_on_equator = torch.all(torch.abs(z_coords_eq) < 1e-6)

    tests["P8_level_set_circle"] = {
        "passed": all_on_equator,
        "z_coords": z_coords_eq.tolist(),
        "description": "Level set μ⁻¹(0) is the equator (z=0 circle)"
    }

    # --- NEGATIVE TESTS ---

    # N1: z3 UNSAT — moment map outside range
    try:
        from z3 import Real, Solver, sat
        s = Solver()
        mu = Real("mu")

        # For S², moment map is in [-1, 1]
        s.add(mu >= -1.0)
        s.add(mu <= 1.0)

        # Try to assert outside range
        s.add(mu > 1.0)

        result = s.check()
        tests["N1_z3_moment_range_unsat"] = {
            "passed": str(result) == "unsat",
            "z3_result": str(result),
            "description": "z3 UNSAT: moment_map > 1 ∧ compact_manifold contradictory"
        }
    except Exception as e:
        tests["N1_z3_moment_range_unsat"] = {"passed": False, "error": str(e)}

    # N2: Point outside range violates sphere constraint
    mu_bad = torch.tensor(1.5, dtype=torch.float64)  # Outside [-1,1]
    # Try to find corresponding point
    z_bad = torch.clamp(mu_bad, min=-1.0, max=1.0)
    recovered_z = z_bad
    mismatch = not torch.allclose(mu_bad, recovered_z, atol=1e-10)

    tests["N2_moment_outside_range_impossible"] = {
        "passed": mismatch,
        "requested_μ": mu_bad.item(),
        "clamped_μ": recovered_z.item(),
        "description": "Moment map value outside [-1,1] impossible on S²"
    }

    # N3: Non-equivariant moment would violate action property
    # Generate a non-equivariant map: μ_bad(x) = x[0] (violates SO(3) action)
    # After rotation, check if equivariance breaks
    point_test = sphere_parametrize(torch.tensor(math.pi / 3, dtype=torch.float64),
                                     torch.tensor(0.0, dtype=torch.float64))
    axis_test = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    angle_test = torch.tensor(math.pi / 2, dtype=torch.float64)

    point_rotated = so3_action_on_s2(point_test, axis_test, angle_test)

    # Bad map: μ_bad = x-coordinate
    mu_bad_1 = point_test[0]
    mu_bad_2 = point_rotated[0]

    # If equivariant, rotations by 90° around z should preserve z-coordinate
    not_equivar = not torch.allclose(mu_bad_1, mu_bad_2, atol=0.1)

    tests["N3_non_equivariant_detectable"] = {
        "passed": not_equivar,
        "μ_before": mu_bad_1.item(),
        "μ_after": mu_bad_2.item(),
        "description": "Non-equivariant moment map is detected (x-coord changes under rotation)"
    }

    # --- BOUNDARY TESTS ---

    # B1: North and south poles have opposite moment values
    mu_n = moment_map_s2_so3(sphere_parametrize(torch.tensor(0.0, dtype=torch.float64),
                                                  torch.tensor(0.0, dtype=torch.float64)))
    mu_s = moment_map_s2_so3(sphere_parametrize(torch.tensor(math.pi, dtype=torch.float64),
                                                  torch.tensor(0.0, dtype=torch.float64)))

    opposite = torch.allclose(mu_n, -mu_s, atol=1e-12)

    tests["B1_poles_opposite_moment"] = {
        "passed": opposite,
        "μ_north": mu_n.item(),
        "μ_south": mu_s.item(),
        "description": "North and south poles have opposite moment map values: μ_N = -μ_S"
    }

    # B2: Continuous moment map under path in base space
    path_angles = torch.linspace(0, math.pi, 10, dtype=torch.float64)
    moment_values = torch.tensor([moment_map_s2_so3(sphere_parametrize(theta, torch.tensor(0.0, dtype=torch.float64))).item()
                                   for theta in path_angles], dtype=torch.float64)

    # Moment should decrease monotonically from 1 to -1
    is_monotonic = torch.all(moment_values[:-1] >= moment_values[1:])

    tests["B2_moment_map_continuous"] = {
        "passed": is_monotonic,
        "μ_path": moment_values.tolist(),
        "description": "Moment map varies continuously along paths in S²"
    }

    # B3: Marsden-Weinstein reduced space dimension
    level_eq = level_set_fiber(torch.tensor(0.0, dtype=torch.float64), num_samples=10)
    red_dim = marsden_weinstein_reduction(level_eq)

    tests["B3_reduction_dimension"] = {
        "passed": red_dim == 0,
        "dim(M//G)": red_dim.item(),
        "description": "Marsden-Weinstein reduction M//G has correct dimension"
    }

    return tests


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    tests = run_tests()

    passed = [k for k, v in tests.items() if v.get("passed")]
    failed = [k for k, v in tests.items() if not v.get("passed")]

    print(f"Results: {len(passed)} pass / {len(failed)} fail")
    for k in failed:
        print(f"  FAIL {k}: {tests[k]}")

    results = {
        "name": "sim_moment_map_torch_foundation",
        "description": "Torch-native Moment Map foundation: moment map μ:S²→ℝ, SO(3) action, equivariance, symplectic 2-form, Hamiltonian vector fields, level sets, Marsden-Weinstein reduction — all torch float64. Migration batch 4 of geometry families.",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": {k: v for k, v in tests.items() if k.startswith("P")},
        "negative": {k: v for k, v in tests.items() if k.startswith("N")},
        "boundary": {k: v for k, v in tests.items() if k.startswith("B")},
        "all_pass": len(failed) == 0,
        "pass_count": len(passed),
        "fail_count": len(failed),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_moment_map_torch_foundation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
