Status: `exists` — an authored proposal, not executed code. This document is
one candidate among rivals in `system_v8/candidates/`. It is not canon and
does not admit anything. `promotion_allowed: false`,
`formal_admission_allowed: false`. Role: `structural_rival` — a genuinely
different carrier family from the pool's existing spinor/QIT, classical
finite-relation, and nonassociative-octonion members, framed as a
stress-variant: its whole claim rests on naming an explicit adversarial
stress it must survive, rather than a static structural description.

Provenance: authored by `xai_grok` (model `grok-build-0.1`, via the `grok`
CLI, `--max-turns 3 --always-approve`, single-turn `-p` prompt,
`--cwd` pointed at an isolated scratch directory with an explicit
instruction not to write files or run tools). The verbatim prompt and the
full session record are in `fuel_gate/manifests/current_pool_provenance_manifest.json`
under this file's `provenance.prompt_lineage`. Body below is the model's
output, reproduced as generated (only this status/provenance preamble was
added on top).

---

# Finite Stochastic Transition-Count Carrier

If the minimal persisting structure of a finite ratchet must preserve exactly the same set of admitted outcomes when atom labels are permuted within a fixed finite set and when a bounded random fraction of recorded observations is dropped, then a carrier built solely from raw finite counts of (context, response) transitions may serve as that structure.

## Carrier identifier and nesting / order identifier

Carrier identifier: `stochastic-transition-count-v1`

Nesting and order identifier: `fuel-adequacy-pool/structural_rival/stress-variant/stochastic-counts/order-3`

## Assumptions the carrier installs

The carrier installs these assumptions:

- All structure relevant to admission is exhausted by the finite matrix of observed transition counts between discrete atoms.
- Atom labels possess no intrinsic identity; only their co-occurrence statistics within the count table matter.
- Observations are discrete, countable events collected inside a fixed finite window.
- The ratchet's admission rule depends only on count-derived properties that remain unchanged under finite permutations of a closed label set and under uniform random subsampling up to a known bound δ.
- Both the label set and the dropout bound are declared in advance and treated as fixed parameters of the stress model.

## Probe / distinguishability test

Construct the raw count table from the finite collection of observed (context, response) pairs. Draw a random permutation of the atom labels and independently select a uniform random subset of observations whose size is at most the declared dropout bound; remove those observations from the table. Re-apply the ratchet's admission rule to the stressed table and compare the resulting set of admitted outcomes against the set obtained from the unstressed table. The probe records whether the admitted-outcome set is identical after stress.

## Defeat condition

The carrier loses its claim to supply the minimal persisting structure if any permitted stress produces a different admitted-outcome set. It would flip under an unbounded family of label permutations or under dropout that exceeds the stated fraction. It can-fail when the generating process is non-stationary inside the observation window or when two distinct processes yield identical marginal counts. A witness of defeat is any pair of count tables related by a stress inside the declared bounds that nevertheless induce unequal admitted sets. The carrier wins if the admitted set is exactly preserved for every stress inside the bounds. The account is falsifiable by concrete exhibition of one bounded label permutation plus one bounded dropout that changes the admitted set while leaving the count table otherwise well-formed.

## Known failure modes

- Adversarial dropout that removes precisely the transitions required to distinguish otherwise confusable count profiles.
- Label alphabets whose size changes during the observation window, so that no fixed finite permutation group applies.
- Dynamics whose relevant distinctions require order, timing, or higher-order joint counts not encoded in the first-order transition matrix.
- Admission rules that inspect absolute label names or external metadata absent from the count table.
- Continuous or countably infinite label spaces for which the finite-permutation model is undefined.
- Observation processes whose dropout is correlated with label identity in ways the uniform random model does not capture.

## Status and constraints

This document is prose-only. It contains no executable code, no formal grammar, and no implementation.

`promotion_allowed: false`

`formal_admission_allowed: false`

This is a candidate among rivals inside the fuel-adequacy pool of Codex-Ratchet. It is not canon. It does not admit anything.
