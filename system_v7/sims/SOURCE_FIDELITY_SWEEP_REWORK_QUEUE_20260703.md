tokens used
277,314
Partial source-fidelity sweep completed from on-disk files. I counted **70** top-level files in [sims_and_scripts](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/sims_and_scripts), not ~66; four are JSON result artifacts, and I included them.

Ceiling: **PARTIAL Wizard/source archaeology only**. No native subagent receipts were available, the MCP graph list call was canceled, and I did not rerun sims. This is a rework-queue classification from docstrings, core computation shape, and source-doc anchors.

Verdict shorthand below:
`RENDERED` = rendered-faithfully for the sim’s narrow object.
`PARTIAL` = right atoms, missing source structure or gate.
`UNANCHORED` = reconstruction outruns or contradicts the corpus.
`STANDARD` = standard QIT/physics result; owner-doc anchor not required.

| sim | claims | anchor docs | verdict | gap |
|---|---|---|---|---|
| access_law_decoupling_sim.py | 8-of-16 access law, terrain-vs-drive chirality | `ENGINE_64`, `WMS`, `Rosetta` | PARTIAL | Two-tier/14-of-16, not full chart traversal. |
| admissibility_two_operator_sim.py | exactly 2 native ops per terrain | `QIT4OP`, `WMS` | PARTIAL | Derives kernel rule, not full source 16-stage contract. |
| agent_loop_sim.py | perception+action active-inference loop | Holodeck/FEP docs | PARTIAL | Generic QIT loop, missing world-coupled holodeck contract. |
| audit_response_w_covariance_sim.py | W maps Ti/Fi to Te/Fe | `QIT4OP`, `WMS` | RENDERED | Narrow W-covariance is faithful. |
| axis0_entropy_production.json | Axis0 entropy-production probe result | `Axis0`, `manifold_build_ladder` | PARTIAL | Artifact says doctrine not realized. |
| axis0_functional_probe.json | Axis0 functional probes | `Axis0`, `manifold_build_ladder` | PARTIAL | All probed functionals miss doctrine target. |
| axis0_gauge_breaking_sim.py | a2 gauge degeneracy, withdrawn linear law | `Rosetta`, `STATE_OF_MODEL` | RENDERED | Corrected negative/monotone rendering. |
| axis0_response_derivative.json | Axis0 response derivative result | `Axis0`, `manifold_build_ladder` | PARTIAL | Artifact says all signs same, no doctrine split. |
| axis0_sector_sim.py | a2 gauge, entropy/phase sector split | `Rosetta`, `WMS` | RENDERED | Narrow structural split is faithful. |
| axis0_spinor_720_sim.py | spinor 720 phase visibility | `WMS`, `QIT4OP` | PARTIAL | 720 bit works; terrain/operator E-operators not closed. |
| axis0_xor_sim.py | parity p=a1 XOR a2 | `Rosetta`, `WMS` | RENDERED | Exact lattice rendering. |
| axis2_two_layer_sim.py | Axis2 = V continuous + W discrete | `Rosetta`, `WMS` | RENDERED | Faithful to corrected fork. |
| axis_laws_dual_proof.py | XOR and b6 forced with z3/cvc5 | `WMS`, `Rosetta` | RENDERED | Logic object faithful, still scratch ceiling. |
| axis_loadbearing_n01_sim.py | coherent-axis choice load-bearing | `WMS`, `ENGINE_64` | RENDERED | Good audit guard; demotes incompatible older rows. |
| biochem_bridge_sim.py | tunneling/catalysis bridge | A2 chirality, bridge ladder | PARTIAL | Standard quantum atoms; biochemical bridge source contract thin. |
| chemistry_bridge_sim.py | Hubbard dimer chemical bond | standard QM/chemistry | STANDARD | Legit textbook realization, not ToE evidence. |
| chi2_decisive_test_sim.py | chi2 not a2-specific; decisive fork | `STATE_OF_MODEL`, `Rosetta` | RENDERED | Faithful negative correction. |
| chi2_openpath_readout_sim.py | Bargmann phase eigenvector meter | `STATE_OF_MODEL`, `Rosetta` | RENDERED | Faithful once a2-specific claim is fenced. |
| constraint_core_audit.py | C1-C7 Hopf/terrain realization checks | `WMS`, `QIT4OP` | RENDERED | Narrow realization battery faithful. |
| constraint_core_symbolic.py | symbolic F01/N01/T01/Hopf proofs | formal spec, `Root` | RENDERED | Good symbolic spine; not admission. |
| coratchet_axis_orthogonality_sim.py | co-ratchet axes and orthogonality | `WMS`, `Rosetta` | PARTIAL | Axis lattice right; missing full M(C)/fresh audit. |
| cosmogenesis_persistence_sim.py | first persistent object from fuzz | cosmology fuel, `WMS` | UNANCHORED | Norm-preserving spinor origin is reconstruction. |
| coupled_coratchet_dualloop_sim.py | dual co-ratchet 720 loop | `WMS` §§13-15 | PARTIAL | Missing full Carnot/Szilard legality stack and controls. |
| data_processing_sim.py | DPI monotone | standard QIT, bridge index | STANDARD | Fine as standard QIT. |
| decoherence_scaling_sim.py | decoherence rate scaling | standard QIT/physics | STANDARD | Fine as standard physics. |
| distinguishability_engine_core_sim.py | integrated root/Hopf core | `Root`, `Owner thesis`, `WMS` | PARTIAL | Faithful installed carrier, not forced by root. |
| division_algebra_ratchet_sim.py | Cayley-Dickson ladder | `WMS` §10.3 | PARTIAL | Right rung atoms; installed/rung-later, not forced. |
| engine_64_schedule_sim.py | 64 schedule uniqueness by N01 | `ENGINE_64`, `QIT4OP` | PARTIAL | Lifts order readout; not full 64 closure. |
| engine_type_access_sim.py | 8-of-16 engine access | `ENGINE_64`, `WMS` | PARTIAL | Superseded/narrowed by access/loadbearing findings. |
| entropic_gravity_axis0_sim.py | entropy-gradient gravity mechanism | `Axis0`, owner cosmology | PARTIAL | Toy mechanism; no GR tensor/empirical bridge. |
| entropic_newton_limit_sim.py | Verlinde Newton limit + dark sector fence | standard entropic gravity, `Axis0` | PARTIAL | Newton limit standard; dark-sector source bridge open. |
| eps_even_a2_dissipation_foothold_sim.py | eps-even a2 foothold negative | `STATE_OF_MODEL` | RENDERED | Useful negative, not closure. |
| eps_even_a2_specificity_sim.py | eps-even symmetrization, a2 no-go | `STATE_OF_MODEL` | RENDERED | Faithful to corrected chi2/a2 scope. |
| evolution_chirality_bridge_sim.py | biological chirality bridge | `A2_CHIRALITY` | PARTIAL | Forces chirality pattern, not biological/evolution proof. |
| fluctuation_theorem_sim.py | Jarzynski/Crooks | standard statistical physics | STANDARD | Fine standard result. |
| flux_nesting_ablation_jax.py | flat-carrier flux ablation | `WMS` flux section | PARTIAL | Good ablation; flux family still candidate. |
| holevo_bound_sim.py | Holevo bound | standard QIT | STANDARD | Fine standard result. |
| holodeck_sim.py | prediction-first learning/memory | Holodeck/FEP docs | PARTIAL | Captures loop atoms, not semantic/world-coupled memory. |
| holographic_bound_sim.py | Bekenstein/Page capacity | standard QIT/physics | STANDARD | Fine standard result. |
| info_processing_sim.py | per-stage info-channel signatures | `QIT4OP`, `ENGINE_64` | PARTIAL | Good instrumentation, not source-specified full contract. |
| instrument_class_split_sim.py | relaxation vs conditioning live-loop split | loopback/live-loop note | PARTIAL | Strong local split; corpus anchor is thin. |
| lev_bridge_sim.py | QIT signal stream into Lev | `QIT_LEV_BRIDGE_SPEC` | RENDERED | Stub adapter matches spec. |
| manifold_build_ladder.py | build manifold layer-by-layer | `GCM`, `WMS`, `Axis0` | PARTIAL | Uses geometric overlays before full finite relation contract. |
| manifold_ladder_results.json | manifold ladder artifact | same as above | PARTIAL | Artifact; Axis0 not realized. |
| manifold_laws_smt_proof.py | access/pole/two-sector laws | `WMS`, `ENGINE_64` | RENDERED | Faithful narrow proofs with degeneracy logged. |
| memory_sim.py | projective cells + spinor phase memory | Holodeck, `WMS` | PARTIAL | Older memory atoms; superseded by spinor/Hopfield rows. |
| nested_basin_sim.py | manifold as nested basins | basin/constraint doctrine | PARTIAL | Basin hierarchy not fully source-extracted. |
| no_cloning_sim.py | no-cloning and 5/6 cloner | standard QIT | STANDARD | Fine standard result. |
| noncommutation_bounds_sim.py | uncertainty + CHSH/Tsirelson | standard QIT | STANDARD | Fine standard result. |
| nonunitality_theorem_sim.py | fusion split = nonunitality | `QIT4OP`, `STATE_OF_MODEL` | RENDERED | Strong faithful repair. |
| octonion_spinor_network_sim.py | G2/octonion spinor network | `WMS` §10-11 | PARTIAL | Good scout; no full network/M(C) admission. |
| operator_geometry_fusion_sim.py | terrain contained in operator algebra | `QIT4OP`, `WMS` | PARTIAL | Pre-theorem probe; superseded by nonunitality theorem. |
| perspective_convergence_sim.py | one basin, many physics perspectives | owner thesis/cosmology | UNANCHORED | Werner-state convergence is invented bridge. |
| physics_bridge_sim.py | Landauer + einselection | standard QIT/physics | STANDARD | Computation fine; Carnot/Szilard overlay remains witness. |
| qit_active_inference_planning_sim.py | active FEP planning on manifold | Holodeck/FEP, `WMS` | PARTIAL | Planning atoms; epistemic part explicitly sign-demo. |
| qit_fep_ratchet_sim.py | pure-QIT FEP through ratchet | Holodeck/FEP, `Root` | PARTIAL | Good translation, not full FEP theorem. |
| quantum_hopfield_memory_sim.py | Hopfield memory earned from terrain | Holodeck, `WMS` | PARTIAL | Promising, but Hopfield dynamics are a separate claim. |
| quantum_speed_limit_sim.py | QSL from finitude/noncommutation | standard QIT | STANDARD | Fine standard result. |
| root_axiom_sim.py | a=a iff a~b root rendering | `Root`, owner thesis | RENDERED | Narrow runnable rendering; not metaphysics proof. |
| signed_axis0_primitive_sim.py | coherent info as signed Axis0 primitive | `Axis0`, entropy tables | PARTIAL | Signed object useful; Xi/rho_AB/Phi0 bridge open. |
| sixteen_stage_engine_schedule_sim.py | 16 stages as policy space | `ENGINE_64`, `WMS` | PARTIAL | Best active schedule row; still not full chart closure. |
| sixteen_stage_engine_sim.py | 16 distinct order-sensitive stages | `ENGINE_64`, `QIT4OP` | PARTIAL | Older row; narrowed by schedule/loadbearing rows. |
| spinor_memory_sim.py | 720 loop bit + sheet retention bit | `WMS`, Holodeck | PARTIAL | Strong psi-only bits; not full 720 dual-engine loop. |
| terrain_8way_separation_sim.py | all 8 terrains separated | `ENGINE_64`, `WMS` | RENDERED | Faithful for installed terrain generators. |
| terrain_differentiation_sim.py | rich 8-terrain fingerprint | `ENGINE_64`, `WMS` | RENDERED | Faithful installed terrain differentiation. |
| terrain_information_signature_sim.py | bridge observables classify terrains | bridge index, `WMS` | PARTIAL | Mostly 3-class info signature, not full terrain source law. |
| terrain_qutip_crosscheck.py | QuTiP crosscheck of generators | `QIT4OP`, `WMS` | RENDERED | Good independent library check. |
| terrain_sourcelock_axis0_sim.py | source-lock terrain, Axis0 miss | `Axis0`, `ENGINE_64` | RENDERED | Faithful negative: Axis0 not terrain-local scalar. |
| three_qubit_octonion_fep.py | 3q/octonion/FEP rung | `WMS`, Holodeck/FEP | PARTIAL | Bundles too much; needs split rungs. |
| weak_force_chirality_bridge_sim.py | weak left coupling bridge | `A2_CHIRALITY` | PARTIAL | Standard side empirical; forces chiral, not left sign. |

**Rework Queue**
1. `cosmogenesis_persistence_sim.py` — UNANCHORED. Extract exact “static fuzz / first pattern / time as sequence” finite-object contract; rebuild as a minimal persistence discriminator with explicit kill controls before spinor/norm claims.
2. `perspective_convergence_sim.py` — UNANCHORED. Replace Werner-state convergence with typed projectors from `D_t`/Axis0/chirality/QSL docs; each perspective gets its own finite map and falsifier.
3. `entropic_gravity_axis0_sim.py` + `entropic_newton_limit_sim.py` — PARTIAL, load-bearing. Build the `Omega_r -> C_G -> Xi_* -> rho_AB -> Phi0` extraction first; only then test gravity/binding/expansion.
4. `coupled_coratchet_dualloop_sim.py` — PARTIAL, load-bearing. Rebuild as `dual_stack_carnot_szilard_hopf_weyl_probe`: same carrier, deductive+inductive loops, Carnot legality, Szilard measurement/reset, six controls.
5. `manifold_build_ladder.py` / `manifold_ladder_results.json` — PARTIAL. Start from `M(C)` finite relation tokens, compatibility, paths, obstructions; delay metric/chart/smooth overlays.
6. `sixteen_stage_engine_sim.py`, `engine_type_access_sim.py`, `engine_64_schedule_sim.py` — PARTIAL. Collapse into the newer `sixteen_stage_engine_schedule_sim.py` target, then add exact chart names, casing, loop traversal, and line-item 64 non-claims.
7. `admissibility_two_operator_sim.py` — PARTIAL. Upgrade P9 extraction: show exactly why two native operators per terrain follows from source constraints, not from chosen kernel table alone.
8. `holodeck_sim.py`, `agent_loop_sim.py`, `memory_sim.py` — PARTIAL. Supersede as active targets with `qit_fep_ratchet_sim.py`, `qit_active_inference_planning_sim.py`, `quantum_hopfield_memory_sim.py`, `spinor_memory_sim.py`, but rebuild against semantic trace/world-coupling source requirements.
9. `instrument_class_split_sim.py` — PARTIAL. Promote only after the independent live-loop packet is in the corpus with exact receipt, stream shape, and split observable.
10. `biochem_bridge_sim.py`, `evolution_chirality_bridge_sim.py`, `weak_force_chirality_bridge_sim.py` — PARTIAL. Split standard science reproduction from owner-bridge claims; add empirical-input fence and source-specific controls.
11. `division_algebra_ratchet_sim.py`, `octonion_spinor_network_sim.py`, `three_qubit_octonion_fep.py` — PARTIAL. Separate division algebra, network carrier, G2 action, and FEP into one-rung packets.
12. `signed_axis0_primitive_sim.py`, `terrain_sourcelock_axis0_sim.py`, `axis0_* JSON artifacts` — PARTIAL/negative. Keep as blockers: Axis0 must move out of terrain-local scalar probing into cut-state bridge extraction.

**Supersession Notes**
`STATE_OF_THE_MODEL.md` says “supersedes nothing, indexes everything,” so I would not mark any sim dead by decree. Practically, the active replacement targets are:

- Type1/dual-loop work narrows `engine_type_access_sim.py`, `engine_64_schedule_sim.py`, `sixteen_stage_engine_sim.py`, and `coupled_coratchet_dualloop_sim.py`.
- Live-loop / instrument-class work narrows `agent_loop_sim.py`, `holodeck_sim.py`, and generic FEP loop demos.
- Spinor-memory / Hopfield work narrows `memory_sim.py` and `axis0_spinor_720_sim.py`.
- `nonunitality_theorem_sim.py` supersedes the earlier interpretive force of `operator_geometry_fusion_sim.py`.

No files were changed; this was a read-only sweep.


