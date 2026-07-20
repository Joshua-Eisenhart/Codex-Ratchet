# Desktop fuel-bearing execution contract

This is an execution contract, not another request for a broad audit.

## Gate 0: preserve and verify

- Verify `MANIFEST.json`, `SHA256SUMS`, and donor ZIP integrity.
- Observe Ratchet, simulations, and Leviathan commits and dirty state.
- Preserve all user-owned changes; use isolated worktrees or cold copies.
- Do not publish, merge, or rewrite canonical state.

## Gate 1: replay the executed floor

Run `./RUN_LOCAL_EXACT.sh`. Require deterministic agreement with:

- eight anonymous sources;
- 25 obligations;
- all obligations scheduled exactly once;
- 33 proposal-fuel entries retained;
- no source-family label in mathematical obligations;
- no scalar epistemic priority; and
- no NumPy claim path.

Any mismatch blocks promotion and becomes a new residual.

## Gate 2: native Leviathan

At the observed local Lev commit:

1. install the plugin in an isolated Lev worktree;
2. adapt only the pinned SDK binding surface;
3. typecheck and prove registry discovery;
4. invoke `ratchet:run-source-balanced` natively;
5. capture start, completed/held, and failure events;
6. ingest the 78-node context graph;
7. exercise interruption/resume over the fair queue; and
8. return exact diffs and native receipts.

Leviathan may choose what can run next under resource/dependency constraints.
It may not choose truth, MSS, an ontology, or a preferred owner hypothesis.

## Gate 3: source-native answers

Begin with fair round 0. After obligations are frozen, use provenance only to
locate the real executable source.

- For plural deterministic completions, run listed discriminating contexts.
- For relation-only sources, request a genuinely new coordinate, longer
  history, or continuation and compete a bounded transducer against the exact
  relation.
- For runtime-gap sources, repair locally and rerun without promoting the old
  projection.
- For held-out kills, preserve Purgatory and re-offer only after material
  context change.

Use existing simulation engines. An authored fixture or archived agreement
envelope cannot substitute for a fresh raw leg.

## Gate 4: plural successor and recursive recomputation

Build a packet of every evidence-licensed candidate, not one winner. Run its
measurements and controls, compute plural MSS frontiers, return new records,
and recompute the complete boundary. At least one frontier must change or the
return must identify the exact source interface that prevents recursive motion.

## Gate 5: independent engines and solvers

Run Julia, JAX, PyTorch, Z3, and cvc5 lanes independently when installed. Mark
only unavailable lanes `BLOCKED_DEPENDENCY_UNAVAILABLE`; continue the rest.
NumPy is not allowed on a claim path.

## Gate 6: broader fuel remains alive

Return every fuel-registry entry with one of `RUN`, `HOLD`, `FAIL`, `PARK`, or
`NOT_RUN`. Recent saliency, donor size, labels, and successful tiny calibrations
cannot delete or silently deprioritize a lane. Owner hypotheses can seed typed
candidates and decoys only after evidence licenses are checked.

## Required return

One ZIP containing native Lev evidence, source executions, successor packet,
recursive frontier receipts, independent engine/solver outputs, all state
answers, isolated diffs, logs, controls, exact blockers, and checksums.
