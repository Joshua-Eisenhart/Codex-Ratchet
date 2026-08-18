# Current ConstraintBox package

This branch contains the unified ConstraintBox product source. A release ZIP is
called current only after its fresh-extract verifier passes; branch cleanliness
is reported by Git and the maintenance receipt, not asserted by this file.

Do not work in the dirty `claimgate/bypass-regression` checkout.
Do not treat `~/.codex/skills` as a second source of truth.
Do not copy Archive, `/tmp`, or the 260-file dirty tree into this package.

## Live directory

`constraint_box/integrated_system/`

| Path | What it is |
|---|---|
| `00_READ_THIS_FIRST.md` | start here |
| `HOW_TO_RUN.md` | bootstrap, doctor, seed, JAX, verify, bundle |
| `SYSTEM_ARCHITECTURE.md` | Light, ZIP, hooks, waves, JAX |
| `WHAT_IS_PROVEN.md` | measured results and limits |
| `bin/cb` | one public command |
| `skills/` | contained wave definitions, dependencies, and runnable cohort |
| `mmms/primary/` | shipped wiki MMM reservoir |
| `runtime_profiles/jax_qit/` | project-neutral JAX/QIT lock, installer, and probes |
| `scripts/` | wave runner, verification, JAX crossing, and bundle builder |
| `runtime/zip_agent_src/` in a ZIP | stateless ZIP communication runtime |
| `context/` | owner object, plan, failures, corpus |
| `runs/` | generated local receipts; not source |

## Run

From this checkout:

```text
python3 constraint_box/integrated_system/bin/cb --light-python constraint_box/.venv/bin/python doctor
```

## Zip

```text
python3 constraint_box/integrated_system/bin/cb bundle --output /absolute/path/to/ConstraintBox_Integrated.zip
```

The ZIP root is `constraintbox-integrated-system-v1/`. Fresh extract uses `bin/cb`.

## Boundaries

- One system. Two interpreters. Light must not import JAX.
- Only the manifest's runnable wave cohort may execute. Extra global `cb-*`
  cells and spec-only waves stay out unless separately admitted.
- Promotion allowed: false.
