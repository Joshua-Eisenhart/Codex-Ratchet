# INFORMAL continuation_required — iter_333 onwards

Date: 2026-05-25
Lane: `system_v5/grok_sim/` only.
Status: sidequest-local continuation artifact.

Closeout state of the iter_327-332 packet: **continued**. Six iters (iter_327 through iter_332) ran end-to-end, boundary guard delta = 0. iter_327 is an intentional falsifier/partial receipt with `strict_scientific_pass = false` because it killed the all-quadrants correlation-driven hypothesis. iter_328 through iter_332 have `strict_scientific_pass = true`. The recommended ladder from `CLAUDE_INFORMAL_CONTINUOUS_EXPLORATION_PROMPT_20260525.md` is complete.

This file is not a stop. It is a `continuation_required` artifact specifying the next packet set so the next agent (or the same agent in a fresh runtime) can pick up directly.

---

## Next bounded iters (from iter_332 dependency gaps)

Run in this order. Each iter must pass the closeout schema from the continuous-exploration prompt: classification, claim_ceiling, mode, F01, N01, finite map/domain/codomain, controls, negative conditions, tool manifest, killed/open hypothesis. Guard delta must remain 0.

### iter_333 — smooth-threshold payoff interpolation (closes G329)

Question: does the iter_327 GHZ-vs-matched-marginal split (linear payoffs marginal-driven, threshold payoffs correlation-driven) interpolate smoothly?

Finite map: `payoff_family(n_c; alpha) = sigmoid(alpha * (n_c - 2)) * scale + offset`; sweep alpha ∈ [0.1, 10.0]. For each alpha, compute GHZ payoff and matched-marginal payoff per quadrant; record `delta_payoff(alpha)`.

Must include: monotone-interpolation positive case; alpha=0.1 control (≈ linear → marginal-driven); alpha=10 control (≈ step → correlation-driven); fail-if condition that the curve is non-monotone or plateaus inconsistently.

### iter_334 — full IGT semisymmetry pair sweep (closes G328)

Question: do all 8 IGT semisymmetry pairs from doc_06 share the basis-alignment vs basis-incompatible dichotomy found in iter_328?

Finite map: for each pair `(τ_a, op_a) ↔ (τ_b, op_b)` from the 8-row semisymmetry table, compute `Delta_CPTP` superoperator commutator, classify as `aligned_collapse` or `incompatible_witness`.

Must include: all 8 pairs as positive cases; identity control; trace-preservation sanity per channel; perturbed lift for each `aligned_collapse` pair (verify perturbing the basis lifts collapse to nonzero witness).

### iter_335 — dissipative schedule step (closes G330)

Question: do iter_330 schedule N01 witnesses survive when some schedule steps are dissipative (amplitude-damping or depolarizing) rather than unitary?

Finite map: replace one or more steps in the iter_330 schedule with CPTP Kraus channels; rerun forward-vs-reverse and commuting-only tests.

Must include: positive case with mixed schedule; commuting-only control still collapsing; trace preservation (CPTP, so trace must be preserved exactly); fail-if condition that adding a single dissipative step destroys the order witness.

### iter_336 — multi-round policy/evidence cycle (closes G331)

Question: how does iter_331 Delta_A12 grow or saturate under k-round cycles of policy and evidence?

Finite map: `(C_p, C_e)^k(rho)` vs `(C_e, C_p)^k(rho)` for k ∈ {1, 2, 4, 8}; record `Delta_A12(k)`.

Must include: k=1 positive case (matches iter_331 baseline); k>1 growth observation; commuting-pair control collapsing at every k.

### iter_337 — A9/A10/A12 on small PEPS3D carrier (closes G327, hardest)

Question: do the A9, A10, A12 shadow signals survive when the dense 4- or 8-qubit carrier is replaced by a 2x2x2 PEPS lattice anchored 2-engine population?

Finite map: build 2-engine population on 2x2x2 PEPS lattice with bond-link channels between engines; lift iter_329/330/331 probes onto the PEPS carrier.

Must include: at least one PEPS-anchored A9 broadcast positive case; PEPS-anchored A10 schedule positive case; PEPS-anchored A12 policy/evidence positive case; per-shadow controls collapsing; fail-if condition that any shadow collapses on the PEPS carrier (would mean dense-carrier finding was small-system artifact).

### iter_338 — reverse derivation for iter_333-337

Roll up the five new iters into patterns, killed/open hypotheses, dependency gaps, narrow formal-lane reproduction targets with fails_if. Same shape as iter_326 and iter_332.

---

## Prompt for the next agent

Copy-paste into the next Claude/informal sidequest runtime:

```text
Read and execute:

system_v5/grok_sim/CLAUDE_INFORMAL_CONTINUOUS_EXPLORATION_PROMPT_20260525.md
system_v5/grok_sim/INFORMAL_CONTINUATION_REQUIRED_iter_333_plus.md

Do not summarize. Start with iter_333 (smooth-threshold payoff
interpolation) unless you can cite a stronger blocker.

Continue the ladder iter_333 -> iter_338 inside system_v5/grok_sim/.
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
  multi_model_parallelism.status: max_used | partial | blocked

Use maximum useful parallelism across available model pools. Attempt Claude plus
Grok/Gemini or another available contrast model when available; if a model pool
is unavailable, record it as blocked with a concrete reason. Do not describe a
single-model run as max parallelism.

Closeout must follow:
  1. what was explored
  2. finite map/domain/codomain
  3. controls held or failed
  4. killed/open hypothesis
  5. guard baseline -> after -> delta
  6. multi-model parallelism status and model pools attempted/completed
  7. files written under system_v5/grok_sim/
  8. next bounded iter started, or continuation_required artifact path
```

---

## Boundary-guard discipline reminder

Before any write: `python3 scripts/grok_sim_boundary_guard.py` and capture baseline path list.
After any write: same command; compute delta. New violations not allowed.

Session boundary-guard baseline (captured 2026-05-25 before iter_327): 80 total / 60 unique paths.
After iter_327-332 + this continuation file: 80 / 60 / delta 0.

---

## What this artifact is NOT

- NOT a stop
- NOT a formal handoff
- NOT a frontier matrix
- NOT a promotion artifact
- NOT permission to skip the closeout schema in the continuous-exploration prompt
- NOT a substitute for actually running iter_333

If a future runtime treats this as a stop signal, it has misread the file. The presence of an iter ladder, a continuation prompt, and explicit closeout requirements is the binding instruction.
