# Allowlist And Denylist

## Absolute denylist

Never touch:
- `.git/`
- `config/`, `requirements/`, and `light_runtime/`
- `zip_agent/src/`
- `integrated_system/bin/`, `scripts/`, `skills/`, `mmms/`, `context/`, and
  `runtime_profiles/`
- `hooks/`, `fixtures/`, and `experiments/`
- `archive/` as a source path
- `Archive/` as a source path

## First-wave allowlist

### `integrated_system/runs/`

Allowed only for:
- bounded archive moves
- exact enumerated families
- prep-supported moves

### `receipts/generated/`

Allowed only for:
- archive or quarantine moves
- explicit superseded job artifact pairs
- `tmp__*` staging residues
- older context packs only when clearly superseded

### `RUNS/`

Allowed only for:
- quarantine moves
- one explicit lane

## Protected run files

Never move:
- `_CURRENT_STATE`
- `CURRENT.json`
- `_RUNS_REGISTRY.jsonl`

## Freshness blocker

Default recent safety window:
- `72 hours`
