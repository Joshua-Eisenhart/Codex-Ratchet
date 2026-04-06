# V5 Content Gap Analysis

Date: 2026-04-05
Purpose: What the v5 docs contain that the clean docs are MISSING.
         This is the integration guide for the next doc pass.

---

## Critical Missing Content (from math/engine/terrain v5 docs)

### 1. Four Base Operators — Explicit Kraus Forms

The clean docs mention Ti/Te/Fi/Fe by name. The v5 docs have:
- Full Kraus form expansions (K₀, K₁, K₂ matrices for each)
- Trace-preserving checks (K₀†K₀ + K₁†K₁ + K₂†K₂ = I)
- Continuous-time generators (Lindbladian forms)
- Key claim: UP/DOWN is NOT additional operator math — it only
  appears after a terrain map is chosen. UP/DOWN are composition
  orders, not new operators.
Source: operator math explicit.md

### 2. Full 16 Placements with Exact Tuples

The clean docs mention 16 placements loosely. The v5 docs have:
- Exact mathematical tuples (γ_ℓ^s, X_τ^s, Φ_τ^s) for each
- Paired (spinor law, density law) for each placement
- Set-theoretic hierarchy: 4 loops → 8 terrain laws → 16 placements
- Structural lock notation
Source: terrain rosetta strong math.md, terrain math.md, terrains.md

### 3. Horizontal Condition A(γ̇_out) = 0

The clean docs mention fiber/base loops. The v5 docs prove:
- The horizontal condition on the base loop is GEOMETRIC NECESSITY
- Inner loop keeps density constant (density-stationary)
- Outer loop changes density (density-traversing)
- Loops are density-constrained paths, not free spinor curves
Source: terrains.md, terrain math.md

### 4. Loop Vector Fields

The clean docs don't have these. The v5 docs define:
- Y_in and Y_out as explicit partial derivatives on spinors
- How the vector fields relate to the Hopf connection
Source: terrain math.md

### 5. Pre-Entropy Ladder (19 Layers)

The clean docs have 8 "resolution levels." The v5 docs have a
19-layer explicit ladder from root constraints to entropy:
1. Root constraints → 2. Extended doctrine → 3. M(C) → 4. C²
carrier → 5. Hopf → 6. Nested tori → 7. Weyl → 8. Chiral density
→ 9. Loop laws → 10. Engine family → 11. Placement law →
12. Negatives on geometry → 13. Entangling operators → 14. Joint
cut-state → 15. Bridge family → 16. Shell/history → 17. Signed/
unsigned entropy readouts → 18. Axis 0 kernel → 19. Dynamics on
entropy

Key claim: entropy is layer 17. Layers 1-16 are prerequisites.
No entropy equation until layer 17.
Source: Pre Entropy tables.md

### 6. Pre-Axis Admission Pipeline

The clean docs have the "anti-teleology" and "graveyard" concepts.
The v5 docs have a formal 6-phase admission process:
- A: define constrained object language
- B: ground in QIT carrier
- C: refine geometry/Weyl/transport
- D: classify candidate vs diagnostic
- E: embargo unadmitted math
- F: elevate admitted machinery to Axis use

Plus 6 admission checks, 6 classical leakage types with defenses,
and the Axis Embargo Rule: no math may function as an Axis object
until admitted as constrained, QIT-grounded, simmed, and
negatively tested.
Source: Pre axies math and geometry work out.md

### 7. Flux Dependency Chain (20 Steps)

The clean docs barely mention flux. The v5 docs have:
- 20-step dependency chain from root constraints to flux placement
- 7 possible flux branch candidates (A-G) with mathematical forms
- 7 decision gates to classify flux
- Extended pre-Axis ladder chain showing where flux sits
- Key claim: flux is NOT primitive — it's derived from stagewise deltas
Source: Weyl Flux.md

### 8. Axis Grounding Status

The clean docs don't distinguish which axes are source-grounded
vs unresolved. The v5 docs have:
- Explicit status per axis (source-grounded / chart-level / open)
- Axis 3 explicitly unresolved (outer vs inner vs chirality)
Source: ENGINE_64_SCHEDULE_ATLAS.md

### 9. 64 Schedule Index Grid

The clean docs mention 64 steps. The v5 docs have:
- 8×8 grid: rows = terrains, cols = signed operators
- Only 16 of 64 slots are chart-locked macro-stages (marked *)
- Governing split: IGT→outcome, Jung→operators, I-Ching→schedule
- Hard Non-Claims list
Source: ENGINE_64_SCHEDULE_ATLAS.md

### 10. Density Visibility Proofs

The clean docs assert fiber=stationary, base=traversing.
The v5 docs PROVE it:
- Sheet flows showing opposite Bloch rotations
- Type 1 gets ×2, Type 2 gets -×2
Source: terrain math.md

### 11. IGT Parse Rule

The clean docs mention IGT loosely. The v5 docs have:
- Exact parse rule: outer = UPPERCASE, inner = lowercase
- Full paired view by IGT label
- Axis-4 inversion between Type 1 and Type 2
Source: Rosetta Terrain Mapping.md

### 12. Loop Order Rules (Axis 4)

- Inductive: Se → Si → Ni → Ne
- Deductive: Se → Ne → Ni → Si
- Type 1: outer=deductive, inner=inductive
- Type 2: outer=inductive, inner=deductive
Source: ENGINE_64_SCHEDULE_ATLAS.md

---

## What This Means

The clean docs captured the PHILOSOPHY well (constraint surface,
nominalism, anti-teleology, FEP, evolutionary logic). But they
MISSED most of the MATH:
- Operator forms (Kraus, Lindbladian)
- Placement tuples (exact mathematical objects)
- Loop geometry proofs (horizontal condition, density visibility)
- The 19-layer pre-entropy ladder
- The formal admission pipeline and embargo rules
- Flux classification
- The 64-schedule grid structure
- Axis grounding status

The next pass should integrate this mathematical content into the
clean docs without losing the philosophical framing. The math is
what makes the philosophy testable.

---

## Awaiting: Batch 2 (axis/rosetta/cosmology) and Batch 3 (system/philosophy)
