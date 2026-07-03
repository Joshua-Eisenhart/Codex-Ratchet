---
title: Constraint On Distinguishability Full Math
created: 2026-04-07
updated: 2026-04-08
type: summary
tags: [reference, research, formal, mathematics]
sources:
  - raw/articles/new-docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md
framing: source_bundle_math_reference
---

# Constraint On Distinguishability: Full Mathematical Treatment

## Overview
Comprehensive source-bundle math reference for the constraint on distinguishability. Individual component claims have bounded supporting sims, but this integrated chain is not a current repo-wide verified or admitted proof. Use live repo receipts and spec mirrors for current status.

## The Primitive
Finite set S of states, finite set M of measurements. Equivalence relation: s1 ~_M s2 iff for all m in M: m(s1) = m(s2). Quotient Q = S/~_M is the ontology at resolution M. F01: |S| finite, |M| finite, dim(H) finite. N01: composition order matters -- A composed with B != B composed with A.

## Carrier and State Space
H = C^2. States: density matrices rho = 1/2(I + r_x sigma_x + r_y sigma_y + r_z sigma_z). Bloch vector |r| <= 1. Pure at |r|=1, mixed at |r|<1, maximally mixed at |r|=0. Trace distance T = 1/2|r1 - r2|. Helstrom bound p_guess = 1/2(1+T).

## Hopf Structure
Pure states live on S^3. Hopf map pi: S^3 -> S^2 with fiber S^1 (global phase). Torus foliation parameterized by eta in [0, pi/2]. Clifford torus at eta = pi/4: minimal, flat. Fiber loops are density-stationary (constant pullback). Base loops are density-traversing (varying Bloch trajectory).

## Connection and Loop Geometry
Hopf connection A = dphi + cos(2eta)dchi. Berry phase gamma_Berry = -1/2 Omega(C). Sim: Berry phase varies from +/-0.92 (inner/outer) to +/-pi (Clifford). This is why pure-state CP^1/Hopf-type structure keeps appearing in the [[cross-domain-equivalence-map|cross-domain map]].

## Weyl Chirality
Two copies with opposite Hamiltonians: H_L = +H_0 (left Weyl), H_R = -H_0 (right Weyl). Joint state rho_AB in D(C^2 tensor C^2). Chirality is the pseudoscalar e_123 in Cl(3,0).

## Four Perceiving Topologies
Se (expansion, sigma+ Lindblad) -- drives state more distinguishable, open boundary. Ne (circulation, Hamiltonian) -- tangential, unitary, closed boundary. Ni (contraction, sigma- Lindblad) -- drives toward maximally mixed, open boundary. Si (stratified, commuting Hamiltonian) -- rotation within invariant subspaces, closed. Forced by su(2) on D(C^2): 2 channel types x 2 families = 4.

## Four Operators
Ti (Z-dephasing): Kraus operators K0=√(1-q)I, K1=√q|0><0|, K2=√q|1><1|. Kills off-diagonal (r_x, r_y → 0), preserves r_z. Entanglement destroyer (ΔC = -0.011). Te (X-dephasing): kills X-basis coherence, populations change. Strongest entanglement destroyer (ΔC = -0.018). Fi (X-rotation, unitary): rotates Bloch around x-axis, preserves purity. Only entanglement builder. Fe (Z-rotation, unitary): rotates Bloch around z-axis, slight destroyer. F-kernel = {Fe,Fi}: purity-preserving. T-kernel = {Ti,Te}: entropy-increasing. Both needed for the [[constraint-surface-and-process|ratchet]]. (from CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md)

## Operator Algebra
Generators sigma_x, sigma_z produce full Pauli algebra. Lie algebra su(2), dimension 3. Chiral split adds U(1). Combined: su(2) x u(1) -- electroweak subalgebra of Standard Model. su(3) (color) requires dim(H) >= 3.

## Composition Grammar
Eight terrains = 4 topologies x 2 loops. Type 1 outer (base, deductive): Se->Ne->Ni->Si. Type 1 inner (fiber, inductive): Se->Si->Ni->Ne. Type 2 = complete inversion. Sim: destroying composition order destroys quantum correlations (normal C=0.059, random C=0.013). Goldilocks zone at p=0.825 (Type1 optimum C=0.162).

## Entropy and Entanglement
Clifford torus = maximum entropy AND maximum entanglement. Entanglement concentration: 5-85x stronger at Clifford than inner/outer. Type 1 accumulates inter-subsystem distinguishability (C grows). Type 2 dissipates it (C decays). Ratchet = their interaction.

## Derivation Chain
a=a iff a~b -> S/~_M -> H=C^2 -> Hopf S^3->S^2 -> torus foliation -> connection -> two loop families -> Weyl chirality -> 4 CPTP semigroups -> 4 operators -> su(2)xu(1) -> loop grammar -> entropy peak -> Type1 accumulates / Type2 dissipates -> ratchet.

## Related pages
- [[cross-domain-equivalence-map]]
- [[berry-phase-and-holonomy]]
- [[hopf-fibration-mathematics]]
- [[clifford-algebra-qit]]
- [[constraint-on-distinguishability-formal-reference]]
