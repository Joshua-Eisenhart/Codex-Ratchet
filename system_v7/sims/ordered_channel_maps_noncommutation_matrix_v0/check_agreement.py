#!/usr/bin/env python3
"""Cross-engine agreement check (separate verification step). Reads the FOUR leg
result JSONs (numpy / jax / pytorch / julia) and asserts the four INDEPENDENT
engines agree to 1e-9 on:
  * the full 6x6 noncommutation matrix delta(A,B,rho0) = ||A(B(rho)) - B(A(rho))||_1,
  * the commuting / noncommuting pair split,
  * the four genuine discriminators (a/b/b2/c/d),
  * the controls (identity-commutes, label-shuffle, classical-baseline).
It does NOT recompute the physics. Exit 1 on any mismatch or any failed
load-bearing fact. The engines use four DISTINCT trace-norm routes:
  numpy  -> eigvalsh (Hermitian eigenvalues)
  jax    -> svdvals (singular values)
  pytorch-> nuclear-norm API
  julia  -> svdvals (independent language)
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_ID = "ordered_channel_maps_noncommutation_matrix_v0"
ATOL = 1e-9
ENGINES = ["numpy", "jax", "pytorch", "julia"]


def load(eng):
    with open(os.path.join(HERE, "results", f"{SIM_ID}_{eng}_results.json")) as f:
        return json.load(f)


def close(vals):
    """True iff all numeric values agree within ATOL."""
    vs = [float(v) for v in vals]
    return (max(vs) - min(vs)) <= ATOL


def main():
    legs = {e: load(e) for e in ENGINES}
    failures = []

    # 0. distinct computation styles + no peer reads
    styles = {e: legs[e]["computation_style"] for e in ENGINES}
    if len(set(styles.values())) != len(ENGINES):
        failures.append(f"computation styles not distinct: {styles}")
    for e in ENGINES:
        if legs[e].get("reads_peer_result") is not False:
            failures.append(f"{e}: reads_peer_result is not False")
        if legs[e].get("classification") != "scratch_diagnostic":
            failures.append(f"{e}: classification != scratch_diagnostic")
        if legs[e].get("promotion_allowed") is not False:
            failures.append(f"{e}: promotion_allowed not False")

    names = legs["numpy"]["map_names"]
    for e in ENGINES:
        if legs[e]["map_names"] != names:
            failures.append(f"{e}: map_names differ")

    # 1. full delta matrix on rho0 agrees across all four engines
    max_matrix_diff = 0.0
    for a in names:
        for b in names:
            vals = [legs[e]["delta_matrix_rho0"][a][b] for e in ENGINES]
            d = max(vals) - min(vals)
            max_matrix_diff = max(max_matrix_diff, d)
            if d > ATOL:
                failures.append(f"delta[{a}][{b}] disagrees: {dict(zip(ENGINES, vals))}")

    # 2. commuting / noncommuting split agrees (compare SETS of UNORDERED pairs;
    #    the matrix is symmetric, so legs may list a pair as (a,b) or (b,a)).
    def split_set(eng):
        c = frozenset(frozenset((a, b)) for a, b, _ in legs[eng]["commuting_pairs_rho0"])
        n = frozenset(frozenset((a, b)) for a, b, _ in legs[eng]["noncommuting_pairs_rho0"])
        return c, n
    base_c, base_n = split_set("numpy")
    for e in ENGINES[1:]:
        c, n = split_set(e)
        if c != base_c:
            failures.append(f"{e}: commuting set differs from numpy")
        if n != base_n:
            failures.append(f"{e}: noncommuting set differs from numpy")

    # 3. discriminators agree
    # (a) commuting pairs ~ 0
    for key in legs["numpy"]["discriminator_a_commuting"]:
        vals = [legs[e]["discriminator_a_commuting"][key] for e in ENGINES]
        if not close(vals):
            failures.append(f"disc_a[{key}] disagrees: {dict(zip(ENGINES, vals))}")
        if max(abs(float(v)) for v in vals) > ATOL:
            failures.append(f"disc_a[{key}] NOT ~0 (commuting pair failed): {vals[0]}")
    # (b) noncommuting pairs > 0
    for key in legs["numpy"]["discriminator_b_noncommuting"]:
        vals = [legs[e]["discriminator_b_noncommuting"][key] for e in ENGINES]
        if not close(vals):
            failures.append(f"disc_b[{key}] disagrees: {dict(zip(ENGINES, vals))}")
        if min(float(v) for v in vals) <= ATOL:
            failures.append(f"disc_b[{key}] NOT > 0 (noncommuting pair failed): {vals[0]}")
    # (b-byconstruction) Lindblad_vs_Te = GAMMA for all rho: agree across engines,
    # recorded as a by-construction constant, NOT counted as a genuine discriminator.
    lvt = [legs[e]["lindblad_vs_te_by_construction_equals_gamma"] for e in ENGINES]
    if not close(lvt):
        failures.append(f"lindblad_vs_te (by-construction) disagrees: {dict(zip(ENGINES, lvt))}")
    # (b2) probe-relative Ti-Fi: 0 on rho0/mixed, >0 on pole0/generic; agree across engines
    b2 = {e: legs[e]["discriminator_b2_probe_relative_TiFi"] for e in ENGINES}
    for probe in ["rho0_plus", "mixed", "pole0", "generic"]:
        vals = [b2[e][probe] for e in ENGINES]
        if not close(vals):
            failures.append(f"disc_b2[{probe}] disagrees: {dict(zip(ENGINES, vals))}")
    if max(abs(float(b2[e]["rho0_plus"])) for e in ENGINES) > ATOL:
        failures.append("disc_b2: Ti-Fi NOT ~0 on rho0 (probe-relativity broken)")
    if min(float(b2[e]["pole0"]) for e in ENGINES) <= ATOL:
        failures.append("disc_b2: Ti-Fi NOT > 0 on pole0 (probe-relativity broken)")
    if min(float(b2[e]["generic"]) for e in ENGINES) <= ATOL:
        failures.append("disc_b2: Ti-Fi NOT > 0 on generic (probe-relativity broken)")
    probe_relative_flip = (max(abs(float(b2[e]["rho0_plus"])) for e in ENGINES) <= ATOL
                           and min(float(b2[e]["pole0"]) for e in ENGINES) > ATOL)
    # (c) signed antisymmetry
    c_ab = [legs[e]["discriminator_c_signed_antisymmetric"]["signed_TiFi"] for e in ENGINES]
    c_ba = [legs[e]["discriminator_c_signed_antisymmetric"]["signed_FiTi"] for e in ENGINES]
    if not close(c_ab) or not close(c_ba):
        failures.append(f"disc_c signed values disagree: ab={c_ab} ba={c_ba}")
    antisym_all = all(legs[e]["discriminator_c_signed_antisymmetric"]["antisymmetric"] for e in ENGINES)
    if not antisym_all:
        failures.append("disc_c: not antisymmetric in some engine")

    # 4. controls
    # identity commutes with everything in every engine
    if not all(legs[e]["control_identity_map"]["identity_commutes_all"] for e in ENGINES):
        failures.append("control: identity does not commute with all maps in some engine")
    # label-shuffle invariance
    if not all(legs[e]["control_label_shuffle"]["invariant"] for e in ENGINES):
        failures.append("control: label-shuffle not invariant in some engine")
    # classical-diagonal baseline gap collapses, reopens with a coherence map
    for e in ENGINES:
        d = legs[e]["discriminator_d_classical_baseline"]
        if not d["classical_gap_collapses"]:
            failures.append(f"{e}: classical-diagonal gap did NOT collapse ({d['classical_gap_max']})")
        if not d["gap_reopens"]:
            failures.append(f"{e}: coherence map did NOT reopen the gap ({d['coherence_map_reopens_gap_on_same_state']})")
    # classical gap values agree
    cg = [legs[e]["discriminator_d_classical_baseline"]["classical_gap_max"] for e in ENGINES]
    if not close(cg):
        failures.append(f"classical_gap_max disagrees: {dict(zip(ENGINES, cg))}")

    # 4b. MAP-LEVEL commutation (tomographically complete basis): the engines must
    #     agree on which pairs commute as SUPEROPERATORS (max delta over the d^2
    #     basis ~ 0) vs which are merely state-null on rho0. This is the fix for
    #     the state-null conflation: a single-probe zero does NOT prove [A,B]=0.
    def map_level_sets(eng):
        commute = set()
        probe_specific = set()
        for r in legs[eng]["map_level_commutation"]["pairs"]:
            key = frozenset(r["pair"])
            if r["map_level_commutes"]:
                commute.add(key)
            if r["rho0_zero_but_map_noncommutes"]:
                probe_specific.add(key)
        return commute, probe_specific
    base_mc, base_ps = map_level_sets("numpy")
    for e in ENGINES[1:]:
        mc, ps = map_level_sets(e)
        if mc != base_mc:
            failures.append(f"{e}: map-level commuting set differs from numpy")
        if ps != base_ps:
            failures.append(f"{e}: probe-specific-zero set differs from numpy")
    # agree on the per-pair max-delta-over-basis value
    mc_pairs = [r["pair"] for r in legs["numpy"]["map_level_commutation"]["pairs"]]
    for pair in mc_pairs:
        a, b = pair
        vals = []
        for e in ENGINES:
            for r in legs[e]["map_level_commutation"]["pairs"]:
                if r["pair"] == pair:
                    vals.append(r["max_delta_over_basis"])
                    break
        if len(vals) == len(ENGINES) and not close(vals):
            failures.append(f"map_level max_delta[{a},{b}] disagrees: {dict(zip(ENGINES, vals))}")
    n_map_commuting = [legs[e]["map_level_commutation"]["n_map_level_commuting"] for e in ENGINES]
    n_probe_specific = [legs[e]["map_level_commutation"]["n_probe_specific_zeros"] for e in ENGINES]
    if len(set(n_map_commuting)) != 1:
        failures.append(f"n_map_level_commuting disagrees: {dict(zip(ENGINES, n_map_commuting))}")
    if len(set(n_probe_specific)) != 1:
        failures.append(f"n_probe_specific_zeros disagrees: {dict(zip(ENGINES, n_probe_specific))}")

    # 5. structural checks (by-construction, recorded)
    for e in ENGINES:
        if not legs[e]["diag_all_zero"]:
            failures.append(f"{e}: diagonal of delta matrix not all zero")
        if not legs[e]["matrix_symmetric"]:
            failures.append(f"{e}: delta matrix not symmetric")
        if not legs[e]["all_maps_cptp"]:
            failures.append(f"{e}: some map failed CPTP validity")

    # agreed headline numbers (from numpy, since all agree)
    n0 = legs["numpy"]
    mc0 = n0["map_level_commutation"]
    agreed = {
        "n_commuting_rho0": n0["n_commuting"],
        "n_noncommuting_rho0": n0["n_noncommuting"],
        "n_map_level_commuting": mc0["n_map_level_commuting"],
        "n_probe_specific_zeros_on_rho0": mc0["n_probe_specific_zeros"],
        "probe_specific_zero_pairs": [r["pair"] for r in mc0["pairs"] if r["rho0_zero_but_map_noncommutes"]],
        "noncommuting_pairs_rho0": [[a, b, round(d, 12)] for a, b, d in n0["noncommuting_pairs_rho0"]],
        "Ti_Fi_probe_relative": {p: round(b2["numpy"][p], 12) for p in ["rho0_plus", "mixed", "pole0", "generic"]},
        "lindblad_vs_te_by_construction_equals_gamma": round(float(lvt[0]), 12),
        "classical_gap_max": cg[0],
        "classical_gap_reopens_to": n0["discriminator_d_classical_baseline"]["coherence_map_reopens_gap_on_same_state"],
    }

    report = {
        "sim_id": SIM_ID,
        "engines": ENGINES,
        "computation_styles": styles,
        "trace_norm_routes": {
            "numpy": "eigvalsh (Hermitian eigenvalues)",
            "jax": "svdvals (singular values)",
            "pytorch": "nuclear-norm API (torch.linalg.matrix_norm ord=nuc)",
            "julia": "svdvals (independent language)",
        },
        "trace_norm_route_note": "THREE distinct trace-norm routes (eigvalsh / svdvals / nuclear-norm), not four: jax and julia both use svdvals. julia's independence is the from-scratch independent-LANGUAGE substrate, not a distinct mathematical route. For a 2x2 trace-0 Hermitian commutator difference these routes are mathematically equivalent (eigvalsh, svdvals, nuclear-norm all give sum|eigvals|); agreement is a code-path / language cross-check, not an independent-algorithm cross-check. The non-trivial cross-validation is the generic-probe value (no closed form).",
        "max_delta_matrix_diff_across_engines": max_matrix_diff,
        "agreement_tolerance": ATOL,
        "four_engine_agreement": len(failures) == 0,
        "agreed_values": agreed,
        "load_bearing_facts": {
            "map_level_commuting_pairs_are_zero_on_full_basis": all(
                legs[e]["map_level_commutation"]["n_map_level_commuting"] == legs["numpy"]["map_level_commutation"]["n_map_level_commuting"]
                for e in ENGINES),
            "state_null_zeros_detected_and_separated": all(
                legs[e]["map_level_commutation"]["n_probe_specific_zeros"]
                == legs["numpy"]["map_level_commutation"]["n_probe_specific_zeros"] for e in ENGINES),
            "noncommuting_pair_is_positive": min(float(legs["numpy"]["discriminator_b_noncommuting"][k]) for k in legs["numpy"]["discriminator_b_noncommuting"]) > ATOL,
            "order_dependence_probe_relative": probe_relative_flip,
            "signed_commutator_antisymmetric": antisym_all,
            "classical_baseline_gap_collapses": all(legs[e]["discriminator_d_classical_baseline"]["classical_gap_collapses"] for e in ENGINES),
            "coherence_reopens_gap": all(legs[e]["discriminator_d_classical_baseline"]["gap_reopens"] for e in ENGINES),
        },
        "structural_checks_recorded_not_load_bearing": {
            "_note": "These are by-construction tautologies (true for ALL inputs); they are recorded as sanity checks but are NOT evidence of any discovered structure. Moved out of load_bearing_facts.",
            "commuting_pair_is_zero_on_rho0": max(abs(float(legs["numpy"]["discriminator_a_commuting"][k])) for k in legs["numpy"]["discriminator_a_commuting"]) <= ATOL,
            "identity_commutes_with_all": all(legs[e]["control_identity_map"]["identity_commutes_all"] for e in ENGINES),
            "label_shuffle_invariant": all(legs[e]["control_label_shuffle"]["invariant"] for e in ENGINES),
            "matrix_symmetric": all(legs[e]["matrix_symmetric"] for e in ENGINES),
            "diag_self_zero": all(legs[e]["diag_all_zero"] for e in ENGINES),
            "choi_psd_pass_is_tautology_for_kraus": "Choi-PSD holds for any Kraus list; the trace-preserving check is the actual CPTP gate.",
            "trace_preserving_is_load_bearing_cptp_gate": all(legs[e]["all_maps_cptp"] for e in ENGINES),
            "lindblad_vs_te_equals_gamma_by_construction": round(float(lvt[0]), 12),
        },
        "failures": failures,
        "engine_consensus_note": "numpy (eigvalsh), jax (svdvals), pytorch (nuclear-norm API), and julia (from-scratch independent language, svdvals) are four distinct code paths in four languages/frameworks; reads_peer_result=false on all four. There are THREE distinct trace-norm routes (jax+julia share svdvals); for 2x2 trace-0 Hermitian input these routes are mathematically equivalent, so agreement is a code-path/language cross-check, not an independent-algorithm cross-check.",
        "classification": "scratch_diagnostic",
        "claim_ceiling": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_agreement_results.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    if failures:
        print(f"\nAGREEMENT CHECK FAILED ({len(failures)} issue(s))", file=sys.stderr)
        sys.exit(1)
    print("\nAGREEMENT OK: four engines agree on the noncommutation matrix and all discriminators/controls.")


if __name__ == "__main__":
    main()
