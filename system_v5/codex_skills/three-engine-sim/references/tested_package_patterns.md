# Tested Package Patterns

These are local Codex rerun receipts from 2026-06-07 plus a targeted package-risk recheck from 2026-06-08. Treat them as smoke patterns, not proof of any scientific claim.

## Canon algebra artifact seed

Current bounded receipt:

```text
source: system_v5/julia_carrier/canon_algebra_artifact_v1.jl
artifact: system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json
result: system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json
classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
```

Load-bearing tools: `Quaternions`, `Octonions`, and `Z3`. The artifact derives quaternion `[4,4,4]` and octonion `[8,8,8]` structure constants from Julia package-native basis products. The Z3 receipt checks bound `C[k,i,j]` entries: quaternion nonzero-associator search is `unsat`, octonion nonzero-associator search is `sat`, and octonion alternative/flexible violation searches are `unsat`. Consumer lanes must verify `source_sha256`, `artifact_sha256`, `proof_tag`, `proof_pass`, `table_version`, and `bracket_convention` before using it.

## Julia

Command:

```bash
/opt/homebrew/bin/julia /tmp/refex/ref_julia.jl
```

Fresh rerun result:

```text
PKG_AVAILABLE requested_installed=CliffordAlgebras,Z3
REF_JULIA_DONE packages_used=CliffordAlgebras,Z3 all_ran=true
```

Strict carrier core stack load check from this session:

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier -e 'packages=["JSON3","JSON","CliffordAlgebras","Z3","Quaternions","Octonions","Graphs","ITensors","QuantumClifford","QuantumOptics","Manifolds","Yao","DifferentialEquations","Attractors","DynamicalSystems","ChaosTools"]; println("active_project=",Base.active_project()); println("load_path=",join(Base.LOAD_PATH,":")); for p in packages; Base.require(Main, Symbol(p)); println("CARRIER_LOAD_OK ",p); end'
```

Fresh load result:

```text
active_project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml
load_path=@:@stdlib
CARRIER_LOAD_OK JSON3
CARRIER_LOAD_OK JSON
CARRIER_LOAD_OK CliffordAlgebras
CARRIER_LOAD_OK Z3
CARRIER_LOAD_OK Quaternions
CARRIER_LOAD_OK Octonions
CARRIER_LOAD_OK Graphs
CARRIER_LOAD_OK ITensors
CARRIER_LOAD_OK QuantumClifford
CARRIER_LOAD_OK QuantumOptics
CARRIER_LOAD_OK Manifolds
CARRIER_LOAD_OK Yao
CARRIER_LOAD_OK DifferentialEquations
CARRIER_LOAD_OK Attractors
CARRIER_LOAD_OK DynamicalSystems
CARRIER_LOAD_OK ChaosTools
```

Previously observed latest-compatible core line after removing optional-package downgrades from the default project:

```text
LinearSolve 3.84.0
OrdinaryDiffEqDifferentiation 3.2.0
SciMLBase 3.18.0
Symbolics 7.26.0
```

Working APIs:

```julia
using CliffordAlgebras
cl3 = CliffordAlgebra(:Cl3)
gp = cl3.e1 * cl3.e2 * cl3.e3
scalar(cl3.e1 * cl3.e1)
```

```julia
using Z3
solver = Z3.Solver()
x = Z3.IntVar("x")
Z3.add(solver, x < Z3.IntVal(42))
Z3.add(solver, x > Z3.IntVal(40))
Z3.check(solver)
Z3.model(solver)
```

Historical default/global-project observation from the requested QIT-aligned list: `CliffordAlgebras`, `Grassmann`, `DifferentialEquations`, `QuantumClifford`, `QuantumOptics`, `Z3`, `ITensorNetworks`, `ITensors`, `ITensorMPS`, `Graphs`, `TensorOperations`, and `Symbolics` were observed outside the strict carrier boundary. This is not strict-carrier evidence. Current strict carrier truth admits `ITensors`/`ITensorMPS`, `Graphs`, and `Symbolics`; `ITensorNetworks` and `TensorOperations` require install intent and deliberate admission before a carrier sim may cite them.

2026-06-08 drift recheck of the default `@v1.12` project:

```text
OK PythonCall
OK DLPack
FAIL CVC5 package not found
OK CombinatorialSpaces
FAIL Catlab package not found
OK Flux
OK Lux
OK Enzyme
Graphs 1.13.1
JSON 0.21.4
QuantumToolbox 0.44.0
Symbolics 6.58.0
CondaPkg 0.2.33
PythonCall 0.9.35
DLPack 0.3.1
```

Interpretation: the default Julia project is currently a usable smoke-test surface, not a clean Canon project. `PythonCall`/`DLPack` can be tested for bridge probes; `CVC5.jl` cannot be assumed; `CombinatorialSpaces`, ML/AD packages, and optional proof packages should be isolated unless a fresh dependency check proves no core/QIT downgrade.

Optional packages are not part of the default project because forcing them there downgraded the core SciML line. Use only the isolated projects below. `TensorKit` has a strict latest project. `PEPSKit` has a PEPSKit-latest compatibility project that currently constrains TensorKit below latest, so it is not the generic TensorKit route.

TensorKit latest optional project:

```bash
/opt/homebrew/bin/julia --startup-file=no --project=@codex-ratchet-tensorkit-v1.12 -e 'using Pkg; deps=Pkg.dependencies(); for n in ["TensorKit","IntervalArithmetic"]; p=first([p for p in values(deps) if p.name==n]); println(n," ",p.version," direct=",p.is_direct_dep); end; using TensorKit, IntervalArithmetic; V=ComplexSpace(2); println("TENSORKIT_ENV_OK space=", V, " interval_sup=", sup(sin(interval(0,1))))'
```

Observed:

```text
TensorKit 0.17.0 direct=true
IntervalArithmetic 1.0.9 direct=true
TENSORKIT_ENV_OK space=ComplexSpace(2) interval_sup=0.8414709848078966
```

PEPSKit compatibility optional project:

```bash
/opt/homebrew/bin/julia --startup-file=no --project=@codex-ratchet-peps-v1.12 -e 'using Pkg; deps=Pkg.dependencies(); for n in ["PEPSKit","TensorKit","IntervalArithmetic","MPSKit","LoggingExtras"]; p=first([p for p in values(deps) if p.name==n]); println(n," ",p.version," direct=",p.is_direct_dep); end; using PEPSKit, TensorKit, IntervalArithmetic; psi=InfinitePEPS(ComplexSpace(2), ComplexSpace(2)); env=CTMRGEnv(psi, ComplexSpace(4)); x=interval(0,1); println("PEPS_ENV_OK psi=", typeof(psi), " env=", typeof(env), " interval_sup=", sup(sin(x)))'
```

Observed:

```text
PEPSKit 0.7.0 direct=true
TensorKit 0.15.3 direct=true
IntervalArithmetic 1.0.9 direct=true
MPSKit 0.13.8 direct=false
LoggingExtras 1.0.3 direct=false
PEPS_ENV_OK ...
```

`Pkg.status(...; outdated=true)` reports `TensorKit v0.15.3 (<v0.17.0)` blocked by `MPSKit`/`PEPSKit`. Treat this as PEPSKit-specific compatibility, not as latest TensorKit evidence. If a sim requires strict latest dependencies, mark the PEPSKit route blocked until upstream compatibility moves.

Attractors optional project:

```bash
/opt/homebrew/bin/julia --startup-file=no --project=@codex-ratchet-attractors-v1.12 -e 'using Pkg; deps=Pkg.dependencies(); for n in ["Attractors","DynamicalSystemsBase","SciMLBase","StaticArrays","IntervalArithmetic"]; p=first([p for p in values(deps) if p.name==n]); println(n," ",p.version," direct=",p.is_direct_dep); end; using Attractors, StaticArrays, IntervalArithmetic; function dumb_map(z,p,n); x,y=z; r=p[1]; return r < 0.5 ? SVector(0.0,0.0) : (x >= 0 ? SVector(r,r) : SVector(-r,-r)); end; r=1.0; ds=DeterministicIteratedMap(dumb_map, SVector(0.0,0.0), [r]); xg=yg=range(-1.5,2.5; length=3); attrs=Dict(1=>StateSpaceSet([SVector(r,r)]), 2=>StateSpaceSet([SVector(-r,-r)])); mapper=AttractorsViaProximity(ds, attrs; Ttr=0); basins, atts=basins_of_attraction(mapper, (xg,yg); show_progress=false); ok=basins[1,:] == fill(2,3) && basins[2,:] == fill(1,3) && basins[3,:] == fill(1,3) && length(atts)==2; println("ATTRACTORS_ENV_OK ", ok, " basins=", basins, " attractors=", length(atts), " interval_sup=", sup(sin(interval(0,1)))); if !ok; exit(1); end'
```

Observed:

```text
Attractors 1.37.0 direct=true
DynamicalSystemsBase 3.18.1 direct=false
SciMLBase 3.18.0 direct=false
StaticArrays 1.9.18 direct=true
IntervalArithmetic 1.0.9 direct=true
ATTRACTORS_ENV_OK true ...
```

Latest-only rule: do not pin stale dependencies or globally downgrade the default Julia project to make an optional package coexist. If a tool only works in an isolated project, record that project in the receipt. If a package's current release requires an older dependency line, quarantine it to that route and do not generalize the dependency as latest.

## JAX

Command:

```bash
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 /tmp/refex/ref_jax.py
```

Fresh rerun result:

```text
z3 triangle_2color=unsat path_2color=sat
cvc5 triangle_2color=unsat path_2color=sat
quimb mps_norm_contract=1.000000000000
diffrax exp_i_pi_over_2=-0.000000000000+1.000000000000j dtype=float64
REF_JAX_DONE packages_used=['jax', 'jax.numpy', 'z3', 'cvc5', 'quimb.tensor', 'diffrax'] all_ran=True
```

Required setup:

```python
from jax import config
config.update("jax_enable_x64", True)
```

Use `NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache` for `quimb` in this environment.

Additional current functional checks passed in the canonical Python venv: JAX x64 complex dtype, `netket` Hilbert space construction, `e3nn_jax` irreps, `ott`, `z3`, `cvc5`, `quimb`, and `diffrax`.

2026-06-08 Python risk recheck:

```text
FAIL bayeux old JAX API
OK blackjax 1.5
OK optimistix 0.1.0
OK jax 0.10.1
OK cvc5 1.3.3
```

Interpretation: do not use `bayeux` in the active JAX lane. `blackjax` and `optimistix` are available as candidate/witness tools, with proof promotion blocked until certification.

## PyTorch

Command:

```bash
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 /tmp/refex/ref_torch.py
```

Fresh rerun result:

```text
REF_TORCH_DONE packages_used=['torch', 'clifford', 'geomstats', 'e3nn'] all_ran=True
```

Additional current functional checks passed:

```text
OK torch complex128
OK torch_ga GeometricAlgebra(...)
OK clifford Cl(3)
OK e3nn_o3 1x0e+1x1o
OK torch_func_jacrev [2.0, 4.0]
OK torch_geometric 2.7.0
```

For proper torch-side `geomstats`, set the backend before importing geomstats:

```bash
env GEOMSTATS_BACKEND=pytorch NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache python3 ...
```

Fresh backend check:

```text
backend geomstats.pytorch
dist tensor(1.5708) <class 'torch.Tensor'> torch.float64
```

Use `torch_ga` plus `torch.func`/`functorch` when the PyTorch lane is meant to test differentiable geometric algebra rather than merely repeat array math.

2026-06-08 Python risk recheck:

```text
FAIL dgl not installed
FAIL torch_scatter not installed
FAIL torch_sparse not installed
OK torch_geometric 2.7.0
OK torchdiffeq 0.2.5
OK torchode 1.0.1
OK xitorch 0.3.0
OK cvxpylayers 1.2.0
OK torch 2.11.0
```

Interpretation: use PyG core only where its current no-extension path is enough. Do not assume DGL or PyG optional extension packages exist on macOS ARM / torch 2.11 without a pinned wheel or container receipt. `torchdiffeq`, `torchode`, `xitorch`, and `cvxpylayers` are witness/candidate tools, not proof surfaces.
