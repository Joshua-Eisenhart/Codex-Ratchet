"""Classical baseline: Hopf U(1) fiber winding.

Mirrors the Hopf fibration's U(1) fiber by counting the winding number of
e^{i n theta} around the circle as theta goes 0->2pi. The winding number is
(1/2pi) * integral of d(arg) and must equal n for integer n.

scope_note: classical_baseline mirror of Hopf U(1) fiber
(ENGINE_MATH_REFERENCE.md Hopf/geometry section).
"""
import numpy as np
from _common import write_results


def winding_number(n, steps=4000):
    theta = np.linspace(0, 2 * np.pi, steps, endpoint=False)
    z = np.exp(1j * n * theta)
    arg = np.angle(z)
    d = np.diff(arg, append=arg[0])
    # unwrap jumps
    d = (d + np.pi) % (2 * np.pi) - np.pi
    return float(np.sum(d) / (2 * np.pi))


def run_positive():
    out = {}
    for n in (1, 2, 3, 5):
        w = winding_number(n)
        out[f"n{n}"] = {"winding": w, "pass": abs(w - n) < 1e-6}
    return out


def run_negative():
    # Winding of a constant loop (n=0) is 0, not 1.
    w = winding_number(0)
    return {"constant_is_zero": {"winding": w, "pass": abs(w) < 1e-9}}


def run_boundary():
    # Negative winding: n=-1 should give -1.
    w = winding_number(-1)
    return {"neg_winding": {"winding": w, "pass": abs(w + 1) < 1e-6}}


if __name__ == "__main__":
    write_results(
        "sim_classical_hopf_u1_fiber_winding",
        "classical_baseline mirror of Hopf U(1) fiber winding (ENGINE_MATH_REFERENCE.md)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_hopf_u1_fiber_winding_results.json",
    )
