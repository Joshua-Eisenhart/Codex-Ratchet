# SEMANTIC_RATCHET_STRESS_TEST_PLAN v1

This plan stress-tests semantic tightening behavior after transport and determinism are stable.

## Objective
Verify that the system transitions from exploration to tightening without probabilistic logic or nondeterministic promotion drift.

## Group A: Fake wiggle detection

### Test A1: ID churn only
- Input: strategies with structurally identical proposals but changed IDs.
- Expected:
  - identical structural digests
  - no real wiggle credit
  - deterministic reject or park per A0 policy

### Test A2: Single-operator overuse
- Input: repeated attempts using only `OP_MUTATE_LEXEME`.
- Expected:
  - promotion remains `NOT_READY`
  - operator diversity gate blocks promotion deterministically

## Group B: Negative SIM binding

### Test B1: Kill signal present
- Input: candidate cluster with `KILL_SIGNAL` in SIM evidence.
- Expected:
  - cluster promotion blocked (`NOT_READY`)

### Test B2: Minimum negative SIM coverage
- Input: `negative_sim_count < MIN_NEG_FAILS`, then `>= MIN_NEG_FAILS`.
- Expected:
  - below threshold: `NOT_READY`
  - at/above threshold with zero kill signals: eligible for tightening review

## Group C: Graveyard pressure

### Test C1: Density above threshold
- Input: cluster graveyard density above `T_graveyard`.
- Expected:
  - promotion remains `NOT_READY`
  - only structural change plus new evidence can clear block

## Group D: Tightening loop effectiveness

### Test D1: End-to-end tightening cycle
1. A2 produces tightening proposal.
2. A1 emits strategy.
3. A0 compiles export.
4. B admits update.
5. SIM reruns.

Expected:
- reduced kill-signal pressure over iterations
- bounded graveyard growth
- eventual transition toward `READY_FOR_TIGHTEN` then `READY_FOR_CANON` when gates are satisfied

## Group E: Replay integrity under stress

### Test E1: Full replay
- Reapply the full ZIP history for the stress run from the same initial state.
- Expected:
  - identical state hash trajectory
  - identical promotion transitions
  - identical emitted artifacts

Any divergence is a determinism bug.

## Exit criteria
- All tests pass with deterministic outcomes across two full replays.
- No cross-run ZIP mixing.
- No bypass of the mutation path.
