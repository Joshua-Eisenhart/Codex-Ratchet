# Ablation Irreducibility Report

Generated from `overnight_logs/ablation_irreducibility_report.json` via `scripts/ablation_harness.py`.

- Sims tested: **10**
- Total (sim x load_bearing_tool) ablations: **27**
- Irreducibility pass rate: **24/27** (88.9%)
- Decorative (claimed LB, survives ablation): **0**
- Baseline-failing sims (excluded from verdict): **1**

## Verdict table

| Sim | Tool | Original | Ablated | Verdict |
|---|---|:-:|:-:|---|
| sim_compound_autograd_sympy_z3_fisher_admissibility.py | pytorch | True | False | irreducible |
| sim_compound_autograd_sympy_z3_fisher_admissibility.py | sympy | True | False | irreducible |
| sim_compound_autograd_sympy_z3_fisher_admissibility.py | z3 | True | False | irreducible |
| sim_compound_clifford_e3nn_so3_equivariance.py | clifford | True | False | irreducible |
| sim_compound_clifford_e3nn_so3_equivariance.py | e3nn | True | False | irreducible |
| sim_compound_clifford_pytorch_xgi_higher_order_rotor.py | pytorch | True | False | irreducible |
| sim_compound_clifford_pytorch_xgi_higher_order_rotor.py | clifford | True | False | irreducible |
| sim_compound_clifford_pytorch_xgi_higher_order_rotor.py | xgi | True | False | irreducible |
| sim_compound_cvc5_rustworkx_toponetx_graph_topology.py | cvc5 | True | False | irreducible |
| sim_compound_cvc5_rustworkx_toponetx_graph_topology.py | rustworkx | True | False | irreducible |
| sim_compound_cvc5_rustworkx_toponetx_graph_topology.py | toponetx | True | False | irreducible |
| sim_compound_pyg_autograd_hopf_ratchet.py | pyg | True | False | irreducible |
| sim_compound_pyg_autograd_hopf_ratchet.py | pytorch | True | False | irreducible |
| sim_compound_pyg_toponetx_gudhi_hodge_pipeline.py | pyg | True | False | irreducible |
| sim_compound_pyg_toponetx_gudhi_hodge_pipeline.py | toponetx | True | False | irreducible |
| sim_compound_pyg_toponetx_gudhi_hodge_pipeline.py | gudhi | True | False | irreducible |
| sim_compound_z3_clifford_e3nn_so3_chirality.py | clifford | True | False | irreducible |
| sim_compound_z3_clifford_e3nn_so3_chirality.py | e3nn | True | False | irreducible |
| sim_compound_z3_clifford_e3nn_so3_chirality.py | z3 | True | False | irreducible |
| sim_compound_z3_clifford_pyg_so3_admissibility.py | pyg | False | False | baseline_fail (cannot verdict) |
| sim_compound_z3_clifford_pyg_so3_admissibility.py | z3 | False | False | baseline_fail (cannot verdict) |
| sim_compound_z3_clifford_pyg_so3_admissibility.py | clifford | False | False | baseline_fail (cannot verdict) |
| sim_compound_z3_cvc5_kcbs_parity.py | z3 | True | False | irreducible |
| sim_compound_z3_cvc5_kcbs_parity.py | cvc5 | True | False | irreducible |
| sim_compound_z3_sympy_clifford_bch_unsat.py | z3 | True | False | irreducible |
| sim_compound_z3_sympy_clifford_bch_unsat.py | sympy | True | False | irreducible |
| sim_compound_z3_sympy_clifford_bch_unsat.py | clifford | True | False | irreducible |

## Notes

- Ablation method: `sys.modules[<tool>] = _Broken` + `__import__` guard BEFORE `runpy.run_path`.
- Pass detection: stdout `PASS=True` OR JSON `overall_pass` / `compound_claim_holds` key.
- **No decorative tools detected** across tested sims.
- **Baseline-failing sims (pre-existing, not an ablation issue):**
  - `sim_compound_z3_clifford_pyg_so3_admissibility.py`
