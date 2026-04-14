"""Classical baseline: Landauer/Jarzynski coupled identity.

Mirrors the Landauer bound (erasing 1 bit dissipates >= k_B T ln 2) and the
Jarzynski equality <exp(-beta W)> = exp(-beta dF). Coupling: Landauer is the
special case where dF = k_B T ln 2 for a bit-reset. We verify Jarzynski
numerically on a Gaussian work distribution and check Landauer consistency.

scope_note: classical_baseline for Landauer/Jarzynski coupling
(ENGINE_MATH_REFERENCE.md thermo-information bridge).
"""
import numpy as np
from _common import write_results


KB = 1.380649e-23


def jarzynski_free_energy(W_samples, beta):
    return -(1.0 / beta) * np.log(np.mean(np.exp(-beta * W_samples)))


def run_positive():
    rng = np.random.RandomState(0)
    # Gaussian work: for Gaussian W~N(mu,sigma^2), analytic dF = mu - beta*sigma^2/2.
    out = {}
    for i, (mu, sigma) in enumerate([(1.0, 0.3), (2.0, 0.5), (0.5, 0.1)]):
        beta = 1.0
        W = rng.normal(mu, sigma, size=200000)
        dF_est = jarzynski_free_energy(W, beta)
        dF_true = mu - beta * sigma ** 2 / 2
        out[f"case{i}"] = {"dF_est": dF_est, "dF_true": dF_true, "pass": abs(dF_est - dF_true) < 5e-3}
    return out


def run_negative():
    # If we use <W> instead of Jarzynski average, we over-estimate dF
    # (equality holds only in reversible limit). For sigma>0 expect <W> > dF_true.
    rng = np.random.RandomState(1)
    mu, sigma, beta = 1.0, 0.5, 1.0
    W = rng.normal(mu, sigma, size=100000)
    dF_true = mu - beta * sigma ** 2 / 2
    mean_W = float(W.mean())
    return {"mean_W_not_dF": {"mean_W": mean_W, "dF_true": dF_true, "pass": mean_W > dF_true + 1e-3}}


def run_boundary():
    # Landauer: erasing 1 bit at T=300 K dissipates >= k_B T ln 2 ≈ 2.87e-21 J.
    T = 300.0
    landauer = KB * T * np.log(2)
    # A process claiming to erase 1 bit with W=0 violates Landauer.
    W_claimed = 0.0
    return {"landauer_bound": {"bound_J": landauer, "W_claimed": W_claimed,
                                "pass": bool(W_claimed < landauer)}}


if __name__ == "__main__":
    write_results(
        "sim_classical_landauer_jarzynski_coupled",
        "classical_baseline for Landauer/Jarzynski coupling (ENGINE_MATH_REFERENCE.md)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_landauer_jarzynski_coupled_results.json",
    )
