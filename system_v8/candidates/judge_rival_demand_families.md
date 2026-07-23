# Rival demand/probe families for the candidate judge

**Status:** FUEL only.  This is a proposal for rival finite judges `(D, M)`, not an
installation, packet, result, candidate edit, admission, or claim that any listed
distinction occurs in the world.  Each family is conditional on source-native rows
being supplied for its named probe transcripts.  A family that lacks such rows stays
`PROPOSED_NOT_YET_SIMULATED`.

## Why the base judge cannot decide this question

`base_campaign` used two anonymous packets and a nesting relation that joins them only
on a common outcome token.  Its two restrictions are independent filters (`ctx.h0=1`
and `ring.h1=0`).  Accordingly, its receipt reports both
`restricting_outer_changes_inner:false` and `order_T2T1_equals_T1T2:true` for all nine
tested carriers.  That is useful negative evidence about that judge, not evidence that
outer constraints can never alter inner admissibility.

The four families below change the *packet shape*.  Each includes an outer selector
whose alteration is required to change a named inner admissibility readout.  This is
the minimum counterfactual missing from the base run:

\[
  A_{u,i}(p) \ne A_{u',i}(p)
\]

for at least one declared inner context `i`, outer condition `u != u'`, and probe `p`.
Here `A` is a finite observed/admitted response set, not an assumed ontology.  A carrier
may represent this effect by relation, channel, bracketed product, or registry; the
judge must not put a carrier name, layer number, or expected winner into a feature key.

For every proposed family, `M` returns: (1) the exact response/admissibility table;
(2) the finite partition induced by the demanded edges; (3) the outer-to-inner change
witness; and (4) erasure, relabel, and matched-budget controls.  Its coface loss is
still `L_D(pi) = |{(x,y) in D : pi(x)=pi(y)}|`.  Thus these are rival *demand
families*, not a replacement for the v7 coface or for the packet-relative MSS rule.

`Separate` below means “would force different executable behavior, a different
primitive/update cost, or a stated insufficiency witness under the same finite budget.”
It never means that prose alone has eliminated a carrier.

## D1 — conditional continuation witness (thin-plus)

### Finite surface, demanded edges, and probe family

Let the finite transcript surface be

\[
X_1=\{T_{u,i,p}:u,i,p\in\{0,1\}\},
\]

where `u` is an outer continuation condition, `i` is an inner context, `p` is a
probe setting, and `T_{u,i,p}` is that cell's full finite observed response set.  The
supplied packet must contain the following named comparisons; it must not infer them
from a carrier.

\[
\begin{aligned}
D_1=\{& (T_{0,0,0},T_{1,0,0}),
         (T_{0,1,0},T_{1,1,0}),\\
       & (T_{0,0,1},T_{1,0,1}),
         (T_{0,1,1},T_{1,1,1}),\\
       & (T_{0,0,0},T_{0,1,0}),
         (T_{1,0,1},T_{1,1,1})\}.
\end{aligned}
\]

An edge is carried only when `M1` can read a difference between its two finite response
sets.  The first four are outer-to-inner edges; the final two prevent a judge from
satisfying them by deleting all inner structure.  `M1` is the eight-cell readout
`(u,i,p) -> A_{u,i}(p)`, plus the witness
`A_{0,i}(p) != A_{1,i}(p)` for at least one of the first four pairs.

The mandatory controls are: erase `u` while preserving `(i,p)`; permute the two outer
labels; and replace the supplied continuation constraint with a matched cardinality
outer condition.  The first control must erase the outer-to-inner edge, while the
second must merely rename it.

### Thickness and likely discrimination

This is thicker than the base demand because it does not merely filter one side of a
join: it demands a conditional response table in which an outer condition changes the
admissibility of an otherwise fixed inner probe.  It is deliberately the thinnest
rival: no probability, tensor factorization, associator, or future objective is
demanded.

- It would pressure the static reading of the **classical-relational** candidate: its
  Layer-0 unrestricted relation can tabulate the rows, but it does not by itself explain
  a constrained update.  An explicitly indexed evolving relation could survive, with
  its added index/update primitives counted.
- It would pressure **spinor/QIT** and **top-down** equally at first.  Either can survive
  only by compiling `u` into an actual channel/cut update or lower-registry restriction;
  a declared “mutual nesting” or “backward constraint” is not a pass.
- It normally still merges **spinor/QIT** with **nonassociative**: no grouping edge is
  live, so an associator is not yet required.  It can also merge any two carriers that
  compile the same table with the same measured budget.

**Cost:** eight possible transcript cells, six demanded comparisons, three controls, and
at least one held-out `(u,i,p)` cell.  Its low semantic cost is also its danger: a lookup
relation can pass it.  It is therefore a gate for genuine outer-to-inner coupling, not a
standalone carrier selector.

## D2 — cut-conditioned joint-versus-marginal witness (medium)

### Finite surface, demanded edges, and probe family

Let `c in {0,1}` name two operationally proposed cuts, `a,b in {0,1}` the two probe
positions, and `j in {0,1}` a joint response.  `mA` and `mB` are matched single-position
readouts.  The finite surface contains the eight joint transcript classes
`J_{c,a,b}` and the eight marginal classes `A_{c,a}`, `B_{c,b}`.

The packet proposes the following six demanded distinctions:

\[
\begin{aligned}
D_2=\{& (J_{0,0,0},J_{1,0,0}), (J_{0,0,1},J_{1,0,1}),\\
       & (J_{0,1,0},J_{1,1,0}), (J_{0,1,1},J_{1,1,1}),\\
       & (J_{0,0,0},A_{0,0}\times B_{0,0}),
         (J_{1,1,1},A_{1,1}\times B_{1,1})\}.
\end{aligned}
\]

The first four demand that changing the outer cut changes a joint inner
admissibility/readout.  The last two demand that, at two declared cells, the joint
response cannot be replaced by the product of its matched marginals.  `M2` reads the
four joint response sets, their eight marginals, and reports both (i) a cut-change
witness and (ii) a joint-minus-marginal witness.  A product or erased-cut control must
make the corresponding witness vanish.  The cut is an operational compiler choice;
the notation does not posit two pre-existing objects.

### Thickness and likely discrimination

This is thicker than `D1` because it requires two kinds of outer influence: cut choice
changes an inner joint readout, and the altered inner distinction cannot be reconstructed
from matched marginal readouts.  It is still finite and makes no entropy formula a
requirement.  If a later packet elects to record conditional entropy, that is an extra
probe readout, not an edge silently added here.

- It is designed to separate **spinor/QIT** from a flat **classical-relational** carrier
  on cost and predictive compression, if the former compiles the joint/cut witnesses and
  the latter needs an explicit table for every cut/joint cell.  The relation is not
  declared impossible; it remains a live, potentially more minimal rival.
- It can separate **spinor/QIT** from the current **nonassociative** proposal because
  associator load alone does not supply a joint-versus-marginal compiler.  A nonassociative
  carrier that does compile the same witnesses remains merged on adequacy and must be
  compared by the declared weakness/resource rule.
- The current **top-down** carrier can merge with spinor/QIT only if its registry makes
  the selected cut restrict an executable lower presentation.  If it merely names a
  higher selection without changing the response table, `M2` gives it an insufficiency
  witness.

**Cost:** 16 response classes, six demanded edges, product and erased-cut controls,
matched marginal acquisition, and enough held-out cells to distinguish compression from
memorization.  It risks smuggling a subsystem split; the cut-permutation/no-cut control
is therefore load-bearing.

## D3 — outer-regrouping / associator witness (thick algebraic)

### Finite surface, demanded edges, and probe family

Let `u in {0,1}` choose an outer boundary/continuation, let `a,b,c in {0,1}` be three
finite action labels, and retain both bracketings

\[
L_{uabc}=((a\circ b)\circ c)_u,\qquad
R_{uabc}=(a\circ(b\circ c))_u.
\]

For the two nontrivial declared triples `001` and `110`, demand the eight edges

\[
\begin{aligned}
D_3=\{& (L_{0,001},R_{0,001}), (L_{1,001},R_{1,001}),
         (L_{0,110},R_{0,110}), (L_{1,110},R_{1,110}),\\
       & (L_{0,001},L_{1,001}), (R_{0,001},R_{1,001}),
         (L_{0,110},L_{1,110}), (R_{0,110},R_{1,110})\}.
\end{aligned}
\]

The first four are grouping distinctions; the latter four say the same outer condition
must change the inner bracketed admissibility/readout.  `M3` evaluates both bracketings
at each named triple and outer condition, returning the finite associator difference
only as a response witness, not as a preinstalled algebraic axiom.  It must report both
a nonzero grouping witness at one named cell and an outer-change witness at one named
bracketing.

Controls: replace `circ` by a matched commuting/associative operation; erase the outer
condition while retaining the action words; reverse the serialized list of triples; and
hold the number of action-table entries fixed.  If the associative control retains every
edge, this family has not earned grouping pressure.

### Thickness and likely discrimination

This is thicker than `D2`: it asks not only for a conditional joint distinction but for
an outer-sensitive distinction between two finite composition histories.  It is exactly
the kind of packet under which the v7 association-unspecified floor permits
nonassociativity to become a candidate requirement; it does not install it before the
witness exists.

- It most directly separates the **nonassociative** carrier from the supplied
  **spinor/QIT** and **classical-relational** forms, whose ordinary product/composition
  presentations are associative.  They can remain live only by supplying an explicitly
  nonassociative compiler or by showing that the packet's grouping witness fails.
- It separates the current **top-down** candidate unless its claimed backward constraint
  compiles a bracket-sensitive lower action.  A registry with no action-side behavior is
  under-specified for this judge.
- It may merge a repaired nonassociative carrier with any rival that implements the same
  outer-sensitive bracketed table.  That is correct: `D3` should not award “octonion”
  merely for being named; resource and other rival weakness preorders remain live.

**Cost:** eight bracketed response classes for the two triples, eight demanded edges, four
controls, and a genuinely compositional source/runner.  This is the most expensive and
most falsifiable family: it can fail cleanly if no source-native grouping difference is
present, in which case it must not be used to select nonassociativity.

## D4 — future-viability backpressure witness (thick dynamical/order rival)

### Finite surface, demanded edges, and probe family

Let `f in {0,1}` be a finite outer future obligation, `i in {0,1}` an inner present
context, and `r in {0,1}` a proposed local rewrite.  A transcript records whether the
rewrite is admissible now and whether it admits a declared continuation to `f`:
`V_{f,i,r}=(now, continuation)`.  The demanded edge set is

\[
\begin{aligned}
D_4=\{& (V_{0,0,0},V_{1,0,0}), (V_{0,0,1},V_{1,0,1}),\\
       & (V_{0,1,0},V_{1,1,0}), (V_{0,1,1},V_{1,1,1}),\\
       & (V_{0,0,0},V_{0,0,1}), (V_{1,1,0},V_{1,1,1}),\\
       & (V_{0,0,0},V_{1,0,1}), (V_{0,1,1},V_{1,1,0})\}.
\end{aligned}
\]

The first four require a future obligation to change present inner rewrite
admissibility.  The next two prevent a carrier from satisfying the family by declaring
all rewrites equally viable.  The final two are crossed alternatives: a future-selected
rewrite must not collapse with the rejected local alternative.  `M4` runs a finite
forward continuation check from each `(i,r)` and a backwards viability check from each
`f`; it reports the exact cell(s) whose present admissibility changes when only `f`
changes.

Controls: erase the future obligation; replace it by a same-size random label; compare
forward-only and backward-viability schedules; and keep rewrite alphabet, horizon, and
row count fixed.  A top label that never changes a lower admissibility cell fails.

### Thickness and likely discrimination

This is thicker than the other families in temporal/order content while remaining a
finite reachability problem.  It directly tests the top-down candidate's stated claim
that higher layers constrain admissible lower realizations, rather than accepting that
claim as a narrative.

- It is tailored to separate the **top-down** carrier: it survives only if a concrete
  higher obligation performs the observed lower restriction.  If it passes, it can
  distinguish top-down scheduling from a bottom-up run that merely records a final
  state.
- **Classical-relational** can represent the finite viability relation, but a static
  relation will generally need an explicit future-indexed expansion; that cost and its
  update witness make the comparison meaningful rather than impossible by definition.
- **Spinor/QIT** can remain live if a finite channel/cut/update compiler realizes the
  same backward restriction.  It then merges with top-down on adequacy but can be
  separated by declared resource, predictive, or dynamical weakness evidence.
- **Nonassociative** is largely orthogonal: it remains merged unless the proposed local
  rewrites are also bracket-sensitive.  Combining `D3` and `D4` is the conditional test
  for an outer-selected associator, not an assumption that such a thing exists.

**Cost:** eight finite viability cells, eight demanded edges, a bounded continuation horizon,
four controls, and replayable forward/backward reachability checks.  Its principal risk is
leakage: `f` must be supplied through observable continuation requirements, never as a
hidden candidate feature or an answer-key scheduler label.

## What this ensemble can and cannot separate

| Pair of current candidate stances | First rival family that can make their difference executable | Conditional remaining merge |
|---|---|---|
| spinor/QIT vs classical-relational | `D2` | both remain if the relation carries all joint/cut rows at equal declared cost |
| spinor/QIT vs nonassociative | `D3` | both remain if a non-QIT bracket-sensitive joint compiler matches every row |
| spinor/QIT vs top-down | `D4` (with `D2` for a cut implementation) | both remain if a channel/cut compiler and a backward registry are behaviorally/resource equivalent |
| classical-relational vs nonassociative | `D3` | both remain only if the relation supplies the same non-associative action behavior |
| classical-relational vs top-down | `D4` | both remain if future-indexed relation and top-down registry are equivalent under the chosen weakness rule |
| nonassociative vs top-down | `D3` plus `D4` | both remain if one carrier compiles both outer-selected grouping and viability behavior |

No row is a promised kill.  The ensemble is intentionally plural: `D1` first tests the
missing outer-to-inner fact; `D2`, `D3`, and `D4` then make different candidate
commitments costly or behaviorally necessary.  A carrier that survives all four has only
survived these finite judges.  It is not an installed MSS, a canonical rung, or a
scientific/manifold result.

## Audit-before-install checklist

Before any family becomes an executable packet, an audit should require:

1. source-native provenance for every named transcript cell and a held-out subset;
2. exact `D` and `M` serialization, including which response-set difference carries each
   edge;
3. a demonstrated `A_{u,i}(p) != A_{u',i}(p)` witness, otherwise mark the family thin or
   failed rather than calling it nested;
4. demand erasure, outer-label permutation, and matched-budget controls; plus the
   family-specific product, associative, or future-label control above;
5. fused, split, and permuted demand-family schedules under the v7 contract; and
6. a result ceiling of packet-relative judge audit.  Neither a positive coface contrast
   nor a surviving carrier promotes a manifold, physics, or canonical claim.

Until those conditions are met, these are rival judges to be compared—not fuel that has
burned.
