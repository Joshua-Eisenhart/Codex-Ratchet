#!/usr/bin/env python3
"""
Tests for retrocausal_possibility_field_v4_irreducibility -- positive + negative +
boundary. The load-bearing object is the TV infimum over width-<=N_f forward Markov
kernels of the global compressor's output sequence-measure. The decisive tests:
  - the negative control (per-shell-independent selection) is REDUCIBLE (tv -> 0) in
    every swept family -> the test CAN fail (not rigged to always say 'irreducible');
  - a deliberately CROSS-COUPLED selection that cannot factor through width N_f is
    detected as IRREDUCIBLE -> the test CAN fire;
  - N_f is the MEASURED v3 fiber size; the embedding search is exhaustive; the verdict
    is reported honestly including family-dependence.

Run:  <sim-stack python3> tests/test_retrocausal_possibility_field_v4_irreducibility.py
Exits 0 only if every test passes.
"""

from __future__ import annotations

import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v4_irreducibility as v4  # noqa: E402

FAILURES: list[str] = []


def check(name: str, cond: bool) -> None:
    status = "PASS" if cond else "FAIL"
    if not cond:
        FAILURES.append(name)
    print(f"[{status}] {name}")


# =====================================================================
# N_f is measured from v3 (not stipulated)
# =====================================================================

def test_Nf_measured_from_v3() -> None:
    fiber = v4.measured_fiber_size_Nf()
    check("N_f: equals measured per-shell max fiber from v3", fiber["N_f"] == max(fiber["per_shell_max_fiber"]))
    check("N_f: is 3 on the canonical v3 carrier", fiber["N_f"] == 3)


# =====================================================================
# mu is a genuine sequence-distribution; the v3 separation under test still holds
# =====================================================================

def test_mu_is_distribution_and_v3_separation_holds() -> None:
    fam = v4.perturbation_family()
    sm = v4.build_sequence_measure(fam, v4.global_output_sequence)
    check("mu: spans >=2 distinct output sequences", len(sm["mu"]) >= 2)
    total = sum(sm["mu"].values())
    check("mu: normalizes to 1", abs(total - 1.0) < 1e-9)
    gate = v4.rpf_v3.acceptance_gate_differs_from_forward(
        {v4.SHELL_ORDER[i]: list(b) for i, b in enumerate(
            [["b1", "b6", "b7"], ["b0", "b4", "b5"], ["b2", "b3", "b8"]])},
        v4.rpf_v3.co_admissibility_relation(
            {v4.SHELL_ORDER[i]: list(b) for i, b in enumerate(
                [["b1", "b6", "b7"], ["b0", "b4", "b5"], ["b2", "b3", "b8"]])}),
        v4.rpf_v3.SHELLS,
    )
    check("v3 separation (b8 != b2) still holds", gate["differs_from_forward_selection"] is True)


# =====================================================================
# NEGATIVE CONTROL: per-shell-independent selection is REDUCIBLE (tv -> 0). The test
# can fail; it is NOT rigged to always return 'irreducible'.
# =====================================================================

def test_negative_control_is_reducible() -> None:
    fam = v4.perturbation_family()
    neg = v4.run_discriminator(fam, v4.reducible_output_sequence, 3, label="neg")
    check("negative: tv_infimum ~ 0 (<= threshold)", neg["tv_infimum"] <= v4.TV_THRESHOLD)
    check("negative: reported NOT irreducible", neg["irreducible_to_forward_hidden_state"] is False)
    check("negative: factors as width-N_f forward Markov",
          neg["tv_search"]["factors_as_width_Nf_forward_markov"] is True)


def test_negative_control_reducible_in_every_swept_family() -> None:
    sweep = v4.family_sensitivity_sweep(3)
    check("negative: reducible in EVERY swept family (machinery, not family, decides)",
          sweep["negative_control_reducible_in_every_family"] is True)


# =====================================================================
# POSITIVE FIRE TEST: a deliberately CROSS-COUPLED selection that cannot factor through
# width N_f must be detected as IRREDUCIBLE -> the test CAN fire. We construct a
# selection whose inner symbol is the XOR-like joint function of BOTH outer symbols with
# MORE than N_f effective previous-classes, so no width-N_f previous-class-only
# transition reproduces it.
# =====================================================================

def test_positive_fire_on_cross_coupled_selection() -> None:
    # Build a tiny synthetic family of length-3 sequences whose 3rd symbol depends on the
    # PAIR (x1, x2) in a way that needs > N_f classes of the previous symbol to predict.
    # Use N_f = 2 so the bound bites: 3rd symbol = f(x1, x2) where x2 alone (in <=2
    # classes) cannot determine it.
    import itertools as it
    seqs = []
    # x1 in {A,B}, x2 in {P,Q,R}; out = depends on (x1,x2) jointly with 6 distinct cells
    table = {
        ("A", "P"): "o0", ("A", "Q"): "o1", ("A", "R"): "o2",
        ("B", "P"): "o2", ("B", "Q"): "o0", ("B", "R"): "o1",
    }
    for (x1, x2), o in table.items():
        seqs.append((x1, x2, o))
    w = 1.0 / len(seqs)
    mu = {}
    for s in seqs:
        mu[s] = mu.get(s, 0.0) + w
    # With N_f = 2 the previous symbol x2 (3 values) must be merged into <=2 classes,
    # and x1 (2 values) likewise; no width-2 previous-class-only transition can carry
    # the joint (x1,x2)->out table -> tv_infimum > 0.
    tv2 = v4.tv_infimum_over_forward_markov(seqs, mu, w, 2)
    check("positive-fire: cross-coupled table is IRREDUCIBLE at N_f=2 (tv > threshold)",
          tv2["tv_infimum"] > v4.TV_THRESHOLD)
    check("positive-fire: does NOT factor as width-2 forward Markov",
          tv2["tv_search"]["factors_as_width_Nf_forward_markov"] is False
          if "tv_search" in tv2 else tv2["factors_as_width_Nf_forward_markov"] is False)


# =====================================================================
# The embedding search is exhaustive over deterministic <= N_f-class maps
# =====================================================================

def test_embedding_search_is_exhaustive() -> None:
    fam = v4.perturbation_family()
    sm = v4.build_sequence_measure(fam, v4.global_output_sequence)
    tv = v4.tv_infimum_over_forward_markov(sm["sequences"], sm["mu"], sm["weight_each"], 3)
    # number of deterministic embeddings of k symbols into N_f classes = N_f ** k
    expected = 3 ** tv["n_symbols"]
    check("exhaustive: searched N_f**n_symbols embeddings",
          tv["n_embeddings_searched"] == expected)


# =====================================================================
# BOUNDARY: a single-sequence (point-mass) family is trivially reducible (tv = 0)
# =====================================================================

def test_boundary_point_mass_is_reducible() -> None:
    seqs = [("b1", "b5", "b8")]
    mu = {("b1", "b5", "b8"): 1.0}
    tv = v4.tv_infimum_over_forward_markov(seqs, mu, 1.0, 3)
    check("boundary: a point-mass sequence-measure factors trivially (tv = 0)",
          tv["tv_infimum"] <= 1e-12)


def test_boundary_total_variation() -> None:
    check("boundary: TV of identical measures is 0",
          v4.total_variation({"a": 0.5, "b": 0.5}, {"a": 0.5, "b": 0.5}) == 0.0)
    check("boundary: TV of disjoint point masses is 1",
          abs(v4.total_variation({"a": 1.0}, {"b": 1.0}) - 1.0) < 1e-12)


# =====================================================================
# Result-level acceptance + ceiling
# =====================================================================

def test_result_all_pass_and_ceiling() -> None:
    result = v4.build_result()
    check("result: all_pass True", result["all_pass"] is True)
    check("result: all_invariants_hold True", result["all_invariants_hold"] is True)
    check("result: classification scratch_diagnostic",
          result["classification"] == "scratch_diagnostic")
    check("result: promotion_allowed False", result["promotion_allowed"] is False)
    check("result: formal_admission_allowed False", result["formal_admission_allowed"] is False)
    check("result: negative control reducible in every family",
          result["family_sensitivity_sweep"]["negative_control_reducible_in_every_family"] is True)
    # the honest verdict field exists and is consistent with the sweep
    check("result: irreducible flag consistent with primary tv vs threshold",
          result["irreducible_to_forward_hidden_state"] == (result["tv_infimum"] > result["threshold"]))


def main() -> int:
    test_Nf_measured_from_v3()
    test_mu_is_distribution_and_v3_separation_holds()
    test_negative_control_is_reducible()
    test_negative_control_reducible_in_every_swept_family()
    test_positive_fire_on_cross_coupled_selection()
    test_embedding_search_is_exhaustive()
    test_boundary_point_mass_is_reducible()
    test_boundary_total_variation()
    test_result_all_pass_and_ceiling()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("ALL TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
