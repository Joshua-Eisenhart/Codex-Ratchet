# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_archive_surface_deep_archive_migrated_run_root_registry_and_family_signatures__v1`
Extraction mode: `ARCHIVE_DEEP_MIGRATED_RUN_ROOT_REGISTRY_SIGNATURE_PASS`

## T1) Low-entropy milestone framing vs massive run-history density
- source markers:
  - migrated subtree counts
  - run-tree file counts
- tension:
  - this family lives under `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`
  - the migrated run-root still preserves `7801` files and `182` directories, with `7772` files concentrated in the run tree alone
- preserved read:
  - low-entropy here means retention class, not small artifact volume

## T2) Compact registry usefulness vs repetitive partial coverage
- source markers:
  - `_RUNS_REGISTRY.jsonl`
- tension:
  - the registry is the clearest bounded index into the subtree
  - it contains `27` lines for only `9` unique run ids, each repeated exactly `3` times, while the run tree root holds dozens of named families beyond those nine ids
- preserved read:
  - the registry is a re-entry aid, not a complete or unique final-state ledger

## T3) Historical archive framing vs preserved current-state residue
- source markers:
  - `bootpack_b_kernel_v1__current_state__`
  - `_CURRENT_RUN.txt`
- tension:
  - the subtree is archived history
  - it still preserves `state.json`, numbered `state` and `sequence_state` ladders, and a current-run pointer to `TEST_STATE_TRANSITION_CHAIN_B`
- preserved read:
  - archive demotion did not strip quasi-live residue; it only changed authority status

## T4) Rich run accumulation vs unresolved readiness
- source markers:
  - `RUN_FOUNDATION_BATCH_0001/summary.json`
  - `RUN_SIGNAL_0005/summary.json`
- tension:
  - long-run families accumulate large accepted counts and broad packet exchange histories
  - their summaries still end at `MAX_STEPS` with `master_sim_status NOT_READY` and large unresolved promotion blocker counts (`519` and `360`)
- preserved read:
  - artifact density and throughput did not translate into promotion readiness

## T5) Shared packet grammar vs family-specific overlay drift
- source markers:
  - representative directory listings
- tension:
  - foundation and signal runs share the same broad `zip_packets/` grammar
  - they diverge through family-specific overlays such as `HARDMODE_METRICS.json`, `SIGNAL_AUDIT.json`, and `REPLAY_AUDIT.json`
- preserved read:
  - common transport skeleton coexisted with multiple experiment/audit modes

## T6) Deterministic test lineage vs external-strategy dependency
- source markers:
  - registry stop reasons
  - `TEST_DET_A/summary.json`
  - residual `A1_TO_A0` packet
- tension:
  - deterministic test families preserve repeated `A2_OPERATOR_SET_EXHAUSTED` outcomes with stable hashes
  - other nearby tests stop for `A1_NEEDS_EXTERNAL_STRATEGY`, and one strategy packet survives detached in a residual subtree
- preserved read:
  - the archive retains both internal determinism experiments and explicit dependence on missing external strategy inputs

## T7) State-ladder completeness vs asymmetry
- source markers:
  - current-state file inventory
- tension:
  - both `state` and `sequence_state` ladders are preserved as numbered history
  - `sequence_state` extends through `14`, while `state` stops at `13`
- preserved read:
  - even residue ladders preserve small incompletions or nonparallel snapshot seams that should not be smoothed away
