---
name: cb-maintenance-wave
description: Run a cautious, independently callable ConstraintBox maintenance and system-management wave before a campaign loop. Diagnose repository, ZIP-agent package, append-only ledger, probe map, hooks, and provider receipts; freeze source/context digests; classify exact candidates without deleting, moving, rewriting, committing, or pushing; emit a receipt and blockers. Use when booting CB, before failure/repair/strategy waves, or when checking whether the workspace is safe and current.
---

# CB Maintenance Wave

Run this wave as step zero of a CB campaign. It is a bounded diagnostic and
classification operation, not a cleanup command. It may propose a move for an
exact allowlisted generated artifact, but it never performs a move or delete.

## Contract

1. Bind one explicit repository root and package root.
2. Inspect only the declared source, context, ledger, map, hook, provider, and
   candidate paths. Do not discover a broad tree and infer what is disposable.
3. Freeze a digest of the declared source paths and a separate digest of the
   declared context paths before any downstream wave.
4. Diagnose path presence, digests, git status, ledger head, map state, hook
   state, and provider-receipt state. Missing evidence is recorded; it is not
   silently filled with prose.
5. Classify every candidate exactly as `KEEP_ACTIVE`, `MOVE_TO_ARCHIVE`,
   `MOVE_TO_QUARANTINE`, or `BLOCKED_REQUIRES_PREP`.
6. Treat `delete`, broad moves, archive-as-source, fresh owner files,
   ambiguous owner files, protected run files, and missing required receipts as
   refusals or blockers.
7. Emit one `constraintbox.maintenance-receipt.v1` receipt. Set
   `mutation_performed: false` and `writes_allowed: false` in every run.
8. Stop. Do not silently chain cleanup, failure, repair, strategy, sync,
   commit, push, or promotion.

## Required execution

Use the deterministic runner:

```bash
python3 "$CB_SKILLS_ROOT/cb-maintenance-wave/scripts/run_maintenance_wave.py" \
  --root "$CB_BOX_ROOT" \
  --package "$CB_BOX_ROOT/zip_agent" \
  --source-path zip_agent/src \
  --source-path zip_agent/scripts \
  --context-path zip_agent/project_state \
  --context-path zip_agent/context \
  --ledger-path zip_agent/project_state/events.jsonl \
  --map-path /exact/path/to/current-map-return.zip \
  --hook-path /exact/path/to/hook-receipt.json \
  --provider-receipt /exact/path/to/provider-call-receipt.json \
  --candidate /exact/path/to/candidate \
  --output /exact/path/to/maintenance.receipt.json
```

Use `--required-receipt` for any receipt that is required by the invocation
contract. A missing required receipt produces `HOLD` and
`REFUSE_MISSING_RECEIPT`. Use `--requested-action delete` only to test the
refusal; never reinterpret it as permission.

Validate the result before admitting a campaign child:

```bash
python3 "$CB_SKILLS_ROOT/cb-maintenance-wave/scripts/validate_receipt.py" \
  /exact/path/to/maintenance.receipt.json
```

## Safety boundary

The packaged allowlist/denylist and 72-hour freshness rule are in
`$CB_SKILLS_ROOT/safe-run-maintenance/references/` and
must be consulted when changing this wave. Never use `archive/` as a source.
Never touch active specs, runtime, tools, A1/A2 state, control-plane work,
owner surfaces, inboxes, or protected run registry files as an inferred cleanup
operation. A candidate outside the explicit allowlist is kept or blocked; it
is not moved because it looks old, large, or generated.

## State and claim ceiling

The receipt is evidence of one bounded diagnostic/classification pass only. It
does not prove that hooks fired, providers ran, MMMs were read, a map is
semantically useful, or cleanup is safe. It does prove the exact paths and
bytes hashed by this pass, the observed git/ledger/path state, candidate
decisions, and that this runner performed no mutation.

Do not count this wave as a failure, repair, strategy, probe, or model council
wave. Those are separate child receipts. A parent campaign must reject a
missing, stale, invalid, or mutation-bearing maintenance receipt before it
starts `cb-failure-wave`.

## Cancellation and blockers

Cancellation, missing roots, source/context drift during the run, invalid
required receipts, destructive action requests, and ambiguous owner files are
non-success terminal states. Preserve the receipt and blockers. Do not retry
with a broader path set in the same invocation.
