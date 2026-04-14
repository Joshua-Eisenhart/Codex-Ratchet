"""Classical baseline: Axis 6 action handedness.

Mirrors Axis 6 handedness (CW vs CCW outer-ring traversal) as a signed area /
Levi-Civita classical analog. A closed 2D loop has signed area whose sign
distinguishes CW from CCW orientation.

scope_note: classical_baseline; mirrors ENGINE_MATH_REFERENCE.md Axis 6 handedness
(Weyl chirality) and OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md handedness rule.
"""
import numpy as np
from _common import write_results


def signed_area(pts):
    x = pts[:, 0]; y = pts[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def circle(n=64, ccw=True):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    if not ccw:
        t = -t
    return np.stack([np.cos(t), np.sin(t)], axis=1)


def run_positive():
    return {
        "ccw_positive":  {"area": signed_area(circle(ccw=True)),  "pass": signed_area(circle(ccw=True))  > 0},
        "cw_negative":   {"area": signed_area(circle(ccw=False)), "pass": signed_area(circle(ccw=False)) < 0},
        "flip_inverts":  {"pass": bool(np.isclose(signed_area(circle(ccw=True)), -signed_area(circle(ccw=False))))},
    }


def run_negative():
    # A self-retracing path has ~zero signed area (not a valid handed loop).
    t = np.linspace(0, np.pi, 32)
    back = np.stack([np.cos(t), np.sin(t)], axis=1)
    forth = back[::-1]
    pts = np.concatenate([back, forth])
    a = signed_area(pts)
    return {"degenerate_no_handedness": {"area": a, "pass": abs(a) < 1e-9}}


def run_boundary():
    # Tiny loop still has correct sign.
    small = 1e-6 * circle(ccw=True)
    a = signed_area(small)
    return {"tiny_ccw_still_positive": {"area": a, "pass": a > 0}}


if __name__ == "__main__":
    write_results(
        "sim_classical_axis6_action_handedness",
        "classical_baseline mirror of Axis 6 handedness via signed area (ENGINE_MATH_REFERENCE.md)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_axis6_action_handedness_results.json",
    )
