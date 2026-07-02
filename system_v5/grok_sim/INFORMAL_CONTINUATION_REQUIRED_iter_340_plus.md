# INFORMAL continuation_required — iter_340 onwards

Date: 2026-05-25
Lane: `system_v5/grok_sim/` only.
Status: sidequest-local continuation artifact (supersedes `INFORMAL_CONTINUATION_REQUIRED_iter_333_plus.md` for the iter_340 packet).

Closeout state of the iter_333-339 sequence: **continued**. Seven iters ran end-to-end. iter_333 and iter_336 are useful falsifiers (strict_scientific_pass=false, useful_falsifier=true) — they killed specific hypotheses cleanly. iter_334, iter_335, iter_337, iter_338, iter_339 are strict_pass=true. Boundary guard delta = 0 across the entire packet.

This is not a stop. iter_338 (reverse derivation) flagged 5 priority-ordered dependency gaps; one (G338_A12_lift_to_PEPS) is now closed by iter_339. The remaining four open gaps drive iter_340-iter_343.

---

## Next bounded iters (from iter_338 + iter_339 residual gaps)

Run in this order. Closeout schema from `CLAUDE_INFORMAL_CONTINUOUS_EXPLORATION_PROMPT_20260525.md` applies. Guard delta must remain 0.

### iter_340 — full IGT pair aligned-configuration parameter search (closes G338_full_IGT_pair_aligned_parameter_search)

Question: do the 7 incompatible IGT pairs from iter_334 also have *aligned* configurations under different parameter choices?

Finite map: for each of the 7 incompatible pairs, sweep parameters (terrain coupling strengths, operator angles) and search for configurations where Delta_CPTP collapses below 1e-6.

Must include: per-pair parameter sweep grid; identification of any collapse points; perturbation lift on any newfound collapses; fail-if condition that no incompatible pair has any aligned configuration (would mean the alignment dichotomy is binary not parametric).

### iter_341 — unitary-only k-round cycle (closes G338_unitary_only_k_round_cycle)

Question: does iter_336's k-round Delta_A12 contraction persist when both policy and evidence are unitary?

Finite map: replace iter_331's C_evidence (z-dephasing CPTP) with U_evidence (z-axis unitary rotation); rerun the k ∈ {1, 2, 4, 8} sweep.

Must include: k=1 positive case (should give nonzero Delta_A12); growth vs contraction with k; commuting-pair control collapsing at every k; trace AND purity preserved (since unitary).

### iter_342 — critical-alpha payoff family atlas (closes G338_critical_alpha_payoff_family_atlas)

Question: does the iter_333 rise-peak-plateau shape have a structural classification across payoff function families?

Finite map: define 5+ payoff family classes (linear, quadratic, sigmoid threshold, saturation/log, ReLU-like piecewise) parameterized by sharpness α; for each family, sweep α and record GHZ-vs-matched-marginal gap curve; classify curves by shape (monotone-increasing, rise-peak-plateau, monotone-decreasing, U-shape, etc.).

Must include: 5+ family classes; per-family α sweep; shape classification per family; fail-if condition that all families give the same shape (would falsify the iter_333+iter_334 family-specificity reading).

### iter_343 — reverse derivation for iter_339-342

Roll up iter_339-342 into patterns, killed/open hypotheses, dependency gaps, narrow formal-lane reproduction targets with fails_if.

---

## Larger remaining blocker (NOT in iter_340-343 scope)

### G338_boundary_MPS_at_finite_chi

All PEPS-layout work (iter_318, iter_320, iter_337, iter_339) uses dense full-state contraction at 8 sites. The next scale step requires either a torch SVD-with-truncation primitive (per iter_306a5 blocker) or a workaround. This is medium-sized informal-lane tooling work; it should be a single dedicated iter (iter_344 or later) rather than wedged into the iter_340-343 packet.

Skip to G338_boundary_MPS_at_finite_chi only if the iter_340-343 packet completes and runtime remains.

---

## Prompt for the next agent

Copy-paste into the next Claude/informal sidequest runtime:

```text
Read and execute:

system_v5/grok_sim/CLAUDE_INFORMAL_CONTINUOUS_EXPLORATION_PROMPT_20260525.md
system_v5/grok_sim/INFORMAL_CONTINUATION_REQUIRED_iter_340_plus.md

Do not summarize. Start with iter_340 (full IGT pair aligned-config
parameter search) unless a stronger blocker.

Continue the ladder iter_340 -> iter_343 inside system_v5/grok_sim/.
Do not write outside system_v5/grok_sim/.
Do not use formal-lane classifications.
Do not default to "Stop."

Each iter must carry:
  classification: sidequest_local_<name>_v1
  claim_ceiling: side_quest_only
  promotion_allowed: false
  evidence_allowed: false
  evidence_allowed_for_formal: false
  formal_reproduction_target: false

Closeout must follow:
  1. what was explored
  2. finite map/domain/codomain
  3. controls held or failed
  4. killed/open hypothesis (useful_falsifier=true when applicable)
  5. guard baseline -> after -> delta
  6. files written under system_v5/grok_sim/
  7. next bounded iter started, or continuation_required artifact path
```

---

## Boundary-guard discipline reminder

Session baseline captured 2026-05-25 before iter_334: 80 total / 60 unique paths.
After iter_334-339 (+ this continuation file): 80 / 60 / delta 0.

Re-snapshot the guard baseline before any iter_340 write.

---

## What this artifact is NOT

- NOT a stop
- NOT a formal handoff
- NOT a frontier matrix
- NOT a promotion artifact
- NOT permission to skip the closeout schema
- NOT a substitute for actually running iter_340

The iter_333_plus continuation artifact is now superseded by this one for the iter_340+ packet; the original is retained for history.
