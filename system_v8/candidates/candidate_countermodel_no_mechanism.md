# Candidate manifold: lookup/replay countermodel, no relational mechanism (conditional, non-canonical)

Status: `exists` — an authored proposal, not executed code. This document is
one candidate among rivals in `system_v8/candidates/`. It is not canon and
does not admit anything. `promotion_allowed: false`,
`formal_admission_allowed: false`. Role: `countermodel` — it exists to
preserve the observed pair-level result tables WITHOUT the claimed
mechanism, per the fuel-adequacy gate's slot definition
(`fuel_gate/fuel_adequacy_gate.py`, `SLOT_DESCRIPTIONS["countermodel"]`).

## 0. Stance and role

`candidate_classical_bottomup.md` claims a specific mechanism: a finite
relation, indexed and closed under admissible rewrite, where Layer 2's
persistent-distinction set is produced BY genuine nesting/composition over
Layer 1's branching structure (`base_ratchet_campaign.py`'s
`nesting_tests()` fields `restricting_outer_changes_inner` and
`order_T2T1_equals_T1T2`). This candidate asks the countermodel question the
fuel-adequacy gate names: can something with no relational-composition
mechanism at all reproduce the same pair-level outcome tables that
mechanism is credited for?

The answer this candidate proposes: yes, for the two tested packets on
record (`system_v8/base_campaign/results/base_campaign_run_20260718/base_campaign_receipt.json`),
a flat lookup table keyed directly on `(context, packet_id)` — with no
index set, no step relation, no closure operation, and no nesting at all —
reproduces every `admitted()` call the classical-relational carrier makes,
because the two tested packets are finite and the lookup table is built by
replaying the same reference outcomes the relational carrier was itself
fitted against. If true, the pair-level result table is evidence for
"a finite carrier exists that matches the reference," not evidence for
"relational composition/nesting is what does the work" — the two are
conflated unless a probe separates them.

## 1. The carrier

`carrier: lookup_replay_table` (a dict from `(context_tuple, packet_id)` to
the reference's own observed-outcome set, built once by reading the
reference receipt and never touched again). No finite relation, no index
set, no step relation, no rewrite, no closure — the operations
`candidate_classical_bottomup.md` names as its Layers 1 and 2 have no
analogue here at all. `nesting_order: none_flat_lookup` — there is no
schedule, ordered or otherwise; the table is queried once per context, flat.

This is deliberately the minimal-mechanism reading of "carrier" the frame
allows: a bare finite map, admissibility-checked against R0 exactly the way
Layer 0 of the incumbent is, but with nothing added on top.

## 2. What it presumes

It presumes: a finite set of `(context, packet_id)` keys (F01, same as
every other candidate in this pool); that the reference-outcome sets used
to populate the table were themselves already computed once
(`base_ratchet_campaign.py`'s own `evaluate()`, already executed and
cited). It presumes nothing about ordering, indexing, branching, or
closure — those are exactly the presumptions this candidate is built to
omit, on purpose, as the countermodel's whole point.

It does not presume: an index set, a step relation, multi-valuedness of
transitions, or any nesting-mutuality structure. Where
`candidate_classical_bottomup.md` Layer 1 presumes a finite step relation
between indices, this candidate has no Layer 1 at all.

## 3. Probe / distinguishability test

Layer-0-equivalent probe — admissibility check, reused directly: for every
reference context in the same two tested packets
(`base_campaign_run_20260718/base_campaign_receipt.json`), does the
lookup table's admitted-outcome set equal the reference's observed-outcome
set, exactly, packet-relative? This is the identical test
`candidate_classical_bottomup.md` §5 runs for its own Layer 0. Because the
lookup table is built BY replaying the same reference, this probe is
expected to pass trivially — that is the countermodel's claim, not a
surprise result.

Nesting-mutuality probe (the decisive one): apply
`base_ratchet_campaign.py`'s own `nesting_tests()` fields
(`restricting_outer_changes_inner`, `order_T2T1_equals_T1T2`) to this
carrier. Because there is no index set and no step relation, both fields
are undefined/inapplicable by construction for this carrier — there is
nothing to restrict and no composition order to vary. This is the
countermodel's central exhibit: the incumbent's own recorded result on
these same two packets already reports
`restricting_outer_changes_inner: false` and `order_T2T1_equals_T1T2: true`
for every one of the nine tested base carriers, including the incumbent
itself (`candidate_classical_bottomup.md` §6d). A flat lookup table with NO
nesting mechanism at all reproduces that same null pattern (nothing to
restrict, nothing to reorder) at zero relational cost — which is exactly
the countermodel's defeat condition against the incumbent's minimality
pitch, not against the pool as a whole.

## 4. Predictions

- On the two currently tested packets, the lookup table matches every
  admitted-outcome set the classical-relational carrier matches, because
  both were fitted against the same reference receipt.
- The lookup table CANNOT extend to any context outside the two tested
  packets' observed key set — it has no generative rule, only stored
  answers. A rival wins over this countermodel the moment a probe supplies
  a context that was never in the training receipt: the lookup table
  returns nothing (undefined key), while a genuine relational mechanism is
  predicted to still produce SOME admissibility judgment from its rewrite
  rule.
- If a fresh packet (not `base_campaign_run_20260718`'s two) is run and the
  lookup table is extended by simply appending its outcomes too, the
  countermodel still reproduces the pair-level result table — this would
  show the pair-level metric itself cannot distinguish mechanism from
  memorization, strengthening rather than weakening this countermodel.

## 5. Rivals

- `candidate_classical_bottomup.md` (the incumbent this countermodel
  targets directly)
- `candidate_spinor_qit.md`, `candidate_topdown_12to0.md`,
  `candidate_foreign_nonassoc.md` (the other pool members; this
  countermodel does not target their specific claims)

## 6. Known failure modes — the witness / defeat conditions

This countermodel loses its whole point, and is falsified as a countermodel
(though it may still stand as a degenerate baseline), under any of the
following witnessed conditions — these are the can-fail conditions the
countermodel's own honesty depends on:

- **Out-of-sample defeat condition (the main one):** if a probe context
  outside the two tested packets' key set is supplied and the incumbent's
  relational mechanism produces a correct, checkable admissibility
  judgment on it while this lookup table cannot (by construction it has no
  answer for an unseen key), the countermodel loses its claim to be a
  genuine rival mechanism — it would show the incumbent's structure carries
  real generalizing work this flat table does not.
- **Falsifiable on packet-count, not just packet-identity:** would flip if
  even a third already-executed packet from the same receipt family shows
  the lookup table failing to match the reference (i.e., the reference
  outcome set itself is not exactly reproducible by a flat replay — this
  has not been checked and is an open gap, named here rather than hidden).
- Known limitation, named directly rather than smoothed: this candidate
  wins the pair-level table test only because "pair-level result table"
  and "training set the table was fitted to" are, on these two packets, the
  same finite object. That is the whole finding this countermodel exists to
  surface, not a defect to explain away.
- Known limitation: no probe in this document (or anywhere in the current
  pool, to this candidate's knowledge) yet tests whether the incumbent's
  relational mechanism ALSO only reproduces its training receipt — if it
  does, the incumbent and this countermodel are, on current evidence,
  indistinguishable at the pair-level, and the mechanism claim is
  unsupported by any probe run so far. This is a real, currently open gap,
  not resolved by this document.

## 7. What would flip this candidate

A witnessed context outside `base_campaign_run_20260718`'s two packets
where the relational mechanism in `candidate_classical_bottomup.md`
produces a checkable, correct admissibility judgment that this flat lookup
table structurally cannot (undefined key) would be the decisive win-if
condition for the incumbent's mechanism claim over this countermodel. Until
that probe is run, the pair-level result table alone does not distinguish
"relational composition happened" from "a stored answer key was replayed."
