#!/usr/bin/env python3
"""Four-engine agreement adjudicator for cut_lattice_schmidt_entropy_v0.

agreement_ok GATES on: (1) every present leg's all_tests_pass + all_controls_pass + scratch
ceiling; (2) cross-engine agreement of the structure (cut-lattice counts, Schmidt ranks, the
integer/bool invariants) and the per-cut entropy VALUES to 1e-9; (3) the STATE-CONTRASTIVE
load-bearing discriminators (GHZ-vs-W per-cut divergence, bell cut-dependence, scramble moves
entropy, GHZ negativity nonzero, AND the subsystem-orientation check that catches an A<->B
partial-trace swap the spectra are blind to); (4) all four engines present and mutually fresh.

Three honest tiers, separated so the gate count is not inflated:
  - load_bearing_discriminators : state-contrastive, GATE agreement_ok.
  - implementation_sanity_checks: algebraically FORCED by the FIXED state definitions (product
    S=0; GHZ S=1 on every cut; max-entangled hits log2 dim; W = log2(3)-2/3; ablation delta=1).
    They catch a broken reduction / wrong state but are NOT discoveries. Reported, NOT gated.
  - by_construction_identities  : pure-state theorems (S_A==S_B; I=2S; I_c=S) true for ANY
    correct reduction; cannot fail. Reported, NOT gated.

Reads only the result JSONs; computes nothing itself; does not self-upgrade the sim.
"""

from __future__ import annotations

import json
import math
import pathlib

SIM_ID = "cut_lattice_schmidt_entropy_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = RESULTS / f"{SIM_ID}_agreement_results.json"
LEGS = {
    "exact": RESULTS / f"{SIM_ID}_exact_results.json",
    "julia": RESULTS / f"{SIM_ID}_julia_results.json",
    "jax": RESULTS / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULTS / f"{SIM_ID}_pytorch_results.json",
}

AGREE_TOL = 1e-9
W_N3 = math.log2(3) - 2 / 3  # ~0.918296

# GATING exact-match cross-engine checks (integers / bools the engines could compute differently)
EXACT_KEYS = ["n_cuts_n2", "n_cuts_n3", "n_cuts_n4", "schmidt_rank_product",
              "n4_max_cut_rank", "n4_ghz_uniform", "n4_w_nonuniform"]
# GATING float cross-engine checks (per-cut entropy VALUES -- the load-bearing state-dependent
# readouts; an engine with a real partial-trace/eigval bug would diverge here)
FLOAT_KEYS = ["n2_product_max_S", "n2_bell_S_cut0", "n3_product_max_S", "n3_ghz_w_max_gap",
              "n3_bell_cut0_S", "n3_bell_cut01_S", "n4_max_cut_S", "product_negativity_max",
              "ghz_negativity_cut0", "purity_symmetry_max_dev", "scramble_S_cut0_n3",
              "scramble_S_cut0_n4", "w4_cut0_marginal_pop1", "w4_cut0_rdm_pop1"]
# GATING per-cut profile dicts (every cut's entropy must agree across engines to 1e-9)
PROFILE_KEYS = ["n3_ghz_profile", "n3_w_profile"]


def main() -> int:
    legs = {}
    failures = []
    for name, path in LEGS.items():
        if not path.exists():
            failures.append(f"{name}: result JSON missing ({path.name})")
            continue
        legs[name] = json.loads(path.read_text())

    for name, obj in legs.items():
        if not obj.get("all_tests_pass"):
            failures.append(f"{name}: all_tests_pass false")
        if not obj.get("all_controls_pass"):
            failures.append(f"{name}: all_controls_pass false")
        if obj.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification {obj.get('classification')}")
        if obj.get("promotion_allowed") is not False:
            failures.append(f"{name}: promotion_allowed not false")

    # FRESHNESS GUARD: surface a leg whose result JSON was not rewritten in the same run window.
    # The checker reads only on-disk JSONs; a stale leg (e.g. an engine that failed to import and
    # left an old file) would otherwise be counted as live. Gate if any present leg's mtime lags
    # the newest by more than STALE_WINDOW_S (a full fresh run rewrites all four within seconds).
    STALE_WINDOW_S = 600  # 10 min: generous for a slow Julia JIT, tight enough to catch a no-run
    mtimes = {n: LEGS[n].stat().st_mtime for n in legs}
    if mtimes:
        newest = max(mtimes.values())
        for n, mt in mtimes.items():
            if newest - mt > STALE_WINDOW_S:
                failures.append(f"{n}: result JSON stale ({int(newest - mt)}s older than newest leg; re-run it)")

    inv = {n: legs[n]["invariants"] for n in legs}
    ref = "exact" if "exact" in inv else next(iter(inv), None)

    # GATING: exact-match structure
    for key in EXACT_KEYS:
        vals = {n: inv[n].get(key) for n in inv}
        if len(set(json.dumps(v, sort_keys=True) for v in vals.values())) > 1:
            failures.append(f"{key}: disagreement {vals}")
    # GATING: per-cut entropy VALUES agree to 1e-9
    for key in FLOAT_KEYS:
        base = inv[ref][key]
        for n in inv:
            if abs(inv[n][key] - base) > AGREE_TOL:
                failures.append(f"{key}: {n}={inv[n][key]} vs {ref}={base}")
    # GATING: per-cut profiles agree to 1e-9 cut-by-cut
    for key in PROFILE_KEYS:
        base = inv[ref][key]
        for n in inv:
            prof = inv[n][key]
            if set(prof) != set(base):
                failures.append(f"{key}: cut keys differ {n}")
                continue
            for c in base:
                if abs(prof[c] - base[c]) > AGREE_TOL:
                    failures.append(f"{key}[{c}]: {n}={prof[c]} vs {ref}={base[c]}")

    agreed = inv[ref] if ref else {}

    # LOAD-BEARING DISCRIMINATORS: STATE-CONTRASTIVE outcomes that could come out otherwise for a
    # DIFFERENT input or a real bug -- they distinguish state classes (GHZ vs W), pin a cut
    # dependence, take entropy off a baseline, OR fix the subsystem orientation (catching an
    # A<->B partial-trace swap the entropy/rank spectra are blind to). These GATE agreement_ok.
    load_bearing_discriminators = {
        "ghz_vs_w_per_cut_profile_divergence": (agreed.get("n3_ghz_w_max_gap", 0) > 0.05
            and agreed.get("n4_w_nonuniform") is True and agreed.get("n4_ghz_uniform") is True),
        "bell_pair_cut_dependence": (abs(agreed.get("n3_bell_cut0_S", 0) - 1.0) < AGREE_TOL
            and agreed.get("n3_bell_cut01_S", 1) < AGREE_TOL),
        "scramble_moves_entropy_off_baseline": (agreed.get("scramble_S_cut0_n3", 0) > 0.1
            and agreed.get("scramble_S_cut0_n4", 0) > 0.1),
        "ghz_negativity_nonzero": agreed.get("ghz_negativity_cut0", 0) > 0.1,
        "subsystem_orientation_no_AB_swap": (
            all(legs[n]["tests"].get("subsystem_orientation_no_AB_swap") for n in legs)
            and abs(agreed.get("w4_cut0_rdm_pop1", -1) - agreed.get("w4_cut0_marginal_pop1", -2)) < AGREE_TOL
            and abs(agreed.get("w4_cut0_marginal_pop1", 0) - 0.25) < AGREE_TOL),
    }
    for k, ok in load_bearing_discriminators.items():
        if not ok:
            failures.append(f"discriminator {k} not satisfied")

    # IMPLEMENTATION-SANITY checks: algebraically FORCED by the fixed state definitions (|0..0>
    # has S=0 / rank 1 / neg 0 on every cut; GHZ has S=1 on every cut; max-entangled 2:2 hits
    # log2(4); W has S=log2(3)-2/3; the GHZ-product ablation delta is exactly 1). For these
    # SPECIFIC states a correct partial trace cannot return otherwise -- they catch a broken
    # reduction or a wrong state construction, but are NOT state-contrastive discoveries. Reported
    # for transparency; they do NOT gate agreement_ok (gating still requires all four engines'
    # all_tests_pass + the cross-engine value agreement above).
    deltas = [legs[n].get("ablation_outcome_delta", {}).get("delta", 0.0) for n in legs]
    implementation_sanity_checks = {
        "product_state_zero_on_every_cut": (agreed.get("n2_product_max_S", 1) < AGREE_TOL
            and agreed.get("n3_product_max_S", 1) < AGREE_TOL
            and agreed.get("schmidt_rank_product") == 1),
        "product_negativity_zero": agreed.get("product_negativity_max", 1) < AGREE_TOL,
        "entangled_vs_separable_ablation_delta_one": all(d > 0.5 for d in deltas),
        "w_n3_uniform_at_log3_form": all(abs(v - W_N3) < AGREE_TOL
            for v in agreed.get("n3_w_profile", {}).values()),
        "ghz_n3_uniform_at_one": all(abs(v - 1.0) < AGREE_TOL
            for v in agreed.get("n3_ghz_profile", {}).values()),
        "max_entangled_cut_hits_log2_dim": (abs(agreed.get("n4_max_cut_S", 0) - 2.0) < AGREE_TOL
            and agreed.get("n4_max_cut_rank") == 4),
    }

    # by-construction / formula-level facts: reported, NOT gated as discoveries. The per-cut
    # reduction + entropy FORMULA is well-defined linear algebra; pure-state S_A==S_B, I=2S and
    # I_c=S are identities true for ANY correct pure-state reduction (cannot fail).
    by_construction_identities = {
        "purity_symmetry_SA_eq_SB": all(
            legs[n].get("by_construction_identities", {}).get("purity_symmetry_SA_eq_SB") for n in legs),
        "mutual_info_equals_2S_pure": all(
            legs[n].get("by_construction_identities", {}).get("mutual_coherent_pure_identities") for n in legs),
        "coherent_info_equals_S_pure": all(
            legs[n].get("by_construction_identities", {}).get("mutual_coherent_pure_identities") for n in legs),
        "per_cut_reduction_is_well_defined_linear_algebra": True,
    }

    n_engines = len(inv)
    agreement_ok = (not failures) and n_engines == 4
    if n_engines < 4:
        failures.append(f"only {n_engines}/4 engines present; four-engine path not complete")

    result = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "agreement_ok": agreement_ok,
        "engines_present": sorted(inv.keys()),
        "n_engines": n_engines,
        "agreed_invariants": agreed,
        "load_bearing_discriminators": load_bearing_discriminators,
        "implementation_sanity_checks": implementation_sanity_checks,
        "by_construction_identities": by_construction_identities,
        "result_file_mtimes": {n: LEGS[n].stat().st_mtime for n in legs},
        "failures": failures,
        "honest_scope": {
            "earns": "four-engine (numpy/jax/pytorch/julia) cross-language AGREEMENT to 1e-9 on the per-cut entropy + Schmidt-rank invariants of the cut lattice (2^{n-1}-1 bipartitions) for n=2,3,4. The GENUINE load-bearing content is the STATE-DEPENDENT discriminators that could have come out otherwise: product state -> S=0 / rank 1 / negativity 0 on every cut; GHZ vs W -> DIFFERENT per-cut entropy profiles (n3 gap ~0.0817; n4 W non-uniform [0.811,1.0] vs GHZ uniform [1.0]); a maximally-entangled 2:2 cut -> S=log2(4)=2 rank 4; bell_01 x |0> -> S=1 on {0}|{1,2} but S=0 on {0,1}|{2}; a deterministic scramble -> S>0.1 off the product baseline.",
            "does_not_earn": "M(C) admission, Axis0 closure, QIT engine, smooth manifold, physics. The per-cut reduction + von Neumann entropy + pure-state I=2S / I_c=S relations are well-defined linear algebra / identities (reported as consistency, NOT discoveries). box viii (multi-model fleet audit) REQUIRED -- a single fresh-context pipeline is insufficient.",
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"agreement_ok": agreement_ok, "n_engines": n_engines,
                      "engines": sorted(inv.keys()), "failures": failures}, indent=2))
    return 0 if agreement_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
