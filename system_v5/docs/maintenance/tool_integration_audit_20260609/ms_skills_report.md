# SKILL + AGENT Tool-Integration Audit

Scope read:

- `.claude/skills/julia-sim/SKILL.md`
- `.claude/skills/jax-sim/SKILL.md`
- `.claude/skills/pytorch-sim/SKILL.md`
- `.claude/skills/three-engine-sim/SKILL.md`
- `.claude/agents/julia-sim-runner.md`
- `.claude/agents/jax-sim-runner.md`
- `.claude/agents/pytorch-sim-runner.md`

Baseline checked against the current Codex-side API lessons:

- Julia namespace qualification in multi-package carrier runs.
- `dynamiqs.QArray.to_jax()` before `jnp` operations.
- Strict-carrier truth is only the verified carrier project package set.
- `ITensorNetworks`, `TensorOperations`, `PythonCall`, `DLPack`, and `Zygote` are not strict-carrier packages.
- JAX x64 before `jax.numpy`.
- No NumPy/host-copy claim path.
- Function-level `tool_calls` for load-bearing tool claims.

## Bottom Line

The `.claude` surfaces are mostly current on strict-carrier truth, x64, `dynamiqs.to_jax`, and no-NumPy claim paths. The main missing tuning is function-level `tool_calls`: the skills and agents often require load-bearing packages, but they do not consistently require receipts at the qualified function/API surface.

There are also a few stale or weak spots:

- Julia examples still use unqualified `scalar(...)`, which conflicts with the namespace-qualification lesson.
- `three-engine-sim` does not carry the `dynamiqs.QArray.to_jax()` footgun in its JAX package surface.
- Runner agents do not force `tool_calls` in their verify/report protocol.
- `julia-sim-runner` lacks the namespace and top-level `using` rules, even though the Julia skill has them.

## Per-Surface Findings

### `.claude/skills/julia-sim/SKILL.md`

Captures:

- Strict carrier command and repo carrier project.
- Optional project isolation.
- Namespace qualification rule.
- `using` inside Julia function footgun.
- Exact strict-carrier package set.
- Explicit non-strict list including `TensorOperations`, `ITensorNetworks`, `Zygote`, `PythonCall`, `DLPack`.

Stale/missing:

- Tested API example still uses unqualified `scalar(...)`.
- Validity checklist does not require function-level `tool_calls`.

Patch:

- Qualify the example as `CliffordAlgebras.scalar(...)`.
- Add a validity gate requiring function-level `tool_calls`.

### `.claude/skills/jax-sim/SKILL.md`

Captures:

- `jax_enable_x64`.
- `dynamiqs.QArray.to_jax()` lesson.
- No `.numpy()`, `np.asarray`, CSV, pickle, or host-copy claim path.
- `numpy`/`scipy` control-only.

Stale/missing:

- Environment line says only Makefile `PYTHON`; patch should also name the canonical sim-stack Python path for consistency with runner and Codex skills.
- Does not require function-level `tool_calls`.

Patch:

- Add explicit x64 snippet before `jax.numpy`.
- Add function-level `tool_calls` requirement.

### `.claude/skills/pytorch-sim/SKILL.md`

Captures:

- PyTorch scoped role.
- No NumPy/host-copy claim path.
- `numpy`/`scipy` control-only.
- PyTorch is not Canon arbiter.

Stale/missing:

- Environment line does not explicitly require `GEOMSTATS_BACKEND=pytorch` before import.
- Does not require function-level `tool_calls`.

Patch:

- Add `GEOMSTATS_BACKEND=pytorch` requirement.
- Add function-level `tool_calls` validity gate.

### `.claude/skills/three-engine-sim/SKILL.md`

Captures:

- Engine roles.
- No NumPy claim path.
- Function-level tool receipts in principle.
- Strict carrier correction appears later in the tested pattern section.
- Non-strict list includes `ITensorNetworks`, `TensorOperations`, `Zygote`, `PythonCall`, `DLPack`, and `CondaPkg`.

Stale/missing:

- Primary Julia package section does not state the exact strict-carrier set where builders will look first.
- JAX package line omits `dynamiqs` and the `.to_jax()` rule.
- Validity checklist does not make `tool_calls` a hard check.
- Tested Julia example still uses unqualified `scalar(...)`.

Patch:

- Add exact strict-carrier set in the primary Julia section.
- Add `dynamiqs` with `QArray.to_jax()` in the JAX package line.
- Add function-level `tool_calls` as a hard validity check.
- Qualify `CliffordAlgebras.scalar(...)`.

### `.claude/agents/julia-sim-runner.md`

Captures:

- Strict carrier command and exact carrier package set.
- Non-strict package list.
- No cross-run parity.
- Standalone execution and load-bearing package usage.

Stale/missing:

- Missing namespace qualification rule.
- Missing `using`-inside-function footgun.
- Verify/report protocol does not require function-level `tool_calls`.

Patch:

- Add API discipline paragraph.
- Add `tool_calls` to verify and report protocol.

### `.claude/agents/jax-sim-runner.md`

Captures:

- Canonical sim-stack Python path.
- `jax_enable_x64`.
- No NumPy/host-copy claim path.
- Avoids stale JAX internals and broken packages.

Stale/missing:

- Lists `dynamiqs` as installed but does not capture `QArray.to_jax()`.
- Verify/report protocol does not require function-level `tool_calls`.

Patch:

- Add JAX API discipline paragraph for `dynamiqs.to_jax()` and `tool_calls`.
- Add `tool_calls` to verify and report protocol.

### `.claude/agents/pytorch-sim-runner.md`

Captures:

- PyTorch scoped role and non-arbiter boundary.
- No NumPy/host-copy claim path.
- Candidate/witness status for ODE/optimization tools.

Stale/missing:

- Verify/report protocol does not require function-level `tool_calls`.

Patch:

- Add tool receipt discipline paragraph.
- Add `tool_calls` to verify and report protocol.

## Exact Patch To Apply

````diff
diff --git a/.claude/skills/julia-sim/SKILL.md b/.claude/skills/julia-sim/SKILL.md
index 29f829f72..958c5a9fd 100644
--- a/.claude/skills/julia-sim/SKILL.md
+++ b/.claude/skills/julia-sim/SKILL.md
@@ -39,7 +39,7 @@ When this lane writes or consumes the current Canon artifact, also follow `syste
 ## Tested API (actually executed)
 ```julia
 using CliffordAlgebras
-cl3 = CliffordAlgebra(:Cl3); gp = cl3.e1*cl3.e2*cl3.e3; s = scalar(cl3.e1*cl3.e1)  # ==1
+cl3 = CliffordAlgebra(:Cl3); gp = cl3.e1*cl3.e2*cl3.e3; s = CliffordAlgebras.scalar(cl3.e1*cl3.e1)  # ==1
 using Z3
 solver = Z3.Solver(); x = Z3.IntVar("x")
 Z3.add(solver, x < Z3.IntVal(42)); Z3.add(solver, x > Z3.IntVal(40))
@@ -57,6 +57,7 @@ Independent Hermes shakedown result: 37/37 Python checks and 18/18 Julia strict-
 
 ## Validity — the Julia leg is INVALID unless
 - [ ] `using` ≥1 aligned package carrying the claim — **not** a bare `LinearAlgebra` reimplementation.
+- [ ] every load-bearing Julia package/API has a function-level `tool_calls` receipt naming the qualified function surface, input object, output object, positive case, erased/negative control, boundary case, and demotion condition.
 - [ ] genuinely RAN standalone (you executed it; result freshly produced).
 - [ ] records the active Julia project; optional packages run under their named isolated project.
 - [ ] no stale pins or global downgrades in the default Julia env.
diff --git a/.claude/skills/jax-sim/SKILL.md b/.claude/skills/jax-sim/SKILL.md
index 04cf28ae9..b80a436de 100644
--- a/.claude/skills/jax-sim/SKILL.md
+++ b/.claude/skills/jax-sim/SKILL.md
@@ -9,7 +9,12 @@ description: "Build the JAX leg of a Codex-Ratchet sim as the batched/exhaustive
 JAX is the batched/exhaustive workhorse after Julia fixes Canon algebra/order. Use it for `vmap`/`jit` sweeps, differentiable dynamics, scale searches, vectorized witness generation, and proof-shaped finite objects. A packet using only `jnp` is baseline, not rich-tool: it is admissible only when the claim is *explicitly* a baseline numeric mirror. Otherwise a rich/crossover package must carry the claim. First line always `jax.config.update("jax_enable_x64", True)`.
 
 ## Environment
-Makefile `PYTHON` interpreter, x64 enabled.
+Makefile `PYTHON` interpreter or `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`, x64 enabled before importing `jax.numpy`:
+
+```python
+from jax import config
+config.update("jax_enable_x64", True)
+```
 
 ## Packages → role
 | role | package |
@@ -35,6 +40,7 @@ For current Canon artifact consumers, require the receipt shape in `system_v5/do
 
 ## API Footguns
 - `dynamiqs` returns its own `QArray`, not a raw JAX ndarray. Call `.to_jax()` before any `jnp`-native operation, for example `jnp.trace(rho.to_jax())`.
+- Every load-bearing JAX/rich/crossover package must emit function-level `tool_calls`: qualified function/API surface, input object, output object, positive case, erased/negative control, boundary case, and demotion condition. Import success or package names alone are not evidence.
 
 ## Tested API (actually executed)
 ```python
@@ -50,6 +56,7 @@ import e3nn_jax as e3; e3.Irreps("1x1o")
 
 ## Validity — the JAX leg is INVALID unless
 - [ ] ≥1 rich/crossover package is load-bearing — not bare `jnp` (unless the claim is *explicitly* a baseline mirror).
+- [ ] load-bearing package use is backed by function-level `tool_calls`, not only `packages_used` or prose.
 - [ ] a `z3`+`cvc5` structural proof is load-bearing and both solvers agree (the erase-flip fires).
 - [ ] geomstats is torch-only — any jax sphere/Riemannian quantity uses `e3nn_jax` or hand-rolled, said honestly; never a faked jax-geomstats path.
 - [ ] genuinely RAN; NO cross-run parity (does not read a Julia/torch file).
diff --git a/.claude/skills/pytorch-sim/SKILL.md b/.claude/skills/pytorch-sim/SKILL.md
index f318ce572..886dbb216 100644
--- a/.claude/skills/pytorch-sim/SKILL.md
+++ b/.claude/skills/pytorch-sim/SKILL.md
@@ -9,7 +9,7 @@ description: Build the PyTorch leg of a Codex-Ratchet sim as a first-class graph
 PyTorch is first-class when the claim path needs graph/network/autograd/existing torch machinery. Its strongest roles are `torch_geometric` message passing, `torch.func`/`functorch` transforms, differentiable geometric computation with `torch_ga`, torch-backed geometry/equivariance, dynamics/candidate tools, and proof checks over torch-derived finite values. PyTorch is never the semantic arbiter over Julia Canon. **If torch would only redo bare array math, mark it `not_scoped` honestly**; a faked or redundant torch leg is worse than none.
 
 ## Environment
-Makefile `PYTHON` interpreter, torch complex128.
+Makefile `PYTHON` interpreter or `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`, torch complex128. If using `geomstats`, set `GEOMSTATS_BACKEND=pytorch` before import and record that distances/geodesics are torch tensors.
 
 ## Packages → role
 | role | package |
@@ -45,6 +45,7 @@ from torch.func import jacrev; jacrev(lambda x:(x**2).sum())(torch.tensor([3.0])
 ## Validity — the PyTorch leg is INVALID unless
 - [ ] it adds a genuinely different check (preferably differentiable/gradient-based) — else skip it and say so.
 - [ ] a real geometric/diff tool is load-bearing — not bare torch array math (shared numpy corruption with jax).
+- [ ] every load-bearing torch/geometric/proof package has a function-level `tool_calls` receipt naming the qualified function/API surface, input object, output object, positive case, erased/negative control, boundary case, and demotion condition.
 - [ ] never the semantic arbiter over Julia Canon; bare array-value agreement is lower authority than Julia-arbitrated Canon evidence.
 - [ ] genuinely RAN; NO cross-run parity. `numpy`/`scipy` control-only. `classification=scratch_diagnostic`, `promotion_allowed=false`.
 
diff --git a/.claude/skills/three-engine-sim/SKILL.md b/.claude/skills/three-engine-sim/SKILL.md
index ba7756ee9..d791bf2c3 100644
--- a/.claude/skills/three-engine-sim/SKILL.md
+++ b/.claude/skills/three-engine-sim/SKILL.md
@@ -31,9 +31,10 @@ The computational substrate's semantics are not neutral. numpy's world (floating
 - `Z3` (Z3.jl) — SMT structural proofs
 - `ITensors` / `ITensorMPS` — strict-carrier MPS / tensor-network checks; `ITensorNetworks` requires install intent and deliberate admission because it is not strict-carrier-available.
 - `DifferentialEquations` — Hopf / nested-tori symplectic (geometry-preserving) integration
+- Strict-carrier truth is only the verified carrier project set: `JSON`, `JSON3`, `Quaternions`, `Octonions`, `CliffordAlgebras`, `Grassmann`, `QuantumClifford`, `QuantumOptics`, `QuantumToolbox`, `Yao`, `Z3`, `ITensors`, `ITensorMPS`, `Graphs`, `Symbolics`, `Attractors`, `DynamicalSystems`, `ChaosTools`, `DifferentialEquations`, `Manifolds`, and `StaticArrays`. `ITensorNetworks`, `TensorOperations`, `Basins`, `Zygote`, `PythonCall`, `DLPack`, and `CondaPkg` are not strict-carrier-available.
 
 **JAX (batched/exhaustive + dynamics)** — interpreter from Makefile `PYTHON`, x64 first line
-- `jnp` (x64) array core · `diffrax` (Lindblad/GKSL ODE, real-imag split for complex) · `netket` (variational many-body, 8–64+ sites) · `quimb`+`cotengra`+`autoray` (tensor-network scale) · `equinox`/`flax` (modules) · `optax`/`jaxopt`/`lineax` (optim/root/linsolve) · `jraph` (graphs) · `ott` (optimal transport) · `e3nn_jax` (SO(3)/SU(2) equivariance, where geomstats can't)
+- `jnp` (x64) array core · `dynamiqs` (`QArray.to_jax()` before `jnp` operations) · `diffrax` (Lindblad/GKSL ODE, real-imag split for complex) · `netket` (variational many-body, 8–64+ sites) · `quimb`+`cotengra`+`autoray` (tensor-network scale) · `equinox`/`flax` (modules) · `optax`/`jaxopt`/`lineax` (optim/root/linsolve) · `jraph` (graphs) · `ott` (optimal transport) · `e3nn_jax` (SO(3)/SU(2) equivariance, where geomstats can't)
 
 **PyTorch (graph/network/autograd machinery)** — torch complex128. Its strengths include graph/message-passing, autograd through geometric structure, torch-native differentiable checks, torch-backed geometry/equivariance, and proof checks over torch-derived finite values.
 - **`torch_ga`** — torch-native DIFFERENTIABLE geometric algebra (autograd GA; `GeometricAlgebra(metric=...)`) — torch's edge over numpy-`clifford`
@@ -47,6 +48,8 @@ The computational substrate's semantics are not neutral. numpy's world (floating
 
 **Control-only — NEVER load-bearing, NEVER in the claim path:** `numpy`, `scipy`, `mpmath`.
 
+**Function-level tool receipts:** every load-bearing tool claim must include `tool_calls` or equivalent function-level receipts naming the qualified function/API surface, input object, output object, positive case, erased/negative control, boundary case, and demotion condition. `packages_used` and imports alone are not evidence.
+
 **Canon artifact rule — finite noncommutation / nonassociativity:** Julia owns the structure constants, bracket order, table version, and proof tag. The current seed artifact is `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json` with receipt `system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json` (`scratch_diagnostic`, no promotion). Any JAX/PyTorch consumer must verify `source_sha256`, `artifact_sha256`, `proof_tag`, `proof_pass`, `table_version`, and `bracket_convention`, then compute `mul(a,b)[k]=sum_ij C[k][i][j]*a[i]*b[j]` with fixed parenthesization. No hand-typed table, hidden reassociation, `.numpy()`, `np.asarray`, CSV, pickle, or host-object bridge can sit on the claim/data path.
 
 **Canon runtime receipt rule:** for any result that consumes the Canon artifact, read `system_v5/docs/JULIA_CANON_RUNTIME_CONTRACT.md` and require `canon_runtime` plus `foreign_runtime_manifest`. Missing fields do not make the result worthless, but they block "full Canon runtime receipt" language and keep the ceiling at scratch/diagnostic unless another exact gate says otherwise.
@@ -66,6 +69,7 @@ The computational substrate's semantics are not neutral. numpy's world (floating
 - [ ] **Mandatory runtime preflight** — before building, verify the actual env (record `sys.executable` / `Pkg.project()` + import status); never trust memory for package state.
 - [ ] **Role-separated, bounded** — one engine leg per build packet (a monolithic all-three build times out); legs are synthesized by the controller, not built in one shot.
 - [ ] **No decorative tooling / unformalized proof = HARD FAIL** — an import that does no work for the claim, or a proof of a sentence that was never formalized, does not count as load-bearing.
+- [ ] **Function-level tool calls** — each load-bearing tool has `tool_calls` or equivalent function-level receipts; package names and import success are insufficient.
 - [ ] **Envelope-first audit** — read the combined envelope, infer or read the declared mode, then inspect Julia, JAX, and PyTorch local lane receipts before any packet-level verdict.
 - [ ] **Canon runtime fields** — Canon artifact consumers include `canon_runtime` and `foreign_runtime_manifest`; if absent, report the missing fields and keep the packet below full runtime-receipt status.
 
@@ -119,7 +123,7 @@ Every pattern below was built by codex2 and **actually executed** (2026-06-07, `
 using CliffordAlgebras
 cl3 = CliffordAlgebra(:Cl3)              # real geometric algebra, NOT LinearAlgebra
 gp  = cl3.e1 * cl3.e2 * cl3.e3           # geometric product
-s   = scalar(cl3.e1 * cl3.e1)            # == 1
+s   = CliffordAlgebras.scalar(cl3.e1 * cl3.e1)  # == 1
 using Z3
 solver = Z3.Solver(); x = Z3.IntVar("x")
 Z3.add(solver, x < Z3.IntVal(42)); Z3.add(solver, x > Z3.IntVal(40))
diff --git a/.claude/agents/julia-sim-runner.md b/.claude/agents/julia-sim-runner.md
index 78e5bb85b..5a08e1ed3 100644
--- a/.claude/agents/julia-sim-runner.md
+++ b/.claude/agents/julia-sim-runner.md
@@ -12,6 +12,8 @@ You run and verify the **Julia leg** of a three-engine Codex-Ratchet sim. Julia
 
 **Canon-algebra mode:** if the bounded claim is finite noncommutation/nonassociativity, Julia must generate or verify the structure-constant artifact. Required receipt fields: artifact path, `table_version`, `bracket_convention`, `proof_tag`, `source_sha256`, `artifact_sha256`, and `proof_pass`. Tables must be derived from package-native objects (`Octonions`, `Quaternions`, `Grassmann`, `CliffordAlgebras`, etc.) and finite laws checked with `Z3.jl` over bound `C[k,i,j]` entries; exported JSON consumers see `C[k][i][j]`. If a downstream engine consumes the table, changing bracket order or table entries requires a new artifact/version.
 
+**API discipline:** namespace collisions are expected in multi-package Julia runs. Require qualified surfaces such as `Quaternions.Quaternion`, `CliffordAlgebras.dimension`, `ITensors.scalar`, `QuantumOptics.entropy_vn`, `Z3.add`, `Z3.check`, `Yao.X`, and `Yao.H` when those packages are in scope. Do not put `using` inside a Julia function; imports belong at top level, with `@eval` only for deliberate dynamic probes.
+
 **REQUIRED Julia QIT-aligned stack — every julia sim uses the package(s) aligned to its layer (bare `LinearAlgebra` is FORBIDDEN as the carrier):**
 
 | package | role — use it for |
@@ -40,6 +42,7 @@ You run and verify the **Julia leg** of a three-engine Codex-Ratchet sim. Julia
    - The sim actually RAN standalone (you executed it; the result was freshly produced, not a pre-existing JSON).
    - No cross-run parity: the Julia sim does NOT read a JAX/torch result file to fake agreement. It computes from scratch.
    - The aligned package is LOAD-BEARING: removing it changes/breaks the result (state this).
-4. **Report:** the Julia-computed observable values (the reference), which packages were genuinely used, whether each is load-bearing, and the standalone exit/pass state. If the build came back as a bare LinearAlgebra mirror, REJECT it and re-dispatch codex2 with a sharper package-usage requirement.
+   - Each load-bearing package/API has a function-level `tool_calls` receipt naming the qualified function surface, input object, output object, positive case, erased/negative control, boundary case, and demotion condition.
+4. **Report:** the Julia-computed observable values (the reference), which packages were genuinely used, whether each is load-bearing, the function-level `tool_calls`, and the standalone exit/pass state. If the build came back as a bare LinearAlgebra mirror, REJECT it and re-dispatch codex2 with a sharper package-usage requirement.
 
 **Fences:** classification `scratch_diagnostic`, `promotion_allowed=false`. numpy/scipy are control-only and never in the claim path (n/a on Julia anyway). You are a runner+verifier — codex2 authors, you execute and judge. A builder never grades its own work, so you (not codex2) decide whether the Julia leg is genuine.
diff --git a/.claude/agents/jax-sim-runner.md b/.claude/agents/jax-sim-runner.md
index 1c1a48749..75d66706b 100644
--- a/.claude/agents/jax-sim-runner.md
+++ b/.claude/agents/jax-sim-runner.md
@@ -12,6 +12,8 @@ You run and verify the **JAX leg** of a Codex-Ratchet sim. JAX is the batched/ex
 
 **Canon-table consumer rule:** if this lane consumes `algebra_structure_constants_v1.json`, load `C[k][i][j]`, `table_version`, `bracket_convention`, and `proof_tag` from the artifact and implement products as explicit fixed-order contractions. Also emit `canon_runtime` and `foreign_runtime_manifest` per `system_v5/docs/JULIA_CANON_RUNTIME_CONTRACT.md`. Never re-associate `(a*b)*c` to `a*(b*c)` unless the proof tag covers that exact case. Do not use `.numpy()`, `np.asarray`, CSV, pickle, or host-object serialization on the claim/data path. Avoid `bayeux`, `oryx`, `jax-verify`, `jax.experimental.host_callback`, and direct JAX internals; optimizers/samplers (`optax`, `jaxopt`, `blackjax`, `numpyro`, `optimistix`, `cvxpylayers`) are candidate/counterexample tools until certified.
 
+**JAX API discipline:** `dynamiqs` returns a `QArray`, not a raw JAX ndarray. Any `jnp`-native operation must call `.to_jax()` first, for example `jnp.trace(rho.to_jax())`. Each load-bearing JAX/rich/crossover package must emit function-level `tool_calls` naming the qualified function/API surface, input object, output object, positive case, erased/negative control, boundary case, and demotion condition.
+
 **Your protocol:**
 1. **Build via codex2, never author yourself.** The build spec MUST require: (a) a LOAD-BEARING `z3`+`cvc5` structural proof (UNSAT/SAT), dual-solver agreement; (b) at least one rich package doing real work where relevant (`diffrax` for dynamics, `quimb`+`cotengra` for tensor-network scale, `netket` for many-body, `e3nn_jax` for equivariance); and FORBID bare-`jnp`-only with no crossover proof.
 2. **Run it** on the Makefile interpreter. Capture stdout + result JSON.
@@ -21,6 +23,7 @@ You run and verify the **JAX leg** of a Codex-Ratchet sim. JAX is the batched/ex
    - geomstats is torch-only — if a sphere/Riemannian quantity is needed on jax, it uses `e3nn_jax` or hand-rolled and SAYS SO; never a faked jax-geomstats path.
    - `numpy`/`scipy` appear only as control/reference, never in the claim path.
    - no cross-run parity: it does not read a Julia/torch file to fake agreement.
-4. **Report:** the JAX-computed observable values (for the divergence table vs Julia), which packages were load-bearing, the dual-SMT verdict, and standalone pass state.
+   - function-level `tool_calls` exist for every load-bearing rich/crossover package.
+4. **Report:** the JAX-computed observable values (for the divergence table vs Julia), which packages were load-bearing, the function-level `tool_calls`, the dual-SMT verdict, and standalone pass state.
 
 **Fences:** `scratch_diagnostic`, `promotion_allowed=false`. You run+verify; codex2 authors. You decide whether the JAX leg is genuine.
diff --git a/.claude/agents/pytorch-sim-runner.md b/.claude/agents/pytorch-sim-runner.md
index 8cfe25c92..199b9ef0b 100644
--- a/.claude/agents/pytorch-sim-runner.md
+++ b/.claude/agents/pytorch-sim-runner.md
@@ -19,11 +19,13 @@ You run and verify the **PyTorch leg** of a Codex-Ratchet sim. PyTorch is first-
 
 **Canon-table consumer rule:** if this lane consumes `algebra_structure_constants_v1.json`, load `C[k][i][j]`, `table_version`, `bracket_convention`, and `proof_tag` from the artifact and implement products as explicit fixed-order contractions. Also emit `canon_runtime` and `foreign_runtime_manifest` per `system_v5/docs/JULIA_CANON_RUNTIME_CONTRACT.md`. Never re-associate `(a*b)*c` to `a*(b*c)` unless the proof tag covers that exact case. Do not use `.numpy()`, `np.asarray`, CSV, pickle, or host-object serialization on the claim/data path. `torchdiffeq`, `torchode`, `xitorch`, and `cvxpylayers` are candidate/witness tools, not proof; PyG optional wheels, DGL, and PyTorch3D require pinned env receipts before assumption.
 
+**Tool receipt discipline:** every load-bearing torch/geometric/proof package must emit function-level `tool_calls` naming the qualified function/API surface, input object, output object, positive case, erased/negative control, boundary case, and demotion condition. Import success, package names, and torch tensor agreement with JAX are not evidence by themselves.
+
 **Your protocol:**
 1. **Decide whether this is a required envelope leg.** If the packet is `schema_version=three_engine_sim_result_v1` or the user asks for all three sims, run the PyTorch leg with a real tool-native role; if no such role exists, mark the packet blocked/excluded rather than silently skipping. For explicitly non-envelope diagnostics, run torch only when `torch_ga`/`clifford`/`geomstats`/`e3nn`/PyG/`torch.func`/proof tools give a real third check.
 2. **Build via codex2** (never author yourself); spec requires genuine `clifford`/`geomstats`/`e3nn` usage for the geometric quantity, torch complex128 for arrays.
 3. **Run it** on the Makefile interpreter.
-4. **Verify — REJECT if:** imports don't show a real geometric tool used; it's bare torch array math (no added value); it reads another engine's file to fake agreement; numpy/scipy in the claim path.
-5. **Report:** the torch-computed values, which graph/network/autograd/geometric/proof tool was load-bearing, and whether the enclosing result should be validated with `scripts/validate_three_engine_sim_result.py --require-pytorch`. For a non-PyTorch-scoped diagnostic only, a clear `not_scoped_by_mode` is allowed.
+4. **Verify — REJECT if:** imports don't show a real geometric tool used; function-level `tool_calls` are missing for a claimed load-bearing tool; it's bare torch array math (no added value); it reads another engine's file to fake agreement; numpy/scipy in the claim path.
+5. **Report:** the torch-computed values, which graph/network/autograd/geometric/proof tool was load-bearing, the function-level `tool_calls`, and whether the enclosing result should be validated with `scripts/validate_three_engine_sim_result.py --require-pytorch`. For a non-PyTorch-scoped diagnostic only, a clear `not_scoped_by_mode` is allowed.
 
 **Fences:** `scratch_diagnostic`, `promotion_allowed=false`. Never the semantic arbiter over Julia Canon. You run+verify; codex2 authors.
````
