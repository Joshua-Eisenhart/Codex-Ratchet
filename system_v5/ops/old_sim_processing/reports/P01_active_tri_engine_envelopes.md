# P01 Active Tri-Engine Envelopes — Controller Fallback Report

Generated: `2026-06-08T20:49:17.090692+00:00`

## Verdict

The Codex TUI `codex1` lane exited without writing the required artifacts, so this report is a **Hermes controller fallback** built from the existing package index and current source-claim/tool-coverage audits.

This is useful for triage and fuel extraction. It is **not** mathematical admission, not deletion authority, and not a substitute for source-backed reruns.

## What this package covered

- Package id: `P01_active_tri_engine_envelopes`
- Rows classified: `202`
- Buckets: `{'current_formal_scout_results': 201, 'current_julia_carrier_results': 1}`
- Classifications: `{'scratch_diagnostic': 183, 'formal_scout': 19}`
- Reuse modes: `{'scratch_diagnostic_keep_under_no_promotion_ceiling': 141, 'active_three_engine_scratch_template_or_receipt': 42, 'formal_scout_revalidate_or_use_as_bounded_pressure': 19}`
- `all_pass`: `{'True': 196, 'None': 5, 'False': 1}`
- `promotion_allowed`: `{'False': 202}`
- `formal_admission_allowed`: `{'False': 195, 'None': 7}`

Top families:

- `quotient_admissibility`: `196`
- `tool_integration`: `186`
- `engine_axis_terrain_operator`: `127`
- `carrier_division_algebra`: `86`
- `proof_symbolic`: `55`
- `qit_density_entanglement`: `46`
- `associator_nonassoc`: `35`
- `weyl_spinor_chirality`: `31`
- `bridge_physics`: `31`
- `hopf_torus_holonomy`: `24`
- `root_distinguishability`: `22`
- `finitude`: `15`


## Top reusable fuel extracted

- Quotient/admissibility scratch patterns dominate the package: `196` rows.
- Tool-integration receipts are dense but still mostly narrow-source coverage: `186` rows.
- Carrier/division-algebra and spinor/Hopf rows are good rebuild fuel, but they must stay under source-backed/strict-source-backed validators before any rich-tool claim.
- One failed bridge-facing row is preserved as a falsifier/negative control, not tuned into a pass.

Sample fuel paths:

- `system_v5/ops/formal_scouts/results/carrier_readout_discriminator_matrix_results.json`
- `system_v5/ops/formal_scouts/results/clifford_spinor_carrier_pytorch_leg_results.json`
- `system_v5/ops/formal_scouts/results/disc_associator_harden_results.json`
- `system_v5/ops/formal_scouts/results/disc_charge_ladder_results.json`
- `system_v5/ops/formal_scouts/results/disc_gravity_knot_results.json`
- `system_v5/ops/formal_scouts/results/disc_hopf_lifted_vs_density_results.json`
- `system_v5/ops/formal_scouts/results/disc_qit_source_native_results.json`
- `system_v5/ops/formal_scouts/results/disc_shell_capacity_2n2_results.json`
- `system_v5/ops/formal_scouts/results/disc_sigma_y_holonomy_results.json`
- `system_v5/ops/formal_scouts/results/disc_spinor_carrier_minimality_results.json`


## Candidate micro-legos to rebuild

- Formal-scout rows with `reuse_mode=formal_scout_revalidate_or_use_as_bounded_pressure` should become bounded micro-legos only after fresh source rerun and freshness checks.
- Scratch rows with null `all_pass` need row-level review before reuse.
- Three-engine envelope-style rows need `scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed`; use `--strict-source-backed` before claiming rich-tool fuel.

## Negative controls / graveyard rows worth preserving

- `system_v5/ops/formal_scouts/results/xi_shell_coherent_information_gradient_adversarial_audit_probe_results.json` has `all_pass=false`; keep it as bridge/Xi falsifier evidence.

## Duplicate/archive/delete candidates

None from this fallback. All cleanup remains blocked behind a later controller cleanup gate.

## Action manifest

Wrote: `system_v5/evidence/old_sim_processing/actions/P01_active_tri_engine_envelopes_actions.json`

Action counts: `{'keep_current': 170, 'rebuild_as_micro_lego': 18, 'mine_into_fuel_bank': 8, 'needs_human_review': 5, 'graveyard_keep_as_falsifier': 1}`

## Open blockers and required validators

- Codex `codex1` worker output is not usable as evidence; no required report/manifest existed before this fallback.
- Source-backed validator gates are necessary because declared package fields alone were already shown too weak.
- Current rich-tool coverage is narrow; do not inflate these rows into full QIT/attractor/spinor-network evidence.

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
