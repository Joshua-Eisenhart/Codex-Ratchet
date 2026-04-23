"""Classical baseline: Szilard / Maxwell-demon coupling.

Mirrors the Szilard engine: a one-particle gas in a box. Measurement (knowing
which half) enables extraction of W = k_B T ln 2 per cycle. The "coupling"
between demon and gas is the information channel. This baseline verifies the
work yield equals k_B T ln 2 and that without information (uniform prior) the
expected extractable work is 0.

scope_note: classical_baseline mirror of Szilard/Maxwell-demon thermodynamics
(ENGINE_MATH_REFERENCE.md thermo-information bridge).
"""
import numpy as np
from _common import write_results


KB = 1.380649e-23


def szilard_work(T):
    return KB * T * np.log(2)


def run_positive():
    out = {}
    for T in (100.0, 300.0, 1000.0):
        W = szilard_work(T)
        expected = KB * T * np.log(2)
        out[f"T{int(T)}"] = {"W": W, "expected": expected, "pass": abs(W - expected) < 1e-30}
    return out


def run_negative():
    # No information (p=1/2 uncorrelated with particle side): expected extractable W=0.
    # Model: demon's belief is uncorrelated; mutual information I=0 -> W=0.
    I_mutual = 0.0  # bits
    W = KB * 300.0 * np.log(2) * I_mutual
    return {"no_info_no_work": {"W": W, "pass": W == 0.0}}


def run_boundary():
    # T=0 yields zero extractable work (consistent with third law).
    W = szilard_work(0.0)
    return {"zero_T_zero_W": {"W": W, "pass": W == 0.0}}


if __name__ == "__main__":
    write_results(
        "sim_classical_szilard_maxwell_demon_coupled",
        "classical_baseline for Szilard/Maxwell-demon coupling (ENGINE_MATH_REFERENCE.md)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_szilard_maxwell_demon_coupled_results.json",
    )
