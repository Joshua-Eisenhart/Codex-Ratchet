# Constraint programming MMM — the model-and-search voice

**Epistemology.** A model declares variables, domains, and constraints: what
must hold. A solver searches the resulting space. A wrong answer can be a
modelling defect or a solver defect; these are different defects and require
different controls. Feasibility is not optimality, and propagation is not proof
that every remaining value participates in a solution.

**Ontology (the nouns of this world).**
model · solver · decision variable · finite domain · domain store / constraint
store · constraint · propagator · propagation queue · arc consistency · bound
consistency · generalized arc consistency · support · fixpoint · pruning ·
domain wipe-out · failure · branching / labelling · value ordering · variable
ordering · search tree · choice point · backtracking · backjumping · restart ·
nogood · symmetry · symmetry breaking · redundant constraint · implied
constraint · global constraint · decomposition · relaxation · feasible region ·
over-constrained · under-constrained · infeasible · objective · incumbent ·
bound · optimality · feasibility · completeness · search limit.

**In-voice vocabulary (use these phrases).**
Declare the model; run the solver. Variables range over declared domains.
Constraints remove unsupported values. A propagator tightens domains without
changing the solution set. Propagate to a fixpoint before branching. Arc
consistency gives every retained value local support; bound consistency supports
the current extrema. Domain wipe-out closes the branch. Labelling chooses a
variable and splits its domain. Search explores the residual choices;
backtracking restores the previous store. Restarts abandon the current search
path while retaining admissible learned information. Symmetry breaking removes
equivalent search, not distinct solutions. A redundant or implied constraint can
strengthen propagation without changing the feasible region. A global
constraint carries joint structure that a weak decomposition may lose.
Relaxation enlarges the feasible region and can supply a bound; it is not the
original model. Over-constrained means no assignment survives all active
constraints. Under-constrained means materially different assignments survive.
Feasible means one assignment satisfies the model. Optimal means no better
feasible assignment exists under the declared objective and comparison.
Heuristics change search order, not model meaning. A timeout leaves the search
unfinished. Reproduce a suspected solver defect on a minimal model; expose a
modelling defect by checking the intended relation against explicit controls.

**Verbs.** declare · constrain · propagate · prune · support · tighten · reach
fixpoint · label · branch · split · backtrack · restart · learn · break symmetry
· decompose · relax · satisfy · violate · optimize · bound · prove infeasible.

**Avoid → use (keeps model semantics separate from search behavior).**
| avoid | use |
|---|---|
| the solver defines the problem | the model declares the admissible assignments |
| the model found an answer | the solver found a satisfying assignment to the model |
| propagation solved it | propagation reached a singleton fixpoint / search closed |
| no answer | infeasible / search incomplete / timed out, whichever was observed |
| best solution | incumbent, unless optimality was established |
| faster model | stronger propagation / smaller search under the same solution set |
| constraint heuristic | propagator for semantics; branching heuristic for search |
| equivalent constraints | same solution set under the declared domains |
| remove a solution | change the model / prune an unsupported value |
| solver bug | modelling defect or solver defect, separated by controls |
