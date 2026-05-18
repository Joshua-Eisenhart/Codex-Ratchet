# Sim Lane Authority Manifest — 20260518

## Boundary

This is a manifest-only lane-authority document derived from Issue #2 `THREAD_RESULT` comments and the local inventory snapshot. It does not edit sim source, result JSON, queues, admissions, receipts, or ledger state.

## Thread Result Intake

| Lane | Intake status | Authority use |
|---|---|---|
| `PRO_A_INVENTORY_STRATEGY_20260518` | present | Used for report structure and inventory bucket rules. |
| `PRO_B_LANE_MANIFEST_DESIGN_20260518` | present | Used for status enum, required fields, evidence vocabulary, and decision order. |
| `PRO_C_MACRO_ATTRACTOR_SPINE_20260518` | present | Used for macro-spine gates and attractor evidence conditions. |
| `PRO_D_NONCLASSICAL_TOOL_BOUNDARY_20260518` | present | Used for tool/lane boundary policy. |
| `PRO_E_GROK_QUARANTINE_TRANSLATION_20260518` | present | Used for Grok quarantine and translation rules. |
| `PRO_F_REPAIR_BATCH_PICKER_20260518` | `MISSING_OR_MALFORMED` | Not used as authority because it was not posted as a top-level `THREAD_RESULT:` comment. |

## Closed Authority Status Enum

Every row gets exactly one `authority_status`:

- `KEEP_CLASSICAL_BASELINE`
- `KEEP_SEMICLASSICAL_BRIDGE`
- `KEEP_NONCLASSICAL`
- `WRAP_IN_V5`
- `QUARANTINE_GROK_PROPOSAL`
- `REPAIR_RESULT_LINK`
- `ADD_WIZARD_ADMISSION`
- `HOLD_AMBIGUOUS`

No other status is valid. Empty, multi-valued, provisional, comma-separated, or prose-only statuses are invalid.

## Decision Order

First matching terminal rule wins:

1. `QUARANTINE_GROK_PROPOSAL`
   - Any `source_path` or `result_path` under `system_v5/grok_sim/`.
   - Original Grok material remains quarantined even if later translated elsewhere.
2. `REPAIR_RESULT_LINK`
   - A result exists but canonical source/result linkage is missing, conflicting, stale, legacy-shaped, or repair-candidate.
3. `ADD_WIZARD_ADMISSION`
   - Source/result is otherwise classifiable but strict Wizard v4.2 admission is missing.
   - Never use for Grok paths.
4. `HOLD_AMBIGUOUS`
   - Lane is unknown or mixed, bridge sides are missing, evidence conflicts, or load-bearing tool role is unclear.
5. `KEEP_CLASSICAL_BASELINE`
   - Clear classical baseline/control/reference row.
   - NumPy may be baseline-only.
6. `KEEP_SEMICLASSICAL_BRIDGE`
   - Clear bridge row with both classical side and nonclassical side named.
   - NumPy may be bridge-side support only.
7. `KEEP_NONCLASSICAL`
   - Clear nonclassical row with local load-bearing nonclassical tools.
   - PyTorch is required for tensor/graph dynamics where claim-relevant.
   - NumPy must not be load-bearing.
8. `WRAP_IN_V5`
   - Useful legacy/reference row requiring clean v5 wrapper and not blocked above.

Fallback: `HOLD_AMBIGUOUS`.

## Required Manifest Columns

| Column | Required shape |
|---|---|
| `row_id` | stable unique slug |
| `source_path` | repo-relative path or `NONE` |
| `result_path` | repo-relative JSON path or `NONE` |
| `artifact_kind` | `source`, `result`, `source_result_pair`, `grok_receipt`, `admission`, or `blocked_reason` |
| `stem` | basename/stem where possible |
| `inventory_status` | inventory bucket or `unknown` |
| `inventory_lane` | `classical`, `semiclassical_bridge`, `semiclassical_szilard`, `nonclassical`, `mixed_or_ambiguous`, or `unknown` |
| `runner_execution_kind` | `classical`, `bridge`, `nonclassical`, or `unknown` |
| `authority_status` | one closed enum value |
| `status_reason` | concise reason |
| `allowed_evidence_refs` | semicolon-separated evidence tokens or `NONE` |
| `disallowed_evidence_seen` | semicolon-separated evidence tokens or `NONE` |
| `promotion_blockers` | semicolon-separated blockers or `NONE` |
| `load_bearing_tools` | semicolon-separated tool names or `none` |
| `numpy_role` | `none`, `classical_baseline_only`, `bridge_side_support`, or `blocked_load_bearing` |
| `pytorch_load_bearing` | `yes`, `no`, `not_required`, or `unknown` |
| `bridge_classical_side` | path/stem/tool description or `NONE` |
| `bridge_nonclassical_side` | path/stem/tool description or `NONE` |
| `wizard_admission_ref` | repo-relative path or `NONE` |
| `linked_result_ref` | repo-relative path or `NONE` |
| `stage_gate_ref` | gate path/key or `NONE` |
| `claim_ceiling` | `baseline_only`, `bridge_support_only`, `nonclassical_evidence`, `proposal_only`, `repair_only`, or `unknown` |
| `parallel_safe` | `yes`, `no`, or `needs_serial_controller` |
| `parallel_blockers` | semicolon-separated blockers or `NONE` |
| `next_action` | `none`, `wrap_v5`, `repair_link`, `add_wizard_admission`, `quarantine`, or `manual_review` |
| `owner` | `unclaimed`, `local_codex:<id>`, `controller`, or `manual_review` |
| `claim_state` | `unclaimed`, `claimed`, `done`, `blocked`, or `superseded` |
| `review_notes` | concise note or `NONE` |

## Evidence Tokens

Allowed evidence tokens:

- `inventory_row`
- `inventory_summary`
- `source_path_exists`
- `result_path_exists`
- `source_result_stem_match`
- `find_admitted_result_match`
- `wizard_admission_v4_2`
- `result_contract_shape`
- `classification_lego`
- `positive_checks_present`
- `graveyard_companions_present`
- `boundary_check_present`
- `tool_manifest_present`
- `claim_ceiling_present`
- `load_bearing_pytorch`
- `load_bearing_pyg`
- `load_bearing_clifford`
- `load_bearing_z3`
- `load_bearing_cvc5`
- `classical_baseline_numpy`
- `bridge_side_numpy`
- `bridge_both_sides_named`
- `stage_gate_allows`
- `independent_artifact_namespace`
- `grok_path_detected`
- `translated_clean_v5_harness`

Disallowed evidence tokens:

- `inventory_only_promotes`
- `runner_done_only_promotes`
- `process_exit_only`
- `grok_receipt_as_evidence`
- `numpy_load_bearing_blocked_for_bridge_or_nonclassical`
- `bridge_without_classical_side`
- `bridge_without_nonclassical_side`
- `unknown_lane_promoted`
- `ambiguous_lane_promoted`
- `missing_wizard_admission_promoted`
- `legacy_v4_1_admission_promoted`
- `unlinked_result_promoted`
- `contract_shape_missing_promoted`
- `stage_gate_string_true`
- `shared_result_path`
- `shared_fixture_path`
- `shared_queue_mutation`
- `ledger_loopback_missing_promoted`
- `council_or_salience_admits`
- `provider_prose_as_evidence`
- `pre_run_output_admits`

## Promotion Blockers

- `execution_lane_metadata_missing_or_derived`
- `execution_lane_conflict_requires_manual_review`
- `nonclassical_requires_local_load_bearing_pytorch`
- `numpy_load_bearing_blocked_for_bridge_or_nonclassical`
- `linked_result_missing`
- `wizard_admission_missing`
- `result_contract_shape_missing`
- `wizard_admission_admission_missing_result_link`
- `classical_baseline_cannot_support_bridge_or_nonclassical_promotion`
- `load_bearing_tool_depth_missing`
- `source_tool_manifest_missing`
- `source_tool_integration_depth_missing`
- `late_stage_signal_requires_gate_and_decomposition`
- `stage_gate_blocks_late_stage`
- `controller_reconciliation_missing`
- `ledger_loopback_missing`
- `grok_proposal_not_translated`
- `shared_artifact_namespace_blocks_parallelism`
- `prior_receipt_dependency_unsatisfied`
- `manual_review_required`

## Tool Boundary Policy

| Tool category | Classical | Bridge | Nonclassical | Boundary |
|---|---|---|---|---|
| `numpy` | baseline-only | bridge-side support | forbidden | Never load-bearing for nonclassical evidence. |
| `scipy` | baseline-only | bridge-side support | support only | Audit as possible hidden NumPy carrier. |
| `sympy` | baseline/support | bridge support | support | Symbolic derivation only unless explicitly load-bearing for proof fixture. |
| `torch` | baseline/support | bridge support | core | Required local carrier for tensor/graph dynamics where claim-relevant. |
| `torch autograd` | support | bridge support | core | Required for differentiable shell/Axis0/gradient claims. |
| `PyG` | support | bridge support | core | Required for graph message-passing claims. |
| `clifford` | support | bridge support | core | Core for spinor/rotor/geometric-product claims. |
| `z3` | support | bridge support | core | Core for structural UNSAT/consistency claims. |
| `cvc5` | support | bridge support | core | Core cross-check/synthesis surface. |
| `qutip` | baseline/reference | bridge support | support | Reference only; not sole v5 nonclassical substrate. |
| `qiskit` | baseline/reference | bridge support | support | Reference/benchmarking only. |
| `gudhi`, `toponetx`, `xgi` | support | bridge support | support/core when topology is actual object | Must be load-bearing, not labels. |
| `networkx` | baseline/support | bridge support | forbidden as nonclassical core | Use as classical graph/reference support only. |
| `e3nn` | support | bridge support | core when symmetry-native claim | Decorative equivariance is blocked. |

## Parallel Use Contract

- This manifest is classification-only.
- Parallel workers may classify row-local evidence, but may not edit sims, result JSON, queues, admissions, ledger files, or shared result paths.
- `row_id` is the work unit.
- Rows with shared queue/result/fixture/ledger/admission implications require `parallel_safe=needs_serial_controller`.
- If evidence conflicts, set `authority_status=HOLD_AMBIGUOUS` and add `manual_review_required`.

## Seed Rows From This Pass

| row_id | source_path | result_path | artifact_kind | inventory_lane | runner_execution_kind | authority_status | status_reason | promotion_blockers | numpy_role | pytorch_load_bearing | next_action |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `grok_proposals_root` | `system_v5/grok_sim/` | `NONE` | `grok_receipt` | `mixed_or_ambiguous` | `unknown` | `QUARANTINE_GROK_PROPOSAL` | Grok is proposal/failure lab only. | `grok_proposal_not_translated` | `none` | `unknown` | `quarantine` |
| `legacy_v4_numpy_nonclassical_bucket` | `system_v4/probes/**` | `NONE` | `blocked_reason` | `nonclassical` | `nonclassical` | `HOLD_AMBIGUOUS` | Legacy nonclassical rows include NumPy load-bearing blockers. | `numpy_load_bearing_blocked_for_bridge_or_nonclassical; nonclassical_requires_local_load_bearing_pytorch` | `blocked_load_bearing` | `no` | `manual_review` |
| `legacy_v4_missing_lane_bucket` | `system_v4/probes/**` | `NONE` | `blocked_reason` | `unknown` | `unknown` | `HOLD_AMBIGUOUS` | Lane metadata is missing or derived for most legacy rows. | `execution_lane_metadata_missing_or_derived` | `unknown` | `unknown` | `manual_review` |
| `current_v5_formal_spine` | `system_v5/ops/formal_scouts/**` | `system_v5/ops/formal_scouts/results/**` | `source_result_pair` | `nonclassical` | `nonclassical` | `HOLD_AMBIGUOUS` | Current v5 spine is cleaner, but keep row-level authority separate from global inventory. | `NONE` | `none` | `unknown` | `manual_review` |

## Selected Small Repair Batch 001 — 20260518

Manifest-only row-level repair batch selected from committed authority docs after commit `0836e3306`. This batch does not run sims, edit result JSON, edit queues, promote Grok output, or claim macro-attractor convergence.

| row_id | source_path | result_path | artifact_kind | stem | inventory_status | inventory_lane | runner_execution_kind | authority_status | status_reason | allowed_evidence_refs | disallowed_evidence_seen | promotion_blockers | load_bearing_tools | numpy_role | pytorch_load_bearing | bridge_classical_side | bridge_nonclassical_side | wizard_admission_ref | linked_result_ref | stage_gate_ref | claim_ceiling | parallel_safe | parallel_blockers | next_action | owner | claim_state | review_notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `v5_density_matrix_numpy_baseline_authority_20260518` | `system_v5/legos/density_matrix_trace_positive_semidefinite.py` | `system_v5/legos/results/density_matrix_trace_positive_semidefinite_results.json` | `source_result_pair` | `density_matrix_trace_positive_semidefinite` | `unknown` | `classical` | `classical` | `KEEP_CLASSICAL_BASELINE` | NumPy finite-linear-algebra density-matrix validity row; baseline only, not bridge or nonclassical evidence. | `source_path_exists; result_path_exists; source_result_stem_match; classification_lego; positive_checks_present; graveyard_companions_present; boundary_check_present; tool_manifest_present; claim_ceiling_present; classical_baseline_numpy` | `NONE` | `classical_baseline_cannot_support_bridge_or_nonclassical_promotion` | `numpy` | `classical_baseline_only` | `not_required` | `NONE` | `NONE` | `NONE` | `system_v5/legos/results/density_matrix_trace_positive_semidefinite_results.json` | `NONE` | `baseline_only` | `yes` | `NONE` | `none` | `local_codex:small-foundation-batch-001` | `done` | Uses committed baseline-support file and result; NumPy is load-bearing only inside baseline ceiling. |
| `v5_coherent_information_gradient_pytorch_source_confirmation_20260518` | `system_v5/legos/coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3.py` | `system_v5/legos/results/coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3_results.json` | `source_result_pair` | `coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3` | `unknown` | `nonclassical` | `nonclassical` | `ADD_WIZARD_ADMISSION` | Source/result stem is exact, lego validator passes, and result records local PyTorch autograd load-bearing coherent-information gradient evidence; strict Wizard admission remains unlinked. | `source_path_exists; result_path_exists; source_result_stem_match; classification_lego; positive_checks_present; graveyard_companions_present; boundary_check_present; result_contract_shape; tool_manifest_present; claim_ceiling_present; load_bearing_pytorch; load_bearing_z3` | `missing_wizard_admission_promoted` | `wizard_admission_missing` | `pytorch_autograd; opt_einsum; z3` | `none` | `yes` | `NONE` | `NONE` | `NONE` | `system_v5/legos/results/coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3_results.json` | `system_v5/ops/formal_scouts/results/source_native_redo_parent_receipt_admission_gate_probe_results.json` | `nonclassical_evidence` | `yes` | `NONE` | `add_wizard_admission` | `local_codex:small-foundation-batch-002` | `done` | Linked-result repair completed; do not promote beyond lego-level nonclassical evidence until exact Wizard admission is added separately. |
| `grok_loop_runner_sidequest_quarantine_20260518` | `system_v5/grok_sim/loop_runner/README.md` | `NONE` | `source` | `loop_runner` | `unknown` | `mixed_or_ambiguous` | `unknown` | `QUARANTINE_GROK_PROPOSAL` | Path is under `system_v5/grok_sim/`; loop runner README declares side-quest/noncanonical fencing, so this remains proposal/failure-lab only. | `source_path_exists; grok_path_detected` | `grok_receipt_as_evidence; provider_prose_as_evidence` | `grok_proposal_not_translated` | `none` | `none` | `unknown` | `NONE` | `NONE` | `NONE` | `NONE` | `NONE` | `proposal_only` | `yes` | `NONE` | `quarantine` | `local_codex:small-foundation-batch-001` | `done` | Quarantine row only; no translation, no evidence use, no promotion. |
