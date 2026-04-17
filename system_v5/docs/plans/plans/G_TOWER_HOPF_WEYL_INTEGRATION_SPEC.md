# G-Tower / Hopf / Weyl Integration Spec

Date: 2026-04-14  
Status: candidate spec — math is proposed structure, not theorem-proved  
Depends on: sim results at `system_v4/probes/sim_gtower_*.py`, `sim_geom_noncomm_*.py`, `sim_assoc_bundle_*.py`, `sim_holonomy_*.py`

Language discipline: all claims are admissibility claims unless a z3 UNSAT or `passes local rerun` result is cited.

---

## 1. Core Claim

The G-tower reduction chain GL(n,C) → O(n) → SO(n) → U(n) → SU(n) → Sp(n) is a candidate nested-constraint-shell structure when the total space is the Hopf fibration S³ → S².

Each reduction step eliminates a family of structures that cannot coexist with the constraints introduced at the next level. Weyl spinors are candidate sections of the associated vector bundle on the surviving fiber.

This is a candidate claim grounded in existing shell-local probes. It is NOT a bridge claim (Coupling Program step 6). Bridge status requires completed steps 1–5.

**What exists in repo to support this:**
- Shell-local G-tower reduction probes: `sim_gtower_gl_to_o.py`, `sim_gtower_o_to_so.py`, `sim_gtower_so_to_u.py`, `sim_gtower_u_to_su.py`, `sim_gtower_su_to_sp.py`, `sim_gtower_full_chain.py`
- U(1)/Hopf fiber coupling: `sim_gtower_u1_hopf_fiber_reduction.py`, `sim_gtower_couple_so3_x_u1_fiber.py`
- Associated bundle construction: `sim_assoc_bundle_associated_vector_bundle_construction.py`, `sim_assoc_bundle_weyl_spinor_as_section.py`, `sim_assoc_bundle_canonical_connection_from_hopf.py`
- Holonomy classifiers: `sim_holonomy_group_classifies_gtower_shell.py`, `sim_holonomy_shell_classifier.py`
- Connes distance bridge: `sim_spectral_triple_connes_distance.py`, `sim_spectral_triple_reduction_connes_distance.py`

---

## 2. Key Equations

### 2a. Principal bundle reduction

A principal G-bundle π: P → M reduces to a principal H-bundle (H ⊂ G) iff there exists a global section of P/H → M.

At each G-tower step, the constraint is: does the reduced structure group H admit a consistent section on the base manifold? For S² (the Hopf base), this is controlled by π₁(S²) = 0 and the second Stiefel-Whitney class.

### 2b. Associated vector bundle for Weyl spinors

Given the principal SU(2)-bundle π: S³ → S² (the Hopf bundle), the associated vector bundle is:

    E = S³ ×_{SU(2)} V

where V = C² is the standard SU(2) representation. Weyl spinors are candidate sections ψ: S² → E satisfying the Weyl equation D̸ψ = 0, where D̸ is the Dirac operator restricted to left-handed components.

Chirality selection (Weyl vs Dirac) corresponds to the choice of left- vs right-handed Weyl representation — probed by `sim_assoc_bundle_weyl_spinor_as_section.py`.

### 2c. Curvature form

The curvature of the canonical connection on the Hopf bundle is proportional to the area form on S²:

    F = dA + A ∧ A = (i/2) sin(θ) dθ ∧ dφ

where A is the U(1) connection one-form. This is the first Chern form; its integral over S² yields the first Chern number c₁ = 1.

Probed by: `sim_assoc_bundle_canonical_connection_from_hopf.py`.

### 2d. Holonomy

For a loop γ in S² enclosing solid angle Ω, the holonomy of the canonical Hopf connection is:

    Hol(γ) = exp(i Ω / 2) ∈ U(1)

The holonomy group is U(1) for the Hopf bundle; promotion to SU(2) requires the double cover (spin structure). This is the structural mechanism linking the G-tower step SU(2) → SO(3) to fiber winding number observability.

Probed by: `sim_holonomy_group_classifies_gtower_shell.py`, `sim_hopf_deep_u1_holonomy_equivariance.py`.

### 2e. Connes distance bridge

The Connes distance on the spectral triple (A, H, D) is:

    d(φ₁, φ₂) = sup { |φ₁(a) − φ₂(a)| : a ∈ A, ‖[D, a]‖ ≤ 1 }

For the Dirac operator on S² restricted to the Hopf bundle, this recovers the geodesic distance on the base. The Weyl spinor restriction (half the degrees of freedom) modifies the operator norm bound and is a candidate distinguishability metric for shell boundaries.

Probed (shell-local, not yet bridge-connected) by: `sim_spectral_triple_connes_distance.py`.

---

## 3. Non-Commutativity Ratchet

The owner doctrine states: a geometry stack is a real ratchet ONLY IF A∘B ≠ B∘A on the structure.

**Session evidence (2026-04-14 and prior):**

- 10/10 non-commutative pairs confirmed across `sim_geom_noncomm_*.py` probes
- 5/6 rigid G-tower reductions confirmed in `sim_gtower_order_*.py` probes; the sixth is the G₂ exceptional case (`sim_gtower_exceptional_g2_admissibility_probe.py`)
- Specific Hopf ↔ Weyl non-commutativity: `sim_geom_noncomm_weyl_then_hopf_vs_hopf_then_weyl.py` and `sim_geom_noncomm_hopf_fiber_then_weyl_projector.py` show ordering matters
- z3 UNSAT on reversed order: `sim_gtower_z3_unsat_nonreductive_chain.py` and `sim_gtower_order_z3_unsat_invalid_reduction_order.py` confirm that reversed G-tower application is structurally inadmissible

**Why it constitutes a ratchet candidate:**

Applying Weyl-projection before Hopf-fiber-reduction eliminates structures that survive the opposite order. z3 UNSAT on reversed chains means the constraint set is inconsistent under reordering — this is the structural signature of a ratchet: direction-of-application encodes information that cannot be recovered by reversal.

This remains a candidate claim; coupling across shells (step 2 of the Coupling Program) is required before treating this as a confirmed multi-shell ratchet.

---

## 4. Proposed Next Micro-Sims (not yet in repo as of 2026-04-14)

All three are absent from `system_v4/probes/` (verified by glob this session).

### 4a. `sim_g_tower_hopf_canonical_connection_deep.py`

**Goal**: verify that the canonical connection on the Hopf bundle (section 2c above) survives the full G-tower reduction chain GL→O→SO→U→SU. Specifically: does the curvature form remain consistent (non-zero, correct Chern number) after each reduction step, or is it excluded at some step?

**Tools to involve**: sympy (curvature form computation), clifford (rotor parallel transport), z3 (UNSAT guard on inconsistent Chern numbers), geomstats (S² geodesic cross-check)

**Test design**: positive = Chern number c₁ = 1 after SU(2) reduction; negative = reversed order yields inconsistent curvature; boundary = partial reduction stops at SO(n) — does holonomy degrade?

### 4b. `sim_weyl_chirality_g_reduction_noncomm.py`

**Goal**: probe whether applying the Weyl chirality projector (L vs R) before vs after the SU(2)→SO(3) G-tower step produces distinguishably different surviving state families.

**Tools to involve**: clifford (Weyl projectors via Cl(3,1) or Cl(1,3) grade decomposition), e3nn (SO(3) irrep decomposition of surviving states), z3 (UNSAT guard: L before SO(3) ≠ SO(3) before L)

**Test design**: positive = non-commutativity confirmed (surviving families differ); negative = z3 UNSAT on the claim that both orderings admit identical state sets; boundary = check whether single-qubit degenerate case collapses the non-commutativity

### 4c. `sim_holonomy_connes_bridge.py`

**Goal**: test whether the U(1) holonomy of the Hopf bundle (section 2d) and the Connes distance on the associated spectral triple (section 2e) co-vary under the same family of loops on S². If both assign the same ordering to a family of loops, they are candidates for the same underlying invariant under different notations (Rosetta candidate — see section 5).

**Tools to involve**: geomstats (geodesic loops on S²), sympy (holonomy integral closed form), clifford (Dirac operator restriction), z3 (consistency guard: holonomy and Connes distance rankings agree on all test pairs)

**Test design**: positive = holonomy rank and Connes-distance rank agree for ≥5 loop families; negative = z3 UNSAT on claim that they can disagree on any admissible loop; boundary = degenerate loop (Ω → 0) collapses holonomy to identity

---

## 5. Rosetta Predictions

Three candidate Rosetta correspondences — pairs of tool families that should agree on the same invariant under different computational notations. These are predictions to be tested, not claims.

### Rosetta R1: Holonomy (geomstats) ↔ Curvature integral (sympy) ↔ Chern number (z3 guard)

- geomstats computes parallel transport and holonomy angle for loops on S²
- sympy integrates the curvature form over enclosed regions
- z3 guards that the Chern number (integer invariant) is consistent with both

Predicted agreement: all three should produce the same winding number for any contractible vs non-contractible loop distinction on the Hopf base.

### Rosetta R2: Weyl chirality projector (clifford) ↔ Parity eigenvalue (e3nn) ↔ Left/right exclusion (z3 UNSAT)

- clifford decomposes a spinor into Weyl grades
- e3nn decomposes SO(3) representations into parity-labelled irreps
- z3 guards that a state cannot simultaneously be in both left and right Weyl eigenspaces

Predicted agreement: the grade decomposition in clifford and the parity decomposition in e3nn should agree on which states are excluded after chirality projection.

### Rosetta R3: Connes distance (spectral triple) ↔ Geodesic distance (geomstats) ↔ Trace distance (sympy/numpy)

- spectral triple Connes distance on the Hopf fiber base
- geomstats geodesic distance on S²
- trace distance as the operational distinguishability metric

Predicted agreement: for states on the Bloch sphere embedded in S², all three distances should agree on state-pair orderings, up to a positive monotone rescaling. Disagreement would indicate a shell boundary (different quantities survive different constraint layers).

---

## 6. Open Questions (patient convergence required)

These are named gaps. Do not claim convergence on any of them until probes at Coupling Program steps 2–5 exist.

**Q1: Does the Hopf bundle support a consistent spin structure under all G-tower reductions?**
Current evidence: shell-local probes confirm individual reductions; no multi-step probe yet tests whether the spin structure survives the full GL→Sp chain simultaneously. Relevant but absent: `sim_g_tower_hopf_canonical_connection_deep.py` (section 4a above).

**Q2: Is the Weyl chirality non-commutativity (section 3) a property of the fiber alone, or does it require the full bundle structure?**
Current evidence: non-commutativity is confirmed at the state-probe level (`sim_geom_noncomm_weyl_then_hopf_vs_hopf_then_weyl.py`). It is unknown whether removing the S² base and working on the fiber S³ alone preserves the non-commutativity signature. This is a topology-variant rerun (Coupling Program step 4) that has not been attempted.

**Q3: Does the Connes distance on the Hopf spectral triple actually recover geodesic distance on S², or does the Weyl restriction modify the bound?**
Current evidence: `sim_spectral_triple_connes_distance.py` and `sim_spectral_triple_reduction_connes_distance.py` exist but their results have not been cross-checked against geomstats geodesic computations this session. Rosetta R3 (section 5) is a prediction, not a confirmed agreement.

**Q4: Where does the G₂ exceptional case fit?**
`sim_gtower_exceptional_g2_admissibility_probe.py` exists. G₂ is the one G-tower candidate without a confirmed rigid reduction (5/6 confirmed). It is unclear whether G₂ is excluded from the nested-shell interpretation or merely requires a different probe family. This is an open candidate, not a closed one.

**Q5: Do pairwise coupling sims between Hopf-layer and Weyl-layer (Coupling Program step 2) change the non-commutativity evidence?**
All current non-commutativity evidence comes from shell-local or single-step probes. No pairwise coupling sim yet activates both the Hopf fibration shell and the Weyl spinor shell simultaneously and tests whether their combined constraint set produces ordering-dependent exclusions different from either alone.
