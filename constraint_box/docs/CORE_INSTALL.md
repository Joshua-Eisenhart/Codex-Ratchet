# ConstraintBox core install

ConstraintBox core is a deterministic harness for untrusted user and LLM work.
This page covers installing and verifying the contained core only. Simulation
runtimes are installed separately; see [SIM_SETUP.md](SIM_SETUP.md).

## What the core ZIP contains

The contained-core ZIP ships source and the local resources its core smoke
surface needs: `src/` (including the contained provider/notary harness),
`config/`, `mmm/`, `fixtures/`, `formal/`, `workers/`, the local ClaimGate
chain, bounded adapter definitions, tests, requirements, docs, and the
deterministic builder, manifest, and isolated-extraction verifier.

It excludes CPython, installed or native dependencies, Node.js, Julia, the GPU
stack, credentials, remote provider backends, `external_sim_estate`, and the
surrounding Codex-Ratchet checkout. Provider adapters are source code, not a
credential or a live-provider claim. Adapter source may be present for
inspectability; it is not an installed engine runtime and is not part of the
contained-core smoke claim.

## Host requirements

You install these on the host; they are not inside the ZIP.

| Host component | Required by the contained verification |
|---|---|
| CPython 3.11, 3.12, or 3.13 | active portable core-profile verification |
| Z3, CVC5, SymPy, Rustworkx, Maude | deterministic SMT, exact-expression, Mini-Lev graph, and bounded rewrite gates |
| Node.js | in-box ClaimGate checker |
| Java plus TLC/Apalache JARs | only to run the separately configured temporal pair; not required for the contained-core smoke proof |
| Writable absolute CB runtime directory | only for a Mini-Lev LLM proposal run; stores local notary keys under an explicit `CONSTRAINTBOX_RUNTIME_DIR` |

The verifier uses the interpreter that invoked it. It never selects another
interpreter, installs a dependency, or accepts a base-Python fallback. A
missing or incompatible core library returns `PARKED` or `BLOCKED`.

## Build and verify a bundle

From `constraint_box/`:

```bash
python scripts/build_contained_core_bundle.py \
  --output /absolute/output/constraintbox-core.zip
python scripts/verify_contained_core_bundle.py \
  --bundle /absolute/output/constraintbox-core.zip \
  --receipt /absolute/output/contained-core-verification.json
```

The verifier checks archive membership and digests, extracts to a fresh
directory, then runs the declared core smoke surface: runtime verification,
demo, MMM/SMT, a fail-closed missing-assumptions request, typed SymPy,
Maude, and Rustworkx/Mini-Lev tasks, local repair/lease/foreign-observation
units, an absent-estate `PARKED` case, a typed `PARKED` temporal-runtime
absence check, two in-box ClaimGate fixtures, and the contained
provider/notary/local-subprocess Mini-Lev integration test.

To enable the temporal pair, place the hash-checked TLC and Apalache JARs in
one external directory and set `CONSTRAINTBOX_FORMAL_RUNTIME_DIR` to it. The
policy names only relative JAR locations; it contains no developer-machine
paths. `formal temporal` is `PARKED` until that runtime is explicitly present.

For the actual Mini-Lev proposal-provider boundary, set an absolute
`CONSTRAINTBOX_RUNTIME_DIR` before `constraintbox run`.  Missing configuration
parks rather than writing under a home directory.  See
[MINILEV_PROVIDER_RUNTIME.md](MINILEV_PROVIDER_RUNTIME.md).

The static proposal-provider registry defaults to the local tool route. An
operator can set `CONSTRAINTBOX_PROPOSAL_PROVIDER=openrouter` plus
`OPENROUTER_API_KEY`, or `CONSTRAINTBOX_PROPOSAL_PROVIDER=nvidia` plus
`NVIDIA_API_KEY`; the route fixes its model in CB source and is bound into the
receipt. Missing selected credentials park with no local fallback. Remote
adapters are source and offline-test coverage only—not included credentials,
installed provider software, live quota evidence, or a live-model claim.

## Separate external failure rehearsal

The core verifier intentionally does **not** run native sim-engine workloads.
When the separately installed SciPy profile is available, the source contains
one fixed failure-rehearsal instrument:

```bash
PYTHONPATH=src /declared/cpython -B \
  scripts/run_failure_rehearsal.py \
  --run-root /absolute/new/cb-scipy-failure-rehearsal
```

It has no capability, worker, operation, tolerance, request-ID, provider, or
retry arguments. CB first runs a real `scipy.linalg.expm` worker normally,
then source-owned code sends only the replay worker through the existing
operation-severance control. It retains the resulting `BLOCKED` receipt and
non-executing `repair_plan.json`, then performs the fixed unpoisoned
same-profile fresh rerun and independently replays its result. The combined
`failure_rehearsal_result.json` remains path-, source-, receipt-, and
ledger-bound.

This is deliberate test fuel: it proves that one real worker failure reaches
CB's deterministic planning and fresh-rerun machinery. It is not a natural
SciPy defect, broad engine readiness, automatic repair/tuning, release,
promotion, CR truth, or scientific claim.

## Ceiling

Every core verification receipt remains `promotion_allowed: false`. A passing
core verifier proves only the declared core installation boundary. It does not
install, validate, or contain the simulation estate.
