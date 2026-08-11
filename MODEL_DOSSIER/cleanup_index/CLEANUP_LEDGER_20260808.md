# Machine cleanup ledger — 2026-08-08

Indexed before touching anything, per owner order. Two indexes run: codebase-memory
(`Documents/Codex/2026-07-27` → 716,232 nodes, 1,201,666 edges) and content-hash manifests
of both trees (`manifest_Codex.txt`, `manifest_Codex-Ratchet.txt`).

## Measured

334,794 files across `Documents/Codex` and `Codex-Ratchet`. 119,833 distinct contents.
**214,961 redundant copies — 64%.** 7.6 GB reclaimable from exact byte-identical duplicates,
7.15 GB of it inside `Documents/Codex/2026-07-27`.

Worst single case: `lev_command_a.stderr`, 5,283 byte-identical copies.

## Done

| action | reclaimed | evidence nothing lost |
|---|---|---|
| removed 3 clean worktrees | 2,259 MB | branches `codex/v8-nonofficial-stress-20260715`, `codex/v8-source-native-qit-foundation-20260718`, `codex/v9-stack-consolidation-20260806` all still present; commit `adbce2707` reachable |
| removed `holodeck/python_fep/venv` | 694 MB | untracked (0 tracked files under `holodeck/`), a virtualenv, regenerable; README retained |
| pruned stale `~/Desktop/Codex` worktree registration | 0 | directory was already gone |

Repo 2.0 GB → 1.4 GB. No env artifacts remain inside the repo.

## Blocked — uncommitted work found

Five worktrees hold 33 uncommitted files. Removing them would destroy that work, so the
safety check refused. Roughly 3.5 GB locked behind them.

| worktree | dirty files |
|---|---|
| v1-1-finite-conformance-20260715 | 12 |
| v1-semantic-forcing-20260715 | 17 |
| v2-root-kernel-calibration-20260716 | 1 |
| v31-root-kernel-calibration-20260716 | 2 |
| v8-integration-repair-20260715 | 1 |

Remedy: commit each to its own branch, as was done for v9, then remove.

## Remaining candidates, ranked by safety

1. `.cache` — 8.1 GB, regenerable by definition. 5.2 GB is `codebase-memory-mcp` index cache.
2. `Documents/Codex` dedup — 7.15 GB of proven byte-identical duplicates.
3. Five dirty worktrees — ~3.5 GB, after committing.
4. `~/Desktop/Codex Ratchet` — 70 state-pack zips, 3.3 GB, numbered RATCHET_167 → RATCHET_190.
   Needs hashing first: these may hold unique material.
5. `.gemini/history` — 41 claimgate versions, 967 MB.

## Do not clean without a retention rule

`~/.codex` (7.6 GB) holds the codex session rollouts. The model-binding gate built today reads
`turn_context.model` from those files to prove which model produced a proposal. Deleting them
silently breaks the evidence chain behind every existing model receipt.

## The behaviour that produced this

Three habits, none specific to ConstraintBox:

1. Copy the whole tree per run rather than reference it once — ten `claimgate_plugin` copies
   under `canonical_claimgate_production_path`, one per scenario, then an `archive_pre_numpy25`
   set duplicating all five again.
2. Install runtimes wherever work happens — a Python 3.11 venv and a JDK 21 inside
   `Documents/Codex`, a venv inside the repo.
3. Zip the whole state each session and never delete — 70 packs on the Desktop.

## Recovered to the repo

`MODEL_DOSSIER/owner_authority/` now holds `01_FABLE_THREAD_OWNER_PROMPTS_VERBATIM.md` and
`02_OWNER_CORRECTIONS_AND_DISTINCTIONS_LEDGER.md`, previously only in `Documents/Codex`.
23 further owner-authority files remain outside the repo.

## ConstraintBox doc consolidation — 2026-08-08

CLAUDE.md's binding entry point `constraint_box/CB_READ_THIS_FIRST.md` did not exist at
session start; every session obeying the instruction hit a dead link. Three reading lanes
read 56 CB documents across `constraint_box/` and `MODEL_DOSSIER/`; the entry point was then
written from their verified one-liners. No file was moved, renamed or deleted.

What the entry point records:

- 56 documents indexed by audience (read first, owner canon, operator, builder, auditor,
  historical), each with a one-line description from an actual read.
- The `docs/` numbering collision resolved as two series: current 2026-08-06/08
  (`00_READ_FIRST` + `01_THEORY`..`05_FINDING_SLOP`, continued by `07`-`10`) versus the
  inherited 2026-07-25 handoff pack (`01_ARCHITECTURE`, `02_SIM_SETUP_TIERS`,
  `03_CLAIMGATE_FOUNDATION_FROM_MANIFOLD`, `04_INSTALL_BOOT_MAINTENANCE`,
  `05_CR_MANIFOLD_FIXTURES`, `06_LIMITS_AND_DEFERRED`). Current series is authority for
  current behavior; inherited pack is design context.
- 7 supersessions named: the five inherited 01-05 files (superseded for current behavior),
  `WIZARD_NESTED_COUNCIL_WAVE_MODEL_20260806.md` (superseded by the owner-canon wave model),
  and `PROJECT_STATE.md` (stale snapshot, predates commit 5ab8fd26d; regenerate first).
- 3 owner-canon-versus-machine contradictions held open, not collapsed (wave model,
  association-floor sweep incomplete outside CB, May/July readiness index conflict per
  CB-CON-005).
- Coverage limits stated: 17 `docs/` files plus most of `doctrine/`, `handoff/`,
  `recovered_specs/` and `owner_authority/` remain unread and unverified.

Moves recommended for owner approval, not performed:

1. Rename or relocate the six inherited 2026-07-25 files (for example into
   `docs/inherited_20260725/`) to end the prefix collision; update inbound references first.
2. Name a primary copy of `CB_DEFINITION_OWNER_CANON_20260806.md` (`constraint_box/docs/`
   versus `MODEL_DOSSIER/`) and make the other a pointer.
3. Hash-compare `constraint_box/docs/OWNER_RULINGS_VERBATIM_20260806.md` against
   `MODEL_DOSSIER/owner_authority/CB_OWNER_RULINGS_VERBATIM_20260806.md`; name a primary.
4. Move `SESSION_WORK_INDEX_20260807.md` and `SESSION_SAVE_20260807.md` out of `docs/` into a
   session-notes location so `docs/` holds product documentation only.
5. Either create `doctrine/06_MANIFEST/` and move `ESTATE_VERIFICATION.md` into it, or fix
   the broken path in `doctrine/00_START_HERE/README.md` line 62.
6. Rule on which ClaimGate copy is canonical: repo-root `claimgate_plugin/` versus
   `constraint_box/claimgate_plugin/` (8 files diverged).
