# Geometric Constraint Manifold — Full Nested Layer Tower, G-Structure Exploration, Integration Gap

Date: 2026-05-15
Status: noncanonical context doc for next-thread re-entry. Pair with Codex's master handoff and the thread-arc handoff.
Paired files:
- `system_v5/docs/GEOMETRIC_CONSTRAINT_MANIFOLD_FULL_THREAD_HANDOFF_20260515.md` (Codex master)
- `system_v5/docs/CLAUDE_THREAD_HANDOFF_FLUX_TERRAIN_AXIS_OPERATOR_DISCIPLINE_20260515.md` (Claude thread arc + Weyl-lane work)

**READING NOTE — structure of this document:**
The main body (Sections A through K) uses only pure-math language: topological terms, algebraic structures, Lie groups, bundles, holonomy, Clifford algebras, eigenvalue partitions, homotopy classes, spinors, chirality sheets, projectors, density operators, entropy, Schmidt spectra. No interpretive labels appear here.

All interpretive names — chirality-sheet nicknames, cycle-class mnemonics, flux-channel labels, operator-family shorthand referencing functional-type systems, and any other operational mnemonic that names an underlying math object via a non-mathematical system — are collected in the **Appendix: Interpretive Overlays** at the end of this document.

Moving terms to the appendix removes no math content. Every math object named there has its definition in the main body.

---

## Why this exists

Owner: *"do we have full running sims of this integrated together? all the legos running as one. this is not something simple to run. it is full rich simulation. and needs all the tools running. and this isn't rungs. this is nested layers. and running a dynamic system. like a real tensor network. don't skip out on stuff."*

Both Codex and Claude had collapsed the geometric constraint manifold into the left/right Weyl operating-space layer. **That is wrong.** The Weyl/chirality layer is one operating layer inside a 13-layer nested tower of simultaneous constraint surfaces, not the manifold itself. The owner-source manifold is much bigger, includes G-structure exploration, and is meant to be run as a coupled dynamic tensor-network simulation across all legos with all tools simultaneously.

This doc preserves: (A) the nested 13-layer tower from the actual scout code, (B) the G-structure scaffold currently in use plus alternatives explored, (C) a survey of existing integration sims, (D) the gap — no receipt yet says "all legos integrated as one nested dynamic tensor-network system," (E) the explicit corrections to prior collapse.

---

## A — The nested 13-layer constraint tower

**Layers are simultaneous constraint shells on the same state space, NOT sequential rungs.** Source: `system_v5/ops/formal_scouts/sim_nested_geometry_tower_dependency_order_probe.py:56-70`.

```
1.  finite_constraint_complex
2.  complex_hilbert_carrier
3.  unit_spinor_sphere
4.  projective_base_sphere
5.  hopf_fiber_bundle
6.  hopf_torus_leaf_family
7.  connection_holonomy_geometry
8.  weyl_spinor_bundle              ← left/right Weyl chirality lives here
9.  chirality_orientation_cover     ← γ_5 / Cl orientation cover here
10. clifford_module_geometry
11. frame_bundle_structure_reduction
12. tensor_product_coupling_geometry
13. dynamic_transition_ratchet_geometry
```

**The exact final order is open.** Per `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md:224`, "each layer has to be tested independently, then tested for admissible stacking/nesting." The dependency-order scout instantiates concrete witnesses at each layer and tests with z3 that mutual-dependency cycles are UNSAT. Open choices recorded in the scout itself: "frame bundle structure reduction may need to move earlier before spinor bundle construction"; "dynamic transition geometry needs richer deformation families beyond adjacent dependency edges."

**The Weyl/chirality-orientation layers live at layers 8 + 9 + possibly bleeding into 10 (Clifford module).** The source-alignment incident concerned one layer being a missing source object beneath the downstream readouts. Fixing layers 8-9 does NOT mean the whole 13-layer tower is integrated.

**Owner directive (verbatim):** *"this isn't rungs. this is nested layers. and running a dynamic system. like a real tensor network."*

---

## B — G-structure exploration

### Current working scaffold (NOT final ontology)

From `system_v5/ops/formal_scouts/sim_finite_density_hopf_spinor_clifford_channel_structure_reduction_order_probe.py:120`:

```
GL(2,C)_real    dim 8
  → O(4)_real    dim 6
  → SO(4)_real   dim 6
  → Spin(4)      dim 6
  → U(2)_real    dim 4
  → SU(2)_real   dim 3
```

The scout explicitly disclaims this as a **support/frame-bundle structure-reduction scaffold**, not final ontology. Open choice recorded: *"support-structure reduction chain is a scaffold lane, not final ontology."*

The corresponding nested constraint composition tested in that scout:

```
finite density carrier
  → support/frame reduction
  → Hopf U(1) bundle / holonomy
  → SU(2)/Spin spinor geometry
  → Weyl chirality orientation cover
  → Clifford module
  → tensor / dynamic transition constraints
```

### Alternative G-structures explored (special-holonomy form constraints)

From `system_v5/ops/formal_scouts/sim_special_holonomy_form_constraint_survivor_quotient_probe.py:99-125`:

| Family | Dim | Form constraints | Survivor / control |
|---|---|---|---|
| SU(3)-like | 6 | Kähler 2-form + complex 3-form (volume) | finite signed-permutation survivors |
| G2-like | 7 | Stable 3-form (octonion-derived) | distinct from generic 3-form control under z3 |
| Spin(7)-like | 8 | Cayley 4-form | distinct from generic 4-form control under z3 |
| generic 3-form control | 7 | all-triples-with-coefficient-1 | baseline |
| generic 4-form control | 8 | all-quadruples-with-coefficient-1 | baseline |

The scout computes finite survivor sets, probe-quotient classes, and persistence over the survivor graphs. z3 confirms G2 ≠ generic-3-form-control and Spin7 ≠ generic-4-form-control. Currently tests only **diagonal sign symmetries**, not continuous holonomy groups. Open choices recorded: "next pass should add permutation symmetries and frame rotations, then compare survivor quotients"; "Gauge-theory-like constraints are not included yet."

### Wider mining-only candidates (not yet v5 formal scouts)

Mentioned in handoff as exploratory: associated bundles, Hitchin fibrations, Higgs bundles, nonabelian Hodge, gerbes, spectral triples, parabolic / stable / harmonic bundles, opers, Floer complexes, derived stacks, twistor lines, arithmetic curves, local systems. None translated into v5 formal-scout receipts yet.

---

## C — Existing integration sims (subset coverage, not all-legos-as-one)

Multiple coupled multi-tool dynamic scouts exist. Each covers a **subset** of the 13 layers and a **subset** of the load-bearing tool stack.

### Rich coupled scouts surveyed this thread

| Scout | Layers covered | Tools (load-bearing) | Dynamic? |
|---|---|---|---|
| `sim_nested_geometry_tower_dependency_order_probe` | 1-13 (witnesses per layer) | pytorch, opt_einsum, geomstats, clifford, rustworkx, torch_geometric, gudhi, toponetx, xgi, z3 | NO — tests dependency-order admissibility, not dynamic evolution across layers |
| `sim_finite_density_hopf_spinor_clifford_channel_structure_reduction_order_probe` | 2, 5, 7, 8, 9, 10 + channel | pytorch, geomstats, clifford, sympy, z3 | partial — single state through ordered chain, not dynamic feedback |
| `sim_special_holonomy_form_constraint_survivor_quotient_probe` | 11-12 (form constraints over frame bundle) | sympy, pytorch, z3, networkx, torch_geometric, gudhi, rustworkx | NO — finite survivor enumeration over sign symmetries |
| `sim_eight_qubit_dynamic_shell_graph_tensor_network_entropy_coupling_probe` | 1, 6 + 12 + 13 (8-qubit dynamic shell graph as Hamiltonian generator, tensor cuts, persistence) | pytorch, opt_einsum, networkx, torch_geometric, gudhi, sympy, z3 | **YES** — 5 dynamic steps, evolves under graph-weighted Hamiltonian, reads all 7 cuts |
| `sim_eight_qubit_mps_channel_order_graph_leakage_pyg_pytorch_opt_einsum_z3_probe` | MPS channel-order on 8-qubit chain | pytorch, opt_einsum, pyg, z3 | partial |
| `sim_eight_qubit_dynamic_shell_chirality_asymmetric_cptp_entropy_coupling_probe` | dynamic shell + chirality-asymmetric CPTP | many | YES — combines layers 6 + 8 + 9 + CPTP |
| `sim_pauli_correlated_topology_flux_operator_channel_tensor_network_probe` | flux + topology + operator + tensor network | many | YES — flux-correlated tensor network |
| `sim_variable_qubit_topology_flux_channel_order_entropy_scaling_probe` | variable-qubit topology + flux scaling | many | YES — scales N |
| `sim_left_right_weyl_density_terrain_loop_placement_mirror_non_equivalence_probe` | 8 + 9 (source-native repair scout) | numpy, scipy, sympy, z3 | partial — 16 placements, 9 samples per loop, but only the Weyl operating-space layer |
| `sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe` | 8 + 9 + stage layer (64 microsteps) | NAMED NEXT BUILD; status: handoff says it's the next correct scout | — |
| `sim_pytorch_neural_network_dynamic_geometry_coherent_information_regression_probe` | dynamic geometry + NN regression on coherent information | pytorch | YES — NN over dynamic geometry |
| `sim_dynamic_shell_rate_sequence_parameter_compression_probe` | dynamic shell with rate-sequence compression | many | YES |

### Tools the integrated sim should run

Full load-bearing tool stack across the scout estate (compiled from manifests above and Codex's handoff `:258-269`):

```
pytorch          — finite states, differentiable dynamics, metrics, Hamiltonians, matrix exp
opt_einsum       — partial traces, tensor contractions, reduced-density matrices
sympy            — exact/symbolic boundary checks, Pauli commutators, mirror identities
z3               — finite UNSAT / SAT controls, non-collapse witnesses, ordering proofs
clifford         — Cl(1,3) γ_5, Cl(3) pseudoscalar, spinor/chirality algebra
rustworkx        — graph dynamics, dependency graphs, transition graphs
networkx         — survivor-quotient graphs, shell graphs
torch_geometric  — message passing on tower features, graph-to-tensor conversion
gudhi            — persistence over filtrations / shell graphs / survivor quotients
toponetx         — simplicial complexes over adjacent tower triples
xgi              — hyperedges for coupled geometry layers
geomstats        — Riemannian S² / S³ membership, projective-base distance
qutip            — channel/density cross-checks (when load-bearing)
numpy / scipy    — numerical baseline (used in repair scout)
```

---

## D — The integration gap

**No formal scout in `system_v5/ops/formal_scouts/` has a receipt claiming "all 13 manifold layers + G-structure reduction + flux + chirality + Weyl + all load-bearing tools coupled in a single dynamic tensor-network simulation."**

Codex's exploration (paste in this thread): *"So far the evidence says we have several rich coupled scouts, including eight-qubit dynamic shell / tensor-network scouts, but I do not yet see a receipt that honestly says 'all manifold legos integrated as one nested dynamic system.'"*

Concrete gap profile:

- **Layer-coverage gap.** No scout instantiates all 13 layers as simultaneously-active constraint surfaces during one dynamic evolution. The dependency-order scout instantiates witnesses at each layer but does not run dynamics across them. The 8-qubit dynamic shell scouts run real dynamics but only at the carrier + shell-graph + tensor-coupling layers.
- **Tool-coverage gap.** No scout's TOOL_MANIFEST simultaneously lists pytorch + opt_einsum + sympy + z3 + clifford + rustworkx + networkx + torch_geometric + gudhi + toponetx + xgi + geomstats as load-bearing in one execution. The dependency-order scout is closest (10 of 13), but is not dynamic.
- **G-structure gap.** The reduction chain scout is single-state ordered chain, not a manifold built with the reduced structure group as the load-bearing constraint surface during dynamic tensor-network evolution.
- **Special-holonomy gap.** Form-preservation scouts (SU3 / G2 / Spin7) test finite sign-survivor classes only, not continuous holonomy groups over a running dynamic system.
- **Cross-layer coupling gap.** Each existing scout couples 2-4 layers. The owner's frame is "running a dynamic system like a real tensor network" — implying all coupled simultaneously.

This is **the** open work. The named next scout `sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py` extends layers 8-9; it does NOT close this gap.

---

## E — Corrections to prior collapse (Claude + Codex)

Both Claude and Codex made the same error this thread: collapsing the manifold to the Weyl operating-space layer.

- **Claude's first manifold layout** cited `M(C)` + `S³ → S² Hopf ladder` + sheets `ψ_L / ψ_R` + fiber/base-lift loops + 5-DoF independence. That captured **layers 1, 3, 4, 5, 6, 7, 8, 9 partially** — missed 2, 10, 11, 12, 13 entirely, and never named the G-structure scaffold or the special-holonomy alternatives.
- **Codex's first manifold layout** collapsed the same way: presented the Weyl operating-space + loop + substage pipeline as if it were the manifold. Owner caught it: *"what? this is NOT what the sims show! you have lost the constraint manifold. and its layers."*
- **Codex's corrected reading** (after re-reading the sims): the 13-layer tower + G-structure exploration + clarification that layers are constraint surfaces not sequential rungs. This doc reflects that corrected reading.

**Established directive (binding for next thread):** when laying out the manifold, the layer set is the 13-layer tower from `sim_nested_geometry_tower_dependency_order_probe.py:56-70`. The Weyl operating-space layer is one operating layer inside it, not a substitute.

---

## F — Re-entry checklist for next-thread manifold work

1. **Do not collapse the manifold to the Weyl layer.** Always start with the 13-layer tower.
2. Layers are **simultaneous constraint shells**, not sequential rungs. "Nested" not "stacked."
3. The Weyl operating-space repair scout (Codex's named next build) closes layers 8-9. **It does NOT close the integration gap.**
4. The G-structure scaffold is `GL(2,C)_real → O(4) → SO(4) → Spin(4) → U(2) → SU(2)` and is **scaffold-only, not final ontology**. Alternatives explored: SU3-like, G2-like, Spin7-like, with finite survivor-class evidence.
5. Wider G-structure mining list (associated bundles, Hitchin fibrations, Higgs bundles, nonabelian Hodge, gerbes, spectral triples, etc.) has not been translated to v5 formal scouts.
6. The integration question is OPEN. No receipt says "all legos integrated as one nested dynamic tensor-network system" yet. The named next scout does not close this; it extends layers 8-9.
7. To attempt the all-legos integration, the design must specify: which subset of the 13 layers run simultaneously, which tools are load-bearing in the coupled evolution, what the read-out is, what would falsify it as "still subset coverage," and what graveyards must trip.
8. **Owner directive: use max Grok and Gemini for this.** Provider audits are proposal/audit support, never canonical evidence.

---

## G — Companion provider audit

Per owner directive, Grok-4.3 + Gemini-3.1-pro-preview are being run at max settings on the integration gap question via `system_v5/ops/formal_scouts/run_claude_manifold_integration_gap_provider_audit.py`. Receipts will land at:

```
system_v5/ops/formal_scouts/provider_receipts/<timestamp>_grok_xai_claude_manifold_integration_gap_audit.json
system_v5/ops/formal_scouts/provider_receipts/<timestamp>_gemini_claude_manifold_integration_gap_audit.json
```

The prompt asks both providers:
1. Confirm or correct the 13-layer enumeration against the source scout file
2. Identify any other formal scouts that could already be interpreted as partial all-legos integration that this audit missed
3. Propose the minimal next-scout spec to close the integration gap (literal filename, layer set, tool stack, dynamics specification, positive predicates, graveyards, kill condition)
4. Identify the strongest falsifier for any proposed integration scout
5. Flag any other drift in the existing scout estate that this thread's source-alignment work has not yet caught

---

## H — Integration sims surveyed — corrected (replaces Section C survey; 2026-05-15)

Section C above catalogued the integration scouts known at initial thread-arc capture. The Gemini provider audit at `system_v5/ops/formal_scouts/provider_receipts/20260515T084118Z_gemini_claude_manifold_integration_gap_audit.json` identified **four additional partial integration scouts** that Section C missed. Both Grok and Gemini independently confirmed the integration gap is open. Updated catalogue:

### Previously-catalogued scouts (Section C — unchanged, still subset coverage)

See Section C table. Key: `sim_eight_qubit_dynamic_shell_graph_tensor_network_entropy_coupling_probe` is the closest dynamic integration scout prior to v3 build; it covers layers 1, 6, 12, 13 only.

### Gemini-identified missed integration scouts

Source: `system_v5/ops/formal_scouts/provider_receipts/20260515T084118Z_gemini_claude_manifold_integration_gap_audit.json` (field `2. missed_integration_scouts`). All four were not catalogued in Section C.

| Scout | Layers covered | Tools (inferred) | Dynamic? |
|---|---|---|---|
| `sim_density_spinor_hopf_shell_graph_coherent_information_coupling_probe.py` | 2, 3, 5, 6, 12, 13 | pytorch, opt_einsum, networkx, torch_geometric, gudhi | YES — coherent information implies dynamic measure |
| `sim_left_right_weyl_density_hopf_loop_shell_graph_persistence_coupling_probe.py` | 2, 5, 6, 8, 12, 13 | pytorch, opt_einsum, networkx, gudhi, clifford | YES — dynamic loops and shell graphs |
| `sim_hopf_shell_chirality_asymmetric_cptp_entropy_coupling_probe.py` | 5, 6, 9, 12, 13 | pytorch, opt_einsum, networkx, clifford | YES — entropy coupling over dynamic process |
| `sim_three_dimensional_shell_flux_inverse_square_geometry_probe.py` | 6, 7, 13 | pytorch, networkx, sympy | YES — dynamic geometry probe |

Gemini's rationale per scout: `sim_density_spinor_hopf_shell_graph_coherent_information_coupling_probe.py` couples at least 4-5 distinct tower layers in a dynamic context; `sim_left_right_weyl_density_hopf_loop_shell_graph_persistence_coupling_probe.py` integrates the source-native Weyl layer (8) with Hopf (5) and dynamic shell graph (6, 13); `sim_hopf_shell_chirality_asymmetric_cptp_entropy_coupling_probe.py` directly couples Hopf geometry (5) to the chirality layer (9) via dynamic shell graph; `sim_three_dimensional_shell_flux_inverse_square_geometry_probe.py` is noted in `CODEX_HANDOFF:241-242` but was not catalogued as an integration attempt.

**None of these close the integration gap.** All are partial-layer, partial-tool coverage. The Gemini audit confirms: "No formal scout in `system_v5/ops/formal_scouts/` can be honestly cited as evidence for the owner's request." Grok's parallel audit (`20260515T084118Z_grok_xai_claude_manifold_integration_gap_audit.json`) reached the same verdict: `3. integration_gap_confirmation: confirmed`.

### v3 Claude integrated scout (post-audit build)

**`sim_thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe.py`** — Claude's v3 sim. Current result: **30/35 pass** (`all_pass: false`). Receipt at `system_v5/ops/formal_scouts/results/thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe_results.json`.

- All 13 layers instantiated as simultaneous active constraint enforcers: `thirteen_layer_active_enforcement_executes: pass=true`, `n_layers=13`, `n_steps=8`
- 6 load-bearing tools in controller: pytorch, opt_einsum, gudhi, networkx, numpy, z3; 8 supportive tools in modules
- Layer-removal sweep: 10/13 layers produce state differences >1e-4 when removed (3 layers — `finite_constraint_complex`, `complex_hilbert_carrier`, `dynamic_transition_ratchet_geometry` — show zero diff; open choice in result)
- Cross-track divergence: 1.7616 (Track A MPS-only vs Track B layer-active)
- Track B signed information: max_coherent_information = 0.0981 (pass); Track A: -4.55e-12 (fail — MPS not generating signed information)

**5 open issues (honest):**
1. `flux_conformal_projector_trajectory_diverges_from_constant` — fail (final Frobenius diff only 0.0005, threshold not met)
2. `hitchin_higgs_spectral_signatures_distinct` — fail (g_structures_extended_pass=false)
3. `track_a_mps_only_evolution_produces_signed_information` — fail (Track A coherent info at machine-precision zero)
4. `g_no_flux_conformal_update_collapses_trajectory` — graveyard fail (flux vs constant trajectory diff too small)
5. Nearby variant sweep: 11/13 passed (2 topology variants not passing)

`promotion_allowed: false`. `classification: formal_scout`. These 5 issues are the v4 build target scope.

### Codex integrated scout

**`sim_integrated_nested_geometric_constraint_manifold_dynamic_tensor_network_probe.py`** — Codex's parallel integrated sim. Current result: **`all_pass: true`** after honest tool-depth audit. Receipt at `system_v5/ops/formal_scouts/results/integrated_nested_geometric_constraint_manifold_dynamic_tensor_network_probe_results.json`. 15 tools declared, 9/9 nearby variants passed. `promotion_allowed: false`. Gemini's Section C drift note (`6. additional_drift_flagged`): filename overreaches — the name claims full integration that the audit context explicitly contradicts; claim_ceiling is likely inflated.

---

## I — v3 hardening evidence (2026-05-15)

Three new Claude modules added in the v3 hardening round. All live at `system_v5/ops/formal_scouts/claude_integrated_manifold_modules/`. These are the modules that implement the failing/new predicates in the v3 integrated sim. Evidence cited from `results/thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe_results.json`.

**Module 1 — `chirality_projected_cuts_and_persistence_weighted_feedback.py`** (721 lines)

Implements: γ5-projected reduced densities for each of 7 bipartite cuts; persistence-weighted Hamiltonian strength feedback from GUDHI shell-graph filtration. Evidence from result receipt:
- `chirality_projected_cuts_show_signed_split: pass=true` — max absolute split = 0.5850 across 6 of 7 cuts
- `clifford_gamma5_projection_changes_cuts: pass=true` — 6 of 7 cuts changed by γ5 projection
- `persistence_weighted_strength_grows_or_oscillates: pass=true` — strength grows from 6.46 to 56.48 across 8 steps (monotone; values: 6.46 → 12.61 → 16.70 → 20.75 → 27.80 → 36.52 → 48.35 → 56.48)
- Grok's formula validated: `λ_{k+1} = λ_k + α Σ_i (δ_i - β_i) · w_i` with persistence-weighted edge weights

**Module 2 — `hitchin_higgs_spectral_triples_module.py`** (509 lines)

Implements: Hitchin residual from Higgs bundle stability equations; Higgs spectral curve eigenvalues; Connes distance via spectral triple Dirac operator; spectral zeta function ζ_D(2). Evidence from result receipt:
- `hitchin_residual: 17.244` (nonzero; measures deviation from Hitchin equations)
- `higgs_spectral_curve_eigenvalues: [-2.94, -2.20, -1.19, 0.154, 1.288, 2.894]` — nontrivial (not flat)
- `spectral_triple_D_eigenvalues: [-1.879, -1.532, -1.0, -0.347, 0.347, 1.0, 1.532, 1.879]` — symmetric spectrum; ζ_D(2) = 20.000
- `spectral_zeta_2: 20.0` — note: `hitchin_higgs_spectral_signatures_distinct` positive predicate still fails (`g_structures_extended_pass: false`); this is open issue 2 in the v3 sim

Gemini's Spectral Triples proposal (receipt `20260515T090905Z_gemini_claude_integrated_v2_wide_exploration.json`) specifically identified noncommutative geometry as a candidate for Connes distance observables absent from the current scaffold; this module is the initial implementation.

**Module 3 — `flux_conformal_projectors_and_floer_complexes.py`** (782 lines)

Implements: flux-conformal metric rescaling for each layer's constraint projectors; Floer complex with chain group boundary maps. Evidence from result receipt:
- `floer_complex_has_finite_homology: pass=true` — β₀=3, β₁=0, boundary²=0 (norm), rank_boundary=5
- `flux_conformal_vs_constant_diff: 0.000501` (small; this is why `flux_conformal_projector_trajectory_diverges_from_constant` fails — open issue 1)
- 5 flux-conformal projectors with per-eigenmode anisotropic scaling: the metric family `g_ℓ ← (1 + β F_k) g_ℓ` rescaled by flux orientation scalar per step
- `g_floer_trivial_path_complex_fails_to_distinguish: pass=true` — real path norm 0.1054 vs trivial 0.0588, distance 0.1242

---

## J — γ5 family-wide drift remediation queued (2026-05-15)

Source: Grok's audit at `system_v5/ops/formal_scouts/provider_receipts/20260515T084118Z_grok_xai_claude_manifold_integration_gap_audit.json` (field `6. additional_drift_flagged`, first entry); confirmed family-wide scope by a separate worker pass that found the pattern consistent across 15 scouts in the γ5 family.

**Drift flagged:** `sim_boundary_projected_gamma5_chirality_channel_choi_rank_probe.py` (and the broader γ5 scout family) imports `gamma5/Cl(1,3)` as a source split rather than as a downstream readout. The source-alignment category for these scouts should be `proxy_source_split` — they treat a downstream readout as a substitute for the source object (`ρ_L`/`ρ_R` operating spaces), a practice now disallowed for operating-space claims per the source-alignment incident report and the formal-scout contract.

**Scope:** 15 scouts in the γ5 family confirmed as carrying this misclassification. Note: the WEYL_TERRAIN_SOURCE_ALIGNMENT_INCIDENT_REPORT.md counts 26 detached γ5/chirality scouts + 1 partial in the full estate audit; the 15-scout count here reflects the subset with the specific proxy-source-split pattern requiring the new field.

**Remediation:** Add `source_alignment_category: "proxy_source_split"` field to all 15 γ5 scouts. **Not yet executed.** This is queued pending owner authorization for a bulk-edit pass on the scout estate. Do not execute without explicit owner go-ahead. Do not mark any of these scouts as repaired until the field is added and verified.

**No other action.** Do not delete, rename, or alter the content of these scouts without authorization. The proxy-source-split label is informational metadata, not a deletion authorization.

---

## K — Two chirality sheets: decomposition, constraint structure, and the v4 integration target (2026-05-15)

Owner issued direct clarification on the two-chirality-sheet framework structure. This replaces any prior collapsed or ambiguous readings.

### Two independent chirality sheets

Layer 8 (`weyl_spinor_bundle`) and layer 9 (`chirality_orientation_cover`) support **two independent operating surfaces** distinguished by the γ_5 eigenvalue:

- **γ_5 = +1 sheet** (right-handed Weyl spinor): operates on `ψ_R ∈ C²`, density `ρ_R = ψ_R ψ_R†`. Flux direction: OUT. Source-coupling Hamiltonian: `H_R = −H₀`. Dominant operator coupling: `σ₊` (source-type). Citation: `system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:1249-1273`.
- **γ_5 = −1 sheet** (left-handed Weyl spinor): operates on `ψ_L ∈ C²`, density `ρ_L = ψ_L ψ_L†`. Flux direction: IN. Sink-law Hamiltonian: `H_L = +H₀`. Dominant operator coupling: `σ₋` sink.

The two sheets run **independently**. Do not merge them or treat them as dual faces of one object. The `γ_5` eigenvalue is a Clifford-algebra element from `Cl(1,3)`; its square is `−1` (pseudoscalar algebra). The chirality split is geometric — it lives in layers 8-9, not in any axis.

### Cycle-class × Cl(3)-basis structure per chirality sheet

Per chirality sheet the operating surface admits:

- **8 main cycle-class placements**: the cardinality is determined by Hopf loop homotopy classes (fiber loop vs. base-lift loop) × 4 admissible Bloch-sphere sector transitions. Source: `system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:1249-1273` and atlas citation `:175-181`.
- **4 sub-placements per main placement**: 4 Cl(3) grade-1-or-2 basis-element selections, signed by the Ax6 ordering bit.
- **32 placements per sheet** = 8 main × 4 sub.
- **64 total placements** across both chirality sheets (2 × 32).

The 64 placements remain non-collapsing because Ax6 (operator precedence: operator-first vs. terrain-first, expressed as left vs. right multiplication ordering) signs each Cl(3) basis element distinctly. The same basis element under different Ax6 sign is not the same projector.

### 8 admissible channel families per chirality sheet

Per chirality sheet, the admissible channel families (flux-pattern variants on the in-flux or out-flux of the Weyl spinor density) number **4 per sheet**, **8 total**:

- **γ_5 = −1 sheet (flux IN, `σ₋` sink):** 4 admissible channel families parameterized by Cl(3) generator choice + flux-IN boundary condition. Mathematical basis: distinct Bloch-sphere flow patterns under `H_L = +H₀` evolving `ρ_L` through 4 topologically distinguishable sink-approach trajectories.
- **γ_5 = +1 sheet (flux OUT, `σ₊` source):** 4 admissible channel families under `H_R = −H₀` evolving `ρ_R` through 4 topologically distinguishable source-departure trajectories.

The 8 channel families are real geometric flow patterns on the Bloch sphere of each sheet — not arbitrary labels. Sims must distinguish them by flow topology, not by name assignment.

### 4 Cl(3) grade-1-or-2 basis-element operators per sheet

Each substage applies one of 4 Cl(3) basis elements in grade-1-or-2 (dephasing-type vs. rotation-type projection), signed by the Ax6 bit:

- **Dephasing-type family**: Cl(3) grade-1 elements whose action on `ρ` is a projective dephasing (commutant structure, off-diagonal suppression).
- **Rotation-type family**: Cl(3) grade-2 elements (bivectors) whose action is a unitary rotation on the Bloch sphere.
- Ax6 (operator-first precedence = +1; terrain-first precedence = −1) determines whether the Cl(3) element is applied before or after the channel projector, producing `operator ∘ projector ∘ state` vs. `projector ∘ operator ∘ state` — non-commuting orderings.

### Manifold constraint requirement

The 13-layer nested tower is not decorative scaffolding. It must enforce simultaneous constraint surfaces on the evolution of both chirality sheets at each cycle-class placement. The load-bearing integration problem: both sheet evolutions running inside the manifold that actively constrains them — not running independently and then checked against manifold structure post hoc.

**Directive on doc contradictions:** where existing docs contain contradictory readings for cycle-class counts, basis-element operators, or channel-family definitions, **sim all options as variants**. Multiple surviving candidate readings are the signal until bounded sim work excludes them. Do not resolve contradictions by authority preference at design time.

### v4 build target

Named target: `sim_two_engine_thirty_two_stage_manifold_constrained_dynamic_tensor_network_probe.py`
(Filename contains interpretive mnemonics "engine" and "stage"; see Appendix A.8 for the naming tension with the formal-scout contract.)

Location: `system_v5/ops/formal_scouts/` (formal scout estate)

Required to close: the 5 open issues from v3 (Sections H/I) plus the two-chirality-sheet structure running under manifold constraint. Minimum spec:
- Two simultaneous chirality-sheet tracks (`ρ_L`/`ρ_R`, independent, γ_5 = ±1) running as distinct constraint surfaces inside the 13-layer manifold
- 32 cycle-class × Cl(3)-basis-element placements per sheet (8 main × 4 sub), signed by Ax6
- Flux-conformal projector trajectory with larger parameter spread (resolve open issue 1)
- MPS signed information with lower truncation threshold or larger time step (resolve open issue 3)
- Hitchin-Higgs G-structure extended pass criterion met (resolve open issue 2)
- Graveyard: left-right collapse control (merge both chirality sheets and check if readouts flatten)
- `promotion_allowed: false`; `classification: formal_scout`

---

---

# Appendix: Interpretive Overlays — Not Part of the Math

**Disclaimer:** These names are interpretive — they are operational mnemonics for the underlying math objects (chirality eigenvalues, loop homotopy classes, Cl(3) basis elements, ratchet direction, flux-pattern channel families). The math is in Sections A through K above. Removing these names does not remove any math content. Where a mnemonic could map to multiple math objects, the ambiguity is preserved below — do not collapse it.

---

## A.1 — Chirality sheet names ("Type 1" / "Type 2")

Owner jargon: the γ_5 = −1 sheet is called **Type 1**; the γ_5 = +1 sheet is called **Type 2**. Source: owner-authored docs `apple axes terrain operator math.md:1249-1306`, `ENGINE_MATH_REFERENCE.md:141-169`, `LEFT_RIGHT_CHIRAL_OPERATING_SPACE_BUILD_NOTE.md:19-78`.

Math objects: `ψ_L ∈ C²` with `H_L = +H₀` (Type 1); `ψ_R ∈ C²` with `H_R = −H₀` (Type 2).

Naming rules (from established directives):
- **Type 1 / Type 2 in prose only.** Banned as sim filenames or class identifiers per formal-scout contract `:88-94`.
- Banned everywhere: `EngineL`, `EngineR`, `Engine_L`, `Engine_R`, `Engine A`, `Engine B`.
- These chirality sheets may also be called "engines" in prose (owner jargon: "2 independent engines"). The formal-scout contract bans `sim_engine_*` filenames; prose use of "engine" is permitted as a mnemonic.

**Agent drift to kill:** `grok_audit.py:16` states "Type 1/2 reserved for sheets only" — this contradicts owner-source and is flagged as agent drift. `grok_audit.py:19-24` introduces "Carnot + Szilard dual-stack" framing — agent hallucination, killed. The QIT framework is NOT Carnot + Szilard.

---

## A.2 — Cycle-class / placement mnemonics ("stages," "substages," "stage structure")

Owner jargon: the 8 main cycle-class placements per chirality sheet are called **"8 main stages."** The 4 sub-placements per main placement are called **"4 sub-stages."** The full count per sheet is **"32 stages"**; both sheets together: **"64 engine stages total."**

Math objects: 8 Hopf-loop homotopy class × Bloch-sector transition placements; 4 Cl(3) grade-1-or-2 basis selections per placement; 32 per sheet; 64 across both sheets.

The "8 main stages" per sheet should not be confused with the 8 qubit count in the 8-qubit dynamic shell scouts (Section C), which is a different 8.

**Mapping ambiguity (preserve, do not collapse):** the precise correspondence between "stage" and a homotopy-class slot has not been fully resolved against the atlas doc. Read `AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md` and `apple axes terrain operator math.md` for contradictions and sim all as variants before building v4.

---

## A.3 — Flux-channel family names ("terrain names")

Owner jargon names the 8 admissible channel families:

**γ_5 = −1 sheet (flux IN, `σ₋` sink, `H_L = +H₀`):**
- **Funnel** — sink-approach trajectory family 1
- **Vortex** — sink-approach trajectory family 2
- **Pit** — sink-approach trajectory family 3
- **Hill** — sink-approach trajectory family 4

**γ_5 = +1 sheet (flux OUT, `σ₊` source, `H_R = −H₀`):**
- **Cannon** — source-departure trajectory family 1
- **Spiral** — source-departure trajectory family 2
- **Source** — source-departure trajectory family 3
- **Citadel** — source-departure trajectory family 4

Source: `system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:1249-1273`.

Math objects: the 4 terrain names per sheet are labels for 4 topologically distinguishable Bloch-sphere flow patterns (flux-IN trajectories for the left sheet; flux-OUT trajectories for the right sheet). They are distinguished by their geometric flow topology — not by name assignment. Sims must produce topological distinctions; the names are mnemonics.

**Mapping ambiguity:** "WIN/LOSE" (mentioned in some doc contexts as an outer-loop direction label) could map to "horizontal-lift Hopf loop class" OR to "ratchet forward direction." This ambiguity is preserved here; do not collapse it into one reading.

---

## A.4 — Operator-family shorthand (Jung-function letter codes)

Some owner-authored and agent-authored documents use Jung cognitive-function letter codes as shorthand for Cl(3) basis-element operator families:

- **Dephasing-type operators** (Cl(3) grade-1): shorthand `{Ti, Te}` — introverted-thinking and extroverted-thinking type mnemonics.
- **Rotation-type operators** (Cl(3) grade-2 bivectors): shorthand `{Fi, Fe}` — introverted-feeling and extroverted-feeling type mnemonics.

These shorthand labels appear in: axis Ax5 definition (`atlas:180, :428-447`); the open/unresolved Ax4 dual-label note; various handoff docs.

Math objects: the four labels are mnemonics for four Cl(3) basis-element projectors — two dephasing-type (grade-1) and two rotation-type (grade-2 bivectors). The letter codes do not introduce any functional-type-system content into the math; they are operational mnemonics only.

**Banned from main body and sim identifiers.** Do not introduce these letter codes into sim code or sim result JSON. Use explicit Cl(3)-basis-element descriptions in sim code.

---

## A.5 — Axis semantic labels referencing functional-type systems

Axis operational DoFs Ax1, Ax4, Ax5 carry mnemonics that reference Jung cognitive-function or IGT system labels in some documents:

| Axis | Math operational DoF | Mnemonic in some docs |
|---|---|---|
| Ax1 | Derived topology-branch split, binary: two homotopy-class families | `{Se, Ni}` vs `{Ne, Si}` |
| Ax4 | Loop-order family: non-commuting composition order | `FeTi`/`TeFi` (IGT loop-family split per atlas:417-418); also "heat-flow / ordering direction" |
| Ax5 | Cl(3) operator family: dephasing vs rotation | `{Ti, Te}` vs `{Fi, Fe}`; also "heat level (hot/cold)" |

These mnemonics appear in: `AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md:176-180, 267-281, 417-418, 428-447`; `CLAUDE_THREAD_HANDOFF_FLUX_TERRAIN_AXIS_OPERATOR_DISCIPLINE_20260515.md` (open/unresolved section).

**Ax4 dual-label:** the atlas keeps both the Jung pair-order split `TiFe`/`FeTi` AND the IGT loop-family split `FeTi`/`TeFi` as candidate readings (atlas:179, 417-418). The handoff adds a third: "heat-flow / ordering direction." All three are held as candidate readings; they have not been collapsed.

**Ax0 dual-layer:** atlas math-side = cut functional Φ₀(ρ_AB), torus seat b₀ = sign(cos 2η). Handoff semantic-side = "positive feedback loop vs negative feedback loop" (NOT hot/cold). Both readings are held; not collapsed.

**Banned from main body and sim code.** Do not introduce Se/Ni/Ne/Si/Te/Ti/Fe/Fi/IGT labels into sim code, sim result JSON, or formal-scout filenames.

---

## A.6 — "Engine slot," "engine stage," and related composite mnemonics

The phrase **"engine slot"** (sometimes "engine stage") appears in some handoff documents to refer to a chirality-sheet × cycle-class-placement combination: one of the 64 total placements (32 per sheet) described in Section K.

Math object: a specific triple (γ_5 eigenvalue, main cycle-class placement index ∈ {0,...,7}, sub-placement Cl(3)-basis index ∈ {0,...,3}).

These composite phrases are not used in formal-scout filenames or class identifiers. They are prose mnemonics only.

---

## A.7 — "Personality" and functional-type-system framing

The term **"personality"** and the broader functional-type-system framing (MBTI, Jungian cognitive functions) appear as the historical motivating analogy for the axis-operator structure in some owner-authored reference documents. Examples: the terrain names (Funnel/Vortex/Pit/Hill for the flux-IN sheet; Cannon/Spiral/Source/Citadel for the flux-OUT sheet) were named using the Bloch-sphere flow intuition from the functional-type typology.

**This framing is motivating analogy, not math content.** The math objects are: Cl(3) basis elements, chirality eigenvalues, Hopf loop homotopy classes, Bloch-sphere flow topologies. The functional-type framing does not appear in sim code, sim filenames, or formal-scout identifiers.

---

## A.8 — Owner directives that resisted clean restructuring

The following owner directives from Section K (original doc) contain interpretive labels that are retained here because removing them would lose the owner's framing as an operational contract:

1. **"2 independent engines. Type 1 operates on left chirality (ψ_L / ρ_L). Type 2 operates on right chirality (ψ_R / ρ_R)."** — Retained verbatim as an owner directive. Math restatement in Section K of main body.

2. **"32 stages per engine. Decomposition: 8 main stages × 4 sub-stages = 32. With 2 engines: 64 engine stages total."** — Retained verbatim. Math restatement in Section K.

3. **"8 terrains total. 4 per side. Left side (flux IN, σ₋ sink): Funnel / Vortex / Pit / Hill. Right side (flux OUT, σ₊ source): Cannon / Spiral / Source / Citadel."** — Retained verbatim. Math restatement in Section K and Appendix A.3.

4. **"8 operators. Structure: 4 base operators × Ax6 signs (up/down)."** — Retained verbatim. Math restatement in Section K.

5. **Named v4 build target filename:** `sim_two_engine_thirty_two_stage_manifold_constrained_dynamic_tensor_network_probe.py` — this filename contains "engine" and "stage" as label-loaded terms. It is retained as the authorized build-target name (owner-authorized filename). The formal-scout contract bans `sim_engine_*` prefix; this filename uses "engine" mid-name. This tension is unresolved and held open — sim all variants if the contract bans this filename structure.
