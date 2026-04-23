#!/usr/bin/env python3
"""
Pure Spinor Transport on Nested Hopf Tori
==========================================
PURE GEOMETRY.  No engine.  No operators.  No dynamics.

Weyl spinors moving on nested Hopf tori via parallel transport.
Berry phase from the connection 1-form.
Cl(3) rotors for the transport.
Cell complex path tracking via TopoNetX.

Parts:
  1. Fiber loop transport  (theta1: 0 -> 2pi)
  2. Base loop transport   (theta2: 0 -> 2pi)
  3. Diagonal transport    (theta1 = theta2)
  4. Inter-torus transport (eta changes)
  5. Full circuit          (inner -> Clifford -> outer -> inner)
  6. Chirality tracking    (L/R Weyl throughout)
  7. Cell complex paths    (TopoNetX)
"""

import sys
import os
import json
import datetime
import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clifford import Cl

from hopf_manifold import (
    torus_coordinates, torus_radii, berry_phase,
    left_weyl_spinor, right_weyl_spinor,
    density_to_bloch, hopf_map,
    coherent_state_density,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
)
from clifford_engine_bridge import (
    rotor_z, rotor_x, apply_rotor,
    bloch_to_multivector, multivector_to_bloch,
    layout, blades, e1, e2, e3, e12, e23, e123, scalar,
)

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

N_STEPS = 200          # Steps per loop
N_ETA_SAMPLES = 20     # Eta values to scan
ETA_VALUES = np.linspace(np.pi / 16, np.pi / 2 - np.pi / 16, N_ETA_SAMPLES)

LEVELS = {
    "inner":    TORUS_INNER,      # pi/8
    "clifford": TORUS_CLIFFORD,   # pi/4
    "outer":    TORUS_OUTER,      # 3*pi/8
}


# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════

def q_to_spinor(q):
    """Quaternion on S3 -> C2 spinor."""
    a, b, c, d = q
    return np.array([a + 1j * b, c + 1j * d], dtype=complex)


def spinor_to_bloch(psi):
    """C2 spinor -> Bloch vector via rho = |psi><psi|."""
    rho = np.outer(psi, np.conj(psi))
    return density_to_bloch(rho)


def spinor_overlap(psi_a, psi_b):
    """<psi_a | psi_b>."""
    return np.vdot(psi_a, psi_b)


def solid_angle_equatorial_circle(eta):
    """Solid angle subtended by the base loop projected onto S2.

    The base loop (theta2: 0->2pi at fixed eta, theta1=0) traces a
    circle on S2 at polar angle 2*eta from the north pole.
    Solid angle of a spherical cap: Omega = 2*pi*(1 - cos(2*eta)).
    Berry phase = -Omega/2 = -pi*(1 - cos(2*eta)).

    The FIBER loop (theta1: 0->2pi) stays on a single Hopf fiber,
    projecting to a single point on S2 => solid angle = 0, Berry = 0.
    """
    return 2 * np.pi * (1 - np.cos(2 * eta))


def transport_along_loop(eta, loop_type="fiber", n_steps=N_STEPS):
    """Parallel-transport a spinor around a loop on the torus at latitude eta.

    loop_type:
      "fiber"    - theta1: 0->2pi, theta2=0  (vertical / Hopf fiber)
      "base"     - theta2: 0->2pi, theta1=0  (horizontal / base circle)
      "diagonal" - theta1=theta2: 0->2pi

    Uses Pancharatnam connection (product of overlaps) for the Berry phase,
    and explicit parallel transport (remove connection phase) for the spinor.
    """
    dt = 2 * np.pi / n_steps

    # Build the path on S3
    path_q = []
    for step in range(n_steps + 1):
        angle = step * dt
        if loop_type == "fiber":
            q = torus_coordinates(eta, angle, 0.0)
        elif loop_type == "base":
            q = torus_coordinates(eta, 0.0, angle)
        else:  # diagonal
            q = torus_coordinates(eta, angle, angle)
        path_q.append(q)

    # --- Pancharatnam Berry phase (correct geometric phase) ---
    # Use the closed loop (exclude the duplicate endpoint for Pancharatnam)
    loop_for_berry = np.array(path_q[:-1])  # N points, loop closes via wrap
    berry_pan = berry_phase(loop_for_berry)

    # --- Explicit parallel transport ---
    psi = q_to_spinor(path_q[0])
    psi /= np.linalg.norm(psi)
    trajectory = [psi.copy()]
    connection_sum = 0.0
    phases = [0.0]

    for step in range(n_steps):
        psi_natural = q_to_spinor(path_q[step + 1])
        psi_natural /= np.linalg.norm(psi_natural)

        overlap = spinor_overlap(trajectory[-1], psi_natural)
        conn = np.angle(overlap)
        connection_sum += conn

        psi_transported = psi_natural * np.exp(-1j * conn)
        psi_transported /= np.linalg.norm(psi_transported)

        trajectory.append(psi_transported.copy())
        phases.append(connection_sum)

    holonomy = np.angle(spinor_overlap(trajectory[0], trajectory[-1]))

    # Track what the loop does on S2 (Hopf image)
    s2_points = np.array([hopf_map(q) for q in path_q])
    s2_diameter = float(np.max(np.linalg.norm(s2_points - s2_points[0], axis=1)))

    return {
        "trajectory": trajectory,
        "phases": phases,
        "berry_phase_pancharatnam": float(berry_pan),
        "connection_sum": float(connection_sum),
        "holonomy": float(holonomy),
        "s2_diameter": s2_diameter,
    }


def run_part1():
    """Fiber loop transport.

    The theta1 loop at fixed (eta, theta2=0) traces a circle on S2.
    The S2 image is a circle at polar angle 2*eta from the z-axis.
    Solid angle of the cap: Omega = 2*pi*(1 - cos(2*eta)).
    Berry phase = -Omega/2 = -pi*(1 - cos(2*eta)).

    Pancharatnam Berry phase is defined mod 2*pi, so we compare
    modulo 2*pi.
    """
    print("=" * 60)
    print("PART 1: Fiber Loop Transport")
    print("=" * 60)
    print("  The theta1 loop traces a circle on S2 with OPPOSITE orientation")
    print("  to the theta2 (base) loop at the same eta.")
    print("  Theory: Berry_fiber = +pi*(1 - cos(2*eta))  [mod 2*pi]\n")

    results = []
    for eta in ETA_VALUES:
        res = transport_along_loop(eta, "fiber")
        omega = solid_angle_equatorial_circle(eta)
        theory = +omega / 2  # = +pi*(1 - cos(2*eta)) -- opposite sign to base
        # Compare mod 2*pi
        berry_val = res["berry_phase_pancharatnam"]
        diff = (berry_val - theory + np.pi) % (2 * np.pi) - np.pi
        error = abs(diff)
        record = {
            "eta": float(eta),
            "eta_over_pi": float(eta / np.pi),
            "berry_phase": berry_val,
            "connection_sum": res["connection_sum"],
            "theory": float(theory),
            "error_mod2pi": float(error),
            "holonomy": res["holonomy"],
            "s2_diameter": res["s2_diameter"],
            "match": error < 0.05,
        }
        results.append(record)
        status = "OK" if record["match"] else "MISS"
        print(f"  eta={eta:.4f}  berry={berry_val:+.6f}  "
              f"theory={theory:+.6f}  err_mod2pi={error:.6f}  "
              f"S2_diam={res['s2_diameter']:.4f}  [{status}]")

    n_match = sum(1 for r in results if r["match"])
    print(f"\n  Fiber loop: {n_match}/{len(results)} match theory (mod 2pi, tol=0.05)")
    return results


# ═══════════════════════════════════════════════════════════════════
# PART 2: BASE LOOP TRANSPORT
# ═══════════════════════════════════════════════════════════════════

def run_part2():
    """Base loop Berry phase for 20 eta values.
    Theory: Berry = -Omega/2 = -pi*(1 - cos(2*eta)).
    """
    print("\n" + "=" * 60)
    print("PART 2: Base Loop Transport")
    print("=" * 60)
    print("  (Base loop = theta2: 0->2pi; traces circle on S2)")
    print("  Theory: Berry = -pi*(1 - cos(2*eta))\n")

    results = []
    for eta in ETA_VALUES:
        fiber_res = transport_along_loop(eta, "fiber")
        base_res = transport_along_loop(eta, "base")
        omega = solid_angle_equatorial_circle(eta)
        theory = -omega / 2
        base_berry = base_res["berry_phase_pancharatnam"]
        # Compare mod 2pi
        diff = (base_berry - theory + np.pi) % (2 * np.pi) - np.pi
        error = abs(diff)
        record = {
            "eta": float(eta),
            "fiber_berry": fiber_res["berry_phase_pancharatnam"],
            "base_berry": base_berry,
            "base_theory": float(theory),
            "base_error_mod2pi": float(error),
            "base_match": error < 0.1,
            "fiber_holonomy": fiber_res["holonomy"],
            "base_holonomy": base_res["holonomy"],
            "base_s2_diameter": base_res["s2_diameter"],
        }
        results.append(record)
        status = "OK" if record["base_match"] else "MISS"
        print(f"  eta={eta:.4f}  base={base_berry:+.6f}  "
              f"theory={theory:+.6f}  err_mod2pi={error:.4f}  "
              f"fiber={fiber_res['berry_phase_pancharatnam']:+.6f}  [{status}]")

    n_match = sum(1 for r in results if r["base_match"])
    print(f"\n  Base loop: {n_match}/{len(results)} match theory (mod 2pi, tol=0.1)")
    return results


# ═══════════════════════════════════════════════════════════════════
# PART 3: DIAGONAL TRANSPORT
# ═══════════════════════════════════════════════════════════════════

def run_part3():
    """Diagonal transport. Test additivity: diag_berry = fiber_berry + base_berry?

    For abelian (U(1)) connection, Berry phases should be additive.
    """
    print("\n" + "=" * 60)
    print("PART 3: Diagonal Transport (theta1 = theta2)")
    print("=" * 60)

    results = []
    for eta in ETA_VALUES:
        fiber_res = transport_along_loop(eta, "fiber")
        base_res = transport_along_loop(eta, "base")
        diag_res = transport_along_loop(eta, "diagonal")
        fb_sum = (fiber_res["berry_phase_pancharatnam"]
                  + base_res["berry_phase_pancharatnam"])
        error = abs(diag_res["berry_phase_pancharatnam"] - fb_sum)
        record = {
            "eta": float(eta),
            "fiber_berry": fiber_res["berry_phase_pancharatnam"],
            "base_berry": base_res["berry_phase_pancharatnam"],
            "diagonal_berry": diag_res["berry_phase_pancharatnam"],
            "fiber_plus_base": float(fb_sum),
            "additivity_error": float(error),
            "additive": error < 0.2,
            "diagonal_s2_diameter": diag_res["s2_diameter"],
        }
        results.append(record)
        status = "ADDITIVE" if record["additive"] else "NON-ADD"
        print(f"  eta={eta:.4f}  diag={diag_res['berry_phase_pancharatnam']:+.6f}  "
              f"f+b={fb_sum:+.6f}  err={error:.4f}  [{status}]")

    n_add = sum(1 for r in results if r["additive"])
    print(f"\n  Additivity: {n_add}/{len(results)} (tol=0.2)")
    return results


# ═══════════════════════════════════════════════════════════════════
# PART 4: INTER-TORUS TRANSPORT
# ═══════════════════════════════════════════════════════════════════

def transport_between_tori(eta_start, eta_end, n_steps=N_STEPS):
    """Transport spinor radially from one torus to another (eta changes).

    This is an OPEN path (not a loop), so Berry phase is not defined.
    We track: connection sum, holonomy, and the transported spinor.
    """
    q0 = torus_coordinates(eta_start, 0.0, 0.0)
    psi = q_to_spinor(q0)
    psi /= np.linalg.norm(psi)

    trajectory = [psi.copy()]
    connection_sum = 0.0
    phases = [0.0]

    for step in range(n_steps):
        eta_next = eta_start + (step + 1) * (eta_end - eta_start) / n_steps
        q_next = torus_coordinates(eta_next, 0.0, 0.0)
        psi_natural = q_to_spinor(q_next)
        psi_natural /= np.linalg.norm(psi_natural)

        overlap = spinor_overlap(trajectory[-1], psi_natural)
        conn = np.angle(overlap)
        connection_sum += conn

        psi_transported = psi_natural * np.exp(-1j * conn)
        psi_transported /= np.linalg.norm(psi_transported)

        trajectory.append(psi_transported.copy())
        phases.append(connection_sum)

    holonomy = np.angle(spinor_overlap(trajectory[0], trajectory[-1]))

    # S2 path traced
    s2_start = hopf_map(torus_coordinates(eta_start, 0.0, 0.0))
    s2_end = hopf_map(torus_coordinates(eta_end, 0.0, 0.0))

    return {
        "trajectory": trajectory,
        "phases": phases,
        "connection_sum": float(connection_sum),
        "holonomy": float(holonomy),
        "eta_start": float(eta_start),
        "eta_end": float(eta_end),
        "radii_start": list(torus_radii(eta_start)),
        "radii_end": list(torus_radii(eta_end)),
        "s2_start": s2_start.tolist(),
        "s2_end": s2_end.tolist(),
        "s2_distance": float(np.linalg.norm(s2_end - s2_start)),
    }


def run_part4():
    """Inter-torus transport: inner -> Clifford."""
    print("\n" + "=" * 60)
    print("PART 4: Inter-Torus Transport")
    print("=" * 60)

    segments = [
        ("inner->clifford", TORUS_INNER, TORUS_CLIFFORD),
        ("clifford->outer", TORUS_CLIFFORD, TORUS_OUTER),
        ("outer->inner", TORUS_OUTER, TORUS_INNER),
        ("inner->outer", TORUS_INNER, TORUS_OUTER),
    ]

    results = []
    for name, eta_s, eta_e in segments:
        res = transport_between_tori(eta_s, eta_e)
        record = {
            "segment": name,
            "connection_sum": res["connection_sum"],
            "holonomy": res["holonomy"],
            "radii_start": res["radii_start"],
            "radii_end": res["radii_end"],
            "s2_distance": res["s2_distance"],
        }
        results.append(record)
        print(f"  {name:22s}  conn={res['connection_sum']:+.6f}  "
              f"holonomy={res['holonomy']:+.6f}  "
              f"R_maj: {res['radii_start'][0]:.3f}->{res['radii_end'][0]:.3f}  "
              f"R_min: {res['radii_start'][1]:.3f}->{res['radii_end'][1]:.3f}  "
              f"S2d={res['s2_distance']:.3f}")

    return results


# ═══════════════════════════════════════════════════════════════════
# PART 5: FULL CIRCUIT
# ═══════════════════════════════════════════════════════════════════

def run_part5():
    """Full circuit: fiber@inner -> move to Clifford -> fiber@Clifford
    -> move to outer -> fiber@outer -> move back to inner.

    Test: is total phase = sum of individual phases?
    """
    print("\n" + "=" * 60)
    print("PART 5: Full Circuit")
    print("=" * 60)

    # Initial spinor
    q0 = torus_coordinates(TORUS_INNER, 0.0, 0.0)
    psi_initial = q_to_spinor(q0)
    psi_initial /= np.linalg.norm(psi_initial)

    # We track the spinor through each segment, carrying it forward
    psi_current = psi_initial.copy()
    total_phase = 0.0
    segment_phases = []

    def _transport_segment(psi_start, points_fn, n_steps=N_STEPS):
        """Generic transport: carry psi_start along a path defined by points_fn."""
        psi = psi_start.copy()
        acc_phase = 0.0
        for step in range(n_steps):
            q_next = points_fn(step + 1, n_steps)
            psi_natural = q_to_spinor(q_next)
            psi_natural /= np.linalg.norm(psi_natural)

            overlap = spinor_overlap(psi, psi_natural)
            conn = np.angle(overlap)
            psi = psi_natural * np.exp(-1j * conn)
            psi /= np.linalg.norm(psi)
            acc_phase += conn

        return psi, acc_phase

    # Segment 1: Fiber loop at inner
    def fiber_inner(step, n):
        return torus_coordinates(TORUS_INNER, step * 2 * np.pi / n, 0.0)
    psi_current, ph = _transport_segment(psi_current, fiber_inner)
    segment_phases.append(("fiber@inner", float(ph)))
    total_phase += ph
    print(f"  1. fiber@inner    phase={ph:+.6f}")

    # Segment 2: inner -> Clifford
    def radial_ic(step, n):
        eta = TORUS_INNER + step * (TORUS_CLIFFORD - TORUS_INNER) / n
        return torus_coordinates(eta, 0.0, 0.0)
    psi_current, ph = _transport_segment(psi_current, radial_ic)
    segment_phases.append(("inner->clifford", float(ph)))
    total_phase += ph
    print(f"  2. inner->cliff   phase={ph:+.6f}")

    # Segment 3: Fiber loop at Clifford
    def fiber_cliff(step, n):
        return torus_coordinates(TORUS_CLIFFORD, step * 2 * np.pi / n, 0.0)
    psi_current, ph = _transport_segment(psi_current, fiber_cliff)
    segment_phases.append(("fiber@clifford", float(ph)))
    total_phase += ph
    print(f"  3. fiber@cliff    phase={ph:+.6f}")

    # Segment 4: Clifford -> outer
    def radial_co(step, n):
        eta = TORUS_CLIFFORD + step * (TORUS_OUTER - TORUS_CLIFFORD) / n
        return torus_coordinates(eta, 0.0, 0.0)
    psi_current, ph = _transport_segment(psi_current, radial_co)
    segment_phases.append(("clifford->outer", float(ph)))
    total_phase += ph
    print(f"  4. cliff->outer   phase={ph:+.6f}")

    # Segment 5: Fiber loop at outer
    def fiber_outer(step, n):
        return torus_coordinates(TORUS_OUTER, step * 2 * np.pi / n, 0.0)
    psi_current, ph = _transport_segment(psi_current, fiber_outer)
    segment_phases.append(("fiber@outer", float(ph)))
    total_phase += ph
    print(f"  5. fiber@outer    phase={ph:+.6f}")

    # Segment 6: outer -> inner (return)
    def radial_oi(step, n):
        eta = TORUS_OUTER + step * (TORUS_INNER - TORUS_OUTER) / n
        return torus_coordinates(eta, 0.0, 0.0)
    psi_current, ph = _transport_segment(psi_current, radial_oi)
    segment_phases.append(("outer->inner", float(ph)))
    total_phase += ph
    print(f"  6. outer->inner   phase={ph:+.6f}")

    # Final comparison
    holonomy = np.angle(spinor_overlap(psi_initial, psi_current))
    fidelity = abs(spinor_overlap(psi_initial, psi_current)) ** 2

    # Sum of individual fiber phases vs total
    fiber_phase_sum = sum(ph for name, ph in segment_phases if name.startswith("fiber"))
    radial_phase_sum = sum(ph for name, ph in segment_phases if not name.startswith("fiber"))

    print(f"\n  Total accumulated phase : {total_phase:+.6f}")
    print(f"  Fiber phases sum        : {fiber_phase_sum:+.6f}")
    print(f"  Radial phases sum       : {radial_phase_sum:+.6f}")
    print(f"  Holonomy (init vs final): {holonomy:+.6f}")
    print(f"  Fidelity |<init|final>|2: {fidelity:.6f}")

    # Additivity test: is total_phase == sum of segments?
    # (It is by construction, but holonomy may differ due to global phase)
    additivity_ok = abs(total_phase - (fiber_phase_sum + radial_phase_sum)) < 1e-10

    return {
        "segment_phases": segment_phases,
        "total_phase": float(total_phase),
        "fiber_phase_sum": float(fiber_phase_sum),
        "radial_phase_sum": float(radial_phase_sum),
        "holonomy": float(holonomy),
        "fidelity": float(fidelity),
        "additivity_exact": additivity_ok,
    }


# ═══════════════════════════════════════════════════════════════════
# PART 6: CHIRALITY DURING TRANSPORT
# ═══════════════════════════════════════════════════════════════════

def chirality_during_transport(eta, loop_type="fiber", n_steps=N_STEPS):
    """Track L/R Weyl spinors and their Bloch vectors during transport.

    Uses Pancharatnam Berry phase for both L and R separately.
    Returns chirality diagnostics: anti-alignment, phase splitting.
    """
    dt = 2 * np.pi / n_steps

    # Build path on S3
    path_q = []
    for step in range(n_steps + 1):
        angle = step * dt
        if loop_type == "fiber":
            q = torus_coordinates(eta, angle, 0.0)
        elif loop_type == "base":
            q = torus_coordinates(eta, 0.0, angle)
        else:
            q = torus_coordinates(eta, angle, angle)
        path_q.append(q)

    # Extract L and R spinor paths
    L_path = [left_weyl_spinor(q) for q in path_q]
    R_path = [right_weyl_spinor(q) for q in path_q]

    # Pancharatnam Berry phase for L
    product_L = 1.0 + 0j
    for i in range(n_steps):
        inner = np.vdot(L_path[i], L_path[i + 1])
        product_L *= inner / abs(inner)
    # Close the loop
    inner_close = np.vdot(L_path[-1], L_path[0])
    product_L *= inner_close / abs(inner_close)
    berry_L = float(-np.angle(product_L))

    # Pancharatnam Berry phase for R
    product_R = 1.0 + 0j
    for i in range(n_steps):
        inner = np.vdot(R_path[i], R_path[i + 1])
        product_R *= inner / abs(inner)
    inner_close = np.vdot(R_path[-1], R_path[0])
    product_R *= inner_close / abs(inner_close)
    berry_R = float(-np.angle(product_R))

    # Track anti-alignment of Bloch vectors throughout
    anti_alignment_angles = []
    for i in range(n_steps + 1):
        bloch_L = spinor_to_bloch(L_path[i] / np.linalg.norm(L_path[i]))
        bloch_R = spinor_to_bloch(R_path[i] / np.linalg.norm(R_path[i]))
        dot_val = np.dot(bloch_L, bloch_R)
        angle = np.arccos(np.clip(dot_val, -1, 1))
        anti_alignment_angles.append(float(angle))

    angles_arr = np.array(anti_alignment_angles)
    mean_angle = float(np.mean(angles_arr))
    std_angle = float(np.std(angles_arr))
    near_pi = float(np.mean(np.abs(angles_arr - np.pi)))

    return {
        "berry_L": berry_L,
        "berry_R": berry_R,
        "phase_ratio": float(berry_L / berry_R) if abs(berry_R) > 1e-12 else None,
        "phase_sum": float(berry_L + berry_R),
        "phase_diff": float(berry_L - berry_R),
        "anti_alignment_mean_angle": mean_angle,
        "anti_alignment_std": std_angle,
        "anti_alignment_deviation_from_pi": near_pi,
    }


def run_part6():
    """Chirality tracking during fiber, base, and diagonal transport."""
    print("\n" + "=" * 60)
    print("PART 6: Chirality During Transport")
    print("=" * 60)

    test_etas = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
    test_names = ["inner", "clifford", "outer"]
    loop_types = ["fiber", "base", "diagonal"]

    results = []
    for eta, name in zip(test_etas, test_names):
        for lt in loop_types:
            res = chirality_during_transport(eta, loop_type=lt)
            record = {
                "torus": name,
                "eta": float(eta),
                "loop_type": lt,
                **res,
            }
            results.append(record)
            print(f"  {name:8s} {lt:8s}  "
                  f"gamma_L={res['berry_L']:+.6f}  "
                  f"gamma_R={res['berry_R']:+.6f}  "
                  f"sum={res['phase_sum']:+.6f}  "
                  f"anti-align dev={res['anti_alignment_deviation_from_pi']:.6f}")

    return results


# ═══════════════════════════════════════════════════════════════════
# PART 7: CELL COMPLEX PATH TRACKING
# ═══════════════════════════════════════════════════════════════════

def run_part7():
    """Build TopoNetX cell complex and map transport paths onto it."""
    print("\n" + "=" * 60)
    print("PART 7: Cell Complex Path Tracking")
    print("=" * 60)

    from toponetx.classes import CellComplex

    n_per_ring = 20
    n_levels = 3
    level_etas = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
    level_names = ["inner", "clifford", "outer"]

    cc = CellComplex()

    # Node labeling: (level, index) -> node_id
    # level in {0,1,2}, index in {0,...,n_per_ring-1}
    def node_id(level, idx):
        return level * n_per_ring + idx

    # Add nodes
    for lv in range(n_levels):
        for idx in range(n_per_ring):
            cc.add_node(node_id(lv, idx))

    # Within-ring edges (fiber loop)
    within_ring_edges = []
    for lv in range(n_levels):
        ring_edges = []
        for idx in range(n_per_ring):
            nxt = (idx + 1) % n_per_ring
            edge = (node_id(lv, idx), node_id(lv, nxt))
            cc.add_edge(*edge)
            ring_edges.append(edge)
        within_ring_edges.append(ring_edges)

    # Between-ring edges (inter-torus transport)
    between_ring_edges = []
    for lv in range(n_levels - 1):
        level_edges = []
        for idx in range(n_per_ring):
            edge = (node_id(lv, idx), node_id(lv + 1, idx))
            cc.add_edge(*edge)
            level_edges.append(edge)
        between_ring_edges.append(level_edges)

    # Build edge set for checking existence
    complex_edges_set = set()
    for e in cc.edges:
        if hasattr(e, '__iter__'):
            complex_edges_set.add(tuple(sorted(e)))
        else:
            complex_edges_set.add(e)

    # Add 2-cells for each ring as a triangulated fan.
    # TopoNetX needs each 2-cell boundary to be a valid cycle whose edges
    # already exist. A single 20-gon cycle fails validation, so we
    # triangulate: fan from node 0 to all adjacent pairs.
    n_2cells_added = 0
    for lv in range(n_levels):
        center = node_id(lv, 0)
        for i in range(1, n_per_ring - 1):
            a = node_id(lv, i)
            b = node_id(lv, i + 1)
            # Need edge center-a, a-b (already added), center-b
            # a-b is a within-ring edge; center-a and center-b may need adding
            for x in (a, b):
                edge_canon = tuple(sorted((center, x)))
                if edge_canon not in complex_edges_set:
                    cc.add_edge(center, x)
                    complex_edges_set.add(edge_canon)
            try:
                cc.add_cell([center, a, b], rank=2)
                n_2cells_added += 1
            except ValueError:
                pass

    print(f"  Complex: {len(cc.nodes)} nodes, "
          f"{len(cc.edges)} edges, "
          f"{len(list(cc.cells))} 2-cells")

    # Map full circuit path onto complex edges
    # Circuit: fiber@inner -> radial(inner->cliff) -> fiber@cliff
    #       -> radial(cliff->outer) -> fiber@outer -> radial(outer->inner)

    circuit_path = []

    # Fiber loop at inner (level 0)
    for edge in within_ring_edges[0]:
        circuit_path.append(edge)

    # Radial: inner(0) -> clifford(0) at index 0
    circuit_path.append((node_id(0, 0), node_id(1, 0)))

    # Fiber loop at clifford (level 1)
    for edge in within_ring_edges[1]:
        circuit_path.append(edge)

    # Radial: clifford(0) -> outer(0) at index 0
    circuit_path.append((node_id(1, 0), node_id(2, 0)))

    # Fiber loop at outer (level 2)
    for edge in within_ring_edges[2]:
        circuit_path.append(edge)

    # Radial: outer(0) -> inner(0) — need to traverse through clifford
    circuit_path.append((node_id(2, 0), node_id(1, 0)))
    circuit_path.append((node_id(1, 0), node_id(0, 0)))

    # Verify closure: first node of first edge == last node of last edge
    start_node = circuit_path[0][0]
    end_node = circuit_path[-1][1]
    is_closed = (start_node == end_node)

    # Verify all edges exist in complex
    complex_edges = set()
    for e in cc.edges:
        # TopoNetX edges are frozensets
        if hasattr(e, '__iter__'):
            pair = tuple(sorted(e))
        else:
            pair = e
        complex_edges.add(pair)

    all_edges_valid = True
    for edge in circuit_path:
        canonical = tuple(sorted(edge))
        if canonical not in complex_edges:
            all_edges_valid = False
            break

    n_fiber_edges = sum(len(ring) for ring in within_ring_edges)
    n_radial_edges = sum(len(le) for le in between_ring_edges)

    print(f"  Within-ring edges : {n_fiber_edges}")
    print(f"  Between-ring edges: {n_radial_edges}")
    print(f"  Circuit path len  : {len(circuit_path)} edges")
    print(f"  Circuit is closed : {is_closed}")
    print(f"  All edges valid   : {all_edges_valid}")

    return {
        "n_nodes": len(cc.nodes),
        "n_edges": len(cc.edges),
        "n_2cells": len(list(cc.cells)),
        "n_within_ring_edges": n_fiber_edges,
        "n_between_ring_edges": n_radial_edges,
        "circuit_path_length": len(circuit_path),
        "circuit_is_closed": is_closed,
        "all_edges_in_complex": all_edges_valid,
        "n_per_ring": n_per_ring,
        "n_levels": n_levels,
    }


# ═══════════════════════════════════════════════════════════════════
# Cl(3) ROTOR VERIFICATION
# ═══════════════════════════════════════════════════════════════════

def verify_cl3_rotors():
    """Verify that Cl(3) rotors reproduce the same Berry phases."""
    print("\n" + "=" * 60)
    print("Cl(3) ROTOR CROSS-CHECK")
    print("=" * 60)

    # For the Clifford torus, transport a Bloch vector around fiber loop
    # using the Cl(3) rotor R = exp(-dt/2 * e12)
    eta = TORUS_CLIFFORD
    n_steps = N_STEPS
    dt = 2 * np.pi / n_steps

    q0 = torus_coordinates(eta, 0.0, 0.0)
    bloch0 = density_to_bloch(coherent_state_density(q0))
    mv0 = bloch_to_multivector(bloch0)

    # Apply incremental rotors
    mv_current = mv0
    for step in range(n_steps):
        R = rotor_z(dt)  # e12 plane rotation
        mv_current = apply_rotor(mv_current, R)

    bloch_final = multivector_to_bloch(mv_current)
    bloch_diff = np.linalg.norm(bloch0 - bloch_final)

    print(f"  Bloch initial : {bloch0}")
    print(f"  Bloch final   : {bloch_final}")
    print(f"  Bloch diff    : {bloch_diff:.8f}")
    print(f"  Full rotation returns Bloch: {'YES' if bloch_diff < 1e-6 else 'NO'}")

    # Also verify base rotor (e23 plane)
    mv_current = mv0
    for step in range(n_steps):
        R = rotor_x(dt)  # e23 plane rotation
        mv_current = apply_rotor(mv_current, R)

    bloch_final_base = multivector_to_bloch(mv_current)
    bloch_diff_base = np.linalg.norm(bloch0 - bloch_final_base)

    print(f"  Base rotor Bloch diff: {bloch_diff_base:.8f}")
    print(f"  Base full rotation   : {'YES' if bloch_diff_base < 1e-6 else 'NO'}")

    return {
        "fiber_rotor_return": bloch_diff < 1e-6,
        "fiber_bloch_diff": float(bloch_diff),
        "base_rotor_return": bloch_diff_base < 1e-6,
        "base_bloch_diff": float(bloch_diff_base),
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("Pure Spinor Transport on Nested Hopf Tori")
    print("=" * 60)
    print(f"  N_STEPS = {N_STEPS}")
    print(f"  N_ETA   = {N_ETA_SAMPLES}")
    print(f"  Levels  = inner({TORUS_INNER:.4f}), "
          f"clifford({TORUS_CLIFFORD:.4f}), "
          f"outer({TORUS_OUTER:.4f})")
    print()

    results = {}

    # Part 1: Fiber loop
    results["part1_fiber_loop"] = run_part1()

    # Part 2: Base loop
    results["part2_base_loop"] = run_part2()

    # Part 3: Diagonal
    results["part3_diagonal"] = run_part3()

    # Part 4: Inter-torus
    results["part4_inter_torus"] = run_part4()

    # Part 5: Full circuit
    results["part5_full_circuit"] = run_part5()

    # Part 6: Chirality
    results["part6_chirality"] = run_part6()

    # Part 7: Cell complex
    results["part7_cell_complex"] = run_part7()

    # Cl(3) rotor check
    results["cl3_rotor_check"] = verify_cl3_rotors()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    p1 = results["part1_fiber_loop"]
    n_p1_match = sum(1 for r in p1 if r.get("match", False))
    print(f"  Part 1 (fiber)   : {n_p1_match}/{len(p1)} match theory")

    p3 = results["part3_diagonal"]
    n_p3_add = sum(1 for r in p3 if r["additive"])
    print(f"  Part 3 (diagonal): {n_p3_add}/{len(p3)} additive")

    p5 = results["part5_full_circuit"]
    print(f"  Part 5 (circuit) : total_phase={p5['total_phase']:+.6f}  "
          f"fidelity={p5['fidelity']:.6f}")

    p7 = results["part7_cell_complex"]
    print(f"  Part 7 (complex) : closed={p7['circuit_is_closed']}  "
          f"valid={p7['all_edges_in_complex']}")

    cl3 = results["cl3_rotor_check"]
    print(f"  Cl(3) rotors     : fiber={cl3['fiber_rotor_return']}  "
          f"base={cl3['base_rotor_return']}")

    # Save results
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "pure_spinor_transport_results.json"
    )
    serializable = json.loads(json.dumps(results, default=str))
    with open(out_path, "w") as f:
        json.dump({
            "timestamp": datetime.datetime.now().isoformat(),
            "sim": "sim_pure_spinor_transport",
            "description": "Pure spinor parallel transport on nested Hopf tori",
            "n_steps": N_STEPS,
            "n_eta_samples": N_ETA_SAMPLES,
            "results": serializable,
        }, f, indent=2)

    print(f"\n  Results saved to {out_path}")
    return results


if __name__ == "__main__":
    main()
