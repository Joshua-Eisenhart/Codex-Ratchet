# Sim-engine / library / repo integration inventory + campaign

Owner directive 2026-07-22: the goal is the **sim engines and their library integration**,
not proving the manifold. Order: Lev-first, then JAX (fastest) across the whole manifold
one library at a time, then Julia the same way. PyTorch is minor. All proof/dynamics tools
must be integrated. Some unbound repos to work in too. Integrate slowly, as resources allow.

Status legend: **INTEGRATED** = used load-bearing in a committed sim · **AVAILABLE** =
imports in the sim-stack env, not yet load-bearing in a sim · **REPO** = a checkout to triage.

## Manifold sim set (what each engine must run)
15 ratcheting arrows: algebra_ladder, anticommutation_rung, bures_to_fubini_study,
cut_dependent_entropy, extension_fibre_capacity, finite_to_continuum_rung, law_order_branch,
magma_smt_genuine, magma_to_semigroup, pure_to_vn, real_vs_complex_tomography,
renyi_alpha_axis, root_foundation, vn_to_shannon, vn_to_shannon_basis_relativity.
Plus 8 system_v8 executable sims.

## JAX (phase 1 — run all manifold sims, integrate libraries one by one)
- **INTEGRATED**: `dynamiqs` 0.3.4 (qutip-jax replacement — entropy_vn/ptrace/tensor; load-bearing in cut_dependent_entropy).
- **AVAILABLE** (integrate one at a time, measure usefulness per arrow): `diffrax` 0.7.2 (Lindblad/GKSL ODE), `netket` 3.21 (variational many-body), `quimb` 1.14 + `cotengra` 0.8 + `autoray` (tensor networks), `ott-jax` 0.6 (optimal transport), `e3nn-jax` 0.21 (SO(3)/SU(2) equivariance), `jaxopt` 0.8.5 + `lineax` 0.1.1 (root/linsolve, sidecar only), `equinox`/`flax` (modules), `blackjax` (sampling), `jax-verify` 1.0 + `auto_LiRPA` repo (NN bounds), `jaxga` (GA), `galois` 0.4.11 (finite fields — load-bearing candidate).

## Julia (phase 2 — same, after JAX) — carrier project system_v5/julia_carrier
- **INTEGRATED**: `QuantumOptics` (entropy_vn/ptrace; load-bearing in pure_to_vn + cut_dependent_entropy).
- **AVAILABLE**: `QuantumClifford`, `CliffordAlgebras`, `Grassmann`, `ITensors`/`ITensorMPS`, `Yao`, `QuantumToolbox`, `DifferentialEquations`, `DynamicalSystems`+`ChaosTools`+`Attractors` (basins), `Manifolds`, `Symbolics`, `Octonions`, `Quaternions`, `Z3`, `StaticArrays`.

## PyTorch (minor per owner) — INTEGRATED: torch complex128 (eigvalsh/einsum ptrace in cut_dependent_entropy). AVAILABLE: torch_geometric, torch_ga, geomstats, e3nn, torchdiffeq/torchode, xitorch.

## Proof / dynamics tools (all needed, engine-agnostic crossover)
- **INTEGRATED**: `z3` 4.16, `cvc5` 1.3.3 (dual-SMT, supportive in the arrows), `sympy` 1.14 (exact identities, load-bearing).
- **AVAILABLE**: `pysindy` 2.1.0 + `pykoopman` 1.2.1 + `pydmd` + `derivative` (dynamics identification — Koopman/SINDy arbiter lanes), `toponetx` 0.4 / `gudhi` 3.12 / `rustworkx` 0.17 / `xgi` 0.10 / `networkx` (topology), `galois` (finite fields), `maude` 1.6 (rewrite), Julia `Z3.jl`.

## Unbound repos (~/GitHub) — triage which bind to an engine or stand alone
`qics` (quantum-information conic solver — proof/optimization candidate), `deeptime`
(dynamics/ML — Koopman/MSM), `auto_LiRPA` (NN verification bounds — pairs with jax-verify),
`physlib`, `resclasses` (residue-class algebra), `codex-autoresearch`, `pysindy`/`pykoopman`
(source clones of the pip pkgs), the `leviathan-*` family + `lev` (Lev OS itself),
`hermes-agent*`, `AnyFlow`/`flowm`/`lpwm`/`le-wm`/`Sana`/`Sofia`/`alco` (unclear — inspect),
`stylegan3` (likely out of scope).

## Lev OS (phase 0 — first) — an admission/evidence/orchestration substrate, NOT a sim runtime
Verified 2026-07-22: `flowmind` is a COMPILER (YAML -> smartdown/prompt/hooks/schedule);
`event-dispatch` not a live command; CR is not a registered Lev project. The genuine CR<->Lev
bridge is `orchestration claimgate-steering consume` (host-recompute; enforced by dna/gates.yaml).
- **DONE**: `claimgate_plugin/run_through_lev.sh` — one command runs a sim receipt through the
  whole box (ClaimGate three-engine-seal + tier0 + claim_verify + floor -> Lev host-recompute).
  Verified on the three-engine cut_dependent_entropy: seal pass [jax,julia,torch], Lev recomputed.
- **NEXT for Lev-full**: set `claim_kind` on the arrows (field_only/manifold_sim/quantum_claim) so
  claim_verify resolves required depth instead of capping at INSUFFICIENT_DEPTH; register CR as a
  Lev project; compile the ClaimGate gate to Lev hooks via `flowmind --target hooks`.

## Campaign order
0. Lev-first: run every manifold receipt through `run_through_lev.sh`; deepen claim_kind + gates. (started)
1. JAX: give each of the 15 arrows a JAX leg, then integrate one JAX library at a time across all
   arrows, rerun, record which library is load-bearing where (some more useful than others).
2. Julia: same, one library at a time.
3. Proof/dynamics tools integrated as their own lanes (pysindy/pykoopman/z3/cvc5/topology).
4. Unbound repos triaged and bound where they add capability.
5. Integrated stacks composed from what proved load-bearing.

## SPEC UPDATE 2026-07-22 (owner — supersedes prior numpy rules)
- **2 engines**: JAX = base workhorse (the load-bearing relaxation, jax.numpy x64 + rich libs); Julia = authoritative canon (QuantumOptics + carrier). Both re-derive-verified by the seal.
- **numpy = CONTAINED satellite**, NOT banned (reverted the blanket reject). Allowed as the downstream CPU analytical layer (post-hoc pysindy/sympy/scipy/sklearn on JAX output), control-only, NEVER load_bearing, NEVER the sim engine. Containment = the seal's >=2-agreeing-engines + jax-re-derive requirement (proves the real work is on the engines, so numpy can only sit in the satellite).
- **PyTorch = LATER** — needs rented cloud GPUs; deferred. Not required by the seal (2 engines suffice).
- **Target machine = M1 MacBook Pro, 16GB unified memory.** Engineering constraints (from the Gemini M1 survival rules, grounded): SEQUENTIAL engine execution (never JAX-Metal + PyTorch-MPS concurrently — swap-death); JAX preallocation off (`XLA_PYTHON_CLIENT_PREALLOCATE=false`); half-precision perception models when PyTorch is eventually used; ~4-6GB active RAM ceiling per stage. Zero-copy on M1 UMA is genuinely zero-copy (shared silicon).
- **Gemini chain verdict**: stack REJECTED (cuts dynamiqs = breaks 4 working arrows; core = unintegrated pennylane/kingdon/V-JEPA2 + env-incompatible PythonCall/DLPack bridge not in carrier). KEEP: the M1 survival rules, the 4 engineering laws (SMT isolation, dimensionality bottleneck, DLPack layout-transpose, jaxtyping padding), and Gate M5 "claim semantic witness binding" (hardens the ClaimGate metadata-trust holes — worth building).

## MEASURED INTEGRATION MATRIX 2026-07-22 (from `pip list` + Project.toml + actual imports + receipt depth — supersedes the guesses above)
State legend: **INTEGRATED** = load_bearing in a committed arrow · **SUPPORTIVE** = cross-check role in a committed arrow · **AVAILABLE** = installed+importable, not load_bearing anywhere yet · **CONTROL** = contained satellite.

### Engines (measured)
- JAX 0.10.1 — INTEGRATED base (cut_dependent_entropy, pure_to_vn, renyi_alpha_axis, vn_to_shannon).
- Julia 1.12 QuantumOptics 1.2.6 — INTEGRATED authoritative (same 4 arrows, `*_julia.jl`).
- PyTorch 2.11.0 — DEFERRED; complex128 in cut_dependent_entropy only + system_v8 torch estate/graph.
- numpy 2.3.4 — CONTROL-ONLY; still load_bearing in the 9 CI-red receipts.

### INTEGRATED / SUPPORTIVE libraries (load-bearing or cross-check in a committed arrow)
- dynamiqs 0.3.4 — INTEGRATED (JAX quantum leg in all 4 numpy-free arrows).
- QuantumOptics 1.2.6 (Julia) — INTEGRATED (authoritative leg in all 4).
- z3-solver 4.16 — INTEGRATED load-bearing in magma_smt_genuine; SUPPORTIVE in ~13 arrows.
- sympy 1.14 — INTEGRATED load-bearing (exact identities, ~10 arrows).
- cvc5 1.3.3 — SUPPORTIVE dual-SMT cross-check (~15 arrows).
- qutip 5.2.3 — SUPPORTIVE/control cross-check (~8 arrows).
- torch 2.11.0 — INTEGRATED in 1 arrow (cut_dependent_entropy complex128 leg).

### AVAILABLE (installed, importable, NOT load-bearing in any committed arrow yet)
- JAX ecosystem: diffrax 0.7.2, netket 3.21, quimb 1.14 (+cotengra 0.8, autoray, kahypar), ott-jax 0.6, e3nn-jax 0.21, jaxlie 1.5, optax 0.2.8, optimistix 0.1, jaxopt 0.8.5, lineax 0.1.1, equinox 0.13.8, flax 0.12.7, dm-haiku 0.0.16, blackjax 1.5, numpyro 0.21, flowMC 0.6, jax-verify 1.0, auto_LiRPA 0.7, jraph, mctx, chex, oryx, jaxga 0.0.2, galois 0.4.11 (finite-field load-bearing candidate).
  - Note: diffrax/netket/quimb ARE imported in system_v8 `jax_scale_lanes`/`jax_estate_test`, but those are not sealed arrows — so still AVAILABLE, not INTEGRATED.
- Julia: QuantumClifford 0.11.4, Yao 0.9.3, QuantumToolbox 0.44, CliffordAlgebras 0.1.4, Grassmann 0.8.44, Octonions 0.2.3, Quaternions 0.7.7, ITensors 0.9.30/ITensorMPS/ITensorNetworks/TensorKit/PEPSKit/TensorOperations, Manifolds 0.11.27/ManifoldsBase/GeometryBasics/CombinatorialSpaces, DifferentialEquations 8.0/DynamicalSystems 3.6.8/ChaosTools 3.5.4/Attractors 1.38.4, Symbolics 6.58/Z3.jl 1.0.4, Flux 0.16.10/Lux 1.31.4/Zygote 0.7.10/Enzyme 0.13.154, PythonCall 0.9.35/DLPack 0.3.1/CondaPkg (bridge, env-incompatible per Gemini, not in carrier).
- Proof/dynamics/topology/convex: maude 1.6 (rewrite); pysindy 2.1/pykoopman 1.2.1/PyDMD/derivative (dynamics ID — numpy-satellite home); TopoNetX 0.4/gudhi 3.12/rustworkx 0.17/xgi 0.10/networkx 3.6/igraph 1.0 (topology); cvxpy 1.9/cvxpylayers 1.2/diffcp/clarabel/osqp/scs/highspy (convex — pairs with `qics` repo).
- PyTorch ecosystem: torch-geometric 2.7, torchdiffeq 0.2.5, torchode 1.0.1, xitorch 0.3, torch_ga 0.0.6, e3nn 0.6, geomstats 2.8, lightning 2.6.5, torchrl 0.13.3, evotorch 0.6.1.
- Other quantum SDKs (unused in any arrow): qutip-jax 0.1.1, cirq 1.6.1, qiskit 2.4.1, pennylane 0.44.1+lightning, clifford 1.5.1, kingdon 2.1.1.
- Prob/ML/evolutionary: inferactively-pymdp 1.0.3 (active inference/FEP), dynamax 1.0.1, pymc 6.0, pytensor, arviz, scikit-learn 1.8, umap-learn, hdbscan, pymoo, deap, cma, ribs.

### Per-arrow wiring (● load_bearing · ○ control · — absent)
| Arrow | JAX | Julia | torch | qutip | numpy | proof | Seal |
|---|:--:|:--:|:--:|:--:|:--:|---|:--:|
| cut_dependent_entropy | ● | ● | ● | ○ | — | z3+cvc5+sympy | PASS 3-engine |
| pure_to_vn | ● | ● | — | ○ | — | z3+cvc5+sympy | PASS |
| renyi_alpha_axis | ● | ● | — | ○ | — | z3+cvc5+sympy | PASS |
| vn_to_shannon | ● | ● | — | ●* | — | z3+cvc5+sympy | PASS |
| bures_to_fubini_study | — | — | — | ○ | ● | z3+cvc5+sympy | RED numpy |
| real_vs_complex_tomography | — | — | — | — | ● | z3+cvc5+sympy | RED numpy |
| extension_fibre_capacity | — | — | — | ○ | ● | z3+cvc5+sympy | RED no engine value |
| vn_to_shannon_basis_relativity | — | — | — | — | ● | helper | RED numpy |
| carnot_engine (v8) | — | — | — | — | ● | — | RED numpy |
| szilard_engine (v8) | — | — | — | — | ● | — | RED numpy |
| quantum_otto_engine (v8) | — | — | — | ○ | ● | — | RED no engine value |
| finite_to_continuum_rung | — | — | — | — | — | sympy+z3+cvc5 | RED mislabeled-numeric |
| law_order_branch | — | — | — | — | — | sympy+z3+cvc5 | RED mislabeled-numeric |
| algebra_ladder / anticommutation_rung / magma_smt_genuine / magma_to_semigroup / root_foundation | — | — | — | — | — | z3(+cvc5+sympy) | PASS pure-SMT |
`●*` vn_to_shannon labels qutip load_bearing (minor inconsistency; passes on jax+julia).

### Clusters that co-occur most
1. Quantum-entropy stack (4 arrows): JAX+dynamiqs ⊗ Julia+QuantumOptics ⊗ (torch), qutip control, z3+cvc5+sympy proof — the ONLY genuine multi-engine integration; the pattern to replicate.
2. SMT stack (5 arrows): z3+cvc5+sympy, pure symbolic/finite, correctly no numeric engine.
3. numpy-red cluster (9 receipts): numpy+sympy(+qutip) — the migration targets.

### SERIALIZED SPINE STACK 2026-07-22 (install-and-test sweep — all functional, not just importable)
Python (sim-stack env), 14/14 one-real-operation smokes PASS: msgspec (encode/decode), fastparquet, pandas+pyarrow parquet roundtrip, pyarrow feather roundtrip, jax CPU x64, diffrax ODE solve, pysindy fit, z3 UNSAT, sympy lambdify->jax, kingdon Cl(3), geomstats hypersphere, pennylane Bell circuit, sklearn r2, scipy solve_ivp.
Julia (carrier project), 7/7 smokes PASS: Catlab SymmetricGraph, Arrow roundtrip, Z3 unsat (And takes Vector), Satisfiability.jl sat, DynamicalSystems henon, QuantumOptics entropy_vn, PackageCompiler loads. Added to carrier 07-22: Catlab, Arrow, Satisfiability, PackageCompiler.
Spine status: Phase 1 (containment) + Phase 2 (real Julia ratchet, Gate M1 sat/unsat pair bound into ledger) at passes-local-rerun; mock quarantine ON (mock stages park, never admit).

### LIBRARY->ARROW INTEGRATION MAP 2026-07-22 (NVIDIA deepseek draft, Claude-triaged)
Adopted, ranked: 1. diffrax->carnot+otto (time-dependent Lindblad cycles — clears 2 CI-reds + the open-system-dynamics capability gap); 2. galois->algebra_ladder (finite fields, S); 3. diffrax->bures_to_fubini (GKSL transport); 4. ott-jax->real_vs_complex_tomography (W2 Sinkhorn); 5. QuantumClifford->magma_smt (orbit enumeration cross-check); 6. Attractors/DynamicalSystems->law_order_branch+finite_to_continuum (basins/Lyapunov).
Rejected w/ reason: netket-NQS szilard (speculative research, not integration), quimb-PEPS for 2-qubit basis sim (overkill), jax-verify->root_foundation (domain mismatch — finite/symbolic arrow).
Full draft: scratchpad nvidia_library_map.md (session 2026-07-22). Stress lane live: sim_engines/stress/ (unofficial_stress_probe, promotion_allowed=false, parks by definition) — first probe: entropy_gradient_sweep (vmap/jit/grad, 247k pts/s, 3-way 1e-15 agreement).

### The 9 CI-red, by remedy
- numpy load-bearing -> migrate to JAX+Julia: bures_to_fubini_study, real_vs_complex_tomography, vn_to_shannon_basis_relativity, carnot_engine, szilard_engine.
- no engine value -> add JAX+Julia legs: extension_fibre_capacity, quantum_otto_engine.
- mislabeled numeric (actually pure symbolic) -> declare numeric_engine_required=false: finite_to_continuum_rung, law_order_branch.
