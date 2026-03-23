# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / SOURCE REDUCTION MAP
Batch: `BATCH_systemv3_active_lineage_integrity_audit__v1`
Extraction mode: `ACTIVE_SYSTEMV3_LINEAGE_INTEGRITY_AUDIT_PASS`
Date: 2026-03-09

## Scope
- bounded audit over the completed `BATCH_systemv3_active_*` chain
- purpose:
  - verify packet completeness
  - preserve reduction lineage
  - preserve manifest-schema differences
  - restate safe reuse limits for the operator-facing reductions

## Source Set
- ledger surface:
  - `a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- active-batch manifest surfaces:
  - all `14` `BATCH_systemv3_active_*` `MANIFEST.json` files
- reduction support surfaces:
  - `BATCH_systemv3_active_crossbatch_a2mid_reduction__v1/A2_3_DISTILLATES__v1.md`
  - `BATCH_systemv3_active_crossbatch_a2mid_reduction__v1/TENSION_MAP__v1.md`
  - `BATCH_systemv3_active_operator_kernel_capsule__v1/A2_3_DISTILLATES__v1.md`
  - `BATCH_systemv3_active_operator_kernel_capsule__v1/TENSION_MAP__v1.md`
  - `BATCH_systemv3_active_operator_boot_card__v1/A2_3_DISTILLATES__v1.md`
  - `BATCH_systemv3_active_operator_boot_card__v1/TENSION_MAP__v1.md`

## Membership By Function
- ledger verification surfaces: `1`
- manifest audit surfaces: `14`
- reduction tension and distillate support surfaces: `6`
- total parent artifacts read for this audit: `21`

## Notes
- no raw `system_v3` sources were reopened
- no active-source coverage was extended
- this packet audits the completed active-system intake chain rather than replacing any batch inside it
