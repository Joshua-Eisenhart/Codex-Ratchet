# SIM Evidence and Tier Specification
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-050..RQ-059`

Companion repair target:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/72_SIM_CAMPAIGN_AND_SUITE_MODES__v1.md`

## Kernel-Facing Artifact Grammar (Bootpack B)
Thread B consumes SIM evidence only via `SIM_EVIDENCE v1` blocks (optionally as a `SIM_EVIDENCE_PACK`).

Canonical container grammar (authority: `core_docs/BOOTPACK_THREAD_B_v3.9.13.md`):
```text
CONTAINER SIM_EVIDENCE v1
BEGIN SIM_EVIDENCE v1
SIM_ID: <ID>
CODE_HASH_SHA256: <hex>
OUTPUT_HASH_SHA256: <hex>
METRIC: <k>=<v>
EVIDENCE_SIGNAL <SIM_ID> CORR <TOKEN> (repeatable)
KILL_SIGNAL <TARGET_ID> CORR <TOKEN>  (optional, repeatable)
END SIM_EVIDENCE v1
```

Pack discipline (message-level):
- A `SIM_EVIDENCE_PACK` is one or more complete `SIM_EVIDENCE v1` blocks back-to-back.
- No other text before/between/after blocks.

## Core Rule
Static admission is insufficient.
Meaningful survivor status requires evidence + graveyard alternatives.

## Evidence Bar (`RQ-050..RQ-052`)
Meaningful survivor requires:
- positive sim evidence
- negative sim evidence
- plausible failed alternatives in graveyard

## Negative Sim Definition (`RQ-053`)
Negative sim is a falsification test with required fields:
- `target_id`
- `failure_mode_id`
- `expected_outcome_class`
  - `NEG_EXPECT_FAIL_TARGET`
  - `NEG_EXPECT_REJECT_ALTERNATIVE`

Negative sim is not a generic failure artifact.

## Deterministic Evidence (`RQ-054`)
Every sim manifest includes:
- `sim_id`
- `tier`
- `family`
- `input_hash`
- `code_hash`
- `output_hash`
- `manifest_hash`
- `evidence_tokens[]`

Replay with same code+input must reproduce hashes.

Hash definitions (deterministic; implementation-level):
- `code_hash` is `sha256` of the exact sim source content that was executed.
- `input_hash` is `sha256` of a canonical JSON encoding of sim inputs (sorted keys; stable lists).
- `output_hash` is `sha256` of the canonical output artifact(s) referenced by the SIM_EVIDENCE block(s).

## Tier Architecture (`RQ-055`)
- `T0_ATOM`
- `T1_COMPOUND`
- `T2_OPERATOR`
- `T3_STRUCTURE`
- `T4_SYSTEM_SEGMENT`
- `T5_ENGINE`
- `T6_WHOLE_SYSTEM`

Rules:
- explicit acyclic dependencies
- no tier-skip promotion
- stage/suite process discipline is defined separately in the companion campaign spec

## Stress Families (`RQ-056`)
Required per target class:
- `BASELINE`
- `BOUNDARY_SWEEP`
- `PERTURBATION`
- `ADVERSARIAL_NEG`
- `COMPOSITION_STRESS`

## Threshold Profile (`RQ-058`)
Initial minimum per target class:

| Tier | Baseline | Boundary | Perturb | Adversarial | Composition |
| --- | --- | --- | --- | --- | --- |
| T0 | 1 | 2 | 4 | 2 | 0 |
| T1 | 1 | 3 | 6 | 3 | 1 |
| T2 | 2 | 4 | 8 | 4 | 2 |
| T3 | 2 | 5 | 10 | 5 | 3 |
| T4 | 3 | 6 | 12 | 6 | 4 |
| T5 | 3 | 8 | 14 | 8 | 6 |
| T6 | 5 | 10 | 20 | 10 | 10 |

These are initial noncanon defaults for stress richness.

## Master Sim Gate (`RQ-057`)
`T6_WHOLE_SYSTEM` requires:
- all lower-tier coverage closed
- full stress family coverage
- whole-system negative sim evidence
- graveyard alternatives for whole-system variants
- reproducibility pass
- no bypass flags

## Promotion Deficit Reporting (`RQ-059`)
Every promotion attempt report includes:
- gate status by gate id
- deficit counts per missing family/tier
- blocking dependency ids
- unresolved evidence token ids

## Graveyard Link Completeness (`RQ-064`)
Meaningful survivor records must include:
- `negative_sim_ids[]`
- `alternative_graveyard_ids[]`

## SIM Kill Recording
Failed sims that invalidate candidates write:
- `SIM_KILL`
- target reference
- failure mode id
- replay pointers to manifest/output
