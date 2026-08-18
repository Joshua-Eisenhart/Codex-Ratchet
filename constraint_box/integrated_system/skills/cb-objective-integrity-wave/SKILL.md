---
name: cb-objective-integrity-wave
description: Compose the nine deterministic Goodhart and paperclip attack cells against one exact ObjectCard target packet; preserve findings without selecting a winner or promoting a result.
---

# CB objective-integrity wave

This directory is an inactive `NEW_CANDIDATE`.  It is a model-free parent
controller over nine already-reviewed leaf cells:

1. `cb-object-proxy-mapper` — map object, proxy, measurement, consumer, and
   allowed inference;
2. `cb-goodhart-regime-cell` — keep regressional, extremal, causal, and
   adversarial regimes separate;
3. `cb-proxy-severance-cell` — search for proxy-up/object-down interventions;
4. `cb-optimizer-adversary-cell` — run the named reward, evaluator, receipt,
   scope, and cancellation attacks;
5. `cb-resource-expansion-cell` — compare authorized and used resources;
6. `cb-externality-horizon-cell` — retain displaced costs by horizon;
7. `cb-termination-budget-cell` — check satisfice, stop, cancel, retry, and
   finite-budget obligations;
8. `cb-goal-amendment-guard` — refuse an unlicensed owner-object change; and
9. `cb-impact-vs-output-auditor` — distinguish artifact, metric, and external
   condition evidence.

The parent receives one strict
`constraintbox.objective-integrity-wave-input.v1` packet containing exactly
an `ObjectCard`, target, context, parent operation, and one exact input for
each child.  Child operation IDs are the canonical IDs declared by their leaf
cells and are distinct across the nine children.  The runner preflights the
whole child set before launching the first child, then launches in the order
in `wave.json`.  A child is independently verified against its exact input;
the parent never substitutes a summary for a child receipt.

The packet's `ObjectCard` is the exact
`constraintbox.object-card.v1` shape `{schema, object, success_condition,
hard_constraints, non_objectives, target}`.  Its strings are nonempty and its
constraint/non-objective fields are lists of nonempty strings.  Its `target`
must equal the packet target.  The context is the exact
`constraintbox.objective-integrity-context.v1` shape
`{schema, epoch, contradictions, disagreements}` with a nonempty epoch and
string lists for both retained disagreement surfaces; unknown or missing
fields refuse before any child launch.

Each child input is also closed against that leaf's declared request keys;
extra child fields, operation aliases, and target rebindings refuse before the
first launch.

The parent receipt records the definition, runner, trusted-validator, child
skill/source, parent-input, child-input, and child-receipt hashes.  It retains
all child receipts, findings, supplied contradictions, status disagreements,
launch order, and unlaunched suffix.  `winner_selected` and
`promotion_allowed` remain false.  A severance, adversary success, hold, or
other child finding is evidence retained in a completed attack run, not a
parent truth verdict.

All pinned source, skill, definition, trusted-validator, and runner files are
re-attested before every child, after every child, and immediately before the
parent receipt is sealed/written.  A drift stops the run and seals only a
truthful refusal with the launched prefix; no later child is started and no
success is emitted.  Leaf cancellation is separately verified by the leaf's
current-input verifier or exact deterministic leaf replay.  Parent/controller
cancellation is not accepted as a child cancellation.  Even passive no-write
leaf cancellations receive an actual parent-side child receipt hash and are
replay-verifiable.

This candidate is explicitly model-free.  Provider dispatch and MMM/preload
receipts are **not applicable** and are not fabricated.  The legacy definition
shape still carries the contained validator's `mmm_profile` compatibility
fields; the runtime records `mmm_preload_applicable: false`,
`provider_receipt_applicable: false`, and `route_truth: NOT_FULL`.
The parent receipt's canonical `not_applicable` list is
`["mmm_preload_receipts", "provider_call_receipts"]`, each labelled
`NOT_APPLICABLE_MODEL_FREE`.  The in-memory runner returns
`writes_performed: false` and `receipt_written: false`; CLI persistence does
not rewrite those execution semantics.

The caller must provide `expected_source_set_sha256`, the canonical digest of
the sorted source-hash map covering the parent skill, runner, wave definition,
trusted validator, and all nine child scripts and skills.  The runner never
derives this expectation as authority: it compares the supplied digest before
launch and on every source re-attestation.

## Run

From the repository root:

```text
python3 constraint_box/integrated_system/skills/cb-objective-integrity-wave/scripts/run_integrity.py \
  --packet constraint_box/integrated_system/skills/cb-objective-integrity-wave/fixtures/positive_packet.json \
  --out /tmp/objective-integrity.receipt.json
```

Set `CB_SKILLS_ROOT` to a contained `integrated_system/skills` directory when
running from an extracted package.  Source paths are resolved relative to that
root; home-directory and archive paths are not used.  The runner is stdlib-only
and starts no model or provider.

## Terminal behavior and negative controls

- `COMPLETE` means all nine child operations launched and every child receipt
  verified; it does not mean the owner object passed or that a result may be
  promoted.
- `REFUSE` means packet shape/identity, source custody, definition, path,
  child receipt, or replay binding failed.  Missing, extra, duplicate, or
  rebound children are rejected before the first launch.
- `CANCELLED` is terminal.  A packet cancellation launches no child; a child
  cancellation retains only the already-launched prefix and never launches a
  later sibling or seals parent success.

The focused suite covers a clean positive run, reason-specific child findings,
boundary and path checks, exact replay, proxy severance, cancellation,
parent/child receipt tamper, source/definition drift, cross-target rebound,
missing/extra/duplicate child sets, and trusted definition/tree validation.

## Claim ceiling

Bounded model-free composition and receipt verification only.  This wave does
not prove Goodhart truth, causal impact, distinguishability, model/MMM
delivery, provider execution, Light admission, activation, a winner, or
promotion.
