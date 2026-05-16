# Repo Cleanup Inventory 2026-05-16

Status: bounded cleanup pass
Scope: dirty-tree noise, runtime spillover, and cleanup blockers

## Actions Taken

- Updated `.gitignore` to ignore root `runs/` runtime spillover.
- Updated `.gitignore` to ignore local `system_v5/grok_sim` loop-runner runtime spillover:
  - `.codex_last_msg_*.txt`
  - `candidates/`
  - `loop_runner/receipts/`
  - `loops/`
  - `iters/`
  - `proposed_formal_sims/`
  - `research_notes/`
- Repaired the `grok_sim` ignore boundary after audit: runner `contracts/`
  and `prompts/` are control source, so they are visible again; generated
  `candidates/` are hidden.
- Added an explicit root `.pytest_cache/` ignore.
- Added explicit ignores for common credential/package-auth files:
  `.npmrc`, `.pypirc`, `.netrc`, SSH key filenames, PEM/key bundles, and
  common service-account JSON names.
- Updated `.gitignore` to hide untracked generated gate/output estates while
  preserving tracked edits:
  - `system_v4/probes/*_survivor_classes.py`
  - `system_v4/probes/*_survivor_count_gap_classes.py`
  - `system_v5/ops/wizard_admissions/*.json`
  - `system_v5/ops/wizard_admission_receipts/*.json`
  - `system_v5/ops/formal_scouts/provider_receipts/`
  - `system_v5/ops/formal_scouts/results/*.json`
  - `system_v5/ops/queue_cleanup/queue_done_duplicate_repair_*.json`
  - `system_v5/legos/results/`
- Moved the exact non-admitted `toponetx_simplex_width` generated v4 probe
  family by manifest:
  - source manifest: `system_v5/ops/queue_cleanup/v4_quarantine_dry_run_manifest_toponetx_simplex_width_20260514.json`
  - move manifest: `system_v5/ops/queue_cleanup/v4_quarantine_move_manifest_toponetx_simplex_width_20260516.json`
  - destination: `system_v5/ops/quarantine/toponetx_simplex_width/`
  - moved files: 8
- Moved the exact non-admitted `gstack_adjacency_companion` generated v4 probe
  family by manifest:
  - move manifest: `system_v5/ops/queue_cleanup/v4_quarantine_move_manifest_gstack_adjacency_companion_20260516.json`
  - destination: `system_v5/ops/quarantine/gstack_adjacency_companion/`
  - moved files: 2
- Moved Wizard v4.2 packet `.DS_Store` files into temp quarantine:
  - `/tmp/codex_ratchet_cleanup_quarantine_20260516_wizard_packet/`
- The packet root `.DS_Store` was recreated once during verification and was
  quarantined again; final immediate conformance plus a short follow-up scan
  found no packet `.DS_Store` files.
- Re-ran packet conformance after packet junk quarantine:
  - `python3 /Users/joshuaeisenhart/wiki/wizard/packet-v4-2-current/conformance/validate_v4_2_packet.py`
  - result: `PASS`
- Repaired live runner gate truth after external advisory audit:
  - `scripts/wizard_sim_admission.py` now supports the runner's `--path-only` call;
  - `scripts/runner_queue_preflight.py` now reports JSON queue-item counts, reports queue junk counts separately, and fails closed on non-empty `claimed/`;
  - targeted guard tests cover both regressions.
- Reconciled runner admission schema truth:
  - `wizard_sim_admission_v4_2` is now the default accepted schema;
  - legacy `wizard_sim_admission_v4_1` is rejected unless `--allow-legacy-v4-1` is explicitly passed for recovery;
  - tracked `sim_choi_matrix_classical` admission packet now uses v4.2.
- Wrote `system_v5/ops/queue_cleanup/atomic_claimed_queue_reconcile_dry_run_20260516.json`
  as a dry-run manifest for the 57 atomic claimed files. It records exact
  paths, hashes, dead claim PIDs, queue junk counts, absolute future block
  argv entries, and the 72-hour freshness blocker. No queue state was moved.
- Moved the exact weak-lego generator residue into quarantine:
  - move manifest: `system_v5/ops/queue_cleanup/weak_lego_generator_quarantine_move_manifest_20260516.json`
  - destination: `system_v5/ops/quarantine/weak_lego_generators_20260516/`
  - moved files: 55
  - kept evidence helpers and the blocked admission mutator in `scripts/`.
- Generated cleanup premortem artifacts:
  - `system_v5/ops/queue_cleanup/premortem-transcript-20260516T223708Z.md`
  - `system_v5/ops/queue_cleanup/premortem-report-20260516T223708Z.html`
  - these match existing ignored `premortem-*` patterns unless force-added.

## Dirty-State Counts

Measured with:

```text
git status --porcelain=v1 --untracked-files=all | wc -l
```

| Checkpoint | Count |
|---|---:|
| Before cleanup | 26,902 |
| After ignore cleanup, before this report | 21,467 |
| After generated-estate ignores and manifest move | 515 |
| After `grok_sim` boundary repair, gstack adjacency quarantine, credential ignore hardening, external advisory audit, runner/preflight/admission repairs, atomic-claim dry-run manifest, and weak-lego generator quarantine | 358 |

Net status-noise reduction after this pass: 26,544 paths.

Note: active/local tooling added visible `system_v5/ops/tooling/` artifacts
during the audit window, so this count is a measured checkpoint rather than a
frozen invariant.

## Candidate Classification

| Surface | Decision | Reason |
|---|---|---|
| `runs/` | `KEEP_ACTIVE` | Local generated Wizard/runtime spillover; hidden from git status, not moved or staged. |
| `system_v5/grok_sim/.codex_last_msg_*.txt` | `KEEP_ACTIVE` | Local controller message spillover from informal proposal lab; hidden from git status. |
| `system_v5/grok_sim/loop_runner/receipts/` | `KEEP_ACTIVE` | Generated proposal-lab receipts, not canonical evidence; hidden from git status. |
| `system_v5/grok_sim/loops/` | `KEEP_ACTIVE` | Local loop runtime state; hidden from git status. |
| `system_v5/grok_sim/iters/` | `KEEP_ACTIVE` | Local iteration runtime state; hidden from git status. |
| `system_v5/grok_sim/candidates/` | `KEEP_ACTIVE` | Generated proposal candidates; hidden unless a curated fixture is selected. |
| `system_v5/grok_sim/loop_runner/proposed_formal_sims/` | `KEEP_ACTIVE` | Proposal-lab generated material; hidden unless force-added for a curated snapshot. |
| `system_v5/grok_sim/loop_runner/contracts/` | `KEEP_ACTIVE` | Runner contract source/control surface; visible again and should be tracked only as source/control, not generated evidence. |
| `system_v5/grok_sim/loop_runner/prompts/` | `KEEP_ACTIVE` | Prompt-control source surface; visible again and should be tracked only as source/control. |
| `system_v5/grok_sim/loop_runner/research_notes/` | `KEEP_ACTIVE` | Mixed control notes and informal retrospectives; still hidden unless curated. |
| `system_v5/ops/wizard_admissions/*.json` | `KEEP_ACTIVE` | Generated queue-admission gate estate; tracked edits still show, untracked spillover is hidden. |
| `system_v5/ops/wizard_admission_receipts/*.json` | `KEEP_ACTIVE` | Generated receipt gate estate; tracked edits still show, untracked spillover is hidden. |
| `system_v5/ops/formal_scouts/provider_receipts/` | `KEEP_ACTIVE` | Generated provider receipt estate; hidden unless making an evidence snapshot. |
| `system_v5/ops/formal_scouts/results/*.json` | `KEEP_ACTIVE` | Generated formal-scout result estate; tracked edits still show, untracked results are hidden. |
| `system_v5/ops/queue_cleanup/queue_done_duplicate_repair_*.json` | `KEEP_ACTIVE` | Generated duplicate-repair reports; tracked history remains visible. |
| `system_v5/ops/quarantine/toponetx_simplex_width/` | `MOVE_TO_QUARANTINE` | Exact dry-run manifest was reviewed and executed; payload hidden, move manifest visible. |
| `system_v5/ops/quarantine/gstack_adjacency_companion/` | `MOVE_TO_QUARANTINE` | Exact unadmitted/failing gstack-named spillover family was hashed, moved, and hidden; move manifest visible. |
| `system_v5/ops/quarantine/weak_lego_generators_20260516/` | `MOVE_TO_QUARANTINE` | 55 untracked one-off weak-lego generator scripts were moved by exact manifest and hidden; evidence helpers stayed visible. |
| `system_v4/probes/a2_state/queue/claimed/` | `BLOCKED_REQUIRES_PREP` | 57 claimed files have dead PIDs but are still inside the 72-hour freshness window; dry-run manifest written, no queue mutation performed. |
| Wizard packet `.DS_Store` files | `MOVE_TO_QUARANTINE` | Packet conformance rejects generated junk files. Originals moved to `/tmp/codex_ratchet_cleanup_quarantine_20260516_wizard_packet/`. |
| `system_v4/probes/*_survivor_classes.py` | `KEEP_ACTIVE` | Most generated files have live admission records pointing at their v4 paths; hidden from git status, not moved unless non-admitted and manifest-selected. |
| remaining weak-lego helper scripts | `BLOCKED_REQUIRES_PREP` | 6 evidence helpers stay visible until the exploratory evidence bundle is accepted or abandoned; `admit_weak_lego_batch.py` remains blocked until it emits v4.2 admission packets or is quarantined as legacy. |
| `.tmp/*` | `KEEP_ACTIVE` | Local handoff/provider scratch material; hidden from git status. |

## Remaining Cleanup Blockers

- `system_v4/probes` still contains many generated survivor/admission files,
  but most are referenced by live admission artifacts. Moving them now would
  break those gate paths. They should be migrated only after admission-path
  retirement or v5 wrapper replacement.
- Wizard runtime audit is still red beyond packet conformance:
  - stale ops reports;
  - large contract-lint violation count;
  - never-run cohort backlog;
  - taxonomy unknown allowlist drift.
- Runner preflight is now red by design because the atomic queue still has
  `claimed=57`, `blocked=795`, and `done=8856`; `queue/.DS_Store` and
  `queue/done/.DS_Store` are recorded separately as junk, not queue items.
- Remaining visible untracked files are mostly source/docs/scout modules that
  need ownership decisions, not runtime junk.

## Next Admissible Step

Classify the remaining visible untracked paths into source/doc/evidence
checkpoint groups, then stage or quarantine by named group only.
