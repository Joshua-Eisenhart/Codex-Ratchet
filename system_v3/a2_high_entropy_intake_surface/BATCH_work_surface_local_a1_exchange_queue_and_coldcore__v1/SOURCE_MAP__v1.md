# SOURCE MAP

Batch id: `BATCH_work_surface_local_a1_exchange_queue_and_coldcore__v1`

Scope
- Bounded `work/` archaeology pass over the local A1 prototype exchange lane: a sandboxed external-memo bridge queue under `work/a1_sandbox`, two distilled cold-core proposal outputs under `work/a1_transient_cold_core`, and a thin pytest cache residue under `work/cache_backup`.
- This preserves prototype mechanics and migration debt only. Nothing here is active system law.

## Source set A: local external-memo bridge queue

Primary anchors
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/requests/000001__A1_EXTERNAL_MEMO_REQUEST__20260306T091555Z.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/requests/000001__A1_EXTERNAL_MEMO_REQUEST__20260306T100007Z.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/requests/000006__A1_EXTERNAL_MEMO_REQUEST__20260306T090852Z.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/responses/000006__A1_EXTERNAL_MEMO_RESPONSE__20260306T090852Z.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/responses/000006__A1_EXTERNAL_MEMO_RESPONSE__20260306T091432Z.json`

Observed structure
- `requests/` contains `2655` JSON packets total.
- Prefix `000001` accounts for `2650` requests spanning `2026-03-06T09:15:55Z` through `2026-03-06T10:00:07Z`.
- Prefix `000006` accounts for `5` requests spanning `2026-03-06T09:08:52Z` through `2026-03-06T09:14:32Z`.
- `responses/` contains only `2` JSON packets, both for prefix `000006`.
- Normalized request comparison collapses the queue into only `2` logical signatures:
  - prepack request signature, sequence `1`, `30` term candidates, `0` graveyard rescue targets, repeated `2650` times
  - graveyard-aware request signature, sequence `6`, `98` term candidates, `24` graveyard rescue targets, repeated `5` times
- Both request families reuse the same `a1_brain_context.excerpt_sha256`:
  - `ad41d1e6f20a078913cf7dfd1d9e16a2d989c0ffc7d92a583f9266bb772d5ef8`

Useful residue
- The queue preserves the packet shape for a local provider bridge: high-entropy A1 context excerpt, prompt path bundle, required role set, term candidate set, and optional graveyard rescue target set.

## Source set B: answered sequence-6 response pair

Primary anchors
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/responses/000006__A1_EXTERNAL_MEMO_RESPONSE__20260306T090852Z.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_sandbox/codex_exchange/provider_bridge/responses/000006__A1_EXTERNAL_MEMO_RESPONSE__20260306T091432Z.json`

Observed structure
- Normalized response comparison yields only `1` signature repeated twice.
- Each response is `A1_EXTERNAL_MEMO_RESPONSE_v1` for the graveyard-aware request signature, sequence `6`, with `12` memos.
- Memo roles are stable across both files:
  - `BOUNDARY_REPAIR`
  - `DEVIL_CLASSICAL_TIME`
  - `DEVIL_COMMUTATIVE`
  - `DEVIL_CONTINUUM`
  - `DEVIL_EQUALS_SMUGGLE`
  - `ENGINE_LENS_SZILARD_CARNOT`
  - `ENTROPY_LENS_MUTUAL`
  - `ENTROPY_LENS_VN`
  - `RESCUER_MINIMAL_EDIT`
  - `RESCUER_OPERATOR_REFACTOR`
  - `STEELMAN_ALT_FORMALISM`
  - `STEELMAN_CORE`

Useful residue
- This preserves the intended multi-role memo response shape even though the capture count is extremely small relative to the request flood.

## Source set C: transient cold-core distillations

Primary anchors
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_transient_cold_core/RUN_GRAVEYARD_VALIDITY_ENTROPY_RATE_LOCAL_0001/cold_core/000001_A1_COLD_CORE_PROPOSALS_v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/a1_transient_cold_core/RUN_SUBSTRATE_FAMILY_EXCHANGE_SMOKE_0011/cold_core/000001_A1_COLD_CORE_PROPOSALS_v1.json`

Observed structure
- entropy-rate cold-core packet:
  - schema `A1_COLD_CORE_PROPOSALS_v1`
  - `memo_count = 24`
  - `min_corroboration = 2`
  - admissible term candidates collapse to one item: `entropy_production_rate`
  - `need_atomic_bootstrap = ["entropy", "production", "rate"]`
  - `state_hash = ""`
- substrate-family cold-core packet:
  - schema `A1_COLD_CORE_PROPOSALS_v1`
  - `memo_count = 10`
  - `min_corroboration = 1`
  - admissible term candidates:
    - `cptp_channel`
    - `density_matrix`
    - `finite_dimensional_hilbert_space`
    - `partial_trace`
    - `positive_semidefinite`
    - `probe_operator`
    - `trace_one`
  - `state_hash = ""`

Useful residue
- These files preserve a prototype reduction stage from role-level memo traffic into a much smaller admissible-term packet.

## Source set D: cache backup residue

Primary anchors
- `/home/ratchet/Desktop/Codex Ratchet/work/cache_backup/.pytest_cache/README.md`
- `/home/ratchet/Desktop/Codex Ratchet/work/cache_backup/.pytest_cache/v/cache/nodeids`

Observed structure
- This is ordinary pytest cache residue, not a designed A1 surface.
- The cache preserves `6` recent node ids:
  - `5` tests under `system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_bridge_parsing.py`
  - `1` test under `system_v3/runtime/bootpack_b_kernel_v1/tests/test_max_sims_enforced.py`

Useful residue
- Even as thin residue, this cache ties the local exchange lane to parser-hardening and budget-enforcement tests.
