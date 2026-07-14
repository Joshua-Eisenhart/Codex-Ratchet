---
name: jax-sim
description: Use when writing or auditing the JAX side of a Codex Ratchet sim so JAX acts as the batched/exhaustive workhorse with rich packages and proof tools instead of bare jax.numpy.
---

# JAX Sim

This is the repo-held Codex skill source governed by `AGENTS.md`.
Claude-family skills and agents are reference-only, not authority or a sync
source. Current tool membership comes from the runtime target map and
`system_v5/ops/tooling/deep_stack_stress_20260714/registry/tool_roster_v1.json`;
do not duplicate membership or deprecation tables here.

JAX is the batched/exhaustive workhorse after Julia fixes the finite object and bracket/order semantics. Use it for `vmap`/`jit` sweeps, differentiable dynamics, scale searches, vectorized witness generation, and proof-shaped finite objects. `jax.numpy` is allowed as array support, but a JAX sim is invalid for rich-tool evidence if `jnp` is the only load-bearing surface.

## Step 1: Use The Repo Python

Before package-dependent work or any install proposal, read
`system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md` and run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py --skip-julia
```

If the doctor says the canonical Python env is missing a scoped package, report
`blocked_missing_package` and create an install intent; do not use bare
`python3` as evidence.

Use the Codex Ratchet environment:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 <script.py>
```

For `quimb` and other numba-backed packages in this environment, use:

```bash
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 <script.py>
```

Validation: command exits 0 in the current session.

On failure: fix the environment/cache path or mark blocked; do not claim package usage from import text alone.

## Step 1a: API And Package Risk Guard

Do not use `bayeux`, `oryx`, or `jax-verify` for current Codex Ratchet JAX
lanes; local imports fail against removed JAX internals in the current JAX API.
Use `blackjax`, `numpyro`, `jaxopt`, `lineax`, and `optimistix` for
sampler/optimization/support roles when they match the bounded claim.

API footguns from the independent Hermes shakedown:

- `dynamiqs` returns its own `QArray`, not a raw JAX ndarray. Call `.to_jax()`
  before any `jnp`-native operation, for example `jnp.trace(rho.to_jax())`.
- Enable x64 before importing `jax.numpy`; false x64 keeps numeric comparison
  lanes diagnostic only.
- Z3/cvc5 claims must derive the target expression inside each solver from
  finite values; do not pass only a precomputed scalar.
- `numpy` is control-only and never in the claim path.

Avoid deprecated or internal JAX surfaces in sim code:

- Do not use `jax.experimental.host_callback`; use current callback/debug APIs only when the side effect is outside the claim path.
- Do not depend on internal modules such as `jax.interpreters.mlir`,
  `jax.interpreters.xla`, or removed `jax.lax` internals.
- Do not make old Julia `Jax.jl` wrappers part of the JAX lane; use direct Python JAX, and bridge from Julia only through explicit `PythonCall` plus `DLPack` receipts.
- Treat `pmap` as a compatibility route, not the default architecture for new SPMD work.

Optimization tools such as `jaxopt`, `blackjax`, `optimistix`, and `cvxpylayers` are candidate or witness generators. They do not promote a proof unless the candidate is certified by exact finite checks, SMT, interval/reachability, or another admitted proof surface.

## Step 2: Enable X64

Before importing `jax.numpy` for numeric work:

```python
from jax import config
config.update("jax_enable_x64", True)
```

Validation: result records x64 for numeric readouts that compare to Julia.

On failure: classify as diagnostic only.

## Step 2a: Tool-Integration Receipt Rule

`load_bearing` = the tool output gates a control, quotient, proof, `all_pass`
condition, divergence value, or demotion condition. A real import/call that
only emits a side readout is `supportive`, NOT `load_bearing`.

Every claimed `load_bearing` tool emits a function-level `tool_calls` entry:
`{tool, qualified_api/function, input_object, output_object, positive_case,
negative/erased_control, boundary_case, demotion_condition, gates: which of
all_pass/divergence/quotient/proof}`. A `load_bearing` claim with no gate is
downgraded to `supportive`.

## Step 3: Make A Rich Package Load Bearing

Canon-table consumer rule: if the JAX lane consumes a Julia algebra artifact, load `C[k][i][j]`, `table_version`, `bracket_convention`, and `proof_tag` from the artifact. Implement products as explicit fixed-order contractions over `C`; never re-associate `(a*b)*c` to `a*(b*c)` unless the proof tag covers that exact case. Do not use `.numpy()`, `np.asarray`, CSV, pickle, or host-object serialization on the claim/data path. DLPack or an explicitly versioned binary tensor bridge requires its own bridge receipt before it becomes claim-bearing.

Use at least one of these in the claim path:

- `z3` and `cvc5` for structural SAT/UNSAT proof.
- `quimb.tensor`, `cotengra`, or `autoray` for tensor-network contraction/scale.
- `diffrax` for dynamics.
- `netket`, `jaxopt`, `lineax`, `jraph`, `ott`, or `e3nn_jax` when matched to the claim.
- `blackjax` or `optimistix` for bounded sampler/solver support, with proof promotion blocked until certification.

Validation: `aligned_packages_load_bearing` names at least one rich package and does not list only `jax.numpy`.

On failure: the JAX side is a bare mirror and cannot support a rich-tool or batched-workhorse claim.

## Step 4: Emit Engine Receipt

Result fragment:

```json
"jax": {
  "ran": true,
  "source_path": "...",
  "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "quimb.tensor", "diffrax"],
  "aligned_packages_load_bearing": ["z3", "cvc5", "diffrax"],
  "reads_peer_result": false
}
```

Validation: no peer result file is read to fabricate parity.

On failure: mark `reads_peer_result: true` and reject from evidence.
