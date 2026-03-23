# A2.2 CANDIDATE SUMMARIES

Batch id: `BATCH_work_surface_local_a1_exchange_queue_and_coldcore__v1`

## Candidate 1: local external memo bridge queue

Summary
- Preserve the `work/a1_sandbox/codex_exchange/provider_bridge` request/response family as a prototype external-A1 memo exchange lane.

Why keep it
- It captures the intended packet contract and shows a real queue/response asymmetry that later cleanup or redesign can target.

Promotion caution
- Do not treat the queue as a successful operational lane; most of the archive is repeated request traffic without matched completion.

## Candidate 2: answered sequence-6 memo response pair

Summary
- Preserve the two `000006` response files as the only visible completed memo-return example in this spillover family.

Why keep it
- They show the intended twelve-role memo layout for a graveyard-aware request packet.

Promotion caution
- The duplicated normalized signature means this is an example response, not evidence of robust multi-turn exchange behavior.

## Candidate 3: cold-core proposal pair

Summary
- Preserve the two `A1_COLD_CORE_PROPOSALS_v1` outputs as prototypes for memo-to-candidate distillation.

Why keep it
- They expose how the lane compresses richer memo traffic into a small admissible-term surface.

Promotion caution
- The packets are not fully state-bound and should not be treated as current executable truth.

## Candidate 4: pytest cache linkback

Summary
- Preserve `work/cache_backup` only as residue showing that A1 bridge parsing and max-sims enforcement tests were in view.

Why keep it
- It is useful as a weak breadcrumb when reconstructing the prototype lane.

Promotion caution
- This is cache residue, not a test report or a validated contract surface.
