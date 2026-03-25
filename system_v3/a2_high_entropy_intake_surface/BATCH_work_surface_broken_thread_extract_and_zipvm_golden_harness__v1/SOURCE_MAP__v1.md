# SOURCE MAP

Batch id: `BATCH_work_surface_broken_thread_extract_and_zipvm_golden_harness__v1`

Scope
- Bounded `work/` archaeology pass over the prototype audit lane that turns a long broken-thread transcript into a curated document pack, distills that pack into issue ledgers and execution roadmaps, and then validates ZIP-style outputs with a mechanical golden-test harness.
- This is preserved as spillover process memory only. Nothing here is promoted to active system law.

## Source set A: curated broken-thread extraction package

Primary anchors
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/THREAD_EXTRACT__BROKEN_THREAD__v1_2026-03-04/README.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/THREAD_EXTRACT__BROKEN_THREAD__v1_2026-03-04/docs/00_MANIFEST.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/THREAD_EXTRACT__BROKEN_THREAD__v1_2026-03-04/docs/07_PLAN_ASSESSMENT_AND_RECOMMENDED_SEQUENCE.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/THREAD_EXTRACT__BROKEN_THREAD__v1_2026-03-04/data/json_filenames_counts.json`

Observed structure
- The package formalizes one prior transcript into `12` extracted docs with a declared read order.
- It preserves a line-numbered source transcript at `/source/branchthread_extract_chat_gpt__line_numbered.txt` with `44,461` lines.
- It keeps auxiliary traceability material in `/data/traceability_map.csv` (`63` lines counted during this pass).
- It also bundles two ZIPs under `/canon/`, even though the package itself lives under `work/audit_tmp/`.

Useful residue
- This package shows a reusable pattern for converting long freeform threads into a navigable archive with source line traceability, explicit reading order, and separated plan assessment.

## Source set B: issue distillation and authority-safe overlays

Primary anchors
- `/home/ratchet/Desktop/Codex Ratchet/work/extracts/READ_THIS_FIRST__v2__AUTHORITY_CONFLICT_SAFE.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/extracts/BRANCHTHREAD_ISSUE_LEDGER__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/extracts/THREAD_EXTRACT__BROKEN_THREAD__ISSUES_AND_UPGRADES__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/extracts/TOP_OPEN_UPGRADES__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/extracts/UPGRADE_STATUS_SUMMARY__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/extracts/NEXT_EXECUTION_ROADMAP__NO_PRO_FIRST__v1.md`

Observed structure
- `READ_THIS_FIRST__v2__AUTHORITY_CONFLICT_SAFE.md` adds a fail-closed overlay: if authority labels conflict, postpone decisions until header quotes are checked directly in source docs.
- `BRANCHTHREAD_ISSUE_LEDGER__v1.md` derives a `260`-item top extract from a `44,461`-line source transcript and maps categories to fix surfaces.
- `THREAD_EXTRACT__BROKEN_THREAD__ISSUES_AND_UPGRADES__v1.md` reframes the broken-thread package into status-tagged issues and upgrade candidates with category counts.
- `UPGRADE_STATUS_SUMMARY__v1.md` compresses the ledger into repo-status buckets such as `OPEN_IF_RUN_SHOWS_NO_CANON`, `PRESENT_IN_REPO`, and `PARTIAL`.
- `NEXT_EXECUTION_ROADMAP__NO_PRO_FIRST__v1.md` recenters the lane on local A0/B/SIM validation first and reserves Pro only for extraction tasks that exceed local reliability.

Useful residue
- This family preserves a prototype pattern for turning high-entropy thread residue into ranked issue ledgers, status summaries, and a “no narrative canon” execution roadmap.

## Source set C: selector-audit runtime residue hidden under audit_tmp

Primary anchor
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/a1_pack_selector_audit_0047/RUN_AUDIT_0047/state.json`

Observed structure
- Despite the `audit_tmp` location, this file is not a tiny scratch artifact.
- During this pass it yielded:
  - `accepted_batch_count = 332`
  - `canonical_ledger_steps = 332`
  - `term_registry_size = 14`
  - `survivor_order_size = 157`
  - `unchanged_ledger_streak = 0`

Useful residue
- The file shows how a prototype audit lane kept a substantial state snapshot beside extraction materials instead of strictly separating transient scratch from runtime-derived evidence.

## Source set D: ZIP-VM golden validation harness

Primary anchors
- `/home/ratchet/Desktop/Codex Ratchet/work/golden_tests/README__ZIP_VM_GOLDEN_TESTS__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/golden_tests/validate_zip_vm_output.py`
- `/home/ratchet/Desktop/Codex Ratchet/work/golden_tests/run_one_check.sh`
- `/home/ratchet/Desktop/Codex Ratchet/work/golden_tests/audit_corpus_with_profile_cascade.sh`
- `/home/ratchet/Desktop/Codex Ratchet/work/golden_tests/expected_checks/GOLDEN_CHECK__FAIL_CLOSED_MISSING_PAYLOAD__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/golden_tests/expected_checks/GOLDEN_CHECK__MODEL_CORE_MINIMAL_PASS__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/golden_tests/expected_checks/GOLDEN_CHECK__A2_REAL_BUNDLE_BASELINE__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/golden_tests/reports/CASCADE_AUDIT__WIGGLE_RETURNS__2026_03_02__00_39_32.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/golden_tests/reports/QUICK_AUDIT_NOTE__L1_5_RETURN__2026_03_02__00_42_12.md`

Observed structure
- The harness is explicitly mechanical and fail-closed: file existence plus required/forbidden substring checks only.
- `expected_checks/` contains `14` profiles, including one current baseline and a broad legacy-compat ladder.
- The cascade audit report records `10` bundles tested, `10` passed, `0` failed.
- The sample bundle at `/home/ratchet/Desktop/Codex Ratchet/work/golden_tests/output_samples/sample_pass` passed both:
  - `FAIL_CLOSED_MISSING_PAYLOAD_v1`
  - `MODEL_CORE_MINIMAL_PASS_v1`

Useful residue
- This harness preserves a reusable pattern for low-entropy template validation without running the full ratchet, while also exposing compatibility drift across bundle generations.
