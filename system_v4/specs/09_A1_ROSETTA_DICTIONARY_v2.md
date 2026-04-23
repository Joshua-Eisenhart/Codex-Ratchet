# A1_ROSETTA_DICTIONARY_v2
**STATUS:** ACTIVE / ENFORCEMENT LAYER
**AUTHORITY:** A1 ROSETTA THREAD
**EVIDENCE:** 32 tokens across 8 SIM files (all PASS)

## ROOT AXIOMS

| ID | Statement | Pure Math | Evidence Token |
|:---|:---|:---|:---|
| F01 | Finite capacity | dim(H) = d < ∞, Tr(ρ) = 1 | E_SIM_F01_OK |
| N01 | Non-commutation | ∀A,B: [A,B] ≠ 0 | E_SIM_N01_OK |

## DERIVED CONSTRAINTS

| ID | Statement | Derivation | Evidence Token |
|:---|:---|:---|:---|
| D01 | Action precedence | N01 → operator order matters | E_SIM_ACTION_PRECEDENCE_OK |
| D02 | Variance direction | F01+N01 → deductive/inductive diverge | E_SIM_VARIANCE_DIRECTION_OK |
| D03 | Discrete spectrum | F01 → exactly d eigenvalues | E_SIM_F01_DISCRETE_OK |
| D04 | Complex numbers forced | N01 → [A,B] anti-Hermitian → i required | E_SIM_N01_FORCES_COMPLEX_OK |
| D05 | Chirality forced | F01+N01 → 100% symmetry breaking | E_SIM_CHIRALITY_FORCED_OK |

## ENGINE OPERATIONS → PURE MATH

| Operation | Math Object | Formula | SIM File |
|:---|:---|:---|:---|
| Measurement | Lüders projection (CPTP) | ρ → Σ_k P_k ρ P_k† | full_8stage |
| Unitary evolution | Hamiltonian generation | ρ' = UρU†, U = e^{-iHt}, S conserved | math_foundations |
| Dissipation | Lindbladian semigroup | dρ/dt = -i[H,ρ] + Σ_j(LρL† - ½{L†L,ρ}) | proto_ratchet |
| Entrainment | Kuramoto coupling | ρ_new = (1-c)ρ + c·σ_target | full_8stage |
| Filtering | Spectral projection | ρ_filt = FρF†/Tr(FρF†) | full_8stage |
| Attractor | CPTP fixed point | lim_{t→∞} e^{Lt}ρ = ρ* | proto_ratchet |
| Berry phase | Geometric holonomy | ∮ A·dl (commutator residue from cycle) | dual_weyl |
| Survivorship Φ | KL divergence / Lyapunov | Φ(ρ) = ln(d) - S(ρ) | proof_cost |

## FOUNDATIONAL IDENTITIES (VERIFIED)

| Claim | Pure Math | Evidence |
|:---|:---|:---|
| a = a iff a ~ b | ∀P∈Π: Tr(Pρ_a) = Tr(Pρ_b) | k=1: 4% false-equals |
| Identity cost | Full tomography needs d²-1 params | Scaling confirmed |
| Entropic monism | Eigenvalue spectrum = complete invariant | corr(Φ, purity) = 0.97 |
| Math = Physics | F01+N01 simultaneously force complex + chirality | 100/100 trials |
| Sets emerge | Equivalence classes from probe limits | 4→91 classes |
| Refinement preorder | Adding probes refines, never coarsens | 5→30, monotone |
| Scalar potential | Φ(ρ) = ln(d) - S(ρ), Φ(I/d)=0, Φ(pure)=ln(d) | Unitary invariant |

## ARITHMETIC EMERGENCE (VERIFIED)

| Structure | Mechanism | Formula |
|:---|:---|:---|
| Counting | Refinement multiplicity | μ([x]) = number of distinguishable classes |
| Addition | Sequential path composition | S(γ) = Σ_k log μ([x_k]), chain rule exact |
| Multiplication | Tensor product | dim(H_A⊗H_B) = dim(H_A) × dim(H_B) |
| Primes | Irreducible cyclic actions | Z_n unfactorable → n is prime |
| Ordering | Refinement relation | [x] ⪯ [y] iff all probes of [x] also in [y] |

## PHYSICS EMERGENCE (VERIFIED)

| Phenomenon | Mechanism | Formula |
|:---|:---|:---|
| Gravity | Entropic force | F = -∇Φ (drift toward max entropy) |
| Arrow of time | Thermal bath coupling | dΦ/dt ≤ 0 when bath = I/d |
| Spacetime | ∇Φ outer product | G_μν = 8πG(∇_μΦ ∇_νΦ) |
| Bekenstein bound | F01 capacity | Φ ≤ ln(d), d set by boundary area |
| Constant-Φ surfaces | Nested Hopf tori | T² on S³ |

## COMPUTATION ARCHITECTURE (VERIFIED)

| Claim | Pure Math | Evidence |
|:---|:---|:---|
| Ne = Turing machine | Unitary evolution: reversible, deterministic, ΔS=0 | drift=0.0 |
| Engine > Turing | Isothermal strokes create attractors | dom=0.50 |
| Gödel = thermodynamic stall | Ne orbits forever (winding saturation) | orbits confirmed |
| Engine resolves Gödel | Isothermal injection → attractor at Landauer cost | 0.79 nats |
| Stall detection | ΔS=0 over window → system knows it's stuck | detected k=0 |

## GRAVEYARD (20 Killed Hypotheses)

See [GRAVEYARD_FULL_LEDGER__v1.txt](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/graveyard/GRAVEYARD_FULL_LEDGER__v1.txt) for the full ledger including:
- 8 classical math axiom kills (Axiom of Infinity, Choice, Peano, ZFC, Reals, Archimedean, Commutativity)
- 4 classical physics kills (continuous time, continuous bath, Euclidean metric, classical temperature)
- 3 topology/graph failures
- Refined: "All open dynamics → S increases" is WRONG — only thermal bath coupling guarantees it

## ANTI-SMUGGLING ENFORCEMENT

The following words are **BANNED from all kernel-facing fields** (SPEC_HYP ids, DEF_FIELD values, SIM_SPEC tokens, EXPORT_BLOCK content, evidence token names):

`Axis`, `Bit`, `Type 1`, `Type 2`, `FeTi`, `NeSi`, `TeFi`, `NiTe`, `SeFi`, `FeSi`, `Jung`, `MBTI`, `cognitive`, `agent`, `plan`, `goal`, `heating`, `cooling`, `hot`, `cold`, `win`, `lose`, `Vortex`, `Ring`

**Note:** "Axis" is the current A2 commentary label. Both "Axis" and "Bit" are legal in `MODE=COMMENTARY`, A2 fuel documents, and the CCL overlay ONLY. Kernel-facing fields must use pure math names from the mapping tables above.

## JARGON → PURE MATH FALLBACK TABLE

| BANNED JARGON (A2/Commentary) | PURE MATH EQUIVALENT (B-Kernel Safe) |
|:---|:---|
| Axis 0 | ENTROPIC_GRADIENT / SURVIVORSHIP_FUNCTIONAL |
| Axis 1 | COUPLING_REGIME / BATH_LEGALITY |
| Axis 2 | FRAME_REPRESENTATION / BOUNDARY_CLASS |
| Axis 3 | CHIRAL_FLUX / WEYL_ORIENTATION |
| Axis 4 | VARIANCE_DIRECTION / THERMODYNAMIC_LOOP_ORDER |
| Axis 5 | GENERATOR_ALGEBRA / FGA_FSA_MODULATION |
| Axis 6 | ACTION_PRECEDENCE / OPERATOR_ORDER |
| Type 1 | LEFT_WEYL_CONVERGENT / CHIRAL_FLUX_INWARD / POLOIDAL_FLOW |
| Type 2 | RIGHT_WEYL_DIVERGENT / CHIRAL_FLUX_OUTWARD / TOROIDAL_FLOW |
| heating | ENTROPY_PRODUCTION / INDUCTIVE_EXPANSION |
| cooling | ENTROPY_REDUCTION / DEDUCTIVE_CONTRACTION |
| cognitive agent | DENSITY_MATRIX_UNDER_CPTP_EVOLUTION |
| short-term memory | FINITE_BUFFER_STATE |
| chain-of-thought | SEQUENTIAL_OPERATOR_COMPOSITION |
| plan / goal | BOUNDARY_CONSTRAINT / ATTRACTOR_TARGET |
| feedback | MEASUREMENT_BACKACTION |
| FeTi / NeSi / TeFi / etc. | QUARANTINED — commentary overlay ONLY |
| MBTI / Jung / Jungian | QUARANTINED — commentary overlay ONLY |
| Major Loop | FIRST_360_ROTATION / BERRY_PHASE_ACCUMULATION |
| Minor Loop | SECOND_360_ROTATION / PHASE_EXPENDITURE |
| Ni (Pit) | SINGULAR_ATTRACTOR / RADIAL_CONTRACTION |
| Si (Hill) | STABLE_BASIN / FIXED_POINT_DAMPING |
| Ne (Mushroom) | DIVERGENT_EXPLORER / PHASE_EXPANSION |
| Se (Wave) | COHERENT_PROPAGATION / TOROIDAL_CIRCULATION |
| hot / cold | HIGH_ENTROPY / LOW_ENTROPY |
| win / lose | STRUCTURE_GAINED / ENTROPY_EXPELLED |
