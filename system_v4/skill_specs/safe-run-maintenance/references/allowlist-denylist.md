# Allowlist And Denylist

## Absolute denylist

Never touch:
- `system_v3/specs/`
- `system_v3/a1_state/`
- `system_v3/a2_state/`
- `system_v3/tools/`
- `system_v3/runtime/`
- `system_v3/control_plane_bundle_work/`
- `core_docs/`
- `.git/`
- `work/zip_job_templates/`
- `work/zip_subagents/`
- `work/zip_dropins/`
- `work/curated_zips/`
- `work/INBOX/`
- `archive/` as a source path

## First-wave allowlist

### `system_v3/runs/`

Allowed only for:
- bounded archive moves
- exact enumerated families
- prep-supported moves

### `work/to_send_to_pro/`

Allowed only for:
- archive or quarantine moves
- explicit superseded job artifact pairs
- `tmp__*` staging residues
- older context packs only when clearly superseded

### `work/system_v3/`

Allowed only for:
- quarantine moves
- one explicit lane

## Protected run files

Never move:
- `_CURRENT_STATE`
- `_CURRENT_RUN.txt`
- `_RUNS_REGISTRY.jsonl`

## Freshness blocker

Default recent safety window:
- `72 hours`

