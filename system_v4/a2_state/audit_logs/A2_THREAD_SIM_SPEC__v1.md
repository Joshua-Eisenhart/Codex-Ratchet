# A2 FUEL: THREAD SIM SPECIFICATION
**STATUS:** A2 HIGH-ENTROPY FUEL — SOURCE-BEARING EXTRACT
**AUTHORITY:** A2 DISTILLERY (NotebookLM, 240 sources)

## Thread SIM Role
Thread SIM is a deterministic evidence WRAPPER — it does NOT execute simulations. It validates and normalizes results into kernel-safe `SIM_EVIDENCE v1` containers for Thread B.

## Normalization Protocol

### Deterministic Hashing (Three Hashes)
- `CODE_HASH_SHA256`: hash of exact source code executed (64 lowercase hex chars)
- `INPUT_HASH_SHA256`: hash of canonically sorted JSON of simulation inputs (64 lowercase hex chars)
- `OUTPUT_HASH_SHA256`: hash of canonically sorted JSON of simulation outputs (64 lowercase hex chars)
- Thread SIM audits and rejects any hash not exactly 64 lowercase hex characters

### Batch Auditing (`SIM_MANIFEST_AUDIT`)
- Ingests via `EMIT_SIM_EVIDENCE_PACK` command
- Scans for required fields: `SIM_ID`, `CODE_HASH_SHA256`, `OUTPUT_HASH_SHA256`, `EVIDENCE_TOKEN`
- On failure: emits `REFUSAL v1` detailing the errors

### Duplicate SIM_ID Handling (Two Modes)
- **Manifest Audit Mode** (`AUDIT_SIM_EVIDENCE_PACK_REQUEST`): Duplicate `SIM_ID` detected → reject ENTIRE batch → emit `REFUSAL v1`
- **Internal Buffer Mode** (individual runs): Buffer stores only LATEST result per `SIM_ID` — duplicate overwrites previous

### Metadata Injection
- Extracts `BRANCH_ID` and `BATCH_ID` from request headers
- Auto-injects as `METRIC:` lines (format: `METRIC: key=value`) into every normalized block

### Grammar Enforcement
- Output structured as `SIM_EVIDENCE v1` grammar
- Contains: ID, hashes, repeatable `METRIC: key=value` pairs, `EVIDENCE_SIGNAL` token
- Maps simulation to required canonical evidence

### Final Output
- Flushed as single `SIM_EVIDENCE_PACK` (back-to-back blocks)
- No prose allowed before, between, or after blocks
- Pure deterministic results only — safe for Thread B ingestion
