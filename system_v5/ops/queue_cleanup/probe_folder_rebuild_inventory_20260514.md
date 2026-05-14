# Probe Folder Rebuild Inventory 2026-05-14

Status: initial inventory
Scope: `system_v4/probes`

## Current Counts

Measured in the working tree:

| Count | Value |
|---|---:|
| Total files directly under `system_v4/probes` | 10,986 |
| `sim_*.py` files | 10,507 |
| `sim_*.json` files | 51 |
| Untracked paths under `system_v4/probes` | 6,725 |
| Tracked modified files under `system_v4/probes` | 3 |
| Tracked deleted files under `system_v4/probes` | 4 |

## Pattern Counts

| Pattern | Count |
|---|---:|
| `*_survivor_classes.py` | 6,588 |
| names containing `axis` | 145 |
| names containing `engine` | 70 |
| names containing `rosetta` | 20 |
| names containing `iching` | 5 |

## Tracked Probe Dirt

```text
M system_v4/probes/a2_state/sim_results/sim_choi_matrix_classical_results.json
D system_v4/probes/sim_axis_couple_0_6_entropy_gradient_x_action_orientation.py
D system_v4/probes/sim_carnot_axis4_cycle_ordering_bridge.py
M system_v4/probes/sim_choi_matrix_classical.py
D system_v4/probes/sim_iching_szilard_initial_state_sweep.py
D system_v4/probes/sim_iching_szilard_measurement_rosetta.py
M system_v4/probes/sim_partial_trace_classical.py
```

## Decision

Freeze `system_v4/probes` as the reference corpus for new work. Do not add
fresh exploratory generated waves there.

Use `system_v5` for clean rebuild surfaces:

- docs and contracts in `system_v5/docs`;
- formal scouts in `system_v5/ops/formal_scouts`;
- cleanup manifests in `system_v5/ops/queue_cleanup`;
- quarantine manifests or moved artifacts in `system_v5/ops/quarantine`.

## Cleanup Sequence

1. Inventory tracked dirt and decide whether each tracked delete/modify is
   intentional.
2. Inventory untracked probe files by generator family and naming pattern.
3. Identify admitted/reference stems that must remain addressable.
4. Move generated untracked waves only by manifest, not by broad delete.
5. For naming-contaminated files, prefer v5 clean wrappers unless the file is
   being actively reused and needs a source rename.
6. Regenerate `system_v5/docs/SIM_INVENTORY_INDEX.md` only after the move/rename
   manifest is stable.

## Stop Condition

Do not run broad sim generation until this folder has a declared write policy
and a cleanup manifest for any touched family.

## Read-Only Classification Pass

Classifier:

`system_v5/ops/queue_cleanup/classify_v4_probe_corpus.py`

Result:

`system_v5/ops/queue_cleanup/v4_probe_corpus_classification_20260514.json`

Summary:

| Candidate action | Count |
|---|---:|
| `quarantine_by_manifest_candidate` | 6,588 |
| `keep_reference_or_review` | 3,845 |
| `review_naming_contamination` | 252 |
| `keep_reference` | 244 |
| `review_result_linkage` | 52 |
| `review_untracked` | 4 |
| `wrap_from_v5_when_reused` | 1 |

Naming contamination found:

| Token | Count |
|---|---:|
| `axis` | 145 |
| `engine` | 70 |
| `rosetta` | 20 |
| `gstack` | 19 |
| `iching` | 5 |
| `type2` | 3 |
| `type1` | 2 |

The classifier is read-only. It moved, renamed, deleted, staged, and promoted
nothing.
