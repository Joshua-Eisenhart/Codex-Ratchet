# STAGE_3_TEMPLATE_AND_SCHEMA_GATE_FLOW__v1
Status: DRAFT / NONCANON
Date: 2026-03-03
Owner: Stage-3 packaging flow

## Purpose
Provide one concrete Stage-3 template family and executable schema-gate validation flow.

## Concrete Bundle
Template root:
- `work/zip_job_templates/A2_A1_RATCHET_FUEL_MINT__BUNDLE_TEMPLATE_v1`

This bundle wires:
1. A2 extraction and invariant-lock outputs.
2. A2 and A1 brain update packet JSON outputs.
3. Ratchet fuel candidate packet JSON output.
4. Fail-closed Stage-2 schema validation report.

## Validation Flow
1. Template structural validation:
```text
python3 system_v3/tools/zip_job_bundle_validator.py \
  --bundle-root work/zip_job_templates/A2_A1_RATCHET_FUEL_MINT__BUNDLE_TEMPLATE_v1 \
  --mode template
```

2. Stage-2 schema gate:
```text
python3 system_v3/tools/stage2_schema_gate.py \
  --bundle-root work/zip_job_templates/A2_A1_RATCHET_FUEL_MINT__BUNDLE_TEMPLATE_v1
```

## Required Schema Bindings
- `meta/STAGE_2_SCHEMA_BINDINGS__v1.json`

Bound outputs:
1. `A2_BRAIN_UPDATE_PACKET_STAGE2...json`
2. `A1_BRAIN_ROSETTA_UPDATE_PACKET_STAGE2...json`
3. `RATCHET_FUEL_CANDIDATE_PACKET_STAGE2...json`

## Failure Policy
- Missing required output => FAIL.
- Missing schema file => FAIL.
- JSON parse failure => FAIL.
- Schema violation => FAIL.
- No silent downgrade and no auto-correction.

