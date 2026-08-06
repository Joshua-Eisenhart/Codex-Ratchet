# Running the three-engine attractor-basin validation

## The boundary

| Part | Product role | Included in the ZIP | Installed by CB core install |
|---|---|---:|---:|
| CPython controller, typed intake, Z3, CVC5, CPython finite enumeration, SymPy, Rustworkx, Mini-Lev | ConstraintBox core/gate machinery | Yes | Yes |
| Basin controller and worker source, object card, external environment declarations | Inspectable opt-in validation adapter | Yes | No engine runtime is installed automatically |
| JAX/Diffrax | External simulation engine | Source adapter only | No |
| Julia/Attractors/DynamicalSystems | External simulation engine | Source adapter and observed Project/Manifest only | No |
| PyTorch/PyG | External simulation engine | Source adapter only | No |
| Run receipts and semantic ledgers | Per-run evidence | No | No |

The SMT subprocess is a CB-owned finite obligation checker over a typed bundle.
It is not a fourth simulation engine. JAX, Julia, and PyTorch are external even
when CB launches them.

## 1. Install the contained CB core

From the extracted `constraint_box` directory, select any CPython satisfying
`>=3.11,<3.14` and create a core environment:

```bash
python3.13 -m venv .venv-cb-core
.venv-cb-core/bin/python -m pip install --upgrade pip
.venv-cb-core/bin/python -m pip install .
.venv-cb-core/bin/constraintbox runtime verify --profile core-py313
```

Use `core-py311` or `core-py312` when that is the selected interpreter. The
runtime verifier checks the interpreter actually invoking it. It never swaps
in a laptop-specific alias.

## 2. Create the external Python worker environment

The exact versions observed on the retained macOS arm64 run are declared in
`requirements/attractor_basin_external_observed_20260801.txt`:

```bash
python3.13 -m venv .venv-basin-workers
.venv-basin-workers/bin/python -m pip install --upgrade pip
.venv-basin-workers/bin/python -m pip install \
  -r requirements/attractor_basin_external_observed_20260801.txt
```

Those pins are an observed profile, not a universal mandate. A different
version set is allowed to run. The controller records the actual versions and
executable identities, and it blocks if the required APIs, results, controls,
or replay do not work. An import alone never passes the profile.

NumPy and SciPy are explicit external Python dependencies here. They are not
CB formal authorities and are not added to the core dependency set.

## 3. Instantiate the external Julia environment

The included Project and Manifest are the exact environment inputs used by the
retained run:

```bash
julia --startup-file=no \
  --project=workers/attractor_basin_v1/julia_environment \
  -e 'using Pkg; Pkg.instantiate()'
```

The retained run used Julia 1.12.6, Attractors 1.37.0, and
DynamicalSystemsBase 3.18.1. A fresh install has not been verified by the ZIP
build itself; the real worker run is the qualifying check.

## 4. Run the challenge

Choose a new output directory. The controller refuses to overwrite an
existing run:

```bash
.venv-cb-core/bin/python \
  workers/attractor_basin_v1/basin_controller.py \
  --constraintbox-root . \
  --worker-python-runtime .venv-basin-workers/bin/python \
  --julia-runtime "$(command -v julia)" \
  --julia-project workers/attractor_basin_v1/julia_environment \
  --worker-root workers/attractor_basin_v1 \
  --output-dir /absolute/new/path/cb-basin-run-001
```

The controller and worker Python interpreters are separate inputs. The final
envelope records both identities and whether they resolve to the same binary.
This avoids treating a resolved venv symlink as the worker invocation path and
does not force CB core onto one host alias.

## What a successful run actually does

1. Runs JAX/Diffrax twice with x64 `jit`, `vmap`, Jacobian, gradient, and ODE
   operations.
2. Runs Julia twice with real `DeterministicIteratedMap`, `reinit!`, `step!`,
   `current_state`, `StateSpaceSet`, `AttractorsViaProximity`, and
   `basins_of_attraction` operations.
3. Runs PyTorch/PyG twice with `torch.func`, eigenspectrum, graph propagation,
   loss, optimizer, and bounded trainable diagnostics.
4. Requires path-independent semantic replay and the finite partition
   `165 negative / 11 boundary / 165 positive` from all three lanes.
5. Builds a strict controller-owned observation bundle. The SMT checker never
   opens raw engine receipts.
6. Requires Z3 and CVC5 SAT on the positive finite obligations, UNSAT cores for
   contradictory, erased, and wrong-stability controls, and agreement with an
   explicit CPython 31-by-11 enumeration.
7. Calls CB's real SymPy polynomial, Rustworkx prerequisite-DAG, and typed
   CB/sim-boundary profiles through their retained formal Mini-Lev flows.
8. Requires cycle, skipped-prerequisite, role-conflation, mutated-count,
   erased-label, wrong-provenance, missing-lane, a real Diffrax operation
   poison, and a retained SMT-missing Mini-Lev flow to be caught.
9. Retains and verifies an outer two-node Mini-Lev semantic ledger.

The final `controller_envelope.json` always keeps
`promotion_allowed=false`, `continuous_basin_proof=false`,
`formal_admission_allowed=false`, `scientific_admission_allowed=false`,
`whole_sim_estate_integrated=false`, and
`claim_gate_sim_admission=false` for this profile.

Verify an existing retained envelope without rerunning the engines:

```bash
.venv-cb-core/bin/python scripts/verify_attractor_basin_envelope.py \
  --envelope /absolute/path/cb-basin-run-001/controller_envelope.json \
  --receipt /absolute/new/path/cb-basin-run-001-verification.json
```

This checks the canonical envelope hash, referenced source/receipt/ledger
digests, both replay pairs, formal dispositions, solver verdicts and UNSAT-core
presence, hostile-control catches, the core/sim boundary, and all false claim
ceilings. It also reloads the retained controller source and re-runs its strict
normalizers against every raw engine/SMT receipt, binding the normalized rows
to the current worker-source hashes. It does not rerun an engine and therefore
cannot replace a fresh controller run or provide an unforgeable OS execution
trace.
