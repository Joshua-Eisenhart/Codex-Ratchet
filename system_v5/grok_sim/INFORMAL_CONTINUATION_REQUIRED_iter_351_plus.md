# INFORMAL continuation_required — iter_351 onwards

Date: 2026-05-25
Lane: `system_v5/grok_sim/` only.
Status: sidequest-local continuation artifact. Supersedes `INFORMAL_CONTINUATION_REQUIRED_iter_346_plus.md` for the iter_351+ packet.

Closeout state of the iter_345-repair + iter_346-350 packet: **continued**. Six iter actions in this loop turn:

| Iter | strict_pass | useful_falsifier | Note |
|---|:---:|:---:|---|
| iter_345 (repair) | True (was False) | False | arithmetic-gate off-by-one fixed; substantive findings unchanged; Ni_Te lower bound 0.0020 across 4650 points |
| iter_346 | True | False | sympy partial-reduction: γ²q²/2 baseline; H term not yet bounded |
| iter_347 | True | False | unitary k-cycle is quasi-periodic (3 FFT peaks at periods 10.67, 16, 5.33) |
| iter_348 | True | False | 12-family atlas v2; rise_peak appears in saturating-step families (sigmoid + tanh) |
| iter_349 | True | False | min chi for 5% inter-engine MI accuracy = 8 (half-rank) |
| iter_350 | True | False | reverse derivation 346-349; 4 patterns / 0 killed / 4 open / 5 gaps / 4 targets |

Boundary guard at end: 80 / 60 unique paths / **delta 0** from baseline.

Stop reason this turn: **condition 2 — runtime/context approaching exhaustion**. NOT condition 5 (next iter is named). Five iters are admissibly named below.

---

## Next bounded iters (iter_351 onwards)

Run in this order. Each iter must pass the closeout schema from `CLAUDE_INFORMAL_CONTINUOUS_EXPLORATION_PROMPT_20260525.md`. Guard delta must remain 0.

### iter_351 — full analytic Ni_Te lower bound (closes G350_full_analytic_Ni_Te_lower_bound)

Question: can the iter_346 (θ, φ)-independent baseline `γ²q²/2` be extended to a full analytic lower bound that includes the Hamiltonian contribution?

Strategy: decompose `[Phi_Ni, Pi_Te] = [γ·D[σ_-], Pi_Te] + [-i·0.1·[H_C, ·], Pi_Te]`. Use sympy to bound the Hamiltonian term's Frobenius norm as a function of (θ, φ). Apply triangle inequality: `‖A + B‖ ≥ |‖A‖ - ‖B‖|`. If `‖B‖_max < ‖A‖`, the total norm has a positive lower bound.

Falsifier target: if `‖B‖_max ≥ ‖A‖`, the iter_345 numerical lower bound 0.0020 cannot be reduced from this analytic decomposition.

### iter_352 — extended k-cycle quasi-period confirmation (closes G350_longer_k_sweep_for_quasi_period_confirmation)

Question: are the 3 FFT peaks from iter_347 truly incommensurate frequencies (quasi-periodic), or do they merge into one period at longer k windows?

Strategy: extend k sweep to 128 or 256. Re-FFT. Distinguish:
- single dominant peak at long period (periodic)
- 3 stable comparable peaks (quasi-periodic)
- spectrum spreads (chaotic / aperiodic)

### iter_353 — saturating-family atlas extension (closes G350_saturating_family_atlas_extension)

Question: is rise_peak_drop the universal signature of saturating-step payoff families, beyond sigmoid and tanh?

Strategy: add arctan(α·(n_c-2)), erf(α·(n_c-2)), smoothstep, and softplus to iter_348's atlas. Apply smoothed shape classifier. Check whether ALL saturating-step families give rise_peak_drop (or _plateau).

### iter_354 — full 2D boundary-MPS at 4x2 lattice (closes G350_full_2D_boundary_MPS_at_larger_lattices)

Question: does iter_349's single-cut Schmidt truncation extend to a real 2D boundary-MPS contraction at a 4x2 lattice (8 sites in 2D, not just 1D-cut)?

Strategy: row-by-row contraction; use iter_344 SVD primitive at each step. Chi sweep on a 4x2 = 8-qubit lattice with XY bonds; measure observable accuracy vs chi.

### iter_355 — finite chi on iter_320 64-cell schedule (closes G350_finite_chi_on_iter_320_64_cell_schedule)

Question: does iter_320's 64-cell schedule final-state entanglement survive finite-chi Schmidt truncation in the same way as iter_337's bond-only state?

Strategy: rerun iter_349 chi-vs-MI sweep on the iter_320 final state (which has 64 cell channels + 64 bonds woven together rather than 12 bonds only).

### iter_356 — reverse derivation for iter_351-355

Roll up the five new iters into patterns, killed/open hypotheses, dependency gaps, narrow formal-lane targets with fails_if.

---

## Prompt for the next agent

Copy-paste into the next Claude/informal sidequest runtime:

```text
Read and execute:

system_v5/grok_sim/CLAUDE_INFORMAL_CONTINUOUS_EXPLORATION_PROMPT_20260525.md
system_v5/grok_sim/INFORMAL_CONTINUATION_REQUIRED_iter_351_plus.md

Do not summarize. Start with iter_351 unless a stronger blocker.

Continue the ladder iter_351 -> iter_356 inside system_v5/grok_sim/.
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

Session baseline (captured 2026-05-25 before iter_346): 80 total / 60 unique paths.
After iter_345 repair + iter_346-350 + this continuation artifact: 80 / 60 / **delta 0**.

Re-snapshot the guard baseline before any iter_351 write.

---

## What this artifact is NOT

- NOT a stop
- NOT a formal handoff
- NOT a frontier matrix
- NOT a promotion artifact
- NOT permission to skip the closeout schema
- NOT a substitute for actually running iter_351

Prior continuation artifacts (`iter_333_plus.md`, `iter_340_plus.md`, `iter_346_plus.md`) are retained for history.
