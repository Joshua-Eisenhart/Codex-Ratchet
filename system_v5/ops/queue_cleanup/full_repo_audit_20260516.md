# Full Repo Audit 2026-05-16

Status: partial Wizard v4.2 Max Assembly audit with read-only parent lanes plus controller cleanup

Route truth: Prior controller transcript reported 12 Codex-native audit lanes and usable returns, but no child subsubagent topology was launched and current `scripts/wizard_v4_2_runtime_audit.py` finds no recent worker receipt files under `system_v5/wizard/receipts`; topology counts are not independently validated from repo artifacts.

## Controller Changes Made

- Repaired `.gitignore` boundaries:
  - added `.pytest_cache/`;
  - added explicit ignores for common credential/package-auth files;
  - hid generated `system_v5/grok_sim/candidates/`;
  - kept `system_v5/grok_sim/loop_runner/contracts/` visible as runner contract source;
  - kept `system_v5/grok_sim/loop_runner/prompts/` visible as prompt-control source;
  - hid `system_v5/ops/quarantine/gstack_adjacency_companion/`.
- Moved one exact unadmitted v4 spillover family into quarantine:
  - `system_v4/probes/sim_gstack_lego_adjacency_order_companion.py`;
  - `system_v4/probes/sim_gstack_lego_adjacency_order_companion_results.json`;
  - manifest: `system_v5/ops/queue_cleanup/v4_quarantine_move_manifest_gstack_adjacency_companion_20260516.json`;
  - preserved hashes: `fee014a2157992331507ec938816a966942d8f934cac189510561986aafedf80`, `1883bcc77a9851e6b0e2aebf0e165e575878a23630fc7994d4b41c4c1c39729d`.
- Updated `system_v5/ops/queue_cleanup/repo_cleanup_inventory_20260516.md` to reflect the corrected boundary and current status count.
- After external advisory audit, repaired the live runner admission interface:
  - `scripts/wizard_sim_admission.py` now accepts `--path-only`;
  - successful `--path-only` calls print only the resolved admission path;
  - `system_v5/tests/test_sim_cleanup_guards.py` now covers the exact runner call shape.
- Reconciled runner admission schema truth:
  - canonical admission schema is now `wizard_sim_admission_v4_2`;
  - legacy `wizard_sim_admission_v4_1` is rejected by default with `schema_legacy_v4_1_requires_explicit_recovery`;
  - recovery-only legacy validation requires `--allow-legacy-v4-1`;
  - tracked `sim_choi_matrix_classical` admission packet now uses the v4.2 schema.
- Repaired runner preflight atomic queue visibility:
  - `scripts/runner_queue_preflight.py` now reports atomic `claimed/blocked/done` counts;
  - non-empty atomic `claimed/` now fails closed with `atomic_claimed_queue_not_empty`;
  - `system_v5/tests/test_sim_cleanup_guards.py` now covers the false-green regression.
- Wrote a manifest-backed dry-run for atomic claim reconciliation:
  - manifest: `system_v5/ops/queue_cleanup/atomic_claimed_queue_reconcile_dry_run_20260516.json`;
  - decision: `BLOCKED_REQUIRES_PREP`;
  - counted `57` claimed queue items, `0` live claim PIDs, `795` blocked queue items, and `8,856` done queue items;
  - recorded two non-queue junk files separately: `queue/.DS_Store` and `queue/done/.DS_Store`;
  - future block commands are recorded as absolute `proposed_argv` entries to avoid cwd-sensitive execution;
  - no queue files were moved because the claimed files are still inside the 72-hour maintenance safety window.
- Moved the exact weak-lego one-off generator residue into quarantine:
  - manifest: `system_v5/ops/queue_cleanup/weak_lego_generator_quarantine_move_manifest_20260516.json`;
  - destination: `system_v5/ops/quarantine/weak_lego_generators_20260516/`;
  - moved files: `55`;
  - kept weak-lego evidence helpers and the blocked admission mutator visible in `scripts/`.
- Generated premortem artifacts for the cleanup strategy:
  - `system_v5/ops/queue_cleanup/premortem-transcript-20260516T223708Z.md`;
  - `system_v5/ops/queue_cleanup/premortem-report-20260516T223708Z.html`;
  - these are ignored by the existing `premortem-*` rules unless explicitly force-added.

## External Advisory Audit

Advisory lanes were run after the initial Codex audit. Codex kept ownership of all repo edits.

- Opus advisory receipt: `/tmp/codex_ratchet_external_audit_20260516/20260516T214928Z-opus-cleanup-audit-5a8ce335f6c2.receipt.json`
- Sonnet advisory receipt: `/tmp/codex_ratchet_external_audit_20260516/20260516T214928Z-sonnet-cleanup-audit-ae04e5ba55cf.receipt.json`
- Gemini advisory output: `/tmp/codex_ratchet_external_audit_20260516/gemini_output.txt`
- Grok advisory output: `/tmp/codex_ratchet_external_audit_20260516/grok_output.txt`
- Mass-parallel Opus advisory receipt: `/tmp/codex_ratchet_mass_parallel_20260516/20260516T223141Z-opus-queue-artifact-review-da8b5a0236b4.receipt.json`
- Mass-parallel Sonnet advisory receipt: `/tmp/codex_ratchet_mass_parallel_20260516/20260516T223141Z-sonnet-patch-review-86f94ba1c930.receipt.json`
- Mass-parallel Gemini advisory output: `/tmp/codex_ratchet_mass_parallel_20260516/gemini_dirty_tree_strategy_with_status.out`
- Mass-parallel Grok advisory output: `/tmp/codex_ratchet_mass_parallel_20260516/grok_repo_audit.out`

Consensus accepted by Codex: the missing `--path-only` flag was the first repair because it directly affects live queue admission. Grok returned several non-existent path claims, so those claims were ignored unless local repo inspection confirmed them.
Later mass-parallel lanes approved the JSON queue-item/junk split and the `grok_sim` tracking boundary. Gemini's first repo-inspection route was blocked by plan-mode tool policy, so the rerun used an embedded git-status snapshot and remains advisory.

## Current Repo State

- Branch: `main`, even with `origin/main` during the audit.
- Staging: no staged files during the audit.
- Git lock: no `.git/index.lock` observed.
- Visible dirty count after this pass: 358 paths at final measurement.
- Main noise reduction already achieved in this cleanup window: 26,902 visible paths down to 358 visible paths.
- Note: active/local tooling added visible `system_v5/ops/tooling/` artifacts during the audit window, so treat the count as a measured checkpoint rather than a frozen invariant.

## High-Risk Findings

1. Legacy runner admission is fail-closed by default.
   `system_v5/ops/sim_runner.sh` calls `scripts/wizard_sim_admission.py --path-only`. This pass added the missing flag, made `wizard_sim_admission_v4_2` the canonical schema, and rejects legacy v4.1 unless `--allow-legacy-v4-1` is explicitly passed for recovery.

2. The wider admission estate still needs migration decisions.
   The tracked smoke packet is v4.2, but ignored/generated admission spillover may still contain legacy v4.1 packets. Do not bulk-rewrite it; migrate only exact packets selected for a runner lane or evidence checkpoint.

3. Queue preflight false-green is repaired, and the current repo is red.
   The atomic queue has `claimed=57`, `blocked=795`, and `done=8856`. `scripts/runner_queue_preflight.py` now reports JSON queue-item counts, records junk counts separately, and fails closed on the 57 claimed files.

4. Formal scout source is not checkpoint-clean.
   A read-only lane confirmed 132 untracked scout modules have core markers, but 6 lack explicit graveyard markers, 19 result receipts are validator-red, 9 filenames still trip banned-name lint, and the README references ignored provider receipts.

5. `grok_sim` had an inverted tracking boundary.
   Generated candidates were visible while runner contracts/prompts were ignored. This pass fixed the ignore side, but source/control staging still needs a curated checkpoint.

6. Scripts are mixed ownership.
   Six modified scripts are currently visible in git status (`scripts/adaptive_controller.py`, `scripts/autonomous_reseed_loop.sh`, `scripts/overnight_two_runner.sh`, `scripts/queue_claim.py`, `scripts/runner_queue_preflight.py`, `scripts/wizard_sim_admission.py`). The 55 one-off weak-lego generator scripts were quarantined by manifest; the remaining 7 untracked scripts are evidence helpers or a blocked admission mutator and need separate decisions.

7. The v4 probe surface still needs owner decisions.
   After the gstack quarantine, the remaining visible v4 dirt is deliberate source/reference work, not cleanup trash: 4 tracked deletes, 3 tracked modifications, and 7 untracked sources.

8. Security scan found no visible raw key material.
   Provider env-var names are referenced by source files, and ignored provider receipts contain key metadata, but no confirmed key values were found. The actionable gap was missing explicit ignore coverage for common auth files; this pass added it.

## Stage Later, As Separate Checkpoints

- Git hygiene and cleanup metadata:
  - `.gitignore`;
  - `system_v5/ops/queue_cleanup/repo_cleanup_inventory_20260516.md`;
  - `system_v5/ops/queue_cleanup/v4_probe_corpus_classification_20260514.json`;
  - `system_v5/ops/queue_cleanup/v4_quarantine_move_manifest_toponetx_simplex_width_20260516.json`;
  - `system_v5/ops/queue_cleanup/v4_quarantine_move_manifest_gstack_adjacency_companion_20260516.json`;
  - `system_v5/ops/queue_cleanup/atomic_claimed_queue_reconcile_dry_run_20260516.json`;
  - `system_v5/ops/queue_cleanup/weak_lego_generator_quarantine_move_manifest_20260516.json`.
- v5 lego source:
  - the 12 new `system_v5/legos/*.py` files;
  - `system_v5/legos/README.md`;
  - evidence JSONs only in a separate force-added evidence snapshot.
- `grok_sim` control source:
  - runner code, contracts, prompts, tests, tools, and control docs;
  - no generated candidates or receipts.
- Formal scout source:
  - engine/support modules and coherent scout batches;
  - no provider receipts/results unless making an explicit evidence snapshot.
- Docs:
  - untracked handoffs/audits should be manifested as noncanonical handoff, audit, scout note, or bootstrap prompt; do not mark canonical.

## Blocked Until Repaired

- Do not stage the 4 v4 tracked deletes until a rename/archive manifest proves old paths are not required by admissions, inventory, loaders, or queue rows.
- Do not stage the modified formal-scout result JSONs as meaningful evidence; the audit says they only changed elapsed seconds.
- Do not stage `scripts/admit_weak_lego_batch.py` until it emits `wizard_sim_admission_v4_2` or is explicitly quarantined as a legacy mutator.
- Do not stage the remaining weak-lego helper scripts until the `qit_gstack_exploratory_wave_manifest_20260513.json` evidence bundle is accepted or abandoned.
- Do not run broad sim queues while runtime audit remains red.
- Do not move the 57 atomic claimed queue files until the 72-hour freshness blocker expires or the owner explicitly overrides it; use the dry-run manifest as the exact candidate list.
- Do not delete `work/external/Sana/` or its venv without owner confirmation; that is the largest disk win but outside the repo evidence flow.

## Validation Snapshot

Green or locally confirmed:

- Wizard packet conformance: pass after packet junk quarantine.
- Helper-process strict audit: pass, `helper_process_count=0`.
- Bounded secrets scan: no real key material found; hits were placeholder examples only.
- Security lane: no confirmed hard-coded provider keys, private-key blocks, JWTs, AWS keys, GitHub tokens, or Slack tokens in visible scoped source.
- Quarantine hash check for `gstack_adjacency_companion`: matched pre-move hashes.
- `wizard_sim_admission.py` schema/path-only regression slice: `29 passed, 256 deselected`.
- Real `sim_choi_matrix_classical` v4.2 `--path-only` admission check: returned the expected admission path.
- Runner preflight/admission regression slice: `6 passed, 277 deselected`.
- Atomic claimed-queue dry-run manifest JSON parse: pass; item decisions all `BLOCKED_REQUIRES_PREP`.
- Weak-lego generator quarantine manifest hash check: pass, `55/55` destination hashes matched.

Red or intentionally blocked:

- `scripts/wizard_v4_2_runtime_audit.py`: red due to stale ops reports, contract-lint debt, never-run debt, taxonomy drift, and no recent worker receipts.
- `make runner-preflight`: red by design after the atomic queue repair, with `atomic_claimed_queue_not_empty`, `claimed=57`, `blocked=795`, `done=8856`, and queue junk counts recorded separately.
- `scripts/lint_sim_contract.py`: red, `checked=10494`, `violation_total=10893`, `sims_with_violations=9175`.
- Ops report consumers: red on current stale/ratchet surfaces.
- Formal-scout validator/provider receipt validator: red on older or incomplete receipts.

## Next Repair Order

1. After the freshness blocker clears, rerun process/PID checks and reconcile the 57 atomic claims with `scripts/queue_claim.py block --claim-path <path> --reason stale_atomic_claim_dead_pid_after_72h_review`.
2. Decide the v4 semantic rename batch: restore, archive, or accept replacements with source/result/admission references updated.
3. Land `.gitignore`, runner admission/preflight repairs, and cleanup manifests as small separated checkpoints.
4. Land v5 lego source separately from lego evidence.
5. Curate `grok_sim` runner contracts/prompts/source separately from generated candidates and receipts.
6. Fix the 6 formal-scout source marker gaps, 9 banned-name hits, and 19 red result receipts before any formal-scout bulk source checkpoint.
