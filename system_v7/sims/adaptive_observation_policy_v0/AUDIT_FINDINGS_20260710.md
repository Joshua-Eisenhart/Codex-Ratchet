# Fresh-context audit — adaptive_observation_policy_v0 (2026-07-10)

Verdict: FINDINGS (one moderate; reproduction clean).

Clean: determinism hash 3ba1802ea63c85703120c8f88d4adc0ab7d66f3075b9ef2352349765ea526603 reproduced from an isolated
scratch copy; null arena genuinely returns gap 0.0; degeneracy and boundary checks recompute; ceiling honest
(scratch_diagnostic, promotion false).

FINDING (moderate, kills one receipt claim): the receipt's "Policy A is NOT a strawman — best fixed schedule" claim is
falsified. Auditor sampled 20,000 random fixed 5-query schedules with the script's own run_fixed_policy: 51.7% beat
shipped Policy A (ident_rate 0.10); best random schedule reached 0.5 vs adaptive B's 0.6. A's greedy design does not
leak ground truth (real, not fabricated) but is an under-optimized baseline. The honest headline is therefore
"adaptive B ~0.6 vs competent fixed ~0.4-0.5" — a modest surviving advantage, NOT the 6x gap the raw numbers suggest.

Carried open items (from the lane receipt): budget sweep unrun; K=16 arena is a second null by construction; single
seed; baseline replacement with an optimized fixed schedule is the required next control before this lane's A-vs-B
comparison can gate anything.

---

# Optimized-baseline control result (2026-07-11, codex1 terra, 121,240 unique fixed schedules, seed 0)

A(old weak) 0.100 / 5.850; A*(best-found fixed, [51,88,62,113,68]) 0.525 / 5.375; B(adaptive) 0.600 / 5.400.
Honest verdict: B survives on identification rate (0.600 vs 0.525) but A* uses fewer mean queries — an
identification/query tradeoff, not an unqualified adaptive advantage. The search is non-exhaustive; A* is not a
proven global optimum. The audit's kill of the "6x gap" headline stands; the surviving claim is the modest margin.
Receipts: results_baseline_v1.json + byte-identical rerun results_baseline_v1_1.json (sha 46e9c374...7923586a).
