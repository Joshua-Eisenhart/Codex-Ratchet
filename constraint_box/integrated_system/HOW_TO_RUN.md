# How to run the integrated system

## Requirements

- macOS with Python 3.13 for the current tested Light lock;
- network access for a first JAX/QIT profile install, or an existing exact-lock
  runtime that can pass explicit adoption;
- no provider credential is required for the deterministic verification path.

The current checked JAX capability profile is `>=0.10.0,<0.11.0`. A later
series is held until its exact/JAX controls are rerun and the profile changes.

The ZIP deliberately contains no virtual environment. Installed packages are
machine-specific and would make the artifact large and untrustworthy. The
included lock and bootstrap command create the environment after extraction.
It also retains a separate small build-only interpreter so later wheel audits
never depend on ambient user-site packages. That interpreter is not Light and
is not a JAX or Heavy execution route.

## Fresh extraction

```text
unzip ConstraintBox_Integrated_<date>.zip -d ConstraintBox_Integrated
cd ConstraintBox_Integrated
```

Create Light with the included lock (network access is required):

```text
python3 bin/cb bootstrap-light
```

Install the included JAX/QIT profile (outside Light):

```text
python3 bin/cb jax-profile plan
python3 bin/cb jax-profile install
export CB_LIGHT_PYTHON="$PWD/PROJECT/constraint_box/.venv/bin/python"
export CB_JAX_QIT_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/jax-qit-stack"
```

To reuse a pre-existing clean runtime, explicitly adopt it. Adoption checks all
112 exact lock pins and runs the 12-operation API probe before writing an
attestation:

```text
python3 bin/cb jax-profile probe --adopt-existing \
  --target /absolute/path/to/jax-qit-stack
```

Then run:

```text
python3 bin/cb doctor
python3 bin/cb context
python3 bin/cb light-seed
python3 bin/cb verify --output runs/VERIFY.json
```

`doctor` must show that Light cannot import JAX, the declared JAX interpreter
can, and its manifest is bound to the lock shipped in this extraction.

## Run the current finite operations

Structured `open/bind` operation:

```text
python3 bin/cb structured-probe --engine exact --output runs/structured-exact.json
python3 bin/cb structured-probe --engine dual --output runs/structured-dual.json
```

Light/JAX/wave crossing:

```text
python3 bin/cb jax-wave --output-dir runs/light-jax-wave
```

Bounded Mini-Lev path-mass probe and exact replay:

```text
python3 bin/cb path-mass --require-jax --output runs/path-mass.json
python3 bin/cb path-mass --require-jax --output runs/path-mass-replay.json \
  --replay runs/path-mass.json
```

This operation measures a finite policy snapshot. It does not call its
components basins or turn the retrieval comparisons into memory claims.

ZIP Agent:

```text
python3 bin/cb zip --help
```

Contained model-free waves:

```text
python3 bin/cb wave list
python3 bin/cb wave inspect cb-maintenance-wave
python3 bin/cb wave run cb-maintenance-wave
python3 bin/cb wave run cb-context-strategy-wave
python3 bin/cb wave run cb-exploration-wave
```

Only those three are currently runnable. Failure, repair, strategy, Goodhart,
object-loop, and management names remain inactive specs until their complete
contained execution graphs run and emit verified receipts.

The package's verifier builds and verifies a bounded demonstration ZIP rather
than asking a model to claim that ZIP execution worked.

## Rebuild the release ZIP

From a source checkout:

```text
python3 constraint_box/integrated_system/bin/cb bundle \
  --output /absolute/path/to/ConstraintBox_Integrated.zip
```

The builder creates a deterministic file manifest and SHA-256 registry. It
excludes environments, caches, credentials, bulk receipts, and temporary
campaign rows.

## Reading project context

Start with:

1. `context/current/OWNER_OBJECT.md`
2. `context/current/PRODUCT_CONTRACT.md`
3. `context/current/WORK_ASSESSMENT.md`
4. `context/current/CURRENT_PLAN.md`
5. `context/current/FAILURE_MEMORY.md`
6. `context/current/OPEN_HYPOTHESES.md`

Use `context/full/prompt_plan_progress_corpus.jsonl` when a compact projection
does not contain the needed owner prompt, failure, or decision. The corpus is
append-only evidence; it is not a single canonical narrative.

## Failure meanings

- `REFUSE_*`: the request is invalid or violates a fixed boundary; no operation
  result should be written.
- `HOLD_*`: required current evidence or capability is missing; retry only after
  the named condition changes.
- `PASS` or a bounded SAT disposition: the named local operation completed.
  It does not imply promotion or scientific truth.
