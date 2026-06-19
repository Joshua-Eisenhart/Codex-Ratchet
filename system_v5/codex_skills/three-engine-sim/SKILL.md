---
name: three-engine-sim
description: Use when authoring, auditing, or rebuilding Codex Ratchet cross-runtime sims so Julia Canon, JAX batched/exhaustive work, PyTorch graph/network/autograd machinery, and proof tools stay mode-declared and receipt-bound.
---

MIRROR: authoritative copy is .claude/skills/three-engine-sim/SKILL.md; sync direction .claude -> codex_skills.

# Three Engine Sim

Use this before any new foundation, carrier, geometry, QIT, tensor, proof, or rebuild sim. The point is not three copies of one algorithm. The point is mode-declared cross-runtime evidence with different failure modes: Julia is Canon for algebra/order/finite carrier/proof semantics, JAX is the batched/exhaustive workhorse, and PyTorch is first-class for graph/network/autograd/existing torch machinery while never arbitrating over Julia Canon.

Audit mode-first: read `engine_contract.mode` when present. Use `all_three_full_sims` only when the envelope explicitly declares all three lanes or when legacy/current `schema_version=three_engine_sim_result_v1` plus `engines=jax,julia,pytorch` makes that the honest schema. Otherwise classify by declared claim path: `julia_canon_jax_workhorse`, `julia_canon_jax_with_pytorch_graph`, `pytorch_graph_network_packet`, or `audit_only`. A packet-level verdict must inspect every scoped lane and the controller envelope; do not infer PyTorch absence or PyTorch requirement from stale prose alone.

Environment coordination is mandatory before installs or package-dependent sim work. Read `system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md` and `system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md`, then run `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py` from the repo. If the doctor reports repo-local env pollution, wrong-env packages, missing expected scoped packages, or active installers, hold installs/sims and route through `codex-ratchet-env-agent-coordination`.

Latest-compatible package rule: do not pin stale dependencies or globally downgrade an engine environment to make an optional package coexist. Julia's default project is intended to stay on the latest-compatible core/QIT stack, but fresh package checks control because the default environment can drift. Optional Julia packages run only in isolated verified projects unless a fresh check proves they work in the default project without downgrades. `TensorKit` latest has its own project; `PEPSKit` is a PEPSKit-compatibility project because it currently constrains TensorKit below latest.

Canon rule: Julia owns the multiplication tables / structure constants, bracket/parenthesization order, finite carrier definitions, proof obligations, proof tags, and arbitration. JAX and PyTorch may accelerate or generate witnesses only after that order is fixed and exported. No JAX/PyTorch optimizer, sampler, learned module, or differentiable solve is proof by itself.

Current canon artifact seed: `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json` with result receipt `system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json`. Treat it as `scratch_diagnostic`, not admission. Consumer packets must verify `source_sha256`, `artifact_sha256`, `proof_tag`, `proof_pass`, `table_version`, and `bracket_convention` before using it; JAX/PyTorch consumers must compute from the exported `C[k][i][j]` and explicit bracket order, not hand-type or reinterpret the algebra.

Runtime contract: for Julia Canon sidecar work, read `system_v5/docs/JULIA_CANON_RUNTIME_CONTRACT.md`. Results that consume the canon artifact should emit `canon_runtime` and `foreign_runtime_manifest` fields, even when the current validator does not require them yet. Missing fields keep the result useful as a scratch diagnostic but block "full Canon runtime receipt" language.

Bridge rule: claim-bearing cross-engine exchange must use an explicit receipt for `DLPack` or an explicitly versioned binary tensor exchange. `PythonCall` may orchestrate a Julia/Python boundary; `PyCall`, `.numpy()`, `np.asarray`, CSV, pickle, and hidden host-copy bridges are not allowed on the claim path.

## Tool-Integration Receipt Rule

`load_bearing` = the tool output gates a control, quotient, proof, `all_pass`
condition, divergence value, or demotion condition. A real import/call that
only emits a side readout is `supportive`, NOT `load_bearing`.

Every claimed `load_bearing` tool emits a function-level `tool_calls` entry:
`{tool, qualified_api/function, input_object, output_object, positive_case,
negative/erased_control, boundary_case, demotion_condition, gates: which of
all_pass/divergence/quotient/proof}`. A `load_bearing` claim with no gate is
downgraded to `supportive`.

Cross-engine note: over-claimed `load_bearing` tools must either be wired to a
real gate or demoted to `supportive`: Julia
`CliffordAlgebras`/`Attractors`/`Manifolds`/`ITensors`/`Yao`; JAX
`dynamiqs`/`quimb`+`cotengra`/`e3nn_jax`; PyTorch `torch_geometric`.

## Step 1: Pick Agent Roles

For substantive sim work, use specialized workers instead of one blended builder. Read `references/sim_agent_role_cards.md` and select only the roles that can change the result.

Default role set:

- `three_engine_sim_controller`
- `julia_authoritative_sim_builder`
- `jax_rich_mirror_sim_builder`
- `smt_crossover_proof_engineer`
- `result_envelope_gatekeeper`
- `hollow_mirror_fabrication_auditor`

Add `pytorch_graph_network_sim_builder` when the claim path scopes graph/network/autograd/existing torch machinery, when the user asks for all three engines, or when an explicit all-three envelope requires PyTorch. Do not add PyTorch as decorative compatibility filler; do not omit it when PyG/torch/autograd machinery is the actual object.

Validation: every visible worker claim has a receipt with `role_id`, commands, source/result paths, terminal status, and usable output.

On failure: call the route partial/blocked; do not count role cards as executed agents.

## Step 2: Classify The Claim

Write the bounded claim before writing code:

```yaml
sim_id:
claim:
julia_reference_package:
jax_workhorse_package:
pytorch_graph_network_package:
crossover_proof:
allowed_claims:
promotion_allowed: false
canon_runtime:
foreign_runtime_manifest:
```

Validation: the claim names the engine mode, the Julia Canon or blocked reason, the scoped JAX workhorse/proof package when JAX is in mode, the scoped PyTorch graph/network/autograd package when PyTorch is in mode, and one structural proof surface when proof is claim-bearing.

On failure: stop. A bare numeric claim is not a three-engine sim.

## Step 3: Use Engine Skills

Use the engine skills as implementation guards:

- `julia-sim`: Canon substrate for algebra/order/finite carrier/proof semantics. `LinearAlgebra` can support local numerics but cannot be the only load-bearing tool.
- `jax-sim`: batched/exhaustive workhorse for vectorized sweeps, dynamics, scale searches, and high-volume witness generation after Julia fixes the finite object. `jax.numpy` can support arrays but cannot be the only load-bearing tool for rich evidence.
- `pytorch-sim`: first-class graph/network/autograd/existing torch machinery lane. Use when its tools add a claim-bearing check, especially `torch_geometric`, differentiable geometric algebra with `torch_ga`, torch-side manifold/equivariant checks, `torch.func`/`functorch`, dynamics/proof tools, or all-three declared mode.

Validation: every scoped engine result has `ran`, `source_path`, `source_sha256`, `packages_used`, `aligned_packages_load_bearing`, `tool_calls` or equivalent function-level receipts, and `reads_peer_result: false`. Each load-bearing tool receipt names the function/API surface, input object, output object, positive case, negative or erased control, boundary case, and demotion condition. If Julia uses an optional project, the result also records the exact `julia_project` or command `--project=...`. If PyTorch is scoped by graph/network/autograd machinery or all-three mode, it must run with a real load-bearing tool or the envelope is blocked/excluded.

On failure: mark the engine `blocked` or `excluded`, not `ran`.

## Step 4: Make Proof Load Bearing

Every result must include a crossover proof:

```json
"crossover_proofs": {
  "z3": {"ran": true, "verdict": "unsat", "load_bearing": true},
  "cvc5": {"ran": true, "verdict": "unsat", "load_bearing": true},
  "julia_z3": {"ran": true, "verdict": "sat", "load_bearing": true}
}
```

`z3` and `cvc5` must agree on the same tiny structural claim. `julia_z3` is used when the Julia package is installed and the Julia side owns an SMT check for the same family.

Validation: removing the proof would remove or demote the claim, and solver variables bind to measured finite table/state values with erased or wrong-structure controls under a named polarity.

On failure: classify the sim as numeric diagnostic only.

Proof promotion route:

```text
simulation witness
-> exact finite algebra/table check
-> z3/cvc5 SMT pressure
-> interval, Taylor, reachability, SOS, or JuMP certificate when continuous dynamics are involved
-> Julia Canon manifest acceptance
```

## Step 5: Emit The Result Envelope

Every result JSON that claims this protocol uses:

```json
{
  "schema_version": "three_engine_sim_result_v1",
  "engine_contract": {
      "mode": "julia_canon_jax_workhorse | julia_canon_jax_with_pytorch_graph | pytorch_graph_network_packet | all_three_full_sims | audit_only",
    "lanes": ["julia", "jax", "pytorch"],
    "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"]
  },
  "classification": "scratch_diagnostic",
  "promotion_allowed": false,
  "canon_runtime": {
    "semantic_owner": "julia",
    "artifact_path": "system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json",
    "artifact_sha256": "...",
    "source_sha256": "...",
    "receipt_path": "system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json",
    "proof_tag": "...",
    "proof_pass": true,
    "table_version": "...",
    "bracket_convention": "...",
    "consumer_policy": "compute_from_exported_C_tensor_with_fixed_parenthesization"
  },
  "foreign_runtime_manifest": {
    "julia": {"project": "...", "packages": [], "role": "semantic_owner"},
    "jax": {"packages": [], "role": "consumer_or_batched_exhaustive_worker"},
    "pytorch": {"packages": [], "role": "consumer_or_graph_network_autograd_worker"},
    "tensor_exchange": "dlpack_or_versioned_binary_receipt_only",
    "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"]
  },
  "claim_path_tools": [],
  "engines": {
    "julia": {
      "ran": true,
      "source_path": "...",
      "packages_used": ["CliffordAlgebras", "Z3"],
      "aligned_packages_load_bearing": ["CliffordAlgebras"],
      "reads_peer_result": false
    },
    "jax": {
      "ran": true,
      "source_path": "...",
      "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "quimb.tensor", "diffrax"],
      "aligned_packages_load_bearing": ["z3", "cvc5", "diffrax"],
      "reads_peer_result": false
    },
    "pytorch": {
      "ran": true,
      "source_path": "...",
      "packages_used": ["torch", "torch_ga", "geomstats", "e3nn", "torch_geometric"],
      "aligned_packages_load_bearing": ["torch_ga"],
      "reads_peer_result": false
    }
  },
  "crossover_proofs": {},
  "divergence": {
    "julia_authoritative": true,
    "engine_values": {"julia": 0.0, "jax": 0.0, "pytorch": 0.0},
    "max_divergence": 0.0
  }
}
```

Validation: `numpy`, `scipy`, and `mpmath` are absent from `claim_path_tools`.

On failure: mark the output invalid for this protocol.

For the Julia Canon lane, the next admissible ratchet order is runtime hygiene, existing artifact audit, DLPack or versioned binary exchange micro-probe, JAX consumer equivalence, PyTorch consumer equivalence, Attractors/dynamics fit, then proof promotion. Do not rebuild the existing algebra artifact by default, and do not let JAX/PyTorch agreement strengthen it unless consumers read and verify the artifact.

## Step 6: Validate

Run the validator matching the declared mode:

```bash
python3 scripts/validate_three_engine_sim_result.py <result.json>
python3 scripts/validate_three_engine_sim_result.py --require-pytorch <result.json>  # explicit all-three envelopes only
```

For an explicitly scoped non-envelope diagnostic that records PyTorch as excluded/blocked, do not use all-three language. If auditing legacy material that does not claim a PyTorch leg, run the weaker validator only as a legacy shape check:

```bash
python3 scripts/validate_three_engine_sim_result.py <result.json>
```

Validation: the validator exits 0.

On failure: do not report the sim as `canonical by process`, and do not use it as a rebuild receipt.

Also validate the role-card library after edits:

```bash
python3 scripts/validate_sim_agent_role_cards.py system_v5/codex_skills/three-engine-sim/references/sim_agent_role_cards.md
```

## Hard Blocks

- Julia that only uses `LinearAlgebra` is not a proper Julia sim for this protocol.
- JAX that only uses `jax.numpy` is not a proper JAX sim for this protocol.
- PyTorch that routes through numpy-backed `geomstats` is not a proper torch-side geomstats check.
- Any engine reading another engine's prior result file is cross-run echo, not parity.
- Agreement between JAX and PyTorch alone is not confirmation; it may be shared numpy-corruption.
- Existing R0-R3 bare-array mirror outputs are at most prior diagnostics until rebuilt under this protocol.
- Optional-package success in one Julia project is not availability in another Julia project.
- No result may use a stale pin or global downgrade as a hidden dependency. Isolate the tool or block it.
- If strict latest-dependency use is required, do not use `PEPSKit` while it requires an older TensorKit line; use latest `TensorKit` separately or mark the PEPSKit route blocked.

For tested local package patterns, read `references/tested_package_patterns.md` only when implementing or debugging the first sim in a session.

## DEPRECATED / DO-NOT-USE

Deprecation authority: capability_matrix receipts + owner 2026-06-09; a deprecated tool needs a passing capability probe + owner sign-off to return.

| Status | Tools / surfaces | Rule |
| --- | --- | --- |
| REPLACE | `torch_ga` (0.0.6 hobby-tier; `kingdon` under test as successor), `clifford` (design-frozen), `qutip-jax` (0.1.1 fragile), `jraph` (dev version) | Use `kingdon` only after probe/sign-off; `clifford` is legacy fallback only; use `dynamiqs` for the qutip-jax role; use PyG as the GNN engine. |
| OUT OF SYSTEM | `qiskit`, `pennylane`, `cirq`, PEPS3D/CTMRG, Julia `PythonCall` (`CondaPkg` pollution), `ITensorNetworks`, `TensorOperations`, `Yao`, `QuantumToolbox` (installed-unused) | Do not use in three-engine claim paths or promise matrices. |
| PRUNE FROM PROMISES | `cma`, `deap`, `evotorch`, `optuna`, `pymoo`, `ribs`, `datasketch`, `hdbscan`, `hypothesis`, `pynndescent`, `sklearn`, `umap`, `igraph`, `blackjax`, `jaxopt`, `lineax`, `optimistix`, `optax`, `flax`, `orbax`, `chex`, `jaxtyping`, `haiku`, `numpyro`, `flowMC`, `jax_dataclasses`, `jaxlie`, `ott-jax` | No matrix cell. `optax`/`jaxopt` are candidate-search only, never proof. |
| UNCHANGED RULE | `numpy`, `scipy`, `mpmath` | Control-lane only; never claim-path or load-bearing. |
