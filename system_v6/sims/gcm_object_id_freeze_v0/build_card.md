# Build Card - gcm_object_id_freeze_v0

Status: ladder step 2 data packet that freezes the IDs future nested packets attach to.
Claim ceiling: `scratch_diagnostic`; ID registry for the first candidate substrate; carrier-and-pins-relative; not THE manifold.
Write scope: `system_v6/sims/gcm_object_id_freeze_v0/` and `scripts/gcm_substrate_check.py` only.
Git boundary: NO git add/commit.

## Authority

Read-first authority:

1. `system_v6/sims/gcm_constraint_carve_v1/audit_verdict.md`: twice-audited carve with second-pass PASS verdict; consume by hash.
2. `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_results.json`: audited carve substrate data.
3. `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_envelope_results.json`: audited three-engine envelope.
4. `system_v6/receipts/gcm_layer_stack_reference_20260612.md`: standing ladder; step 2 freezes `gcm_object_id`, `survivor_id`, `quotient_class_id`, and `candidate_region_id`.
5. `system_v6/receipts/full_proper_audit_synthesis_20260612.md` and `system_v6/receipts/postmortem_forensic_codex1_20260612.md`: substrate-first doctrine and consumptive-object rule.
6. `system_v6/receipts/audit_standards_codex_v1.md`: standards codex; G.2a idempotency-from-birth.

## Packet Contract

The builder emits one frozen registry JSON:

- `gcm_object_id`: content hash over the carve's pinned spec: carrier `S`, active C1-C3 predicate hashes, probe family, and survivor set.
- `survivor_id`: 16 stable content-derived IDs, one per audited carve survivor.
- `quotient_class_id`: 8 stable content-derived IDs, each with member survivor IDs.
- `candidate_region_id`: stable IDs for the carved components from the post-carve structure read-off.

The registry is the attachment surface for future nested packets. A nested packet cites the `gcm_object_id` and maps its objects to frozen `survivor_id`, `quotient_class_id`, and `candidate_region_id` values. It does not invent a new carrier and then call it manifold-compatible.

## Staleness Tooth

The registry embeds source and result hashes for the audited carve. The shared consumer helper is `scripts/gcm_substrate_check.py` and exports `gcm_substrate_check(payload)`.

That helper fails when:

- the payload cites a different `gcm_object_id`;
- any embedded carve source/result hash no longer matches the carve packet on disk;
- the payload cites an unknown survivor, quotient class, or candidate region ID.

## G.2a Boundary

G.2a is binding from birth. The packet-local validator delegates audit verdict handling to `scripts/builder_audit_boundary.py` through `gcm_object_id_freeze_v0_boundary.py`; it must not hard-code permanent absence of `audit_verdict.md`.
