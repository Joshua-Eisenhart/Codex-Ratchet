**Verdict:** APPLY

**Reasons:**
1.  **No Fake-Pass Risks:** The metadata inserts explicitly include `contract_metadata_repair='safe_repair_v1'` and `divergence_log_source='safe_repair_v1'`, providing clear provenance. `tool_manifest` only marks tools as `used=true` with direct call sites, preventing false positives.
2.  **No Evidence-Promotion Risks:** All actionable classification values are `classical_baseline` only, with zero canonical actions. Crucially, `divergence_log` entries explicitly state "classical-baseline metadata repair and explicitly says not promoted without reviewed canonical receipt," mitigating any risk of promoting unreviewed data as canonical scientific evidence.
3.  **No Process-Gate Risks:** The system correctly identifies and excludes `487 blocked plans` (e.g., `C1_canonical_needs_review`, `C1_classification_missing_needs_review`) from application. The `--apply` mechanism skips these until `C1` review is complete, demonstrating adherence to established process gates.

**Required Additional Checks:**
While the current unblocked repairs are safe to apply, ensure there is a clear, documented process for reviewing and addressing the `blocked plans`, especially those related to `C1_canonical_needs_review`, to eventually promote them to canonical status. This ensures the full metadata debt is systematically resolved.
Verdict: APPLY

**Reasons:**
1.  **No Fake-Pass Risks:** The dry-run explicitly tags all metadata inserts with `contract_metadata_repair='safe_repair_v1'` and `divergence_log_source='safe_repair_v1'`, ensuring clear auditability and preventing any misinterpretation of the repaired metadata as original or fully validated. The `tool_manifest` intelligently marks tools as `used=true` only when a direct call site is found, avoiding false claims for import-only tools.
2.  **No Evidence-Promotion Risks:** All actionable classification values are confined to `classical_baseline` only, with no promotions to "canonical actions." Crucially, `divergence_log` entries explicitly state that they represent "classical-baseline metadata repair and explicitly says not promoted without reviewed canonical receipt." This rigorous distinction prevents any unreviewed `classical_baseline` data from being inadvertently promoted as canonical scientific evidence.
3.  **No Process-Gate Risks:** The system demonstrates robust process-gate enforcement by actively excluding `487 blocked plans` (e.g., `C1_canonical_needs_review`, `C1_classification_missing_needs_review`) from the `--apply` operation. These blocked changes will only be applied once the `C1` review gate is satisfied, confirming that critical review processes are respected and not bypassed.

**Required Additional Checks:**
While applying these unblocked metadata repairs is acceptable, it is critical to establish and execute a clear, systematic process for addressing the `487 blocked plans`, particularly those requiring `C1_canonical_needs_review`. This follow-up ensures that the remaining metadata debt is systematically reviewed, validated, and eventually integrated to achieve full metadata health.
