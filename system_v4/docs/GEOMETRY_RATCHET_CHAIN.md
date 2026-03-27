# Geometry Ratcheting: The Yin-Yang Constraint Chain

**Status**: Active investigation, not locked canon.  
**Session**: 2026-03-27, 23 commits, 15 sims.

---

## The Ratchet Chain (Current Best Read)

The engine's geometry is not one layer — it's a **stack of representations and constraints**, where each level preserves some structure and loses some. The ordering is not simple causation ("A leads to B") but **admissibility / carrier / projection / loss**.

```
Level 0:  Root constraints (F01_FINITUDE, N01_NONCOMMUTATION)
Level 1:  Admissible complex state carrier
Level 2:  Spinor representation
Level 3:  S³ / SU(2) carrier
Level 4:  Hopf map π: S³ → S²
Level 5:  S² / Bloch sphere (pure-state image)
Level 6:  Density-matrix representation
Level 7:  Torus foliation / nested Hopf-tori organization
Level 8:  Chirality / Weyl distinctions
Level 9:  Surviving observable DOFs
Level 10: Engine / action / operator structures
```

> [!IMPORTANT]
> Weyl spinors look closer to the **engine's actual geometric constraint manifold** than tori or density matrices. The other structures are carrers, projections, observable representations, or derived geometric organizations.

---

## Information Loss at Each Projection

From `sim_geometry_ratchet_chain.py` (has known bugs — see below):

| DOF | Dirac 4×4 | ρ_L 2×2 | Bloch S² | Where it's lost |
|---|---|---|---|---|
| **U(1) phase** | 2.03 | **0.00** | 0.00 | **Destroyed** at Dirac → ρ_L/ρ_R |
| SU(2)_L rotations | 0.89 | 0.53 | 0.007 | Survives (attenuated) |
| SU(2)_R rotations | 0.89 | 0.00 | — | Invisible in ρ_L block |
| **Parity** | 2.40 | 0.93 | 0.008 | Survives |

---

## Yin-Yang ↔ Axis Mapping

The taijitu IS a stereographic projection of the Clifford torus on S³.

| Yin-Yang Feature | Axis | Corrected Math | Weyl DOF |
|---|---|---|---|
| **Black vs white** | Ax0 | Binary partition | parity (block-diagonal) |
| **Seeds of the other** | Ax1 | CPTP vs Unitary | parity + L_z |
| **Dots vs teardrops** | Ax2 | Concentrated vs spread | L_x |
| **Flip + invert** (inverted mirror) | Ax3 | **CP: ψ_L ↔ ψ_R*** | parity + rotations |
| **Spin direction** (CW/CCW) | Ax4 | **Process path integral** | ≈ Ax6 (overlap 0.97) |
| **S-curve curvature** | Ax5 | **Geodesic curvature** | Ax0 cluster (overlap 0.66) |
| **Which fish chases which** | Ax6 | Aρ vs ρA | L_z ≈ Ax4 |

---

## Definitive Axis Status

From `sim_definitive_7axis.py` (corrected formulations, mixed states):

| Axis | Best formulation | Max overlap | Status |
|---|---|---|---|
| **Ax0** | Coarse-graining | 0.70 (Ax1/Ax5) | Cluster member |
| **Ax1** | Open/closed channel | 0.70 (Ax0 pure), 0.14 (Ax0 hot) | **Separates on hot states** |
| **Ax2** | Boundary (concentrated/spread) | 0.60 (Ax1) | ⚠️ Marginal |
| **Ax3** | **CP mirror (ψ_L ↔ ψ_R*)** | **0.47** | **Cleanest base axis** |
| **Ax4** | Process direction (CW/CCW path) | **0.97 (Ax6)** | **≡ Ax6** |
| **Ax5** | Trajectory curvature (FGA/FSA) | 0.66 (Ax0) | Cluster with Ax0 |
| **Ax6** | Action side (Aρ vs ρA) | **0.97 (Ax4)** | **≡ Ax4** |

### Verified Merges
- **Ax4 ≡ Ax6**: Process direction and action side are the same DOF (0.97 overlap). In the yin-yang: which way you spin it determines who chases whom.

### Verified Separations  
- **Ax1 ≠ Ax5**: Separate on mixed states. Channel type (open/closed) ≠ trajectory curvature (FGA/FSA). Curvature overlap with Ax1 stays at 0.12–0.17 at d=8 regardless of entropy.
- **Ax3 ≠ Ax6**: CP mirror (0.24 overlap) — cleanly distinct with correct formulation.

### Open Conflations
- **Ax0 / Ax5**: 0.66 overlap. May be aspects of the same DOF.
- **Ax0 / Ax1**: 0.70 on pure states, but 0.14 on hot states — they separate with entropy.

---

## Known Bugs in Current Sims

> [!WARNING]
> Codex identified these issues:
> 1. `sim_geometry_ratchet_chain.py:53` — non-normalized Weyl-state bug
> 2. `sim_weyl_dof_analysis.py:64` — mis-specified 4×4 density matrix construction
> 3. Several sims use `make_random_density_matrix()` on generic space, not on the constraint manifold

---

## Weyl DOF Structure

From `sim_weyl_dof_analysis.py` (8 independent DOFs from Weyl pair):

```
SU(2)_L × SU(2)_R × U(1) × Z₂ = 3 + 3 + 1 + 1 = 8 DOFs
```

| DOF | Physical meaning |
|---|---|
| L_x, L_y, L_z | Left SU(2) rotation (3 DOF) |
| R_x, R_y, R_z | Right SU(2) rotation (3 DOF) |
| phase | U(1) relative phase (1 DOF) — **lost at density projection** |
| parity | Z₂: ψ_L ↔ ψ_R exchange (1 DOF) |

---

## Sim Files

| File | What it tests |
|---|---|
| `sim_axis_anti_conflation.py` | Original 7×7 overlap |
| `sim_axis_exploration_suite.py` | Ax1/Ax5 redundancy, Ax3/Ax6 disentangle |
| `sim_axis_independence_matrix.py` | 11×11 definitive overlap matrix |
| `sim_axis_dimension_scaling.py` | d-scaling: does cluster split? |
| `sim_axis_hopf_geometry.py` | Test on actual Hopf geometry |
| `sim_weyl_dof_analysis.py` | 13 candidates → 8 Weyl DOFs |
| `sim_geometry_ratchet_chain.py` | Named axes → Weyl DOFs + info loss |
| `sim_yinyang_axis_mapping.py` | Yin-yang features → Weyl DOFs |
| `sim_ax1_ax5_separation.py` | Ax1/Ax5 blur separation (superseded) |
| `sim_ax1_ax5_curvature.py` | Ax1/Ax5 curvature separation |
| `sim_corrected_axes.py` | CP mirror Ax3, process Ax4 |
| `sim_definitive_7axis.py` | All 7 corrected axes on mixed states |

---

## Next Steps

1. **Fix sim bugs** flagged by Codex (normalization, state construction)
2. **Resolve Ax0/Ax5** — are coarse-graining and curvature truly different?
3. **Map the full ratchet chain** with all intermediate layers (S³, Bloch, etc.)
4. **Settle the Ax4≡Ax6 merge** — is there any condition where they separate?
5. **Assign Jungian labels** to the surviving DOFs
