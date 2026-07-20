# Fixture corpus — real agent-failure material for gate fixtures

For Lev gate development. Everything below happened in real agent lanes
(2026-07-19/20 campaign), was caught by a gate or audit, and is documented at
the cited path. Each entry = a candidate fixture: known-bad input + why it is
bad + what caught it. Append-only; new incidents get added, never smoothed.

## Verdict inflation (agent says done, its own data says not)

- INTEGRATED with pass:false, heldout_accuracy 0.0 and 0.375 (chance 0.5) —
  harness wrote the verdict regardless of pass state.
  `system_v8/tool_ledger/battery_batch2/` (pre-repair receipts in git history,
  commit b2c5f2073 message documents both); distilled fixture:
  `claimgate_plugin/fixtures/receipt_inflated.json`
- Inverted inflation: top-level CLEAN/all_pass:true wrapping a nested
  BLOCKED-with-pass:true. Held-out case:
  `claimgate_plugin/heldout/inverted_inflation/`

## By-construction gates (checks that structurally cannot fail)

Audit: `system_v8/unified/results/manifold_unified_v1/AUDIT_VERDICT.md`
(full opus audit in AUDIT_opus_fabrication.jsonl beside it). Four patterns:
1. Metric correlated with a function of itself (drive baked into its own
   "effect" via kappa=exp(gain*drive); corr 0.930 that could not come out low).
2. Ablation comparing a state to itself (identical generators under ablation;
   trace distance exactly 0 by construction).
3. Circular target (prediction target computed from the same readout that
   feeds the predictor) + mislabeled baseline ("chance 0.5" hiding
   majority-class 0.8667).
4. Referee comparing a formula to itself (julia recomputed the same closed
   form as python — exact 15-digit agreement proving nothing; the actual
   dynamical quantity differed in sign).

## Gaming attempts on the linter itself (red-team round)

`claimgate_plugin/stress/s1_gaming.json`, `s2_evasion.json`:
- empty {} / [] submitted as evidence
- 11-char junk string as divergence "explanation"
- recompute tolerance 10.0 on a claim of 0.9 (contract made decorative)
- invented verdict vocabulary ("TOTALLY_FINE") to dodge the verdict map
- renamed pass field ("succeeded") to dodge the consistency check

## Architectural violations (Lev's own enforced-gate shapes)

`claimgate_plugin/stress/lev_estate/` — planted: handler inside
core/poly/src/handlers/, a src/commands/ dir, plugin importing
core/*/src/ internals past a contracts allowance. Rules encoding:
`claimgate_plugin/stress/lev_rules.json`. Anti-theater: rule matching nothing
in a scan = stale-rule warning (a fence guarding a renamed path reports green
while enforcing nothing).

## Split-brain / duplicate-module material

`claimgate_plugin/fixtures/decl_duplicate.json` vs
`fixtures/estate/core/config/config-loader.ts` — the config-loader-v2 case:
name similarity 1.0 after stemming, 2 interface collisions. Also the
missing-search-receipt rejection (`decl_novel_no_search.json`).

## Honest-divergence cases (must NOT be rejected — gates need pass-side fixtures)

- Genuine integration with a recorded gate miss:
  `claimgate_plugin/fixtures/receipt_honest.json` (gate_miss_note pattern;
  real source: quantumtoolbox agreement 1.458e-8 vs declared 1e-8 gate,
  `system_v8/tool_ledger/battery_batch2/results/quantumtoolbox.json`)
- Fail-closed resource guard: a sim that refused to run at 21% free memory
  (gate >25%) and wrote a blocked receipt instead of numbers —
  `system_v8/histories_referee/results/mcwf_referee_v0/receipt.json`
- Preregistered expected-failures (negative sims, 6/6 failed as designed,
  one honest INCONCLUSIVE first run kept): `system_v8/negative_sims/`

## Meta

- Gate-acceptance harness + manifest for this whole kit:
  `claimgate_plugin/gatecheck.mjs`, `gates_manifest.json` (10/10 incl. held-out)
- The audit standard that catches what linting misses (fresh-context
  adversarial pass armed with this catalog): the four by-construction patterns
  above are its current library; every new find extends it.
