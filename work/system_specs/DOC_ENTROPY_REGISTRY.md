# Doc Entropy Registry (what we processed, at what tier)

Status: NONCANON | Updated: 2026-02-18  
Rule: Registry entries are short. Use UNKNOWN rather than guessing.

Columns:

- **ID**
- **Path**
- **Tier** (E0/E1/E2/E3)
- **Role**
- **Hazards**
- **Derived artifacts (pointers)**

## Registry

| ID | Path | Tier | Role | Hazards | Derived artifacts (pointers) |
| --- | --- | --- | --- | --- | --- |
| R-A1-BOOT | `core_docs/a2 hand assembled docs/uploads/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md` | E0 | Canon thread topology + embedded bootpacks | High density; avoid synthesis drift | `work/rebaseline/BOOTPACK_THREAD_A1_v1.0__VERBATIM.md`, `work/rebaseline/BOUNDARY_QUOTES_A0_A1_A2.md` |
| R-A0-BOOT | `core_docs/a2 hand assembled docs/uploads/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md` | E0 | Embedded A0 bootpack | Output-format rigidity; avoid “helpful prose” drift | `work/rebaseline/BOOTPACK_THREAD_A0_v2.62__VERBATIM.md`, `work/system_specs/A0_CONTRACT.md` |
| R-B-BOOT | `core_docs/BOOTPACK_THREAD_B_v3.9.13.md` | E0 | Canon fence + container + term pipeline law | Internal inconsistencies possible; never “smooth” them | `work/system_specs/B_FENCES.md`, `work/system_specs/B_ACCEPTED_CONTAINERS.md`, `work/system_specs/JARGON_GATE.md` |
| R-ZIP | `core_docs/a2 hand assembled docs/uploads/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md` | E0 | ZIP protocol + text limits | Temptation to invent schema details | `work/system_specs/ZIP_JOB_SCHEMA.md` |
| R-ZIP-INDEX | `core_docs/a2_runtime_state/ZIP_INDEX_v1.md` | E1 | Noncanon inventory of a ZIP snapshot contents | Not a schema; do not infer protocol fields | `work/system_specs/ZIP_JOB_SCHEMA.md` |
| R-SAVE-LEVELS | `core_docs/a2 hand assembled docs/uploads/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md` | E0 | Save-level definitions | Conflation between B-required vs A-only overlays | `work/system_specs/SAVE_LEVELS.md` |
| R-A2-BOOT | `core_docs/a2 hand assembled docs/uploads/A2_EXPORT_PACK_SMALL_2026-02-12T043701Z/A2_JP_BEHAVIORAL_BOOT.md` | E0 | A2 behavior contract | High entropy if treated narratively | `work/system_specs/A2_PROTOCOL.md` |
| R-A2-CONTEXT | `core_docs/a2 hand assembled docs/uploads/A2_EXPORT_PACK_SMALL_2026-02-12T043701Z/A2_WORKING_UPGRADE_CONTEXT_v1.md` | E1 | Layering definition (A2/A1/A0/B/SIM) | Can conflict with megaboot wording; treat as working-layer | `work/rebaseline/BOUNDARY_QUOTES_A0_A1_A2.md` |
| R-A1-MATRIX | `work/rebaseline/BOOTPACK_THREAD_A1_v1.0__VERBATIM.md` | E1 | Basis for A1 mode matrix | None | `work/rebaseline/A1_ALLOWED_FORBIDDEN_MATRIX.md`, `work/system_specs/A1_CONTRACT.md` |
| R-TOE-RAW | `core_docs/high entropy doc/x grok chat TOE.docx` | E3 | High-entropy physics “fuel” | Teleology/time/causality/FTL narrative traps | `work/rebaseline/x_grok_chat_TOE__RAW_EXTRACT.txt` |
| R-TOE-FUEL | `core_docs/high entropy doc/x grok chat TOE.docx` | E2 | A2 fuel extract | Same as above (quarantined) | `work/rebaseline/A2_FUEL_EXTRACT_x_grok_chat_TOE.md` |
