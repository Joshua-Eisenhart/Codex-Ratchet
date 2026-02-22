# A0 Contract (deterministic orchestrator)

Status: NONCANON | Updated: 2026-02-18
Implementation: `ratchet_core/a0_generator_v2.py`, `ratchet_core/containers.py`
Authority source: `work/rebaseline/BOOTPACK_THREAD_A0_v2.62__VERBATIM.md`

## What A0 is (topology pointer)

See Megaboot thread topology quote in `work/rebaseline/BOUNDARY_QUOTES_A0_A1_A2.md`.

## Output discipline (hard)

From `BOOTPACK_THREAD_A0_v2.62` (verbatim file):

- A0 default output is **phone-first** (short and skimmable).
- A0 must use a fixed frame: `[ROUTE]`, `[OUTPUT]`, `[OPTIONS]`, `[CITES]`.
- All user-copyable payloads must be real code-fenced `text` blocks preceded by `COPY TO: ...`.
- Atomicity: each box is exactly one executable unit (request line, one EXPORT_BLOCK, one intent invocation, one terminal command).

## Determinism boundary (hard, practical)

- A0 is not the place to “explain physics” or mine high-entropy sources.
- A0 routes/packaging only; interpretation belongs upstream (A2/A1) and canon acceptance belongs downstream (B).

## Batch policy (Megaboot HARD)

From Megaboot Section 0:

- Batches must not be conservative. The system converges via massive exploration under finitude and noncommutation.
- Constraint systems begin with large sets and converge toward attractor basins.
- Any "classical proof thinking" behavior in A0/A1 outputs is treated as drift and must be corrected.

Related mandatory structures:

- **Graveyard**: mandatory and never dead; must be larger than active canon; A0 must target >= 50% graveyard rescue share in batches when non-empty.
- **Campaign tape**: mandatory; records proposal + B report pairs; used to reconstruct graveyard pressure.
- **Export tape**: pre-run planned batch list; used for mega batching.

## Current implementation

`a0_generator_v2.py` is a hardcoded 19-term ladder compiler. It generates EXPORT_BLOCKs
from a fixed term sequence. Used by `--run-once` and `--cycle` modes.

In `--full-cycle` mode, A0's role is handled by `a1_protocol.compile_batch()` which
compiles A1-expanded items into EXPORT_BLOCK format via `containers.build_export_block()`.

The "creative layer" from the original design is now the A1 LLM half.
The "compiler layer" is `a1_protocol.expand_strategy()` + `compile_batch()`.

## Pointer

- Verbatim boot: `work/rebaseline/BOOTPACK_THREAD_A0_v2.62__VERBATIM.md`
