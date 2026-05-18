# Sim Lane Blocker Report — 20260518

## Source Snapshot

- GitHub issue: `Joshua-Eisenhart/Codex-Ratchet#2`
- Comment collection rule: only comments whose body begins with `THREAD_RESULT:`
- Local inventory source: `/tmp/sim_inventory_full.json`, generated with `scripts/sim_inventory_index.py --include-rows --json-out /tmp/sim_inventory_full.json --md-out /tmp/sim_inventory_full.md`
- Boundary: inventory/collation only. This report does not admit, promote, validate, run, edit, or repair any sim.
- Guardrails: no sim source edits, no result JSON edits, no queue edits, no Grok promotion.

## Thread Result Intake

| Lane | Status | Notes |
|---|---|---|
| `PRO_A_INVENTORY_STRATEGY_20260518` | present | Usable full body present in a `THREAD_RESULT:` comment. A later blocked relay for the same lane was ignored. |
| `PRO_B_LANE_MANIFEST_DESIGN_20260518` | present | Usable full body present. |
| `PRO_C_MACRO_ATTRACTOR_SPINE_20260518` | present | Usable full body present. |
| `PRO_D_NONCLASSICAL_TOOL_BOUNDARY_20260518` | present | Usable full body present. |
| `PRO_E_GROK_QUARANTINE_TRANSLATION_20260518` | present | Usable full body present. |
| `PRO_F_REPAIR_BATCH_PICKER_20260518` | `MISSING_OR_MALFORMED` | A raw `PRO_HANDOFF_RESULT_BEGIN` comment exists, but it does not begin with `THREAD_RESULT:` and is not accepted under this pass. |

## Current Summary Counts

Local inventory counts from the fresh `/tmp` run:

- Source files indexed: `10,855`
- Result JSON files seen: `8,319`
- Linked result JSON files: `6,825`
- Unlinked result JSON files: `1,494`
- Wizard-admitted stems: `6,247`
- Source-only rows: `3,479`
- Repair candidates: `552`

The large blocker field is mostly legacy/proposal surface, not the current v5 formal-scout spine:

- `nonclassical_requires_local_load_bearing_pytorch`: `3,213` total, with `3,181` under `system_v4` and `32` under `system_v5/grok_sim`.
- `numpy_load_bearing_blocked_for_bridge_or_nonclassical`: `241` total, all under `system_v4`.
- `execution_lane_metadata_missing_or_derived`: `5,442` total, with `5,417` under `system_v4` and `25` under `system_v5/grok_sim`.
- `execution_lane_conflict_requires_manual_review`: `1,165` total, with `1,142` under `system_v4` and `23` under `system_v5/grok_sim`.

## Priority Blocker Counts

| Blocker | Count | Main domain |
|---|---:|---|
| `execution_lane_metadata_missing_or_derived` | `5,442` | Legacy v4 plus Grok proposals |
| `wizard_admission_missing` | `4,031` | Legacy v4 plus Grok proposals |
| `linked_result_missing` | `4,056` | Legacy v4 plus Grok proposals |
| `nonclassical_requires_local_load_bearing_pytorch` | `3,213` | Legacy v4 plus Grok proposals |
| `execution_lane_conflict_requires_manual_review` | `1,165` | Legacy v4 plus Grok proposals |
| `numpy_load_bearing_blocked_for_bridge_or_nonclassical` | `241` | Legacy v4 |

## Lane Authority Interpretation

The inventory supports the WebUI audit's warning, but it narrows the repair target:

- The current v5 formal-scout spine is much cleaner than the whole historical estate.
- The global counts are dominated by `system_v4/probes` and `system_v5/grok_sim`.
- Macro-attractor claims must not use global inventory presence as evidence.
- Any convergence claim must explicitly separate `current_v5_formal`, `legacy_v4_reference`, and `grok_proposal_lab`.

## Top Blocker Samples: Nonclassical Missing Local PyTorch

These are samples from `/tmp/sim_inventory_full.json`. They are not selected for promotion.

| Row | Path | Lane | Tools | Result count | Proposed authority |
|---|---|---|---|---:|---|
| `sim_proposed_axis_0_lego_gemini_20260514T005805Z` | `system_v5/grok_sim/loop_runner/proposed_formal_sims/_quarantine_jargon/sim_proposed_axis_0_lego_gemini_20260514T005805Z.py` | `nonclassical` | none | 0 | `QUARANTINE_GROK_PROPOSAL` |
| `sim_proposed_axis_0_lego_grok_20260514T005805Z` | `system_v5/grok_sim/loop_runner/proposed_formal_sims/_quarantine_jargon/sim_proposed_axis_0_lego_grok_20260514T005805Z.py` | `nonclassical` | none | 0 | `QUARANTINE_GROK_PROPOSAL` |
| `chirality_aware_boundary_conditional_expectation_area_law_compatibility_probe` | `system_v5/grok_sim/loop_runner/proposed_formal_sims/manifold_legos_nonclassical/chirality_aware_boundary_conditional_expectation_area_law_compatibility_probe.py` | `nonclassical` | none | 0 | `QUARANTINE_GROK_PROPOSAL` |
| `sim_proposed_axes_math_gemini_20260514T190612Z` | `system_v5/grok_sim/loop_runner/proposed_formal_sims/sim_proposed_axes_math_gemini_20260514T190612Z.py` | `nonclassical` | `qutip` | 0 | `QUARANTINE_GROK_PROPOSAL` |
| `followup_anomaly_investigation` | `system_v4/probes/followup_anomaly_investigation.py` | `nonclassical` | none | 1 | `HOLD_AMBIGUOUS` |
| `sim_admissibility_manifold_mc` | `system_v4/probes/sim_admissibility_manifold_mc.py` | `nonclassical` | `numpy` | 1 | `HOLD_AMBIGUOUS` |
| `sim_clifford_basis_grade_product_table_survivor_classes` | `system_v4/probes/sim_clifford_basis_grade_product_table_survivor_classes.py` | `nonclassical` | `clifford; z3` | 1 | `HOLD_AMBIGUOUS` unless rewrapped in v5 |

## Top Blocker Samples: Bridge Or Nonclassical NumPy Load-Bearing

These rows should not be used as nonclassical evidence until reclassified, wrapped, or repaired.

| Row | Path | Lane | Tools | Result count | Proposed authority |
|---|---|---|---|---:|---|
| `sim_admissibility_manifold_mc` | `system_v4/probes/sim_admissibility_manifold_mc.py` | `nonclassical` | `numpy` | 1 | `HOLD_AMBIGUOUS` |
| `sim_carnot_tool_coupling_matrix` | `system_v4/probes/sim_carnot_tool_coupling_matrix.py` | `semiclassical_bridge` | many including `numpy; pytorch; clifford; z3` | 1 | `HOLD_AMBIGUOUS` until bridge sides and NumPy role are explicit |
| `sim_f01_finitude_constraint` | `system_v4/probes/sim_f01_finitude_constraint.py` | `nonclassical` | `numpy; z3` | 1 | `HOLD_AMBIGUOUS` |
| `sim_geomstats_s3_loop_endpoint_distance_collision_survivor_classes` | `system_v4/probes/sim_geomstats_s3_loop_endpoint_distance_collision_survivor_classes.py` | `nonclassical` | `geomstats; numpy; z3` | 1 | `HOLD_AMBIGUOUS` |
| `sim_hopf_base_angle_torus_winding_coordinate_coupling_gap_survivor_classes` | `system_v4/probes/sim_hopf_base_angle_torus_winding_coordinate_coupling_gap_survivor_classes.py` | `nonclassical` | `numpy; z3` | 1 | `HOLD_AMBIGUOUS` |
| `sim_hopf_projection_phase_difference_circle_coordinate_survivor_classes` | `system_v4/probes/sim_hopf_projection_phase_difference_circle_coordinate_survivor_classes.py` | `nonclassical` | `cvc5; numpy` | 1 | `HOLD_AMBIGUOUS` |

## Result Linkage Bucket

Global result linkage remains a blocker:

- `linked_result_missing`: `4,056`
- `unlinked_result_json_count`: `1,494`

Handling rule:

- Do not auto-link by filename similarity alone.
- Rows with result files but missing or conflicting canonical linkage should be `REPAIR_RESULT_LINK`.
- If schema/source match is stale or ambiguous, use `HOLD_AMBIGUOUS`, not evidence.

## Wizard Admission Bucket

Global Wizard admission remains a blocker:

- `wizard_admission_missing`: `4,031`

Handling rule:

- Missing admission is `ADD_WIZARD_ADMISSION` only after lane and result linkage are otherwise clear.
- Missing admission on Grok paths remains `QUARANTINE_GROK_PROPOSAL`, not `ADD_WIZARD_ADMISSION`.
- Legacy v4.1 or prose/council agreement is not live v4.2 admission.

## Grok Visible But Non-Evidence

Every path under `system_v5/grok_sim/` is proposal/failure-lab material only:

- It may seed translation.
- It may document failure patterns.
- It may motivate graveyard companions.
- It may not be used as admission, result evidence, proof support, nonclassical support, bridge support, or macro-attractor evidence.

Examples visible in inventory:

- `system_v5/grok_sim/loop_runner/proposed_formal_sims/_quarantine_jargon/*.py`
- `system_v5/grok_sim/loop_runner/proposed_formal_sims/manifold_legos_nonclassical/*.py`
- `system_v5/grok_sim/loop_runner/receipts/**`

Authority status: `QUARANTINE_GROK_PROPOSAL`.

## Negative / Graveyard Bucket

Rows with `source_only_negative_or_graveyard`, `graveyard_negative`, or negative-space role should not be treated as trash by default.

Authority handling:

- Keep as graveyard/reference candidates if they have useful failure shape.
- Do not promote them as survivors.
- Require manifest decision before archive/move/delete.

## Candidate Rows Safe For V5 Wrapping

Candidate-only filter:

- Prefer rows with useful math object and callable surface.
- Exclude Grok paths unless translated into clean v5.
- Exclude high-risk NumPy load-bearing nonclassical paths until rewritten.
- Exclude ambiguous lane rows unless the next action is explicitly `HOLD_AMBIGUOUS`.
- Do not run or repair during this report pass.

## Blocked Promotion Gates

Promotion remains blocked where any of these are true:

- lane authority missing or conflicted;
- linked receipt missing;
- nonclassical local load-bearing PyTorch missing;
- NumPy is load-bearing in bridge/nonclassical evidence path;
- Wizard admission missing;
- Grok/proposal material is not translated into clean v5;
- result contract shape missing;
- negative/graveyard companion missing;
- claim ceiling missing.
