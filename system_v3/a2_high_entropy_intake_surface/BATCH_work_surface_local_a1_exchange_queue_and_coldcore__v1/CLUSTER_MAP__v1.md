# CLUSTER MAP

Batch id: `BATCH_work_surface_local_a1_exchange_queue_and_coldcore__v1`

## CLUSTER_A: PREPACK_REQUEST_FLOOD

Representative sources
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/requests/000001__A1_EXTERNAL_MEMO_REQUEST__20260306T091555Z.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/requests/000001__A1_EXTERNAL_MEMO_REQUEST__20260306T100007Z.json`

Pattern
- One logical prepack request signature is emitted `2650` times with timestamp/path churn but no captured response.

Why it matters
- This is the clearest queue-pathology residue in the local A1 exchange lane.

## CLUSTER_B: ANSWERED_GRAVEYARD_MEMO_EXCHANGE

Representative sources
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/requests/000006__A1_EXTERNAL_MEMO_REQUEST__20260306T090852Z.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/responses/000006__A1_EXTERNAL_MEMO_RESPONSE__20260306T090852Z.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/responses/000006__A1_EXTERNAL_MEMO_RESPONSE__20260306T091432Z.json`

Pattern
- A richer graveyard-aware request family with `98` terms and `24` rescue targets yields two identical `12`-memo responses.

Why it matters
- This is the only visible closed loop in the bridge residue, even though the closure is duplicated rather than broadened.

## CLUSTER_C: COLD_CORE_REDUCTION_PACKETS

Representative sources
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_transient_cold_core/RUN_GRAVEYARD_VALIDITY_ENTROPY_RATE_LOCAL_0001/cold_core/000001_A1_COLD_CORE_PROPOSALS_v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_transient_cold_core/RUN_SUBSTRATE_FAMILY_EXCHANGE_SMOKE_0011/cold_core/000001_A1_COLD_CORE_PROPOSALS_v1.json`

Pattern
- Multi-role memo inputs are collapsed into small admissible-term candidate packets with explicit corroboration thresholds.

Why it matters
- This preserves a prototype “cold-core” distillation stage between A1 memo exchange and later executable use.

## CLUSTER_D: PYTEST_CACHE_LINKBACK

Representative sources
- `/home/ratchet/Desktop/Codex Ratchet/work/cache_backup/.pytest_cache/README.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/cache_backup/.pytest_cache/v/cache/nodeids`

Pattern
- Only cache residue remains, but it points directly to A1 bridge parsing tests and max-sims enforcement tests.

Why it matters
- The cache is weak evidence, yet it links this spillover family to concrete parser/budget verification work.
