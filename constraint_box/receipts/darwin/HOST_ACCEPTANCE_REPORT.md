# Host acceptance on darwin/arm64

Regenerated 2026-07-27 from the six receipts in this directory. The tier
receipt timestamps are:

| Receipt | `generated_at_utc` |
|---|---|
| `S1_ACCEPTANCE.json` | `2026-07-27T08:07:04.689907+00:00` |
| `S2_ACCEPTANCE.json` | `2026-07-27T08:07:16.301990+00:00` |
| `S3_ACCEPTANCE.json` | `2026-07-27T08:07:43.893094+00:00` |
| `S4_BOOT.json` | `2026-07-27T08:07:46.056680+00:00` |

All four came from a single regeneration pass. An earlier version of this report
described a 07:58-08:01 set that two writers had produced concurrently; in that
set `DENSITY_PARITY.json` was bound by its own `receipt_sha256` map to
`S1_ACCEPTANCE.json` and `S2_ACCEPTANCE.json` bytes that no longer existed on
disk. The whole set was regenerated in one quiet pass to fix that. The parity
receipt's `receipt_sha256` map now matches both files on disk.

`DENSITY_PARITY.json` and `MAJOR_RUN_PREFLIGHT.json` have no timestamp field
in their schemas. Nothing in this report is asserted independently of the six
receipts. The freshly computed file digests below are included only to
cross-check the receipt and manifest fields.

Host: macOS arm64, Python 3.13.6, interpreter
`/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.

No Julia. `grep -ril julia src config workers tests` returned no paths (exit 1).

`promotion_allowed: false` on every one of the six receipts. These are host
capability receipts, not promotion or scientific-admission evidence.

## Digests

Freshly computed with `shasum -a 256`:

| Object | sha256 |
|---|---|
| controller `src/constraintbox/estate.py` | `ff1fb8d1b9bbd5f52e034e0ad33a62000a50148944844d9032564baadb3256a7` |
| manifest `config/sim_estate_v2.json` | `90ccb6cc9504ce6efc74603f219b169df43656b4726b75eef2e2373abb15427c` |
| worker `workers/estate/capability_worker.py` | `355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257` |
| import blocker `workers/estate/import_blocker.py` | `b3e027e60eb963cd8bf143bad4c721b7fd2581508bb62a1d4a7a81970e2b6418` |
| fixture `fixtures/manifold/manifold_fixture_v1.json` | `bef31abdda024743467a0479de650ffd814764bbbab193709a04b9318c484bed` |

The controller digest on disk, the `controller_sha256` pin in the manifest,
and the `controller_sha256` recorded in `S1_ACCEPTANCE.json`,
`S2_ACCEPTANCE.json`, `S3_ACCEPTANCE.json`, and `S4_BOOT.json` are the same
value. That is four receipts, not six. `DENSITY_PARITY.json` and
`MAJOR_RUN_PREFLIGHT.json` have no `controller_sha256` key because that key is
not part of either schema; no controller-digest claim is made for them.

## Producing commands

There is no checked-in generator for this report. It was rewritten by hand
from the six regenerated receipts. With `PY` set to the interpreter above and
the working directory at `constraint_box/`, the producing commands were:

```
PYTHONPATH=src $PY -m constraintbox estate --pack-root . --manifest config/sim_estate_v2.json --fixture fixtures/manifold/manifold_fixture_v1.json --tier S1 --mode acceptance --python $PY --output receipts/darwin/S1_ACCEPTANCE.json
```

```
PYTHONPATH=src $PY -m constraintbox estate --pack-root . --manifest config/sim_estate_v2.json --fixture fixtures/manifold/manifold_fixture_v1.json --tier S2 --mode acceptance --python $PY --output receipts/darwin/S2_ACCEPTANCE.json
```

```
PYTHONPATH=src $PY -m constraintbox estate --pack-root . --manifest config/sim_estate_v2.json --fixture fixtures/manifold/manifold_fixture_v1.json --tier S3 --mode acceptance --python $PY --output receipts/darwin/S3_ACCEPTANCE.json
```

```
PYTHONPATH=src $PY -m constraintbox estate --pack-root . --manifest config/sim_estate_v2.json --fixture fixtures/manifold/manifold_fixture_v1.json --tier S4 --mode boot --python $PY --output receipts/darwin/S4_BOOT.json
```

```
PYTHONPATH=src $PY -m constraintbox estate-parity receipts/darwin/S1_ACCEPTANCE.json receipts/darwin/S2_ACCEPTANCE.json --tolerance 1e-08 --output receipts/darwin/DENSITY_PARITY.json
```

```
PYTHONPATH=src $PY -m constraintbox preflight receipts/darwin/S1_ACCEPTANCE.json receipts/darwin/S2_ACCEPTANCE.json receipts/darwin/S3_ACCEPTANCE.json --require-tier S1 --require-tier S2 --require-tier S3 --max-age-hours 24 --output receipts/darwin/MAJOR_RUN_PREFLIGHT.json
```

None used `--enforce`; all six commands exited 0. Exit 0 records command
completion, while the receipt state carries the verdict.

## Receipt states

| Receipt | State or disposition | Receipt reason |
|---|---|---|
| S1 | **DRIFT** | Environment is behind its Linux lock; required `numpy_density`, `scipy_channel`, and `z3_finite` are unready because installed versions differ from the tested lock. |
| S2 | **DRIFT** | Environment is behind its Linux lock; required `jax_density` and `cotengra_path` have version drift. |
| S3 | **DRIFT** | Environment is behind its Linux lock. All required S3 capabilities are READY, so preflight records an empty `required_unready` value. |
| S4 | **FAILED** | `nvidia_smi` is absent; both CUDA parity positive witnesses failed, and neither required GPU capability set was satisfied. |
| Density parity | **FAILED** | `sources` is `["quimb_tensor"]` and `independent_families` is `{jax: false, numpy: false, quimb: true, torch: false}`. One density family is READY, so there is nothing to compare against and `comparisons` is empty. |
| Major-run preflight | **PARKED** | S1, S2, and S3 are all not READY; the exact unready required capabilities are recorded above. |

The three acceptance tiers remain DRIFT, S4 remains FAILED, and preflight remains
PARKED. Nothing improved or worsened at tier level.

`quimb_tensor` is intermittent on this host, and that matters because density
parity depends on it. It came back `FAILED` with `positive_witness_failed` at
08:01 UTC, its retained stderr reporting a Numba cache locator error while
importing `quimb/core.py`, and `READY` with `all_required_controls_passed` at
08:07 UTC with no change to any input. Both outcomes were observed within one
session. `PROVENANCE.md` already carried a row noting an earlier `quimb_tensor`
failure that did not reproduce; this is the second occurrence. The density parity
receipt is therefore not stable run to run: on the failing run it has no sources
at all, and on this run it has one. Its `FAILED` state is the same either way,
but for different reasons, so do not read the parity state as a stable fact about
this host.

Across S1-S3, the environment reports 31 locked distributions missing from
this host (S1: 4, S2: 11, S3: 16). The receipts do not justify changing locks
or installing packages in this acceptance run.

## Capability controls and pin guard

The string `controller_source_digest_mismatch` is absent from every
per-capability evidence object in all four tier receipts. Controls are
populated for every capability that reached an implemented executable oracle:
5 of 6 S1 capabilities, 4 of 4 S2, 4 of 6 S3, and 2 of 4 S4. The five empty rows
are `tla_controller` (UNAVAILABLE), `pykoopman_rate` and `dimod_anneal`
(UNTESTED), `nvidia_device` (UNAVAILABLE) and `cuquantum_tensor` (UNTESTED) —
unavailable or unimplemented capabilities, not a controller-digest short circuit.

Twenty capabilities appear once each: 7 READY, 6 DRIFT, 2 UNAVAILABLE,
3 UNTESTED, 2 FAILED. Five of them record `controls_not_measured`:
`stdlib_finite` `["severance"]`, and `z3_finite`, `cvc5_finite`,
`cotengra_path` and `pymdp_fep` each `["mutation"]`. Three of those four mutation
cases are `required: true` — `z3_finite`, `cotengra_path`, `pymdp_fep`. The
receipts say so; the tier state and the CLI exit code do not. That open defect is
unchanged by this round.

`tests/test_pins_current.py` now independently guards these three manifest
pins:

- `controller_sha256`
- `import_blocker_sha256`
- `worker_sha256`

The test resolves the box root relative to its own file and does not require a
Git checkout. `workers/estate/operation_poisoner.py` is not pinned and
therefore is not guarded by this test.
