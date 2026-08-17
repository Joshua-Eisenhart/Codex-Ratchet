---
name: zip-agent
description: Use when creating, validating, running, nesting, or verifying a ConstraintBox ZIP_JOB packet or deterministic return ZIP.
---

# ConstraintBox ZIP Agent

The ZIP is the work process. A chat message or loose file is not a ZIP_JOB result.

## 1. Build or receive the packet

Require `ZIP_JOB_MANIFEST.json`, `00_RUN_ME_FIRST.md`, ordered
`tasks/*.task.json`, all task inputs, and an exact SHA-256 registry. Every task
declares operation, inputs, outputs, dependencies, and optional preload files.

Validation:

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent validate JOB.zip
```

Expected: `ZIP_JOB_VALIDATED_LOCAL`. Any refusal stops before output.

## 2. Execute only through the ZIP runtime

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent run JOB.zip \
  --return-zip RETURN.zip --cache-dir /tmp/cb-zip-cache
```

Validation: command exits zero, `RETURN.zip` exists, and the JSON disposition is
`ZIP_JOB_EXECUTED_LOCAL`. A failure must leave `RETURN.zip` absent.

## 3. Verify the return binding

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent verify-return \
  RETURN.zip --input JOB.zip
```

Validation: `ZIP_RETURN_INTEGRITY_BOUND`. This is integrity and execution-shape
evidence only; it is not semantic replay, admission, or release.

## 4. Nest children through CB

A parent may use `run_child_zip_v1` only when the child job ID is in
`allowed_child_job_ids` and the root depth bound is not exceeded. The child ZIP
is an input member and the child return ZIP is an output member. A task never
privately starts a child.

Validation: the parent return contains the child return ZIP and both return
manifests verify independently.

## 5. Keep model work held until a connector exists

Mini-MMM files may be packet members and must be hashed. The current prototype
returns `HOLD_MODEL_CONNECTOR_UNBOUND` for any task with preload files. Do not
replace that HOLD with local prose or claim the model-backed task ran.

Validation: no return ZIP is written for the held task.

## Rationalization guard

| Shortcut | Why it is false |
|---|---|
| "The task file exists, so it ran." | Only a verified return task receipt shows execution. |
| "The worker answered in chat." | The return ZIP is the result. |
| "The child was requested, so it spawned." | The parent return must retain the child return. |
| "Required outputs exist." | Each output must be owned by one task and hash-bound. |
| "The cache has it, so it is admitted." | Cache/index is retrieval only. |

Claim ceiling: local deterministic ZIP execution only; no model execution,
host enforcement, admission, promotion, or release.
