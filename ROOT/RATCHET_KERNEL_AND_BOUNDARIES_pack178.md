# Ratchet Kernel and Boundaries

This file isolates the Ratchet from the owner hypotheses it is allowed to explore.

## Minimal operational kernel

At a declared finite context \(r\), let:

- \(\mathcal G_r\): candidate grammar;
- \(\mathcal K_r\): generated finite candidates;
- \(\mathcal C_r\): executable constraints and controls;
- \(\Pi_r\): admitted probes/readouts;
- \(\preceq_r\): exposed presumption comparisons;
- \(V_r\): exposed persistence/evolvability/work tests;
- \(\mathcal P_r\): Purgatory records with immutable context fingerprints;
- \(H_r\): retained execution history and provenance.

The survivor population is not one predetermined object:

\[
S_r=\{x\in\mathcal K_r:\mathcal C_r(x)=1\}.
\]

The packet-relative MSS frontier is an antichain:

\[
F_r=\operatorname{Min}_{\preceq_r}\{x\in S_r:V_r(x)=1\}.
\]

No scalar score may silently eliminate incomparable minima. Every logical admission requires a satisfiable base and an absent bounded countermodel:

\[
\operatorname{SAT}_B(C)
\land
\operatorname{UNSAT}_B(C\land\neg\phi).
\]

Every solver model must be replayed in the executable semantics.

## Recursive motion

The Ratchet becomes recursive only when results modify the next context without installing the desired endpoint:

\[
(\mathcal G_r,\mathcal C_r,\Pi_r,H_r)
\mapsto
(\mathcal G_{r+1},\mathcal C_{r+1},\Pi_{r+1},H_{r+1}).
\]

A context change makes every Purgatory item eligible for reconsideration. Fair scheduling may select which items actually rerun. Failure at \(r\) is not permanent rejection.

The next context may admit a newly recurring relation or constraint only when it survives:

- independent proposal lineages;
- provenance hiding during scoring;
- controls and ablations;
- held-out configurations;
- alternate finite representations or runtimes;
- deletion tests showing load-bearing contribution;
- a presumption audit.

If no invariant survives, the Ratchet returns `HOLD`. Termination of enumeration is not discovery.

## Nested completion candidate

The owner claims a deeper nested constraint process. A useful candidate formalization is the complete compatible nest:

\[
\mathcal T_r=
\left\{
(x_0,\ldots,x_L):
\bigwedge_i C_i(x_i)
\land
\bigwedge_i R_i(x_i,x_{i+1})
\land H_r(x_0,\ldots,x_L)
\right\}.
\]

The state visible at layer \(i\) is the projection

\[
X_{i,r}^{\star}=\pi_i(\mathcal T_r),
\]

not a locally computed object independent of the rest. This captures the proposed principle that outer constraints change inner admissibility and inner extendability changes which outer structures survive.

This equation is a candidate implementation of the owner idea, not a new root axiom. The Ratchet must compete it against sheaf/gluing systems, constraint hypergraphs, finite history codes, factor graphs, spinor complexes, nondeterministic automata, and other finite local-to-global constructions.

## Escape/completion candidate

For a finite horizon \(h\), let \(\Lambda_{r,h}(x)\) be the finite language of probe signatures reachable from \(x\). An unresolved operational degree exists when

\[
x\sim_r y
\quad\text{but}\quad
\Lambda_{r,h}(x)\ne\Lambda_{r,h}(y).
\]

The present quotient has identified states whose admissible continuations remain distinguishable. A minimal successful refinement adds a coordinate, relation, operation, history bit, or larger recurrent complex that closes the counterexample. “Closure” may forbid an exit or convert a former boundary exit into an internal viable transition.

This is one exact way to interpret “entropy finds an escape and the manifold ratchets to contain it,” without pretending the word entropy is already defined.

## What the Ratchet cannot know in advance

It cannot install:

- spinors, qubits, tensors, octonions, or a continuum carrier;
- 2 engines, 2 loops, 4 terrains, 16 placements, 64 addresses, or 13 axes;
- a particular shell dimension or Hopf fibration;
- FEP, JEPA, IGT, Jungian labels, I Ching lines, gravity, or the Standard Model;
- a specific entropy functional;
- causal or noncausal ontology as an evaluation shortcut.

It may receive every one of these as provenance-tagged proposal families. After generation, anonymous execution and controls decide what survives.

## Executable inheritance

The compact execution bridge preserves the governing v2 surfaces under `90_EXECUTION_BRIDGE/`:

- `ROOT_RATCHET_KERNEL.md`
- `FUEL_MECHANISM.md`
- `FUEL_REGISTRY.json`
- `desktop/`
- `lev-plugin/`
- `tri-engine/`

Selected inherited receipts are under `receipts/`. The complete executable tree and source inputs remain in Pack 177 v2, identified by exact hash in `DONOR_AND_LINEAGE_INDEX.md`.

Those components are implementation scaffolding. Their current outputs do not establish the nested manifold, Axis 0, the engines, or the physics.
