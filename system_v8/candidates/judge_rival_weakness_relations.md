# Rival weakness relations for packet-relative MSS (conditional fuel)

**Status:** `exists` — an authored proposal. Conditional throughout. This document is fuel only. It does not install any weakness relation, does not rank any candidate as admitted, and does not claim that any preorder is superior to partition refinement or to any other. Every sentence is scoped to an "if this definition were used for this packet, then..."

The observation in `STRAWMAN_AUDIT.md` is taken as given: the four candidates rest their MSS verdicts on one weakness relation (partition refinement as stated in `system_v7/constraint_core/RATCHET_SPEC.md` §6), while that section explicitly flags rival categorical, computational/resource, predictive, and dynamical preorders as live digs. `ROOT/ROOT_CARD.md` and `RATCHET_SPEC.md` §6 are the reference points for the exercise. No other files are read or modified.

## Current single weakness relation (for contrast only)

For presentations π and ρ that both achieve L_D(π) = L_D(ρ) = 0 on a fixed finite demand set D,

```
π ≼_part ρ   iff   every block of ρ is contained in a block of π
                   (i.e., ρ refines π; π is coarser or equal).
```

M(D) is then the set of ≼_part-minimal survivors. The presumption ranking reported in `STRAWMAN_AUDIT.md` (classical-relational least presumptive, then spinor/QIT, then nonassociative, then top-down most presumptive) is itself computed under a structure-count proxy that aligns with this partition-refinement logic. Any rival that produces a different total or partial order on the same four carriers is therefore a reordering candidate.

The four carriers (read only from the files listed above):

- spinor/QIT: finite density + minimal-ideal Clifford/spinor presentation, cut-conditioned, negative conditional entropy as proposed gradient, 9 layers, geometry deliberately not installed.
- classical-relational: finite probe-response incidence / unrestricted relation carrier, 3 layers, deliberately minimal, re-uses executed base-campaign receipts at layer 0.
- nonassociative: octonion algebra with nonzero associator as load-bearing primary structure, 8 layers through density, Hopf, S²/S³, coface, basin.
- top-down: 12-to-0 schedule with multi-agent / differentiated-engine registry at the high end, imposing constraints downward; thinnest local carrier at each layer but highest entry presumption.

All statements below remain conditional on the finite presentations and behaviors described in those four documents, for finite D and M that those documents could in principle compile against.

## Rival 1 — Resource (description-length / table-size) preorder

**(a) Exact definition on finite presentations**

Let a finite presentation π for a packet (D, M) be a finite grammar G_π together with a compiler C_π that, on the observation surface X induced by applying the probe family M to the demanded edges D, produces a behaviour b_π such that L_D(b_π) = 0.

Let size(π, D, M) be the length (in tokens, bits, or explicit table entries, under a fixed encoding scheme chosen before the comparison) of the smallest finite description of (G_π, C_π) sufficient to reproduce b_π exactly on the tested surface.

Define the preorder:

```
π ≼_res ρ   iff   size(π, D, M) ≤ size(ρ, D, M)
```

Ties are allowed; the preorder is partial in practice because different carriers may have incommensurable minimal encodings until an explicit size measure is fixed for the packet.

**(b) Expected reordering relative to partition refinement**

If the four carriers compile to behaviours that match the descriptions in their files, a resource preorder would be expected to place the classical-relational carrier first (smallest explicit relation table over a small atom set plus probe contexts) and the spinor/QIT carrier second (finite matrix plus generator list plus cut; structured but still compact for small dimension). The top-down carrier would be expected to sit third (requires naming differentiated engine sheets, registry entries, and 12-layer distinctions even if each local table is thin). The nonassociative carrier would be expected to sit last (full octonion multiplication table or associator surface for every tested triple, plus octonion-valued density entries, plus the finite grammar needed to evaluate α(x,y,z) on demand triples).

Relative to the current partition-refinement / structure-count ranking (classical < spinor < nonassoc < top-down), this would reorder nonassociative and top-down: top-down would now appear weaker (smaller description) than nonassociative. If the spinor matrices turn out larger than the classical relation tables under the chosen encoding, the first two could also flip, but the nonassoc / top-down reversal is the more stable predicted difference.

**(c) What it presumes**

It presumes that a uniform, carrier-independent encoding cost can be defined and measured for the minimal compiler that realises the required L_D = 0 behaviour. It presumes that "smaller description" is a legitimate reading of "weaker" for MSS purposes. It does not presume that the smallest description is the physically correct one; it only supplies one rival total preorder on the presentations that already survive the demand.

## Rival 2 — Categorical (factorisation / universal-property) preorder

**(a) Exact definition on finite presentations**

Fix a category C_{D,M} whose objects are the finite presentations π that achieve L_D = 0 for the active demand set and probe family. A morphism f : π → ρ in C_{D,M} is a finite map on the underlying observation surface (or on the generated quotients) that commutes with the probe behaviours: applying the probes after f yields the same distinction outcomes as applying the probes inside π and then mapping.

Say π is initial in a full subcategory of survivors if, for every other survivor ρ, there exists exactly one morphism π → ρ (up to the equivalence of maps that induce the same behaviour on D). Say π is weakly initial if at least one such morphism exists for every ρ.

Define the preorder on survivors:

```
π ≼_cat ρ   iff   π is weakly initial in the subcategory and ρ is not
               or both are weakly initial and every morphism out of ρ factors through π
               or (tie case) neither is weakly initial and size of the automorphism group or endomorphism monoid of π is ≤ that of ρ.
```

The concrete choice of "weakly initial" versus "has the smallest endomorphism monoid" is a packet-level parameter; the definition is the existence of a factorisation or universal property rather than a numerical count.

**(b) Expected reordering relative to partition refinement**

If the classical-relational carrier really is the least-committed finite relation (only probe-context to response incidence, no further algebraic structure), it would be expected to be weakly initial: maps exist from its relation tuples into matrix entries, into octonion components, or into slots in an engine registry. The spinor/QIT carrier would be expected to sit next (Clifford ideals and minimal-left-ideal projections supply clean factorisation routes for sign/order distinctions, so many maps into and out of it exist once the cut is fixed). The top-down carrier would be expected to sit lower (its high-layer engine differentiations and shell constraints are rigid; fewer maps out to a pure bottom-up relation or to a pure associator surface). The nonassociative carrier would be expected to sit lowest or tied lowest (the octonion multiplication table and nonzero associator are highly rigid; the automorphism group of O is small (G2), and maps into an associative matrix carrier or a plain relation carrier are obstructed exactly where the associator is nonzero).

Relative to partition refinement, this would reorder spinor/QIT above or beside classical in some packets (because of its factorisation tools) and would place top-down clearly after both bottom-up carriers, with nonassociative last. The top-down / nonassociative reversal relative to the current ranking is again visible.

**(c) What it presumes**

It presumes that the category C_{D,M} can be defined with well-behaved morphisms (structure-preserving maps on the observation surface or quotients) and that "having a universal property" or "being the source of the most maps" is a coherent reading of weakness for MSS. It presumes finiteness of the relevant hom-sets so that initiality is checkable. It does not presume that the initial object is the only survivor worth keeping; antichains remain admissible.

## Rival 3 — Predictive (continuation-language reachability) preorder

**(a) Exact definition on finite presentations**

For a survivor π and a finite horizon h, let Λ_h(π, D, M) be the set of all finite continuation words of length ≤ h drawn from the admissible update / probe-extension alphabet of π, such that after the word is applied the evolved presentation still separates at least one previously unresolved or newly extended demand edge that was not required by the original D.

Define the predictive cost of π as the cardinality (or the maximum branching factor, under a fixed enumeration) of the smallest such language needed to keep L_D = 0 after all currently active demands are met:

```
pred(π, h) = |Λ_h(π, D, M)|
```

Then

```
π ≼_pred ρ   iff   pred(π, h) ≤ pred(ρ, h)
```

for the smallest h at which both presentations first achieve full coverage of D. Smaller predictive cost = weaker under this preorder.

**(b) Expected reordering relative to partition refinement**

If the top-down carrier really imposes high-layer constraints first, many future distinctions are already fixed or excluded by the engine-type and shell choices; its continuation language would be expected to be the smallest (high layers close off branches). The spinor/QIT carrier would be expected to sit next (the cut and signed readout constrain which updates remain relevant; negative conditional entropy regions are fragile and therefore low-branching once the cut is fixed). The classical-relational carrier would be expected to sit lower (its deliberately open Layer-1 branching relation and multi-valued rewrites keep more continuations live). The nonassociative carrier would be expected to sit last (every tested triple carries a nonzero associator possibility; each continuation word can branch on the value of α(x,y,z), producing a large reachable language of grouping distinctions).

Relative to the current ranking this would be a strong reordering: top-down would now appear weakest (least predictive commitment), followed by spinor/QIT, then classical-relational, with nonassociative strongest (highest reachability cost). The top-down carrier moves from last to first; the nonassociative carrier moves from third to last.

**(c) What it presumes**

It presumes that a well-defined finite alphabet of admissible updates and probe extensions exists for each carrier and that "number of future distinctions still separable" is a meaningful cost. It presumes that a presentation that already determines more of the future (smaller Λ_h) can count as "weaker" for MSS purposes inside the packet. It does not presume that low predictive power is always desirable outside the packet; it only supplies one rival preorder on the survivors for the current D.

## Rival 4 — Dynamical (basin size / persistence under perturbation) preorder

**(a) Exact definition on finite presentations**

Fix a finite perturbation budget k (number of elementary admissible changes: single table-entry flip, single generator addition/deletion, single probe-context coarsening, single cut move, etc.). For a survivor π let N_k(π, D, M) be the set of all presentations at distance ≤ k from π (under the chosen elementary moves) that still satisfy L_D = 0 on the original demand set (or on D plus a small fixed noise set declared with the packet).

Define

```
π ≼_dyn ρ   iff   |N_k(π, D, M)| ≥ |N_k(ρ, D, M)|
```

Larger basin = weaker (more stable minimal survivor) under this preorder. The preorder is packet-relative and k must be fixed before comparison.

**(b) Expected reordering relative to partition refinement**

If the classical-relational carrier really carries the fewest moving parts (plain relation table plus index-step relation), most small perturbations would still leave some variant that covers D; its basin would be expected to be the largest. The spinor/QIT carrier would be expected to sit next (many explicit controls are already named — cut erasure, product, gradient ablation — so the carrier is already hardened against some perturbations, yet the matrix and Clifford data still have more degrees of freedom than the bare relation). The top-down carrier would be expected to sit lower (high-layer presumptions — stable multi-agents, engine differentiation, shell radii — are easy to perturb; a small change in Layer 12 or 11 can make the downward constraints unsatisfiable, shrinking the basin). The nonassociative carrier would be expected to have the smallest basin (the associator surface is load-bearing at L1; flipping even a modest number of α values either collapses demanded distinctions or forces extra structure, so few k-step neighbours remain survivors).

Relative to partition refinement this would reorder top-down below spinor/QIT and would place nonassociative clearly last. Classical remains first, but the gap between spinor/QIT and top-down widens and the nonassociative carrier falls further than in the current ranking.

**(c) What it presumes**

It presumes that a finite, carrier-comparable notion of "elementary perturbation" can be declared and that counting the number of nearby survivors is a coherent proxy for stability. It presumes that a larger stability basin under small changes to the carrier or to D is a legitimate reading of "weaker" for MSS. It does not presume that the most stable basin is the physically preferred one; it only measures one dynamical dimension of minimality on the finite population.

## Summary of possible reorderings (conditional)

If any one of the four rival preorders above were substituted for partition refinement on a packet whose demands actually exercise the differences described in the four candidate files, the expected total or partial orders on the four carriers would differ from the current presumption-count / partition-refinement order in at least the following ways:

- Resource: nonassociative and top-down would swap or narrow their gap; nonassociative would look more expensive.
- Categorical: top-down would fall behind both bottom-up carriers; spinor/QIT might rise relative to classical because of factorisation tools.
- Predictive: top-down would move to the front (smallest continuation language); nonassociative would move to the back (largest branching language).
- Dynamical: top-down would fall behind spinor/QIT; nonassociative would be isolated at the bottom (smallest basin).

These reorderings are not predictions of execution outcomes. They are only the differences one would expect to see if the respective definition of ≼ were used to select M(D) from the same set of L_D = 0 survivors. Whether any of them would actually produce a different antichain, a different tooth, or a different DIG_CONTINUES outcome remains a question for finite execution under a concrete packet.

All four rivals remain live digs in the sense of RATCHET_SPEC.md §6. None is installed by this document.

**End of judge_rival_weakness_relations.md**