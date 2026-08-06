# Installation, boot, and maintenance

## Process rule

Use one heavy runtime at a time:

```text
input artifact -> runtime boots -> bounded task -> receipt written atomically
               -> runtime exits -> next runtime boots
```

This avoids memory-lifetime coupling and makes every handoff inspectable.
Shared-memory acceleration can be tested later as an optional optimization;
it is not the default evidence path.

## Dependency policy

1. Candidate requirements live in `requirements/candidates/`.
2. A tested environment is frozen into `requirements/locks/`.
3. `scripts/finalize_sim_registry.py` binds each lock and each controller
   source by digest.
4. A boot checks the exact selected interpreter. Virtual-environment Python
   paths are never resolved through their symlink to the base interpreter.
5. Version drift produces `DRIFT`, not an automatic upgrade.
6. Updating is an explicit maintenance operation: build a new environment,
   run acceptance, compare receipts, then replace the lock intentionally.

“Use current versions” therefore means routinely test current candidates; it
does not mean silently install the newest release before a major run.

## Suggested environment build

```bash
python3.12 -m venv .estates/S1
.estates/S1/bin/pip install -r requirements/locks/e0-py312-linux.lock

python3.12 -m venv .estates/S2
.estates/S2/bin/pip install -r requirements/locks/e1-py312-linux.lock

python3.12 -m venv .estates/S3
.estates/S3/bin/pip install -r requirements/locks/e2-py312-linux.lock
```

Do not merge the three environments merely because all packages can coexist.
Isolation is part of the acceptance contract.

## Check cadence

| Event | Check |
|---|---|
| every process boot | controller/worker hashes, interpreter identity, required import, bounded positive fixture |
| before a major run | acceptance-mode receipts for all required tiers; freshness check |
| after a dependency change | positive, mutation, replay, severance, version and environment-lock checks |
| after controller policy change | full unit suite, TLA+ lifecycle model, hostile fixtures |
| before cloud dispatch | local CPU golden fixture, serialized input digest, declared device route |
| after cloud completion | device receipt, output digest, CPU/GPU parity, cost and runtime |
| scheduled maintenance | build fresh candidate environments; never update the active lock in place |

## Acceptance versus boot

`boot` is a quick positive integration check. `acceptance` adds mutation,
replay, and dependency severance. Major science runs should require fresh
acceptance receipts for the exact tiers and capabilities they use.

## Applicability

Tools run only when the controller-owned registry says their capability is
required for a claim type. A qualitative structure claim should not pay the
cost of JAX or PySINDy. A dynamics-law claim cannot invoke PySINDy unless its
candidate library was declared before the fit. An engine-cycle claim requiring
Julia remains parked when Julia is unavailable.

## Failure behavior

- `UNKNOWN`, timeout, missing output, malformed output, non-finite values,
  missing dependency, stale receipt, or source drift do not pass.
- Optional absence may yield `DEGRADED`.
- Required absence yields `UNAVAILABLE`.
- A failed control yields `FAILED`.
- A missing acceptance implementation yields `UNTESTED`.
