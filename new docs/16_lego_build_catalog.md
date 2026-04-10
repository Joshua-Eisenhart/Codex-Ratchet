# Local Math Lego Ledger

Status: working execution ledger  
Date: 2026-04-08

## Purpose

This doc is the current working catalog of the legos the system needs.

It is not a theory essay.
It is not a raw sim dump.
It is not a bridge, Phi0, or axis plan.

It exists to answer:
- which pure-math or boundary legos must exist
- which already have a usable local anchor
- which still need deeper lego work
- which tool surfaces should be load-bearing for each lego
- which pairwise or coexistence successor each lego should feed next
- which legos are blocked from assembly even if they are useful

## Plain-English Notes

- `16` is not a math label.
- `16` only means this is the sixteenth numbered file in `new docs`.
- `lego` means a small, local, pure-math building block that should be simulated before bigger coupled or bridge surfaces.
- there are no “sub-legos”
- if one row hides multiple concrete math objects, those are separate legos and the row should be split
- If a row does not name the concrete math objects clearly enough, it is not doing its job.

## Authority Order

Use these surfaces in this order:

1. Machine artifacts
- `system_v4/probes/a2_state/sim_results/lego_stack_audit_results.json`
- `system_v4/probes/a2_state/sim_results/lego_coupling_candidates.json`
- `system_v4/probes/a2_state/sim_results/lego_batch_queue.json`
- `system_v4/probes/a2_state/sim_results/controller_alignment_audit_results.json`

2. Core execution docs
- `new docs/07_model_math_geometry_sim_plan.md`
- `new docs/08_aligned_sim_backlog_and_build_order.md`
- `new docs/LEGO_SIM_CONTRACT.md`
- `new docs/FALSIFICATION_SIM_DESIGNS.md`
- `new docs/ENFORCEMENT_AND_PROCESS_RULES.md`

3. Everything else
- useful only if it does not conflict with the surfaces above

## Scope Boundary

### What Counts As Lego

- local or tightly bounded pure-math structure
- carrier, geometry, operator, graph/topology, bipartite, or boundary-falsifier work
- can be useful even when rejected by the two root constraints
- must be understandable without appealing to bridge, bakeoff, or axis promotion logic

### What Does Not Count As Lego

| Surface | Why It Is Not A Lego |
| --- | --- |
| `dependency_dag_and_collapse` | coupling/build-order analysis surface |
| `viability_vs_attractor_falsifier` | falsifier surface, but not part of the default lego ladder |
| `axis_entry_after_admission` | explicitly later than the lego stack |
| bridge / cut / kernel / Phi0 files | late-object or seam surfaces |
| bakeoffs / audits / packets / validations | controller or comparison surfaces, not foundational math objects |

## Build Rules

- A lego is local or tightly bounded. It is not a bridge, bakeoff, packet, audit, integrated pipeline, or axis-entry surface.
- Root-killed or rejected sims are useful. Keep them as evidence surfaces.
- A lego does not promote because it exists. It promotes only if the result is clear, scoped, and tool-honest.
- A tool only counts if it is load-bearing or clearly supportive in the real execution path.
- Pairwise and coexistence work come after the lego is real.
- Assembly does not consume a lego just because the lego passed once.

## Label Systems

### Lego Status

- `covered`: there is at least one good current lego probe
- `partial`: there is real lego work, but the lego is still thinner than it should be
- `needs_deeper_lego_work`: current candidates exist, but the lego is not strong enough yet
- `ready_for_pairwise`: there is already a real successor path
- `blocked_from_assembly`: useful lego, but not allowed to feed assembly yet

### Queue State

- `ready_now`: safe to run next
- `ready_but_supporting_only`: queueable, but current successor is still only supporting
- `blocked_on_lego`: do not move upward yet
- `blocked_from_assembly`: do not move upward at all

### Result Truth

- `exists`
- `runs locally`
- `passes local rerun`
- `canonical by process`

## Master Lego Ledger

This is the widest operator-facing table in the doc.
Use it when deciding what lego to build next, what math it contains, and how to simulate it without jumping upward too early.

| Lego ID | Lego Name | Build Stage | Core Math Object | Full Math | Source Docs | Why It Matters | Useful If Rejected | How To Sim It | Best Current Local Anchor | Tools To Try | Preferred Load-Bearing Tools | Shallow Tool Pressure To Force Early | Best Next Successor | Queue State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `constraint_probe_admissibility` | Constraint and probe admissibility | lego | admissibility fences and root-constraint boundary | admissible probe families, guard conditions, fence pressure, lower-shell exclusion surfaces | `07`, `08`, `LEGO_SIM_CONTRACT` | stops illegal legos from polluting the stack | yes | build small guard/fence probes and prove boundary kills before richer shells | `bridge_entropy_inequality_guardrails_results.json` as evidence only; no clean default lego anchor yet | `z3`, `cvc5`, `sympy`, `pytorch` | `z3` | `cvc5` | `sim_constraint_shells_binding_crosscheck.py` | `blocked_on_lego` |
| `carrier_admission_density_matrix` | Carrier admission and density-matrix representability | lego | density matrices on finite carriers | positivity, trace-one normalization, representability, admissible carrier choice | `07`, `08` | everything above this assumes the carrier is real | yes | start with finite density carriers, vary admissible forms, keep trace/positivity exact | `density_hopf_geometry_results.json` | `pytorch`, `sympy`, `z3` | `pytorch`, `sympy` | none | `sim_integrated_dependency_chain.py` and `sim_operator_geometry_compatibility.py` | `ready_now` |
| `geometry_crosschecks_same_carrier` | Geometry cross-checks on the same carrier | lego | multiple geometries on one admitted carrier | Hopf, torus, Berry phase, QFI, QGT, holonomy, same-carrier metric comparisons | `07`, `08` | kills geometry smuggling and flat-only shortcuts | yes | hold the carrier fixed and compare geometric invariants under multiple geometry choices | `foundation_hopf_torus_geomstats_clifford_results.json` | `geomstats`, `clifford`, `sympy`, `pytorch`, `z3`, `gudhi` | `geomstats`, `clifford` | `e3nn` | `sim_operator_geometry_compatibility.py` and `sim_compound_operator_geometry.py` | `ready_now` |
| `operator_family_admission` | Operator admission lego | lego | local operator and channel legos before assembly | Pauli, Clifford, commutator, chirality, channel-local operator action | `07`, `08`, `FALSIFICATION_SIM_DESIGNS` | prevents later operator stories from skipping local admission | yes | apply local operators and local channels to admitted carriers/geometries and kill collapsed or symmetric-only cases | no clean default local anchor yet | `clifford`, `sympy`, `z3`, `pytorch`, `e3nn` | `clifford`, `sympy`, `z3` | `e3nn` | `sim_operator_geometry_compatibility.py` | `blocked_on_lego` |
| `graph_cell_complex_geometry` | Graph and cell-complex carrier geometry | lego | graph, hypergraph, cell-complex, persistence views | graph, hypergraph, cell-complex, topology and differentiable graph views on the same carrier | `07`, `08` | gives multi-view local structure before late integration | yes | map one admitted carrier into graph, hypergraph, and cell-complex forms and compare what survives | `xgi_family_hypergraph_results.json` and `foundation_equivariant_graph_backprop_results.json` | `xgi`, `toponetx`, `pyg`, `gudhi`, `pytorch`, `rustworkx` | `xgi`, `pytorch` | `pyg`, `toponetx` | `sim_xgi_indirect_pathway.py`, `sim_toponetx_state_class_binding.py`, `sim_pyg_dynamic_edge_werner.py` | `ready_now` |
| `bipartite_structure_local` | Bipartite structure lego set | lego | local bipartite reductions and witnesses | partial trace, reduced states, concurrence, negativity, Werner and Schmidt-style local structure | `07`, `08` | gives local entanglement structure without seam claims | yes | stay local to bipartite reductions and witness families before wider bridge or entropy promotion | `gudhi_concurrence_filtration_results.json` | `gudhi`, `pyg`, `sympy`, `pytorch`, `z3` | `gudhi` | `pyg` | `sim_pyg_dynamic_edge_werner.py` and `sim_lego_entropy_bipartite_cut.py` | `ready_now` |
| `entropy_family_crosschecks` | Entropy cross-check lego | lego | local entropy and information summaries | von Neumann, mutual, coherent, conditional, Renyi/Tsallis/min-max style comparisons | `07`, `08` | keeps entropy later and subordinate to stronger local structure | yes | compare entropy summaries locally and reject any summary that tries to dominate before lower-lego support exists | no clean local anchor yet | `sympy`, `pytorch`, `z3` | `sympy`, `pytorch` | none | none yet | `blocked_on_lego` |
| `gauge_group_falsifier` | Gauge-group correspondence falsifier | boundary lego | symmetry/gauge kill surface | Lie algebra, commutator, projective/group geometry falsifier against over-strong correspondence claims | `FALSIFICATION_SIM_DESIGNS` | useful because a clean kill is stronger than vague symbolic similarity | yes | build small algebra/geometry falsifiers and keep the negative result as the product | `geom_cp1_u1_projective_results.json` | `sympy`, `pytorch`, geometry stack | `sympy` | none | none | `blocked_from_assembly` |
| `quantum_metric_nonuniqueness` | Quantum metric nonuniqueness lego | boundary lego | metric-choice pressure surface | compare alternative quantum metrics and phase-space views without assuming one primitive | `FALSIFICATION_SIM_DESIGNS`, `08` | forces the system to admit metric choice is structure, not doctrine | yes | run the same state set through multiple metric choices and keep disagreement as evidence | `geomstats_shell_metrics_results.json` | `geomstats`, `sympy`, `pytorch` | `geomstats` | none | none | `blocked_from_assembly` |

## Concrete Math In Each Lego

This table is the direct answer to “what kinds of geometry and math are actually inside each lego?”

| Lego ID | Concrete Geometry Types | Concrete Math Types | Smallest Honest Sim Shape |
| --- | --- | --- | --- |
| `constraint_probe_admissibility` | boundary surfaces, shell fences, admissibility regions | inequalities, satisfiability, exclusion conditions, guard predicates, lower-shell boundary tests | tiny state/probe sets with explicit admissibility and impossibility checks |
| `carrier_admission_density_matrix` | density-state carrier space, finite state manifolds | density matrices, positivity, trace-one normalization, eigenvalue admissibility, reduced-state consistency | smallest valid density families with exact positivity/trace checks |
| `geometry_crosschecks_same_carrier` | Hopf fibration, torus geometry, projective geometry, Berry geometry, QFI/QGT geometry, holonomy geometry | Berry phase, quantum Fisher information, quantum geometric tensor, connection/transport quantities, metric comparison on one carrier | one admitted carrier viewed through several geometries without changing the underlying state |
| `operator_family_admission` | operator action on local carrier/geometry, channel-local geometry | Pauli operators, Clifford operators, commutators, chirality operators, local channels, operator-induced symmetry breaking | apply primitive operators and local channels to local states and test what survives or collapses |
| `graph_cell_complex_geometry` | graph geometry, hypergraph geometry, cell-complex geometry, persistence/topology views | adjacency structure, hyperedges, cells, homology-sensitive structure, differentiable graph embeddings | encode the same local carrier as graph, hypergraph, and cell complex and compare preserved structure |
| `bipartite_structure_local` | two-party state geometry, bipartite cut geometry, witness geometry | partial trace, reduced density matrices, concurrence, negativity, Schmidt structure, Werner local witnesses | small bipartite states with local witness and reduction comparisons |
| `entropy_family_crosschecks` | entropy/readout geometry on fixed local states | von Neumann entropy, mutual information, coherent information, conditional entropy, Renyi/Tsallis/min-max summaries | same bounded state set measured by several entropy summaries before any bridge claim |
| `gauge_group_falsifier` | projective geometry, group-manifold geometry, algebra-vs-geometry comparison surfaces | Lie algebra, commutator algebra, projective correspondence tests, symmetry falsifiers | smallest explicit counterexample to an over-strong gauge/group identification |
| `quantum_metric_nonuniqueness` | metric manifolds, phase-space geometry, alternative quantum geometry surfaces | Bures-type metrics, Fubini-Study-type metrics, QFI-derived metrics, phase-space comparisons, metric disagreement tests | same state set run through multiple metric choices and compared for qualitative disagreement |

## Bundled Rows That Should Become Separate Legos

These are not “sub-legos.”
They are separate legos that are still incorrectly bundled together in the current ledger.

| Current Bundled Row | Separate Legos Hidden Inside It |
| --- | --- |
| `geometry_crosschecks_same_carrier` | `hopf_torus_geometry`, `berry_phase_geometry`, `qfi_qgt_geometry`, `holonomy_transport_geometry` |
| `operator_family_admission` | `pauli_operator_family`, `clifford_operator_family`, `commutator_algebra_family`, `local_channel_family`, `chirality_operator_family` |
| `graph_cell_complex_geometry` | `graph_geometry`, `hypergraph_geometry`, `cell_complex_geometry`, `persistence_geometry` |
| `bipartite_structure_local` | `partial_trace_family`, `reduced_state_family`, `concurrence_family`, `negativity_family`, `schmidt_structure_family`, `werner_local_family` |
| `entropy_family_crosschecks` | `von_neumann_entropy_family`, `mutual_information_family`, `coherent_information_family`, `conditional_entropy_family`, `renyi_tsallis_family`, `min_max_entropy_family` |
| `quantum_metric_nonuniqueness` | `bures_metric_family`, `fubini_study_family`, `qfi_metric_family`, `phase_space_metric_family` |

## Lego Inventory

### Core Local Legos

| Lego ID | Build Stage | Math Object | Source Docs | Useful If Rejected | Best Current Anchor | Lego Status | Queue State | Assembly Gate | Primary Tool Pressure | Best Next Successor | Main Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `constraint_probe_admissibility` | lego | admissibility fences, probe guards, root-constraint boundary | `07`, `08`, `LEGO_SIM_CONTRACT` | yes | `bridge_entropy_inequality_guardrails_results.json` as evidence only; no clean default lego probe yet | `needs_deeper_lego_work` | `blocked_on_lego` | `pairwise_only` | `z3`, later `cvc5` | `sim_constraint_shells_binding_crosscheck.py` | current local probe set is thin and the queue still blocks upward motion |
| `carrier_admission_density_matrix` | lego | density matrices, positivity, trace, normalization, carrier admission | `07`, `08` | yes | `density_hopf_geometry_results.json` | `partial` | `ready_now` | `pairwise_only` | `pytorch`, `sympy` | `sim_integrated_dependency_chain.py`, `sim_operator_geometry_compatibility.py` | only one strong default lego anchor so far |
| `geometry_crosschecks_same_carrier` | lego | Hopf, Berry, QFI, QGT, holonomy, same-carrier metric comparisons | `07`, `08` | yes | `foundation_hopf_torus_geomstats_clifford_results.json` | `covered` | `ready_now` | `safe_for_coexistence` | `geomstats`, `clifford`, `sympy` | `sim_operator_geometry_compatibility.py`, `sim_compound_operator_geometry.py` | one successor is still only supporting |
| `operator_family_admission` | lego | Pauli, Clifford, commutator, channel, chirality operator behavior before assembly | `07`, `08`, `FALSIFICATION_SIM_DESIGNS` | yes | no clean default local anchor yet | `needs_deeper_lego_work` | `blocked_on_lego` | `pairwise_only` | `clifford`, `sympy`, `z3` | `sim_operator_geometry_compatibility.py` | current best successor is supporting-only and the lego layer is weak |

### Graph / Topology Legos

| Lego ID | Build Stage | Math Object | Source Docs | Useful If Rejected | Best Current Anchor | Lego Status | Queue State | Assembly Gate | Primary Tool Pressure | Best Next Successor | Main Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `graph_cell_complex_geometry` | lego | graph, hypergraph, cell-complex, persistence views on the same carrier | `07`, `08` | yes | `xgi_family_hypergraph_results.json` and `foundation_equivariant_graph_backprop_results.json` | `covered` | `ready_now` | `safe_for_coexistence` | `pyg`, `toponetx` | `sim_xgi_indirect_pathway.py`, `sim_toponetx_state_class_binding.py`, `sim_pyg_dynamic_edge_werner.py` | shallow tool pressure is still concentrated in `pyg` and `toponetx` |

### Bipartite / Information Legos

| Lego ID | Build Stage | Math Object | Source Docs | Useful If Rejected | Best Current Anchor | Lego Status | Queue State | Assembly Gate | Primary Tool Pressure | Best Next Successor | Main Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bipartite_structure_local` | lego | partial trace, concurrence, negativity, Schmidt/Werner local structure | `07`, `08` | yes | `gudhi_concurrence_filtration_results.json` | `covered` | `ready_now` | `safe_for_coexistence` | `pyg`, `gudhi`, `sympy` | `sim_pyg_dynamic_edge_werner.py`, `sim_lego_entropy_bipartite_cut.py` | local lego is strong, but `pyg` still needs more mid-ladder depth |
| `entropy_family_crosschecks` | lego | local entropy cross-check before bridge or axis promotion | `07`, `08` | yes | no clean local anchor yet; current strongest evidence is later-stage and should not stand in for lego completion | `needs_deeper_lego_work` | `blocked_on_lego` | `blocked_from_assembly` | `sympy`, `pytorch` | none yet | still too tied to later surfaces and explicitly blocked from assembly |

### Boundary / Falsifier Legos

| Lego ID | Build Stage | Math Object | Source Docs | Useful If Rejected | Best Current Anchor | Lego Status | Queue State | Assembly Gate | Primary Tool Pressure | Best Next Successor | Main Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gauge_group_falsifier` | boundary lego | gauge / Lie / commutator falsifier against over-strong group correspondences | `FALSIFICATION_SIM_DESIGNS` | yes | `geom_cp1_u1_projective_results.json` | `covered` | `blocked_from_assembly` | `blocked_from_assembly` | `sympy`, geometry stack | none | should remain a kill surface, not feed the main assembly ladder |
| `quantum_metric_nonuniqueness` | boundary lego | pressure-test nonunique quantum metric choices without smuggling one geometry as primitive | `FALSIFICATION_SIM_DESIGNS`, `08` | yes | `geomstats_shell_metrics_results.json` | `covered` | `blocked_from_assembly` | `blocked_from_assembly` | `geomstats`, `sympy` | none | useful pressure surface, but should remain a boundary/selective lego until lower metric-choice effects are cleaner |

## Doc-Extracted Legos Not Yet Fully Normalized Into The Machine Ledger

These legos appear clearly in `new docs`, but they are not yet cleanly represented as standalone lego rows in the current machine routing surfaces.

| Extracted Lego ID | Plain-English Lego | Core Math Object | Source Docs | Useful If Rejected | Current Relationship To Active Ledger | What Still Needs To Happen |
| --- | --- | --- | --- | --- | --- | --- |
| `state_representation_class` | state representation lego | density matrix / Bloch / coherence vector / purification / spectrum / Stokes views | `07`, `08` | yes | partly absorbed into `carrier_admission_density_matrix` | split out if representation-level differences matter independently of carrier admission |
| `quantum_metric_family` | quantum metric lego | trace distance / Bures / Fubini-Study / QFI / QGT / Berry-holonomy metrics | `07`, `08`, `FALSIFICATION_SIM_DESIGNS` | yes | split between `geometry_crosschecks_same_carrier` and `quantum_metric_nonuniqueness` | decide whether to keep as one metric lego or two legos: local geometry vs boundary-pressure |
| `channel_cptp_dynamics` | channel and CPTP dynamics lego | CPTP maps, channels, instruments, commutator-sensitive dynamics | `07`, `08` | yes | partly absorbed into `operator_family_admission` | promote to its own lego row if channel-local work becomes deeper than generic operator admission |
| `symmetry_algebra_falsifier` | symmetry algebra falsifier | operator Lie algebra generated by commutators | `FALSIFICATION_SIM_DESIGNS`, `08` | yes | near-duplicate of `gauge_group_falsifier` | normalize naming and either merge cleanly or split by algebra-vs-geometry role |
| `correlation_measure_family` | correlation and witness lego | correlation tensors, mutual information, coherent information, concurrence, negativity | `07`, `08` | no | partly absorbed into `bipartite_structure_local` and `entropy_family_crosschecks` | split local witness work from later entropy-lego comparisons more cleanly |
| `decomposition_compression_family` | decomposition and compression lego | Schmidt decomposition, SVD, principal-subspace truncation, low-rank approximation | `08` | no | not yet routed as its own lego row | decide whether it is a real lego or only a support method inside bipartite/state-representation work |
| `trajectory_viability_family` | viability-vs-attractor lego | trajectory geometry under repeated constrained evolution | `FALSIFICATION_SIM_DESIGNS` | no | currently outside the default lego ladder | keep separate unless it becomes a bounded local falsifier lego rather than a later dynamics surface |

## Probe Inventory

### Carrier / Geometry Probes

| Lego ID | Probe File | Likely Result File | Probe Role | Evidence Level Now | Load-Bearing Tools | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `carrier_admission_density_matrix` | `sim_density_hopf_geometry.py` | `density_hopf_geometry_results.json` | carrier admission anchor | `canonical by process` | `pytorch`, `sympy` | current best local carrier anchor |
| `geometry_crosschecks_same_carrier` | `sim_foundation_hopf_torus_geomstats_clifford.py` | `foundation_hopf_torus_geomstats_clifford_results.json` | same-carrier geometry anchor | `canonical by process` | `geomstats`, `clifford` | strongest current geometry lego |
| `geometry_crosschecks_same_carrier` | `sim_berry_qfi_entangled_path.py` | `berry_qfi_entangled_path_results.json` | Berry/QFI path comparison | `canonical by process` | `pytorch`, `sympy`, `z3` | useful same-carrier path pressure |
| `geometry_crosschecks_same_carrier` | `sim_berry_qfi_shell_paths.py` | `berry_qfi_shell_paths_results.json` | shell-path geometry comparison | `canonical by process` | `pytorch`, `sympy` | feeds the compound successor path |
| `geometry_crosschecks_same_carrier` | `sim_hopf_torus_lego.py` | `hopf_torus_lego_results.json` | local Hopf/torus geometry lego | `canonical by process` | `pytorch`, `z3`, `geomstats`, `gudhi`, `clifford` | rich local geometry lego |

### Graph / Topology Probes

| Lego ID | Probe File | Likely Result File | Probe Role | Evidence Level Now | Load-Bearing Tools | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `graph_cell_complex_geometry` | `sim_foundation_equivariant_graph_backprop.py` | `foundation_equivariant_graph_backprop_results.json` | graph/equivariant foundation lego | `canonical by process` | `pytorch`, `pyg` | strongest current PyG-linked local anchor |
| `graph_cell_complex_geometry` | `sim_xgi_dual_hypergraph.py` | `xgi_dual_hypergraph_results.json` | dual hypergraph local structure | `canonical by process` | `xgi` | useful local multi-way anchor |
| `graph_cell_complex_geometry` | `sim_xgi_family_hypergraph.py` | `xgi_family_hypergraph_results.json` | local hypergraph anchor | `canonical by process` | `xgi`, `pytorch` | current best XGI lego anchor |
| `graph_cell_complex_geometry` | `sim_xgi_shell_hypergraph.py` | `xgi_shell_hypergraph_results.json` | shell-aware hypergraph topology | `canonical by process` | `xgi` | strongest topology-side XGI anchor |
| `graph_cell_complex_geometry` | `sim_foundation_shell_graph_topology.py` | `foundation_shell_graph_topology_results.json` | shell graph / cell-complex anchor | `runs locally` to `passes local rerun` but thinner than the best graph anchors | `toponetx`, `pytorch` | important because it feeds `toponetx_state_class_binding` |

### Bipartite / Entanglement Probes

| Lego ID | Probe File | Likely Result File | Probe Role | Evidence Level Now | Load-Bearing Tools | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `bipartite_structure_local` | `sim_gudhi_bipartite_entangled.py` | `gudhi_bipartite_entangled_results.json` | local bipartite topology witness | `canonical by process` | `gudhi`, `pytorch` | good local topology witness |
| `bipartite_structure_local` | `sim_gudhi_concurrence_filtration.py` | `gudhi_concurrence_filtration_results.json` | concurrence filtration lego | `canonical by process` | `gudhi` | strongest local bipartite anchor |
| `bipartite_structure_local` | `sim_pyg_dynamic_edge_werner.py` | `pyg_dynamic_edge_werner_results.json` | narrow differentiable successor that still teaches local structure | `canonical by process` | `pyg`, `z3`, `pytorch`, `rustworkx`, `xgi` | useful because it also deepens a shallow tool |

### Boundary / Falsifier / Metric Probes

| Lego ID | Probe File | Likely Result File | Probe Role | Evidence Level Now | Load-Bearing Tools | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `gauge_group_falsifier` | `sim_geom_cp1_u1_projective.py` | `geom_cp1_u1_projective_results.json` | gauge/projective falsifier | `canonical by process` | `pytorch`, `sympy` | keep as a kill surface |
| `gauge_group_falsifier` | `sim_geom_su2_so3_quaternions.py` | `geom_su2_so3_quaternions_results.json` | group geometry falsifier | `canonical by process` | `pytorch`, `clifford` | strong boundary geometry pressure |
| `quantum_metric_nonuniqueness` | `sim_geomstats_shell_metrics.py` | `geomstats_shell_metrics_results.json` | metric nonuniqueness pressure test | `canonical by process` | `geomstats`, `pytorch` | current best metric-pressure anchor |
| `quantum_metric_nonuniqueness` | `sim_lego_weyl_wigner_phase_space.py` | `lego_weyl_wigner_phase_space_results.json` | alternate metric/phase-space pressure | `canonical by process` | `pytorch` | useful because disagreement is informative |

## Successor Routing

| Lego ID | Current Best Lego Probe | Best Existing Successor | Evidence State | Safe Next Stage | Tool Pressure | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `carrier_admission_density_matrix` | `sim_density_hopf_geometry.py` | `sim_integrated_dependency_chain.py` | `promotion_ready` | `coupling` | none | stronger than the operator-compatibility path right now |
| `carrier_admission_density_matrix` | `sim_density_hopf_geometry.py` | `sim_operator_geometry_compatibility.py` | `usable_but_supporting` | `coupling` | none | useful, but not closure-grade yet |
| `geometry_crosschecks_same_carrier` | `sim_foundation_hopf_torus_geomstats_clifford.py` | `sim_operator_geometry_compatibility.py` | `usable_but_supporting` | `coupling` | none | default operator compatibility lane |
| `geometry_crosschecks_same_carrier` | `sim_berry_qfi_shell_paths.py` | `sim_compound_operator_geometry.py` | `usable_but_supporting` | `coupling` | none | specifically useful for Berry/QFI geometry follow-on |
| `graph_cell_complex_geometry` | `sim_xgi_family_hypergraph.py` | `sim_xgi_indirect_pathway.py` | `promotion_ready` | `coexistence` | `toponetx` | best XGI mid-ladder explanation anchor |
| `graph_cell_complex_geometry` | `sim_foundation_shell_graph_topology.py` | `sim_toponetx_state_class_binding.py` | `promotion_ready` | `coexistence` | `toponetx` | best TopoNetX follow-on |
| `graph_cell_complex_geometry` | `sim_foundation_equivariant_graph_backprop.py` | `sim_pyg_dynamic_edge_werner.py` | `promotion_ready` | `coexistence` | `pyg`, `toponetx` | most useful shallow-tool deepen row |
| `bipartite_structure_local` | `sim_gudhi_concurrence_filtration.py` | `sim_pyg_dynamic_edge_werner.py` | `promotion_ready` | `coexistence` | `pyg` | strongest cross-tool successor |
| `bipartite_structure_local` | `sim_gudhi_bipartite_entangled.py` | `sim_lego_entropy_bipartite_cut.py` | `partial_anchor` | `coexistence` | `pyg` | useful successor, but less central than the PyG lane |
| `constraint_probe_admissibility` | `no clean default probe yet` | `sim_constraint_shells_binding_crosscheck.py` | `partial_anchor` | `coupling` | none | queue still blocks upward motion because the lego layer is not clean enough |
| `operator_family_admission` | `no clean default probe yet` | `sim_operator_geometry_compatibility.py` | `usable_but_supporting` | `coupling` | none | real successor exists, but not closure-grade |
| `entropy_family_crosschecks` | `none yet` | `none yet` | `blocked_on_lego` | none | none | stay local until a clean entropy lego exists |
| `gauge_group_falsifier` | `sim_geom_cp1_u1_projective.py` | `none` | `blocked_from_assembly` | none | none | preserve as falsifier evidence only |
| `quantum_metric_nonuniqueness` | `sim_geomstats_shell_metrics.py` | `none` | `blocked_from_assembly` | none | none | preserve as selection pressure only |

## Tool Pressure

### Tool Maturity For The Lego Program

| Tool | Tool Maturity | Current Strong Anchor | Weakest Stage Now | Best Next Lego | Best Next Successor |
| --- | --- | --- | --- | --- | --- |
| `pytorch` | core | `density_hopf_geometry_results.json` | none; already cross-stage | all lego families | already everywhere |
| `z3` | mature proof core | `hopf_torus_lego_results.json` | pairwise/local operator pressure is thinner than proof coverage | `constraint_probe_admissibility`, `operator_family_admission` | `sim_constraint_shells_binding_crosscheck.py` |
| `sympy` | established | `berry_qfi_entangled_path_results.json` | graph/topology use is narrower than carrier/geometry use | `geometry_crosschecks_same_carrier` | `sim_compound_operator_geometry.py` |
| `rustworkx` | established mid-ladder | `rustworkx_family_dag_results.json` | local lego stage | not a first lego target here | later dependency/collapse surfaces |
| `xgi` | established mid-ladder | `xgi_family_hypergraph_results.json` | local-only route is already decent | `graph_cell_complex_geometry` | `sim_xgi_indirect_pathway.py` |
| `gudhi` | established topology | `gudhi_concurrence_filtration_results.json` | local carrier geometry | `bipartite_structure_local` | `sim_gudhi_concurrence_filtration.py` |
| `geomstats` | specialized but real | `geomstats_shell_metrics_results.json` | local geometry still narrower than coexistence/topology pressure | `geometry_crosschecks_same_carrier`, `quantum_metric_nonuniqueness` | `sim_foundation_hopf_torus_geomstats_clifford.py` |
| `clifford` | specialized but real | `foundation_hopf_torus_geomstats_clifford_results.json` | local operator-family use is still thin | `operator_family_admission` | future local operator algebra sims |
| `pyg` | shallow | `foundation_equivariant_graph_backprop_results.json` | lego and pairwise | `graph_cell_complex_geometry`, `bipartite_structure_local` | `sim_pyg_dynamic_edge_werner.py` |
| `cvc5` | shallow proof cross-check | `cvc5_shells_crosscheck_results.json` | lego and pairwise | `constraint_probe_admissibility` | future stronger admissibility/fence lego |
| `e3nn` | shallow but real | `e3nn_equivariant_qubits_results.json` | lego and pairwise | geometry/operator legos | future richer local equivariance lego |
| `toponetx` | shallow topology specialist | `toponetx_state_class_binding_results.json` | lego and pairwise | `graph_cell_complex_geometry` | `sim_toponetx_state_class_binding.py` |

## Queue Ledger

### Ready Now

| Queue Rank | Task ID | Lego | Target Stage | Recommended Sim | Depends On | Queue State | Tool Pressure | Stop Rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `p2` | `lego-batch-007` | `graph_cell_complex_geometry` | `coexistence` | `sim_pyg_dynamic_edge_werner.py` | `sim_foundation_equivariant_graph_backprop.py` | `ready_now` | `pyg`, `toponetx` | stop if shallow-tool pressure is not increased at the target stage |
| `p2` | `lego-batch-008` | `bipartite_structure_local` | `coexistence` | `sim_pyg_dynamic_edge_werner.py` | `sim_gudhi_concurrence_filtration.py` | `ready_now` | `pyg` | stop if shallow-tool pressure is not increased at the target stage |
| `p2` | `lego-batch-009` | `bipartite_structure_local` | `coexistence` | `sim_lego_entropy_bipartite_cut.py` | `sim_gudhi_bipartite_entangled.py` | `ready_now` | `pyg` | stop if shallow-tool pressure is not increased at the target stage |
| `p4` | `lego-batch-005` | `graph_cell_complex_geometry` | `coexistence` | `sim_xgi_indirect_pathway.py` | `sim_xgi_family_hypergraph.py` | `ready_now` | `toponetx` | stop if shallow-tool pressure is not increased at the target stage |
| `p4` | `lego-batch-006` | `graph_cell_complex_geometry` | `coexistence` | `sim_toponetx_state_class_binding.py` | `sim_foundation_shell_graph_topology.py` | `ready_now` | `toponetx` | stop if shallow-tool pressure is not increased at the target stage |
| `p7` | `lego-batch-001` | `carrier_admission_density_matrix` | `coexistence` | `sim_operator_geometry_compatibility.py` | `sim_density_hopf_geometry.py` | `ready_now` | none | stop if no new pairwise/coexistence evidence is produced |
| `p7` | `lego-batch-002` | `carrier_admission_density_matrix` | `coexistence` | `sim_integrated_dependency_chain.py` | `sim_density_hopf_geometry.py` | `ready_now` | none | stop if no new pairwise/coexistence evidence is produced |
| `p7` | `lego-batch-003` | `geometry_crosschecks_same_carrier` | `topology` | `sim_operator_geometry_compatibility.py` | `sim_foundation_hopf_torus_geomstats_clifford.py` | `ready_now` | none | stop if no new pairwise/coexistence evidence is produced |

### Ready But Supporting Only

| Queue Rank | Task ID | Lego | Target Stage | Recommended Sim | Depends On | Queue State | Blocked By | Stop Rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `p6` | `lego-batch-004` | `geometry_crosschecks_same_carrier` | `coupling` | `sim_compound_operator_geometry.py` | `sim_berry_qfi_shell_paths.py` | `ready_but_supporting_only` | `successor_only_supporting` | stop if successor remains supporting-only after schema/truth hardening |

### Blocked On Lego

| Queue Rank | Task ID | Lego | Target Stage | Recommended Sim | Queue State | Blocked By | Stop Rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `p6` | `lego-batch-011` | `operator_family_admission` | `coupling` | `sim_operator_geometry_compatibility.py` | `blocked_on_lego` | `deeper_lego_work_needed`, `successor_only_supporting` | stop if successor remains supporting-only after schema/truth hardening |
| `p7` | `lego-batch-010` | `constraint_probe_admissibility` | `coupling` | `sim_constraint_shells_binding_crosscheck.py` | `blocked_on_lego` | `deeper_lego_work_needed` | stop if no new pairwise/coexistence evidence is produced |
| `p9` | `lego-batch-012` | `entropy_family_crosschecks` | `coupling` | none | `blocked_on_lego` | `deeper_lego_work_needed`, `blocked_until_better_lego` | stop here; do not feed assembly until blocking lego condition is resolved |

### Blocked From Assembly

| Queue Rank | Task ID | Lego | Target Stage | Queue State | Blocked By | Stop Rule |
| --- | --- | --- | --- | --- | --- | --- |
| `p9` | `lego-batch-013` | `gauge_group_falsifier` | `coupling` | `blocked_from_assembly` | `blocked_from_assembly` | stop here; do not feed assembly until blocking lego condition is resolved |
| `p9` | `lego-batch-014` | `quantum_metric_nonuniqueness` | `coupling` | `blocked_from_assembly` | `blocked_from_assembly` | stop here; do not feed assembly until blocking lego condition is resolved |

## Current Build Order

1. finish the weak legos first:
- `constraint_probe_admissibility`
- `operator_family_admission`
- `entropy_family_crosschecks`
- `carrier_admission_density_matrix`

2. deepen the shallow tools at lego and pairwise stages:
- `pyg`
- `cvc5`
- `e3nn`
- `toponetx`

3. run the ready-now queue before new bridge or axis work

4. keep root-killed legos and falsifiers as retained evidence, not as discarded failures

## Commands

- `make lego-audit`
- `make lego-coupling`
- `make lego-queue`

Bot read-only views:
- `lego`
- `pairs`
- `queue`
- `sims`

## Bottom Line

The current program should be:

1. build or strengthen all local legos
2. force honest tool integration per lego
3. run the queued pairwise and coexistence successors
4. only then widen into topology reruns, seam work, and assembly
