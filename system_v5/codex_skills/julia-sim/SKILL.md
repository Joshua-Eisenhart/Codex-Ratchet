---
name: julia-sim
description: Use when writing or auditing the Julia side of a Codex Ratchet sim so Julia uses the QIT-aligned Julia stack as load-bearing tools instead of a bare LinearAlgebra mirror.
---

# Julia Sim

This is the repo-held Codex skill source governed by `AGENTS.md`.
Claude-family skills and agents are reference-only, not authority or a sync
source. Current tool membership comes from the runtime target map and
`system_v5/ops/tooling/deep_stack_stress_20260714/registry/tool_roster_v1.json`;
do not duplicate membership or deprecation tables here.

Julia is the reference substrate when it can express the claim through aligned packages. It is not enough for code to be written in Julia.

## Step 1: Check Packages

Before package-dependent work or any install proposal, read
`system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md` and run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
```

If the doctor reports repo-local env pollution, wrong-env packages, or active
installers, hold and route through `codex-ratchet-env-agent-coordination`.

Run a direct package check before claiming availability. Use the repo carrier
project with a strict load path; the global default Julia project is a
smoke/bridge surface and can leak packages that are not declared by the
carrier. Treat the fresh check, not the skill text, as authority. Do not add
optional packages if doing so forces stale pins or downgrades.

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier -e 'mods=["JSON3","JSON","CliffordAlgebras","Z3","Quaternions","Octonions","Graphs","ITensors","QuantumClifford","QuantumOptics","Manifolds","Yao","DifferentialEquations","Attractors","DynamicalSystems","ChaosTools"]; println("active_project=",Base.active_project()); println("load_path=",join(Base.LOAD_PATH,":")); for m in mods; try; @eval using $(Symbol(m)); println("OK ",m); catch e; println("FAIL ",m," ",typeof(e),": ",e); end; end'
```

Optional/compatibility packages use isolated named projects and only count for
sims run under that project:

```bash
/opt/homebrew/bin/julia --startup-file=no --project=@codex-ratchet-tensorkit-v1.12 -e 'using TensorKit, IntervalArithmetic; V=ComplexSpace(2); println("TENSORKIT_ENV_OK ", V, " ", sup(sin(interval(0,1))))'
```

```bash
/opt/homebrew/bin/julia --startup-file=no --project=@codex-ratchet-peps-v1.12 -e 'using PEPSKit, TensorKit, IntervalArithmetic; psi=InfinitePEPS(ComplexSpace(2), ComplexSpace(2)); env=CTMRGEnv(psi, ComplexSpace(4)); println("PEPS_ENV_OK ", typeof(psi), " ", typeof(env))'
```

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=@codex-ratchet-attractors-v1.12 -e 'using Attractors, StaticArrays, IntervalArithmetic; println("ATTRACTORS_COMPAT_ENV_OK ", Base.active_project())'
```

Validation: record `Base.active_project()` or `--project=...` in the receipt.
A package loading in an optional project is not available in the carrier
project unless the strict carrier check also imports it.

On failure: if Julia cannot write `.julia/logs` or compile cache under sandbox, rerun with approval. Do not infer package availability.

## Step 1a: Avoid And Quarantine

Hard avoid or replace:

- Do not use `Basins.jl`; use the isolated `Attractors` project.
- Do not use `TensorFlow.jl` for Canon or new sim work.
- Do not use `PyCall` as a tensor bridge for claim-bearing paths; use `PythonCall` plus explicit `DLPack` only after a bridge micro-receipt proves the exchange.
- Do not use old `Jax.jl` wrappers or thin Julia-to-JAX wrappers as Canon infrastructure.
- Do not use `Clipper.jl` as the Clifford/spinor foundation; prefer `Grassmann`, `CliffordAlgebras`, or another verified Clifford package.
- Do not add `PythonCall`, `DLPack`, or `CondaPkg` to the repo carrier project unless the user explicitly asks for a bridge micro-probe. They are bridge machinery, not normal carrier dependencies.

Quarantine by default:

- `CVC5.jl` is not available in the current default Julia project as of the 2026-06-08 check; use Python `cvc5` as the sidecar unless a Julia-native wrapper passes an isolated probe.
- `CombinatorialSpaces`, `Catlab`, extra ML packages, interval/SOS/reachability packages, and PyTorch bridge packages must run in isolated named projects unless a fresh dependency check proves no core/QIT downgrade.
- `Flux`, `Lux`, and `Enzyme` may support candidate generation or differentiation probes, but they do not make a proof or Canon claim by themselves.

## Strict-Carrier Truth + Namespace Discipline

Independent Hermes shakedown result: 37/37 Python checks and 18/18 Julia
strict-carrier checks passed. Preserve these API lessons in carrier sims:

- Namespace collisions are real in multi-package Julia runs. Qualify package
  APIs: `Quaternions.Quaternion`, `CliffordAlgebras.dimension`,
  `ITensors.scalar`, `QuantumOptics.entropy_vn`, `Z3.add`, `Z3.check`,
  `Yao.X`, and `Yao.H`. Unqualified `Quaternion`, `dimension`, `scalar`,
  `entropy_vn`, `X`, and `add` are ambiguous when many packages load.
- `using` inside a Julia function fails. Import packages at top level in probe
  scripts, or use `@eval` carefully when dynamic imports are unavoidable.
- Strict-carrier truth is not global Julia truth. Under
  `JULIA_LOAD_PATH=@:@stdlib --project=system_v5/julia_carrier`, the
  verified-available set is exactly: `JSON`, `JSON3`, `Quaternions`,
  `Octonions`, `CliffordAlgebras`, `Grassmann`, `QuantumClifford`,
  `QuantumOptics`, `QuantumToolbox`, `Yao`, `Z3`, `ITensors`, `ITensorMPS`,
  `Graphs`, `Symbolics`, `Attractors`, `DynamicalSystems`, `ChaosTools`,
  `DifferentialEquations`, `Manifolds`, and `StaticArrays`.
- Not strict-carrier-available: `TensorOperations`, `ITensorNetworks`,
  `Basins`, `Zygote`, `PythonCall`, `DLPack`, and `CondaPkg`. Treat these as
  global-visible or unavailable for carrier claims. Do not claim them in a
  carrier sim without install intent and deliberate admission.

## Tool-Integration Receipt Rule

`load_bearing` = the tool output gates a control, quotient, proof, `all_pass`
condition, divergence value, or demotion condition. A real import/call that
only emits a side readout is `supportive`, NOT `load_bearing`.

Every claimed `load_bearing` tool emits a function-level `tool_calls` entry:
`{tool, qualified_api/function, input_object, output_object, positive_case,
negative/erased_control, boundary_case, demotion_condition, gates: which of
all_pass/divergence/quotient/proof}`. A `load_bearing` claim with no gate is
downgraded to `supportive`.

Julia API footguns:

- Qualify Julia APIs in carrier files: `CliffordAlgebras.<fn>`,
  `Quaternions.Quaternion`, `QuantumOptics.entropy_vn`, `Z3.add`, and
  `Z3.check`.
- Import packages at top level; do not rely on `using` inside functions.
- Strict-carrier truth is only the verified aligned package set above, not
  `ITensorNetworks`, `TensorOperations`, `PythonCall`, `DLPack`, or `Zygote`.

## Step 2: Choose A Load-Bearing Package

Canon-algebra mode: if the claim involves finite noncommutation or nonassociativity, Julia must own or verify the structure-constant artifact. Record the artifact path, `table_version`, `bracket_convention`, `proof_tag`, `source_sha256`, and `artifact_sha256`. When generating tables, derive them from package-native objects (`Octonions`, `Quaternions`, `Grassmann`, `CliffordAlgebras`, etc.) and prove the relevant finite laws with `Z3.jl` over bound `C[k,i,j]` entries. The JSON export shape is `C[k][i][j]`. When consuming tables, do not hand-type, reorder, or reinterpret `C`; if a consumer changes bracket order, it is a new artifact/version.

Use at least one aligned package in the claim path:

- `CliffordAlgebras` for geometric product, Clifford modules, rotors, Hopf/geometric carrier checks.
- `Grassmann` for geometric/exterior algebra, Weyl spinors as even-subalgebra elements, chirality, and carrier layers.
- `DifferentialEquations` for Hopf or nested-tori dynamics with geometry-preserving integration.
- `QuantumClifford` for stabilizers and finite Clifford-group/QIT structures.
- `QuantumOptics` for QIT states, channels, operators, and entropy checks.
- `Z3` for Julia-side SMT checks.
- `ITensors` and `ITensorMPS` for strict-carrier MPS and tensor-network checks.
- `ITensorNetworks` only after install intent and deliberate admission; it is not strict-carrier-available.
- `Graphs` and `Symbolics` for graph/DAG and exact symbolic support.
- `TensorOperations` only after install intent and deliberate admission; it is not strict-carrier-available.
- `TensorKit` and `IntervalArithmetic` latest-direct probes in `--project=@codex-ratchet-tensorkit-v1.12`.
- `PEPSKit` PEPS probes only in `--project=@codex-ratchet-peps-v1.12`; this is the latest PEPSKit line, but it currently constrains TensorKit below latest, so do not use it as a generic TensorKit-latest route.
- `Attractors`, `StaticArrays`, and `IntervalArithmetic` only in `--project=@codex-ratchet-attractors-v1.12` unless a fresh latest-compatible core check proves they no longer downgrade the default env.
- `PythonCall` and `DLPack` only for explicit bridge probes. A bridge path is not claim-bearing until it proves no hidden `.numpy()`, `np.asarray`, CSV, pickle, or host-copy tensor exchange.

Validation: `aligned_packages_load_bearing` contains at least one aligned package and not only `LinearAlgebra`.

On failure: classify the Julia output as bare diagnostic, not a proper Julia sim.

## Step 3: Run Standalone

The Julia file must run without reading a JAX, PyTorch, or previous result JSON to produce parity.

Validation: result includes:

```json
"julia": {
  "ran": true,
  "source_path": "...",
  "packages_used": ["CliffordAlgebras", "Z3"],
  "aligned_packages_load_bearing": ["CliffordAlgebras"],
  "reads_peer_result": false
}
```

On failure: mark `reads_peer_result: true` and reject it from three-engine evidence.

## Step 4: Report Limits

Current 2026-06-08 recheck showed the global default project `/Users/joshuaeisenhart/.julia/environments/v1.12/Project.toml` is not the repo carrier target and is not clean-latest: it loads `PythonCall`, `DLPack`, `CombinatorialSpaces`, `Flux`, `Lux`, and `Enzyme`, but reports drifted dependencies including `Graphs 1.13.1`, `JSON 0.21.4`, `QuantumToolbox 0.44.0`, `Symbolics 6.58.0`, and `CondaPkg 0.2.33`. Use `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml` for carrier/Canon work, and record the exact package versions/project used by the current run.

Optional envs verified on 2026-06-07:

- `--project=@codex-ratchet-tensorkit-v1.12`: `TensorKit 0.17.0`, `IntervalArithmetic 1.0.9`; functional probe constructed `ComplexSpace(2)` and evaluated an interval bound.
- `--project=@codex-ratchet-peps-v1.12`: `PEPSKit 0.7.0`, `TensorKit 0.15.3`, `IntervalArithmetic 1.0.9`; functional probe constructed `InfinitePEPS` and `CTMRGEnv`. This is a PEPSKit-compatibility env, not a TensorKit-latest env.
- `--project=@codex-ratchet-attractors-v1.12`: `Attractors 1.37.0`, `DynamicalSystemsBase 3.18.1`, `SciMLBase 3.18.0`, `StaticArrays 1.9.18`, `IntervalArithmetic 1.0.9`; functional probe computed a tiny bistable-map basin.

Validation: optional packages are recorded with their project. They are blocked in the default env unless a fresh latest-compatible check says otherwise.

On failure: do not pin stale dependencies or globally downgrade the default env to make an optional package work. Isolate it in a project or block it. If a strict latest-dependency requirement is in force, block PEPSKit until its compatibility line supports the needed latest dependency. Do not let a missing package become a fallback to bare `LinearAlgebra`.
