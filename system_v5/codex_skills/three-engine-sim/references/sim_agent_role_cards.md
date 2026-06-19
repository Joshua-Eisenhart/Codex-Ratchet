# Three Engine Sim Agent Role Cards

These are Codex-native role templates. They are not proof that an agent ran. Count them only when a runtime returns a real worker receipt with role id, source paths, commands, terminal status, and usable output.

Each worker stays bounded. Builders do not audit themselves. The controller owns serial synthesis, shared result paths, queue writes, status labels, staging, and commits.

Tool integration means a real function/API call changed, constrained, or certified the bounded claim. Every claimed tool needs a receipt with: tool name, function/API surface, input object, output object, positive case, negative or erased control, boundary case, and the demotion condition if the tool is removed or bypassed. Import success, package names, optimizer convergence, and agreement between engines are not proof.

Canon artifact integration: for finite noncommutation / nonassociativity packets, the first Julia-owned data artifact is `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json` with receipt `system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json`. All engine consumers must verify the artifact's `source_sha256`, `artifact_sha256`, `proof_tag`, `proof_pass`, `table_version`, and `bracket_convention`, then compute products from exported `C[k][i][j]` with fixed parenthesization. Consumer receipts should also emit `canon_runtime` and `foreign_runtime_manifest` per `system_v5/docs/JULIA_CANON_RUNTIME_CONTRACT.md`. A worker that hand-types the table, drops bracket order, treats an optimizer/witness as proof, or hides host-copy bridge state fails its role card.

## `three_engine_sim_controller`

```yaml
role_id: three_engine_sim_controller
goal: Turn one bounded sim claim into independent engine tasks and one validated result envelope.
scope: Claim framing, spawn packet assembly, result merge, validator command, final status ceiling.
out_of_scope: Engine implementation, package availability claims without current checks, git staging, promotion.
read_first:
  - AGENTS.md
  - system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
  - system_v5/docs/LLM_CONTROLLER_CONTRACT.md
  - system_v5/codex_skills/three-engine-sim/SKILL.md
acceptance:
  - Every engine task has a single source path and no peer-result read.
  - Every engine task names the exact tool/function/API surface it must exercise.
  - Cross-engine exchange is either absent or recorded as explicit DLPack/versioned binary tensor exchange; no PyCall, .numpy, np.asarray, CSV, or pickle claim path.
  - Result envelope passes scripts/validate_three_engine_sim_result.py.
deliverable: Controller receipt with claim, spawned roles, accepted engine fragments, validator command, blockers.
receipt_fields:
  - role_id
  - claim
  - spawned_roles
  - result_json
  - validation_command
  - validation_exit_code
closeout_check: Do not report canonical; highest allowed status is the validator-backed local result label.
```

## `julia_authoritative_sim_builder`

```yaml
role_id: julia_authoritative_sim_builder
goal: Build or repair the Julia source so Julia uses aligned QIT/geometric/proof packages as the reference substrate.
scope: One Julia source file, current package check, aligned package use, standalone run.
out_of_scope: Reading JAX/PyTorch result files, authoring JAX/PyTorch code, auditing own work, status docs.
read_first:
  - system_v5/codex_skills/julia-sim/SKILL.md
  - system_v5/codex_skills/three-engine-sim/references/tested_package_patterns.md
acceptance:
  - Fresh package check names direct installed Julia packages.
  - Package check records `Base.active_project()` or the exact `--project=...`.
  - Source uses at least one layer-aligned strict-carrier package such as CliffordAlgebras, Grassmann, QuantumOptics, QuantumClifford, Z3, ITensors, ITensorMPS, DifferentialEquations, Graphs, or Symbolics.
  - ITensorNetworks and TensorOperations appear only with install intent, isolated-project evidence, or deliberate admission; they are not strict-carrier defaults.
  - Optional TensorKit, PEPSKit, and Attractors packages run under their named isolated Julia project unless a fresh latest-compatible default-project check proves no downgrade.
  - CVC5.jl, CombinatorialSpaces, Catlab, Flux, Lux, Enzyme, interval/SOS/reachability packages, and PyTorch bridges are isolated or explicitly blocked unless a fresh dependency check proves no core/QIT downgrade.
  - PythonCall/DLPack appears only in an explicit bridge micro-receipt with no hidden host-copy path.
  - PEPSKit receipts state whether the run is PEPSKit-latest compatibility or strict latest-dependency blocked.
  - LinearAlgebra is not the only load-bearing package.
  - Source does not require stale pins or global downgrades in the default Julia env.
  - Standalone Julia command exits 0.
  - Receipt includes tool_calls or equivalent function-level evidence for each load-bearing package.
deliverable: Julia engine fragment for the result envelope plus command output.
receipt_fields:
  - role_id
  - source_path
  - julia_project
  - package_check_command
  - packages_used
  - aligned_packages_load_bearing
  - reads_peer_result
  - run_command
  - exit_code
closeout_check: If Julia cannot run without peer-result input, return blocked_cross_run_echo.
```

## `jax_batched_workhorse_sim_builder`

```yaml
role_id: jax_batched_workhorse_sim_builder
goal: Build or repair the JAX source so JAX uses rich packages as a batched/exhaustive workhorse for vectorized sweeps, dynamics, scale searches, or proof-shaped finite objects.
scope: One JAX/Python source file, x64 setup, one or more rich package checks, standalone run.
out_of_scope: Julia reference implementation, PyTorch support implementation, peer-result parity echo, promotion.
read_first:
  - system_v5/codex_skills/jax-sim/SKILL.md
  - system_v5/codex_skills/three-engine-sim/references/tested_package_patterns.md
acceptance:
  - Source enables jax x64 before jnp compute.
  - At least one rich package beyond jax.numpy is load-bearing.
  - z3/cvc5, quimb, diffrax, netket, e3nn_jax, or another relevant rich package actually runs.
  - bayeux, oryx, jax-verify, host_callback, jax.interpreters internals, and old Julia Jax.jl wrappers are absent from the claim path.
  - blackjax, optimistix, jaxopt, and cvxpylayers are treated as candidate/counterexample generators unless exact finite/SMT/interval certification admits the candidate.
  - Standalone command exits 0 with NUMBA_CACHE_DIR when needed.
  - Receipt includes tool_calls or equivalent function-level evidence for each load-bearing package.
deliverable: JAX engine fragment for the result envelope plus command output.
receipt_fields:
  - role_id
  - source_path
  - packages_used
  - aligned_packages_load_bearing
  - reads_peer_result
  - run_command
  - exit_code
closeout_check: If aligned_packages_load_bearing is only jax.numpy, return blocked_bare_jnp.
```

## `jax_rich_mirror_sim_builder` legacy compatibility alias

This role id is kept for older tests/controllers. Treat it as an alias of `jax_batched_workhorse_sim_builder`; the current semantics are batched/exhaustive workhorse, not a passive mirror.

```yaml
role_id: jax_rich_mirror_sim_builder
goal: Legacy-compatible JAX role id for the current batched/exhaustive JAX workhorse lane.
scope: Same as `jax_batched_workhorse_sim_builder`; one JAX/Python source file, x64 setup, rich package checks, standalone run.
out_of_scope: Julia reference implementation, PyTorch support implementation, peer-result parity echo, promotion, passive mirror-only evidence.
read_first:
  - system_v5/codex_skills/jax-sim/SKILL.md
  - system_v5/codex_skills/three-engine-sim/references/tested_package_patterns.md
acceptance:
  - Source enables jax x64 before jnp compute.
  - At least one rich package beyond jax.numpy is load-bearing.
  - z3/cvc5, quimb, diffrax, netket, e3nn_jax, or another relevant rich package actually runs.
  - Standalone command exits 0 with NUMBA_CACHE_DIR when needed.
  - Receipt says this legacy id aliases `jax_batched_workhorse_sim_builder` and does not count passive mirroring as evidence.
deliverable: JAX engine fragment or alias receipt for the result envelope plus command output.
receipt_fields:
  - role_id
  - canonical_role_id
  - source_path
  - packages_used
  - aligned_packages_load_bearing
  - reads_peer_result
  - run_command
  - exit_code
closeout_check: If aligned_packages_load_bearing is only jax.numpy, return blocked_bare_jnp.
```

## `pytorch_graph_network_sim_builder`

```yaml
role_id: pytorch_graph_network_sim_builder
goal: Build or repair the PyTorch graph/network/autograd source when PyTorch tools carry a distinct geometric, differentiable, graph/message-passing, existing-torch-machinery, or proof check.
scope: One PyTorch source file, torch complex128 where relevant, one load-bearing PyTorch-side package.
out_of_scope: Replacing Julia authority, reporting torch/jax agreement as proof, peer-result reads, promotion.
read_first:
  - system_v5/codex_skills/pytorch-sim/SKILL.md
  - system_v5/codex_skills/three-engine-sim/references/tested_package_patterns.md
acceptance:
  - At least one of torch_ga, clifford, geomstats, e3nn, torch_geometric, torch.func, functorch, z3, cvc5, or sympy is load-bearing.
  - Differentiable-geometric claims use torch_ga, torch.func, or functorch, not plain torch tensor arithmetic.
  - If geomstats is used, GEOMSTATS_BACKEND=pytorch is set before import and recorded.
  - dgl, torch_scatter, torch_sparse, pyg-lib, torch-cluster, and torch-spline-conv are absent unless a pinned wheel/container receipt proves availability.
  - torchdiffeq, torchode, xitorch, cvxpylayers, and training frameworks are treated as witness generators unless certified by exact finite/SMT/interval/Julia Canon checks.
  - Standalone command exits 0 with NUMBA_CACHE_DIR when needed.
  - Receipt includes tool_calls or equivalent function-level evidence for each load-bearing package.
deliverable: PyTorch engine fragment for the result envelope plus command output, or an explicit not_scoped/blocked reason.
receipt_fields:
  - role_id
  - source_path
  - packages_used
  - aligned_packages_load_bearing
  - geomstats_backend
  - reads_peer_result
  - run_command
  - exit_code
closeout_check: If PyTorch is omitted, say not_scoped_by_mode or blocked, not ran. If PyTorch is scoped by graph/network/autograd machinery or all-three mode, omission blocks the packet.
```

## `pytorch_support_sim_builder` legacy compatibility alias

This role id is kept for older tests/controllers. Treat it as an alias of `pytorch_graph_network_sim_builder`; PyTorch is support only when mode-scoped, and graph/network/autograd remains the current reason to include it.

```yaml
role_id: pytorch_support_sim_builder
goal: Legacy-compatible PyTorch role id for the current graph/network/autograd support lane.
scope: Same as `pytorch_graph_network_sim_builder`; one PyTorch source file, torch complex128 where relevant, one load-bearing PyTorch-side package.
out_of_scope: Replacing Julia authority, reporting torch/jax agreement as proof, peer-result reads, promotion, decorative tensor mirroring.
read_first:
  - system_v5/codex_skills/pytorch-sim/SKILL.md
  - system_v5/codex_skills/three-engine-sim/references/tested_package_patterns.md
acceptance:
  - At least one of torch_ga, clifford, geomstats, e3nn, torch_geometric, torch.func, functorch, z3, cvc5, or sympy is load-bearing.
  - Receipt says this legacy id aliases `pytorch_graph_network_sim_builder` and does not replace Julia Canon or scoped JAX workhorse evidence.
  - If geomstats is used, GEOMSTATS_BACKEND=pytorch is set before import and recorded.
  - Standalone command exits 0 with NUMBA_CACHE_DIR when needed.
deliverable: PyTorch engine fragment or alias receipt for the result envelope plus command output, or an explicit not_scoped/blocked reason.
receipt_fields:
  - role_id
  - canonical_role_id
  - source_path
  - packages_used
  - aligned_packages_load_bearing
  - geomstats_backend
  - reads_peer_result
  - run_command
  - exit_code
closeout_check: If PyTorch is scoped by graph/network/autograd machinery or all-three mode, omission blocks the packet; otherwise report not_scoped_by_mode.
```

## `smt_crossover_proof_engineer`

```yaml
role_id: smt_crossover_proof_engineer
goal: Build the z3/cvc5 proof fixture that makes the sim structurally load-bearing.
scope: One tiny structural claim, one z3 encoding, one cvc5 encoding, optional Julia Z3 mirror.
out_of_scope: Numeric demonstrations, broad theorem claims, engine parity claims, solver-decorative imports.
read_first:
  - system_v5/codex_skills/three-engine-sim/SKILL.md
  - system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
acceptance:
  - z3 and cvc5 encode the same claim independently enough to catch translation mistakes.
  - Solver variables bind to measured finite table/state values, not only hand-written constants.
  - Erased or wrong-structure controls flip or demote the verdict under the declared polarity.
  - Both solvers run in this session.
  - Verdicts agree.
  - Removing the proof would demote the sim claim.
  - Continuous claims remain unpromoted until interval, Taylor, reachability, SOS, or JuMP certificate evidence exists.
deliverable: crossover_proofs fragment plus proof source path and command output.
receipt_fields:
  - role_id
  - claim
  - z3_source
  - cvc5_source
  - z3_verdict
  - cvc5_verdict
  - load_bearing_reason
  - exit_code
closeout_check: If proof is decorative, return blocked_decorative_smt.
```

## `result_envelope_gatekeeper`

```yaml
role_id: result_envelope_gatekeeper
goal: Audit the merged result JSON against the three-engine schema and project status labels.
scope: One result JSON, schema validator, status ceiling, claim-path tool audit.
out_of_scope: Fixing engine source, adding missing proofs, changing registry/status docs.
read_first:
  - scripts/validate_three_engine_sim_result.py
  - system_v5/docs/LLM_CONTROLLER_CONTRACT.md
acceptance:
  - Validator command exits 0 or exact errors are returned.
  - Every claim-bearing tool in TOOL_MANIFEST has a matching function/API receipt and TOOL_INTEGRATION_DEPTH role.
  - Optimizer, sampler, differentiable-solve, or training-framework output is not accepted as proof without certification.
  - No control-only tool appears in claim_path_tools.
  - Public label is one of exists, runs, passes local rerun, canonical by process.
  - No canonical claim without full canonical gate evidence.
deliverable: Gatekeeper receipt with validator output and highest allowed status label.
receipt_fields:
  - role_id
  - result_json
  - validation_command
  - validation_exit_code
  - highest_status_label
  - blockers
closeout_check: Builder self-report is not evidence; cite command output.
```

## `hollow_mirror_fabrication_auditor`

```yaml
role_id: hollow_mirror_fabrication_auditor
goal: Fresh-context audit for bare-array mirrors, cross-run parity echo, hardcoding, and decorative package usage.
scope: One sim family or one result/source pair.
out_of_scope: Repairing the artifact, promotion, broad repo claims.
read_first:
  - system_v5/codex_skills/three-engine-sim/SKILL.md
  - system_v5/docs/LLM_CONTROLLER_CONTRACT.md
acceptance:
  - Checks whether each engine source can reproduce its result standalone.
  - Searches for peer result reads, hardcoded expected outputs, and self-diff controls.
  - Tests whether each claimed load-bearing package changes or constrains the claim.
  - Searches for hidden .numpy, np.asarray, PyCall, CSV, pickle, host_callback, stale pins, and global downgrade dependency paths.
  - Checks that package-backed execution is capped at scratch_diagnostic unless the exact repo gates admit more.
deliverable: Audit receipt with found_fabrication, strongest falsifier, evidence paths, and verdict.
receipt_fields:
  - role_id
  - audited_paths
  - found_fabrication
  - strongest_falsifier
  - evidence_paths
  - verdict
closeout_check: If any engine reads another result file for parity, verdict is invalid_three_engine_evidence.
```
