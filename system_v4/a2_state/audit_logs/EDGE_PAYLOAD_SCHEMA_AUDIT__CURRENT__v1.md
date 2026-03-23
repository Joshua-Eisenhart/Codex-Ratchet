# Edge Payload Schema Audit

- generated_utc: `2026-03-21T23:52:04Z`
- status: `ok`
- audit_only: `True`
- do_not_promote: `True`

## Schema Rows
### DEPENDS_ON
- required_carriers: `relation, source_id, target_id`
- optional_scalar_carriers: `none`
- optional_string_carriers: `link_type, pass, referenced_term`

### EXCLUDES
- required_carriers: `relation, source_id, target_id`
- optional_scalar_carriers: `shared_name_parts`
- optional_string_carriers: `link_type, reason`

### STRUCTURALLY_RELATED
- required_carriers: `relation, source_id, target_id`
- optional_scalar_carriers: `shared_components`
- optional_string_carriers: `link_type, nested_layer, reasoning`

### RELATED_TO
- required_carriers: `relation, source_id, target_id`
- optional_scalar_carriers: `shared_count`
- optional_string_carriers: `link_type`

## Recommended Next Actions
- Keep the schema sidecar-only and relation-scoped; do not write these payloads into canonical graph edges yet.
- Keep OVERLAPS and all skill-edge families outside the admitted schema scope.
- If this line continues, the next bounded step would be a read-only payload-schema probe over one admitted relation family, not a runtime mutation pass.

## Issues
- none
