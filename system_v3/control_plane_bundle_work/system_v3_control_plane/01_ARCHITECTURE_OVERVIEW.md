
# Architecture Overview

## Layers
- **A2**: high-entropy meta layer (analysis, mining, governance suggestions). Can communicate to A1 only.
- **A1**: nondeterministic structured proposer (emits A1_STRATEGY_v1 objects).
- **A0**: deterministic compiler + state owner + ZIP router + SIM router.
- **B**: deterministic constraint kernel; accepts only `EXPORT_BLOCK vN` containers.
- **SIM**: deterministic validator; emits `SIM_EVIDENCE v1` containers.

## Directional flow (ZIP-mediated)
All cross-layer communication uses typed ZIPs per `specs/ZIP_PROTOCOL_v2.md`.

### FORWARD lane (proposals only)
A2 → A1 → A0 → B

### BACKWARD lane (feedback + save ladder)
B/SIM → A0 → A1 → A2

## Artifact invariants
- Transport is structure-only (no policy logic).
- SAVE ZIPs are informational summaries only.
- B admission is only via `EXPORT_BLOCK vN` containers.
- SIM evidence is only via `SIM_EVIDENCE v1` containers.
- State snapshots are only via `THREAD_S_SAVE_SNAPSHOT v2` containers.

## Federation note (A2 governance only)
- Multi-MMM/decentralized ideation is treated as an A2 governance strategy for exploration diversity and monoculture risk reduction.
- It is not a transport primitive, not a kernel primitive, and not a direct mutation path.
- Any federation output must still traverse the single mutation path via `A1_TO_A0_STRATEGY_ZIP` → A0 compile → `A0_TO_B_EXPORT_BATCH_ZIP`.

## Determinism
- ZIP validation determinism is defined over extracted file bytes under canonicalization rules.
- A0 determinism is defined by `A0-DET-01` (see `specs/ZIP_PROTOCOL_v2.md` and `validator_contract/A0_DETERMINISM_TEST.md`).

## Non-goals
- No architecture redesign.
- No new container primitives.
- No probabilistic reasoning inside B/A0/SIM or transport.
