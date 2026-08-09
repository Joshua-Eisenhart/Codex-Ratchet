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
