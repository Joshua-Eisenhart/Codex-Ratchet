# Geometry Stack = Constraint Ratchet Doctrine

*Owner doctrine, 2026-04-14. Repo-tracked copy of memory entry `user_geometry_stack_ratchet_doctrine.md`.*

## Core Claim

Stacked geometries form a **real ratcheting constraint layer** IFF the stack is **non-commutative** (A∘B ≠ B∘A on some probe state). If you can freely swap order, it's not a ratchet — just independent filters.

## Why This Matters

The geometric constraint manifold is described as nested simultaneous shells where inner shells are MORE constrained than outer. For this nesting to be a ratchet (rather than a decorative hierarchy), the composition of shells must be order-sensitive. Non-commutativity IS the constraint ratchet.

## Tests / Markers

- Pairwise geometry couplings: A∘B on probe P vs B∘A on P → assert inequality
- BCH commutator: non-zero [A,B] = non-trivial stacking
- z3 UNSAT: probe admissible under A∘B → excluded under B∘A
- Triple/N-stack: of N! orderings, only a subset admits a witness
- Commuting pair controls: use as negative controls (not targets)

## Candidate Math

The **G-tower reduction chain** (GL→O→SO→U→SU→Sp) is the leading candidate for the ratchet carrier:
- Each reduction tightens structure group
- Chain order is rigid in 5/6 tested adjacent pairs (session 2026-04-14)
- z3 UNSAT proofs exist for invalid-order reductions (sim_gtower_order_z3_unsat_invalid_reduction_order, sim_gtower_order_full_chain_unique_path_admissibility)

## Tool Discipline

- clifford (Cl(3), Cl(6), Pin/Spin): natural carrier of non-commutative rotor composition
- sympy (Pauli algebra, BCH): closed-form commutators
- e3nn: equivariant irrep composition
- z3 / cvc5: UNSAT proof of excluded-reversed-order
- NO numpy for decisive non-commutativity computations — numpy matrix products lose the rotor/bivector structure

## Evidence from Session 2026-04-14

- **10/10 non-commutative pairs** confirmed A∘B ≠ B∘A (sim_geom_noncomm_*)
- **5 rigid G-tower adjacent reductions** (sim_gtower_order_*)
- **Commuting controls** (same-plane rotors, scalar irrep, same-axis rotation) correctly classified as non-ratcheting
- **Clifford rotor deep**: 8/8 PASS with non-commutative composition as the load-bearing claim

## Open Questions

- Full G-tower permutation enumeration: z3 lattice over all chain permutations
- 4-layer and 5-layer stack ordering (triple done; quad+ declined pending pairwise-matrix closure)
- Whether Spin/Pin distinction survives G-reduction as a separate ratchet
- Whether noncommutative Hopf tori (math ideas backlog #10) give a deeper carrier
- Khovanov / Heegaard Floer for shell-transition topological invariants (backlog #23)

## Cross-References

- Memory: `user_geometry_stack_ratchet_doctrine.md`
- Session: `docs/plans/session_2026_04_14_plan_and_findings.md`
- Backlog: `docs/plans/math_ideas_backlog_2026_04_14.md`
- Sims: `system_v4/probes/sim_geom_noncomm_*.py`, `sim_gtower_order_*.py`, `sim_cl3_deep_*.py`, `sim_gtower_deep_*.py`
