"""Classical baseline: FEP active inference step.

Mirrors owner doctrine "FEP as literal physics mirror". Classical analog:
Gaussian variational free energy F(q) = KL(q||p) between approximate posterior
q=N(mu,sigma^2) and true posterior p=N(mu*,sigma*^2). One active-inference
step (gradient descent on mu) should reduce F.

scope_note: classical_baseline mirror of FEP active inference
(OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md FEP doctrine).
"""
import numpy as np
from _common import write_results


def kl_gauss(mu_q, s_q, mu_p, s_p):
    return float(np.log(s_p / s_q) + (s_q ** 2 + (mu_q - mu_p) ** 2) / (2 * s_p ** 2) - 0.5)


def step(mu_q, s_q, mu_p, s_p, lr=0.1):
    # dF/dmu_q = (mu_q - mu_p) / s_p^2
    g = (mu_q - mu_p) / s_p ** 2
    return mu_q - lr * g


def run_positive():
    out = {}
    for i, (mq, mp) in enumerate([(2.0, 0.0), (-3.0, 1.0), (5.0, 4.5)]):
        F0 = kl_gauss(mq, 1.0, mp, 1.0)
        mq2 = step(mq, 1.0, mp, 1.0)
        F1 = kl_gauss(mq2, 1.0, mp, 1.0)
        out[f"case{i}"] = {"F_before": F0, "F_after": F1, "pass": F1 < F0}
    return out


def run_negative():
    # Moving AWAY from mu_p should INCREASE F.
    mq, mp = 0.0, 0.0
    F0 = kl_gauss(mq, 1.0, mp, 1.0)
    mq2 = mq + 1.0  # step away
    F1 = kl_gauss(mq2, 1.0, mp, 1.0)
    return {"away_increases_F": {"F_before": F0, "F_after": F1, "pass": F1 > F0}}


def run_boundary():
    # Already at posterior mean: step is zero, F unchanged.
    mq, mp = 3.0, 3.0
    F0 = kl_gauss(mq, 1.0, mp, 1.0)
    mq2 = step(mq, 1.0, mp, 1.0)
    F1 = kl_gauss(mq2, 1.0, mp, 1.0)
    return {"fixed_point": {"delta_mu": abs(mq2 - mq), "pass": abs(mq2 - mq) < 1e-12 and abs(F1 - F0) < 1e-12}}


if __name__ == "__main__":
    write_results(
        "sim_classical_fep_active_inference_step",
        "classical_baseline mirror of FEP active inference (OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md FEP doctrine)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_fep_active_inference_step_results.json",
    )
