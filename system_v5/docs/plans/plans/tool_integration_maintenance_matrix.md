# Tool Integration Maintenance Matrix

Status: PRIMARY LIVE TOOL-DEPTH SURFACE

Goal: show which tools are already strong, which are shallow, where they belong in the sim program, and what bounded next move best deepens them.

Authority surfaces:
- `docs/TOOLING_STATUS.md`
- `docs/TOOL_MANIFEST_AUDIT.md`
- `docs/16_lego_build_catalog.md`
- `docs/17_actual_lego_registry.md`
- `docs/plans/plans/2026-04-18-tool-stage-plan.md`

## Current maturity snapshot

## Tool-capability lane rule

This matrix should now be read as part of a broader tool-capability lane, not only as an after-the-fact anchor list.

For each major tool family, the process goal is ideally to maintain three bounded surfaces:
1. a classical baseline / reference sim
2. a canonical tool-native counterpart
3. a comparison note showing what the tool adds beyond the baseline

Granularity rule:
- a tool-row status does not prove the whole library
- each important function/API surface needs its own micro receipt before it becomes load-bearing in a lego or tool-tool coupling
- every tool should choose useful bounded legos or minimal fixtures that expose that function's value
- tool-lego fit probes are pre-lego tool-stage work; they do not promote the lego
- tool-tool couplings require prior receipts for the exact functions being coupled

Interpretation rule:
- the tools and next moves named below are seed examples, not an exhaustive list of all valid packets
- when a nearby bounded packet better clarifies the same tool capability, the controller may choose it instead of rigidly following only the named examples
- current implementation selector: pick one proof/symbolic capability packet first (`z3`, `cvc5`, or `sympy`), pair it with the missing baseline/reference or canonical counterpart, then write the comparison note. If that is blocked, choose one graph/topology or geometry/equivariance packet with the same bounded baseline/counterpart/note shape.
- do not choose a stage-heavy integration, bridge, axis, engine, cascade, or whole-stack packet just because it is more salient.

| Tool | Repo-current maturity | Strong current anchor | Main weakness now | Best next bounded deepen move |
|---|---|---|---|---|
| PyTorch | core | `density_hopf_geometry_results.json` | still not universal substrate in all newer seams | keep using as default substrate for geometry spine packets |
| z3 | mature proof core | `hopf_torus_lego_results.json` | local admission/operator packets still thinner than they should be | direct `constraint_probe_admissibility` + operator packet pressure |
| sympy | established; load_bearing in base_loop_law and berry_holonomy as of 2026-04-12 4h-run | `foundation_hopf_torus_geomstats_clifford_results.json`, `toponetx_state_class_binding_results.json`, `base_loop_law_results.json`, and `berry_curvature_stokes_results.json` | sympy depth upgraded from supportive to load_bearing in base_loop_law (symbolic closure proof is a direct gate) and berry_holonomy (symbolic F=dA derivation is a direct gate); still not always used before numerics in later seams | continue requiring symbolic pass in geometry/operator packets; use as proof gate not just confirmation |
| clifford | specialized but real | `foundation_hopf_torus_geomstats_clifford_results.json` | local operator-family use still thin | explicit Pauli/Clifford/Weyl local packet |
| geomstats | specialized but real | `foundation_hopf_torus_geomstats_clifford_results.json` | good local geometry, but underused beyond that | same-carrier geometry + connection/holonomy packet |
| GUDHI | established topology with fresh direct persistence anchors | `gudhi_concurrence_filtration_results.json`, `hopf_torus_lego_results.json`, `persistence_geometry_results.json`, `sim_gudhi_rips_point_cloud_micro_results.json`, and `sim_gudhi_alpha_complex_micro_results.json` | SimplexTree, RipsComplex, and AlphaComplex now have narrow load-bearing receipts; broader graph/topology integration is still secondary to the main geometry spine | topology couplings and TopoNetX cross-checks only after exact downstream admission |
| XGI | established mid-ladder | `xgi_family_hypergraph_results.json` and `toponetx_state_class_binding_results.json` | has a real fresh rerun-backed TopoNetX/XGI anchor, but multi-way packet relations are still not central in late seams | deepen graph/topology packet on same carrier |
| rustworkx | established mid-ladder | bridge proof integration DAG | often broad support, not specific local load-bearing role | dependency/collapse and DAG ordering surfaces |
| PyG | shallow but real, with strict function receipts | `pyg_dynamic_edge_werner_results.json`, `geometric_constraint_manifold_pyg_results.json`, `foundation_equivariant_graph_backprop_results.json`, `sim_pyg_message_passing_autograd_micro_results.json`, and `sim_pyg_batching_micro_results.json` | PyG now has exact MessagePassing/autograd and Batch.from_data_list receipts plus narrow NetworkX/e3nn handoff receipts; broader graph-learning, HeteroData, density-matrix, and coexistence use remains separate | admit downstream graph-native rows only when they name the exact PyG parent receipt and do not widen to training or bridge claims |
| cvc5 | shallow but explicit proof-tool capability anchor | `cvc5_shells_crosscheck_results.json` | real and load-bearing in a narrow shell/fence cross-check lane with an explicit baseline-vs-canonical contract now recorded in the artifact, but still underused as a broader proving engine | promote the same contract into `constraint_probe_admissibility`: z3-only reference, cvc5 independent UNSAT cross-check, real SyGuS fence synthesis |
| e3nn | shallow but real, with strict function receipts | `density_hopf_geometry_results.json`, `e3nn_equivariant_qubits_results.json`, `e3nn_hopf_spinor_equivariance_results.json`, `sim_e3nn_irreps_tensor_product_micro_results.json`, and `sim_e3nn_spherical_harmonics_equivariance_micro_results.json` | Irreps/tensor-product and spherical-harmonics surfaces now have narrow load-bearing receipts, plus e3nn-PyG additive message equivariance; learned GNN, convolution, and operator-geometry promotion remain separate | geometry/operator equivariance packets only after exact parent receipt admission |
| TopoNetX | underused outlier but with strict cell-operation receipts | `toponetx_state_class_binding_results.json`, `cell_complex_geometry_results.json`, `sim_toponetx_cell_incidence_micro_results.json`, and `sim_toponetx_hodge_laplacian_micro_results.json` | CellComplex rank-2 incidence and CellComplex Hodge-Laplacian operation are real narrow receipts; graph-cell promotion, Hodge spectral agreement, dynamics, and coexistence/coupling use remain sparse | graph-cell or Hodge rows only after exact downstream admission and parent receipt naming |
| hdbscan | specialized but reconciled | `sim_hdbscan_umap_verdict_clustering.py` and `sim_integration_hdbscan_constraint_clustering.py` | ledger-only reconciliation DONE on 2026-05-02; not a rerun receipt and does not promote beyond existing truth labels; exact capability and integration anchors are usable only at their named scope, with stale failed duplicate verdict-clustering evidence excluded | no new clustering work before a named downstream target requires it |
| umap | specialized but reconciled | `sim_hdbscan_umap_verdict_clustering.py` and `sim_integration_umap_gtower_projection.py` | ledger-only reconciliation DONE on 2026-05-02; not a rerun receipt and does not promote beyond existing truth labels; exact capability and integration anchors are usable only at their named scope, with stale failed duplicate verdict-clustering evidence excluded | no new projection work before a named downstream target requires it |

## Claim-to-tool reminders

| Claim type | Required pressure |
|---|---|
| impossibility / fence / structural exclusion | z3, with cvc5 cross-check where relevant |
| symbolic identity / derived formula | sympy before numerics |
| geometric algebra / spinor transport / Pauli-Weyl local action | clifford |
| geodesic / metric / Frechet / holonomy manifold work | geomstats |
| graph-native dynamics | PyTorch + PyG |
| hypergraph / multi-way local structure | XGI |
| cell-complex / shell higher-order structure | TopoNetX |
| persistence / filtration evidence | GUDHI |
| dependency / ordering / DAG routing | rustworkx |
| equivariant carrier computation | e3nn |

## Immediate maintenance priorities
1. Per-tool baseline vs canonical pairing
- for each major tool family, identify whether the repo already has:
  - a baseline/reference packet
  - a canonical tool-native counterpart
  - a comparison note
- if any one of the three is missing, prefer a bounded packet that fills the missing role

2. Proof/symbolic tools
- deepen z3, cvc5, and sympy as explicit capability lanes rather than incidental imports
- best bounded moves: impossibility micro-probes, cross-check proofs, derivation micro-probes, SyGuS/fence synthesis
- choose one exact function/API surface per packet, such as one solver assertion pattern, one UNSAT certificate shape, one SyGuS synthesis target, or one symbolic simplification/identity check

3. Graph/topology tools
- deepen rustworkx, PyG, XGI, TopoNetX, and GUDHI as explicit capability lanes
- best bounded moves: DAG kernels, tensor-on-graph packets, hypergraph packets, cell-complex packets, persistence packets
- choose one graph operation or invariant per packet before coupling tools

4. Geometry/equivariance tools
- deepen clifford, e3nn, and geomstats as explicit capability lanes
- best bounded moves: rotor/spinor packets, equivariance packets, metric/geodesic packets
- choose one rotor, spinor, metric, geodesic, holonomy, or equivariance function per packet before stacking geometry claims

5. Honest second-wave tool-stage packets
- keep second-wave integrations below lego work
- verified 2026-04-18 current bounded candidates:
  - `sim_integration_networkx_rustworkx_crosscheck.py`
  - `sim_integration_geomstats_constraint_manifold.py`
- executed 2026-04-18 but stage-heavier than the clean Tier A default:
  - `sim_integration_toponetx_gtower_chain_complex.py`
  - keep as baseline/reference only unless it is rewritten to stay below tower-order / shortcut-law semantics

6. Coverage-lego tool-stage anchors
- use real bounded legos to exercise tool families honestly
- fresh verified examples:
  - `sim_gtower_reduction_obstruction_z3.py`
  - `sim_toponetx_hopf_crosscheck.py`
  - `sim_gudhi_deep_s3_hopf_torus_persistent_homology.py`
  - `sim_foundation_hopf_torus_geomstats_clifford.py`
- these are still tool-stage / coverage-stage work, not permission to start coupling

## Maintenance rule
After any meaningful batch:
- if a tool became newly load-bearing, update this matrix
- if a tool regressed to decorative use in promoted claims, record it here
- if a new sim exposes a better anchor for a tool, replace the weaker anchor
- keep the linked truth status in `system_v5/docs/plans/sim_truth_audit.md` aligned so tool-depth claims do not outrun the current safe truth label for the anchor file
- if the batch was run through the on-demand Telegram controller, include any tool-anchor change in the run closeout or explicitly queue the follow-up update before closure
- do not let a stage-heavy integration packet become the default next move just because it executed successfully
