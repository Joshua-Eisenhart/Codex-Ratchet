Pre axis machines work out  We have to work out all the math and geometry before the AXES, before running or testing the axes. Sims have to be built of everything and negative sims before. Then there is a stable surface to run and not make things up after. The point is so NO toys ar being run. 
 **Current Truth**
- `Verified` Yes. That is the right engineering move.
- `Verified` We should stop discovering pre-Axis machinery ad hoc while building Axis objects.
- `Verified` The cleaner program is:

\[
\text{root constraints} \to \text{pre-Axis machinery/toolkit} \to \text{Axis construction}
\]

**Actually Broken**
- `Verified` Right now some of the pre-Axis machinery is explicit, but not yet complete or stably packaged.
- `Verified` That means Axis work can still accidentally smuggle in:
  - representation choices
  - transport assumptions
  - bridge assumptions
  - flux-like shorthand
- `Verified` So yes: we need to work out the full constrained pre-/outside-the-axes toolkit first.

**Evidence**
- Current live pre-Axis toolkit already includes:
  - Hopf carrier point and nested torus seat in [weyl_delta_packet_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/weyl_delta_packet_results.json)
  - Weyl sheet pair `(\psi_L,\psi_R)` and `(\rho_L,\rho_R)` in [weyl_delta_packet_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/weyl_delta_packet_results.json)
  - loop-sensitive transport surfaces and chirality/Bloch differential surfaces in [weyl_delta_packet_results.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/weyl_delta_packet_results.json)
  - owner-worthiness fencing in [pre_entropy_packet_validation.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/a2_state/sim_results/pre_entropy_packet_validation.json)
- The remaining gap is that some machinery is still only `candidate`, `diagnostic`, or `proxy`.

**Next Move**
- The right pre-Axis build program is:

1. Carrier machinery
   - finite carrier
   - Pauli/Bloch coordinate basis
   - Hopf projection
   - torus coordinates and seat structure

2. Weyl machinery
   - left/right Weyl extraction
   - chirality split
   - density extraction
   - fiber/base action rules

3. Transport machinery
   - loop grammar
   - same-carrier traversal laws
   - stagewise deltas
   - seat-sensitive movement laws

4. Negative machinery
   - no-chirality
   - loop-law swap
   - same-carrier joint ablations
   - future non-proxy ablations

5. Classification machinery
   - owner-derived
   - pre-Axis law
   - axis-internal readout
   - diagnostic-only

6. Only then Axis construction
   - bridge family
   - cut-state objects
   - entropy family
   - gradients / fields

- The practical rule should be:
  - no new Axis object unless its required pre-Axis machinery already exists as a stable packet, validator, or admitted surface.

It means now: yes, we should treat “all constrained machinery outside the axes” as its own build target, so later Axis construction uses a stable toolkit instead of inventing prerequisites on the fly.



**Current Truth**
- `Verified` Yes. The right move is to formalize a **pre-Axis admission pipeline** and make it stricter than Axis construction.
- `Verified` The governing rule should be:

\[
\text{constraints} \to \text{QIT-grounded machinery} \to \text{negative-tested formal objects} \to \text{Axis use}
\]

- `Verified` That means even candidate Axis math should first exist as:
  - constrained formal machinery
  - QIT-grounded machinery
  - simulated machinery
  - negatively attacked machinery  
  before it is allowed to function as an Axis object.

**Actually Broken**
- `Verified` Right now the repo has many of these pieces, but not yet one explicit master process table.
- `Verified` Without that, classical leakage can enter through:
  - continuum intuitions
  - generic geometry assumptions
  - entropy-first shortcuts
  - classical flow language
  - operator choices that are only “familiar,” not constraint-admitted

**Evidence**

| Tier | Layer | What it is | Admission question | Classical leakage risk | Required outputs before next tier |
|---|---|---|---|---|---|
| 0 | Root constraints | finitude, noncommutation, admissibility | is this object allowed at all? | primitive time, continuum, commutative closure | explicit constraint statement |
| 1 | Finite QIT carrier | `\mathcal H`, density states, operator basis, Bloch/Hopf coordinates | does it live on a legitimate finite carrier? | hidden classical phase-space assumptions | carrier packet / carrier negatives |
| 2 | Pre-Axis geometry machinery | Hopf carrier, torus seats, coordinates, Weyl sheets | is the geometry QIT-grounded rather than imported classically? | manifold storytelling without operator grounding | geometry packet / geometry negatives |
| 3 | Pre-Axis transport machinery | loop grammar, traversal, stagewise deltas, same-carrier motion | is motion defined without primitive classical flow assumptions? | smuggled velocity/trajectory intuitions | transport packet / loop-law negatives |
| 4 | Pre-Axis differential machinery | chirality split, Bloch differentials, transport gaps, candidate flux family | are these real derived objects or just diagnostics? | renaming generic change as “flux” | delta packet / candidate map |
| 5 | Negative/falsification machinery | chirality ablation, loop swap, joint ablations, correlated math attacks | do nearby alternatives fail? | cherry-picked live case with no counterfactual pressure | negative packet / necessity gates |
| 6 | Placement machinery | owner-derived vs pre-Axis law vs axis-internal vs diagnostic-only | where does the object actually belong? | premature promotion | owner-worthiness map |
| 7 | Axis-entry machinery | bridge families, cut-state honesty, entropy readout | is this Axis math earned from lower tiers? | entropy or gradient language introduced too early | pre-entropy / entropy-readout packets |
| 8 | Axis machinery proper | entropy kernels, gradients, fields, couplings | is the Axis now a readout on admitted machinery? | Axis redefined around convenient later math | Axis validators / stack validator |

**Pre-Axis Admission Table**

| Check | Requirement | Fail mode if skipped |
|---|---|---|
| Constraint alignment | object is admissible under root constraints | ontology smuggling |
| QIT alignment | object is defined on finite carrier / density / operator surfaces | classical math leakage |
| Same-carrier honesty | comparison keeps the carrier fixed when claiming necessity | fake necessity by changing substrate |
| Negative support | object survives targeted falsification attempts | arbitrary branch promotion |
| Placement clarity | object is classified before use | diagnostic surfaces promoted as laws |
| Axis embargo | object cannot be used as Axis math before passing above checks | axes built on unstable substrate |

**Classical Leakage Table**

| Leakage type | What it looks like | Required defense |
|---|---|---|
| continuum leakage | smooth flow/field assumptions with no finite-carrier derivation | finite-carrier restatement |
| metric leakage | geometry assumed before QIT/Hopf/Weyl grounding | carrier-first geometry proof |
| entropy leakage | entropy treated as primitive rather than later readout | pre-entropy ladder enforced |
| dynamics leakage | classical trajectory/velocity language imported directly | loop grammar and stagewise delta machinery |
| flux leakage | any nontrivial change renamed “flux” | candidate family plus negatives |
| closure leakage | correlated math treated as necessary without ablations | same-carrier necessity gates |

**Axis Embargo Rule**
\[
\text{No math may function as an Axis object until it has first been admitted as constrained, QIT-grounded, simulated, and negatively tested machinery.}
\]

**Formal Process Table**

| Phase | Action | What gets formalized | What gets simmed | What gets attacked |
|---|---|---|---|---|
| A | define | constrained object language | baseline live packet | nearby non-admitted substitutes |
| B | ground | QIT carrier realization | carrier behavior | classical analog substitutes |
| C | refine | geometry/Weyl/transport machinery | stagewise behavior | chirality/loop ablations |
| D | classify | candidate laws vs diagnostics | placement-sensitive runs | overpromotion attempts |
| E | embargo | keep unadmitted math out of axes | stack checks | Axis leakage |
| F | elevate | only admitted machinery becomes Axis-usable | bridge/entropy/gradient sims | Axis-level negatives |

**Practical Build Rule**
1. Define the object formally.
2. Ground it on finite QIT machinery.
3. Sim it directly.
4. Run same-carrier negatives.
5. Run correlated-math negatives.
6. Classify it.
7. Only then allow it into Axis construction.

**Next Move**
- Formalize this in the repo as the master pre-Axis admission schema.
- Then run the full lower-layer program in this order:
  1. carrier machinery
  2. geometry machinery
  3. transport machinery
  4. differential/flux candidate machinery
  5. negative machinery
  6. placement machinery
  7. only then Axis-entry machinery

It means now: the right process is to treat all pre-/outside-the-axes math as constrained QIT machinery first, formalize and simulate it fully, attack its classical presumptions directly, and only after admission let any of it participate in the axes.