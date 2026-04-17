---
title: Tooling Status
created: 2026-04-07
updated: 2026-04-16
type: concept
tags: [system, tooling, validation, simulation, planning]
sources:
  - raw/articles/new-docs/TOOLING_STATUS.md
framing: current
---

# Tooling Status

Current repo Makefile interpreter: `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3` (from the repo Makefile `PYTHON := ...`). Date: 2026-04-13. This supersedes the older homebrew-python note.

## Current Truth

- Stack is broader and more active than older docs implied
- Proof/graph/geometry tool surface is real but uneven
- Bridge / Phi0 seam is still mostly numpy-first, underintegrated with proof/graph stack
- Foundational legos better covered; bridge/cut-state/Phi0 separation now real; deep graph/proof integration still behind

Important distinction:
- tool present in repo
- tool load-bearing in a bounded sim
- tool/corresponding claim promoted to `canonical by process`

Those are different axes. Do not collapse them.

## GREEN — Installed, imported, verified

| Tool | Version | Role | Usage |
|------|---------|------|-------|
| torch | 2.11.0 | Core computation substrate | 134 sim-like files |
| PyG | 2.7.0 | Graph dynamics, message passing | 55 files |
| z3 | 4.16.0 | SMT constraint proofs (UNSAT) | 100 files |
| cvc5 | 1.3.3 | SMT cross-check, SyGuS synthesis | 54 files |
| sympy | 1.14.0 | Symbolic algebra | 102 files |
| clifford | 1.5.1 | Geometric algebra Cl(3)/Cl(6) | 82 files |
| TopoNetX | 0.4.0 | Cell-complex topology | 3 files (underused) |
| GUDHI | 3.12.0 | Persistent homology, TDA | 59 files |
| geomstats | 2.8.0 | Riemannian manifolds | 59 files |
| e3nn | 0.6.0 | E(3)-equivariant NNs | 55 files |
| rustworkx | 0.17.1 | Fast graph kernels, DAGs | 64 files |
| XGI | 0.10.1 | Hypergraphs, simplicial complexes | 55 files |

## 2026-04-16 whole-system re-audit snapshot
A Hermes re-audit dated 2026-04-16 reported that the repo Makefile interpreter was still:
- `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`

Current runtime/package truth from the repo audit surfaces:
- core sim stack floors are met for `torch 2.11.0`, `sympy 1.14.0`, `z3-solver 4.16.0.0`, `cvc5 1.3.3`, `clifford 1.5.1`, `geomstats 2.8.0`, `e3nn 0.6.0`, `rustworkx 0.17.1`, `xgi 0.10.1`, `TopoNetX 0.4.0`, `gudhi 3.12.0`, and `torch-geometric 2.7.0`
- newer runtime-side tools now present in the audited environment include `networkx 3.6.1` and `pydantic 2.12.5`
- additional helper tooling present in the audited environment includes `jsonschema 4.26.0`, `hypothesis 6.151.12`, and `pytest 9.0.3`
- `matplotlib 3.10.8` is installed and importable
- current runtime blockers are:
  - `pandas 2.3.3` is below the repo floor `>=3.0.0`
  - `pyvista` is still missing

Repo-health snapshot from the same 2026-04-16 re-audit:
- `probe_truth_audit.py`: `hard_finding_count=76`, `warning_finding_count=18`
- `lego_tool_reporting_audit.py`: `blocker_count=7`, `advisory_count=9`
- `repo_hygiene_audit.py`: `blocker_count=3`, dirty worktree still high
- overall system hygiene remains not green

So the honest state is:
- the tool stack is broader than the older table alone suggests
- several newer tools are now installed and visible in the runtime contract
- the environment is ahead of some prose docs, but whole-system process truth is still blocked more by stale result/process/hygiene surfaces than by missing core tool installs

## Broader classical-sim tool surface (2026-04-16 audit)
Separate from the core canonical sim stack, the repo now also contains a larger classical-sim / exploratory tool surface. These tools are present in the environment and are being used in bounded classical or capability-style probes, even when they are not yet part of the main canonical contract.

Live repo scan highlights:
- `numpy`: imported in 2557 probe files; appears in 362 result manifests (`254 classical_baseline`, `86 canonical`, `22 other`)
- `scipy`: imported in 231 probe files; appears in 81 result manifests (`59 classical_baseline`, `14 canonical`, `8 other`)
- quantum/classical simulator layer:
  - `pennylane`: 32 probe files
  - `qutip`: 32 probe files
  - `cirq`: 30 probe files
- graph / classical network layer:
  - `networkx`: 26 probe files
  - `igraph`: 4 probe files
- search / optimization / archive / clustering layer:
  - `datasketch`: 10 probe files
  - `ribs`: 10 probe files
  - `optuna`: 9 probe files
  - `hdbscan`: 8 probe files
  - `umap`: 8 probe files
  - `pymoo`: 8 probe files
  - `sklearn`: 7 probe files
  - `pynndescent`: 7 probe files
  - `evotorch`: 6 probe files
  - `deap`: 6 probe files
  - `cma`: 2 probe files
- auxiliary GA / distributed surfaces:
  - `torch_ga`: 33 probe files
  - `ray`: at least 1 active probe import in the current scan

Important distinction:
- these tools are part of the live repo’s broader classical/exploratory capability surface
- they are not automatically part of the core canonical process contract
- import/use in classical sims does not by itself imply load-bearing canonical status

So the cleaner repo-wide picture is:
1. core canonical contract stack: torch / z3 / cvc5 / sympy / clifford / geomstats / e3nn / rustworkx / XGI / TopoNetX / GUDHI / PyG
2. broader classical-sim stack: numpy / scipy plus the larger simulator, graph, search, clustering, and archive tooling used in classical or capability probes

## PLANNED — Not installed

- **Lean 4**: interactive theorem prover (elan/lake install needed)
- **TLAPS**: temporal logic model checking (separate install)

## REMOVED from consideration

- DGL (redundant with PyG), quimb (not needed until Phase 6+), qutip (overlaps with hand-built legos), ripser (superseded by GUDHI), pySMT (z3+cvc5 direct is cleaner), HyperNetX (XGI covers need)

## Stack Architecture

```
PROOF LAYER:     z3 (UNSAT) + cvc5 (cross-check, SyGuS) + Lean 4 [planned] + TLAPS [planned]
GEOMETRY LAYER:  clifford (Cl(3)/Cl(6)) + geomstats (Riemannian) + e3nn (equivariant)
GRAPH LAYER:     rustworkx (DAGs, routing) + PyG (message passing) + XGI (hypergraphs)
TOPOLOGY LAYER:  TopoNetX (cell complexes) + GUDHI (persistent homology) + XGI (simplicial)
COMPUTATION:     torch (core) + numpy (baseline) + rustworkx (perf-critical)
SYMBOLIC:        sympy (algebra, derivation)
```

All layers are simultaneous constraint shells, not sequential pipeline. Current failure mode: "tool declared or imported, but not load-bearing in the actual seam."

## 2026-04-13 tool-boundary audit snapshot
A live repo scan in this session counted 726 `sim_*.py` files and measured import counts against declared `load_bearing` / `supportive` tool roles for the main graph/proof/geometry stack.

This is a snapshot-labeled capability read, not an evergreen authority table:
- import count does not equal meaningful use
- meaningful use does not equal load-bearing proof
- load-bearing proof in one lane does not automatically equal `canonical by process`

| Tool | Imports | Load-bearing | Supportive |
|---|---:|---:|---:|
| pytorch | 259 | 74 | 14 |
| z3 | 235 | 48 | 17 |
| sympy | 226 | 37 | 26 |
| rustworkx | 156 | 16 | 3 |
| clifford | 153 | 13 | 3 |
| cvc5 | 128 | 8 | 6 |
| geomstats | 133 | 14 | 7 |
| pyg | 120 | 11 | 0 |
| gudhi | 121 | 11 | 2 |
| toponetx | 127 | 7 | 0 |
| xgi | 122 | 8 | 1 |
| e3nn | 118 | 5 | 0 |

This is not a final quality score, but it does confirm the same architectural problem the project has been discussing: many tools are present/imported far more often than they are genuinely load-bearing. That is exactly why the [[tool-capability-sim-program]] exists.

## 2026-04-14 bounded sim-tranche note
The newest artifact tranche strengthens the "real but uneven" reading of the stack rather than replacing it.

New bounded artifacts now exist for deeper claim-local packets including:
- `sim_pyg_deep_hopf_u1_equivariant_conservation_results.json`
- `sim_sympy_deep_lindblad_dephasing_spectrum_results.json`
- `sim_rustworkx_deep_cayley_s4_admissibility_results.json`
- `sim_z3_deep_no_classical_stochastic_under_dephasing_weyl_commute_results.json`
- `sim_gudhi_deep_s3_hopf_torus_persistent_homology_results.json`
- `sim_torch_deep_axis0_autograd_vn_entropy_results.json`

This matters because PyG, SymPy, rustworkx, z3, GUDHI, and torch now have newly visible deep packets in the public wiki, not just broad capability claims.

But the tranche also preserves an important split:
- the sampled deep GUDHI artifact records `all_pass: false`
- several adjacent sampled deep-tool artifacts record positive internal pass fields

So the honest public summary is still: these deeper packets `exist`, and some tool surfaces are clearly widening, but this page should not promote the whole deep-tool tranche beyond `exists` without fresh reruns.

## Baseline vs canonical boundary
Another live correction from this session: some newer geometry-side sims were rightly reclassified from `canonical` to `classical_baseline` because numpy is still computing the primary objects while richer tools only check properties of those outputs. This is not a failure; it is the intended baseline layer. The problem was false classification, not baseline existence. See [[classical-baseline-vs-canonical-tool-boundary]].

## Integration Gaps

### Gap 1 — Bridge/Phi0 seam underusing proof tools
**CLOSED 2026-04-08** — `sim_bridge_phi0_proof_integration.py`
- z3 UNSAT: classical states cannot achieve I_c>0 at the flip
- cvc5 SyGuS: bisects flip boundary to relay=0.706180; UNSAT below 0.6562
- sympy eigenvalue chain confirms dS(AC)/dr<0 on [0.5,0.7]
- pytorch autograd: dI_c/d(relay)>0 at all tested values

### Gap 2 — Graph/topology tools not yet central
**PARTIALLY CLOSED** — rustworkx 5-node dependency DAG now load-bearing. geomstats SPD geodesic confirms no interior anomaly.
Still open: TopoNetX barely used (3 files), XGI multi-way packet relations missing, cell-complex reasoning on shell families missing.

### Gap 3 — Basic plan partially executed
1. foundations as independent legos ✓
2. bridge families as independent legos ✓
3. rho_AB construction as own family ✓
4. cut kernels as own family ✓
5. graph/proof integration on seam ✓ (closed 2026-04-08)
6. promotion pressure — **remaining gap**

## Tool-Role Contract

| Tool | Must do | Must NOT be reduced to |
|------|---------|----------------------|
| z3 | UNSAT impossibility proofs | post-hoc SAT confirmation |
| cvc5 | Cross-check z3; SyGuS synthesis | redundant z3 clone |
| sympy | Derive formulas before numerics | verify-only layer |
| clifford | Native Cl(3)/Cl(6) computation | roundtrip unit test |
| rustworkx | Fast graph algorithms, DAGs | NetworkX drop-in |
| XGI | Hypergraph multi-way interactions | pairwise graph + labels |
| TopoNetX | Cell-complex topology | Betti-number checker |
| GUDHI | Persistent homology at scale | unused import |
| geomstats | Riemannian metrics, geodesics | numpy manifold wrapper |
| e3nn | E(3)-equivariant PyTorch layers | decorative equivariance |
| torch | Core differentiable substrate | numpy replacement |
| PyG | Message passing as computation | graph visualization only |

## Overclassification Audit (2026-04-08)

Reclassified to `exploratory_signal`:
- `q3_bipartite_analysis_results.json` — clifford_z_rotor_on_ket0 fails
- `z3_channel_boundary_theorem_results.json` — test returns SAT, expected UNSAT
- `xgi_torch_autograd_results.json` — no per-test status fields

## Related Pages

- [[tool-manifest-audit]] — detailed usage gap analysis
- [[tool-capability-sim-program]]
- [[networkx-graph-structure-reference]]
- [[pydantic-typed-schema-reference]]
- [[jsonschema-artifact-validation-reference]]
- [[pytest-tiered-gate-reference]]
- [[hypothesis-property-based-testing-reference]]
- [[witness-recorder-and-trace-reference]]
- [[e3nn-equivariant-geometry-reference]]
- [[lean4-proof-assistant-reference]]
- [[tlaps-temporal-proof-reference]]
- [[z3-smt-solver-reference]]
- [[cvc5-smt-and-sygus-reference]]
- [[sympy-symbolic-math-reference]]
- [[rustworkx-graph-algorithms-reference]]
- [[xgi-hypergraph-reference]]
- [[toponetx-topological-complex-reference]]
- [[pytorch-geometric-reference]]
- [[gudhi-persistent-topology-reference]]
- [[geomstats-manifold-geometry-reference]]
- [[clifford-geometric-algebra-reference]]
- [[enforcement-and-process-rules]] — Rule 2 (try all tools)
- [[pytorch-ratchet-build-plan]] — tool integration requirements
- [[system-tools-and-plan]] — v5 tool plan
- [[current-tool-status-installed-vs-missing-vs-not-wired]] — install status
