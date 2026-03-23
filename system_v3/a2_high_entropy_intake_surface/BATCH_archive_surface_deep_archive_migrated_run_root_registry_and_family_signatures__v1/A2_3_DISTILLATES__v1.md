# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / ARCHIVE-ONLY DISTILLATES
Batch: `BATCH_archive_surface_deep_archive_migrated_run_root_registry_and_family_signatures__v1`
Extraction mode: `ARCHIVE_DEEP_MIGRATED_RUN_ROOT_REGISTRY_SIGNATURE_PASS`

## D1) Registry is the best bounded entry, not the whole truth
- `_RUNS_REGISTRY.jsonl` is the cleanest compact re-entry surface in the migrated run-root subtree.
- It is still repetitive and partial: `27` rows, `9` unique run ids, and only `6` distinct final-state hashes.

## D2) Archive demotion preserved quasi-live residue
- the subtree retains `state.json`, numbered `state` snapshots, numbered `sequence_state` snapshots, and `_CURRENT_RUN.txt`
- these are historical residue only; they do not become current authority because they survived migration

## D3) Run-tree taxonomy preserves multiple experimentation eras
- the root of `bootpack_b_kernel_v1__runs__` mixes `RUN`, `TEST`, `V2`, `BOOT`, `GPT`, `PHASEA`, and `CODEX` families
- this is a lineage archive of campaigns and transport experiments, not one single runtime epoch

## D4) Large campaigns share one ZIP-traffic skeleton
- representative long runs preserve repeated `A1_TO_A0`, `B_TO_A0`, `SIM_TO_A0`, and `A0_TO_B` packet ladders
- family-specific overlays such as `HARDMODE_METRICS`, `SIGNAL_AUDIT`, and `REPLAY_AUDIT` sit on top of that common transport grammar

## D5) Throughput did not equal readiness
- `RUN_FOUNDATION_BATCH_0001` and `RUN_SIGNAL_0005` both run to `MAX_STEPS`
- both keep `master_sim_status NOT_READY` and large unresolved promotion blockers despite large accepted totals

## D6) External-strategy dependency remains explicit in the archive
- the registry preserves `A1_NEEDS_EXTERNAL_STRATEGY` stop reasons
- the residual subtree preserves a detached `A1_TO_A0_STRATEGY_ZIP`, linking packet-boundary history to that dependency

## D7) Best next descent target
- `RUN_FOUNDATION_BATCH_0001` is the best next bounded batch target
- it is one of the largest preserved families and directly anchors the progress-bundle derivatives
