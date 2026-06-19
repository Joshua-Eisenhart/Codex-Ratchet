#!/usr/bin/env python3
"""Contract tests for rpf_v5_broader_irreducibility."""

from __future__ import annotations

import importlib.util
import os
import sys


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(TESTS_DIR)
MODULE_PATH = os.path.join(SIM_DIR, "rpf_v5_broader_irreducibility.py")


def _mod():
    spec = importlib.util.spec_from_file_location("rpf_v5", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


FAILURES: list[str] = []


def check(name: str, cond: bool) -> None:
    print(("PASS" if cond else "FAIL") + " " + name)
    if not cond:
        FAILURES.append(name)


def test_negative_controls_fit():
    m = _mod()
    toy = m.fit_stochastic_hmm_tv(m.toy_negative_sequences(), [1, 2, 3], restarts=4, max_iter=160, seed=1)
    grounded = m.fit_stochastic_hmm_tv(m.grounded_negative_sequences(), [1, 3, 6], restarts=4, max_iter=160, seed=2)
    check("toy negative control tv near zero", toy["tv_infimum_estimate"] <= 1e-8)
    check("grounded negative control tv near zero", grounded["tv_infimum_estimate"] <= 1e-8)


def test_hidden_sweep_shape_and_Nf():
    m = _mod()
    check("toy N_f is inherited from v4 as 3", m.v4.measured_fiber_size_Nf()["N_f"] == 3)
    check("grounded N_f is measured as 6", m.measured_grounded_Nf()["N_f"] == 6)
    check("toy hidden sweep reaches 2*N_f", max(m.hidden_counts(3)) == 6)
    check("grounded hidden sweep reaches 2*N_f", max(m.hidden_counts(6)) == 12)


def test_result_ceiling_and_status_consistency():
    m = _mod()
    result = m.build_result(restarts=6, max_iter=180)
    toy_open = result["cases"]["toy_v3_global"]["stochastic_hmm_fit"]["irreducible_under_stochastic_hmm"]
    grounded_open = result["cases"]["grounded_M_C_global"]["stochastic_hmm_fit"]["irreducible_under_stochastic_hmm"]
    check("classification scratch_diagnostic", result["classification"] == "scratch_diagnostic")
    check("promotion disallowed", result["promotion_allowed"] is False)
    check("formal admission disallowed", result["formal_admission_allowed"] is False)
    check("negative controls pass", result["negative_controls_pass"] is True)
    check("status matches carrier openness",
          result["strong_retrocausal_global_claim_status"] == ("OPEN" if (toy_open or grounded_open) else "KILLED"))


def main() -> int:
    test_negative_controls_fit()
    test_hidden_sweep_shape_and_Nf()
    test_result_ceiling_and_status_consistency()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("ALL TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
