---
id: "A2_2::REFINED::content_redundancy_lint::0bb2761bf47387ae"
type: "KERNEL_CONCEPT"
layer: "A2_MID_REFINEMENT"
authority: "CROSS_VALIDATED"
---

# content_redundancy_lint
**Node ID:** `A2_2::REFINED::content_redundancy_lint::0bb2761bf47387ae`

## Description
[AUDITED] Semantic near-duplicate detection across spec docs. 4 dimensions: duplicate headings (exact normalized), near-duplicate paragraphs (cosine >= 0.85), repeated requirement prose across non-owners, overlapping section intent (cosine >= 0.70). Output: content_redundancy_report.json.

## Outward Relations
- **STRUCTURALLY_RELATED** → [[v3_spec_13_content_redundancy_lint_spec]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_13_content_redundancy_lint_spe]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_13_content_redundancy_lint_spe]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_13_content_redundancy_lint_spe]]
- **STRUCTURALLY_RELATED** → [[v3_tools_content_redundancy_lint]]
- **STRUCTURALLY_RELATED** → [[13_content_redundancy_lint_spec]]
- **STRUCTURALLY_RELATED** → [[content_redundancy_lint_py]]
- **DEPENDS_ON** → [[output]]
- **STRUCTURALLY_RELATED** → [[v3_spec_content_redundancy_report]]
- **STRUCTURALLY_RELATED** → [[content_redundancy_report_json]]
- **STRUCTURALLY_RELATED** → [[redundancy_and_drift_lint]]

## Inward Relations
- [[content_redundancy_lint]] → **REFINED_INTO**
- [[v3_spec_13_content_redundancy_lint_spec]] → **DEPENDS_ON**
- [[content_redundancy_report.json]] → **SOURCE_MAP**
