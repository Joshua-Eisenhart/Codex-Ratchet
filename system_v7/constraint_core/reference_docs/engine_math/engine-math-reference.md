---
title: Engine Math Reference
created: 2026-04-07
updated: 2026-04-13
type: summary
tags: [reference, research, mathematics, system]
sources:
  - raw/articles/new-docs/ENGINE_MATH_REFERENCE.md
framing: current
---

# Engine Math Reference

## Overview
Extracted from v5 docs (operator math explicit.md, terrain math.md). Math is verbatim from source. Covers the four base operators, loop vector fields, and density visibility proofs.

## Four Base Operators
Only 4 intrinsic operator families exist. UP/DOWN is NOT additional operator math -- it only appears after a terrain map is chosen. UP and DOWN are composition orders, not new operators.

### State Matrix Parameters
rho = (a, d, u, v) where a,d,u,v in R, a >= 0, d >= 0, a+d = 1, u^2+v^2 <= ad

### Ti (sigma_z dissipation)
Kraus operators: K0 = sqrt(1-q1) I, K1 = sqrt(q1) |0><0|, K2 = sqrt(q1) |1><1|. Lindbladian: L1(rho) = (kappa1/2)(sigma_z rho sigma_z - rho). Effect: destroys off-diagonal coherence in Z basis. Leaves populations unchanged.

### Te (sigma_x dissipation)
Kraus operators: K0 = sqrt(1-q2) I, K1 = sqrt(q2) . `(1/2)([1,1],[1,1])`, K2 = sqrt(q2) . `(1/2)([1,-1],[-1,1])`. Lindbladian: L2(rho) = (kappa2/2)(sigma_x rho sigma_x - rho). Effect: destroys coherence in X basis. Changes populations.

### Fi (sigma_x rotation -- unitary)
Unitary: U_x(theta) = exp(-i*theta*sigma_x/2). Effect: rotates Bloch vector around x-axis. Preserves purity.

### Fe (sigma_z rotation -- unitary)
Unitary: U_z(phi) = exp(-i*phi*sigma_z/2). Effect: rotates Bloch vector around z-axis. Preserves purity.

### Operator Classification
| Operator | Type | Generator | Axis 5 family |
|---|---|---|---|
| Ti | Dissipative (CPTP) | sigma_z dephasing | T-kernel |
| Te | Dissipative (CPTP) | sigma_x dephasing | T-kernel |
| Fi | Unitary | sigma_x rotation | F-kernel |
| Fe | Unitary | sigma_z rotation | F-kernel |

## Loop Vector Fields

### Inner Field (fiber loop -- density-stationary)
Y_in = d_phi -- the phi coordinate varies but does not affect density matrix.

### Outer Field (base loop -- density-traversing)
Y_out = -cos(2eta) d_phi + d_chi -- the chi coordinate rotates, creating new distinguishability in the off-diagonal phase.

### Density Visibility Proof
Inner density path: rho_in(u) = rho(phi0+u, chi0; eta0) = rho(phi0, chi0; eta0) -- INDEPENDENT of inner loop parameter. Outer density path: rho_out(u) varies with u -- the off-diagonal phase rotates with u.

## 16 Placements
Each placement is a paired (spinor law, density law): Terrain families {Se, Ne, Ni, Si} x chirality {L,R} x loop {in,out} = 16 placements. Terrain = the generator X_{tau,s}. Loop = the spinor path field Y_in or Y_out. Placement = the pair (X_{tau,s}, Y_l). Type 1 (Left Weyl): Se/Funnel, Ne/Vortex, Ni/Pit, Si/Hill. Type 2 (Right Weyl): Se/Cannon, Ne/Spiral, Ni/Source, Si/Citadel. Each placement specifies exact spinor and density evolution laws. (from ENGINE_MATH_REFERENCE.md)

## Related pages
- [[constraint-on-distinguishability-full-math]]
- [[current-architecture-core]]
- [[berry-phase-and-holonomy]]
