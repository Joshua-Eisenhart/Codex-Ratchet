# RUN_AND_WORK_BLOAT_MAP__2026_03_10__v1

Status: DRAFT / NONCANON / A2 AUDIT OUTPUT
Date: 2026-03-10
Role: bounded size and concentration map for the system-shape and bloat audit lane

## 1) Top-level local size map

- `system_v3/runs`: `557M`
- `work`: `437M`
- `system_v3/a2_high_entropy_intake_surface`: `16M`
- `system_v3/a2_state`: `1.5M`

Immediate counts:
- `system_v3/runs` immediate run dirs: `130`
- `work` immediate subdirs: `21`

Read:
- local bloat is concentrated almost entirely in `runs/` and `work/`

## 2) `system_v3/runs` concentration

Largest visible entries:
- `17M` `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0015`
- `16M` `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0016`
- `15M` `_RUNS_REGISTRY.jsonl`
- `15M` `RUN_DUAL_THREAD_NO_PRO_SMOKE_0004`
- `13M` `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0006`

Then a long tail of `6M`-`9M` run dirs, heavily dominated by:
- `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_*`
- related `RUN_GRAVEYARD_VALIDITY_ENTROPY_*` families

Operational read:
- the run burden is not one giant pathological directory
- it is many medium-size legacy/heavy evidence runs plus one large registry file
- repeated graveyard-validity / entropy-bridge families are the main concentration class

## 3) `work/` concentration

Largest entries:
- `136M` `work/system_v3`
- `117M` `work/to_send_to_pro`
- `59M` `work/audit_tmp`
- `45M` `work/out`
- `42M` `work/a1_sandbox`
- `24M` `work/zip_dropins`

Mid-tier:
- `3.1M` `work/curated_zips`
- `2.6M` `work/extracts`
- `1.8M` `work/zip_job_templates`
- `136K` `work/zip_subagents`

Operational read:
- `work/` bloat is mostly staging, mirrored system fragments, generated outputs, and sandbox spillover
- the active ZIP authoring surfaces are comparatively small

## 4) Main bloat classes

### Class 1: runtime evidence concentration
- `system_v3/runs`
- specifically legacy/heavier run families and registry accumulation

### Class 2: external-send and staging spillover
- `work/to_send_to_pro`
- `work/audit_tmp`
- `work/out`

### Class 3: mirrored/prototype system fragments
- `work/system_v3`

### Class 4: sandbox / exploratory residue
- `work/a1_sandbox`

## 5) Bloat-map conclusions

- local size pressure is real but structurally mixed
- the biggest cleanup opportunity is not `a2_state/` or intake docs
- the biggest opportunities are:
  - classify and thin/rotate old run evidence carefully
  - classify staging/output mirrors under `work/`
  - distinguish active ZIP surfaces from old send/build residue
