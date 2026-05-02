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

---

## Ledger

| Tool | Capability probe file | Capability probe status | Integration sims count | Integration depth | Next step |
|---|---|---|---|---|---|
| **z3** | `sim_z3_capability.py` | passes local rerun (2026-04-19) | 2 (`sim_integration_ribs_z3_constraint_archive.py`, `sim_integration_hypothesis_z3_property_guard.py`) | load_bearing confirmed (both dedicated integration sims reran cleanly on 2026-04-18, and `sim_gtower_reduction_obstruction_z3.py` now gives a real coverage-lego anchor) | Run capability probe fresh; keep the integration reruns plus the G-tower obstruction packet as current proof-lane anchors |
| **cvc5** | `sim_cvc5_capability.py` | passes local rerun (2026-04-19) | 0 dedicated integration sims; used in ≥20 compound sims | load_bearing confirmed (parity-check and fence proofs throughout) | Author isolated `sim_integration_cvc5_*` to make integration explicit; run capability probe |
| **sympy** | `sim_sympy_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_optuna_sympy_invariant_search.py`) | load_bearing confirmed (the dedicated integration reran cleanly on 2026-04-18) | Run capability probe fresh; keep the optuna+sympy rerun as the current bounded search/proof anchor |
| **clifford** | `sim_clifford_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_deap_clifford_rotor_evolution.py`) | load_bearing confirmed (rotor double-cover and spinor chirality probes; `sim_foundation_hopf_torus_geomstats_clifford.py` now re-verifies a real coverage-lego anchor on 2026-04-18) | Run capability probe fresh; keep the Hopf geometry coverage-lego as the current bounded anchor |
| **e3nn** | `sim_e3nn_capability.py` | passes local rerun (2026-04-19) | 0 dedicated integration sims | load_bearing confirmed (equivariance and SO(3) irrep probes) | Author `sim_integration_e3nn_*`; add comparison note against broader geometry/operator use |
| **pyg** | `sim_pyg_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_datasketch_pyg_lsh_graph.py`) | load_bearing confirmed (the dedicated integration reran cleanly on 2026-04-18) | Run capability probe fresh; keep the datasketch+pyg rerun as the current graph-native integration anchor |
| **toponetx** | `sim_toponetx_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_toponetx_gtower_chain_complex.py`) | load_bearing confirmed; current explicit integration packet is stage-heavy baseline/reference, but `sim_toponetx_hopf_crosscheck.py` now gives a cleaner real coverage-lego anchor | Keep the G-tower packet as reference only; use the Hopf crosscheck as the current bounded TopoNetX anchor |
| **gudhi** | `sim_gudhi_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_pymoo_gudhi_pareto_persistence.py`) | load_bearing confirmed (persistent homology, Betti exclusion; `sim_gudhi_deep_s3_hopf_torus_persistent_homology.py` now reran cleanly on 2026-04-18) | Run capability probe fresh; keep the Hopf persistent-homology packet as the current bounded anchor |
| **rustworkx** | `sim_rustworkx_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_networkx_rustworkx_crosscheck.py`) | load_bearing confirmed (DAG/SCC admissibility, Cayley graph probes) | Keep the integration packet baseline/reference grade; add baseline-vs-canonical comparison note |
| **geomstats** | `sim_geomstats_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_geomstats_constraint_manifold.py`) | load_bearing confirmed (Fréchet mean, SO(3) geodesic, Stiefel probes; `sim_foundation_hopf_torus_geomstats_clifford.py` reran cleanly as a real coverage-lego anchor) | Keep the integration packet baseline/reference grade; use the Hopf geometry packet as the current real coverage-lego anchor |
| **xgi** | `sim_xgi_capability.py` | passes local rerun (2026-04-19) | 0 dedicated integration sims | load_bearing confirmed (hypergraph shell probes, higher-order coupling) | Author `sim_integration_xgi_*`; use the fresh capability run as the current strong anchor |
| **networkx** | `sim_networkx_capability.py` | passes local rerun (2026-04-19) | 0 dedicated integration sims | superficial (used as baseline/comparison, not load-bearing proof) | Clarify whether networkx is structural or just a cross-check baseline |
| **numpy** | `sim_numpy_capability.py` | passes local rerun (2026-04-19) | 0 dedicated integration sims | superficial (baseline numeric substrate; torch is load-bearing by doctrine) | Keep as classical baseline; no integration sim needed |
| **pytorch / autograd** | `sim_pytorch_capability.py` | passes local rerun (2026-04-19) | 1 (`sim_integration_evotorch_autograd_constraint_search.py`) | load_bearing confirmed (∇I_c via autograd; Axis 0 gradient probes) | Run capability probe fresh; verify Axis 0 probe still earns `passes local rerun` |
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

2. **Zero or unresolved dedicated integration sims** for: cvc5, e3nn, xgi, networkx, and numpy still lack clean dedicated integration anchors; TopoNetX, rustworkx, and geomstats have files on disk, but the current anchors are baseline/reference or need truth-label reconciliation before they count as clean Tier A defaults.

3. **Manifest debt remains only on the unrepaired subset**: deap, evotorch, and pymoo still need the same debt repayment pass. The ribs, datasketch, hypothesis, and optuna integration anchors were rerun cleanly on 2026-04-18.

4. **Run status confirmed across all 22 capability probes on 2026-04-19**: hdbscan and umap no longer count as missing-capability tools. Dedicated hdbscan and umap integration files now exist; the remaining work is truth-label reconciliation, not capability-probe authoring.

## Immediate bounded batch

The next honest tool-stage batch should stay below lego work:
- `sim_rustworkx_capability.py`
- `sim_geomstats_capability.py`
- `sim_xgi_capability.py`
- `sim_e3nn_capability.py`
- `sim_integration_networkx_rustworkx_crosscheck.py`
- `sim_integration_geomstats_constraint_manifold.py`
- do not queue `sim_integration_toponetx_gtower_chain_complex.py` as a default clean Tier A candidate until it is thinned below tower-order / shortcut-law semantics
