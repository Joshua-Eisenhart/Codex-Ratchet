# Independent Audit Verdict - gcm_object_id_freeze_v0 + scripts/gcm_substrate_check.py

audit_mode: independent fresh audit; live repo read-only except this file
freshness_tier: TIER-2 results-available with independent recomputation and scratch mutation controls
auditor: Codex controller/local-tools audit
audit_date: 2026-06-12
route_truth: partial Wizard v4.2 only; controller/local-tools audit, no full parent/child subagent topology claimed
standards_codex: system_v6/receipts/audit_standards_codex_v1.md
binding_references: system_v6/receipts/gcm_layer_stack_reference_20260612.md; system_v6/receipts/full_proper_audit_synthesis_20260612.md

Bottom line: VERDICT = PASS FOR THE ID FREEZE DATA, FAIL AS THE SUBSTRATE-FIRST ENFORCEMENT CORE UNTIL HELPER TEETH ARE REPAIRED.

The frozen registry data recomputes: `gcm_object_id = gcmobj_a40e54e13cec01466c9d675028b3574b`, `pinned_spec_sha256 = a40e54e13cec01466c9d675028b3574b29263ce3179bea8768970ac490f8245c`, 16 survivor IDs, 8 quotient-class IDs, and 6 candidate-region IDs all match the registry. A scratch content flip of one survivor changes the `gcm_object_id` and all derived survivor/class/region ID sets. The registry body hash `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed` matches.

But `scripts/gcm_substrate_check.py` is not yet strong enough to be the enforcement core. Two bypass controls pass when they should fail:

1. A payload with only `gcm_object_id` and no survivor/class/region lineage returns `ok: true`.
2. A forged alternate registry passed via `registry_path`, with `registry_body_sha256` removed and a forged `gcm_object_id`, returns `ok: true`.

Accepted claim ceiling for the data packet: `scratch_diagnostic_id_registry_first_candidate_substrate_carrier_and_pins_relative_not_THE_manifold`. No promotion, no formal admission, no terrain-atlas admission, no axis/engine/physics claim, and no "THE manifold" claim.

## Binding Standard

The layer-stack reference makes this exact rung step 2: after the carve passes, freeze `gcm_object_id`, `survivor_id`, `quotient_class_id`, and `candidate_region_id` before attaching base geometry. It also defines nesting as the same `gcm_object_id` plus survivor/class/region lineage, lower-to-upper maps, removal/quotient controls, and induced geometry recomputed after constraints (`system_v6/receipts/gcm_layer_stack_reference_20260612.md:45-59`).

The substrate-first doctrine says terrain/stage/engine/axis packets must consume a current `gcm_object_id` and instantiate within the live object, or their validation fails (`system_v6/receipts/full_proper_audit_synthesis_20260612.md:66-72`). The carve prerequisite is satisfied by the second-pass carve audit: `gcm_constraint_carve_v1` passes as the first real candidate substrate at scratch, carrier-and-pins-relative strength, with the freeze unblocked (`system_v6/sims/gcm_constraint_carve_v1/audit_verdict.md:304-320`, `:413-420`).

G.2a is the right boundary: new packet validators must delegate audit verdict handling to `scripts/builder_audit_boundary.py`, not hard-code permanent absence of `audit_verdict.md` (`system_v6/receipts/audit_standards_codex_v1.md:170-177`).

## Positive Results

- Independent derivation matched the registry: `gcmobj_a40e54e13cec01466c9d675028b3574b`.
- `registry_body_sha256` recomputed cleanly.
- Every `carve_hashes` row and every `source_locks` row matched disk.
- Registry rebuild matched the checked-in registry exactly; packet validator returned no errors.
- Packet tests passed: `3 passed`.
- Stale-carve-hash scratch control failed with `carve hash drift` and body hash mismatch.
- Unknown survivor ID scratch control failed with `unknown survivor_id`.
- Candidate regions are downstream-read from the carve's `post_carve_terrain_readout.quotient_components`, matching `[["Q0"], ["Q1", "Q6"], ["Q2"], ["Q3", "Q4"], ["Q5"], ["Q7"]]`.
- G.2a shape passes: the validator uses the packet boundary helper rather than a permanent no-audit-verdict absence check (`system_v6/sims/gcm_object_id_freeze_v0/validate_gcm_object_id_freeze_v0.py:109-125`).

Relevant implementation facts:

- ID derivation uses canonical JSON and stable SHA-256 IDs (`gcm_object_id_freeze_v0.py:65-70`, `:111-112`).
- The pinned spec includes S, C, probe family, and survivor set, and `gcm_object_id` is the 32-hex prefix over that spec (`gcm_object_id_freeze_v0.py:189-218`).
- Survivor, quotient-class, and candidate-region IDs are content-derived and include the `gcm_object_id` (`gcm_object_id_freeze_v0.py:115-186`).
- The registry records `gcm_object_id`, its rule, lineage contract, body hash, and source locks (`results/gcm_object_id_freeze_v0_registry.json:568-584`).

## Findings

### BLOCKER-1 - Object-only payload passes without frozen lineage

`gcm_substrate_check` documents survivor/class/region IDs and `object_maps` as optional (`scripts/gcm_substrate_check.py:69-76`). It collects cited IDs only if present and then only checks the values it sees (`scripts/gcm_substrate_check.py:44-66`, `:114-119`). My scratch control:

```json
{"gcm_lineage": {"gcm_object_id": "gcmobj_a40e54e13cec01466c9d675028b3574b"}}
```

returned:

```json
{"ok": true, "errors": []}
```

That is too weak for the attachment surface. A downstream packet can pass without mapping any object to `survivor_id`, `quotient_class_id`, or `candidate_region_id`, even though the registry's own lineage contract says a nested packet maps objects to those IDs (`results/gcm_object_id_freeze_v0_registry.json:570-573`).

Required repair: enforce at least one concrete frozen lineage citation for production consumption, and ideally require object-map rows to include the appropriate survivor/class/region ID set declared by the consumer's layer coordinate. Object-id-only should be a separate lightweight existence check, not `gcm_substrate_check` success.

### BLOCKER-2 - Forged alternate registry can pass if body hash is absent

The helper accepts arbitrary `registry_path` (`scripts/gcm_substrate_check.py:69-85`) and only verifies `registry_body_sha256` if the field exists (`scripts/gcm_substrate_check.py:106-112`). The CLI also exposes `--registry` (`scripts/gcm_substrate_check.py:132-136`).

My scratch control copied the registry, changed `gcm_object_id` to `gcmobj_forged_registry_without_body_hash`, removed `registry_body_sha256`, and cited the forged ID. It returned:

```json
{"ok": true, "errors": [], "gcm_object_id": "gcmobj_forged_registry_without_body_hash"}
```

That is an enforcement-core bypass. The helper consumed a registry, but not the frozen registry.

Required repair: make `registry_body_sha256` mandatory; fail if missing. For production mode, reject non-default registry paths or require a pinned expected registry-body hash passed by the caller and equal to the canonical freeze registry hash. Keep alternate registry paths only for explicit audit/test mode that cannot be mistaken for production validation.

### CAVEAT-1 - Parent carve ceiling is carried safely but not verbatim as data

The registry carries a safe packet ceiling (`scratch_diagnostic_id_registry_first_candidate_substrate_carrier_and_pins_relative_not_THE_manifold`), safe flags, and disallowed claims (`results/gcm_object_id_freeze_v0_registry.json:73-89`). The parent carve result's exact ceiling is `first_carve_candidate_v1_only_carrier_and_pins_relative` (`system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_results.json:387-388`).

That is semantically safe, but not verbatim. If the standard for this packet is "carry the carve's ceilings verbatim," add explicit parent fields such as:

```json
"parent_carve_classification": "scratch_diagnostic",
"parent_carve_claim_ceiling": "first_carve_candidate_v1_only_carrier_and_pins_relative",
"parent_carve_promotion_allowed": false,
"parent_carve_formal_admission_allowed": false
```

## Consumption Rule Citation Form

Until the helper is repaired, citations should use this stricter form and downstream validators should enforce it directly:

```yaml
gcm_lineage:
  gcm_object_id: gcmobj_a40e54e13cec01466c9d675028b3574b
  registry_path: system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json
  registry_body_sha256: 0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed
  parent_carve_result_sha256: ca6ae0277e4a5c77044b1075626262e6bfdab4c99f818e85abc123322f74b756
  parent_carve_audit_verdict_sha256: c85f5f544d2f849e53a240f10d1c1e0f3d5ca8fadd6838288f61122a03fc2d8e
  object_maps:
    - local_object_id: <packet-local object id>
      survivor_id: <one frozen surv_... id when applicable>
      quotient_class_id: <one frozen qcls_... id when applicable>
      candidate_region_id: <one frozen creg_... id when applicable>
      relation: <restricted_to | quotient_of | region_readout_of | lifted_from>
```

Minimum production rule: a future terrain/stage/engine/axis/nested-geometry packet must cite the canonical registry body hash and at least one concrete frozen lineage ID appropriate to the packet. `gcm_object_id` alone is not enough.

## Commands Run

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# independent canonical recomputation + scratch mutation controls
PY
```

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# common.build_registry equality + validator.validate_payload
PY
```

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/gcm_object_id_freeze_v0/tests/test_gcm_object_id_freeze_v0.py
```

```text
git status --short -- system_v6/sims/gcm_object_id_freeze_v0 scripts/gcm_substrate_check.py .pytest_cache
```

No `git add` or commit was run.
