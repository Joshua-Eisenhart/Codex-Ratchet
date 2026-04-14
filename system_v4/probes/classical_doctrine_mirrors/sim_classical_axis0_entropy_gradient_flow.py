"""Classical baseline: Axis 0 entropy gradient flow.

Mirrors owner doctrine (Entropic Monism): time = entropy increasing.
Classical analog: gradient ascent on Shannon entropy of a 1D categorical
distribution moves toward the uniform maximum-entropy point. This is a
classical stand-in for Axis 0 = ∇I_c, not the nonclassical object itself.

scope_note: classical_baseline; mirrors OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md
(space=entropy, time=entropy increasing) and ENGINE_MATH_REFERENCE.md Axis 0
= entropy gradient. Non-canonical by construction (numpy-only, no PyG autograd).
"""
import numpy as np
from _common import write_results


def shannon(p):
    p = np.clip(p, 1e-12, 1.0)
    return float(-np.sum(p * np.log(p)))


def ascend(p0, lr=0.05, steps=200):
    p = p0.copy()
    traj = [shannon(p)]
    for _ in range(steps):
        # grad of H wrt p_i is -(log p_i + 1); project to simplex by softmax
        g = -(np.log(np.clip(p, 1e-12, 1.0)) + 1.0)
        p = p + lr * g
        p = np.clip(p, 1e-9, None)
        p = p / p.sum()
        traj.append(shannon(p))
    return p, traj


def run_positive():
    out = {}
    for n in (3, 5, 8):
        p0 = np.random.RandomState(n).dirichlet(np.ones(n) * 0.3)
        pf, traj = ascend(p0)
        uniform = np.full(n, 1.0 / n)
        out[f"n{n}"] = {
            "H_initial": traj[0],
            "H_final": traj[-1],
            "H_uniform": shannon(uniform),
            "monotonic_nondecreasing": bool(all(traj[i] <= traj[i + 1] + 1e-9 for i in range(len(traj) - 1))),
            "close_to_uniform": bool(np.allclose(pf, uniform, atol=1e-2)),
            "pass": bool(traj[-1] > traj[0] and np.allclose(pf, uniform, atol=1e-2)),
        }
    return out


def run_negative():
    # Gradient DESCENT should NOT reach uniform; entropy should decrease.
    p0 = np.array([0.2, 0.3, 0.5])
    p = p0.copy()
    H0 = shannon(p)
    for _ in range(200):
        g = -(np.log(np.clip(p, 1e-12, 1.0)) + 1.0)
        p = p - 0.05 * g
        p = np.clip(p, 1e-9, None); p = p / p.sum()
    Hf = shannon(p)
    return {"descent_decreases_H": {"H0": H0, "Hf": Hf, "pass": bool(Hf < H0)}}


def run_boundary():
    # Already-uniform input stays ~uniform; gradient vanishes.
    n = 4
    p0 = np.full(n, 1.0 / n)
    pf, traj = ascend(p0, lr=0.05, steps=50)
    return {"uniform_fixed_point": {
        "drift": float(np.linalg.norm(pf - p0)),
        "pass": bool(np.linalg.norm(pf - p0) < 1e-6),
    }}


if __name__ == "__main__":
    write_results(
        "sim_classical_axis0_entropy_gradient_flow",
        "classical_baseline mirror of Axis 0 entropy-gradient (OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md, ENGINE_MATH_REFERENCE.md)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_axis0_entropy_gradient_flow_results.json",
    )
