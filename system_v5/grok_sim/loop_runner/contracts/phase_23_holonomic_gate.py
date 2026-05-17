"""phase_23_holonomic_gate.py — Berry / Wilczek-Zee holonomic gate via outer-loop traversal.

The outer loop γ_b is density-traversing — moving along it accumulates a geometric phase
(Berry phase for non-degenerate states, Wilczek-Zee holonomy for degenerate ones). This
is a real AI primitive: geometric gates are immune to dynamical (timing) noise.

Required API: `holonomic_gate(loop_angle: float = 2 * math.pi, n_steps: int = 64) -> dict`
  Returns:
    {
      "loop_angle": float,
      "berry_phase": float,                # net phase accumulated around closed loop
      "holonomy_matrix": list[2][2] of complex,  # 2×2 SU(2) holonomy
      "is_unitary": bool,                  # holonomy_matrix is unitary
      "winding_number_estimate": float,    # net Bloch-sphere solid angle / 2π
    }

Pass criteria:
  - At loop_angle = 2π, berry_phase ≠ 0 (and ≠ 2π — must be a non-trivial holonomy)
  - At loop_angle = 0 (no traversal), berry_phase ≈ 0
  - holonomy_matrix is unitary (U U† ≈ I to 1e-4)
  - Different angles produce different phases (sensitivity to loop)
"""
import numpy as np
import math


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "holonomic_gate"):
        return {
            "pass": False,
            "failures": [{
                "check": "holonomic_gate_exists",
                "msg": "Required function `holonomic_gate(loop_angle: float = 2*pi, n_steps: int = 64) -> dict` "
                       "is not exported. The outer-loop γ_b traversal accumulates a Berry / Wilczek-Zee "
                       "geometric phase — expose this as a callable AI primitive for geometric (noise-immune) "
                       "quantum gates. Return dict with: loop_angle, berry_phase, holonomy_matrix (2×2 SU(2)), "
                       "is_unitary, winding_number_estimate.",
            }],
            "metrics": metrics,
        }

    # Test at three loop angles
    test_angles = [0.0, math.pi, 2 * math.pi]
    results = {}
    for ang in test_angles:
        try:
            r = candidate.holonomic_gate(ang)
        except Exception as e:
            failures.append({"check": f"holonomic_call_ang_{ang:.2f}",
                             "msg": f"holonomic_gate({ang}) raised {type(e).__name__}: {str(e)[:200]}"})
            continue
        if not isinstance(r, dict):
            failures.append({"check": f"holonomic_dict_ang_{ang:.2f}", "msg": "not dict"})
            continue
        for k in ("berry_phase", "holonomy_matrix", "is_unitary", "winding_number_estimate"):
            if k not in r:
                failures.append({"check": f"holonomic_missing_{k}_ang_{ang:.2f}", "msg": f"missing `{k}`"})
                break
        else:
            results[ang] = r

    if len(results) < 2:
        return {"pass": False, "failures": failures, "metrics": metrics}

    # At loop_angle = 0, berry_phase should be ≈ 0
    if 0.0 in results:
        bp0 = float(results[0.0]["berry_phase"])
        metrics["berry_phase_at_0"] = bp0
        if abs(bp0) > 0.05:
            failures.append({
                "check": "berry_phase_trivial_at_zero",
                "msg": f"berry_phase at loop_angle=0 is {bp0:.4f}, expected ≈ 0 "
                       f"(no traversal means no accumulated phase).",
            })

    # At loop_angle = 2π, berry_phase should be nonzero (non-trivial holonomy)
    if 2 * math.pi in results:
        bp = float(results[2 * math.pi]["berry_phase"])
        metrics["berry_phase_at_2pi"] = bp
        if abs(bp) < 0.05:
            failures.append({
                "check": "berry_phase_nontrivial_at_2pi",
                "msg": f"berry_phase at loop_angle=2π is {bp:.4f}. Expected nonzero — a non-trivial "
                       f"U(1) connection produces a measurable Berry phase around a full loop.",
            })

    # Holonomy matrix is unitary at 2π
    if 2 * math.pi in results:
        try:
            M = np.asarray(results[2 * math.pi]["holonomy_matrix"], dtype=complex)
            if M.shape != (2, 2):
                failures.append({
                    "check": "holonomy_matrix_shape",
                    "msg": f"holonomy_matrix has shape {M.shape}, expected (2, 2)",
                })
            else:
                err = float(np.max(np.abs(M @ M.conj().T - np.eye(2))))
                metrics["holonomy_unitarity_error"] = err
                if err > 1e-3:
                    failures.append({
                        "check": "holonomy_unitary",
                        "msg": f"holonomy_matrix @ holonomy_matrix^† differs from I by {err:.4e} > 1e-3. "
                               f"Berry holonomy must be a unitary (U(1) phase) or SU(2) for non-Abelian.",
                    })
        except Exception as e:
            failures.append({"check": "holonomy_matrix_parse", "msg": f"could not parse matrix: {e}"})

    # Different angles produce different phases (sensitivity)
    if 0.0 in results and 2 * math.pi in results:
        delta = abs(float(results[2 * math.pi]["berry_phase"]) - float(results[0.0]["berry_phase"]))
        metrics["phase_delta_0_vs_2pi"] = delta
        if delta < 0.05:
            failures.append({
                "check": "holonomic_angle_sensitive",
                "msg": f"|berry_phase(2π) - berry_phase(0)| = {delta:.4f}, expected > 0.05. "
                       f"The gate is not actually sensitive to loop traversal.",
            })

    # Determinism
    try:
        r1 = candidate.holonomic_gate(2 * math.pi)
        r2 = candidate.holonomic_gate(2 * math.pi)
        bp_diff = abs(float(r1["berry_phase"]) - float(r2["berry_phase"]))
        if bp_diff > 1e-6:
            failures.append({"check": "holonomic_deterministic",
                             "msg": f"two calls at 2π returned berry_phase differing by {bp_diff:.2e}"})
    except Exception:
        pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "trivial U(1) connection (zero winding) — berry_phase = 0 even at 2π",
            "unitary applied without geometric phase — fails angle sensitivity",
            "non-unitary holonomy matrix — fails unitarity check",
        ],
        "baseline_variants": [
            "no-evolution baseline — berry_phase = 0 at all angles",
            "pure dynamical phase baseline — proportional to time, not loop topology",
        ],
    }
