---
name: cb-formalization-digger-wave
description: Draft four source-bound formalization proposals from a verified context-epoch.v2 and capability-probe-map receipt; never decide truth or activate a gate.
---

# CB formalization/digger candidate wave

This directory is an inactive `NEW_CANDIDATE`. It is a structural proposal
wave, not a decision council and not an admission gate. The runner requires a
declared repository root and consumes the actual `constraintbox.context-epoch.v2`
fixture through the current repo-held `seal_context_epoch.py` verifier. It also
consumes the actual `constraintbox.capability-probe-map-receipt.v1` emitted by
`cb-capability-probe-map-wave` and calls that producer's `verify_receipt`.

The sealer verifies the complete epoch parent chain and every bound file. The
capability receipt is stale if its producer, definition, registry, or any
bound capability source changes. The runner also re-runs the model-free
capability producer through the repository-declared
`constraint_box/.venv/bin/python` controller interpreter (never an ambient
`CB_*` interpreter override) and requires the exact
inactive producer identity (`wave_id`, candidate state, and `HOLD` status),
receipt and stable semantic projection to match the supplied fixture. Raw
runtime-path evidence may differ after extraction, but it is excluded from the
projection and the declared interpreter remains bound. A self-resealed
capability receipt therefore cannot launder a changed map into this wave. All
input and output paths are root-confined; absolute escapes, `..`, and symlink
components are refused.

## Four bounded children

The children are explicit and independent in the definition:

1. `axiom_digger` (`assumption-audit`) names assumptions and non-objectives.
2. `constraint_digger` (`distinguishability-smt`) drafts finite candidate
   predicates and their declared domains.
3. `gate_digger` (`specification-boundary`) drafts candidate gate obligations
   together with reason-specific negative cases. It never runs a gate.
4. `basin_digger` (`voice-zhuangzi`) drafts probe-relative quotient, mass, and
   topology interpretations. These are interpretations to test, not basin
   observations or geometry claims.

The declared skills are composition provenance only. Fixture children emit
`terminal_state: PROPOSAL_VALIDATED` and
`skill_execution_claimed: false`; no child provider or skill execution is
claimed.

## Inputs and invocation

From the repository root:

```bash
python3 constraint_box/integrated_system/skills/cb-formalization-digger-wave/scripts/run_formalization_digger.py \
  --root /absolute/path/to/constraintbox-integrated-20260817 \
  --context-epoch constraint_box/integrated_system/skills/cb-formalization-digger-wave/fixtures/context_epoch_v2.json \
  --capability-probe-map constraint_box/integrated_system/skills/cb-formalization-digger-wave/fixtures/capability_probe_map_v1.json \
  --proposals constraint_box/integrated_system/skills/cb-formalization-digger-wave/fixtures/digger_proposals_v2.json \
  --out constraint_box/integrated_system/skills/cb-formalization-digger-wave/formalization-digger.receipt.json
```

The runner is stdlib-only and model-free. A model-backed route may be
designed by a later owner, but no provider call is made or claimed. Each
`source_refs` value is a strict `{path, sha256}` row. It must resolve under
the declared root and match either an epoch-bound file or a source/wrapper
binding in the capability receipt.

## Strict proposal and receipt contracts

Every child object binds the real `epoch_digest` and capability
`receipt_sha256`, and sets `proposal_only: true`, `observations: []`,
`decisions: []`, and `activation_requested: false`. Child-specific fields are
closed schemas:

- axiom: named `assumptions` and named `non_objectives`;
- constraint: finite `predicates` with explicit candidate status and domain;
- gate: candidate `obligations` plus explicit `negatives` and dispositions;
- basin: probe IDs plus candidate `quotient`, `mass`, and `topology`
  interpretations.

The candidate receipt binds runner, epoch-sealer, capability-producer,
definition, and registry source SHAs; raw input SHAs; semantic epoch and
capability IDs; the freshly reproduced capability receipt/projection; child
output digests; frontier and contradiction digests; and a self SHA.
`verify_receipt` and replay re-read the root-confined inputs. PASS and
CANCELLED receipts are recomputed from those inputs, while REFUSE receipts
must exactly match a fresh refusal replay; a self-resealed refusal cannot
change its reason or error list.

Semantic contradictions are retained as `UNRESOLVED` rows in the non-voting
frontier. They do not select a winner, activate a gate, or decide truth.
Structural/schema contradictions still refuse compilation.

## Terminals and controls

- `PASS` — all four fixture proposals validate and a non-voting frontier is
  compiled.
- `REFUSE` — malformed/tampered source, stale producer, path escape, schema
  failure, structural contradiction, or an activation/truth/observation
  request.
- `CANCELLED` — cancellation requested before compilation; the self-bound
  receipt proves `frontier: null`, no frontier/output artifact write, and no
  authority state.

The tests cover real-input verification, stale producer, path/symlink refusal,
source and receipt tampering, exact replay, cancellation, and semantic
contradiction preservation.

## Claim ceiling

The candidate proves only deterministic validation of four source-bound,
proposal-only structural objects and compilation of a non-voting frontier.
It does not invent observations, decide truth, establish a gate, prove a
basin, quotient, mass, topology, provider route, portability, promotion, or
any external scientific claim.
