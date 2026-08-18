---
name: cb-strategy-framing-wave
description: Compose six deterministic strategy-framing cells before Decision while preserving the portfolio antichain and tensions without selecting a winner.
---

# CB strategy-framing wave

This directory is an inactive `NEW_CANDIDATE`.  It is a model-free parent
controller over six independently reviewed deterministic leaves:

1. `cb-object-boundary-cell` — restate the supplied ObjectCard boundary;
2. `cb-strategy-portfolio-cell` — retain direct, alternative, reframe, back,
   wildcard, and stop branches as an antichain;
3. `cb-multi-horizon-cell` — record immediate, downstream, maintenance, and
   long-horizon considerations;
4. `cb-option-value-retreat-cell` — map reversible probes, commitments, hold
   and retreat conditions, and preserved options;
5. `cb-dependency-sequence-cell` — order prerequisites by finite information
   value; and
6. `cb-strategy-discriminator-cell` — design the cheapest finite observable for
   a named disagreement without running it or choosing a strategy.

The runner accepts one strict
`constraintbox.strategy-framing-wave-input.v1` packet containing an exact
target, ObjectCard, context, parent operation, and exactly one current input
for each child.  It preflights the complete child set before launching any
child, resolves only files below the contained skills root, invokes the six
children in definition order, and verifies every receipt against its exact
current input.  A missing, extra, duplicate, rebound, tampered, collapsed, or
source-drifted child refuses before a parent completion can be sealed.

The ObjectCard is exactly `constraintbox.object-card.v1` with
`{schema, object, success_condition, hard_constraints, non_objectives,
target}`.  Its scalar fields are nonblank, its two list fields contain only
nonblank strings, and its target equals the packet target.  The context is
exactly `constraintbox.strategy-framing-context.v1` with
`{schema, epoch, contradictions, disagreements}`; the epoch is nonblank and
both retained surfaces are lists of nonblank strings.  Unknown or missing
fields refuse before any child launch.  Each child request is closed against
its reviewed leaf request keys and is checked by the leaf's pure request
validator before any child runs.

The parent output keeps the complete portfolio antichain and records supplied
and child-derived tensions/disagreements.  It never emits a winner, decision,
implementation, activation, provider call, or MMM claim.  It records
`route_truth=NOT_FULL` with `route_truth_label=NOT_FULL/model_free`, and marks
MMM/provider evidence not applicable rather than fabricating it.

The parent skill, definition, trusted validator, runner, and every child
source/skill are pinned and re-attested before each child, after each child,
and immediately before an explicitly requested receipt write.  Drift stops
the run while retaining the truthful launched prefix and unlaunched suffix.
Leaf cancellation is verified against the exact child input with the current
leaf verifier and an exact replay; a status dictionary alone is never
accepted as cancellation evidence.

## Run

```text
python3 constraint_box/integrated_system/skills/cb-strategy-framing-wave/scripts/run_framing.py \
  --packet /path/to/strategy-framing.packet.json \
  --out /tmp/strategy-framing.receipt.json
```

Use `--verify RECEIPT` to verify an existing receipt against the exact packet.
Set `CB_SKILLS_ROOT` to a contained `integrated_system/skills` directory when
running from an extracted package.  The runner is stdlib-only and never calls
a model or provider.  It writes only the explicitly requested parent receipt.

## Terminals

- `COMPLETE` — all six children ran and their exact receipts verified;
- `REFUSE` — packet, source, definition, path, child, portfolio, or receipt
  custody failed; and
- `CANCELLED` — parent or a child requested cancellation; no later sibling is
  launched.

## Claim ceiling

Bounded model-free strategy framing and receipt verification only.  This wave
does not prove a strategy, pick a winner, make a Decision, implement a plan,
measure a discriminator, claim provider/MMM delivery, activate, or promote.
