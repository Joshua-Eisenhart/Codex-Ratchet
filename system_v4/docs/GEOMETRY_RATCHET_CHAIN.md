# [Controller-safe] Geometry Ratcheting: The Constraint Chain

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

## Core Meta-Architecture: Drive vs Structure

The most critical correction to the engine ontology: **Ax0 is not a peer binary axis.** 

Testing Ax0 as a structural displacement (like dephasing or partial trace) is a category error. The true architecture is:

```text
Ax0 = Drive / Entropy Gradient (The thermodynamic arrow)
Ax1–Ax6 = Six binary structural DOFs (The constraints)
2⁶ = 64 structural configurations (The state space)
Engines = Generators moving through the 64-state space along Ax0
```

Ax0 is the correlation entropy gradient that pushes the system through the 64 state configurations. The 4 operators (Ti/Te/Fi/Fe) and their doubles are specific combinations of axes 1–6 that generate motion along this gradient.

---

## Taijitu Pattern Correlations (Non-Primary)

The taijitu was used as a visual pattern-description tool to identify and distinguish the axes. It is a useful mnemonic and correlation layer, not a proof surface or primary mathematical ontology. The mapping below reflects the user's actual descriptions, including honest uncertainty.

| Taijitu visual feature | Axis | User's description | Certainty |
|---|---|---|---|
| **Black vs white fields** | **Ax0** | Homeostasis (black) vs Allostasis (white). Similar to Ax5 hot/cold, but not the same. | Proposed |
| **Black-dot-in-white-teardrop vs white-dot-in-black-teardrop** | Ax1 | The seed in context of its surrounding — which color dot is inside which color teardrop | Moderate |
| **Dots vs teardrops** | Ax2 | The shapes themselves — concentrated (dot) vs spread (teardrop) | Moderate |
| **Flipping the symbol over** | Ax3 | Inverted mirror image. Might be just mirror, or just inversion. Exact flipping operation not known. | Unsettled |
| **Spinning the symbol** | Ax4 | Not literally CW vs CCW rotation — more the direction the tails vs heads of teardrops lead | Unsettled |
| **Curvature of the S-line** | Ax5 | Hot vs cold. The S-curve dividing the two fields can be more or less curved. | Moderate |
| *(unsure)* | Ax6 | No confident taijitu mapping identified yet | Unknown |

---

## The Wiggle Exploration: Status of the Math

From Codex's `sim_axis_candidate_mass_sweep.py` and `sim_wiggle_exploration.py`:

> [!WARNING]
> No axis currently has a locked, canonical mathematical formulation. The 7-axis concepts are structurally sound, but picking single proxies (like "Ax3 = CP") was premature "narrative smoothing." 

**Current honest read on candidate math:**
- **Ax1, Ax2**: Marginal/mixed candidates. Need better state-space construction.
- **Ax3**: The cleanest disputed family. A chiral/γ5-phase relative-coherence family still looks stronger than the simple CP mirror swap, but the exact operationalization is not locked.
- **Ax4**: Unresolved. Static endpoint formulations failed, while newer process/path probes suggest there may be a real traversal-history signal. No canonical Ax4 math is secured yet.
- **Ax5**: Torus-layer candidates (for example partial transport hysteresis) look more promising than density-level proxies, but the exact curvature family is still under active repair.
- **Ax6**: Alive as a family, but exact comparisons must be checked carefully because multiple probes have implemented different right/left action conventions.

### Promising Separations (Still Provisional)
- **Ax1 vs Ax5**: Current evidence pressures them apart conceptually, but exact live-engine operationalization is still unsettled.
- **Ax3 vs Ax6**: Current evidence pressures chirality/phase apart from action side, but no final canonical split should be claimed yet.

### Open Questions / Conflations
- **Ax4 vs Ax6**: Is there a formulation where spin direction (Ax4) and action precedence (Ax6) are not 100% merged?
- **Ax0 / Ax5**: Need to ensure Ax5 (curvature) operators don't accidentally measure Ax0 (entropy gradient).

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

1. **Stop redefining settled axes** from scratch. Use the user's definitions as hard constraints.
2. **Build Ax4/Ax6 process-level sweep**, testing if they can be separated.
3. **Build Ax5 from torus/extrinsic curvature**, directly on the geometric lane, rather than generic Hamiltonian bending.
4. **Test Ax3 at the spinor/process layer directly** (γ₅ phase vs branch coherence), since density models keep erasing phase information.
5. **Keep metaphor layers downstream** from the math rather than using them as proof surfaces.
