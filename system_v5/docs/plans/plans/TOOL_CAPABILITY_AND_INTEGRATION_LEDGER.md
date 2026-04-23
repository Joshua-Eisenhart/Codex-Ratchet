# Tool Capability and Integration Ledger

Date: 2026-04-14  
Status: living ledger — update when probes run or integration sims are added  
Authority: tracks `system_v4/probes/sim_capability_*.py` and `sim_integration_*.py` as of this session

## How to Read

- **Capability probe file**: path relative to `system_v4/probes/`, or `none` if absent
- **Capability probe status**: one of the four canonical labels (`exists / runs / passes local rerun / canonical by process`), or `never-run` / `none`
- **Integration sims count**: count of `sim_integration_*<tool>*` files found at `system_v4/probes/`
- **Integration depth**: `load_bearing confirmed` (tool drives a structural test), `superficial` (used but not structural), or `none` / `unverified`
- **Next step**: what is actually needed before this tool is in good standing

Status `unverified` = file exists but run status was not confirmed this session.

---

## Ledger

| Tool | Capability probe file | Capability probe status | Integration sims count | Integration depth | Next step |
|---|---|---|---|---|---|
| **z3** | `sim_z3_capability.py` | exists (unverified run status) | 2 (`sim_integration_ribs_z3_constraint_archive.py`, `sim_integration_hypothesis_z3_property_guard.py`) | load_bearing confirmed (z3 UNSAT is primary proof form across ≥10 probes) | Run capability probe fresh; elevate to `passes local rerun` |
| **cvc5** | `sim_cvc5_capability.py` | exists (unverified run status) | 0 dedicated integration sims; used in ≥20 compound sims | load_bearing confirmed (parity-check and fence proofs throughout) | Author isolated `sim_integration_cvc5_*` to make integration explicit; run capability probe |
| **sympy** | `sim_sympy_capability.py` | exists (unverified run status) | 1 (`sim_integration_optuna_sympy_invariant_search.py`) | load_bearing confirmed (BCH, Lindblad, closed-form derivations) | Run capability probe fresh; integration count low relative to usage |
| **clifford** | `sim_clifford_capability.py` | exists (unverified run status) | 1 (`sim_integration_deap_clifford_rotor_evolution.py`) | load_bearing confirmed (rotor double-cover and spinor chirality probes) | Run capability probe fresh; confirm `passes local rerun` |
| **e3nn** | `sim_e3nn_capability.py` | exists (unverified run status) | 0 dedicated integration sims | load_bearing confirmed (equivariance and SO(3) irrep probes) | Author `sim_integration_e3nn_*`; run capability probe |
| **pyg** | `sim_pyg_capability.py` | exists (unverified run status) | 1 (`sim_integration_datasketch_pyg_lsh_graph.py`) | load_bearing confirmed (dynamic edge tensors, message-passing probes) | Run capability probe fresh; verify load_bearing in manifest |
| **toponetx** | `sim_toponetx_capability.py` | exists (unverified run status) | 0 dedicated integration sims | load_bearing confirmed (Hodge boundary, cell-complex probes) | Author `sim_integration_toponetx_*`; run capability probe |
| **gudhi** | `sim_gudhi_capability.py` | exists (unverified run status) | 1 (`sim_integration_pymoo_gudhi_pareto_persistence.py`) | load_bearing confirmed (persistent homology, Betti exclusion) | Run capability probe fresh; confirm `passes local rerun` |
| **rustworkx** | `sim_rustworkx_capability.py` | exists (unverified run status) | 0 dedicated integration sims | load_bearing confirmed (DAG/SCC admissibility, Cayley graph probes) | Author `sim_integration_rustworkx_*`; run capability probe |
| **geomstats** | `sim_geomstats_capability.py` | exists (unverified run status) | 0 dedicated integration sims | load_bearing confirmed (Fréchet mean, SO(3) geodesic, Stiefel probes) | Author `sim_integration_geomstats_*`; run capability probe |
| **xgi** | `sim_xgi_capability.py` | exists (unverified run status) | 0 dedicated integration sims | load_bearing confirmed (hypergraph shell probes, higher-order coupling) | Author `sim_integration_xgi_*`; run capability probe |
| **networkx** | `sim_networkx_capability.py` | exists (unverified run status) | 0 dedicated integration sims | superficial (used as baseline/comparison, not load-bearing proof) | Clarify whether networkx is structural or just a cross-check baseline |
| **numpy** | `sim_numpy_capability.py` | exists (unverified run status) | 0 dedicated integration sims | superficial (baseline numeric substrate; torch is load-bearing by doctrine) | Keep as classical baseline; no integration sim needed |
| **pytorch / autograd** | `sim_pytorch_capability.py` | exists (unverified run status) | 1 (`sim_integration_evotorch_autograd_constraint_search.py`) | load_bearing confirmed (∇I_c via autograd; Axis 0 gradient probes) | Run capability probe fresh; verify Axis 0 probe still earns `passes local rerun` |
| **ribs** | `sim_capability_ribs_isolated.py` | exists (unverified run status) | 1 (`sim_integration_ribs_z3_constraint_archive.py`) | unverified — integration sim exists but manifest reasons were flagged as stub (KNOWN_DISCIPLINE_DEBT entry 2026-04-14) | Rewrite manifest reasons ≥25 chars; rerun; re-promote to `canonical by process` |
| **deap** | `sim_capability_deap_isolated.py` | exists (unverified run status) | 1 (`sim_integration_deap_clifford_rotor_evolution.py`) | unverified — same debt class as ribs | Same as ribs: rewrite manifest, rerun, re-promote |
| **evotorch** | `sim_capability_evotorch_isolated.py` | exists (unverified run status) | 1 (`sim_integration_evotorch_autograd_constraint_search.py`) | unverified — same debt class | Same as ribs |
| **datasketch** | `sim_capability_datasketch_isolated.py` | exists (unverified run status) | 1 (`sim_integration_datasketch_pyg_lsh_graph.py`) | unverified — same debt class | Same as ribs |
| **pymoo** | `sim_capability_pymoo_isolated.py` | exists (unverified run status) | 1 (`sim_integration_pymoo_gudhi_pareto_persistence.py`) | unverified — manifest stub debt (KNOWN_DISCIPLINE_DEBT 2026-04-14) | Same as ribs |
| **hypothesis** | `sim_capability_hypothesis_isolated.py` | exists (unverified run status) | 1 (`sim_integration_hypothesis_z3_property_guard.py`) | unverified — manifest stub debt | Same as ribs |
| **optuna** | `sim_capability_optuna_isolated.py` | exists (unverified run status) | 1 (`sim_integration_optuna_sympy_invariant_search.py`) | unverified — manifest stub debt | Same as ribs |
| **hdbscan** | none | none | 0 (combined with umap in `sim_hdbscan_umap_verdict_clustering.py`) | none — no capability probe, no dedicated integration sim | Author isolated `sim_capability_hdbscan_isolated.py`; separate from umap probe |
| **umap** | none | none | 0 (combined with hdbscan above) | none — no capability probe | Author isolated `sim_capability_umap_isolated.py`; separate from hdbscan probe |

---

## Key Gaps Summary

1. **Missing capability probes**: hdbscan and umap have no isolated capability probes. They share one combined classical sim (`sim_hdbscan_umap_verdict_clustering.py`), which violates the four-sim-kinds discipline (capability probe must precede integration).

2. **Zero dedicated integration sims** for: cvc5, e3nn, toponetx, rustworkx, geomstats, xgi, networkx, numpy. Each of these tools has many compound sims but no explicit `sim_integration_<tool>_*` file anchoring the tool-to-lego integration story.

3. **Manifest debt on 7 probes** (ribs, deap, evotorch, datasketch, pymoo, hypothesis, optuna): capability probes exist but integration sims had stub manifests at time of authoring. See KNOWN_DISCIPLINE_DEBT.md for repayment criteria.

4. **No capability probe run status confirmed this session**: all `exists` claims above are based on filesystem glob only. None are elevated to `passes local rerun` here.
