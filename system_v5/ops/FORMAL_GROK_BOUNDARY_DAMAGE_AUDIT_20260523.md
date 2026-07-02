# Formal / grok_sim Boundary Damage Audit

Date: 2026-05-23

Status: damage audit, not recovery execution. No reverts, deletes, staging, commits, or sim repairs are performed by this document.

Supersession note: this is a historical damage snapshot. For current cleanup
state, use `EXPANDED_QUARANTINE_FULL_INVENTORY_20260523.json`,
`EXPANDED_QUARANTINE_SURFACE_CLASSIFICATION_20260523.md`, and
`EXPANDED_QUARANTINE_ACTION_MANIFEST_20260523.json`. Later cleanup restored
tracked canonical files and archived/removed the formal-scout quarantine,
legacy-intake, external-audit, top-level generated ops, and cache-noise buckets.

## Trigger

Owner correction: `system_v5/grok_sim/` was supposed to remain an informal side-quest sim project. It may read selected formal references, but it must not write canonical formal-scout docs, classifiers, results, or indexes. The formal project and grok side-quest project must remain separate until a deliberate reproduction / ingest path is opened.

## Intended Boundary

Evidence from repo-local grok_sim docs:

- `system_v5/grok_sim/SESSION_HANDOFF.md` declares:
  - `system_v5/ops/formal_scouts/` is the formal v5 sim project.
  - `system_v5/grok_sim/` is side-quest territory.
  - "DO NOT WRITE HERE" for formal_scouts.
  - Side-quest outputs stay `side_quest_only` / `promotion_allowed=false` until formal reproduction.
- `system_v5/grok_sim/HANDOFF_NESTED_BASIN_ARCHITECTURE_AND_TOOLING_BLOCK_20260520.md` declares:
  - "grok_sim writes to grok_sim/; formal_scouts reads grok_sim/; no writes from grok_sim/ into formal_scouts/"
  - "All paths are under system_v5/grok_sim/. ... No commits, no writes to formal_scouts/."
- `system_v5/grok_sim/SIDEQUEST_PLAN_terrain_lindblad_algebra_basin.md` declares:
  - read-only access to `system_v5/ops/formal_scouts/canonical_qit_engine_specs.py`
  - no writes to formal_scouts
  - no formal admission / no canonization

## Findings

### F1 - grok_sim itself does not show recent Git-visible canonical writes

Commands / observations:

- `git status --short -- system_v5/grok_sim` is empty.
- Recent `grok_sim` writes in the last day are limited to iter 220-223 outputs and `.DS_Store`; no recent tracked dirty source under `grok_sim`.
- Static scan of Python files under `system_v5/grok_sim/` found 6 references to formal paths and 0 write-context hits:
  - `iter_115_terrain_lindblad_composition_algebra_basin.py` references `canonical_qit_engine_specs.py` as read-only reconstruction source.
  - `iter_223_test_missed_derived_constraints.py` references Codex formal scouts as an audit target.
  - `loop_runner/proposed_formal_sims/...` files mention formal_scouts in comments or proposed-formal contexts.

Interpretation: the immediate write breach does not appear to be `grok_sim` scripts writing into formal_scouts. The stronger evidence points to canonical formal lanes absorbing or registering informal/advisory work without quarantine.

### F2 - canonical formal_scout surfaces are dirty and must be treated as contaminated pending triage

Current Git-visible dirty tracked surfaces:

```text
M system_v5/docs/FORMAL_SCOUT_READINESS_INDEX.md
M system_v5/docs/SIM_ESTATE_INTEGRATION_INDEX.md
M system_v5/evidence/formal_scout_readiness_index.json
M system_v5/evidence/sim_estate_integration_index.json
M system_v5/ops/formal_scouts/README.md
M system_v5/ops/formal_scouts/sim_source_aligned_stack_completion_gap_classifier_probe.py
M system_v5/ops/formal_scouts/sim_two_root_constraint_flux_recovery_runtime_tensor_bridge_classifier_probe.py
M system_v5/ops/formal_scouts/sim_two_root_constraint_tensor_scaling_status_classifier_probe.py
```

Untracked canonical/advisory surfaces:

- 23 untracked `system_v5/ops/formal_scouts/sim_*.py` files.
- 29 total untracked `system_v5/ops/...` files, including:
  - `system_v5/ops/CROSS_LANE_PHI0_KILL_CONVERGENCE_20260523.md`
  - `system_v5/ops/SOURCE_ALIGNED_STACK_CROSS_LANE_SYNTHESIS_20260523.md`
  - `system_v5/ops/external_audits/three_artifact_run_20260523/*.json`

Generated / ignored receipt surface:

- 61 result JSON files under `system_v5/ops/formal_scouts/results/` have mtimes after 2026-05-23 04:57.
- 28 result JSON files under that result surface have mtimes after 2026-05-23 05:19.
- These do not appear in `git status`, so Git cleanliness under-reports the actual receipt estate mutation.

Interpretation: the formal project has been advanced by a large wave of formal_scout source, generated result, docs, evidence, and external audit artifacts. Because the boundary was disputed and informal/advisory lanes were mixed into the reasoning chain, these surfaces are quarantine candidates until re-adjudicated.

### F3 - formal indexes were regenerated to include the suspect wave

Observed diff summary:

```text
system_v5/docs/FORMAL_SCOUT_READINESS_INDEX.md     |   22 +-
system_v5/docs/SIM_ESTATE_INTEGRATION_INDEX.md     |   22 +-
system_v5/evidence/formal_scout_readiness_index.json     | 1383 +++++++-
system_v5/evidence/sim_estate_integration_index.json     | 3292 +++++++++++++++++++-
```

The readiness / estate indices increased the indexed scout/result surface from 404 to 427 entries. This index movement canonically registers the suspect scout wave and is the highest-risk contamination mechanism because later agents will treat index inclusion as project state.

### F4 - external Grok audit receipts were stored under canonical ops, not under grok_sim

Untracked files:

```text
system_v5/ops/external_audits/three_artifact_run_20260523/grok_audit_a1.json
system_v5/ops/external_audits/three_artifact_run_20260523/grok_audit_a2.json
system_v5/ops/external_audits/three_artifact_run_20260523/grok_audit_a3.json
system_v5/ops/external_audits/three_artifact_run_20260523/grok_audit_a3v2.json
```

These may be useful advisory artifacts, but under the user-stated two-project separation they should not be treated as grok_sim formal evidence or silently integrated into canonical formal-scout conclusions. Their current placement under canonical `system_v5/ops/external_audits/` is at least a quarantine issue.

### F5 - contamination scope is epistemic as well as filesystem-level

Even where files are technically formal_scout files rather than grok_sim files, the formal chain used:

- Claude cold-context audits as route corrections,
- Grok external audit receipts,
- generated synthesis docs,
- repeated bounded section-connection stress probes,
- classifier wiring that propagated these into the top-level completion/gap classifier.

This breaks the intended separation because informal/advisory/project-management evidence became part of formal progression before a clean reproduction boundary was established.

## Quarantine Classification

| Surface | Status | Reason |
|---|---|---|
| `system_v5/grok_sim/` | hold, not necessarily dirty | No recent Git-visible canonical write evidence; remains informal side-quest evidence only. |
| 23 untracked `formal_scouts/sim_*.py` | quarantine | Created in suspect wave; must be reclassified or discarded before formal use. |
| 3 modified tracked formal classifiers/probes | quarantine | Wired suspect wave into classifier logic. |
| 61 recent result JSONs after 04:57 | quarantine | Generated during suspect wave; ignored by Git but visible to validators/indexers. |
| 28 recent result JSONs after 05:19 | high quarantine | Section-connection / PEPS3D / close-test cluster from the late suspect wave. |
| `FORMAL_SCOUT_READINESS_INDEX.*` / `SIM_ESTATE_INTEGRATION_INDEX.*` | quarantine | Registered 404 -> 427 scout/result estate expansion. |
| `formal_scouts/README.md` | quarantine | Human-facing canonical summary updated with suspect wave. |
| `system_v5/ops/external_audits/three_artifact_run_20260523/` | quarantine | Grok advisory artifacts stored outside grok_sim / quarantine namespace. |
| `SOURCE_ALIGNED_STACK_CROSS_LANE_SYNTHESIS_20260523.md` and `CROSS_LANE_PHI0_KILL_CONVERGENCE_20260523.md` | quarantine | Synthesis docs may be useful, but are not formal sim evidence. |

## Immediate Recovery Rule

Until cleanup is complete:

1. Do not run more forward formal scouts.
2. Do not regenerate formal indexes.
3. Do not consume result JSONs written after the selected cutoff.
4. Do not accept completion/gap classifier output from the contaminated classifier versions.
5. Do not move grok_sim outputs into canonical paths.
6. Treat Grok/Claude/Gemini audit receipts as advisory-only unless explicitly admitted through a reproducible formal ingest scout.

## Recommended Cutoff

Use a conservative quarantine cutoff of:

```text
2026-05-23 04:57:00 local file mtime
```

Rationale:

- The mass formal result rewrite begins at 04:57.
- After that point, 61 result JSONs, 116 formal_scout files, external audit receipts, docs, and evidence indices changed.
- The exact earlier safe boundary may be recoverable, but this cutoff is a clear first quarantine line.

Stricter sub-cutoff:

```text
2026-05-23 05:19:00 local file mtime
```

Rationale:

- 23 untracked formal-scout source files begin at 05:19.
- This isolates the section-connection / PEPS3D / close-test cluster.

## Recovery Plan

### R1 - Freeze and manifest

Write a machine-readable quarantine manifest listing:

- all formal_scout source files with mtime after cutoff,
- all result JSONs with mtime after cutoff,
- all docs/evidence files changed after cutoff,
- all external audit receipts created in this run,
- all tracked dirty files and their status.

Do not delete yet.

### R2 - Restore canonical indexes to last trusted estate

Either:

- revert the four index files to tracked HEAD, or
- regenerate them from an allowlist that excludes quarantined scouts/results.

Do this before any future scout validation that reads estate/index state.

### R3 - Detach external audit receipts from formal evidence

Move or reclassify `system_v5/ops/external_audits/three_artifact_run_20260523/` into a quarantine/advisory namespace or leave it untracked with a quarantine note. Do not let it appear as formal evidence.

### R4 - Rebuild formal progression from source-owned receipts only

For each quarantined formal scout, choose one:

- discard,
- keep as informal/advisory note,
- re-run as a new formal scout from canonical source only with no Grok/Claude audit dependency,
- reproduce a grok_sim observation from scratch inside formal_scouts under an explicit reproduction contract.

No quarantined scout should be admitted merely because it passed during the contaminated wave.

### R5 - Add write-boundary guards

Add two small guards before resuming:

- a grok_sim runner guard that refuses writes outside `system_v5/grok_sim/`;
- a formal-scout ingest guard that refuses to consume grok_sim paths or external audit paths unless an explicit `informal_source_ingest: true` / `formal_reproduction_required: true` contract is present.

### R6 - Re-run only minimal health checks

After cleanup:

- run contract lint on the remaining trusted formal_scout estate,
- regenerate readiness/index files from trusted estate only,
- run a focused classifier that excludes quarantined results,
- compare source/result counts against the pre-contamination 404 baseline.

## Current Bottom Line

The latest evidence does not show `grok_sim` scripts directly writing formal_scouts in the recent window. The confirmed damage is that canonical formal_scout source, result receipts, README, docs, evidence indexes, and external audit artifacts absorbed a large suspect wave while the informal/formal boundary was not being enforced.

Therefore both projects should be considered compromised for interpretation:

- `grok_sim` remains an informal side-quest corpus and should not be used as formal evidence.
- formal_scouts must be rolled back or allowlist-regenerated to a trusted estate before any further scientific conclusion is drawn.
