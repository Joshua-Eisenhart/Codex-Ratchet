# V5 Clean Rebuild Completion Audit 2026-05-14

Status: working audit
Scope: current v5 clean rebuild batch

## Objective Restated

Rebuild SIM/QIT work cleanly in v5 while treating v4 as a reference corpus:

- v4 is mined for callables, receipts, ceilings, and graveyards;
- v5 contains clean docs, formal scouts, queue cleanup, and provider records;
- exploration remains active but fenced;
- gates reject bad evidence without blocking rough formal-scout work;
- git/worktree state is measured and reported.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Read/support clean rebuild doctrine | `system_v5/docs/V5_CLEAN_REBUILD_CHARTER.md` | present |
| Read/support formal-scout contract | `system_v5/docs/GEOMETRIC_CONSTRAINT_MANIFOLD_FORMAL_SCOUT_CONTRACT.md` | present |
| Read/support provider split | `system_v5/docs/MULTIMODEL_PROPOSAL_SPLIT.md` | present |
| v4 as reference only | `V5_CLEAN_REBUILD_CHARTER.md`, formal-scout imports from v4 | satisfied for new work |
| v5 as clean rebuild surface | `system_v5/ops/formal_scouts/`, `system_v5/ops/queue_cleanup/` | satisfied |
| `grok_sim` proposal-only boundary | `MULTIMODEL_PROPOSAL_SPLIT.md` | present |
| Cleanliness before/after counts | this file, probe inventory | partial, counts recorded |
| Runtime byproducts removed | `system_v5/ops/formal_scouts/__pycache__` removed | satisfied |
| Transfer from real v4 callables | formal-scout harnesses import v4 files by path | satisfied for current scouts |
| Formal-scout receipts | two result receipts under `system_v5/ops/formal_scouts/results/` | satisfied |
| Provider proposal record | `system_v5/ops/formal_scouts/provider_scouts_20260514.md` | satisfied: Grok done, Gemini blocked, Sonnet done |
| Probe cleanup inventory | `probe_folder_rebuild_inventory_20260514.md` | satisfied initial inventory |
| Probe cleanup manifest-level classifier | `classify_v4_probe_corpus.py`, `v4_probe_corpus_classification_20260514.json` | satisfied read-only pass |
| Gate-quality findings | this file | partial, initial findings below |
| Literal math names | current v5 scout executable names | satisfied |
| Git status summary | this file | current counts below |

## Current Git Counts

Measured before this audit update:

```text
?? 20544
D 4
M 11
```

Measured after validation/classification reruns and runtime cleanup:

```text
?? 20547
D 4
M 11
```

The increase is this v5 batch plus generated v5 evidence; the large pre-existing
dirty state remains outside this batch.

Runtime byproduct check:

```text
find system_v5/ops -type d -name __pycache__ -print
```

Result: no output.

Scoped new v5 batch paths are untracked:

```text
.tmp/goal_geometric_constraint_manifold_20260514.md
system_v5/docs/GEOMETRIC_CONSTRAINT_MANIFOLD_FORMAL_SCOUT_CONTRACT.md
system_v5/docs/MULTIMODEL_PROPOSAL_SPLIT.md
system_v5/docs/V5_CLEAN_REBUILD_CHARTER.md
system_v5/ops/formal_scouts/
system_v5/ops/queue_cleanup/probe_folder_rebuild_inventory_20260514.md
system_v5/ops/queue_cleanup/v5_clean_rebuild_completion_audit_20260514.md
```

## Validation Evidence

Command:

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py
```

Result:

```text
all_pass: true
validated:
- entropy_reduction_before_hopf_projection_order_probe_results.json
- nested_finite_geometry_holonomy_noncommutation_probe_results.json
```

## Poor-Gate Findings

1. `system_v4/probes` has no active write fence. The charter now declares the
   policy, but enforcement still needs a script or preflight check.
2. Existing inventory is count-level, not manifest-level. It blocks broad delete,
   but it does not yet classify all 6,725 untracked probe paths. Updated:
   `classify_v4_probe_corpus.py` now writes a direct-file classification JSON.
3. Gemini CLI still attempts interactive browser auth and is not currently a
   reliable headless scout lane.
4. Formal-scout validation originally did not enforce `boundary`,
   `nearby_variants`, or `why_not_v4_probes`. Updated:
   `validate_formal_scout_results.py` now requires those fields and both scout
   receipts pass after rerun.
5. Grok translation targets needed importability verification. Updated: all
   five target v4 files loaded through `importlib`.
6. Provider outputs are recorded manually; they need a receipt schema if they
   become routine.

## Next Clean Transfer Action

Build a manifest-level probe classifier under `system_v5/ops/queue_cleanup/`
that reads `system_v4/probes` and writes a v5 JSON inventory with:

- tracked status;
- admitted/reference match;
- generated survivor-class wave;
- naming contamination;
- source-only/result-only;
- candidate action: keep, wrap-from-v5, quarantine-by-manifest, or review.

Do not move files in the classifier pass.

Status: completed as a read-only classifier. Next action is selecting one
candidate family, likely `quarantine_by_manifest_candidate`, and writing a move
manifest before any file movement.

## Commit Candidate Paths

Stage only these paths for the v5 clean rebuild checkpoint:

```text
system_v5/docs/V5_CLEAN_REBUILD_CHARTER.md
system_v5/docs/GEOMETRIC_CONSTRAINT_MANIFOLD_FORMAL_SCOUT_CONTRACT.md
system_v5/docs/MULTIMODEL_PROPOSAL_SPLIT.md
system_v5/ops/formal_scouts/README.md
system_v5/ops/formal_scouts/provider_scouts_20260514.md
system_v5/ops/formal_scouts/sim_nested_finite_geometry_holonomy_noncommutation_probe.py
system_v5/ops/formal_scouts/sim_entropy_reduction_before_hopf_projection_order_probe.py
system_v5/ops/formal_scouts/validate_formal_scout_results.py
system_v5/ops/formal_scouts/results/nested_finite_geometry_holonomy_noncommutation_probe_results.json
system_v5/ops/formal_scouts/results/entropy_reduction_before_hopf_projection_order_probe_results.json
system_v5/ops/queue_cleanup/probe_folder_rebuild_inventory_20260514.md
system_v5/ops/queue_cleanup/v5_clean_rebuild_completion_audit_20260514.md
system_v5/ops/queue_cleanup/classify_v4_probe_corpus.py
```

Do not stage existing `queue_done_duplicate_repair_*.json` files in
`system_v5/ops/queue_cleanup/`.

Do not stage `v4_probe_corpus_classification_20260514.json` in the normal source
checkpoint. It is a 5.9 MB generated inventory artifact. The classifier and this
markdown summary are the clean checkpoint; the JSON can be regenerated or staged
later as an explicit evidence snapshot.
