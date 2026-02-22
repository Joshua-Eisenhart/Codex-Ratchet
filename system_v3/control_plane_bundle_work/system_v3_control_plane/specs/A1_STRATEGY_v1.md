
# A1_STRATEGY v1

This specification defines the only admissible A1 strategy object to be transported in:
- `A1_TO_A0_STRATEGY_ZIP` as `A1_STRATEGY_v1.json`.

This is a **non-kernel** artifact. B never sees it.

NOTE: Outcome `PARK` is reserved exclusively for ZIP_PROTOCOL_v2 sequence-gap handling. A0 strategy admission MUST use deterministic accept/reject semantics and MUST NOT reuse ZIP `PARK`.

## 1. Canonical filename
- `A1_STRATEGY_v1.json`

## 2. Canonical JSON rules
The file MUST follow the canonical JSON rules defined by `ZIP_PROTOCOL_v2.md` (UTF-8, LF, sorted keys, stable separators, trailing LF).

## 3. Top-level schema

### Required fields (no extras allowed)
- `schema`: MUST equal `"A1_STRATEGY_v1"`
- `run_id`: string (MUST equal ZIP_HEADER.run_id)
- `sequence`: integer (MUST equal ZIP_HEADER.sequence)
- `strategy_id`: string (unique within run_id scope)
- `inputs`: object (see below)
- `budget`: object (see below)
- `diversity_budget`: object (see below)
- `targets`: array of proposal objects (>= 1)
- `alternatives`: array of proposal objects (>= 1)
- `self_audit`: object (see below)

Unknown top-level fields MUST cause A0 admission failure.

## 4. inputs object

Required:
- `a0_save_zip_sha256`: lowercase hex64 (sha256 of the A0_TO_A1_SAVE_ZIP this strategy was based on)
- `state_hash`: lowercase hex64 (state hash as referenced in the A0 save summary)
- `evidence_summary_hash`: lowercase hex64 (digest of SIM outcome summary referenced by A0 save)

If an input is not available, the value MUST be the empty string `""` and A0 MUST record admission downgrade/park outside the kernel path.

## 5. budget object (non-probabilistic)

Required integer fields:
- `max_targets`
- `max_alternatives`
- `max_total_items`
- `max_sim_requests`

Invariants:
- `len(targets) <= max_targets`
- `len(alternatives) <= max_alternatives`
- `len(targets) + len(alternatives) <= max_total_items`

## 6. diversity_budget object (structural, non-optimizing)

Purpose: prevent “fake wiggle” by requiring coverage across structural axes without probability/time/optimization.

Required fields:
- `axes`: array (>= 1)

Each axis entry:
- `axis_id`: string (e.g., `"operator_id"`, `"spec_kind"`, `"dependency_shape"`)
- `min_distinct_values`: integer >= 1

Interpretation:
- Across `targets ∪ alternatives`, the set of values observed for `axis_id` MUST have cardinality >= `min_distinct_values`.
- A0 may enforce this as a hard admission rule or as a deterministic “PARK until satisfied” gate (implementation choice; must be deterministic and documented by A0).

## 7. Proposal object

Each element in `targets` and `alternatives` MUST be:

Required fields:
- `proposal_id`: string (unique in this strategy)
- `proposal_class`: MUST be `"TARGET"` or `"ALTERNATIVE"`
- `spec_kind`: string (MUST be recognized by A0’s bootpack registry; A1 MUST NOT invent new kinds)
- `requires`: array of strings (dependency ids; may be empty)
- `fields`: array of field entries (may be empty)
- `asserts`: array of assert entries (may be empty)
- `operator_id`: string (must be in the operator enum defined by `A1_REPAIR_OPERATOR_MAPPING_v1.md`)
- `parent_proposal_id`: string or `""` (used for repair lineage)

### Field entry
- `field_id`: string
- `name`: string
- `value_kind`: string (A0-defined; must be recognized by A0)
- `value`: string

### Assert entry
- `assert_id`: string
- `token_class`: string (A0-defined; must be recognized by A0)
- `token`: string

## 8. self_audit object (required)

Required:
- `strategy_sha256`: lowercase hex64 (sha256 of canonical bytes of this JSON file)
- `target_count`: integer (must equal len(targets))
- `alternative_count`: integer (must equal len(alternatives))
- `operator_ids_used`: array of strings (deduplicated, sorted)
- `structural_digest`: lowercase hex64 (A0-recomputable digest over normalized proposal structure per `STRUCTURAL_DIGEST_v1.md`)

### strategy_sha256 computation rule (recursion-safe)

`self_audit.strategy_sha256` MUST be computed as:

sha256(canonical JSON bytes of the full strategy object
with `self_audit.strategy_sha256` temporarily set to empty string `""`)

Procedure:
1. Set `self_audit.strategy_sha256` = `""`.
2. Serialize strategy using canonical JSON rules (`ZIP_PROTOCOL_v2`).
3. Compute SHA-256 over those bytes.
4. Insert resulting lowercase hex64 into `self_audit.strategy_sha256`.

Validators MUST recompute and verify this hash.
If mismatch -> admission failure (A0-level deterministic failure).

## 9. Anti-fake constraints (hard)
A1_STRATEGY_v1 MUST NOT contain:
- probability/confidence fields
- embeddings
- hidden prompts
- raw transcripts

Forbidden keys anywhere in the JSON (case-sensitive):
- `confidence`
- `probability`
- `embedding`
- `hidden_prompt`
- `raw_text`

If present, A0 MUST reject strategy admission.

## 10. Minimal “real wiggle” gate (structural)
At least one alternative MUST be structurally distinct from all targets under A0’s structural_digest comparator.

Structural distinctness MUST be defined deterministically by A0 as:
- difference in `spec_kind` OR
- difference in dependency graph (`requires`) OR
- difference in `operator_id` OR
- difference in at least one `(field.name, field.value)` pair OR
- difference in at least one `(assert.token_class, assert.token)` pair

No probabilistic scoring permitted.


If this gate fails, A0 MUST deterministically REJECT strategy admission (A0-level), and MUST NOT compile any B-facing artifacts from the strategy.
