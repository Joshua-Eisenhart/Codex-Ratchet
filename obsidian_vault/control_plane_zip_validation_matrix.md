---
id: "A2_3::SOURCE_MAP_PASS::control_plane_zip_validation_matrix::e9118c621916e85d"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# control_plane_zip_validation_matrix
**Node ID:** `A2_3::SOURCE_MAP_PASS::control_plane_zip_validation_matrix::e9118c621916e85d`

## Description
ZIP_VALIDATION_MATRIX.md (2065B):  # ZIP_VALIDATION_MATRIX  This matrix defines deterministic validation outcomes and reject tags for ZIP_PROTOCOL_v2.  ## Outcomes - `OK`: ZIP is valid and accepted. - `PARK`: ZIP is structurally valid but deferred due to sequencing/replay preconditions. - `REJECT`: ZIP is invalid under protocol.  ##

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[zip_protocol_v2]]
- **DEPENDS_ON** → [[zip_validation_matrix]]
- **DEPENDS_ON** → [[ZIP_PROTOCOL_V2]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_zip_validation_matrix]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_zip_validation_matrix]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_zip_validation_matrix]]

## Inward Relations
- [[README.md]] → **SOURCE_MAP_PASS**
