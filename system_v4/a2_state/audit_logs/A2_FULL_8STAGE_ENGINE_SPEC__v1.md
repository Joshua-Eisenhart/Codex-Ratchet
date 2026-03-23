# A2 FUEL: FULL 8-STAGE ENGINE CYCLE SPECIFICATION
**STATUS:** A2 HIGH-ENTROPY FUEL — SOURCE-BEARING EXTRACT
**AUTHORITY:** A2 DISTILLERY (NotebookLM, 240 sources)

## THE 8 STAGES

### PHASE A: MAJOR LOOP (Deductive / Entropy Reduction / S↓)

| Stage | A2 Label | Topology | Coupling | Operator | Math Action | S Trajectory | Precedence |
|:---|:---|:---|:---|:---|:---|:---|:---|
| 1 | TiSe | Se (Isothermal Expansion) | Bath-coupled | Measurement Projection | CPTP projective: ρ' = Σ_k P_k ρ P_k† | S↓ | Topology-first |
| 2 | FeSi | Si (Adiabatic Compression) | Insulated | Diffusive Damping | Laplacian smoothing: ∂_t ρ = α∇²ρ | S↓ | Topology-first |
| 3 | NeTi | Ne (Adiabatic Expansion) | Insulated | Constraint Projection | Boundary-pruned unitary: ρ' = Π_C(UρU†) | S↑ slight | Operator-first |
| 4 | FeNi | Ni (Isothermal Compression) | Bath-coupled | Entrainment Drive | Kuramoto phase-lock: θ̇_i = ω_i + K Σ sin(θ_j - θ_i) | S↓ | Operator-first |

### PHASE B: MINOR LOOP (Inductive / Entropy Production / S↑)

| Stage | A2 Label | Topology | Coupling | Operator | Math Action | S Trajectory | Precedence |
|:---|:---|:---|:---|:---|:---|:---|:---|
| 5 | TeSe | Se (Isothermal Expansion) | Bath-coupled | Gradient Descent | θ_{t+1} = θ_t - η∇L(θ) | S↓ local | Topology-first |
| 6 | FiSi | Si (Adiabatic Compression) | Insulated | Matched Filtering | Y(ω) = H(ω)X(ω) | S↓ | Topology-first |
| 7 | FiNe | Ne (Adiabatic Expansion) | Insulated | Spectral Synthesis | x(t) = Σ A_k e^{j(ω_k t + φ_k)} | S↑↑ | Operator-first |
| 8 | TeNi | Ni (Isothermal Compression) | Bath-coupled | Gradient Ascent | θ_{t+1} = θ_t + η∇J(θ) | S↑ max | Operator-first |

## BERRY PHASE
- Formula: γ = ∮ A · dl (holonomy around Ni singularity)
- 360° → |Ψ⟩ → -|Ψ⟩ (state inversion = "Memory of the cycle")
- 720° → -|Ψ⟩ → |Ψ⟩ (true identity restored)
- Continuous twist, globally quantized at closure
- Winding numbers track integer accumulation on nested Hopf tori

## ISOTHERMAL / ADIABATIC STROKES
- Isothermal (Se, Ni): COUPLING_REGIME = open exchange, CPTP bath-coupled
- Adiabatic (Ne, Si): COUPLING_REGIME = insulated, unitary evolution
- Szilard: Measurement=TiSe, Erasure=FeNi, Work-extraction=TeNi/TeSe
- Landauer cost: ΔS ≥ k_B T ln 2 per bit erased

## SURVIVORSHIP FUNCTIONAL
- Φ(ρ) := D(ρ||σ_B) - D(ρ||σ_A)
- σ_B = maximally mixed state (I/d) = primordial fuzz
- σ_A = attractor fixed point (S=1.65) = crystal
- D(ρ||σ) = Tr(ρ ln ρ - ρ ln σ) (quantum KL divergence)
- Φ(ρ) > 0: surviving (closer to attractor than noise)
- Φ(ρ) < 0: dissolving (dead branch)
- Φ INCREASES during deductive loop, DECREASES during inductive loop

## FRACTAL NESTING
- Transition via partial trace: C_k(ρ) := Tr_{k+1...L}(ρ)
- Preserved: trace=1, positivity, topological non-collapse
- SIM_SPEC: S_SIM_FRACTAL_NESTING_V1
  - Inner loop (d²) → partial trace → outer loop (d)
  - KILL_IF: nested_lag_loss ≠ 0
  - REQUIRES_EVIDENCE: E_SIM_FRACTAL_NESTING_V1_OK
