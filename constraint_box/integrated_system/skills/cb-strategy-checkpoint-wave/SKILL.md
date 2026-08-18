---
name: cb-strategy-checkpoint-wave
description: Run a contained, inactive strategy checkpoint after failure and repair; compare object impact, scope, rival memory, and recency without voting or promotion.
---

# CB strategy-checkpoint wave

This candidate runs after a verified failure and an isolated repair. It is a
deterministic checkpoint, not a strategy council and not a repair runner.

The packet must bind one target to exact before/after repair artifacts, a
verified failure receipt, a verified repair-candidate receipt, a sealed context
epoch, a read-only branch-memory snapshot, and current/ablated strategy
projections. The parent validates every source digest and runs four distinct
children in the order declared by `wave.json`:

The caller must also provide `expected_source_set_sha256`. It is the SHA-256
of canonical JSON (`sort_keys`, compact separators) for the source-hash object
containing `parent_skill`, `runner`, `trusted_validator`, `definition`, and a
`children` map of each child `skill` and `script` hash. These are the fixed
candidate `SKILL.md`, runner, `wave.json`, trusted validator, and child source
bytes. The runner checks this caller value before and throughout execution; it
never recaptures a replacement baseline.

1. `cb-impact-vs-output-auditor` checks that the repair is classified as an
   artifact/metric/impact observation; it cannot turn an output into impact.
2. `cb-resource-expansion-cell` compares the authorized and used resource
   vectors from the exact repair artifact.
3. `cb-branch-failure-memory` is called only through its read-only resurrection
   check; the snapshot is never appended to or changed.
4. `cb-recency-bias-auditor` compares the exact current and latest-delta-
   ablated projections.

The parent preserves all child findings, contradictions, disagreements, and
minority branches. A fixed precedence table in the receipt compiles one
non-voting checkpoint disposition: `continue_candidate`, `revert_repair`,
`split_target`, `run_discriminator`, `reopen_rival`, `stop_satisfied`,
`reject_local_optimum`, `request_owner_amendment`, or `cancelled`.

The candidate is inactive (`candidate_state=INACTIVE`), model-free, and
does not start a provider, load an MMM, apply a repair, write memory, activate
a wave, select a winner, or promote a result. The CLI writes only an explicitly
requested parent receipt; normal execution is in-memory and replayable.

```text
python3 constraint_box/integrated_system/skills/cb-strategy-checkpoint-wave/scripts/run_checkpoint.py \
  --packet constraint_box/integrated_system/skills/cb-strategy-checkpoint-wave/fixtures/positive_packet.json \
  --out /tmp/checkpoint.receipt.json
```

Claim ceiling: source-bound checkpoint evidence and a deterministic,
non-voting routing disposition only. It is not a truth verdict, strategy vote,
repair, provider execution, MMM-read proof, activation, or promotion.
