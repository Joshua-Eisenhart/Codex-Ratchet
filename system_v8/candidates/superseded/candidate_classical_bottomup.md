# Candidate manifold: classical bottom-up relational carrier (conditional, non-canonical)

Status: `exists` — an authored proposal, not executed code. Layer 0 reuses one
already-executed comparison (cited below, itself capped at `passes local
rerun`); Layers 1 and 2 are `PROPOSED_NOT_YET_SIMULATED`. This document is
one candidate among rivals in `system_v8/candidates/`. It is not canon and
does not admit anything. `promotion_allowed: false`,
`formal_admission_allowed: false`.

## 0. Stance and role

This candidate is bottom-up and classical: a finite relation (equivalently a
finite automaton or evolving graph) carrying the whole structure, never a
density matrix or spinor. It is deliberately minimal — as few layers as this
document can defend, with every presumption named and every omission marked.

Its role is comparative, not assertive. It tests how much of the shared
frame (constraint on distinguishability, no assumed identity/time/space/
probability/object, MSS as weakest-persisting-evolving structure, mutual
nesting, finitude) a strictly relation-only carrier can satisfy before it
needs anything more. Spinor, density-matrix, or octonionic rivals are
expected to add structure this candidate omits; the open question for them
is whether that extra structure is admissible and needed, or merely
installed.

This puts the candidate in direct, acknowledged tension with `ROOT_CARD.md`
line 3 (owner verbatim): "everything has to run on density matrices if it is
the MSS." That line outranks this document. This candidate does not deny
it — it is the weaker rival ROOT_CARD's own framing calls for: "machine
formalizations are candidates measured against these words, never
replacements for them." Where this candidate stalls, that is evidence for
the density-matrix requirement, not against it. Where it does not stall, the
requirement has to say why the extra structure was still needed. Section 6
names exactly where that collision becomes checkable.

## 1. Ordered layer list

| Layer | Name | Maps to `system_v8/README.md` ladder | Carrier read |
|---|---|---|---|
| 0 | Probe-relative distinguishability relation | R0 (admissibility relation) | finite relation / probe-response incidence over a finite atom set |
| 1 | Ordered, branching relation-family under local admissible rewrite | R1 + R2 (nested compatibility, ordered relations) | a finite index set, one Layer-0 relation attached per index, a finite step relation between indices |
| 2 | Persistent-distinction closure | R3 (persistent distinctions) | the sub-relation of Layer-0 distinctions surviving every admissible Layer-1 path in the current finite index family |

The list stops at Layer 2. It does not propose a rung for entropy, geometry,
a drive/gradient, or any bridge claim (Axis 0). Section 6(e) names this as a
deliberate omission, not an oversight.

All three layers share one carrier type (a finite relation), reused at
increasing indexing depth rather than replaced. No layer introduces a new
ontological object — Layers 1 and 2 add finite operations (indexing,
closure) over the Layer-0 carrier, not a new kind of thing.

## 2. The carrier

One carrier throughout: a finite relation over a finite atom set, read
either as (a) an unrestricted set of admissible tuples, or (b) a
probe-context to response incidence map. Both readings are already the
surviving frontier of an executed comparison in this repo —
`system_v8/base_campaign/results/base_campaign_run_20260718/base_campaign_receipt.json`,
`base_frontier: ["b0_unrestricted_relation", "probe_response_incidence"]` —
and this candidate does not choose between them. Per the shared frame's "MSS
... never absolute, possibly plural," both stay live at Layer 0.

Explicitly rejected as the ground carrier, each with a specific executed
reason (detailed in §6a): a plain pairwise graph, a partition/equivalence-
class carrier, and a deterministic finite-automaton/transducer. All three
were candidates in the same executed comparison and all three lost. This
matters for the brief: the brief names "a finite relation or finite
automaton or evolving-graph carrier" as acceptable options for this stance,
and two of those three (automaton, plain graph) already have a recorded,
packet-relative negative against their static/flat form in this exact repo.
This candidate's Layer 1 is written as a specific, named response to those
two negatives (§4, §6b) — not a claim that the negatives don't
apply.

## 3. What each layer presumes

Layer 0 presumes: a finite set of atoms (finitude/countability, F01); a
finite set of admissible probe contexts; a response relation between them
that is not assumed reflexive, symmetric, transitive, or single-valued —
those are properties to test, never to assume. It does not presume:
identity, equality, equivalence-relation structure, probability, metric,
order, time, causality, algebraic composition, geometry, coordinates, or an
observer. This mirrors `constraint_core/CLAUDE.md`'s explicit primitive list
("distinctions derived from constraints... forbidden as primitives:
probability, metric, time, causality, coordinates, observer, linearity,
dynamics") and this repo's ladder naming R0 an "admissibility relation," not
an equivalence relation.

Layer 1 presumes, in addition: a finite index set with a finite step
relation between indices — not assumed to be a strict total order; whether
an order is forced, merely installed, or idle is itself a Layer-1 test (the
same installed-vs-forced-vs-idle discipline `manifold/DEEP_LAYER_BUILD_CARD.md`'s
`chirality_layer.py` already uses for orientation). It also presumes a
finite local rewrite relation between (index, Layer-0-state) pairs, and that
relation is allowed to be multi-valued. Nondeterminism is not smuggled in
for its own sake — it is a direct response to a named executed failure
(§6a): the one carrier in this repo that presumed a single-valued transition
function already lost.

Layer 2 presumes nothing beyond Layers 0 and 1. It is a finite closure —
an intersection of survivors over every admissible Layer-1 path — computable
because the index and path space are finite (F01 again, not a new
presumption).

## 4. Persistence and evolution

Persistence: a Layer-0 distinction (two atoms separated by some probe
context) counts as persistent exactly when it stays separated across every
admissible Layer-1 path reachable in the current finite index family. This
is the repo's own R3 phrasing — "surviving-distinction inventory per
candidate manifold" — read literally, not extended.

Evolution: a step from one index to another through the local rewrite
relation, which may be multi-valued. The result is a finite branching
structure (a DAG or tree of admissible relation-states) over the index set,
not one deterministic trajectory. Where the brief's "finite automaton"
option would read this as a single-valued transition function, this
candidate deliberately weakens that to a relation, because the
single-valued reading already has a recorded negative (§6a).

Nothing here carries a rate, a metric, or a continuous parameter. "How much"
or "how fast" a structure changes is out of scope by design — see the
omissions in §6(e). An "object," under this candidate, is nothing more than
a distinction that survives this closure: durable conditional survivor
structure and nothing else, per the shared frame's own definition. MSS
candidacy first has a referent at Layer 2, as a maximal set (possibly
several incomparable such sets — plural, not resolved by taste) of
distinctions stable under the Layer-1 branching relation.

## 5. Probe / distinguishability test per layer

Layer 0 probe — admissibility check: for every reference context, does the
candidate's admitted-outcome set equal the reference's observed-outcome
set, exactly, packet-relative? This is a direct reuse of
`base_ratchet_campaign.py`'s own `evaluate()` R1 test. Pass/fail is a set
equality per context, not a similarity score.

Layer 1 probes — two of them, both reused from the same executed script
rather than newly invented:
- relisting/order-reversal control (`RATCHET_SPEC.md` §8): permute or
  reverse the finite index-step sequence and recompute Layer 2. If the
  surviving-distinction set does not change, the ordering was not
  load-bearing for this carrier under these probes — an informative,
  clean negative, not a failure of the whole candidate.
- nesting-mutuality probe, reusing `base_ratchet_campaign.py`'s own
  `nesting_tests()` fields `restricting_outer_changes_inner` and
  `order_T2T1_equals_T1T2`, applied to the Layer-1 index family: does
  restricting a later index's admissible context change what an earlier
  index admits, and does composition order (outer-then-inner vs.
  inner-then-outer restriction) stay equal? A pass on mutual nesting needs
  at least one witnessed case where restricting the outer side changes the
  inner side. See §6d for why this is currently open, not just untested.

Layer 2 probe — adequacy and demand-erasure controls (`RATCHET_SPEC.md` §8):
every distinction claimed persistent must be checked against all admissible
Layer-1 paths, not a sample — exhaustive, not approximate, because the path
space is finite (F01). Demand erasure: remove one active demanded
distinction edge from the input packet and confirm the closure's read of
the other distinctions does not spuriously move.

## 6. Honest weaknesses, deliberate omissions, and order risk

(a) Named prior negatives against this exact carrier family, already
executed. All three come from
`system_v8/base_campaign/results/base_campaign_run_20260718/base_campaign_receipt.json`
and `base_ratchet_campaign.py`, status ceiling "packet-relative executable
base-structure comparison over two anonymous source packets; no scientific,
physical, or canonical claim" — cited at that ceiling, not higher:
  - Plain pairwise graph (`pairwise_graph`): edges are built from every
    2-subset of (coordinate, value) pairs that ever co-occur in any row; a
    context+outcome is admitted whenever every pairwise sub-combination was
    independently witnessed somewhere. That is a relaxation of the true
    4-ary joint relation to its 2-ary marginals, and it over-admits by
    exactly 8 outcome pairs on both tested packets
    (`ctx_overadmitted_outcome_pairs: 8`) — it lets through combinations the
    reference never produced.
  - Deterministic transducer (`deterministic_transducer`): its own code
    refuses any context where its fitted rows already show more than one
    outcome ("cannot represent: no deterministic value exists"). Witnessed
    failure: on the `ring` packet, context `[0,0,0]` genuinely carries both
    outcomes `{0,1}` in the reference, and the transducer can only
    return `null` there. It does not over-admit
    (`ctx_overadmitted_outcome_pairs: 0`) — it under-represents, and it is
    the only one of the nine tested base candidates whose derived
    distinctions fail to persist under the tested restriction path
    (`distinction_persists_under_restriction_path: false`).
  - Partition/equivalence-class carrier (`finite_partition`): its
    `admitted()` is context-independent by construction — it always returns
    `{0,1}`, discarding the probe context entirely. This is the sharpest
    warning for Layer 0: if `~` were read as a single global equivalence
    relation instead of a probe-context-relative relation, it collapses to
    this same failure. Layer 0 above is written to avoid exactly that
    reading.

  Layer 1's design choices — a relation rather than a function between
  steps, and a full joint rather than a pairwise-decomposed state — are
  direct, named responses to the transducer and graph failures above. That
  is a reason to expect Layer 1 to do better than the flat readings, not a
  demonstration that it does. It has not been executed.

(b) Layer 1 and Layer 2 are proposals, not results. Status
`PROPOSED_NOT_YET_SIMULATED`, this repo's own label for exactly this state.
Weakening the transducer's function to a relation could fail a different
way — for instance, if implemented as a graph of (index, state) pairs
rather than a genuine joint structure, it risks reintroducing the same
pairwise-marginal over-admission that already beat `pairwise_graph`. Nothing
in this document rules that out; it is a build-time risk for whoever
implements Layer 1.

(c) Possible order-smuggling inside Layer 1. The finite index set risks
carrying real ordering work without that ordering being independently
earned. The relisting control in §5 is the check, not a formality: if
reversing the index sequence leaves Layer 2 unchanged, the index was not
load-bearing, and this candidate is not yet at its own claimed minimum — a
direct tension with its own minimality pitch, not a hypothetical one.

(d) Nesting-mutuality is an open negative across every tested base
candidate, not a special weakness of this one. The one existing execution
of `nesting_tests()` found `restricting_outer_changes_inner: false` and
`order_T2T1_equals_T1T2: true` for all nine candidates it ran, including
both frontier members. Under the two packets tested so far, restricting an
outer relation never changed an inner one, and composition order never
mattered, for any classical base carrier tried. That sits in real tension
with the shared frame's "nesting is mutual... order or bracket can [admit
or exclude] a distinction." This document holds that tension rather than
resolving it: it may mean mutual nesting needs a richer carrier (evidence
for the rivals), or it may mean the two tested packets are too thin to
exercise it yet (evidence for more packets before ruling on carriers at
all). Both readings stay live.

(e) Deliberate omissions. Not layers of this candidate, named so a
rival's extra structure can be judged against a concrete list rather than a
vague "more than this": probability or measure; metric or geometric
distance; continuous time; algebraic composition beyond finite relation and
intersection operations (no group, ring, module); Hilbert space; density
matrices; spinors; Clifford structure; quantum superposition; any entropy
formula (Shannon, von Neumann, BKM, Fisher); the entropy-geometry coface of
`RATCHET_SPEC.md` §3; any drive, gradient, or Axis-0 claim; any coupling or
physical-bridge claim. Per `CLAUDE.md`'s Hard Stage Gate, this candidate
does not attempt couplings or bridge claims — it is written to stop at the
base/lego rung on purpose, not to run out of ideas there.

(f) Where this order might be wrong.
  - Static-then-dynamic (Layer 0 fixed, then Layer 1 indexed) may be an
    artifact of how this document is written rather than a forced order.
    The reference packets used to test Layer 0 were themselves built from
    repeated probing over the same atoms — a "prior to any process" static
    relation may not be separable from process at all, in which case Layers
    0 and 1 should be one layer, not two.
  - Deferring the nesting-mutuality probe to Layer 1 is a choice, not a
    necessity — `base_ratchet_campaign.py` already runs it on the static
    base candidates directly. The Layer 0/Layer 1 boundary drawn here for
    when nesting gets tested may not be forced either.
  - Two incomparable Layer-0 realizations (unrestricted relation vs.
    probe-response incidence) are both retained rather than chosen between.
    That follows the anti-collapse rule, but it also means a rival
    candidate that does force a choice at this rung — for a stated,
    checkable reason — would be doing strictly more work than this one.

What would flip this candidate: a witnessed case where restricting an
outer Layer-1 index changes an inner one (would upgrade §6d from open
tension to a real requirement this carrier has to meet); a relisting run
where reversing the index order changes Layer 2 (would justify keeping the
index as load-bearing rather than idle, closing §6c); or a fresh comparison
in which one of the six `PROPOSED_NOT_YET_SIMULATED` quantum-flavored
carriers (`rebit_carrier`, `complex_density_matrix`, `jordan_structure`,
`clifford_vector_spinor`, `quaternionic_carrier`,
`bracket_preserving_octonionic_carrier`) is finally executed against the
same packets and beats the Layer-0 frontier outright — that would be the
first checkable collision with `ROOT_CARD.md` line 3 named in §0.
