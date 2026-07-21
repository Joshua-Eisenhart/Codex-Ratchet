# Integration inventory — every sim engine, tool, library, repo, and Lev OS component

Status: exists + runs (every number below was read from a receipt file already on
disk, and two claims — the ratchet kernel self-test and the Lev CLI command
list — were re-run live in this session). Not canonical by process. This
document is an inventory, not an admission.

## Scope and method

Sources read in full: `system_v8/tool_ledger/TOOL_LEDGER.md` (including the
"COMPLETE ESTATE INVENTORY" section), `system_v8/engine_estate/ENGINE_ESTATE_REPORT.md`
and its four `results/*/receipt.json` files, all five
`system_v8/tool_ledger/battery_batch{1..5}/receipt.json` files, the three
new-donor result files, `ROOT/RUNNING_THE_RATCHET_ON_ENGINES_AND_LEV.md`,
`claimgate/README.md` and `claimgate/results/first_sweep.json`,
`fuel_gate/results/first_pool_verdict.json`, and
`~/.local/share/lev/events/runtime-events.jsonl`. Every row below cites the
file it came from. Where I could not find a grounding receipt for a claim the
ledger itself makes, that is reported as a finding, not silently repeated.

Four states, owner's own definitions (`TOOL_LEDGER.md` lines 3-7):
`INTEGRATED` (genuine load-bearing use, not import-only), `BLOCKED` (real
error, exact message recorded), `PRUNED` (installed, importable, a real
limitation rules it out), `UNTESTED` (installed and importable, no
integration receipt yet — may not be leaned on). Lev OS gets a fifth,
non-standard label, `PARTIAL`, which the source ledger introduces itself; it
is flagged below rather than folded into the other four.

Claim ceiling on every row: tool-integration evidence only. Nothing in this
document is a canonical, bridge, QIT, GStack, axis, or nonclassical admission
claim — that ceiling is stated explicitly in every receipt cited.

---

## 1. Sim engines and their attached library estates

### 1.1 Julia — canon engine

Self-test: 7/7 sections PASS, 0 fail, 0 blocked. Julia 1.12.6.
Receipt: `system_v8/engine_estate/results/julia/receipt.json`.
25 packages carry integration receipts; 2 are untested.

| Package | Version | State | Receipt | Computed evidence |
|---|---|---|---|---|
| QuantumOptics | 1.2.6 | INTEGRATED | `engine_estate/results/julia/receipt.json` (`quantumoptics_gksl_L8`) | GKSL amplitude-damping + depolarizing entropy laws, 5/5 checks pass to 1e-6 |
| ITensors | 0.9.30 | INTEGRATED | same, `itensors_schmidt_cut_L7` | GHZ Schmidt cut entropy S = ln 2, 4/4 checks pass |
| ITensorMPS | 0.4.1 | INTEGRATED | same (paired with ITensors); reconfirmed `battery_batch2/test_itensormps.jl` | GHZ cut entropy matches ln 2 to 1e-16 |
| QuantumClifford | 0.11.4 | INTEGRATED | same, `quantumclifford_ghz_L6` | Stabiliser cut entropies, 4/4 checks pass |
| Octonions | 0.2.3 | INTEGRATED | same, `octonions_nonassoc_L10` | Nonassociativity witnessed + norm composition holds to 1e-12, 2/2 |
| Grassmann | 0.8.44 | INTEGRATED | same, `grassmann_pseudoscalar_L10` | Pseudoscalar squares to +1, one-vectors anticommute, 3/3 checks |
| CliffordAlgebras | 0.1.4 | INTEGRATED | same, `cliffordalgebras_gamma5_L10` | gamma5 anticommutes with generators, squares to +1, 3/3 checks |
| Attractors | 1.38.4 | INTEGRATED (unblocked this session) | same, `attractors_bistable_basins_L13`; prior break in `known_breakage` | Bistable basins symmetric/disjoint, 5/5; was `UndefVarError: referenced_sciml_model` at v1.37.0, fixed by `Pkg.add(version="1.38.4")` |
| DynamicalSystems | (via Attractors/QuantumOptics) | INTEGRATED | exercised through `QuantumOptics.timeevolution` and the Attractors mapper, per `TOOL_LEDGER.md` line 182 | no independent receipt row of its own — riding on the two packages above |
| Z3.jl | 1.0.4 | INTEGRATED | `engine_estate/results/julia/receipt.json` (package present, PASS); load-bearing in `manifold/results/proof_order_lane.json` | see SMT table (section 2) |
| JSON3 | 1.14.3 | INTEGRATED | `engine_estate/results/integration/receipt.json` | Cross-engine JSON handoff cost no precision at the 1e-8 level (see 1.4 below) |
| Flux | (batch2) | INTEGRATED | `battery_batch2/test_flux.jl` | Heldout accuracy 0.6146 on real senses data, n=384, chance 0.5 |
| Lux | (batch2) | INTEGRATED | `battery_batch2/test_lux.jl` | Heldout accuracy 0.5104 > chance 0.5 (weak margin, honestly reported) |
| QuantumToolbox | (batch2) | INTEGRATED — gate miss documented | `battery_batch2/results/quantumtoolbox.json`; **receipt itself records `pass: false`** | mesolve max error 1.458e-8 against a declared 1e-8 gate — misses its own gate; TOOL_LEDGER.md keeps the INTEGRATED label with an explicit "(gate miss documented)" note rather than silently rounding up |
| ChaosTools | (batch2) | INTEGRATED | `battery_batch2/test_chaostools.jl` | Lyapunov spectrum [-0.10536, -0.22314], both < 0 (contractive) |
| CombinatorialSpaces | (batch2) | INTEGRATED | `battery_batch2/test_combinatorialspaces.jl` | Annular-strip DeltaSet2D Euler characteristic chi = 0 |
| Zygote | (batch2) | INTEGRATED | `battery_batch2/test_zygote.jl` | Gradient vs finite-difference error 1.86e-11 |
| Symbolics | (batch2) | INTEGRATED | `battery_batch2/test_symbolics.jl` | Derived symbolic law matches reference RHS `-x*gamma` |
| Quaternions | (batch2) | INTEGRATED | `battery_batch2/test_quaternions.jl` | SU(2) carrier square residual exactly 0 |
| PythonCall | (batch2) | INTEGRATED | `battery_batch2/test_pythoncall.jl` | SHA256 roundtrip on a real receipt, exact match |
| Yao | (batch2) | INTEGRATED | `battery_batch2/test_yao.jl` | State norm + unitarity residuals < 1e-15 on the real two-sheet stage circuit |
| Enzyme | (batch2) | INTEGRATED | `battery_batch2/test_enzyme.jl` | Analytic-gradient match, error exactly 0 |
| Graphs | (batch2) | INTEGRATED | `battery_batch2/test_graphs.jl` | Hamming-1 components (2) agree bitwise with the rustworkx receipt |
| Manifolds | (batch2) | INTEGRATED | `battery_batch2/test_manifolds.jl` | Bures SPD distance 20.0421, finite and positive |
| TensorOperations | (batch2) | INTEGRATED | `battery_batch2/test_tensoroperations.jl` | GHZ cut entropy via `@tensor`, matches quimb reference to 1.1e-16 |
| ITensorNetworks | — | UNTESTED | none | installed, no integration receipt |
| GeometryBasics | — | UNTESTED | none | installed, no integration receipt |

### 1.2 JAX — batched workhorse engine

Self-test: 22/22 checks PASS. jax/jaxlib 0.10.1.
Receipt: `system_v8/engine_estate/results/jax/receipt.json`.
Nine libraries were exercised directly inside this phase's own harness
(distinct from the general Python sim-stack battery in 1.5, many of whose
tools are also JAX-backed).

| Package | Version | State | Receipt | Computed evidence |
|---|---|---|---|---|
| jax / jaxlib | 0.10.1 | INTEGRATED | `engine_estate/results/jax/receipt.json` | L13 vmap census 384x256, 78x speedup over a numpy loop (1.336s to 0.0171s), agreement 1.1e-16 |
| diffrax | 0.7.2 | INTEGRATED | same, `L8.gksl_vs_analytic` | 512-trajectory GKSL solve vs analytic law, max error 2.924e-11 |
| quimb | 1.14.0 | INTEGRATED | same, `L7.ghz_cut_entropy` | 12-qubit GHZ cut entropy 0.693147180560 vs ln 2 = 0.693147180560 |
| cotengra | 0.8.0 | INTEGRATED (search path only) | same, `L7.cotengra_load_bearing`; own contraction executor BLOCKED (see 2/section-note) | HyperOptimizer tree search: cost 9.19e3, width 12, path length 23 — quimb executes along the searched path; direct `tree.contract` raises `IndexError` in `_parse_tensordot_axes_to_matmul` and is killed (exit 137) |
| lineax | 0.1.1 | INTEGRATED | same, `L12.lineax_residual` | Fisher-solve residual 1.937e-15 over 256 RHS; vs numpy.solve 2.046e-12 |
| jaxopt | 0.8.5 | INTEGRATED | same, `L12.jaxopt_vs_numpy` | jaxopt CG vs numpy.solve, max diff 1.311e-09 |
| e3nn-jax | 0.21.0 | INTEGRATED | same, `smoke.e3nn_jax` | l=2 spherical-harmonic norm rotation-invariant, |d| = 4.441e-16 |
| ott-jax | 0.6.0 | INTEGRATED — slow-tail-convergence caveat | same, `smoke.ott` | Sinkhorn transport cost 4.0090 vs analytic 4.0 in 8840 iters at eps=0.05; 1e-6 threshold not reached in 20000 iters (documented, not blocking) |
| jraph | 0.0.6.dev0 | INTEGRATED | same, `smoke.jraph` | Message-passing sum == A @ X exactly, max diff 0.0 |
| netket | 3.21.0 | INTEGRATED | same, `smoke.netket` | TFIM N=4 pbc h=1: dense diagonalization E0 = lanczos E0 = -5.2262518595 |

### 1.3 PyTorch — graph/autograd engine

Self-test: 13/13 checks PASS. torch 2.11.0.
Receipt: `system_v8/engine_estate/results/torch/receipt.json`.

| Package | Version | State | Receipt | Computed evidence |
|---|---|---|---|---|
| torch / torch.func | 2.11.0 | INTEGRATED | `engine_estate/results/torch/receipt.json`, `L12_hessian_KL_equals_delta_over_p` | Exact KL Hessian = diag(1/p) to 0.0; softmax Hessian to 2.776e-17 |
| torch_geometric | 2.7.0 | INTEGRATED | same, `L0_pyg_data_valid_all_packets` / `L1_message_passing_components_match_unionfind` | `Data.validate()` on all 9 capacity-complex graphs; MessagePassing fixed points == pure-python union-find on all 9 |
| geomstats | 2.8.0 | INTEGRATED | same, `Lgs_bures_wasserstein_diagonal_closed_form` / `Lgs_fisher_rao_dist_matches_closed_form` | Bures-Wasserstein dist 0.1617643616 vs closed form, diff 1.665e-16; Fisher-Rao diff 1.110e-15 |
| clifford | 1.5.1 | INTEGRATED | same, `smoke_clifford_cl3_bivector` | Cl(3): e1e2 = -e2e1, (e12)^2 = -1 |
| e3nn | 0.6.0 | INTEGRATED | same, `smoke_e3nn_irreps_rep_orthogonal` | Irreps(0e+1o) dim 4, D(R) orthogonal to 1e-10 |
| torch_ga | 0.0.6 | PRUNED (float32-only) | same, `smoke_torch_ga_anticommute` passes at float32, but `findings` records the break | Under `torch.set_default_dtype(torch.float64)`, `geom_prod` raises `expected m1 and m2 to have the same dtype: float != double` — hard-coded float32 internals, not float64-safe |

### 1.4 The three-engine integration chain — one quantity, four independent computations

This is the one receipt where all three declared engines hand real data to
each other in sequence, not just run side by side. Receipt:
`system_v8/engine_estate/results/integration/receipt.json`. All-pass 10/10.

Chain: torch builds the `gcm_completion_projection` continuation digraph and
capacity complex, exports p0 = (1 + out-degree)/sum &rarr; jax runs a batched
64-gamma damped-entropy sweep over those torch-built weights and selects the
interior argmax (k* = 19, gamma* = 0.939683) &rarr; julia integrates the GKSL
amplitude-damping master equation per node at that jax-selected gamma*
(reltol 1e-12) and returns S_master = sum_i S_vN(rho_i(T)) = 4.799504063233.

Independent single-process numpy control of the whole chain:
S_control = 4.799504063233417 vs S_master (chained) = 4.7995040632334325,
abs deviation 1.51e-14. Stage-by-stage: torch p0 vs numpy control exactly
0.0; jax sweep vs numpy control max diff 1.776e-15 over 64 gammas; julia
master-equation populations vs the analytic damping law, max error 4.829e-14.
All three stage subprocesses exit 0; memory free 50% throughout.

### 1.5 Python sim-stack — general library estate (cross-engine)

Everything below ran under the general sim-stack interpreter
(`/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`, one heavy stack
per subprocess, memory-pressure gate checked before each), not the
`engine_estate` phase harness in 1.2/1.3. Many of these libraries are
themselves JAX- or PyTorch-backed (noted where that is a plain fact about the
library, not a claim about which engine "owns" it in this repo) but their
Codex-Ratchet integration evidence comes from the battery receipts below, one
receipt per tool, `promotion_allowed: false` on every row.

#### New donors (2026-07-19), receipt: `system_v8/tool_ledger/receipt.json`

| Tool | State | Receipt | Computed evidence |
|---|---|---|---|
| torchrl 0.13.3 + tensordict 0.13.0 | INTEGRATED | `tool_ledger/test_torchrl_rssm.py`, `results/torchrl_result.json` | RSSM-style GRUModule + WorldModelWrapper trained 60 steps on real 64-object x 6-view x 8-probe occluded sequences; reconstruction MSE 0.7640 &rarr; 0.0065, 909 params |
| inferactively-pymdp 1.0.3 | INTEGRATED | `tool_ledger/test_pymdp_active_inference.py`, `results/pymdp_result.json` | POMDP Agent with A matrix = real empirical probe-outcome distribution (obj-000:view:1); one belief update moves posterior 0.5000 &rarr; 0.6000, correct Bayesian direction |
| transformers (vjepa2 path) | INTEGRATED — scope-limited | `tool_ledger/test_vjepa2_instantiate.py`, `results/vjepa2_result.json` | No standalone `vjepa2` PyPI package; used the `transformers` 4.57.0 `VJEPA2Model` path. Tiny config (191,856 params, random init, no pretrained weights) ran one forward pass on random noise &rarr; `last_hidden_state` shape [1, 8, 48]. A tinier first attempt hit a real rotary-embedding shape bug in shipped `modeling_vjepa2.py`, noted but not blocking at the working config |

#### Already-earned (prior sessions, re-stated for one standing ledger)

| Tool | State | Receipt | Computed evidence |
|---|---|---|---|
| qutip | 5.2.3 | INTEGRATED | `system_v8/deep_integration/results/qit_referee/receipt.json` | Independent mesolve/entropy_vn/ptrace/to_choi/steadystate re-derivation of 3 law families; relative-entropy agreement 1.945e-11 / 4.185e-11 (gate 1e-6); Choi CP audit correctly fails under a gamma&rarr;-gamma control (min eig -0.08104) |
| diffrax | 0.7.2 | INTEGRATED | also `py_battery_results_simstack_20260713.json` | dy/dt=-y solved, err 1.1e-14 (independent of the 1.2 engine-phase receipt) |
| gudhi | 3.12.0 | INTEGRATED | `deep_integration/results/topology/receipt.json` | VR persistence decides all 6 H0/H1 basin-count checks (pit=2, source=4, depolarizing collapses to 1; H1 loop 1.4773 vs scrambled 0.3091) |
| galois | 0.4.11 | INTEGRATED | `deep_integration/results/dynamics_fields/receipt.json` | GF(7)/GF(8) field arithmetic decides all 5 galois-tagged checks (word-match, quadratic-residue set, extension-field structure) |
| pysindy | 2.1.0 | INTEGRATED | same | SINDy regression identifies the Bloch law: const matches +gamma to 5%, linear matches -gamma to 5%, model score > 0.999 |
| torch_geometric | 2.7.0 | INTEGRATED | `engine_estate/results/torch/receipt.json` | (see 1.3; also independently confirmed via `py_battery_results_simstack_20260713.json`) |
| pennylane | 0.44.1 | INTEGRATED | `deep_integration/results/qit_referee/receipt.json` | KAK compilation of the two-sheet unitary stage to RY/RZ+CNOT; circuit unitary vs scipy expm max diff 8.713e-15; parameter-shift vs finite-diff gradient max diff 3.632e-08 |
| quimb | 1.14.0 | INTEGRATED | (see 1.2) | 12-qubit GHZ cut entropy via cotengra-searched path |
| lineax | 0.1.1 | INTEGRATED | (see 1.2) | Fisher solves, residual 1.9e-15 vs numpy |
| jaxopt | 0.8.5 | INTEGRATED | (see 1.2) | max diff 1.311e-09 vs numpy.solve |
| netket | 3.21.0 | INTEGRATED | (see 1.2); also `py_battery_results_simstack_20260713.json` | 4-spin Hilbert space, 16 states |
| e3nn 0.6.0 / e3nn-jax 0.21.0 | INTEGRATED | (see 1.2/1.3); also `py_battery_results_simstack_20260713.json` | 1o x 1o &rarr; 0e invariant tensor-product extraction |
| ott-jax | 0.6.0 | INTEGRATED — caveat | (see 1.2) | slow-tail-convergence note carried forward |
| jraph | 0.0.6.dev0 | INTEGRATED | (see 1.2) | message-passing sum == A @ X, diff 0.0 |
| rustworkx | 0.17.1 | INTEGRATED | `deep_integration/results/topology/receipt.json` | `connected_components`/`adjacency_matrix` agrees bitwise with networkx and the torch receipt on all 9 packets |
| toponetx | 0.4.0 | INTEGRATED | same | CellComplex + Euler + Hodge-Laplacian Betti numbers decide all 3 strip checks (nested-leaf chi=0, betti=[1,1,0] vs flattened control chi=1, betti=[1,0]) |
| geomstats | 2.8.0 | INTEGRATED | (see 1.3); also `py_battery_results_simstack_20260713.json` | great-circle distance = pi/2 exact |
| networkx | (installed) | INTEGRATED | reference engine throughout the topology/graph agreement checks above | agrees bitwise with rustworkx, igraph, and Julia Graphs.jl on 9/9 real capacity packets |

#### Batch 1 — 16 tools, receipt: `battery_batch1/receipt.json` (2026-07-19)

| Tool | State | Receipt | Computed evidence |
|---|---|---|---|
| pykoopman | INTEGRATED | `battery_batch1/test_pykoopman.py` | EDMD recovers continuous eigenvalue -0.361005795087912 vs -gamma = -0.3610057950879211, relative error 2.52e-14 |
| PyDMD | INTEGRATED | `battery_batch1/test_pydmd.py` | DMD on 3 amplitude-damping observables recovers the known spectrum, max error 4.951e-15 |
| dynamiqs | INTEGRATED | `battery_batch1/test_dynamiqs.py` | JAX GKSL mesolve, population error 2.894e-13 vs referee value |
| qutip-jax | INTEGRATED | `battery_batch1/test_qutip_jax.py` | Same channel, population error 3.910e-11, trace preserved exactly |
| numpyro | INTEGRATED | `battery_batch1/test_numpyro.py` | Categorical posterior agrees with m_slow, max hypothesis-posterior diff 6.939e-18 |
| mctx | INTEGRATED | `battery_batch1/test_mctx.py` | Gumbel MuZero selects a real probe action, information gain 0.980829 nats vs uniform-random mean 0.597710 |
| kingdon | INTEGRATED | `battery_batch1/test_kingdon.py` | float64 Cl(4) recomputation of the Julia gamma5 receipt, all 3 residuals 0.0 |
| clifford | INTEGRATED | `battery_batch1/test_clifford.py` | Independent repeat of the same quantity, all 3 residuals 0.0 |
| cvxpy | INTEGRATED | `battery_batch1/test_cvxpy.py` | Closest-CPTP SDP: TP deviation 6.217e-15, projected distance 0.053927 < 0.087464 perturbation |
| jax-verify | BLOCKED | `battery_batch1/test_jax_verify.py` | `AttributeError: module 'jax.lax' has no attribute 'standard_naryop'` while loading a tournament-GRU family |
| torchdiffeq | INTEGRATED | `battery_batch1/test_torchdiffeq.py` | Torch adjoint solve of the damped Bloch ODE, max error 3.309e-11 (diffrax reference 2.924e-11) |
| xgi | INTEGRATED | `battery_batch1/test_xgi.py` | Hamming-1 hypergraphs from all 9 real capacity packets; edge/component stats agree with rustworkx on all 9 |
| maude | INTEGRATED | `battery_batch1/test_maude.py` | 8 real QCA left-shift words normalize in at most 1 rank-decreasing step, 0 critical pairs |
| hypothesis | INTEGRATED | `battery_batch1/test_hypothesis.py` | 80 generated perturbations of real 1024-state posteriors; invariants hold to 1e-12 |
| umap-learn | INTEGRATED | `battery_batch1/test_umap_learn.py` | Embeds 384 real trajectories, trustworthiness 0.916117 vs PCA control 0.747774 |
| optuna | INTEGRATED | `battery_batch1/test_optuna.py` | Ridge-alpha search selects 0.00109141, held-out accuracy 0.880466 inside [0.85, 0.905173] |

#### Batch 3 — 19 tools, receipt: `battery_batch3/receipt.json` (2026-07-20)

12 integrated, 7 blocked.

| Tool | State | Receipt | Computed evidence |
|---|---|---|---|
| blackjax | INTEGRATED | `battery_batch3/test_blackjax.py` | NUTS posterior over gamma from real lawD trajectory likelihood; mean 0.6047 inside the 95% CI of receipt gamma = 0.5 |
| cma | INTEGRATED | `battery_batch3/test_cma.py` | CMA-ES evolves real probe-order IG to 33.72586, beats random mean |
| deap | INTEGRATED | `battery_batch3/test_deap.py` | GA on same objective, 33.94900, beats random mean |
| pymoo | INTEGRATED | `battery_batch3/test_pymoo.py` | Same objective, 33.72586, beats random mean |
| gymnasium | INTEGRATED | `battery_batch3/test_gymnasium.py` | Wraps real occluded-object probe sequences as a Gym env; 100 load-bearing steps, total reward 42.0 |
| osqp | INTEGRATED | `battery_batch3/test_osqp.py` | QP solve on a real channel projection subproblem, residual 7.59e-06 |
| xitorch | INTEGRATED | `battery_batch3/test_xitorch.py` | Linear solve on a real capacity-word Gram matrix vs numpy, max abs diff 0.0 |
| torchode | INTEGRATED | `battery_batch3/test_torchode.py` | Bloch ODE integration on receipt-derived damping, abs error 2.29e-07 vs analytic |
| equinox | INTEGRATED | `battery_batch3/test_equinox.py` | Tiny readout on real batch-2 senses features, heldout accuracy 0.625 > chance |
| optax | INTEGRATED | `battery_batch3/test_optax.py` | SGD on same linear readout, heldout accuracy 0.625 > chance |
| jaxlie | INTEGRATED | `battery_batch3/test_jaxlie.py` | SO3 transport of a real Bloch vector, max abs error 2.38e-08 |
| igraph | INTEGRATED | `battery_batch3/test_igraph.py` | `connected_components` on real capacity graphs, bitwise match to rustworkx receipt, 4 components |
| dynamax | BLOCKED | `battery_batch3/test_dynamax.py` | `AttributeError: module 'jax.interpreters.xla' has no attribute 'pytype_aval_mappings'` |
| tensorflow-probability | BLOCKED | `battery_batch3/test_tensorflow_probability.py` | Same interpreter-internals error via the jax substrate |
| evotorch | BLOCKED | `battery_batch3/test_evotorch.py` | `AttributeError: 'NoneType' object has no attribute 'evals'` in the internal evals path |
| cvxpylayers | BLOCKED | `battery_batch3/test_cvxpylayers.py` | `NotImplementedError: Complex variables are not yet supported` |
| flax | BLOCKED — honest negative | `battery_batch3/test_flax.py` | Heldout accuracy exactly 0.5 == chance on real senses features (not a crash, a real negative result) |
| hdbscan | BLOCKED at batch3, superseded | `battery_batch3/test_hdbscan.py` | 32 clusters vs gudhi-source 4, gate missed — traced afterward to a batch3 test-code bug (complex `rho_fast` cast that silently zeroed every imaginary part); see batch4 retry below |
| kahypar | BLOCKED at batch3, superseded | `battery_batch3/test_kahypar.py` | Constructor mismatch reported as an arm64-wheel limitation — traced afterward to a batch3 test-code bug (Mode/Objective/coarsening left undefined); see batch4 retry below |

#### Batch 4 — 12 tools, receipt: `battery_batch4/receipt.json` (2026-07-21), own recorded counts: 10 INTEGRATED / 1 BLOCKED / 1 PRUNED

Includes two corrected retries of batch-3 rows.

| Tool | State | Receipt | Computed evidence |
|---|---|---|---|
| pymc 6.0.1 | INTEGRATED | `battery_batch4/test_pymc.py` | NUTS posterior over gamma, mean 0.596113, diff vs batch-3 blackjax 0.0086, inside the 0.15 agreement gate |
| arviz 1.1.0 | INTEGRATED | `battery_batch4/test_arviz.py` | rhat 1.0 (< 1.01 gate), ess_bulk 681 on a 4-chain pymc trace |
| flowMC 0.6.0 | INTEGRATED | `battery_batch4/test_flowMC.py` | Normalizing-flow-assisted MALA posterior, mean 0.601474, diff vs blackjax 0.0033 |
| nutpie 0.16.10 | INTEGRATED | `battery_batch4/test_nutpie.py` | Rust NUTS sampler on the same pymc model, mean 0.595527, diff vs blackjax 0.0092 |
| numba 0.65.0 | INTEGRATED | `battery_batch4/test_numba.py` | `@njit` union-find, bitwise-equal to pure-python on all 9 packets, 3.552x post-warmup speedup |
| datasketch 1.9.0 | INTEGRATED | `battery_batch4/test_datasketch.py` | MinHash Jaccard estimate on 9 real word sets, max abs diff 0.0344 (< 0.15 gate) |
| sparse 0.18.0 | INTEGRATED | `battery_batch4/test_sparse.py` | `sparse.COO` adjacency/degree/Laplacian recompute vs dense numpy, all 3 max-abs-diffs exactly 0.0 |
| kahypar 1.3.7 | INTEGRATED (retry, corrected API) | `battery_batch4/test_kahypar.py` | Loads the cotengra-shipped `.ini` profile correctly before `setK`/`setEpsilon`; partitions a real 70-word hypergraph into 35/35, 0 cut hyperedges |
| hdbscan | INTEGRATED (retry, corrected reconstruction) | `battery_batch4/test_hdbscan.py` | Fixed complex reconstruction; 6 clusters at min_cluster_size=5, within the close-gate (\|6-4\|<=2) of the gudhi source-basin receipt |
| ray 2.54.1 | INTEGRATED | `battery_batch4/test_ray.py` | `ray.remote` parallel map of 4 real packet checks, identical to the serial run on all 4 |
| oryx | BLOCKED | `battery_batch4/test_oryx.py` | Same `jax.interpreters.xla.pytype_aval_mappings` break as dynamax/tfp (its `bijectors` import forces the tfp-jax substrate) |
| treescope 0.1.10 | PRUNED (display-only) | `battery_batch4/test_treescope.py` | Renders a real 95,129-char HTML string containing a known real key; explicitly "no computational role in any sim leg" per the ledger's own finding |

#### Batch 5 — 13 tools, receipt: `battery_batch5/receipt.json` (2026-07-20)

10 newly integrated; the other 3 (dynamax, jax-verify, oryx) are reconfirmations of
already-known blocks, not new distinct blocked tools.

| Tool | State | Receipt | Computed evidence |
|---|---|---|---|
| derivative 0.6.3 | INTEGRATED | `battery_batch5/test_derivative.py` | Savitzky-Golay derivative of a real 31-tick relative-entropy trajectory, max abs diff vs np.gradient 0.0436 (< 0.05 gate), sign consistent with monotone decay |
| optht | INTEGRATED | `battery_batch5/test_optht.py` | Gavish-Donoho rank on real 384x32 SVD, rank 16, within 8 of the PCA 90%-variance elbow (rank 8) |
| cirq 1.6.1 | INTEGRATED | `battery_batch5/test_cirq.py` | Real two-sheet stage circuit rebuilt from the exact KAK gate list; unitary agrees with expm to 8.646e-15 (pennylane reference 8.713e-15) |
| qiskit 2.4.1 | INTEGRATED | `battery_batch5/test_qiskit.py` | Same circuit, corrected for qiskit's reversed wire convention; agreement 8.757e-15 |
| pennylane-lightning | INTEGRATED | `battery_batch5/test_pennylane_lightning.py` | `lightning.qubit` vs `default.qubit` on the same real stage state; agreement 2.269e-16 (< 1e-9 gate) |
| pynndescent 0.6.0 | INTEGRATED | `battery_batch5/test_pynndescent.py` | Approximate 10-NN graph on 384 real trajectory states, mean recall 0.9835 vs exact sklearn kNN (> 0.9 gate) |
| miniKanren (kanren + logical-unification) | INTEGRATED | `battery_batch5/test_minikanren.py` | Relational query over a real 8-word grammar finds ['1000','1110'], exactly matching brute-force enumeration |
| moocore 0.2.0 | INTEGRATED | `battery_batch5/test_moocore.py` | Bi-objective front hypervolume 3.425213 over a real probe-order objective; Pareto-optimality confirmed |
| ribs (pyribs) 0.10.0 | INTEGRATED | `battery_batch5/test_ribs.py` | CMA-ES-driven QD archive best 33.949 (global optimum) vs random mean 32.613, 32 cells populated |
| sparsediffpy 0.3.0 | INTEGRATED | `battery_batch5/test_sparsediffpy.py` | CSR Jacobian of the real amplitude-damping Liouvillian, densifies to exact match with the real generator, max abs diff 0.0 |
| dynamax (reconfirmed) | BLOCKED | `battery_batch5/test_dynamax.py` | Same root cause confirmed: no separate jax-substrate path to route around |
| jax-verify (reconfirmed) | BLOCKED | `battery_batch5/test_jax_verify.py` | Plain `import jax_verify` already fails at module-load |
| oryx (reconfirmed) | BLOCKED | `battery_batch5/test_oryx.py` | Same tfp-jax-substrate break, no alternate entry point bypasses it |

gpjax was skipped: `ModuleNotFoundError: No module named 'gpjax'`, not installed.

---

## 2. SMT / proof tools

| Tool | State | Receipt | Computed evidence |
|---|---|---|---|
| z3-solver | INTEGRATED | `system_v8/engine_native/results/jax_scale/receipt.json`, `L14_smt_kill_set_proof` | Dual-prover K1 kill-set proof: z3_zz, z3_xx, z3_zx, z3_xz all `True`, gating `L14_K1_kill_set_structurally_exact_dual_smt = True`. Package note: "load_bearing: half of the dual-SMT K1 kill-set proof" |
| cvc5 | INTEGRATED | same receipt | cvc5_zz, cvc5_xx, cvc5_zx, cvc5_xz all `True`, agreeing with z3 on all 4; package note: "second prover of the same claim; both must agree or the check fails" |
| z3-solver + cvc5 (Phi0 seam) | INTEGRATED | `system_v8/manifold/results/proof_order_lane.json` | 8 proof obligations; z3 and cvc5 agree on every one (`solvers_agree: true` x8) — 4 unsat, 4 sat, no disagreement |
| Z3.jl | INTEGRATED | `system_v8/engine_estate/results/julia/receipt.json` (package present, section PASS) | Julia-side SMT binding, exercised as part of the Julia engine self-test; no standalone Julia-side SAT/UNSAT receipt was found distinct from the Python z3-solver rows above |
| sympy | claimed INTEGRATED by `TOOL_LEDGER.md` ("proof lanes"), **ungrounded this pass** | none found | `grep -rli sympy system_v8` returns only `TOOL_LEDGER.md` itself — no code file, test file, or receipt anywhere in `system_v8` imports or exercises sympy directly. This is reported as a finding, not silently repeated: the summary-line claim currently has no independent receipt behind it in this repo tree |
| auto_LiRPA | INTEGRATED, v5-era only | `system_v5/evidence/formal_scout_readiness_index.json` and related v5 evidence files | Self-labeled "(v5 scout)" by the ledger itself; not independently re-verified anywhere under `system_v8` in this pass |

---

## 3. Lev OS components

| Component | Verified-vs-reported | Evidence |
|---|---|---|
| `lev exec` / `lev gate` / `lev trace` | VERIFIED, live | `lev --help` (run this session) lists `exec`, `exec-status`, `gate`, `trace` as a top-level command group. 7 `exec.gate.run` events exist in `~/.local/share/lev/events/runtime-events.jsonl`, spanning 2026-07-16 to 2026-07-20, with real `execId`s, `verdict`/`branch_taken`, `exit_code`, and `evidence_refs` pointing at actual stdout/stderr artifact files under `~/.local/share/lev/execution-ledger/artifacts/` |
| ClaimGate (`claimgate/claimgate.py`) | VERIFIED, but not a registered Lev plugin | Deterministic 6-check receipt validator (classification, promotion-without-canonical-evidence, verdict-inflation, controls-missing/copy, negative-mutual-information, preregistration-missing), exit-code only, no LLM judgment. Its Lev wiring is a `lev exec --verifier="python3 claimgate/claimgate.py <path>"` invocation, not a registered `lev` subcommand — `lev --help` shows no `claimgate` group, confirming `claimgate/README.md`'s own framing ("independent plugin that consumes Lev... not part of Lev core"). One specific run is durably logged: `execId=473cd6c1e00e`, `branch_taken: "fail"`, `exit_code: 1`, against `manifold_unified_v1/receipt.json`, confirmed present in `runtime-events.jsonl` this session |
| ClaimGate — full sweep | VERIFIED | `claimgate/results/first_sweep.json`: 109 receipts checked, 62 admit, 47 reject. The README names two specific real rejections (not path-special-cased): `manifold_unified_v1/receipt.json` fails `preregistration_missing`; `nested_manifold/results/stage64/receipt.json` fails `classification_missing` despite `all_pass: true` |
| fuel_adequacy_gate (`fuel_gate/fuel_adequacy_gate.py`) | VERIFIED | `fuel_gate/results/first_pool_verdict.json`: real exit-code gate ran against a 4-candidate pool and correctly returned `verdict: "HOLD_INSUFFICIENT_FUEL"` (required 6 variation slots, only 4 candidates present, `a_required_variation_slots: pass=false`) — the gate is doing its job, not rubber-stamping |
| Ratchet kernel (`system_v7/constraint_core/ratchet/ratchet_engine.py`) | VERIFIED, re-run live this session | `python3 system_v7/constraint_core/ratchet/ratchet_engine.py --self-test` printed, in this session: `PASS order_open_ratchet_v0_5` / "mass candidate batches, all gate orders/decompositions, coface gradients, and anti-canon controls verified" |
| flowmind (`lev flowmind`, `flowmind-debug`, `execute-epic`) | REPORTED only | Present as its own top-level command group in `lev --help`; not exercised or evidenced in any receipt read this pass |
| Trace &rarr; partition bridge (the ratchet's own admission-critical missing piece) | REPORTED as missing, by the source doc itself | `ROOT/RUNNING_THE_RATCHET_ON_ENGINES_AND_LEV.md` line 31 names this explicitly: "[THIS IS THE MISSING PIECE]" — carried forward here rather than silently dropped |

Lev OS overall state per `TOOL_LEDGER.md` line 188: `PARTIAL` ("exec/gate/trace
alive; ClaimGate plugin + per-lane evidence routing pending"). That is the
non-standard fifth label flagged in the scope note above — accurate on the
evidence re-checked here: the exec/gate/trace primitives are real and
exercised, but ClaimGate rides on top as an external verifier command rather
than a first-class Lev plugin, and only one of the nine ratchet stages named
in that same document (`lev exec` for ClaimGate) has an actual Lev-orchestrated
demo run.

---

## 4. Repos / packs / services vendored

| Item | State (per `TOOL_LEDGER.md`) | Independently checked this pass | Evidence |
|---|---|---|---|
| codex1 (CLI, gpt-5.6-terra roster) | INTEGRATED | VERIFIED | `codex1` is a real shell alias (`CODEX_HOME="$HOME/.codex" codex`); `~/.codex` exists with live session/state data (`session_index.jsonl`, `models_cache.json`, `sessions/`, `skills/`, dated today) |
| grok CLI (grok-build-0.1) | INTEGRATED | VERIFIED (binary only) | `~/.grok/bin/grok` exists on disk. Did not independently re-run a grok audit this pass; "first audit landed" claim not re-verified beyond the binary's presence |
| NVIDIA API (40 rpm, referee-panel pattern) | INTEGRATED | VERIFIED | `system_v8/loop3_senses/results/senses_v2_slow_memory/nvidia_referee_receipts.json` contains real, distinct model responses keyed by model id: `deepseek-ai/deepseek-v4-pro`, `nvidia/llama-3.3-nemotron-super-49b-v1.5`, `moonshotai/kimi-k2.6`, `qwen/qwen3.5-397b-a17b`, `z-ai/glm-5.2`, `openai/gpt-oss-120b` |
| xAI API | INTEGRATED | PARTIALLY VERIFIED | `system_v8/manifold/results/cross_audit_20260718.json` records a response tagged `model: "grok-4.5"` alongside NVIDIA-style model ids in the same audit round — consistent with xAI access, but I did not independently trace which specific API key/endpoint served that call |
| codebase-memory-mcp index | INTEGRATED | CONNECTIVITY VERIFIED, index-use not re-run | `mcp__codebase-memory-mcp__*` tools are present and callable in this session's tool set, confirming the server is connected; I did not invoke `search_code`/`query_graph` this pass to re-verify index freshness |
| cocoindex_wiki index | INTEGRATED | VERIFIED (index artifacts present) | Real `.cocoindex_code` directories exist at `~/wiki/.cocoindex_code`, `~/Codex-Ratchet/.cocoindex_code`, and `~/.cocoindex_code` — genuine index output on disk, not merely a claimed connection |
| wiki (`~/wiki`) | INTEGRATED | VERIFIED | Directory exists, actively written (contents dated through 2026-07-20) |
| Pack-183 engine (vendored, hash-bound) | INTEGRATED | NOT INDEPENDENTLY RELOCATED | No file or directory literally named "Pack-183" was found by filename search in this pass; the ledger's own claim is carried forward but not re-grounded here — treat as reported, not re-verified |
| owner packs 167-189 (ingested) | INTEGRATED | PARTIALLY VERIFIED | Concrete artifacts found: `ratchet_engine/pack177v2` (directory, referenced and re-run via memory index as "177v2 reruns clean"), `ROOT/*_pack178.md` (3 files), `system_v8/inputs/pack_artifacts/exceptional_stack_geometry_pack186.py`, `...pack188.py`. Did not enumerate all 23 pack numbers (167-189) individually this pass |
| codex2 (gpt-5.5 roster) | UNTESTED ("idle this session" per ledger) | INSTALLATION VERIFIED, non-idle claim not checked | `~/.codex-second` exists with its own session/state data — a real, separate install, distinct from codex1's `~/.codex`. Whether it was actually idle in the specific session TOOL_LEDGER.md describes was not independently checked |
| OpenRouter | UNTESTED ("used once 07-18") | NOT CHECKED | Carried forward from the ledger; no receipt located or searched for in this pass |
| Gemini key | UNTESTED | NOT CHECKED | Carried forward from the ledger |

---

## 5. UNTESTED tail

Installed and importable; no integration receipt exists yet. Per the ledger's
own rule, these may not be leaned on for any claim until a receipt exists.

| Domain | Items |
|---|---|
| Julia (2) | ITensorNetworks, GeometryBasics |
| Python sim-stack (16 named) | gpjax (confirmed not installed this session — `ModuleNotFoundError`), bayeux-ml, dm-haiku, diffcp, clarabel, scs, highspy, hoptorch, (pytorch-)lightning, torchmetrics, jaxga, optimistix, orbax-checkpoint, scikit-learn, trimesh, pyvista/vtk |
| Repos/services (3) | OpenRouter, Gemini key, codex2 |

---

## 6. Honest totals

Method: one row per distinct integration receipt (a shared receipt covering
two co-tested packages, such as torchrl+tensordict or jax+jaxlib, counts once
here; where the ledger's own summary line double-lists a package under two
names — see the pennylane note below — that is flagged, not silently
resolved).

| Domain | INTEGRATED | BLOCKED | PRUNED | UNTESTED | Other |
|---|---|---|---|---|---|
| Julia | 25 | 0 | 0 | 2 | — |
| Python sim-stack | 76 (recounted; see note) | 8 live + 2 historical-superseded | 2 | 16 named | — |
| SMT/proof (cross-listed, not double-counted into the totals above) | z3, cvc5 already inside the 76; sympy flagged ungrounded | — | — | — | — |
| Repos/services/infra | 9 | 0 | 0 | 3 | 1 PARTIAL (Lev OS) |
| **Grand total tracked items** | **110** | **8 live** | **2** | **21** | **1 PARTIAL** |

Notes on the two reconciliation gaps found while building this table:

1. `TOOL_LEDGER.md` line 176 headlines Python `BLOCKED (10)` but names only 8
   tools (cotengra's direct executor, jax-verify, dynamax,
   tensorflow-probability, evotorch, cvxpylayers, flax, oryx). The count only
   reaches 10 if the two batch-3 rows later corrected by batch-4 retries
   (hdbscan, kahypar — both test-code bugs, not real tool limitations) are
   counted as historical blocks. Both are INTEGRATED in their final,
   corrected state and are counted that way in section 1.5 and in the total
   above; the "10" in the source ledger conflates current and historical
   status without saying so.
2. `TOOL_LEDGER.md` line 175 headlines Python `INTEGRATED (77)`. A careful
   recount of the named list, treating one receipt as one row, reaches 76.
   The likely source of the one-item drift: `pennylane-lightning` is named
   twice — once folded into "pennylane+lightning" in the already-earned
   block, once again as its own batch-5 entry testing the lightning backend
   specifically. Both receipts are real and both are listed in section 1.5;
   this is a bookkeeping-precision note about the summary line, not a
   missing-evidence finding.
3. `battery_batch2/results/quantumtoolbox.json` carries `pass: false` (max
   error 1.458e-8 against a declared 1e-8 gate) while its own row is labeled
   `INTEGRATED`. `TOOL_LEDGER.md` documents this openly ("gate miss
   documented") rather than hiding it, which is why it is counted as
   INTEGRATED-with-caveat here rather than reclassified — but it is the one
   row in the entire ledger where the verdict label and the receipt's own
   `pass` field disagree.
4. sympy is claimed INTEGRATED in the Python summary line with no receipt
   anywhere under `system_v8` (checked by case-insensitive grep across the
   whole tree). It is excluded from "76" above pending a real receipt, and
   listed separately in section 2 as a finding.

---

## 7. Deepest and shallowest integration

Deepest: the three-engine integration chain in section 1.4
(`system_v8/engine_estate/results/integration/receipt.json`). It is the only
receipt in the whole estate where the three declared sim engines do not just
run side by side — torch's graph output becomes jax's sweep input, jax's
selected gamma* becomes julia's integration parameter, and the single chained
number that comes out the other end (S_master = 4.799504063233) is checked
against an independent single-process numpy control at every stage, agreeing
to 1.5e-14 end to end. This is a genuine data-flow dependency across all
three engines, not a parallel cross-check.

Shallowest, full stop: treescope 0.1.10 (`battery_batch4/test_treescope.py`),
labeled `PRUNED (display-only)` by the ledger's own finding. It is genuinely
exercised — it renders a real 95,129-character HTML string from a real
receipt dict, and the number recorded is that string's own length — but the
ledger's own words are "no computational role in any sim leg." It is a
pretty-printer, not a computation.

Shallowest among tools still labeled INTEGRATED: vjepa2
(`system_v8/tool_ledger/test_vjepa2_instantiate.py`). The scope was
deliberately narrow — instantiate a tiny, randomly-initialized config and run
one forward pass on random noise, no pretrained weights, no real video data,
no comparison to any reference law. It produced a real tensor of the right
shape ([1, 8, 48]) and surfaced a real upstream bug along the way, which is
why it clears the INTEGRATED bar at all — but among everything labeled
INTEGRATED in this inventory, it carries the least computational weight
behind the label.
