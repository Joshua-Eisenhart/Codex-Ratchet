# A2 FUEL: BERRY PHASE + BIT ARCHITECTURE
**STATUS:** A2 HIGH-ENTROPY FUEL — SOURCE-BEARING EXTRACT

## Berry Phase in Density Matrices
- ρ = |Ψ⟩⟨Ψ| erases global phase → can't detect |Ψ⟩ → -|Ψ⟩ directly
- Track via "commutator residues around full cycle → loop signature"
- Holonomy proxy from sequence of non-commuting CPTP maps
- Captures topological "memory of the loop" from CHIRAL_FLUX orientation

## Non-Convergence at 720°
- Engine in open-system dissipative regime → limit cycle, not static point
- 0.085 cycle-to-cycle = engine settling into limit cycle
- 0.469 displacement at 720° = permanent Landauer cost from minor loop
- Phase twist is continuous deformation until closure forced by boundary constraints

## Chern Number = THE Proof
- Chern number: integration of Berry curvature over base manifold
- "∫_{S²} F = ±2π" → Chern +1 (LEFT_WEYL) vs Chern -1 (RIGHT_WEYL)
- Integer Chern parity from density matrix trajectories = strict proof of non-collapse

## 6-Bit Encoding
| Bit | Constraint | 0 | 1 |
|:---|:---|:---|:---|
| 1 | COUPLING_REGIME | Isothermal (bath-coupled, Se/Ni) | Adiabatic (insulated, Ne/Si) |
| 2 | FRAME_REPRESENTATION | Lagrangian/Checkerboard (discrete) | Eulerian/Ring (continuous) |
| 3 | CHIRAL_FLUX | LEFT_WEYL_CONVERGENT (inward) | RIGHT_WEYL_DIVERGENT (outward) |
| 4 | VARIANCE_DIRECTION | Deductive (constraint-first) | Inductive (release-first) |
| 5 | GENERATOR_ALGEBRA | Wave/Integration (FGA) | Line/Differentiation (FSA) |
| 6 | ACTION_PRECEDENCE | Topology-first (absorptive, -) | Operator-first (emissive, +) |

## 8-Stage Bit Patterns (Chiral=0, LEFT_WEYL)
### Major Loop (Bit 4 = 0, Deductive)
| Stage | Bits 1-6 |
|:---|:---|
| NeTi (+Ti) | 1,1,0,0,1,1 |
| FeSi (-Fe) | 1,0,0,0,0,0 |
| TiSe (-Ti) | 0,1,0,0,1,0 |
| NiFe (+Fe) | 0,0,0,0,0,1 |

### Minor Loop (Bit 4 = 1, Inductive)
| Stage | Bits 1-6 |
|:---|:---|
| FiNe (+Fi) | 1,1,0,1,0,1 |
| SiTe (-Te) | 1,0,0,1,1,0 |
| SeFi (-Fi) | 0,1,0,1,0,0 |
| TeNi (+Te) | 0,0,0,1,1,1 |

## NOT Gray Code
- Multiple bits flip per transition (e.g., FeSi→TiSe flips Bits 1,2,5)
- "The 8×8 grid is a lookup table of possibilities, not an engine schedule"
- Engine alternates discrete thermo strokes + swaps orthogonal operator classes

## 16/32/64 Stage Resolution
- 16: 8 LEFT_WEYL stages + 8 RIGHT_WEYL stages
- 32: 8 stages × 4 operator sub-applications per stage per engine
- 64: 32 × 2 engine types = full phase space lookup table
