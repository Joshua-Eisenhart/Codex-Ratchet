# Tool × Lego-Family Integration Matrix

Date: 2026-04-14. Scope: `system_v4/probes/*.py` sims whose
`TOOL_INTEGRATION_DEPTH[tool] == "load_bearing"` AND whose file-name / docstring
ties to the named lego family. Empty cell = no such sim exists (backlog).
Report-only, no new sims authored.

Lego families (columns) scanned by prefix / docstring:
- `Hopf` : hopf / hopf_torus / hopf_fiber / nested_hopf
- `Weyl` : weyl / weyl_geometry / weyl_spinor
- `Cl3`  : cl3_* (Clifford(3,0))
- `Cl6`  : cl6_* (Clifford(6,0))
- `Gtower`: sim_gtower_*, g_structure_tower
- `Spec3`: spectral triple (candidate name: `spectral_triple`) — none found
- `Gerbe`: sim_gerbe_*
- `Assoc`: sim_assoc_bundle_*
- `FEP`  : sim_fep_*, fep_ratchet
- `SzC`  : sim_qit_szilard_*, sim_qit_carnot_*, sim_carnot_*
- `F01`  : sim_axiom_f01_*
- `N01`  : sim_axiom_n01_*
- `L0-19`: sim_L*_*, sim_layer*_coupling_matrix
- `Bridge`: sim_bridge_*, bridge
- `Holo` : sim_holodeck_*
- `Axis0`: sim_axis0_*, axis0 gradient

## Matrix (cell = representative load-bearing sim path; "—" = EMPTY)

| tool \ family | Hopf | Weyl | Cl3 | Cl6 | Gtower | Spec3 | Gerbe | Assoc | FEP | SzC | F01 | N01 | L0-19 | Bridge | Holo | Axis0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| numpy       | baseline-everywhere (non-canon) | | | | | | | | | | | | | | | |
| pytorch     | sim_hopf_torus_lego | sim_weyl_nested_shell | — | — | — | — | — | — | — | — | sim_axiom_f01_finite_hilbert_dim | sim_axiom_n01_composition_order_distinguishes | sim_layer_coupling_matrix_v3 | — | — | sim_torch_deep_axis0_autograd_vn_entropy |
| sympy       | — | — | — | — | — | — | — | — | sim_fep_generative_model_as_shell | — | sim_axiom_f01_quotient_well_defined | sim_axiom_n01_identity_via_indistinguishability | — | — | — | — |
| z3          | sim_hopf_foliation_structure | sim_weyl_geometry_proof_pressure | — | — | sim_gtower_reduction_obstruction_z3 | — | — | — | sim_fep_pair_free_energy_x_engine_coupling | sim_qit_szilard_landauer_cycle, sim_carnot_constraint_admissibility_fence | sim_axiom_f01_finite_measurement_set | sim_axiom_n01_indiscernibility_implies_identity | sim_L2_eight_stages, sim_layer_coupling_matrix | sim_qit_weyl_carnot_bridge | sim_holodeck_distinguishability_gate | — |
| cvc5        | — | — | — | — | — | — | — | — | — | — | — | — | — | sim_bridge_cvc5_crosscheck (as load-bearing? supportive), sim_blackwell_style_comparison | — | — |
| clifford    | sim_hopf_torus_lego | sim_weyl_nested_shell | sim_cl3_basis, sim_cl3_rotor_product, sim_cl3_bivector_exp, sim_cl3_reflection, sim_cl3_composition, sim_cl3_invariants, sim_clifford_deep_cl3_rotor_double_cover | sim_cl6_basis, sim_cl6_rotor_product, sim_cl6_chirality, sim_cl6_spin_group_embedding | — | — | — | — | — | — | — | — | sim_layer_coupling_matrix_v2 | — | — | — |
| e3nn        | sim_density_hopf_geometry, sim_torch_hopf_connection | — | — | — | — | — | — | — | — | — | — | — | — | sim_axis6_e3nn_fe_bridge | — | — |
| geomstats   | sim_foundation_hopf_torus_geomstats_clifford, sim_hopf_torus_lego | sim_weyl_nested_shell | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| pyg         | sim_pyg_deep_hopf_u1_equivariant_conservation | — | — | — | — | — | — | — | — | — | — | — | sim_geometric_constraint_manifold_pyg | — | — | — |
| rustworkx   | — | sim_weyl_geometry_graph_proof_alignment, sim_lego_weyl_geometry_protocol_dag | — | — | — | — | — | — | — | sim_carnot_graph_proof_alignment, sim_szilard_graph_proof_alignment | — | — | sim_layer_coupling_matrix, sim_layer_coupling_matrix_v2 | sim_rustworkx_bridge_dag, sim_qit_weyl_carnot_bridge | — | — |
| toponetx    | sim_toponetx_hopf_crosscheck | — | — | — | — | — | — | — | — | — | — | — | sim_toponetx_constraint_shells | sim_toponetx_bridge_seam, sim_toponetx_deep_hodge_boundary | — | — |
| gudhi       | sim_gudhi_deep_s3_hopf_torus_persistent_homology, sim_hopf_torus_lego | sim_weyl_nested_shell | — | — | — | — | — | — | — | — | — | — | — | sim_persistence_geometry | — | — |
| xgi         | — | — | — | — | — | — | — | — | — | — | — | — | sim_xgi_shell_hypergraph, sim_xgi_l7_marginal | — | — | sim_xgi_gradient_ascent, sim_xgi_torch_autograd |
| networkx    | — | — | — | — | — | — | — | — | — | — | — | — | — | — | sim_leviathan_as_civilizational_shell_on_manifold | — |

## Coverage Summary

- Matrix dimension: 14 tools × 16 lego families = 224 cells.
- numpy row: omitted per doctrine (classical baseline, non-canon by construction). Remaining addressable surface: 13 × 16 = 208 cells.
- Load-bearing cells populated (counting only cells with at least one concrete file): ~42 / 208 ≈ **20% coverage**.
- Tool rows with strongest coverage: **z3** (13/16), **clifford** (5/16 concentrated on Cl3/Cl6/Hopf/Weyl), **pytorch** (6/16 via torch/e3nn/pyg combos).
- Tool rows with near-zero coverage: **cvc5** (1 supportive only, no unambiguous load-bearing), **networkx** (1 decorative), **e3nn** (2, only Hopf + axis6 bridge), **geomstats** (2, only Hopf + Weyl), **xgi** (L0-19 + axis0 only).
- Column gaps: **SpectralTriple column is fully empty across every tool** (highest-value single backlog). **Gerbe** column also empty for load-bearing (existing gerbe sims are classical/structural without declared load-bearing tool). **AssocBundle** column similarly empty for load-bearing.
- Compound-tool cells (memory doctrine §"Compound step"): rare — `sim_qit_weyl_carnot_bridge` (z3+rustworkx), `sim_layer_coupling_matrix_v2/v3` (pytorch+clifford+rustworkx). Compound coverage ≈ 3 cells.

## Largest uncovered rows

1. **cvc5** — no unambiguous load-bearing sim on ANY family (parity-crosscheck-only posture). Highest-priority backlog.
2. **networkx** — single decorative cell.
3. **e3nn** — only 2 cells, and both are Hopf-adjacent; missing Weyl, Cl6, G-tower.
4. **geomstats** — 2 cells; missing Cl3/Cl6, Gtower, Gerbe, Assoc.

## Largest uncovered columns

1. **SpectralTriple** — 0 tools load-bearing. Family may not yet have a
   carrier sim at all (no `spectral_triple` filename hit in probes scan).
2. **Gerbe** — 5 gerbe sims exist but none declare a load-bearing tool (likely
   numpy-only cochain arithmetic today).
3. **AssocBundle** — 6 assoc_bundle sims exist, none load-bearing for any tool.
4. **Axis0** — only pytorch (autograd) and xgi load-bear; no z3/sympy/clifford
   load-bearing Axis0 proof despite doctrine framing Axis0 as ∇I_c.

---

# Ablation Audit of 8 Deep-Integration Sims

Method: read each file's CLAIM / structural_identity section and determine
whether the admissibility claim (not the computation) collapses when the named
tool is replaced with a numpy stub.

| tool | sim | ablation verdict | why |
|---|---|---|---|
| z3 | sim_z3_deep_no_classical_stochastic_under_dephasing_weyl_commute.py | **TRUE load-bearing** | Claim is a UNSAT structural impossibility over a 4×4 row-stochastic circulant surrogate with constrained off-diag contraction + chirality delta. z3 `prove/unsat` IS the admissibility statement. A numpy stub can only sample, cannot certify UNSAT — the exclusion claim evaporates. |
| sympy | sim_sympy_deep_lindblad_dephasing_spectrum.py | **TRUE load-bearing** | Admissibility boundary is declared as the exact locus γ_φ = -γ₁/2 derived in closed symbolic form. A numerical eigendecomp would approximate the boundary but cannot prove exactness nor identify degeneracy structure. Claim depends on symbolic form, not numeric value. |
| clifford | sim_clifford_deep_cl3_rotor_double_cover.py | **TRUE load-bearing** | Double-cover identity (P1) R v R~ = (−R) v (−R)~ while R ≠ −R as multivectors is meaningful only inside the GA algebra where R and −R are distinct Spin(3) elements. A numpy SO(3) matrix stub erases the sign — `R ≠ −R` becomes `rotation == rotation`, and the 2-to-1 claim disappears. |
| pytorch | sim_torch_deep_axis0_autograd_vn_entropy.py | **TRUE load-bearing (but narrow)** | Claim is that autograd reproduces dS/dθ = 0 through matrix_exp→conj→eigvalsh. Swapping to numpy + finite-difference would still hit ~0 for the positive case. HOWEVER the doctrinal claim ("forward = possibilities, backward = constraints, autograd IS the ratchet") requires actual backward-pass through complex matrix_exp; finite-diff is a different object. Verdict TRUE on ratchet-architecture grounds; would be FALSE if the claim were only "derivative = 0". |
| pyg | sim_pyg_deep_hopf_u1_equivariant_conservation.py | **FALSE (decorative)** | Update rule f'ᵢ = fᵢ + α Σ(fⱼ − fᵢ) is linear symmetric aggregation; charge conservation and U(1) equivariance follow from arithmetic, not from PyG's `MessagePassing.propagate()`. A 10-line numpy edge-loop reproduces the same conservation and the same equivariance check exactly. PyG here is a thin wrapper; the admissibility claim does not break under ablation. Upgrade path: require non-trivial aggregator (attention, gated) or edge_index-derived topology that numpy cannot reconstruct. |
| rustworkx | sim_rustworkx_deep_cayley_s4_admissibility.py | **TRUE load-bearing** | Claims use `cycle_basis`, `is_isomorphic` (VF2), `max_flow`, `node_connectivity`. Graph isomorphism and max-flow are non-trivial algorithms; a numpy stub would either be wrong (naive subgraph match) or would effectively reimplement rustworkx. The Mader-theorem check (edge-connectivity = degree) requires real max-flow. |
| toponetx | sim_toponetx_deep_hodge_boundary.py | **PARTIALLY TRUE (weak load-bearing)** | Boundary-of-boundary B_{k−1} B_k = 0 and PSD Hodge Laplacian are properties of ANY correctly-constructed incidence matrix. A hand-coded numpy incidence for a triangulated S² trivially satisfies them. What toponetx actually contributes is the *construction* of incidence_matrix from SimplicialComplex / CellComplex objects — structural, but not admissibility-load-bearing. Verdict: load-bearing as a construction surface, decorative as a proof surface. Upgrade path: use a carrier whose cell structure numpy cannot easily hand-encode (higher-dim or attached cells). |
| gudhi | sim_gudhi_deep_s3_hopf_torus_persistent_homology.py | **TRUE load-bearing** | Vietoris-Rips persistence + SimplexTree + persistent_betti_numbers is a non-trivial algorithm (filtration over simplicial complex, boundary matrix reduction). Numpy stub cannot reproduce persistent Betti signatures from a point cloud without reimplementing gudhi. Claim "S³ sample → (1,0,0,1), T² sample → (1,2,1)" collapses without gudhi. |

## Ablation Summary

- **6 / 8 TRUE load-bearing**: z3, sympy, clifford, pytorch, rustworkx, gudhi.
- **1 / 8 PARTIAL**: toponetx (construction yes, proof no).
- **1 / 8 FALSE decorative**: pyg (linear aggregation is numpy-equivalent).
- Highest-value upgrade: **pyg** sim needs a claim that requires non-linear
  aggregation or learned weights on the Hopf graph, OR a PyG-specific
  structural claim (e.g. over-smoothing bound under Laplacian propagation).
- Secondary upgrade: **toponetx** sim should target a claim only the cell-
  complex construction admits — e.g. coboundary on an attached 2-cell where
  the incidence pattern is not hand-constructible.
