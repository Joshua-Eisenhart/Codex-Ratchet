# Candidate manifold: classical bottom-up relational carrier, v2 (conditional, non-canonical)

**Supersession note:** this is a v2 restatement/improvement of
`candidate_classical_bottomup.md`, produced in a 2026-07-21 fuel-regeneration
task. Per the immutability rule, this is a NEW fuel-pool entry admitted
through the same gates as the original, never an overwrite. The original
document remains on disk unchanged, as its own honest history; nothing here
claims to invalidate it. Where this v2 differs from v1, the difference is
named explicitly in §7 below, not silently substituted.

Status: `exists` — an authored proposal, not executed code. Layer 0 reuses
one already-executed comparison (cited below, itself capped at `passes local
rerun`); Layers 1 and 2 are `PROPOSED_NOT_YET_SIMULATED`. This document is one
candidate among rivals in `system_v8/candidates/`. It is not canon and does
not admit anything. `promotion_allowed: false`, `formal_admission_allowed:
false`.

## 0. Stance and role

This candidate is bottom-up and classical: a finite relation (equivalently a
finite automaton or evolving graph) carrying the whole structure, never a
density matrix or spinor. It is deliberately minimal — as few layers as this
document can defend, with every presumption named and every omission marked.

Its role is comparative, not assertive: minimal_rival. It tests how much of
the shared frame (constraint on distinguishability, no assumed
identity/time/space/probability/object, MSS as weakest-persisting-evolving
structure, mutual nesting, finitude) a strictly relation-only carrier can
satisfy before it needs anything more. Spinor, density-matrix, or octonionic
rivals are expected to add structure this candidate omits; the open question
for them is whether that extra structure is admissible and needed, or merely
installed.

This puts the candidate in direct, acknowledged tension with `ROOT_CARD.md`
line 3 (owner verbatim): "everything has to run on density matrices if it is
the MSS." That line outranks this document. Where this candidate stalls,
that is evidence for the density-matrix requirement, not against it.

## 1. Ordered layer list

| Layer | Name | Maps to `system_v8/README.md` ladder | Carrier read |
|---|---|---|---|
| 0 | Probe-relative distinguishability relation | R0 (admissibility relation) | finite relation / probe-response incidence over a finite atom set |
| 1 | Ordered, branching relation-family under local admissible rewrite | R1 + R2 (nested compatibility, ordered relations) | a finite index set, one Layer-0 relation attached per index, a finite step relation between indices |
| 2 | Persistent-distinction closure | R3 (persistent distinctions) | the sub-relation of Layer-0 distinctions surviving every admissible Layer-1 path in the current finite index family |

Unchanged from v1: the list stops at Layer 2, deliberately (§6e names the
omission list). All three layers share one carrier type, reused at increasing
indexing depth, never replaced.

## 2. The carrier

One carrier throughout: a finite relation over a finite atom set, read either
as (a) an unrestricted set of admissible tuples, or (b) a probe-context to
response incidence map — both readings are the surviving frontier of the
executed comparison at
`system_v8/base_campaign/results/base_campaign_run_20260718/base_campaign_receipt.json`
(`base_frontier: ["b0_unrestricted_relation", "probe_response_incidence"]`),
and this candidate does not choose between them, per the shared frame's "MSS
... never absolute, possibly plural."

Explicitly rejected as ground carrier, each with a specific executed reason
(§6a): a plain pairwise graph, a partition/equivalence-class carrier, and a
deterministic finite-automaton/transducer. All three lost in the same
executed comparison.

## 3. What each layer presumes

Layer 0 presumes a finite atom set (F01), a finite set of admissible probe
contexts, and a response relation not assumed reflexive, symmetric,
transitive, or single-valued. It does not presume identity, equality,
equivalence-relation structure, probability, metric, order, time, causality,
algebraic composition, geometry, coordinates, or an observer.

Layer 1 presumes, additionally, a finite index set with a finite step
relation between indices — not assumed a strict total order (whether the
order is forced, merely installed, or idle is itself a Layer-1 test) — and a
finite local rewrite relation between (index, Layer-0-state) pairs, allowed
multi-valued. Nondeterminism responds directly to a named executed failure
(§6a): the one carrier that presumed a single-valued transition already lost.

Layer 2 presumes nothing beyond Layers 0 and 1: a finite closure, computable
because the index and path space are finite.

## 4. Persistence and evolution

Persistence: a Layer-0 distinction counts as persistent exactly when it stays
separated across every admissible Layer-1 path reachable in the current
finite index family — the repo's own R3 phrasing, read literally.

Evolution: a step through the local rewrite relation, which may be
multi-valued, producing a finite branching structure (a DAG or tree), not one
deterministic trajectory.

Nothing here carries a rate, a metric, or a continuous parameter — out of
scope by design (§6e). An "object," under this candidate, is a distinction
that survives this closure and nothing else. MSS candidacy first has a
referent at Layer 2, as a maximal set (possibly several incomparable such
sets) of distinctions stable under the Layer-1 branching relation.

## 5. Probe / distinguishability test per layer

Layer 0 probe — admissibility check: for every reference context, does the
candidate's admitted-outcome set equal the reference's observed-outcome set,
exactly, packet-relative? Direct reuse of `base_ratchet_campaign.py`'s own
`evaluate()` R1 test.

Layer 1 probes, both reused from the same executed script:
- relisting/order-reversal control (`RATCHET_SPEC.md` §8): permute or reverse
  the finite index-step sequence and recompute Layer 2. No change in the
  surviving-distinction set means the ordering was not load-bearing for this
  carrier under these probes — an informative negative, not a candidate
  failure.
- nesting-mutuality probe, reusing `base_ratchet_campaign.py`'s
  `nesting_tests()` fields `restricting_outer_changes_inner` and
  `order_T2T1_equals_T1T2`: does restricting a later index's admissible
  context change what an earlier index admits, and does composition order
  stay equal? A pass on mutual nesting needs at least one witnessed case
  where restricting the outer side changes the inner side (currently open,
  §6d, sharpened below).

Layer 2 probe — adequacy and demand-erasure controls (`RATCHET_SPEC.md` §8):
every distinction claimed persistent is checked against all admissible Layer-1
paths, exhaustively (F01 makes this finite). Demand erasure: remove one active
demanded distinction edge and confirm the closure's read of the other
distinctions does not spuriously move.

**Sharpened defeat condition (v2 addition, not in v1):** this candidate's
minimality claim is falsifiable in a single, concretely stated way — run the
relisting control on the current two tested packets (`ring`, and the second
packet named in `base_campaign_run_20260718`). If Layer 2's
surviving-distinction set is byte-identical before and after index reversal
on BOTH packets, the index was idle on the only evidence this document has,
and §6c's "possible order-smuggling" risk is resolved against this candidate
(the index adds cost, not distinguishing power, on this evidence) — a
concrete can-fail check, not a hypothetical one.

## 6. Honest weaknesses, deliberate omissions, and order risk

(a) Named prior negatives against this exact carrier family, already
executed, from `system_v8/base_campaign/results/base_campaign_run_20260718/base_campaign_receipt.json`
and `base_ratchet_campaign.py`:
  - Plain pairwise graph (`pairwise_graph`): over-admits by exactly 8 outcome
    pairs on both tested packets (`ctx_overadmitted_outcome_pairs: 8`).
  - Deterministic transducer (`deterministic_transducer`): on the `ring`
    packet, context `[0,0,0]` genuinely carries both outcomes `{0,1}` in the
    reference; the transducer can only return `null` there
    (`distinction_persists_under_restriction_path: false`).
  - Partition/equivalence-class carrier (`finite_partition`): `admitted()` is
    context-independent by construction — always `{0,1}`, discarding the
    probe context entirely.

  Layer 1's design choices (a relation rather than a function between steps,
  a full joint rather than pairwise-decomposed state) are direct, named
  responses to the transducer and graph failures — a reason to expect Layer 1
  to do better, not a demonstration that it does. Not yet executed.

(b) Layer 1 and Layer 2 remain `PROPOSED_NOT_YET_SIMULATED`, unchanged from
v1. Weakening the transducer's function to a relation could fail differently
— e.g. reintroducing pairwise-marginal over-admission if implemented as a
graph of (index, state) pairs rather than a genuine joint structure.

(c) Possible order-smuggling inside Layer 1, unchanged from v1, now with the
concrete can-fail check in §5 attached to it directly rather than described
only in prose.

(d) Nesting-mutuality is an open negative across every tested base candidate,
not a special weakness of this one: the one existing execution of
`nesting_tests()` found `restricting_outer_changes_inner: false` and
`order_T2T1_equals_T1T2: true` for all nine candidates it ran, including both
frontier members. This candidate holds that tension rather than resolving
it — it may mean mutual nesting needs a richer carrier (evidence for the
rivals), or that the two tested packets are too thin to exercise it yet
(evidence for more packets before ruling on carriers at all). Both readings
stay live.

(e) Deliberate omissions, unchanged from v1: probability or measure; metric
or geometric distance; continuous time; algebraic composition beyond finite
relation and intersection (no group, ring, module); Hilbert space; density
matrices; spinors; Clifford structure; quantum superposition; any entropy
formula; the entropy-geometry coface of `RATCHET_SPEC.md` §3; any drive,
gradient, or Axis-0 claim; any coupling or physical-bridge claim.

(f) Where this order might be wrong, unchanged from v1: static-then-dynamic
(Layer 0 fixed, then Layer 1 indexed) may be an artifact of exposition rather
than a forced order; deferring the nesting-mutuality probe to Layer 1 is a
choice, not a necessity; two incomparable Layer-0 realizations are both
retained rather than chosen between, per the anti-collapse rule.

## 7. What changed from v1 (named explicitly, per the supersession note)

- Added the sharpened, concretely stated defeat condition in §5 (byte-identical
  relisting-control check on the two named packets) — v1 named the relisting
  control as a check but did not commit to a specific pass/fail read on the
  currently available two-packet evidence.
- Restated §0's role explicitly as `minimal_rival`, matching this pool's
  `variation_slots` vocabulary (`fuel_gate/fuel_adequacy_gate.py`
  `SLOT_DESCRIPTIONS`), where v1 described the role in prose without naming
  the slot term.
- No change to the carrier, the layer list, the ordered probes, or the
  honest-weaknesses content beyond the additions named above — this v2 is a
  restatement, not a redesign.

**Witness / defeat condition, restated for this document as a whole:** this
candidate wins its minimality pitch over the pool's richer rivals only while
no weaker carrier matches its frontier and no relisting/nesting-mutuality
probe defeats its own ordering claim. It loses its minimality status the
moment a rival preserves all active distinctions with fewer declared
commitments; it loses its ordering claim the moment a relisting run changes
Layer 2's surviving-distinction set (which would instead validate the index
as load-bearing); and a witnessed case where restricting an outer Layer-1
index changes an inner one would flip §6d from open tension to a real
requirement this carrier must meet.
