# Ratchet Process Specification v1

Status: owner-aligned executable process proposal, not Ratchet canon.

## 0. Authority Boundary

The wiki, source documents, specifications, messages, simulations, external
theories, model outputs, and bundles are a hypothesis-and-evidence basin. They
can establish provenance and supply candidates. They cannot admit themselves.

```text
Search wide. Gate hard. Admit narrowly.
Canonize scoped claims, never narratives.
Preserve every informative death.
```

The promotable unit is one claim with frozen scope, predecessor receipts,
candidate search, controls, independent recomputation, a fabrication audit,
demotion conditions, and an append-only decision receipt.

## 1. Root: Constrained Distinction Records

The root does not contain objects, states, probes, equality, a quotient,
geometry, entropy, probability, cells, or dynamics.

Let `A_t` be a finite sequence of syntactic presentation-mark occurrences,
`D_t` a finite sequence of attempted distinction tokens, `H_t` a finite
history prefix, and `C_t` the active finite constraint record. An occurrence is
addressed only by its finite presentation position. This uses syntactic token
identity so the record can execute; it does not install semantic equality or
object identity. The marks `a,b in A_t` are positions or occurrences, not
presumed individuals.

The root record is a partial, contextual map

```text
Delta_C(h, d; a, b) in {DISTINGUISHABLE, INDISTINGUISHABLE, UNRESOLVED}.
```

`Delta` need not initially be symmetric, reflexive, transitive, total,
context-independent, or history-independent. `UNRESOLVED` is not the same as
`INDISTINGUISHABLE`.

### F01: finite realization

At every realized run step, the marks, distinction attempts, active
constraints, history prefix, candidate family, and receipts are finite and
effectively inspectable. No completed infinity is root furniture. This is a
scope condition, not empirical disproof of continuum mathematics and not proof
of a globally smallest physical length.

### N01: typed order sensitivity

An admissible realization must preserve the possibility of a typed witness

```text
Delta_C(h . d1 . d2, r; a, b)
  !=
Delta_C(h . d2 . d1, r; a, b)
```

where `d1,d2,r in D_t`; `r` is a subsequent distinction-attempt token applied
after the reordered prefix. The anti-log condition is a continuation witness:
there must exist an otherwise identical finite continuation `k`, a later token
`d3 in D_t`, and addressed marks `a',b'` such that

```text
Delta_C(h . d1 . d2 . r . k, d3; a', b')
  !=
Delta_C(h . d2 . d1 . r . k, d3; a', b').
```

This difference changes a later constrained distinction rather than merely
reordering a receipt. Static predicates that reduce to set intersection are
the commuting control.

N01 does not derive an update family. Any update, clock, schedule, or memory
mechanism is supplied until a lower process independently forces it.

## 2. Earning Relations, Probes, Quotients, and Objects

Raw non-separation means only that no attempted distinction currently returns
`DISTINGUISHABLE`. It is not an equivalence relation.

A family `P` becomes an admitted probe family only after its members are typed,
replayable, finite, and outcome-stable in the declared scope. Its certified
domain contains only pairs on which every probe resolves; any pair with an
`UNRESOLVED` outcome remains outside that domain rather than being silently
merged. Certified
indistinguishability can then be proposed as

```text
a ~_P b  iff  every p in P resolves (a,b) as INDISTINGUISHABLE.
```

A quotient `A/~_P` is available only after reflexivity, symmetry, and
transitivity have been checked or explicitly completed and the completion has
survived a lower-structure control. Contextual or directional records may
instead require a graph, preorder, tolerance relation, hypergraph, sheaf, or
other weaker presentation.

An object is therefore provisional:

> an equivalence class or other functional compression of surviving
> constrained distinctions under a declared finite observation family.

New attempts may split it, merge it with another candidate, hold several
rivals live, or retract it. No quotient readout is the private carrier.

## 3. MSS: A Defeasible Meta-Gate

MSS is not a root axiom. It compares candidate presentations of the current
distinction obligations.

For a frozen obligation set `O`, structure family `K`, and supplied update
family variants `V`, the actual candidates are pairs `(S,U) in K x V`. This
prevents the update mechanism from shaping the frontier while remaining
outside MSS. Let `Surv(K x V; O,C)` be the pairs satisfying all active tests.
A campaign must declare a finite family of weakness-preorder variants
`W={<=_w1,...,<=_wm}`. One useful variant is:

```text
S <=_w T
```

when there is a structure-forgetting map `f:T->S` that preserves every frozen
observation, permitted update, and prediction target in `O`. All prediction
targets and their evaluation rule must be sealed by hash when the card is
frozen; their outcomes may remain hidden. Other preorder variants may compare
primitive signatures, automorphism freedom, data requirements, or predictive
compression. Each preorder and update-family variant is installed and must
face explicit variant controls.

The MSS frontier is the plural antichain

```text
MSS_w(K x V) = {(S,U) in Surv(K x V) :
                no (T,U') in Surv(K x V) satisfies (T,U') <_w (S,U)}.
```

Do not choose a unique winner when minima are incomparable. Compute one
frontier per preorder. Report their intersection as the preorder-robust core
and their union as the live sensitivity envelope; no variant is silently
selected as the correct one. An empty survivor set produces `NO_SURVIVOR` and
blocks admission. A plural frontier must fan out downstream evaluation over
every member unless a separate receipt removes one.

### Defeasibility law

No finite campaign proves that no weaker candidate exists. Every admitted rung
must record:

- the finite candidate-universe model, generator variants, coverage claim, and
  stopping rule;
- the weakness preorder and its version/hash;
- every preorder-specific plural MSS frontier, robust intersection, and
  sensitivity union;
- the frozen obligations it satisfies;
- the unsearched region;
- a demotion rule.

If a later candidate `S'` challenges `S`, both are rerun against the same
combined frozen obligation set. If only `S'` passes, the old claim is
falsified. `SUPERSEDED_BY_WEAKER` is used only when both pass and `S' <_w S`
under the declared comparison. The old receipt remains immutable. A
content-addressed current-status index points to the new hash-chained branch
receipt so consumers cannot mistake historical acceptance for current status.

## 4. Geometry and Entropy Are Co-Views of One Boundary

After a distinction structure `B_t` is admitted, two view constructors are
recomputed from that same boundary:

```text
G_t = GeometryView_tau_G(B_t) | UNLICENSED
E_t = EntropyView_tau_E(B_t) | UNLICENSED
```

`G_t` records relation shape: incidence, refinement, adjacency, reachability,
order, boundary, path, or later metric/connection structure. Its type is
licensed only when the corresponding relation, graph, topology, metric, or
connection prerequisites survive.

`E_t` records typed unresolved, hidden, erased, transferable, or distributed
distinguishability. Its type must be licensed. Examples include finite capacity
after individuation/counting, Shannon entropy after a measure, von Neumann
entropy after a positive density representation, and cut quantities after a
cut and tensor structure.

Neither view runs on the other. Both require explicit type licenses, both are
projections of `B_t`, and both are recomputed after every carve. This shared
source does not imply numerical
identity. Any relation such as

```text
Hessian D(rho || rho*) = g_BKM(rho*)
```

is a later, typed theorem under full-rank operator assumptions. It cannot be
carried down to the root or generalized to all geometry and entropy.

The dual-Ratchet square is

```text
           admitted update u
      B_t --------------------> B_{t+1}
       |                           |
   (G,E)_tau                   (G,E)_tau'
       |                           |
    (G_t,E_t) --------------> (G_{t+1},E_{t+1})
             recompute both
```

The lower arrow must be recomputed from the new boundary, never copied as a
label. Geometry can restrict which entropy types are licensed; unresolved
entropy/readout residuals can nominate new distinction attempts. Neither may
self-admit a lift. The constraints and MSS gate decide.

## 5. Branch-Local Ratchet Dynamics

Within one frozen card and branch, exclusion is monotone and receipts are
append-only. The card freezes the candidate-universe model, generator variants,
preorder variants, update-family variants, initial obligations, a deterministic
obligation-generation rule, the sealed target suite, and a maximum pass count.
Across new evidence or any change to those items, replay opens a new branch; it
does not rewrite the old one.

At tick `t`:

1. Freeze sources, claim, obligations, history, and predecessor receipts.
2. Enumerate a wide finite candidate family, including weaker and rival forms.
3. Run the Minimalist first: search for a lower structure that carries every
   obligation.
4. Apply typed constraints and every admitted supplied-update variant to the
   raw distinction record.
5. Preserve all surviving incomparable candidates.
6. Recompute the admitted relation boundary and both `(G,E)` views.
7. Project every stronger survivor through its forgetting map and measure the
   residual.
8. Run claim-specific controls and an anti-by-construction audit.
9. Independently recompute the load-bearing result.
10. Record `ACCEPT_PROVISIONAL`, `PARK`, `REJECT`, `GRAVEYARD_KEEP`, or
    `SUPERSEDED_BY_WEAKER` with hashes and blocked consumers.

A second tick is recursive only when a measured residual from tick `t` enters
the card-frozen obligation-generation rule and generates an obligation from its
sealed finite domain. Any rule change opens a new branch. The next boundary
must be recomputed from a content-addressed raw-record artifact; derived caches
are forbidden inputs and a stale-cache mutation must fail. Replaying an
installed label, terrain, channel, metric, or class does not count.

## 6. Generic Control Classes

Controls are selected per claim. There is no universal physics-specific fixed
roster. Every card must cover or explicitly mark inapplicable:

1. `lower_structure` - a weaker candidate does the same work and demotes the
   lift.
2. `representation` - harmless relabeling/encoding changes no invariant claim.
3. `order_erasure` - commuting or order-shuffled control kills an N01 claim.
4. `history_erasure` - amnesia kills a history-dependent claim.
5. `wrong_structure` - a rival or counterfeit carrier fails the target.
6. `anti_tautology` - the gate is not a restatement of the result.
7. `held_out` - the lift predicts/compresses an unobserved distinction.
8. `boundary` - empty, singleton, degenerate, scale, and domain edges.
9. `alternate_attempt_family` - conclusions are tested under another admitted
   distinction/probe family.
10. `integrity` - source, lineage, receipt, and result tampering is rejected.
11. `preorder_variant` - frontier dependence on weakness ordering is measured;
    robust and variant-sensitive survivors are separated.
12. `update_family_variant` - supplied dynamics are varied and their effect on
    the frontier is reported.
13. `generator_variant` - candidate coverage is repeated under rival finite
    generators and universe models.

A control must be mechanically coupled to the claim and must flip where its
design says it should. Solver agreement over hardcoded constants is not proof.

## 7. Finite Run-Surface and Cellular-Automaton Hypothesis

F01 licenses finite witnesses. It does not force cells, regular lattices,
synchronous time, locality, or a cellular automaton.

The CA/ring-checkerboard proposal enters as one candidate among weaker finite
transition systems, rewriting systems, event structures, graphs, hypergraphs,
asynchronous automata, block automata, and lookup models. A CA lift must earn:

- stable local units rather than presumed cells;
- a finite alphabet;
- an admitted neighborhood/locality relation;
- a supplied or derived update rule and schedule;
- representation-independent behavior under ring/board relabeling;
- held-out prediction or compression beyond a finite lookup table;
- failure of weaker non-cellular carriers;
- comparison against von Neumann CA and asynchronous/block alternatives.

Until those gates run, ring-checkerboard and CA are high-value candidate
run-surfaces, not admitted foundations. Finite resolution in a run also does
not establish a universal ontological atom or smallest number.

## 8. Status and Admission

Keep three axes separate:

```text
lifecycle_status:
  RAW_INTUITION | CANDIDATE | SCRATCH_DIAGNOSTIC | PASS_LOCAL |
  ACCEPT_PROVISIONAL | PARKED | REJECTED | GRAVEYARD_KEEP |
  SUPERSEDED_BY_WEAKER

evidence_grade:
  none | advisory | executable | independently_recomputed

claim_ceiling:
  hypothesis | scratch_diagnostic | pass_local | admitted_scoped_claim
```

`ACCEPT_PROVISIONAL` means canon-by-process only for the exact scoped claim and
current MSS frontier. It remains defeasible and promotes no downstream claim.
Acceptance also requires the claim to declare every later structure it uses.
Each declared dependency must be `EARNED` and point to a content-addressed
receipt. A card with no declared earned dependency cannot be accepted. Geometry
and entropy licenses, the independent-agreement record, the fresh fabrication
audit, the decision, its parent, and the current-status index must likewise
resolve through the card's receipt registry; a correctly shaped but unbound
hash is not evidence.

## 9. Required Ratchet Card

Before simulation or promotion, a closed Ratchet Card must name:

- source manifest, claim, and explicit earned-structure dependencies;
- root distinction record without primitive objects;
- F01/N01 scope and supplied structures;
- predecessor receipts and frozen obligations;
- finite universe model, generator variants, coverage claim, breadth, sealed
  target suite, and stop rule;
- preorder variants, update-family variants, plural frontiers, robust core,
  sensitivity envelope, and empty-frontier rule;
- relation/quotient earning gates;
- shared boundary for geometry and entropy co-views;
- projection maps and residuals;
- controls, independent recomputation, and fabrication audit;
- raw-record hash, frozen obligation-generation rule, path-bound hash-chained receipts,
  current-status index, decision, claim ceiling, blocked consumers, and
  demotion conditions.

If a required field is missing, allowed work is source extraction, conflict
mapping, candidate generation, or card repair. Simulation and admission are
blocked.

## 10. Present Scientific Ceiling

The live repo currently contains useful finite quotient, order-sensitivity,
carrier-comparison, and exact cross-runtime diagnostics. It does not yet
contain an admitted recursive core satisfying this specification.

In particular, these remain unearned:

- exactly four internal substages;
- sixteen distinct useful intelligences;
- complete Type-1/Type-2 mirrored engines;
- learned open-world perception or object creation;
- Axis0 entry/return alignment;
- CA or ring-checkerboard as the uniquely weakest run-surface;
- global identity of entropy and geometry.

The next executable target is a label-blind recursive foundations packet that
performs at least two raw-record recomputations and survives the generic control
classes above. Its first possible ceiling is only:

> A finite constrained-distinction process used a declared defeasible MSS
> preorder to select plural minimal survivors, recomputed geometry and a
> licensed entropy view from the same altered boundary, and returned a measured
> residual as a new root-level distinction obligation under destructive
> controls.
