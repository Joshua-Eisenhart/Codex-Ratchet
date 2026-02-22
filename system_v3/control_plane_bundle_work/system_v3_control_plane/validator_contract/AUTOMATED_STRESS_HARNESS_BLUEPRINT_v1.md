# AUTOMATED_STRESS_HARNESS_BLUEPRINT v1

## Objective

Continuously validate:
- ZIP transport determinism and fail-closed behavior
- A1 “real wiggle” enforcement (structural distinctness)
- repair mapping correctness (non-transport failures only)
- promotion gating correctness (deterministic labels)
- replay integrity
- no mutation leakage outside the mutation path

## Harness location (recommended)

`runtime/bootpack_b_kernel_v1/tests/ratchet_stress_harness/`

## Required artifact discipline

- Test inputs are ZIPs plus initial state snapshot bytes.
- Test outputs are deterministic digests and outcomes.
- No live LLM calls are required.

## Required scenario families (must map to tags/gates)

### Family A — ZIP validator reject tags (REJECT)

For each reject tag in `specs/ENUM_REGISTRY_v1.md` (`reject_tag`), provide at least one scenario ZIP that deterministically triggers it.

Each scenario MUST record:
- zip_type
- expected outcome = REJECT
- expected reject tag

### Family B — Sequence handling (PARK)

Provide:
- `sequence_gap` scenario: `sequence > last_accepted + 1` → expected outcome PARK (and only PARK).

### Family C — Replay integrity

Provide a multi-ZIP chain that includes both FORWARD and BACKWARD ZIPs.

Required checks:
- Replay the chain twice from the same initial state → identical final state hash and identical emitted artifact digests.
- Backward gating: BACKWARD ZIPs must not be applied unless prior FORWARD ZIPs are validated or deterministically parked (per ZIP_PROTOCOL_v2 Replay Integrity Rule).

### Family D — Real wiggle enforcement (A0-level admission failures)

Provide A1 strategies that deterministically fail:
- structural distinctness (alternatives structurally identical to targets under `STRUCTURAL_DIGEST_v1`)
- forbidden keys present (confidence/probability/etc.)
- self-hash mismatch (recursion-safe rule)

Expected:
- ZIP validator OK (structure is fine)
- A0 admission deterministically rejects and emits no B-facing artifacts.

### Family E — Promotion gating determinism

Provide controlled histories (via SAVE summaries and SIM outcomes) that deterministically yield:
- NOT_READY (missing negative sims)
- NOT_READY (kill_signal present)
- READY_FOR_TIGHTEN (meets configured gates)
- READY_FOR_CANON (meets configured gates, no kill signals, sufficient operator diversity)

Promotion state transitions MUST NOT mutate canon directly.

## Mandatory replay gate

Any change that results in B mutation MUST be accompanied by a replay test that passes deterministically.
