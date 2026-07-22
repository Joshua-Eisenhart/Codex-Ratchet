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
