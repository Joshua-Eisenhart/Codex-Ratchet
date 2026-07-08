#!/usr/bin/env python3
"""v7_codex_ratchet_crosscheck_sim -- loop this bundle's engine results back against the v7 codex-ratchet repo's
qit engine sims, so the two builds stay in sync and any drift is caught.

The v7 codex-ratchet repo (granted read-only at /Users/joshuaeisenhart/Codex-Ratchet) contains an independent engine
build: qit_full_type1_type2_64_live_v1. This sim reads that build's result JSON (if the repo is present) and checks
that its structural facts AGREE with this bundle's engine reconstruction:

  1. 64-schedule AGGREGATE COUNTS: 64 slots = 16 macro-stages x 4 substages, 16 chart-locked + 48 runtime,
     32 Type-1 + 32 Type-2, plus unique-coordinate cardinality 64. These are 7 summary counts + a cardinality --
     NOT a per-slot field-by-field identity (the v7 result exposes only a schedule hash, not the per-slot list, so a
     full per-slot diff is not possible from the result alone).
  2. engine loop pairing: T1_outer=deductive / T1_inner=inductive, T2 mirrored -- the SAME mirror pairing this
     bundle's engine_pair_matrix_sim uses.
  3. object formation by distinguishability: the v7 build reports ordered object formation over the 4 engine loops
     with ordered_accuracy 1.0, object_count 4, entropy monotone 2.0->0.0 bits. This is CONSISTENT with this bundle's
     16-stage re-identification (0.6875, 3 degenerate pairs): at the coarser 4-loop granularity the objects are fully
     distinguishable; the degeneracies appear only at the finer 16-stage granularity. Same criterion, two resolutions.

HONEST SCOPE: this is a structural cross-check (schedule shape, pairing, formation criterion), NOT a numeric
bit-for-bit reproduction of the v7 trajectory (different substrate, different probe battery). If the v7 repo is absent
the check is SKIPPED (not failed) -- it is a sync probe, not a hard dependency. The v7 build is itself scratch_diagnostic
/ promotion_allowed=false; agreement here does not promote either build. scratch_diagnostic.
"""
import json, os, sys

HERE=os.path.dirname(os.path.abspath(__file__))
V7="/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/qit_full_type1_type2_64_live_v1/results/qit_full_type1_type2_64_live_v1_results.json"
BUNDLE_TABLE=os.path.join(HERE,"..","reference_docs","engine_math","source_schedule_tables","engine_64_source_schedule.json")
BUNDLE_REID=os.path.join(HERE,"engine_reidentification_objective_sim_results.json")

# fixed structural counts this bundle's schedule_source_fidelity_linter certifies (aggregate counts, NOT per-slot content)
BUNDLE_COUNTS={"slot_count":64,"macro_stage_count":16,"substage_count_per_macro":4,"chart_locked_slots":16,
        "runtime_probe_slots":48,"type1_slots":32,"type2_slots":32}
PAIRING_EXPECTED={"T1_outer_deductive","T1_inner_inductive","T2_outer_inductive","T2_inner_deductive"}

def bundle_reid():
    # read the bundle's REAL re-id result live (do not hardcode)
    if not os.path.exists(BUNDLE_REID): return None
    r=json.load(open(BUNDLE_REID))
    rate=r.get("real_reidentification_rate_novel_probes")
    ndeg=len(set(frozenset(p) for p in r.get("stages_that_failed_reid",[])))
    return {"rate":rate,"n_reid":r.get("n_stages_reidentified"),"n":r.get("n_stages"),"degenerate_pairs":ndeg,
            "separation":r.get("separation_real_minus_shuffled")}

def bundle_canonical_coords():
    # derive the 64 canonical per-slot coordinate tuples from the bundle table (engine,loop,step,terrain,operator,sign)
    if not os.path.exists(BUNDLE_TABLE): return None
    rows=json.load(open(BUNDLE_TABLE))
    coords=set()
    for r in rows:
        coords.add((r.get("engine"),r.get("loop"),r.get("step"),r.get("terrain"),r.get("operator"),r.get("axis6_sign")))
    return coords

def main():
    if not os.path.exists(V7):
        out={"classification":"scratch_diagnostic","promotion_allowed":False,"v7_repo_present":False,
             "note":"v7 codex-ratchet repo not present; cross-check skipped (sync probe, not a hard dependency)",
             "V7_CODEX_RATCHET_CROSSCHECK":"SKIP"}
        json.dump(out,open(__file__.replace(".py","_results.json"),"w"),indent=1)
        print("v7 codex-ratchet repo not present -> cross-check SKIPPED (not a failure)")
        print("PASS v7_codex_ratchet_crosscheck (skip-clean)")
        print("ALL_GATES: PASS (skip) ->",__file__.replace(".py","_results.json")); sys.exit(0)

    r=json.load(open(V7)); m=r["matrix64_schedule"]; of=r["core_measurement"]["ordered_object_formation"]
    # 1. AGGREGATE-COUNT agreement (7 summary counts -- NOT per-slot content identity)
    count_keys=["slot_count","macro_stage_count","substage_count_per_macro","chart_locked_slots",
                "runtime_probe_slots","type1_slots","type2_slots"]
    counts_agree=all(m.get(k)==BUNDLE_COUNTS[k] for k in count_keys)
    count_diffs={k:(BUNDLE_COUNTS[k],m.get(k)) for k in count_keys if m.get(k)!=BUNDLE_COUNTS[k]}
    # 1b. per-slot CONTENT: the bundle derives 64 unique canonical coordinates; v7 exposes only a hash + a
    #     unique_coordinate_count. We can check the bundle produces 64 unique coords AND matches v7's
    #     unique_coordinate_count. We CANNOT field-diff per-slot (v7 result carries only schedule_sha256, not the list).
    bcoords=bundle_canonical_coords()
    bundle_unique=len(bcoords) if bcoords is not None else None
    v7_unique=m.get("unique_coordinate_count")
    unique_agree=(bundle_unique is not None and v7_unique is not None and bundle_unique==v7_unique==64)
    perslot_content_note=("v7 result exposes only schedule_sha256="+str(m.get("schedule_sha256",""))[:16]+
                          "... and unique_coordinate_count; per-slot field-by-field diff is NOT possible from the "
                          "result alone. This check compares aggregate counts + unique-coordinate cardinality, not full content.")
    # 2. pairing agreement (v7 trace loop names)
    v7_loops=set(of["traces"].keys())
    pairing_agree=(v7_loops==PAIRING_EXPECTED)
    # 3. v7's own formation cleanliness
    formation_clean=(of["ordered_accuracy"]==1.0 and of["object_count"]==4 and of["all_entropy_gradients_monotone"])
    # 4. GENUINE two-resolution cross-comparison: read the bundle's REAL re-id result LIVE (not a hardcoded literal)
    #    and confirm both resolutions are internally distinguishable and mutually consistent. v7 sees 4 distinct
    #    objects at the coarse 4-loop granularity; the bundle re-identifies its 16 STAGES at the finer granularity.
    #    Consistency means: coarse clean AND fine strictly distinguishing (rate strictly above chance and above the
    #    shuffled control -- i.e. identity survives probe rotation at BOTH resolutions). The fine resolution may be
    #    fully clean (16/16) or partially degenerate (0<rate<1); what must hold is that it separates FAR above chance.
    #    HISTORY: before the 2026-07-08 stage-probe repair the fine re-id was inherently degenerate (0.6875, 3 chirality-
    #    mirror pairs collapsed by the singular-value signature). That was a DEFECT, not the thing being validated;
    #    the repair (full affine map) lifted it to 16/16. This check therefore requires strong distinguishability,
    #    NOT the presence of degeneracies. FAILS if the bundle re-id file is absent OR the fine rate does not clear
    #    the shuffled control by a wide margin (identity not rotation-invariant at the fine resolution).
    br=bundle_reid()
    if br is None:
        resolutions_consistent=False; res_detail="bundle re-id result file absent"
    else:
        rate=br["rate"] or 0
        fine_distinguishes = (rate is not None and rate>0.5 and br["separation"] is not None and br["separation"]>0.5)
        coarser_is_clean=formation_clean
        resolutions_consistent=bool(fine_distinguishes and coarser_is_clean)
        res_detail=f"v7 4-loop clean {formation_clean}; bundle 16-stage rate {br['rate']} ({br['n_reid']}/{br['n']}) sep {br['separation']} over shuffled, {br['degenerate_pairs']} degenerate pairs (fine resolution distinguishes far above chance: {fine_distinguishes})"

    agree=bool(counts_agree and unique_agree and pairing_agree and formation_clean and resolutions_consistent)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,"v7_repo_present":True,
         "v7_source_sha256":r.get("source_sha256","")[:16],"v7_generated_at":r.get("generated_at"),
         "aggregate_counts_agree":bool(counts_agree),"aggregate_count_diffs":count_diffs,
         "bundle_unique_coordinate_count":bundle_unique,"v7_unique_coordinate_count":v7_unique,
         "unique_coordinate_count_agrees":bool(unique_agree),
         "per_slot_content_note":perslot_content_note,
         "engine_pairing_agrees":bool(pairing_agree),"v7_loops":sorted(v7_loops),
         "v7_formation_clean":bool(formation_clean),
         "v7_ordered_accuracy":of["ordered_accuracy"],"v7_object_count":of["object_count"],
         "v7_mean_entropy_drop_bits":of["mean_entropy_drop_bits"],
         "bundle_reid_live":br,
         "two_resolutions_consistent":bool(resolutions_consistent),"two_resolutions_detail":res_detail,
         "resolution_note":"v7 measures object formation over 4 engine LOOPS (fully distinguishable, 4/4); this bundle measures re-id over 16 STAGES (read LIVE from its result file) with degeneracies. Consistent: coarser granularity is cleaner, finer granularity exposes the oracle-predicted degeneracies -- same distinguishability criterion at two resolutions.",
         "scope_note":"structural + aggregate-count + live re-id cross-check; NOT a bit-for-bit per-slot reproduction of the v7 trajectory (different substrate/probe battery, and v7 exposes only a schedule hash).",
         "V7_CODEX_RATCHET_CROSSCHECK":agree}
    json.dump(out,open(__file__.replace(".py","_results.json"),"w"),indent=1)
    print("V7 CODEX-RATCHET CROSS-CHECK -- looping this bundle back against the v7 qit engine build.\n")
    print(f"  v7 build: {r.get('sim_id')}  source_sha256 {r.get('source_sha256','')[:16]}  generated {r.get('generated_at')}")
    print(f"  1. aggregate counts agree (7 summary counts: 16x4=64, 16 chart-locked + 48 runtime, 32+32): {counts_agree}"+("" if counts_agree else f"  DIFFS {count_diffs}"))
    print(f"  1b. unique-coordinate cardinality agrees (bundle {bundle_unique} == v7 {v7_unique} == 64): {unique_agree}  [per-slot field diff NOT available: v7 exposes only a hash]")
    print(f"  2. engine mirror pairing agrees (T1 outer=deductive, T2 mirrored): {pairing_agree}")
    print(f"  3. v7 object formation clean (ordered_accuracy {of['ordered_accuracy']}, {of['object_count']} objects, entropy monotone {of['mean_entropy_drop_bits']}->0 bits): {formation_clean}")
    print(f"  4. two resolutions consistent (LIVE bundle re-id): {resolutions_consistent}  [{res_detail}]")
    print(f"\n  V7 CODEX-RATCHET CROSS-CHECK (bundle agrees with v7 build): {agree}")
    if agree: print("PASS v7_codex_ratchet_crosscheck")
    print("ALL_GATES:", "PASS" if agree else "FAIL","->",__file__.replace(".py","_results.json"))
    sys.exit(0 if agree else 1)

if __name__=="__main__":
    main()
