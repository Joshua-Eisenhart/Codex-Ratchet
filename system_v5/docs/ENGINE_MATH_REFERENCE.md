# Engine Math Reference

Date: 2026-04-05
Status: Extracted from v5 docs (operator math explicit.md, terrain math.md).
        Math is verbatim from source. Not paraphrased.

---

## Scope and Boundary

This doc owns:
- the four intrinsic operator families
- the loop vector fields
- the density-visibility proof
- the exact terrain/loop/placement separation

This doc does NOT own:
- the axis schedule taxonomy as a whole
- live bridge or entropy status
- current repo truth about what has been earned by sims

Read this with:
- `CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md` for the broader derivation chain
- `AXIS_AND_ENTROPY_REFERENCE.md` for axis placement and entropy routing
- `TIER_STATUS.md` for live status

Short rule:
- this is the operator/terrain math packet
- do not quote it as evidence that a later bridge, cut, or Axis 0 claim is closed

## Four Base Operators

Only 4 intrinsic operator families exist. UP/DOWN is NOT additional
operator math — it only appears after a terrain map is chosen.
UP and DOWN are composition orders, not new operators.

### State Matrix Parameters

ρ = (a, d, u, v) where a,d,u,v ∈ ℝ, a ≥ 0, d ≥ 0, a+d = 1, u²+v² ≤ ad

### Ti (σ_z dissipation)

Kraus operators:
  K₀ = √(1-q₁) I
  K₁ = √q₁ |0⟩⟨0|
  K₂ = √q₁ |1⟩⟨1|

Trace-preserving: K₀†K₀ + K₁†K₁ + K₂†K₂ = (1-q₁)I + q₁P₀ + q₁P₁ = I

Lindbladian: ℒ₁(ρ) = (κ₁/2)(σ_z ρ σ_z - ρ)

Output: ℒ₁(ρ) = [[0, -κ₁(u-iv)], [-κ₁(u+iv), 0]]

Effect: destroys off-diagonal coherence in Z basis. Leaves populations unchanged.

### Te (σ_x dissipation)

Kraus operators:
  K₀ = √(1-q₂) I
  K₁ = √q₂ · (1/2)[[1,1],[1,1]]
  K₂ = √q₂ · (1/2)[[1,-1],[-1,1]]

Trace-preserving: K₀†K₀ + K₁†K₁ + K₂†K₂ = (1-q₂)I + q₂Q₊ + q₂Q₋ = I

Lindbladian: ℒ₂(ρ) = (κ₂/2)(σ_x ρ σ_x - ρ) = (κ₂/2)[[d-a, 2iv], [-2iv, a-d]]

Effect: destroys coherence in X basis. Changes populations.

### Fi (σ_x rotation — unitary)

Unitary: U_x(θ) = exp(-iθσ_x/2) = [[cos(θ/2), -i·sin(θ/2)], [-i·sin(θ/2), cos(θ/2)]]

Lindbladian: ℒ₃(ρ) = -i[ω₃σ_x/2, ρ] = [[ω₃v, -iω₃(d-a)/2], [iω₃(d-a)/2, -ω₃v]]

Effect: rotates Bloch vector around x-axis. Preserves purity.

### Fe (σ_z rotation — unitary)

Unitary: U_z(φ) = exp(-iφσ_z/2) = [[e^{-iφ/2}, 0], [0, e^{iφ/2}]]

Lindbladian: ℒ₄(ρ) = -i[ω₄σ_z/2, ρ] = [[0, -iω₄(u-iv)], [iω₄(u+iv), 0]]

Effect: rotates Bloch vector around z-axis. Preserves purity.

### Operator Classification

| Operator | Type | Generator | Axis 5 family |
|---|---|---|---|
| Ti | Dissipative (CPTP) | σ_z dephasing | T-kernel |
| Te | Dissipative (CPTP) | σ_x dephasing | T-kernel |
| Fi | Unitary | σ_x rotation | F-kernel |
| Fe | Unitary | σ_z rotation | F-kernel |

Strength parameters: q₁, q₂ (dissipation), θ, φ (rotation angles).
Lindbladian rates: κ₁, κ₂ (dissipative), ω₃, ω₄ (unitary).

---

## Loop Vector Fields

### Inner Field (fiber loop — density-stationary)

Y_in ψ_s = ∂_φ ψ_s = i [e^{i(φ+χ)} cos η, e^{i(φ-χ)} sin η]ᵀ

### Outer Field (base loop — density-traversing)

Y_out ψ_s = (-cos(2η) ∂_φ + ∂_χ) ψ_s
           = i [(1-cos2η) e^{i(φ+χ)} cosη, -(1+cos2η) e^{i(φ-χ)} sinη]ᵀ

### Density Visibility Proof

Inner density path:
  ρ_in^s(u) = ρ_s(φ₀+u, χ₀; η₀) = ρ_s(φ₀, χ₀; η₀)

The density is INDEPENDENT of the inner loop parameter u.
The φ coordinate varies but does not affect density.

Outer density path:
  ρ_out^s(u) = ρ_s(φ₀ - cos(2η₀)u, χ₀+u; η₀)
             = [[cos²η₀, e^{2i(χ₀+u)} cosη₀ sinη₀],
                [e^{-2i(χ₀+u)} cosη₀ sinη₀, sin²η₀]]

The off-diagonal phase rotates with u → density CHANGES along outer loop.

---

## Exact Separation: Terrain vs Loop vs Placement

| Layer | Count | Elements |
|---|---:|---|
| Terrain families | 4 | {Se, Ne, Ni, Si} |
| Terrains | 8 | {(τ,s) : τ ∈ {Se,Ne,Ni,Si}, s ∈ {L,R}} |
| Placements | 16 | {(τ,s,ℓ) : τ ∈ families, s ∈ {L,R}, ℓ ∈ {in,out}} |

- Terrain = the generator X_{τ,s}
- Loop = the spinor path field Y_in or Y_out
- Placement = the pair (X_{τ,s}, Y_ℓ)

---

## 16 Placements (Exact Mathematical Tuples)

Each placement is a paired (spinor law, density law):

### Type 1 (Left Weyl, s=L)

| # | Terrain | Loop | Math |
|---|---|---|---|
| 1 | Se/Funnel | inner | (ψ̇_L, ρ̇_L) = (Ω_{Se,L,in} Y_in ψ_L, X_{Se,L}(ρ_L)) |
| 2 | Se/Funnel | outer | (ψ̇_L, ρ̇_L) = (Ω_{Se,L,out} Y_out ψ_L, X_{Se,L}(ρ_L)) |
| 3 | Ne/Vortex | inner | (ψ̇_L, ρ̇_L) = (Ω_{Ne,L,in} Y_in ψ_L, X_{Ne,L}(ρ_L)) |
| 4 | Ne/Vortex | outer | (ψ̇_L, ρ̇_L) = (Ω_{Ne,L,out} Y_out ψ_L, X_{Ne,L}(ρ_L)) |
| 5 | Ni/Pit | inner | (ψ̇_L, ρ̇_L) = (Ω_{Ni,L,in} Y_in ψ_L, X_{Ni,L}(ρ_L)) |
| 6 | Ni/Pit | outer | (ψ̇_L, ρ̇_L) = (Ω_{Ni,L,out} Y_out ψ_L, X_{Ni,L}(ρ_L)) |
| 7 | Si/Hill | inner | (ψ̇_L, ρ̇_L) = (Ω_{Si,L,in} Y_in ψ_L, X_{Si,L}(ρ_L)) |
| 8 | Si/Hill | outer | (ψ̇_L, ρ̇_L) = (Ω_{Si,L,out} Y_out ψ_L, X_{Si,L}(ρ_L)) |

### Type 2 (Right Weyl, s=R)

| # | Terrain | Loop | Math |
|---|---|---|---|
| 9 | Se/Cannon | inner | (ψ̇_R, ρ̇_R) = (Ω_{Se,R,in} Y_in ψ_R, X_{Se,R}(ρ_R)) |
| 10 | Se/Cannon | outer | (ψ̇_R, ρ̇_R) = (Ω_{Se,R,out} Y_out ψ_R, X_{Se,R}(ρ_R)) |
| 11 | Ne/Spiral | inner | (ψ̇_R, ρ̇_R) = (Ω_{Ne,R,in} Y_in ψ_R, X_{Ne,R}(ρ_R)) |
| 12 | Ne/Spiral | outer | (ψ̇_R, ρ̇_R) = (Ω_{Ne,R,out} Y_out ψ_R, X_{Ne,R}(ρ_R)) |
| 13 | Ni/Source | inner | (ψ̇_R, ρ̇_R) = (Ω_{Ni,R,in} Y_in ψ_R, X_{Ni,R}(ρ_R)) |
| 14 | Ni/Source | outer | (ψ̇_R, ρ̇_R) = (Ω_{Ni,R,out} Y_out ψ_R, X_{Ni,R}(ρ_R)) |
| 15 | Si/Citadel | inner | (ψ̇_R, ρ̇_R) = (Ω_{Si,R,in} Y_in ψ_R, X_{Si,R}(ρ_R)) |
| 16 | Si/Citadel | outer | (ψ̇_R, ρ̇_R) = (Ω_{Si,R,out} Y_out ψ_R, X_{Si,R}(ρ_R)) |

---

## Source

Extracted verbatim from:
- system_v5/READ ONLY Reference Docs/operator math explicit.md
- system_v5/READ ONLY Reference Docs/terrain math.md
