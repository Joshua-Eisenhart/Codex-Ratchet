# P03 QIT/Density/Entropy Classical Baselines — Controller Fallback Report

Generated: `2026-06-08T20:49:17.090692+00:00`

## Verdict

The Codex TUI `codex2` lane exited with signal/termination status before writing the required artifacts, so this report is a **Hermes controller fallback** built from the existing package index and current audits.

This package is a large mining lane. Its outputs are baseline/fuel classifications only. Old v4/source/archive rows are not current QIT evidence until rebuilt and rerun under current contracts.

## What this package covered

- Package id: `P03_qit_density_entropy_classical_baselines`
- Rows classified: `900`
- Buckets: `{'v4_probe_sources': 585, 'read_only_legacy_reference': 166, 'v4_a2_state_results': 80, 'v4_docs': 69}`
- Kinds: `{'sim_source': 615, 'result_or_index_json': 147, 'doc_or_reference': 138}`
- Classifications: `{'None': 815, 'classical_baseline': 53, 'tool_lego_fit_probe': 18, 'audit': 8, 'canonical': 3, 'supporting': 2, 'controller_audit': 1}`
- Reuse modes: `{'legacy_translate_to_micro_lego_or_baseline_control': 734, 'archive_mine_for_math_objects_controls_falsifiers': 166}`
- `all_pass`: `{'None': 822, 'True': 78}`
- `promotion_allowed`: `{'None': 854, 'False': 46}`

Top families:

- `engine_axis_terrain_operator`: `542`
- `bridge_physics`: `360`
- `entropy_classical_engine`: `284`
- `external_archive`: `205`
- `qit_density_entanglement`: `157`
- `tool_integration`: `94`
- `hopf_torus_holonomy`: `82`
- `graph_topology`: `77`
- `proof_symbolic`: `73`
- `weyl_spinor_chirality`: `54`
- `carrier_division_algebra`: `46`
- `noncommutation_order`: `17`


## Top reusable fuel extracted

- QIT/density/entropy rows are best treated as side-lane baselines, controls, and rebuild templates.
- Carnot/Szilard/classical-engine rows can supply finite-time/control baselines, but not current nonclassical evidence.
- Graph/QIT mapping docs can seed future fuel-bank entries with source quotes.
- Bridge/axis rows are control/falsifier material unless rebuilt after lower-layer admissibility is real.

Sample QIT/entropy/classical paths:

- `READ ONLY Legacy core_docs/QIT_COMPRESSION_FUTURE_REFERENCES.md`
- `READ ONLY Legacy core_docs/QIT_GRAPH_LAYER_MAPPING.md`
- `READ ONLY Legacy core_docs/QIT_GRAPH_PROMOTION_GATES.md`
- `READ ONLY Legacy core_docs/QIT_GRAPH_RUNTIME_MODEL.md`
- `READ ONLY Legacy core_docs/QIT_GRAPH_SCHEMA.md`
- `READ ONLY Legacy core_docs/QIT_GRAPH_SIDECAR_POLICY.md`
- `READ ONLY Legacy core_docs/QIT_GRAPH_SYNC_README.md`
- `READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/constraint ladder/Constraints. Entropy.md`
- `READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/constraint ladder/Entropy contract v1.md`
- `READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/constraint ladder/METRIC_ADMISSIBILITY_v1.md`
- `READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_sagb_entangle_seed.py`
- `READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_metrics.py`


## Candidate micro-legos to rebuild

- Translate legacy `system_v4/probes/*.py` sources into current micro-legos with isolated temp reruns first.
- Rebuild QIT/density rows using current rich tools where load-bearing: `dynamiqs`, `qutip`, `quimb`, `netket`, `toponetx`, `gudhi`, `torch_geometric`, `geomstats`, or `e3nn` as appropriate.
- Keep classical-engine/Carnot/Szilard rows as side-lane controls, not as admission evidence.

## Negative controls / graveyard rows worth preserving

- Bridge/Axis0-adjacent rows should remain falsifier/control fuel until lower-layer geometry/carrier gates are rebuilt.
- Any old result without source freshness or current-contract validator remains mining material only.

## Duplicate/archive/delete candidates

None from this fallback. The manifest proposes no deletion. Any cleanup requires the P00 controller gate sequence.

## Action manifest

Wrote: `system_v5/evidence/old_sim_processing/actions/P03_qit_density_entropy_classical_baselines_actions.json`

Action counts: `{'rebuild_as_micro_lego': 579, 'mine_into_fuel_bank': 309, 'needs_human_review': 12}`

## Open blockers and required validators

- Codex `codex2` worker did not close normally or write artifacts; treat its prose/log as non-evidence.
- This fallback did not read all 900 underlying source files line-by-line; it classifies from the package index. Row-level source quote extraction remains a future fuel-bank step.
- Reuse requires fresh current-contract rebuild/rerun. Old rows stay no-promotion/no-admission.

## Closeout check

Command run:

```bash
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 -c 'import json, pathlib\nbase=pathlib.Path(\'/Users/joshuaeisenhart/Codex-Ratchet\')\npaths=[\n \'system_v5/evidence/old_sim_processing/actions/P01_active_tri_engine_envelopes_actions.json\',\n \'system_v5/evidence/old_sim_processing/actions/P03_qit_density_entropy_classical_baselines_actions.json\',\n]\nfor rel in paths:\n    data=json.load(open(base/rel))\n    print(f"{rel}: schema={data.get(\'schema\')} package_id={data.get(\'package_id\')} rows={len(data.get(\'rows\', []))}")'
```

Output:

```text
system_v5/evidence/old_sim_processing/actions/P01_active_tri_engine_envelopes_actions.json: schema=old_sim_action_manifest.v1 package_id=P01_active_tri_engine_envelopes rows=202
system_v5/evidence/old_sim_processing/actions/P03_qit_density_entropy_classical_baselines_actions.json: schema=old_sim_action_manifest.v1 package_id=P03_qit_density_entropy_classical_baselines rows=900
```
