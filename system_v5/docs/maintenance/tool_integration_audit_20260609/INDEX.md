# Tool-Integration Audit — Full-Stack Spinor-Network Three-Engine Test (2026-06-09)

**Status label:** `useful scratch diagnostic — partly-decorative — tune skills/agents, then rerun one bounded integration test`
**Ceiling:** `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. No canon/admission/bridge/manifold/M(C)-final/physics claim is made or implied by this audit.

## Why this folder exists
The full-stack spinor-network three-engine integration test was the **vehicle** for the current goal:
test tool integration + fine-tune the skills/agents/tool-stack BEFORE running the foundation ladder.
Six fresh read-only codex2 audits (high effort) of that test were produced in volatile `/tmp/found`.
They are preserved here so the actionable content survives a `/tmp` wipe. Prune this whole folder in one move once the patch lands and a clean post-patch receipt exists.

## Raw audit artifacts (preserved this folder)
- `integration_audit.md` — overall genuine-vs-decorative verdict on the test.
- `ms_julia_report.md` / `ms_jax_report.md` / `ms_pytorch_report.md` — per-engine per-tool verdicts.
- `ms_skills_report.md` — skill/agent surface audit (what's stale/missing).
- `ms_coverage_report.md` — installed-tool coverage (used vs unused).
- `mc_gap_table_DEFERRED_LADDER_INPUT.md` — M(C) gap table. **DEFERRED**: ladder input, not current-task. Do not act on it until the ladder formally resumes.

## Converged verdict
The test **runs and TMR-agrees** (max_divergence ≈ 2.3e-10) and the CORE is real and value-coupled:
octonion/quaternion associator algebra, QIT coherent-information, ODE trace/population, finite-basin
controls, and z3+cvc5 derive-in-solver flips. **But the receipts over-claim `load_bearing`** for tools
whose outputs do NOT gate `all_pass`, `max_divergence`, a named control, the quotient, or a proof:

| Engine | Genuinely load-bearing | Over-claimed (real call, side-receipt only) |
|---|---|---|
| Julia | QuantumOptics, Octonions, Quaternions, DifferentialEquations, Z3 | CliffordAlgebras, Attractors+DynamicalSystems, Manifolds, ITensors, Yao |
| JAX | jax/vmap, diffrax, z3, cvc5 | dynamiqs, quimb+cotengra, e3nn_jax |
| PyTorch | torch, torchdiffeq, torch.func, xitorch, z3, cvc5 | torch_geometric MessagePassing (overstated — partial, not the full network-engine role) |

Coverage (codex2 count): 34 used-with-receipt · 6 installed-but-unused · 6 schema-thin (no `tool_calls` key) · 1 under-exercised.

## THE PATCH SPEC (narrow — apply to skills + agents, do NOT relaunch a mass wave)

**Definition to install:**
> `load_bearing` = the tool output gates a control, quotient, proof, `all_pass` condition, divergence
> value, or demotion condition. A real import/call that only emits a side readout is `supportive`,
> NOT `load_bearing`.

**Receipt rule to require:**
> Every claimed `load_bearing` tool emits a function-level `tool_calls` entry:
> `{tool, qualified_api/function, input_object, output_object, positive_case, negative/erased_control,
> boundary_case, demotion_condition, gates: which of all_pass/divergence/quotient/proof}`.
> A `load_bearing` claim with no gate is downgraded to `supportive`.

**API footguns to add to the relevant per-engine skill:**
- Julia: qualify APIs (e.g. `CliffordAlgebras.<fn>`, `Quaternions.Quaternion`, `QuantumOptics.entropy_vn`, `Z3.add/check`); import at top level; strict-carrier truth (only the ~20 aligned pkgs; NOT ITensorNetworks/TensorOperations/PythonCall/DLPack/Zygote).
- JAX: `dynamiqs` returns a `QArray` → call `.to_jax()` before `jnp` ops; enable x64; derive-in-solver z3/cvc5; numpy control-only.
- PyTorch: `GEOMSTATS_BACKEND=pytorch`; PyG `MessagePassing` must actually carry the noncommutative octonion edge update to earn the network-engine `load_bearing` label.

## Surfaces to patch (they are INDEPENDENT COPIES and already DRIFTED)
`.claude/skills/` is NOT a symlink of `system_v5/codex_skills/`. As of 2026-06-09 they differ; `.claude` jax-sim/pytorch-sim were stale (17:34 / 15:43) vs the 23:42 codex_skills tuning. Patch BOTH plus the agents:
- `system_v5/codex_skills/{julia-sim,jax-sim,pytorch-sim,three-engine-sim}/SKILL.md`
- `.claude/skills/{julia-sim,jax-sim,pytorch-sim,three-engine-sim}/SKILL.md`
- `.claude/agents/{julia,jax,pytorch}-sim-runner.md`
- (installed Codex homes + Hermes skills are SEPARATE surfaces — patching the repo does not update them.)

## Out of scope (do not do now)
No installs. No M(C) build. No new ladder sim work until the tuned stack produces a clean post-patch receipt. The leaked M(C) v1 artifacts are quarantined — see `../mc_v1_quarantine_20260609.md`.
