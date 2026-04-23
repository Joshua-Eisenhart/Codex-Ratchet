# Survivor Kernel Bridge Backfill Audit

- generated_utc: `2026-03-21T23:43:58Z`
- status: `ok`
- audit_only: `True`
- do_not_promote: `True`
- authoritative_graph: `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
- allow_direct_kernel_backfill_now: `False`

## Survivor Source Classes
- `blank_source_concept_id`: `31`
- `live_kernel_already_linked`: `1`
- `live_nonkernel_already_linked::EXTRACTED_CONCEPT`: `34`
- `live_nonkernel_already_linked::REFINED_CONCEPT`: `12`

## Recommended Next Actions
- Do not run bulk direct survivor-to-kernel backfill under current truth unless a survivor resolves to a live KERNEL_CONCEPT without an existing ACCEPTED_FROM edge.
- Treat survivor links that already resolve to REFINED_CONCEPT or EXTRACTED_CONCEPT as evidence of concept-class layering, not as missing direct kernel edges.
- Return to skill-kernel-link-seeding-policy-audit after this slice so the skill island remains fail-closed while witness-side class layering is clarified.
- If survivor-side bridge strengthening continues later, add an explicit concept-class normalization or promotion policy before any broader kernel backfill claim.

## Issues
- none
