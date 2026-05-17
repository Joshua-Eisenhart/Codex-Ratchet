# Constraint Manifold Component Map

Binding contract for the grok_sim sidequest. Per user standard:
1. Stop treating primitive sims as manifold progress.
2. Read manifold docs and existing formal sims (done).
3. **Build a component map: required manifold object → existing formal lego(s) → missing assembly code** (this file).
4. Only then let Grok/Gemini propose wiring.
5. Codex audits against THIS component map, not against generic "passes tests."

Scope: informal-scout only. Sidequest writes proposals; **NO writes to `system_v4/probes/`**.
Existing legos are READ-ONLY references — they are evidence, not files to modify.

Status vocabulary: SURVIVED / KILLED / OPEN / NOT_YET_TESTED.

---

## 1. Carrier

**Required object:** S³ as normalized spinor carrier (ψ ∈ ℂ², ‖ψ‖ = 1) with explicit Hopf coordinates ψ_s(φ, χ; η).

**Existing legos:**
- `system_v4/probes/sim_hopf_fibration_embedding_classical.py` — real embedding (a,b,c,d) ∈ S³ → S², callable `hopf(x)` + `rand_S3(n)`. classical_baseline.
- `system_v4/probes/sim_hopf_fibration_constraint_canonical.py` — canonical Hopf-fibration constraint.

**Missing assembly:** None at the carrier level — S³ + Hopf coords are in `sim_hopf_fibration_embedding_classical.py`. Sidequest proposal must REFERENCE these by name and import-of-record only; do not re-encode.

---

## 2. Hopf projection π: S³ → S² (principal U(1)-bundle)

**Required object:** the Hopf projection, phase-invariant under U(1) fiber rotation.

**Existing legos:**
- `system_v4/probes/sim_hopf_projection_s3_s2_phase_invariant_survivor_classes.py` — verifies global phase leaves S² projection fixed; load-bearing torch + z3.

**Missing assembly:** None. Reference by path.

---

## 3. Canonical U(1) connection A on the Hopf bundle

**Required object:** A = dφ + cos(2η) dχ (or equivalent global-section form A = Im(z̄₀ dz₀ + z̄₁ dz₁)), with horizontal-lift property `A(γ̇_base) = 0`.

**Existing legos:**
- `system_v4/probes/sim_hopf_connection_one_form_loop_integral_survivor_classes.py` — connection one-form, loop integral, orientation-aware. Numeric + sympy paths. load-bearing torch + sympy + z3.
- `system_v4/probes/sim_hopf_connection_u1_curvature_base_form_survivor_classes.py` — curvature base form F.

**Missing assembly:** None at the connection level. Reference both files.

---

## 4. Curvature form F and first Chern number c₁

**Required object:** F = dA + A∧A = (i/2) sin θ dθ∧dφ; ∫_{S²} F / 2π = c₁ = 1.

**Existing legos:**
- `system_v4/probes/sim_chern_weil_torch_foundation.py` — Chern forms c₁, c₂ from curvature; integrality via z3 UNSAT. callable `chern_form_c1(F)`, `chern_form_c2(F)`. load-bearing torch + z3 + sympy.
- `system_v4/probes/sim_hopf_connection_u1_curvature_base_form_survivor_classes.py` — curvature base form on Hopf base.

**Missing assembly:** A sidequest harness that calls `chern_form_c1` on the curvature returned by the Hopf connection one-form lego, asserts `c₁ = 1` numerically. Single integration step.

---

## 5. Holonomy Hol(γ) = exp(iΩ/2) ∈ U(1)

**Required object:** path-ordered phase along closed loops on S²; loop enclosing solid angle Ω returns `exp(iΩ/2)`.

**Existing legos:**
- `system_v4/probes/sim_holonomy_torch_foundation.py` — U(1) holonomy via parallel-transport ODE; `connection_along_loop(loop_param, winding_number)`; torch autograd accumulation. load-bearing torch + z3 + sympy.
- `system_v4/probes/sim_density_matrix_parallel_transport_holonomy_survivor_classes.py` — parallel-transport survivor classes on density matrices.
- `system_v4/probes/sim_holonomy_group_classifies_gtower_shell.py` — holonomy-group classification of G-tower shell.

**Missing assembly:** Sidequest harness that feeds the Hopf connection (item 3) into `holonomy_torch_foundation`, verifies `exp(iΩ/2)` for ≥3 concrete loops with known Ω. Cross-checks `chern_form_c1` integral against Gauss-Bonnet.

---

## 6. Principal-bundle reduction chain GL(n,ℂ) → O → SO → U → SU → Sp

**Required object:** 6-step reduction with admissibility witness at each step; z3 UNSAT on reversed order.

**Existing legos:**
- `system_v4/probes/sim_gtower_reduction_chain_composition.py` — tier-stepping framework; callable `tier_trace(M)` returns boolean dict per tier. sympy + numpy. canonical.
- `system_v4/probes/sim_gtower_full_chain.py` — full chain reduction + z3 UNSAT (det=−1 obstruction; Sp preservation impossible). callable `classify_complex(M)`. load-bearing z3 + sympy.
- `system_v4/probes/sim_gtower_order_full_chain_unique_path_admissibility.py` — unique-path admissibility under fixed order.
- `system_v4/probes/sim_geom_noncomm_z3_unsat_order_swap.py` — z3 UNSAT proof: A∘B admissible ⇒ B∘A excluded.

**Missing assembly:** Sidequest harness that classifies a sequence of test matrices through `tier_trace` AND `classify_complex` to confirm agreement, then runs `sim_geom_noncomm_z3_unsat_order_swap` to confirm non-commutativity z3 UNSAT.

**OPEN:** G₂ exceptional case (`sim_gtower_exceptional_g2_admissibility_probe.py`) — 5/6 reductions rigid, G₂ unresolved. Per doc Q4. Manifold proposal must mark this OPEN, not fake closure.

---

## 7. Associated vector bundle E = S³ ×_{SU(2)} ℂ² with Weyl-spinor sections

**Required object:** E with ψ_L, ψ_R as sections (left/right Weyl); chirality projectors P_L = (I − γ₅)/2, P_R = (I + γ₅)/2; H_L = +H₀, H_R = −H₀.

**Existing legos:**
- `system_v4/probes/sim_assoc_bundle_weyl_spinor_as_section.py` — ψ as section of E = S³ ×_{U(1)} ℂ_{1/2}; SU(2) equivariance via Pauli algebra; `su2(axis, angle)`, `spinor_to_s2(psi)`. clifford + numpy. canonical.

**Missing assembly:** Sidequest harness that builds (ψ_L, ψ_R) on top of the Hopf carrier (item 1), verifies `spinor_to_s2(psi)` agrees with the standalone `hopf` projection, exhibits `H_L = +H₀, H_R = −H₀` with opposite Bloch circulation `ṙ_L = 2 n × r_L`, `ṙ_R = −2 n × r_R`.

---

## 8. Connes distance on the spectral triple (A, H, D)

**Required object:** d(φ₁, φ₂) = sup { |φ₁(a) − φ₂(a)| : a ∈ A, ‖[D, a]‖ ≤ 1 }; should recover geodesic distance on S² for the Hopf base (per doc Q3, NOT yet confirmed).

**Existing legos:**
- `system_v4/probes/sim_spectral_triple_connes_distance.py` — exact via LP reduction; `connes_distance_points(N, j, k)`; load-bearing z3 + sympy.

**Missing assembly:** Sidequest harness that calls `connes_distance_points` and a separate geomstats-style geodesic computation on matched S² points; reports whether they agree at the ranking level or only up to monotone rescaling. **Q3 is OPEN per doc — proposal MUST report this honestly, not claim recovery.**

---

## 9. Outer/inner split (Axis 3 — carrier not canonical)

**Required object:** outer versus inner distinction. Do not canonize the
carrier. Weyl spinor, Hopf fiber/base loop geometry, and chirality/flux are
candidate substrates/readouts/controls only, not the Axis-3 definition.

**Existing legos:** Implicit in the Hopf-connection legos (item 3) — Y_in, Y_out vector fields satisfy the property by construction. No standalone Ax3 lego.

**Missing assembly:** Sidequest harness exploring outer/inner on candidate
carriers and reporting which carriers survive. **Claim ceiling MUST state Axis
3's carrier stays OPEN**: a harness may show that one candidate carrier is
consistent, not that the carrier is canonical.

---

## 10. Three-layer entropy split (per AXIS_AND_ENTROPY_REFERENCE §Three-Layer Entropy Architecture)

**Required object:**
- runtime: S(ρ_L), S(ρ_R)
- torus seat: S(η) over `bar rho(eta) = diag(cos²η, sin²η)`
- bipartite Ax0 family: S(A|B), I(A:B), I_c(A⟩B) — signed; conditional and coherent info can be negative.

**Existing legos to scan:** `sim_lego_coherent_info_advanced.py`, `sim_coherent_info_erasure_canonical.py`, `sim_lego_entropy_bipartite_cut.py`, `sim_global_shell_cut_coherent_info.py` (under `system_v4/probes/`). Read-only.

**Missing assembly:** Sidequest harness that computes all three layers on a state produced by the items 1+3+7 pipeline; explicitly tests signed I_c and S(A|B) negativity on an entangled (A, B). Bridge Ξ is OPEN per doc — claim ceiling must say so.

---

## What the sidequest proposal IS, then

A single sidequest proposal file (`system_v5/grok_sim/loop_runner/proposed_formal_sims/sim_proposed_constraint_manifold_assembly.py`) that:

- Documents each required object → existing lego mapping above as in-file claim, with paths.
- Implements ONLY the missing assembly code (items 4, 5, 6, 7, 8, 9, 10 — the cross-call harness). No re-encoding of carrier, projection, connection, curvature, Chern form, reduction chain, Connes distance, or spinor lift.
- Marks Ax3, Q3 (Connes ↔ geodesic), Q4 (G₂), Bridge Ξ, Axis 0 cut as OPEN in the claim ceiling.
- Returns one assembled dict + an `is_constraint_satisfied(state)` verifier that composes the legos' individual checks.
- Carries the nominalist schema (X, C, M, ~_M, survivors, graveyard, claim ceiling).
- Uses ZERO contaminated identifiers (no axis/Ax0..6/engine/gstack/terrain/Type 1/2/prime_resonance/Carnot/Szilard).

## What Codex audits against (per user step 5)

Not "passes tests." It audits against THIS map: does the proposal reference each required object via the named lego path? Does it leave the OPEN items honestly open? Does it avoid re-implementing what the formal corpus already has?

## What Grok/Gemini are NOT asked

To re-implement Hopf, gtower, Weyl-as-section, Chern, holonomy, Connes distance. Those are READ-ONLY legos. Grok/Gemini propose the assembly wiring only.

---

## Round-2 binding (post round-1 Codex audit, 2026-05-13)

Round 1 of step 4 (Grok+Gemini propose wiring) was REJECTED by Codex against
this map. Per-object reason: **both proposals hardcoded the values that the
legos compute.** Specifically:

- Curvature + Chern: hardcoded `c1 = 1.0` instead of computing it.
- Holonomy: hardcoded `hol = exp(iΩ/2)` instead of running the parallel-
  transport ODE in `sim_holonomy_torch_foundation.py`.
- Reduction chain: hardcoded `z3_unsat_on_reversed = True` instead of
  calling `classify_complex` in `sim_gtower_full_chain.py` and running the
  z3 UNSAT proof in `sim_geom_noncomm_z3_unsat_order_swap.py`.
- Weyl spinor: hardcoded chirality / circulation claims instead of wiring
  through `sim_assoc_bundle_weyl_spinor_as_section.py`.
- Connes: hardcoded `d_value` as a fallback constant instead of calling
  `connes_distance_points` in `sim_spectral_triple_connes_distance.py`.
- Loop split Ax3: hardcoded density deltas for γ_f / γ_b.
- Three-layer entropy: hardcoded entropy values instead of computing them.

Round-2 binding constraints (REJECT any proposal violating any):

1. **NO HARDCODED VALUES.** Every numeric output (`c1`, `hol_value`,
   `z3_unsat_on_reversed`, `d_value`, density deltas, entropies) must come
   from an actual call to the named lego's exported callable. Reading the
   lego file, identifying the callable, and invoking it is the assembly
   work this proposal is for.

2. **HOW TO INVOKE A LEGO.** The lego files live at
   `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/<name>.py`.
   Load them via `importlib.util.spec_from_file_location` (not regular
   `import` — they are outside the package). Identify exported callables
   by reading the file; call them on a small concrete input; capture and
   report the actual return value.

3. **FALLBACK BEHAVIOR ON UNAVAILABLE LEGO.** If a lego file is missing
   or its callable raises, the matching field must return
   `{"status": "NOT_YET_TESTED", "lego_load_error": "<msg>"}`. Do NOT
   substitute a hardcoded constant. A missing lego is graveyard evidence,
   not a fake survivor.

4. **THE `evidence` FIELD IS THE COMPUTED VALUE, NOT A QUOTED STRING.**
   `evidence` is whatever the lego returned. Print it. Do not write
   `"evidence": "lego computes c_1 = 1"` — write `"evidence": <number>`.

5. **EVERY REQUIRED PATH FROM THE MAP MUST BE LISTED — for the ASSEMBLY
   FILE only.** The 15 lego paths named in items 1–10 above are the full
   coverage for `sim_proposed_constraint_manifold_assembly_handbuilt.py`
   (or any future replacement that claims to BE the manifold assembly).
   Downstream scout probes that CONSUME a subset of the assembled manifold
   (e.g. a prime-resonance probe that only uses holonomy + Hopf
   projection) are not bound by this path-coverage rule — they are
   bound only by:
     (a) using ONLY legos that appear in this map (no smuggling new
         dependencies)
     (b) preserving the OPEN items (Ax3, Q3, Q4, Bridge Ξ, Axis-0 cut)
     (c) the doctrine constraints elsewhere in the map.
   The path-coverage rule prevents the assembly file from claiming
   "I am the manifold" while only invoking part of it. It does not
   force every downstream probe to invoke the whole manifold.

6. **THE `is_constraint_satisfied` CALLABLE COMPOSES THE LEGOS' OWN
   CHECKS, NOT YOUR OWN ASSERTIONS.** Load each lego; find its
   `is_*_satisfied` / `run_positive` / verification callable; call them;
   AND together. No author-written checks.

7. **MARK FAILURE-TO-INVOKE AS KILLED, NOT SURVIVED.** If a lego throws,
   the assembly entry for that object is KILLED with a captured trace.
   That is honest mapping; faking SURVIVED with a hardcoded value is the
   audited failure mode.

The component map is unchanged. Round-2 binding tightens HOW the wiring
must invoke the named legos.
