# Disposition of the external “L5 answered” claim

## Claim received

The archive `129_claude_science_working_ratchet_v0_4_2_L5_answered.zip` adds a ten-line note asserting that an external
directory named `system_v7/sims/l5_reaudit_data_driven_v1/` contains a clean audit with data-fitted candidates, an AST
answer-key fence, three seeded splits, and headline RMSE values `0.0143` versus `0.0588`.

## Materialization audit

- The named directory is absent from the supplied archive.
- No source program, input data, split indices, raw predictions, result JSON, audit, environment lock, or file hashes
  for the claimed experiment are included.
- The connected repository `Joshua-Eisenhart/Codex-Ratchet` was searched by the exact directory name and by the claim
  wording; no indexed file or commit was found.
- Direct path checks returned not found on every visible branch:
  - `main`
  - `session/r0-three-engine-probes`
  - `estate/desktop-gated-maintenance-20260702`
  - `codex/sync-clean-main-20260619`
  - `codex/source-cleanup-checkpoint-20260506`
- The actual `ratchet/manifold_l5_reaudit.py` inside the “answered” archive is unchanged from the killed v0.4
  answer-key instrument/tombstone lineage. Its existing result is not the claimed new experiment.

## Ratchet disposition

```text
status: CLAIM_ONLY__SOURCE_MISSING
locally_executed: false
independently_auditable: false
promotion_allowed: false
may_change_L5_state: false
```

The numerical assertion is preserved as an authored dig seed. It is not an execution receipt and cannot answer L5.
The independent audit shipped beside this note does not attempt to reproduce those exact unmaterialized numbers; it
tests the bundled observations and records its own source, math, outputs, and ceiling.

## Evidence-complete re-entry condition

The external claim may re-enter the Ratchet only with all of the following:

1. executable source and candidate compiler grammar;
2. immutable input data and exact train/validation/test splits;
3. answer-key/leakage audit source and output;
4. raw per-candidate predictions, not only aggregate RMSE;
5. every negative and permutation control output;
6. environment/dependency record and random seeds;
7. file hashes and a rerun command;
8. a claim ceiling that distinguishes predictive equivalence from manifold admission.

