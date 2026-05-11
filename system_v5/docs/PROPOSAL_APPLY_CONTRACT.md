# Proposal Apply Contract

Generated proposal reports are review surfaces, not source-of-truth repairs.

Inputs:

- `system_v5/ops/c1_classification_proposals.json`
- `system_v5/ops/c4_divergence_log_proposals.json`
- `system_v5/ops/c6_loadbearing_report.json`
- `system_v5/ops/proposal_apply_preview.json`

Rules:

- Reports must be regenerated before review if `scripts/wizard_v4_2_runtime_audit.py` marks `ops_reports_freshness.ok=false`.
- `proposal_apply_preview.json` is the owner queue. Each `action_item` needs explicit owner review before source edits.
- Dry-run reports may propose edits, but they must not mutate sim files.
- Applied means the relevant sim file is edited, the exact proposal row is cited, and a receipt is written beside the review surface or into the canonical result surface.
- C6 rows in `inconclusive_needs_owner` cannot be auto-applied. They require a human or route-owner decision.
- C6 rows in `genuinely_load_bearing_so_promote_to_canonical_candidate` are candidates only; promotion still needs the normal sim contract and admission gates.

Stop conditions:

- Do not apply proposals while the global queue is active on the same files.
- Do not use proposal application to make full-repo lint green by erasing uncertainty.
- Do not classify a bridge or scientific promotion from proposal metadata alone.
