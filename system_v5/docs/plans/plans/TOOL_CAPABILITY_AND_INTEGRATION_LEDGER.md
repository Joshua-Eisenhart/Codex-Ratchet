# Tool Capability and Integration Ledger

Date: 2026-04-14  
Status: living ledger — update when probes run or integration sims are added  
Authority: tracks `system_v4/probes/sim_capability_*.py` and `sim_integration_*.py` as of this session

Planning companion:
- `system_v5/docs/plans/plans/2026-04-18-tool-stage-plan.md`

## How to Read

- **Capability probe file**: path relative to `system_v4/probes/`, or `none` if absent
- **Capability probe status**: one of the four canonical labels (`exists / runs / passes local rerun / canonical by process`), or `never-run` / `none`
- **Integration sims count**: count of `sim_integration_*<tool>*` files found at `system_v4/probes/`
- **Integration depth**: `load_bearing confirmed` (tool drives a structural test), `superficial` (used but not structural), or `none` / `unverified`
- **Next step**: what is actually needed before this tool is in good standing

Status `unverified` = file exists but run status was not confirmed this session.

Important granularity rule: a tool row is not a blanket proof of the whole library. Treat every capability or integration claim as scoped to the exact function/API surface and test shape named by its probe. Before a tool function becomes load-bearing in a lego-stage claim or a tool-tool coupling, it needs a micro receipt: one function, one bounded lego target or minimal fixture, one positive case, one negative case, one boundary case, and one demotion condition. Tool-lego fit probes are pre-lego tool-stage evidence; they do not promote the lego.

Schema upgrade target: future ledger rows should track `function/API surface`, `useful_lego_anchor`, `individual_receipt`, `eligible_for_tool_tool_coupling`, and `last_demoted_by`. Until that schema exists, record those facts inside the `Next step` cell or in a cited companion note before treating a row as coupling-eligible.

Parallelization note: ledger discovery is row-local and should fan out across independent tools and function/API surfaces. LLM/tool workers may author, audit, and reconcile MICRO/BOUND packets for separate rows in parallel, provided each row keeps its own exact function surface, receipt path, demotion condition, and loopback target. Runner execution and ledger writes remain serial only when required by the runner, shared result paths, queue mutation, or dependency on prior receipts.

---

## Ledger

| Tool | Capability probe file | Capability probe status | Integration sims count | Integration depth | Next step |
|---|---|---|---|---|---|
| **z3** | `sim_z3_capability.py` | passes local rerun (2026-04-19) | 2 (`sim_integration_ribs_z3_constraint_archive.py`, `sim_integration_hypothesis_z3_property_guard.py`) | load_bearing confirmed (both dedicated integration sims reran cleanly on 2026-04-18, and `sim_gtower_reduction_obstruction_z3.py` now gives a real coverage-lego anchor) | Micro receipt DONE locally: `sim_z3_qf_lia_unsat_witness_micro.py` for `SolverFor('QF_LIA').add/check/model` over bounded linear integer SAT/UNSAT fixtures produced `system_v4/probes/a2_state/sim_results/sim_z3_qf_lia_unsat_witness_micro_results.json` with `4/4`, `all_pass: true`, and `z3: load_bearing`. Next z3 surface: keep additional SMT surfaces separate before coupling or lego-stage use. |
| **cvc5** | `sim_cvc5_capability.py` | passes local rerun (2026-04-19) | 0 dedicated integration sims; used in >=20 compound sims | load_bearing confirmed (parity-check and fence proofs throughout) | Micro receipt DONE locally: `sim_cvc5_qf_lia_model_extraction_micro.py` for `Solver.assertFormula/checkSat/getValue` over QF_LIA produced `system_v4/probes/a2_state/sim_results/sim_cvc5_qf_lia_model_extraction_micro_results.json` with `4/4`, `all_pass: true`, and `cvc5: load_bearing`. Next cvc5 surface: separate SyGuS micro before coupling or lego-stage use. |
| **sympy** | `sim_sympy_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_optuna_sympy_invariant_search.py`) | load_bearing confirmed (the dedicated integration reran cleanly on 2026-04-18) | Micro receipt DONE locally: `sim_sympy_matrix_identity_micro.py` for `sympy.Matrix.inv` plus `Matrix.equals` over exact 2x2 matrices produced `system_v4/probes/a2_state/sim_results/sim_sympy_matrix_identity_micro_results.json` with `all_pass: true` and `sympy: load_bearing`. Next sympy surface: keep invariant-search integration as anchor, but require separate micros for non-matrix symbolic surfaces. |
| **clifford** | `sim_clifford_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_deap_clifford_rotor_evolution.py`) | load_bearing confirmed (rotor double-cover and spinor chirality probes; `sim_foundation_hopf_torus_geomstats_clifford.py` now re-verifies a real coverage-lego anchor on 2026-04-18) | Micro receipt DONE locally: `sim_clifford_rotor_norm_micro.py` for `clifford.Cl(3)` MultiVector geometric product, reverse, and rotor sandwich action produced `system_v4/probes/a2_state/sim_results/sim_clifford_rotor_norm_micro_results.json` with `all_pass: true` and `clifford: load_bearing`. Next clifford surface: keep Hopf/spinor/coupling claims separate from this rotor norm gate. |
| **e3nn** | `sim_e3nn_capability.py` | passes local rerun (2026-04-19) | 0 dedicated integration sims | load_bearing confirmed (equivariance and SO(3) irrep probes) | Author `sim_integration_e3nn_*`; add comparison note against broader geometry/operator use |
| **pyg** | `sim_pyg_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_datasketch_pyg_lsh_graph.py`) | load_bearing confirmed (the dedicated integration reran cleanly on 2026-04-18) | Run capability probe fresh; keep the datasketch+pyg rerun as the current graph-native integration anchor |
| **toponetx** | `sim_toponetx_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_toponetx_gtower_chain_complex.py`) | load_bearing confirmed; current explicit integration packet is stage-heavy baseline/reference, but `sim_toponetx_hopf_crosscheck.py` now gives a cleaner real coverage-lego anchor | Keep the G-tower packet as reference only; use the Hopf crosscheck as the current bounded TopoNetX anchor |
| **gudhi** | `sim_gudhi_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_pymoo_gudhi_pareto_persistence.py`) | load_bearing confirmed (persistent homology, Betti exclusion; `sim_gudhi_deep_s3_hopf_torus_persistent_homology.py` now reran cleanly on 2026-04-18) | Micro receipt DONE locally: `sim_gudhi_simplex_persistence_micro.py` for `SimplexTree.insert/persistence/persistence_intervals_in_dimension/persistent_betti_numbers` produced `system_v4/probes/a2_state/sim_results/sim_gudhi_simplex_persistence_micro_results.json` with `6/6`, `all_pass: true`, and `gudhi: load_bearing`. Next gudhi surface: keep point-cloud/Rips/AlphaComplex coverage separate before coupling or lego-stage use. |
| **rustworkx** | `sim_rustworkx_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_networkx_rustworkx_crosscheck.py`) | load_bearing confirmed (DAG/SCC admissibility, Cayley graph probes) | Micro receipt DONE locally: `sim_rustworkx_dag_reachability_micro.py` for `PyDiGraph + has_path/descendants/ancestors` over bounded DAG reachability produced `system_v4/probes/a2_state/sim_results/sim_rustworkx_dag_reachability_micro_results.json` with `all_pass: true` and `rustworkx: load_bearing`. Next rustworkx surface: keep NetworkX cross-check baseline/reference grade and separate higher-order graph claims from this DAG reachability receipt. |
| **geomstats** | `sim_geomstats_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_geomstats_constraint_manifold.py`) | load_bearing confirmed (Frechet mean, SO(3) geodesic, Stiefel probes; `sim_foundation_hopf_torus_geomstats_clifford.py` reran cleanly as a real coverage-lego anchor) | Micro receipt DONE locally: `sim_geomstats_so3_distance_micro.py` for `SpecialOrthogonal(3).metric.dist` over bounded SO(3) intrinsic distance fixtures produced `system_v4/probes/a2_state/sim_results/sim_geomstats_so3_distance_micro_results.json` with `7/7`, `all_pass: true`, and `geomstats: load_bearing`. Next geomstats surface: keep SO(3) log/exp branch-selection and Hopf geometry claims separate from this distance receipt. |
| **xgi** | `sim_xgi_capability.py` | passes local rerun (2026-04-19) | 0 dedicated integration sims | load_bearing confirmed (hypergraph shell probes, higher-order coupling) | Author `sim_integration_xgi_*`; use the fresh capability run as the current strong anchor |
| **networkx** | `sim_networkx_capability.py` | passes local rerun (2026-04-19) | 0 dedicated integration sims | superficial (used as baseline/comparison, not load-bearing proof) | Clarify whether networkx is structural or just a cross-check baseline |
| **numpy** | `sim_numpy_capability.py` | passes local rerun (2026-04-19) | 0 dedicated integration sims | superficial (baseline numeric substrate; torch is load-bearing by doctrine) | Keep as classical baseline; no integration sim needed |
| **pytorch / autograd** | `sim_pytorch_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_evotorch_autograd_constraint_search.py`) | load_bearing confirmed (gradient I_c via autograd; Axis 0 gradient probes) | Micro receipt DONE locally: `sim_pytorch_autograd_gradient_micro.py` for `torch.autograd.grad(outputs, inputs, create_graph=True)` produced `system_v4/probes/a2_state/sim_results/sim_pytorch_autograd_gradient_micro_results.json` with `all_pass: true` and `pytorch: load_bearing`. Next pytorch/autograd surface: keep PyG message passing and density-matrix entropy gradients as separate MICRO rows. |
| **ribs** | `sim_capability_ribs_isolated.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_ribs_z3_constraint_archive.py`) | load_bearing confirmed (reran cleanly 2026-04-18 after optional-import hardening) | Run the isolated capability probe fresh; keep the z3 archive packet as the current integration anchor |
| **deap** | `sim_capability_deap_isolated.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_deap_clifford_rotor_evolution.py`) | unverified — same debt class as ribs | Same as ribs: rewrite manifest, rerun, re-promote |
| **evotorch** | `sim_capability_evotorch_isolated.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_evotorch_autograd_constraint_search.py`) | unverified — same debt class | Same as ribs |
| **datasketch** | `sim_capability_datasketch_isolated.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_datasketch_pyg_lsh_graph.py`) | load_bearing confirmed (reran cleanly 2026-04-18) | Run the isolated capability probe fresh; keep the PyG LSH graph packet as the current integration anchor |
| **pymoo** | `sim_capability_pymoo_isolated.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_pymoo_gudhi_pareto_persistence.py`) | unverified — manifest stub debt (KNOWN_DISCIPLINE_DEBT 2026-04-14) | Same as ribs before promotion |
| **hypothesis** | `sim_capability_hypothesis_isolated.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_hypothesis_z3_property_guard.py`) | load_bearing confirmed (reran cleanly 2026-04-18) | Run the isolated capability probe fresh; keep the z3 property-guard packet as the current integration anchor |
| **optuna** | `sim_capability_optuna_isolated.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_optuna_sympy_invariant_search.py`) | load_bearing confirmed (reran cleanly 2026-04-18) | Run the isolated capability probe fresh; keep the sympy invariant-search packet as the current integration anchor |
| **hdbscan** | `sim_capability_hdbscan_isolated.py` | passes local rerun (2026-04-19) | 2 (`sim_hdbscan_umap_verdict_clustering.py`, `sim_integration_hdbscan_constraint_clustering.py`) | load_bearing confirmed (density clustering, core distances, noise labeling) | Reconcile the dedicated hdbscan integration anchor into the current tool-stage truth labels; no capability-authoring debt remains |
| **umap** | `sim_capability_umap_isolated.py` | passes local rerun (2026-04-19) | 2 (`sim_hdbscan_umap_verdict_clustering.py`, `sim_integration_umap_gtower_projection.py`) | load_bearing confirmed (dimensionality reduction, n_neighbors sensitivity) | Reconcile the dedicated umap integration anchor into the current tool-stage truth labels; no capability-authoring debt remains |

---

## Key Gaps Summary

1. **All 22 tools now have a capability probe** that passes a fresh local rerun (2026-04-19). Earlier ledger entries claiming hdbscan/umap had no probe were stale — `sim_capability_hdbscan_isolated.py` and `sim_capability_umap_isolated.py` both exist and pass.

2. **Zero or unresolved dedicated integration sims** for: cvc5, e3nn, xgi, networkx, and numpy still lack clean dedicated integration anchors; TopoNetX, rustworkx, and geomstats have files on disk, but the current anchors are baseline/reference or need truth-label reconciliation before they count as clean Tier A defaults. cvc5, z3, sympy, clifford, gudhi, rustworkx, geomstats, and pytorch/autograd now have canonical load-bearing micro receipts for the named function/API surfaces above; those receipts do not by themselves promote dedicated integration anchors.

3. **Manifest debt remains only on the unrepaired subset**: deap, evotorch, and pymoo still need the same debt repayment pass. The ribs, datasketch, hypothesis, and optuna integration anchors were rerun cleanly on 2026-04-18.

4. **Run status confirmed across all 22 capability probes on 2026-04-19**: hdbscan and umap no longer count as missing-capability tools. Dedicated hdbscan and umap integration files now exist; the remaining work is truth-label reconciliation, not capability-probe authoring.

## Immediate bounded batch

The next honest tool-stage batch should stay below lego work:
- additional cvc5 surface micro, likely SyGuS
- additional z3 SMT surface micro only if a new solver API surface is needed
- separate SymPy non-matrix symbolic surface micro before symbolic coupling
- separate Clifford Hopf/spinor surface micro before tool-tool coupling
- separate geomstats SO(3) log/exp branch-selection micro before geometry coupling
- separate rustworkx non-DAG or graph-algorithm surface micro before graph-cell promotion
- separate GUDHI point-cloud/Rips/AlphaComplex micro before topology coupling
- separate PyTorch density-matrix entropy-gradient or PyG/autograd micro before downstream differentiable claims
