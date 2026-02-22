# A1_STRATEGY_v1

## Container
- Artifact format: JSON document on disk.
- Required top-level keys:
  - `strategy_id` (string)
  - `version` (string, must be `A1_STRATEGY_v1`)
  - `input_doc_refs` (array)
  - `intent` (string)
  - `candidate_families` (array)
  - `repair_rules` (object)
  - `stop_conditions` (object)
  - `budget` (object)
- Optional top-level key:
  - `rosetta_map` (object)

## Schema

### `input_doc_refs[]`
- required keys per item:
  - `path` (string)
  - `sha256` (64-char lowercase hex)

### `candidate_families[]`
- required keys per family:
  - `family_id` (string)
  - `purpose` (string)
  - `required_terms` (array[string])
  - `forbidden_terms` (array[string])
  - `candidate_templates` (array)
  - `expected_b_fences` (array[string])
  - `sim_hooks` (array)

### `candidate_templates[]`
- required keys per template:
  - `spec_id` (string)
  - `expected_kind` (string, must be `SIM_SPEC`)
  - `probe_id` (string)
  - `probe_kind` (string)
  - `probe_token` (string)
  - `requires_probe` (string)
  - `evidence_token` (string)
- optional key:
  - `assert_evidence_token` (string; if absent compiler sets to `evidence_token`)

### `sim_hooks[]`
- required keys per hook:
  - `sim_spec_id` (string)
  - `sim_id` (string)

### `repair_rules`
- map: `B_TAG -> ACTION`
- expected tags:
  - `UNDEFINED_TERM_USE`
  - `DERIVED_ONLY_PRIMITIVE_USE`
  - `PROBE_PRESSURE`
  - `MISSING_REQUIRED_PROBE`
  - `EVIDENCE_TOKEN_MISMATCH`
  - `SPEC_KIND_UNSUPPORTED`
- deterministic actions supported by A0 compiler:
  - `DROP_CANDIDATE`
  - `ADD_REQUIRED_PROBE`
  - `ALIGN_ASSERT_TO_DEF_FIELD`
  - `INJECT_PROBES`
  - `DROP_OR_REMAP_KIND`

### `stop_conditions`
- required keys:
  - `max_repair_attempts_per_step` (int >= 1)
  - `repeated_noop_limit` (int >= 1)
  - `repeated_schema_fail_limit` (int >= 1)

### `budget`
- required keys:
  - `max_new_terms_per_batch` (int >= 0)
  - `max_new_specs_per_batch` (int >= 1)
  - `max_graveyard_growth_per_n_cycles` (int >= 0)
  - `n_cycles` (int >= 1)
  - `probe_pressure_ratio` (number > 0)

## Determinism Contract
- Given `(canonical_state_snapshot_hash, strategy_json_bytes, compiler_version)`, A0 compiler must produce identical `EXPORT_BLOCK` bytes and identical compilation report bytes.
- `candidate_templates` are expanded in deterministic order:
  - family order by `family_id` ascending
  - template order by `spec_id` ascending
  - probe bootstrapping components-first by underscore segments

## Boundary Contract
- A1 may be nondeterministic before artifact creation.
- Once `A1_STRATEGY_v1` is persisted, A0/B/SIM processing is deterministic.
- A0 emits only `EXPORT_BLOCK v1` containers (no prose).
- B consumes strict containers only.
