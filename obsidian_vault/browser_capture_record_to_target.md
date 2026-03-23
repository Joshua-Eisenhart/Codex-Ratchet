---
id: "A2_3::SOURCE_MAP_PASS::browser_capture_record_to_target::de5257c6777117d5"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# browser_capture_record_to_target
**Node ID:** `A2_3::SOURCE_MAP_PASS::browser_capture_record_to_target::de5257c6777117d5`

## Description
Conversion step from an observed record to a target packet. Emits READY only if COMPOSER_READY_OBSERVED was YES and all other location fields are present.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **EXCLUDES** → [[derived_indices_browser_codex_thread_capture_record_temp]]
- **EXCLUDES** → [[v3_spec_55_browser_capture_record_to_target]]
- **EXCLUDES** → [[browser_codex_thread_capture_record]]
- **EXCLUDES** → [[capture_record_invalid_for_wrapper_json]]
- **EXCLUDES** → [[codex_thread_launch_surface_capture_record_json]]
- **EXCLUDES** → [[codex_browser_launch_from_capture_record__result_j]]
- **EXCLUDES** → [[codex_thread_launch_surface_capture_record__valida]]
- **EXCLUDES** → [[create_browser_codex_thread_capture_record_py]]
- **EXCLUDES** → [[create_browser_target_from_capture_record_py]]
- **EXCLUDES** → [[create_codex_thread_launch_surface_capture_record_]]
- **EXCLUDES** → [[browser_codex_thread_capture_record_template_v1_js]]
- **DEPENDS_ON** → [[packet]]
- **RELATED_TO** → [[browser_codex_thread_target_capture]]

## Inward Relations
- [[55_BROWSER_CAPTURE_RECORD_TO_TARGET__v1.md]] → **SOURCE_MAP_PASS**
- [[v3_spec_55_browser_capture_record_to_target]] → **DEPENDS_ON**
