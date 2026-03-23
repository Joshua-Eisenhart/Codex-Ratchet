# A2.3 DISTILLATES

Batch id: `BATCH_work_surface_local_a1_exchange_queue_and_coldcore__v1`

## Reusable process patterns

### 1. External memo bridge packet shape
- Request packets bundle one high-entropy A1 context excerpt, prompt-path fanout, required role set, term candidates, and optional graveyard rescue targets.
- Response packets return a memo list keyed by role.

### 2. Queue-pathology detection by normalization
- Comparing raw packets alone overstates novelty because timestamps and prompt paths churn.
- Normalized signature counting cleanly separates real semantic variation from repeated queue emissions.

### 3. Cold-core reduction stage
- Multi-role A1 memo traffic can be distilled into a compact `A1_COLD_CORE_PROPOSALS_v1` packet with:
  - admissible term candidates
  - corroboration threshold
  - atomic bootstrap needs
  - aggregated negative classes

### 4. Thin parser/budget test linkback
- Even bare pytest cache residue is enough to reveal which concrete tests were exercising the exchange lane.

## Migration debt and contradictions preserved

### 1. Request flooding without matched completion
- The `000001` prepack family floods the queue for roughly `44` minutes with no captured response.

### 2. Duplicate closed-loop response
- The only answered family normalizes to one repeated response payload.

### 3. Stable overlay, unstable scope
- The same A1 context excerpt is reused across a small prepack request and a much richer graveyard-aware request family.

### 4. Distillation outputs are under-bound
- `state_hash` is empty in both cold-core packets, so the reduction stage loses a clear state anchor.

### 5. Cache residue is evidentiary but too weak for promotion
- It suggests tests existed, but not enough survives to treat the cache as authoritative proof of correctness.
