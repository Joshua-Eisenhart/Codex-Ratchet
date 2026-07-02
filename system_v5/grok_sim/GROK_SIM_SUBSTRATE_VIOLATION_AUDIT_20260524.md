# grok_sim Substrate Violation Audit - 2026-05-24

Status: sidequest-local audit only. No formal-sim proof import or promotion.

## Summary

- Scope: discovery-based scan; detected 34 iters.
- Iters found: ['283', '284', '285', '286', '287', '288', '289', '290', '291', '292', '293', '294', '295', '296', '297', '298', '299', '300', '301', '302', '303', '304', '305', '306a', '306a2', '306a3', '306a4', '306a5', '306a6', '307', '308', '309', '310', '311']
- Counts: {"adapter_control": 3, "aligned_candidate": 17, "hard_block": 14}.
- Aligned-candidate sources: ['283', '284', '285', '286', '290', '291', '306a', '306a2', '306a3', '306a4', '306a5', '306a6', '307', '308', '309', '310', '311'].
- Adapter/control sources: ['287', '288', '289'].
- Hard-block sources: ['292', '293', '294', '295', '296', '297', '298', '299', '300', '301', '302', '303', '304', '305'].
- Boundary-vocabulary issue iters: ['283', '284', '285', '286', '287', '288', '289', '290', '291', '292', '293', '294', '295', '296', '297', '298', '299', '300', '301', '302', '303', '304'].

## Rebuild Baseline

Use aligned candidates only as source baselines, not as evidence receipts. Receipts using formal_scout vocabulary need boundary repair before they can serve even as grok_sim-local ledger entries.

Recommended source baseline window after this scan: ['283', '284', '285', '286', '290', '291', '306a', '306a2', '306a3', '306a4', '306a5', '306a6', '307', '308', '309', '310', '311'].

Hard-block iters may still be useful as question generators or negative controls.
Adapter/control iters may be useful for chart/readout controls, not root substrate.

## Iter Ledger

| iter | class | rebuild role | main blockers/caveats |
|---:|---|---|---|
| 283 | aligned_candidate | candidate_source_baseline_only_receipt_boundary_invalid | Pauli_Bloch_mentioned_as_disclaimer_or_representation_note; grok_sim_result_uses_formal_scout_classification; grok_sim_result_mentions_formal_scout_claim_ceiling |
| 284 | aligned_candidate | candidate_source_baseline_only_receipt_boundary_invalid | Pauli_Bloch_mentioned_as_disclaimer_or_representation_note; grok_sim_result_uses_formal_scout_classification; grok_sim_result_mentions_formal_scout_claim_ceiling |
| 285 | aligned_candidate | candidate_source_baseline_only_receipt_boundary_invalid | Pauli_Bloch_mentioned_as_disclaimer_or_representation_note; grok_sim_result_uses_formal_scout_classification; grok_sim_result_mentions_formal_scout_claim_ceiling |
| 286 | aligned_candidate | candidate_source_baseline_only_receipt_boundary_invalid | Pauli_Bloch_mentioned_as_disclaimer_or_representation_note; grok_sim_result_uses_formal_scout_classification; grok_sim_result_mentions_formal_scout_claim_ceiling |
| 287 | adapter_control | adapter_or_negative_control_only | Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture; quimb_declared_decorative_or_fallback_only; PEPS_surface_is_measured_through_Pauli_Bloch_adapter |
| 288 | adapter_control | adapter_or_negative_control_only | Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture; PEPS_surface_is_measured_through_Pauli_Bloch_adapter; grok_sim_result_uses_formal_scout_classification |
| 289 | adapter_control | adapter_or_negative_control_only | Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture; PEPS_surface_is_measured_through_Pauli_Bloch_adapter; grok_sim_result_uses_formal_scout_classification |
| 290 | aligned_candidate | candidate_source_baseline_only_receipt_boundary_invalid | Pauli_Bloch_mentioned_as_disclaimer_or_representation_note; grok_sim_result_uses_formal_scout_classification; grok_sim_result_mentions_formal_scout_claim_ceiling |
| 291 | aligned_candidate | candidate_source_baseline_only_receipt_boundary_invalid | Pauli_Bloch_mentioned_as_disclaimer_or_representation_note; grok_sim_result_uses_formal_scout_classification; grok_sim_result_mentions_formal_scout_claim_ceiling |
| 292 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; dense_numpy_density_or_kraus_stack_without_tensor_carrier; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture |
| 293 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; dense_numpy_density_or_kraus_stack_without_tensor_carrier; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture |
| 294 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; dense_numpy_density_or_kraus_stack_without_tensor_carrier; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture |
| 295 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; dense_numpy_density_or_kraus_stack_without_tensor_carrier; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture |
| 296 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; dense_numpy_density_or_kraus_stack_without_tensor_carrier; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture |
| 297 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture; grok_sim_result_uses_formal_scout_classification |
| 298 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture; grok_sim_result_uses_formal_scout_classification |
| 299 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture; grok_sim_result_uses_formal_scout_classification |
| 300 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture; grok_sim_result_uses_formal_scout_classification |
| 301 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture; PEPS_surface_is_measured_through_Pauli_Bloch_adapter |
| 302 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture; PEPS_surface_is_measured_through_Pauli_Bloch_adapter |
| 303 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture; PEPS_surface_is_measured_through_Pauli_Bloch_adapter |
| 304 | hard_block | question_generator_only | numpy_or_scipy_declared_load_bearing; Pauli_Bloch_or_cartesian_chart_used_as_code_primitive; numpy_present_as_support_or_fixture; PEPS_surface_is_measured_through_Pauli_Bloch_adapter |
| 305 | hard_block | question_generator_only | torch_autograd_severed_by_dot_numpy_conversion; Pauli_Bloch_mentioned_as_disclaimer_or_representation_note; numpy_present_as_support_or_fixture |
| 306a | aligned_candidate | candidate_source_baseline_only | Pauli_Bloch_mentioned_as_disclaimer_or_representation_note |
| 306a2 | aligned_candidate | candidate_source_baseline_only | torch_present; quaternion_language_or_ops_present |
| 306a3 | aligned_candidate | candidate_source_baseline_only | Pauli_Bloch_mentioned_as_disclaimer_or_representation_note |
| 306a4 | aligned_candidate | candidate_source_baseline_only | torch_present; quaternion_language_or_ops_present |
| 306a5 | aligned_candidate | candidate_source_baseline_only | torch_present; quaternion_language_or_ops_present |
| 306a6 | aligned_candidate | candidate_source_baseline_only | torch_present; quaternion_language_or_ops_present |
| 307 | aligned_candidate | candidate_source_baseline_only | Pauli_Bloch_mentioned_as_disclaimer_or_representation_note |
| 308 | aligned_candidate | candidate_source_baseline_only | torch_present; quaternion_language_or_ops_present |
| 309 | aligned_candidate | candidate_source_baseline_only | torch_present; quaternion_language_or_ops_present |
| 310 | aligned_candidate | candidate_source_baseline_only | torch_present; quaternion_language_or_ops_present |
| 311 | aligned_candidate | candidate_source_baseline_only | torch_present; quaternion_language_or_ops_present |

## Forward Rule

- New grok_sim substrate rebuilds should be PyTorch-native and spinor/quaternion-first.
- NumPy/SciPy may not be load-bearing for nonclassical root-manifold claims.
- Pauli, Bloch, and Cartesian d=2 charts are adapter/control surfaces only.
- PEPS/PEPS3D claims must state whether they perform actual tensor-network contraction or only full-state/product fixtures.
- Axis0 and flux claims must stay sidequest-local until independently rebuilt by formal sims.

Receipt: `results/grok_sim_substrate_violation_gate_20260524_results.json`
