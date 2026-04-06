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

---

## Critical Missing Content (from axis/rosetta/cosmology v5 docs)

### 13. Full 7-Row Global Axis Table

Axes 0-6 mapped across 8 columns: math, status, Jung, IGT, I-Ching,
terrain, etc. NOT in clean docs.
Source: AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS

### 14. Eight Terrain Equations (full form, both Types)

Exact Lindblad/Hamiltonian forms for all 8 terrains with Type 1/2
variants. NOT in clean docs as formal equations.
Source: apple axes terrain operator math.md

### 15. Eight Signed Judging Variants

Ti↑/Ti↓/Te↑/Te↓/Fi↑/Fi↓/Fe↑/Fe↓ with precedence semantics.
NOT systematized in clean docs.
Source: JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP

### 16. Type 1/Type 2 Pair Lock Table

Exact mathematical differences between Type 1 and Type 2 for each
terrain. NOT in clean docs.
Source: apple axes terrain operator math.md

### 17. 36-Row Ratchet Order Master Table

Every object in the system ordered by ratchet precedence with status
(live base / live geometry / live engine / live proxy / open bridge).
NOT in clean docs.
Source: QIT_ENGINE_GEOMETRY_ENTROPY_BRIDGE_MASTER_TABLE

### 18. Sign Encoding Closure (χ₀ = χ₁χ₂)

Explicit sign structure and closure proof. NOT in clean docs.
Source: AXIS_0_1_2_QIT_MATH.md

### 19. Token Partition Tables (Axes 3 and 6)

Which tokens are inner/outer (Ax3) and up/down (Ax6).
Source: TAIJITU_PROBE_RECONCILIATION_CARD, AXES_0_6 ATLAS

### 20. Active Mismatches and Demoted Hypotheses

Explicit reconciliation between symbolic layer and lower stack.
What was tried and killed. Valuable graveyard data.
Source: TAIJITU_PROBE_RECONCILIATION_CARD

### 21. Anti-Flattening Rule

Sim composition must go substage → stage → loop → engine → schedule.
Cannot flatten/skip levels.
Source: apple axes terrain operator math.md

---

## Critical Missing Content (from system/philosophy/process v5 docs)

### 22. Admissibility Fence Catalog (BC04-BC12, T1-T8)

24 formal fences (12 base boundary conditions + 12 topology/relation
fences). Complete "anti-assumption" structure. NOT systematized in
clean docs.
Source: Formal constraints and geometry.md

### 23. CS Translation Layer

The entire system described in computational terms:
- finitude → budgets/caps
- noncommutation → append-only logs
- 8 CS general principles
- Graph-topological computation model
Source: CS version of system first draft.md

### 24. Sim Admission Contract + Process Contract

Formal enforcement structures:
- Required declarations per sim (class, tier, tools, inputs/outputs, claims, blockers)
- Required order, allowed tools, required outputs, forbidden shortcuts per tranche
Source: System tools and plan.md

### 25. Host Architecture Planes

Four planes: Topology, Orchestration, Dispatch, Event Spine.
Runtime kernel objects: RuntimeState, Probe, Transform, Witness, StepEvent.
NOT in clean docs.
Source: System tools and plan.md

### 26. Three-Phase Audit Framework

Phase A (pre-Axis machinery build), Phase B (packet tightening),
Phase C (runtime diagnostic). With ranked evidential value of specific
artifacts.
Source: preaxis sim run.md

### 27. Full Axis 0 Formalization (8 sections)

Shell/boundary bookkeeping, j/k fuzz as admissible future, Feynman-like
path form, entanglement tensor-network shell, ring checkerboard support,
entropy field and i-scalar family.
Source: Axis 0 rough and drifty. NOT CANON.md

### 28. Layer 0/1/2 Control Governance

System governs itself via:
- Layer 0: INVARIANTS
- Layer 1: ARCHITECTURE
- Layer 2: DIRECTION
Source: INTENT_SUMMARY copy.md

### 29. Three-Layer Entropy Architecture

Three separate entropy layers explicitly separated:
- Runtime engine entropy
- Torus entropy seat
- Bipartite Ax0 family
Source: Contraint on Admisibility, ENTROPY tables, Entropic Monism.md

### 30. Classical Residue Stripping Table

15+ aligned researchers with explicit mapping of useful structures
vs classical assumptions to strip from each.
Source: MODEL_CONTEXT copy.md

---

## Summary: Clean Docs vs V5 Docs

| Clean docs have | V5 docs have that clean docs DON'T |
|---|---|
| Philosophy (nominalism, FEP, anti-teleology) | Formal operator math (Kraus, Lindblad) |
| Process framing (surface, graveyard, boots) | 16/19/36-layer ladders with exact objects |
| Reference traditions (14 external docs) | Terrain equations in full form |
| Session corrections (18 corrections) | Admissibility fences (24 formal anti-assumptions) |
| Boot prompt templates | CS translation of entire system |
| Tradition-system mapping | Sim admission contracts |
| Falsification sim designs | Host architecture (4 planes, 5 kernel objects) |
| | Token partition tables for each axis |
| | Sign encoding closure law |
| | Anti-flattening rule |
| | Full Axis 0 formalization (8 sections) |
| | Three-layer entropy architecture |
| | Type 1/Type 2 pair lock tables |

The clean docs are ~30% of the system's actual content.
The v5 docs contain the other ~70% — the math, the structure,
the formal machinery that makes the philosophy testable.

---

## Next Steps

Integrating 30 missing items into 13 clean docs requires careful work.
Options:
1. Add new sections to existing clean docs (TIER_STATUS, THESIS, PROCESS)
2. Create new clean docs for the heaviest gaps (operators, placements, fences)
3. Do both incrementally, one gap at a time

The v5 docs should NOT be paraphrased. The math should be extracted
exactly as written and placed in the clean doc set with source attribution.
