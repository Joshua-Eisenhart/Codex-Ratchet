# Ratchet Runbook — PARTIAL first multi-model run (wf wg6p8be1d, 2026-06-15)

**Status: `PARTIAL_WITH_REROUTE_REQUIRED` — `process_ran=true`, `adjudication_grade=true`, `evidence_grade=false`.** NOT "full run worked" (corrected per codex audit): the Minimalist role was UNAVAILABLE on 2/4 projections (gemini quota 429), so density_rho + entropy_von_neumann lacked a complete Minimalist-first triad. 17 agents: 4 contested projections through Minimalist (gemini) → Lift (deepseek) → Control (qwen) → Receipt (codex2), then a codex2 ledger. SUPERSEDED by the MASS run (wf wohhmsn1o) which reroutes Minimalist to gemini-API + grok across two disjoint passes. Receipts SCRATCH_DIAGNOSTIC.

## The four verdicts — all REJECT_LIFT (MSS "presume less" held)
| Projection | Verdict | Weakest admissible carrier | Why the lift failed |
|---|---|---|---|
| density_rho | **REJECT_LIFT** | finite quotient `X/~_P` + classical outcome weights | Lift conceded; Control's trace-to-measure test reproduces Born probs by a classical measure on the quotient. Matches rung-0 fleet (ρ installed). |
| **spinor** | **REJECT_LIFT** (sharpest) | double cover + finite cyclic `Z_N` phase/bin label | Lift argued continuous U(1) phase is load-bearing; Control's FRIQ test (finite probe resolution `Δθ=2π/N`) showed a finite `Z_N` reproduces every distinguishable fringe → continuous Hopf/U(1) is unobservable metadata under finite probes. |
| qca_ordered_update | **REJECT_LIFT** | ordered local update on `X/~_P` | Noncommutativity is carried by discrete ordered composition; no Hilbert/ρ needed. Separates non-commutativity from quantum structure. |
| entropy_von_neumann | **REJECT_LIFT** | Shannon entropy of probe-outcome distributions | von-Neumann/ρ entropy is packaging unless probes directly expose coherence. |

**The pattern:** all four reject upward lifts, but each by a *different* weakest carrier and failure point — not one generic argument. Consistent extension of the rung-0 fleet: under **strictly finite probes**, even the continuous lifts (Hopf/spinor) are *installed, not forced* — a finite `Z_N` suffices.

## The runbook's OWN weak points (codex2 ledger flagged these — the process self-critiquing is the point)
1. **Minimalist unavailable on 2/4** (gemini hit HTTP 429 quota mid-run) → density_rho + entropy verdicts lean on MSS-default + Control, not a complete Minimalist-first triad. Re-run those two when quota resets.
2. **Control-Auditor is "too decisive" while controls are NARRATIVE.** Each control needs an executable artifact: exact probe suite `P`, the mapping, a pass/fail criterion, and a negative control. Until then it can reject lifts on a clever-sounding but unrun test.
3. **⚠️ Load-bearing caveat: the finite-probe framing may make continuous lifts fail BY CONSTRUCTION.** The runbook needs an explicit test for when *increasing probe resolution forces a genuine lift* rather than just a finer finite quotient. (Same class as the emergence-sim rounding artifact — a framing that can only ever produce one answer.)
4. Project-down maps asserted "in spirit," not shown per lift.
5. Receipts are adjudication-grade (no paths/seeds/hashes/rerun) — not canonical evidence-grade.

## Disposition
The runbook is a working process: it presumed less, rejected unforced lifts with distinct controls, named residuals, and honestly reported its own limits — disciplined non-collapse. **Next to turn adjudication-grade → evidence-grade:** make the controls executable (weak point 2), and build the resolution-forcing test (weak point 3) so "reject continuous lift" is a finding, not a framing artifact. Do NOT promote these verdicts past SCRATCH until that is done.
