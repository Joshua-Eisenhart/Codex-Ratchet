# Tier B — G-Tower / G-Stack Shell-Local Coverage (B1)

Status: 25 probes (↑4 added 2026-04-17)

## E-Class Shell-Local Additions (2026-04-17)

Four new E-class (E6/E7/E8) probes added for Tier D boundary evidence:

1. **sim_gtower_e6_root_weight_structure_shell_local** — E6 root system and weight lattice shell-local admissibility
   - Verifies 72-root system closure, weight lattice non-degeneracy, simply-laced property
   - Tools: z3 (kernel triviality), sympy (Cartan eigensystem), xgi (root hypergraph)
   - Classification: canonical

2. **sim_gtower_e7_weight_chamber_shell_local** — E7 dominant weight chamber closure and adjacency
   - Verifies 7-dimensional polytope structure, chamber cone property, facet boundaries
   - Tools: z3 (chamber closure), sympy (Cartan inversion), xgi (polytope hypergraph)
   - Classification: canonical

3. **sim_gtower_e8_root_system_dynamics_shell_local** — E8 root/coroot duality and multiplicity
   - Verifies 240-root system balance, coroot duality via Cartan matrix, Dynkin rigidity
   - Tools: z3 (multiplicity enforcement), sympy (Cartan spectrum), xgi (240-node root diagram)
   - Classification: canonical

4. **sim_gtower_e_class_cartan_admissibility_shell_local** — E6/E7/E8 determinant ordering and admissibility
   - Verifies det(E6)=3, det(E7)=2, det(E8)=1; strictly ordered; conjugacy-invariant
   - Tools: z3 (determinant uniqueness), sympy (exact determinant computation), xgi (E-class membership encoding)
   - Classification: canonical

## Coverage Summary

| Probe Type | Count | Examples |
|---|---|---|
| Classical groups | 6 | GL(3), O(3), SO(3), U(3), SU(3), Sp(6) |
| Exceptional groups | 4 | E6 (2), E7 (1), E8 (1) |
| G-Stack structures | 4 | Oper, Parabolic Bundle, Local System, Derived Stack |
| Total B1 shell-local | 25 | — |

## Tier D Readiness

E-class evidence now complete for pairwise/coupling boundary work:
- E6 root-weight structure: positive/negative/boundary closure rules
- E7 chamber adjacency: weight polytope facet constraints
- E8 multiplicity dynamics: root/coroot duality requirements
- E-class Cartan admissibility: determinant-based E-class classification

Next: E-class pairwise coupling (E6↔E7, E7↔E8) deferred to Tier D bridge programs.
