# Expanded Quarantine Surface Classification - 2026-05-23

Status: first-pass surface classification. This is cleanup control, not science.

Source inventory:

`system_v5/ops/EXPANDED_QUARANTINE_FULL_INVENTORY_20260523.json`

## Classification Table

| Surface | Count | Status | Reason | Next action |
|---|---:|---|---|---|
| Recovery-control docs | 11 | `recovery_control_artifact` | These document the breach, process stop, quarantine, and independent-rerun rule. | Keep untrusted as process-control until reviewed; do not treat as sim evidence. |
| `system_v5/docs/MULTIMODEL_PROPOSAL_SPLIT.md` | 1 tracked dirty | `recovery_rule_patch` | Boundary rule was tightened to ban cross-lane result evidence. | Candidate to keep after review. |
| Readiness / estate indexes | 4 | `restored_to_HEAD` | They had registered contaminated result/source surfaces. | Rebuild later from trusted allowlist only. |
| Formal-scout README and classifiers | 4 | `restored_to_HEAD` | They wired the mixed wave into canonical summaries/classifier logic. | Rebuild only after independent reruns. |
| Tracked formal result receipt | 1 | `restored_to_HEAD` | `su2_unit_quaternion_hopf_holonomy_order_probe_results.json` is a result receipt and should not travel with docs. | Verify separately if needed. |
| `system_v5/docs/00_manifest.md`, `CURRENT_DOCS_MAP.md` | 2 | `restored_to_HEAD` | They were touched during the live expansion and could point to quarantine docs. | Re-edit only after cleanup packet is reviewed. |
| Untracked formal-scout sims | 0 current | `archived_and_removed` | 42 generated files were archived outside the repo and removed. | Restore only for manual inspection, not evidence. |
| Recent untracked/ignored formal-scout result JSONs | 0 current | `archived_and_removed` | 95 generated receipts were archived outside the repo and removed. | Restore only for manual inspection, not validators/indexes. |
| `system_v5/ops/external_audits/` untracked 2026-05-23 packets | 0 current | `archived_and_removed` | 53 model-audit packet files were archived outside the repo and removed. | Restore only for manual inspection; never cite as proof. |
| `system_v5/ops/clean_rebuild_20260523/` | 17 | `manual_review_independent_rerun_candidate` | Runnable clean-rebuild scout scripts and receipts, but explicitly not canonical formal-scout evidence. | Keep quarantined; rerun independently from clean baseline if useful. |
| `system_v5/ops/constraint_audit_20260523/` | 41 | `manual_review_process_control_candidate_transcripts_archived` | Core process-control docs, local candidate-gate scripts, registries, validator, and results remain; external transcripts/prompts were archived. | Keep quarantined for manual review; do not treat contained sims/results as formal receipts. |
| `system_v5/docs/system_levels_20260523/` | 18 | `manual_review_non_evidence_docs_with_receipt_anchors_quarantined` | System-level docs may be conceptual/spec support but had stale receipt/pass anchors. | Review against source docs; current receipt-anchor arrays are empty pending clean independent reruns. |
| `system_v5/ops/legacy_high_entropy_intake_20260523/` | 0 current | `archived_and_removed` | 388 chunk files were archived outside the repo and removed. | Restore only for manual reference. |
| Top-level QIT/physics/holodeck docs and JSON | 0 current | `archived_and_removed` | 8 generated conclusion-like docs/JSON were archived outside the repo and removed. | Restore only for manual inspection; do not wire into formal indexes. |

## Recovery-Control Docs

Current recovery-control set:

```text
system_v5/ops/CROSS_LANE_SIM_INDEPENDENCE_RESET_20260523.md
system_v5/ops/FORMAL_GROK_BOUNDARY_DAMAGE_AUDIT_20260523.md
system_v5/ops/FORMAL_GROK_BOUNDARY_QUARANTINE_MANIFEST_20260523.json
system_v5/ops/CLAUDE_SELF_VIOLATION_INVENTORY_20260523.md
system_v5/ops/FORMAL_GROK_SIM_REDO_PLAN_20260523.md
system_v5/ops/LIVE_CLAUDE_PROCESS_STOP_AND_EXPANDED_QUARANTINE_20260523.md
system_v5/ops/EXPANDED_QUARANTINE_FULL_INVENTORY_20260523.json
system_v5/ops/EXPANDED_QUARANTINE_INVENTORY_SUMMARY_20260523.md
system_v5/ops/EXPANDED_QUARANTINE_SURFACE_CLASSIFICATION_20260523.md
system_v5/ops/EXPANDED_QUARANTINE_ACTION_MANIFEST_20260523.json
system_v5/ops/EXPANDED_QUARANTINE_ACTION_PLAN_20260523.md
```

These should be reviewed as a single cleanup packet. They should not be mixed
with formal scout source, result estate, or scientific docs.

## Hard Blocks Before More Formal Science

1. No forward formal-scout runs.
2. No readiness or estate index regeneration from the current result estate.
3. No validator run that consumes restored quarantined formal results.
4. No cross-lane comparison as evidence.
5. No staging mixed buckets together.
6. No background writer processes in this repo during inventory or cleanup.

## First Safe Cleanup Slice

The first cleanup slice restored contaminated tracked canonical files to `HEAD`.
It was not a scientific commit and did not stage anything.

The second cleanup slice archived and removed the untracked formal-scout
source/result quarantine bucket. It was not a scientific commit and did not
stage anything.

The third cleanup slice archived and removed the legacy high-entropy intake
chunks. It was not a scientific commit and did not stage anything.

The fourth cleanup slice archived and removed the untracked external-audit
packet bucket. It was not a scientific commit and did not stage anything.

The fifth cleanup slice archived and removed the top-level generated ops
docs/JSON bucket. It also removed local `.DS_Store` and `__pycache__` noise
from remaining quarantine folders. It was not a scientific commit and did not
stage anything.

The sixth cleanup slice quarantined system-level receipt anchors and marked older
damage/stop/self-inventory/redo docs as historical snapshots superseded by the
expanded quarantine inventory. It was not a scientific commit and did not stage
anything.

The seventh cleanup slice archived and removed constraint-audit external
transcripts and prompt drafts, leaving the core process-control packet in place.
It was not a scientific commit and did not stage anything.

The next slice should manually review the remaining quarantine surfaces:
clean-rebuild, constraint-audit, system-level docs, and the recovery-rule patch.
Canonical indexes should be regenerated only from a trusted allowlist after
quarantine classification.
