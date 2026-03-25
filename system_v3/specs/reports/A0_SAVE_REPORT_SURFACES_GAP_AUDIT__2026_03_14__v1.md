# A0_SAVE_REPORT_SURFACES_GAP_AUDIT__2026_03_14__v1
Status: NONCANON / AUDIT
Date: 2026-03-14

## Scope

Audit current tool/spec surface against:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/74_A0_SAVE_REPORT_SURFACES__v1.md`

Legacy witness:
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/BOOTPACKS/BOOTPACK_THREAD_S_v1.64.md`

Audited current surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/schemas`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_save_profile_zip.py`

## Findings

### 1. Required A0 save/report surfaces are mostly spec-only, not tool-backed

The required recovered surface family is:
- `PROJECT_SAVE_DOC`
- `AUDIT_PROJECT_SAVE_DOC_REPORT`
- `EXPORT_BLOCK_LINT_REPORT`
- `TAPE_SUMMARY_REPORT`
- `TERM_CHAIN_REPORT`
- `INSTRUMENTATION_REPORT`

Current tool inventory does not contain executable tools named for those surfaces.

Witness:
- tool inventory under `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools`
- schema inventory under `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/schemas`

Gap:
- the concepts exist in old bootpack and extracted reports
- they do not exist as first-class executable current tools

### 2. Current save tooling is ZIP-profile oriented, not report-surface oriented

Current save tooling focuses on building ZIP profiles and packet/run surfaces.

Witness:
- [build_save_profile_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/build_save_profile_zip.py#L198)

Gap:
- save packaging exists
- semantic save/report docs do not

### 3. No current schema set covers the recovered A0 save/report family

Current schema directory contains:
- A1/A2 update packet schemas
- fuel candidate schema
- ZIP manifest schema

It does not contain schemas for:
- `PROJECT_SAVE_DOC`
- `AUDIT_PROJECT_SAVE_DOC_REPORT`
- `EXPORT_BLOCK_LINT_REPORT`
- `TAPE_SUMMARY_REPORT`

Witness:
- schema inventory under `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/schemas`

Gap:
- tool and schema layers are both missing

## Exact patch targets

1. Add tool pair:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_project_save_doc.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_project_save_doc.py`

2. Add lint/summary tools:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_export_block_lint_report.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_tape_summary_report.py`

3. Add chain/instrumentation tools:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_term_chain_report.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_instrumentation_report.py`

4. Add schemas:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/schemas/PROJECT_SAVE_DOC_v1.schema.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/schemas/AUDIT_PROJECT_SAVE_DOC_REPORT_v1.schema.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/schemas/EXPORT_BLOCK_LINT_REPORT_v1.schema.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/schemas/TAPE_SUMMARY_REPORT_v1.schema.json`
