# Estate Installation and Boot

This is a candidate operating procedure. It separates environments so a cheap
ConstraintBox check never has to load the manifold or science-field runtimes.

## Candidate environment build

The `.in` files name direct candidates. The tested Linux resolutions are in
`requirements/locks/`. Build a new environment; never update the active one in
place.

```bash
uv venv /opt/constraintbox/e0 --python 3.12
uv pip install --python /opt/constraintbox/e0/bin/python \
  -r requirements/locks/e0-py312-linux.lock

uv venv /opt/constraintbox/e1 --python 3.12
uv pip install --python /opt/constraintbox/e1/bin/python \
  -r requirements/locks/e1-py312-linux.lock

uv venv /opt/constraintbox/e2 --python 3.12
uv pip install --python /opt/constraintbox/e2/bin/python \
  -r requirements/locks/e2-py312-linux.lock
```

The supplied locks record the environment actually tested for this pack. They
are not universal cross-platform locks. macOS, Linux/CUDA and other Python
minor versions need their own named lock and acceptance receipt.

## Cheap boot check

```bash
PYTHONPATH=runtime/src python3 -m constraintbox estate \
  --pack-root . \
  --manifest 04_SPEC/estate/estate_v1.json \
  --fixture 04_SPEC/estate/manifold_fixture_v1.json \
  --layer E0 \
  --mode boot \
  --python /opt/constraintbox/e0/bin/python \
  --enforce
```

`--enforce` exits nonzero on required `UNAVAILABLE`, `DRIFT`, or `FAILED`.
`DEGRADED` is allowed only when every required capability passed and an
explicit optional capability did not.

## Full pre-run acceptance

The suite boots one worker estate at a time. Heavy libraries remain in child
processes and exit before the next estate starts.

```bash
TLA2TOOLS_JAR=/opt/tla/tla2tools-1.7.4.jar \
PYTHONPATH=runtime/src python3 runtime/scripts/verify_estate.py \
  --pack-root . \
  --manifest 04_SPEC/estate/estate_v1.json \
  --fixture 04_SPEC/estate/manifold_fixture_v1.json \
  --output-dir run-evidence/estate \
  --mode acceptance \
  --layer-python E0=/opt/constraintbox/e0/bin/python \
  --layer-python E1=/opt/constraintbox/e1/bin/python \
  --layer-python E2=/opt/constraintbox/e2/bin/python
```

The acceptance mode adds:

- fixture mutation;
- deterministic replay;
- dependency severance;
- controller, worker, blocker, fixture and lock hashes;
- exact direct and transitive dependency-set comparison;
- NumPy/JAX/quimb density parity.

## TLA+ artifact

The pack does not redistribute `tla2tools.jar`. E0 accepts the stable 1.7.4
artifact only when `TLA2TOOLS_JAR` points to a file whose official release SHA-1
is `bee4a54f3ee3d4afc347c3240ec2d9e93b075104`. The receipt also records SHA-256.
TLC must pass the bounded controller model and fail the deliberately weakened
evidence invariant.

## Major-run gate

A major task should bind:

1. the suite index hash;
2. every participating layer receipt hash;
3. the exact fixture and scientific input hashes;
4. the environment lock hash;
5. any cross-estate parity receipt;
6. a declared claim ceiling.

No worker may select its own environment, fixture, tolerance, or readiness
state.
