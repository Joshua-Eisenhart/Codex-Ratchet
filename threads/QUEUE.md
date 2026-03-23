# Thread Job Queue

> Jobs are YAML files in `threads/jobs/`. Each GPT Pro thread picks one.
> Results go to `threads/results/JOB_<id>/`.
> After processing into the refinery, results can be cleaned up.

## Active Jobs

| Job ID | Type | Status | Scope | Assigned To |
|--------|------|--------|-------|-------------|
| JOB_001 | DEEP_READ | OPEN | v3 specs 35-79 (A1 process specs) | — |
| JOB_002 | DEEP_READ | OPEN | v3 specs 40-66 (parallel codex, auto-go-on) | — |
| JOB_003 | AUDIT | OPEN | A2 persistent brain vs current state | — |
| JOB_004 | CROSS_VALIDATE | OPEN | v3 system understanding vs v4 system spec | — |
| JOB_005 | DISTILL | OPEN | core_docs/ thread extracts (compress) | — |
| JOB_006 | WIGGLE | OPEN | A1 as packet generator (steelman vs prose) | — |
| JOB_007 | PROBE | OPEN | Graph density analysis + community detection | — |
| JOB_008 | BRIDGE | OPEN | Map v3 tools to v4 skills (215 tools) | — |
| JOB_009 | AUDIT | OPEN | Graveyard health: 378 entries, rescue paths | — |
| JOB_010 | DEEP_READ | OPEN | Lev-os upstream .claude/ hooks + .lev/ config | — |
| JOB_011 | DISTILL | OPEN | GPT Pro architecture audit → actionable steps | — |
| JOB_012 | PROBE | OPEN | SIM evidence coverage: 68 evidenced of 401 | — |

## Status Legend
- `OPEN` — Available for pickup
- `CLAIMED` — Thread is working on it
- `COMPLETE` — Results deposited
- `PROCESSED` — Results ingested into refinery
- `ARCHIVED` — Job cleaned up
