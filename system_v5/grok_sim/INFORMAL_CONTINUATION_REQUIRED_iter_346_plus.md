# INFORMAL continuation_required — iter_346 onwards

Date: 2026-05-25
Lane: `system_v5/grok_sim/` only.
Status: sidequest-local continuation artifact. Supersedes `INFORMAL_CONTINUATION_REQUIRED_iter_340_plus.md` for the iter_346+ packet.

Closeout state of the iter_334-345 sequence: **continued**. Twelve iters ran end-to-end across this and the prior loop turn.

| Iter | strict_pass | useful_falsifier | Note |
|---|:---:|:---:|---|
| iter_334 | True | False | 8-pair sweep + P333 carry-forward (P333 reading refined: family-specific shape) |
| iter_335 | True | False | dissipative schedule N01 survives |
| iter_336 | False | True | killed "Δ_A12 grows with k" |
| iter_337 | True | False | A9/A10 PEPS-layout lift |
| iter_338 | True | False | reverse derivation 333-337 |
| iter_339 | True | False | A12 PEPS-layout lift |
| iter_340 | True | True | killed universal-alignment (Ni_Te is structural outlier) |
| iter_341 | True | True | killed "iter_336 contraction is structural" — actually dissipation-driven |
| iter_342 | True | False | payoff family atlas — iter_333 shape family-specific |
| iter_343 | True | False | reverse derivation 340-342 |
| iter_344 | True | False | torch SVD truncation primitive works (chi-error scaling clean) |
| iter_345 | False (arithmetic gate) | False | Ni_Te structural incompatibility hardened across 4650 parameter points; min Δ = 0.0020 |

Boundary guard at end: 80 / 60 unique paths / delta 0 from baseline. Four useful falsifiers preserved as falsifiers (not smuggled to strict_pass).

Stop reason this turn: **condition 2 — runtime/context approaching exhaustion**. NOT condition 5 (next iter is named). Next admissible iter is named below.

---

## Next bounded iters (iter_346 onwards)

Run in this order. Each iter must pass the closeout schema from `CLAUDE_INFORMAL_CONTINUOUS_EXPLORATION_PROMPT_20260525.md`. Guard delta must remain 0.

### iter_346 — sympy analytic proof of Ni_Te incompatibility (closes G343_Ni_Te_structural_proof)

Question: can sympy prove analytically that `[Phi_Ni(H_C), Pi_Te]` has Frobenius norm bounded away from zero for every (theta, phi) parameterizing H_C?

Finite map: symbolic 4x4 superoperator commutator over `H_C = nx σ_x + ny σ_y + nz σ_z` with `nx² + ny² + nz² = 1`; simplify; lower-bound the norm.

Must include: symbolic Phi_Ni and Pi_Te superoperators; commutator computation; Frobenius norm as function of (theta, phi); show the function has a positive minimum (e.g., 0.002 from iter_345 numerical sweep).

Estimated effort: short. If sympy chokes on the symbolic algebra, write a blocker note explaining the tooling limitation and proceed to iter_347.

### iter_347 — unitary k-cycle dense sweep + period analysis (closes G343_unitary_k_cycle_period)

Question: does iter_341's unitary Delta_A12 oscillation have a discoverable period?

Finite map: sweep k ∈ {1, 2, 3, ..., 32}; record Delta_A12(k); apply FFT to the curve; identify dominant frequencies / periods.

Must include: k=1 baseline matches iter_341; commuting-pair control at every k; purity stays at 1; FFT analysis with identified peaks.

### iter_348 — payoff family atlas v2 (closes G343_payoff_family_atlas_density)

Question: when the atlas extends to 10+ payoff families with a smoothed classifier, do the shape classes survive?

Finite map: define 10+ families (add: polynomial of degree 3-5, multiplicative, symmetric-step, asymmetric-step, tanh-saturation, log-sigmoid mix); sweep alpha; refine shape classifier to tolerate floating-point bumps below 0.01 of the curve range.

Must include: per-family shape class; classifier robustness check; verification that iter_333 rise_peak_plateau still appears in winlose_sigmoid only.

### iter_349 — full PEPS environment contraction at chi=4 on 8-site lattice (closes G343_boundary_MPS_finite_chi)

Question: does iter_337's A9 inter-engine MI survive a real boundary-MPS contraction at chi=4 rather than dense 256-dim?

Finite map: build the iter_337 8-site lattice as a tensor-network; truncate via iter_344 SVD primitive at chi = 4, 8, 16; compute MI(engine_A : engine_B) per chi; compare to dense reference.

Must include: chi=16 (no truncation) matches dense reference; chi-error monotone decrease; identify minimum chi for MI accuracy within 5%.

### iter_350 — reverse derivation for iter_346-349

Roll up the four new iters into patterns, killed/open hypotheses, dependency gaps, narrow formal-lane targets with fails_if.

---

## Prompt for the next agent

Copy-paste into the next Claude/informal sidequest runtime:

```text
Read and execute:

system_v5/grok_sim/CLAUDE_INFORMAL_CONTINUOUS_EXPLORATION_PROMPT_20260525.md
system_v5/grok_sim/INFORMAL_CONTINUATION_REQUIRED_iter_346_plus.md

Do not summarize. Start with iter_346 (sympy analytic Ni_Te proof) unless a stronger blocker.

Continue the ladder iter_346 -> iter_350 inside system_v5/grok_sim/.
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

Session baseline (captured 2026-05-25 before iter_340): 80 total / 60 unique paths.
After iter_334-345 (+ this continuation file): 80 / 60 / delta 0.

Re-snapshot the guard baseline before any iter_346 write.

---

## What this artifact is NOT

- NOT a stop
- NOT a formal handoff
- NOT a frontier matrix
- NOT a promotion artifact
- NOT permission to skip the closeout schema
- NOT a substitute for actually running iter_346

The iter_340_plus continuation artifact is superseded by this one for the iter_346+ packet; both prior continuation artifacts are retained for history.
