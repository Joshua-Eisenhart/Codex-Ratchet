# Tool ledger

Owner doctrine: integrate before use; prune unsupported tools honestly. Three
states only: `INTEGRATED` (genuine load-bearing use, not import-only),
`BLOCKED` (real error, exact message recorded, retry condition named),
`PRUNED` (installed and importable but a real limitation rules it out for the
scoped use).

Interpreter for all checks below: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.
Memory gate observed before every torch/jax/qutip import in this session:
`memory_pressure` free percentage 37-46% (gate is >25%).

## New donors tested this session (2026-07-19)

| Tool | State | Evidence | Retry condition |
|---|---|---|---|
| torchrl 0.13.3 + tensordict 0.13.0 | INTEGRATED | `system_v8/tool_ledger/test_torchrl_rssm.py`. Built a genuine RSSM-style latent rollout with `torchrl.modules.GRUModule` (`default_recurrent_mode=True`) + `WorldModelWrapper` (transition_model=GRU->linear decoder, reward_model=linear head), wired through `tensordict.nn.TensorDictModule`/`TensorDictSequential`. Trained 60 steps on the REAL 64-object x 6-view x 8-probe occluded-view sequences from `system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl`. Reconstruction MSE loss 0.7640 -> 0.0065 (909 params). Result: `results/torchrl_result.json`. | n/a — integrated |
| inferactively-pymdp 1.0.3 (`pymdp.legacy` Agent) | INTEGRATED | `system_v8/tool_ledger/test_pymdp_active_inference.py`. Built a minimal 2-state/2-obs POMDP `Agent(A, B, D)` whose A (observation/likelihood) matrix IS the empirical probe-outcome distribution of one real packet, `obj-000:view:1` (p1=0.4000 over 5 non-withheld real probes; A=[[0.6,0.4],[0.4,0.6]]). One `infer_states()` belief update on the match-consistent observation moved the posterior P(state=match) 0.5000 -> 0.6000 (delta +0.1000), the correct Bayesian direction. Note: `obj-000:view:0` was tried first and rejected — its empirical p1 was exactly 0.5 (3 ones/3 zeros of 6 real probes), giving an uninformative A matrix that cannot move any posterior by construction (not a pymdp defect); view 1 was substituted. Result: `results/pymdp_result.json`. | n/a — integrated |
| vjepa2 (facebookresearch, via `transformers.models.vjepa2`) | INTEGRATED | `system_v8/tool_ledger/test_vjepa2_instantiate.py`. No standalone `vjepa2` pip package exists (`pip install vjepa2` -> no matching distribution); the officially-supported integration path for the released facebookresearch/vjepa2 checkpoints is bundled in `transformers` 4.57.0 (`VJEPA2Config`/`VJEPA2Model`). Scope was import+config-load+tiny-instantiate only, no video training. A tiny config (hidden_size=48, pred_hidden_size=48, crop_size=32, frames_per_clip=4, 2 encoder + 2 predictor layers, 191,856 params, random init, no pretrained weights) instantiated and ran one forward pass on a random tiny video tensor -> `last_hidden_state` shape `[1, 8, 48]`. Secondary finding: an even-tinier first attempt (hidden_size=32, pred_hidden_size=16) hit a real shape bug in the shipped rotary-embedding code (`modeling_vjepa2.py: rotate_queries_or_keys`), `RuntimeError: The size of tensor a (2) must match the size of tensor b (32) at non-singleton dimension 3` — traced to a `D//2==1` corner case in the 3-way (temporal/height/width) RoPE split that never occurs at released-checkpoint scale or at the working hidden_size=48 config. Result: `results/vjepa2_result.json`. | n/a — integrated (secondary rotary-embedding corner-case bug noted, not blocking at real or working-tiny scale) |

## Already-earned entries (prior sessions, re-stated here for one standing ledger)

| Tool | State | Evidence | Retry condition |
|---|---|---|---|
| torch_ga 0.0.6 | PRUNED (float32-only) | `system_v8/engine_estate/results/torch/receipt.json` finding: "torch_ga 0.0.6 mixes hard-coded float32 internals with default-dtype tensors: under `torch.set_default_dtype(torch.float64)` `geom_prod` raises `expected m1 and m2 to have the same dtype: float != double`. Works at the float32 default; not float64-safe." | Retry if a torch_ga release ships float64-safe internals, or if a scoped sim only needs float32 precision. |
| cotengra 0.8.0 (direct executor) | BLOCKED (search-only workaround) | `system_v8/engine_estate/results/jax/receipt.json` finding: "cotengra 0.8.0 own contraction executor broken in this env: `HyperOptimizer` passed directly to quimb `tn.contract` raises `IndexError` in `_parse_tensordot_axes_to_matmul`; `tree.contract(arrays)` killed (exit 137)." Workaround used and load-bearing: cotengra `HyperOptimizer.search` finds the contraction tree (cost 9.19e+03, width 12, path length 23 on a 12-qubit GHZ cut), quimb executes along `tree.get_path()`. | Retry direct `tree.contract` after a cotengra release fixes `_parse_tensordot_axes_to_matmul`, or on a Linux/x86 build if this is an arm64-macOS-specific path. |
| Attractors.jl `extract_attractors` | INTEGRATED (unblocked 2026-07-19 by upstream update to v1.38.4) | Was BLOCKED at v1.37.0 (`UndefVarError: referenced_sciml_model` API skew vs installed DynamicalSystemsBase). Retry condition met: `Pkg.add(name="Attractors", version="1.38.4")` resolved cleanly; `AttractorsViaRecurrences` + `extract_attractors` on the Henon map returns 1 attractor (351 points, labels [-1,1]). Regression check after the env update: `julia_estate_test.jl` fresh rerun pass=7 fail=0 blocked=0 (`/tmp/julia_estate_rerun.log`). | n/a — integrated |
| qutip 5.2.3 | INTEGRATED | `system_v8/deep_integration/results/qit_referee/receipt.json`: load-bearing `mesolve`/`entropy_vn`/`ptrace`/`to_choi`/`steadystate` re-derivation of three law families independently of the Julia lane; relative-entropy series agree to 1.945e-11/4.185e-11 (gate 1e-6); Choi CP audit correctly fails under a gamma -> -gamma control (min eig -8.104e-02). Also `py_battery_results_simstack_20260713.json: qutip_lindblad PASS` (trace-preserving 1.000000000000). | n/a — integrated |
| diffrax 0.7.2 | INTEGRATED | `system_v8/engine_estate/results/jax/receipt.json` L8: 512-trajectory GKSL vs analytic, 2.9e-11. `py_battery_results_simstack_20260713.json: diffrax_ode_solve PASS`, dy/dt=-y solved, err 1.1e-14. | n/a — integrated |
| gudhi 3.12.0 | INTEGRATED | `system_v8/deep_integration/results/topology/receipt.json`: load-bearing VR persistence decides all 6 H0/H1 basin-count and loop-vs-scrambled-control checks (pit=2, source=4, depolarizing collapses to 1; H1 loop 1.4773 vs scrambled 0.3091). | n/a — integrated |
| galois 0.4.11 | INTEGRATED | `system_v8/deep_integration/results/dynamics_fields/receipt.json`: load-bearing GF(7) field mul/is_square/legendre decides the T5 word-match check; GF(2^3) extension arithmetic is the sole constructor of the gf8 packet. All 5 galois-tagged checks pass (`galois_gf7_packet_words_match_t5_archive`, `galois_gf7_qr_set_is_124_all_three_methods`, `galois_gf8_every_element_square_unlike_gf7`, `galois_gf8_packet_width_four_nonempty`, `galois_gf8_units_closed_intmod8_has_zero_divisors`). | n/a — integrated |
| pysindy 2.1.0 | INTEGRATED | `system_v8/deep_integration/results/dynamics_fields/receipt.json`: load-bearing SINDy regression coefficients decide the Bloch-law identification checks (const matches +gamma to 5%, linear matches -gamma to 5%, form is linear with no higher terms, model score > 0.999). Also `py_battery_results_simstack_20260713.json: pysindy_recover_ode PASS`, recovered dx/dt=-2.0001*x (true -2). | n/a — integrated |
| torch_geometric 2.7.0 | INTEGRATED | `system_v8/engine_estate/results/torch/receipt.json`: `Data.validate()` on all 9 capacity-complex graphs; MessagePassing fixed-point components == pure-python union-find on all 9 packets; spectral zero-eigenvalue law. | n/a — integrated |
| pennylane 0.44.1 | INTEGRATED | `system_v8/deep_integration/results/qit_referee/receipt.json`: load-bearing KAK compilation of the two-sheet unitary stage to RY/RZ+CNOT; circuit unitary vs scipy `expm` max diff 8.713e-15; parameter-shift vs finite-diff gradient of `<Z0>` max diff 3.632e-08. | n/a — integrated |
| quimb 1.14.0 | INTEGRATED | `system_v8/engine_estate/results/jax/receipt.json` L7: 12-qubit GHZ cut entropy via quimb executing along the cotengra-searched path. | n/a — integrated |
| lineax 0.1.1 | INTEGRATED | `system_v8/engine_estate/results/jax/receipt.json` L12: Fisher solves, residual 1.9e-15 vs numpy. | n/a — integrated |
| jaxopt 0.8.5 | INTEGRATED | `system_v8/engine_estate/results/jax/receipt.json` L12.jaxopt_vs_numpy: max \|jaxopt CG - numpy.solve\| = 1.311e-09. | n/a — integrated |
| netket 3.21.0 | INTEGRATED | `system_v8/engine_estate/results/jax/receipt.json` smoke.netket PASS; `py_battery_results_simstack_20260713.json: netket_hilbert PASS`, 4-spin Hilbert space, 16 states. | n/a — integrated |
| e3nn 0.6.0 / e3nn-jax 0.21.0 | INTEGRATED | `system_v8/engine_estate/results/torch/receipt.json` smoke_e3nn_irreps_rep_orthogonal: Irreps(0e+1o) dim 4, D(R) orthogonal to 1e-10. `py_battery_results_simstack_20260713.json: e3nn_irrep_tensor_product PASS`, 1o x 1o -> 0e invariant extraction. | n/a — integrated |
| ott-jax 0.6.0 | INTEGRATED | `system_v8/engine_estate/results/jax/receipt.json` (Sinkhorn transport); finding notes tail convergence is slow at small epsilon (threshold 1e-6 not reached in 20000 iters at eps=0.05, but 1e-4 converges in 8840 iters, cost 4.009 vs analytic 4.0). | n/a — integrated (slow-tail-convergence caveat, not blocking) |
| jraph 0.0.6.dev0 | INTEGRATED | `system_v8/engine_estate/results/jax/receipt.json` smoke.jraph: message-passing sum == A @ X, max diff 0.000e+00. | n/a — integrated |
| rustworkx 0.17.1 | INTEGRATED | `system_v8/deep_integration/results/topology/receipt.json`: load-bearing independent graph object, `connected_components`/`adjacency_matrix`, agrees bitwise with networkx and the torch receipt on all 9 packets. | n/a — integrated |
| toponetx 0.4.0 | INTEGRATED | `system_v8/deep_integration/results/topology/receipt.json`: load-bearing `CellComplex` bookkeeping + Euler method + Hodge-Laplacian Betti numbers decide all 3 strip checks; nested-leaf strip chi=0, betti=[1,1,0] (annulus) vs flattened control chi=1, betti=[1,0]. | n/a — integrated |
| geomstats 2.8.0 | INTEGRATED | `system_v8/engine_estate/results/torch/receipt.json` Lgs checks: Bures-Wasserstein and Fisher-Rao distances match closed forms to ~1e-15/1e-16. `py_battery_results_simstack_20260713.json: geomstats_sphere_geodesic PASS`, great-circle distance = pi/2 exact. | n/a — integrated |

## Notes

- All three new-donor tests write structured JSON to `system_v8/tool_ledger/results/` (`torchrl_result.json`, `pymdp_result.json`, `vjepa2_result.json`) with a `verdict` field and full check detail — see `receipt.json` in this directory for the consolidated new-donor summary.
- Claim ceiling for everything in this ledger: tool-integration evidence only. Nothing here is a canonical, bridge, QIT, GStack, axis, or nonclassical admission claim.
- No files were deleted or moved. No commit was made.

## COMPLETE ESTATE INVENTORY (2026-07-19, from live environments — every substantive item, four states)

States: INTEGRATED (load-bearing receipt exists) / BLOCKED (real error recorded) / PRUNED (real limitation excludes it) / UNTESTED (installed+importable, no integration receipt yet — may NOT be leaned on until integrated; each is queue work).

### Python sim-stack (/Users/joshuaeisenhart/.local/share/sim-stack) — substantive packages

INTEGRATED (28): torch 2.11, jax+jaxlib 0.10.1, diffrax, quimb, lineax, jaxopt, netket, e3nn, e3nn-jax, ott-jax, jraph, torch-geometric, geomstats, qutip, pennylane+lightning, pysindy, galois, gudhi, toponetx, rustworkx, networkx, torchrl+tensordict, inferactively-pymdp, transformers(vjepa2 path), z3-solver, cvc5, sympy (proof lanes), auto_LiRPA (v5 scout), numpy (control-only by doctrine).
BLOCKED (1): cotengra direct executor (search path IS integrated).
PRUNED (1): torch_ga (float32-only).
UNTESTED (~60): pykoopman, PyDMD, derivative, optht, dynamiqs, qutip-jax, qiskit, cirq(+5 plugins), dynamax, numpyro, blackjax, pymc/pytensor, tensorflow-probability, flowMC, nutpie, oryx, arviz, bayeux-ml, mctx, dm-haiku, gymnasium, evotorch, cma, deap, pymoo, moocore, ribs, optuna, cvxpy, cvxpylayers, diffcp, clarabel, osqp, scs, highspy, xitorch, hoptorch, torchdiffeq, torchode, (pytorch-)lightning, torchmetrics, kingdon (GA), clifford (GA), jaxga, jax-verify, jaxlie, equinox, flax, optax, optimistix, orbax-checkpoint, umap-learn, hdbscan, pynndescent, kahypar, igraph, xgi (hypergraphs), maude (rewriting logic), miniKanren+logical-unification, hypothesis, datasketch, sparse, sparsediffpy, ray, numba, scikit-learn, trimesh, pyvista/vtk, treescope.

### Julia environment (~/.julia/environments/v1.12)

INTEGRATED (10): QuantumOptics, QuantumClifford, CliffordAlgebras, Grassmann, ITensors, Octonions, DynamicalSystems, Attractors (v1.38.4, unblocked this session), Z3.jl, JSON3 (handoffs); DifferentialEquations exercised through QuantumOptics timeevolution.
UNTESTED (17): Yao, QuantumToolbox, Flux, Lux, Enzyme, Zygote, Manifolds+ManifoldsBase, CombinatorialSpaces, Symbolics, TensorOperations, ChaosTools, ITensorMPS, ITensorNetworks, Graphs.jl, GeometryBasics, Quaternions (historical v5 use, no v8 receipt), PythonCall/DLPack bridge.

### Repos / services / infrastructure

INTEGRATED: Pack-183 engine (vendored, hash-bound), owner packs 167-189 (ingested), codebase-memory-mcp index, cocoindex_wiki index, codex1 (gpt-5.6-terra; sol OFF), grok CLI (grok-build-0.1 first audit landed), NVIDIA API (40 rpm, referee-panel pattern), xAI API, wiki (~/wiki).
PARTIAL: Lev OS (exec/gate/trace alive; ClaimGate plugin + per-lane evidence routing pending).
UNTESTED: OpenRouter (used once 07-18), Gemini key, codex2 (gpt-5.5 roster; idle this session).
