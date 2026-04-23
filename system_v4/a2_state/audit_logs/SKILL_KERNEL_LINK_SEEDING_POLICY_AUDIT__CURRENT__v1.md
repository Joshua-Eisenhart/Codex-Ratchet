# Skill Kernel Link Seeding Policy Audit

- generated_utc: `2026-03-21T23:46:30Z`
- status: `ok`
- audit_only: `True`
- do_not_promote: `True`
- allow_auto_seeding_now: `False`

## Forbidden Now
- Do not seed SKILL -> KERNEL_CONCEPT links from source_path, source_type, skill_type, status, provenance, tags, applicable_trust_zones, applicable_graphs, inputs, outputs, adapters, or related_skills alone.
- Do not seed SKILL -> KERNEL_CONCEPT links from inferred SKILL -> SKILL relations such as RELATED_TO or SKILL_FOLLOWS.
- Do not seed SKILL -> KERNEL_CONCEPT links from free-text descriptions or SKILL.md prose without an owner-bound concept-id field.

## Future Minimally Sufficient Evidence
- An explicit owner-bound concept identity field on the registry row and mirrored skill node properties, such as concept_refs or kernel_concept_ids.
- A bounded audited packet or report that names skill_id, target concept ids, and relation semantics, with repo-held provenance.
- A durable runtime witness or dispatch record that ties skill execution to explicit concept ids rather than only to phase or graph-family metadata.

## Recommended Next Actions
- Keep auto-seeding fail-closed now; current registry rows and graph nodes do not carry owner-bound concept identity on the skill side.
- Treat the current skill island as metadata-only for kernel linkage purposes, even though it is graph-complete as a skill inventory.
- Move next to clifford-edge-semantics-audit for graph-side edge semantics, while keeping run_real_ratchet dispatch debt in watch-only mode.

## Issues
- none
