# Operations Runbook v1
Status: ACTIVE
Date: 2026-02-24

## 1) Validate Structure Before Running
```bash
python3 system_v3/tools/sprawl_guard.py
python3 system_v3/tools/archive_guard.py
```
Expected: both return `"status": "PASS"`.

Optional storage janitor audit (dry-run):
```bash
python3 system_v3/tools/storage_janitor.py
```

Apply storage janitor cleanup + bookkeeping log:
```bash
python3 system_v3/tools/storage_janitor.py --apply --write-bookkeeping-log
```

## 2) Run One Deterministic Cycle
From `system_v3/runtime/bootpack_b_kernel_v1/`:
```bash
python3 a1_a0_b_sim_runner.py --a1-source packet --run-id RUN_EXAMPLE_0001 --steps 1 --clean
```

## 3) Inspect Run Outputs
Canonical location:
- `system_v3/runs/RUN_EXAMPLE_0001/`

Minimum files to check:
- `system_v3/runs/RUN_EXAMPLE_0001/state.json`
- `system_v3/runs/RUN_EXAMPLE_0001/summary.json`
- `system_v3/runs/RUN_EXAMPLE_0001/events.jsonl`
- `system_v3/runs/RUN_EXAMPLE_0001/zip_packets/`

## 4) Build Save ZIPs
Bootstrap:
```bash
python3 system_v3/tools/build_save_profile_zip.py \
  --profile bootstrap \
  --repo-root .
```

Debug (selected run):
```bash
python3 system_v3/tools/build_save_profile_zip.py \
  --profile debug \
  --repo-root . \
  --include-run-id RUN_EXAMPLE_0001
```

## 5) Archive Policy
- Use `archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/` for short-term noisy bundles.
- Use `archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/` for milestone artifacts.
- Use `archive/LEGACY_REFERENCE__READ_ONLY/` for legacy docs/packs.

## 6) Do Not Do
- Do not write live run state under `system_v3/runtime/`.
- Do not treat `archive/` as runtime input.
- Do not store canonical replay artifacts outside `system_v3/runs/`.
