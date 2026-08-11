# CB Light first fixture wave — premortem

**Run:** 2026-08-10 (America/Los_Angeles)  
**Method:** five independent failure-analysis dives, then a bounded synthesis.  
**Scope:** design guardrails for the first contained CB Light fixture wave. This is not a wave execution, tool admission, portability proof, or promotion evidence.

## Premise

It is six months later and the first CB Light fixture wave failed: its receipts and graphs looked convincing, but it could not prove what ran, whether inputs were independent, or whether model-shaped output affected a deterministic settlement.

## Target plan being falsified

Build one small, contained, Light-only fixture after the now-exercised installer and Pydantic control-plane seams:

1. Seal a typed `IssueCard` and a strict `ProbePacket`.
2. Run exactly three local deterministic fake adapters: witness/operation, falsifier/counterexample, and evidence map.
3. Validate topology with Rustworkx and settle only a finite, locally recomputed FactSet with Z3 plus an enumerated cross-check.
4. Persist append-only SQLite attempt/receipt lineage and replay it from raw local observations.
5. Return only a local fixture disposition (`SETTLED`, `HOLD`, `REFUSE`, or `EXPIRED`) with `promotion_allowed=false`.

The fixture may bind skills, MMMs, formal agents, and models as **references** in its many-to-many ledger, but reference is not invocation. It does not require PydanticAI, a network provider, a Heavy/simulation engine, or portability claims.

## Raw failure reasons

| Dive | How it failed | Early warning | Binding safeguard |
| --- | --- | --- | --- |
| Authority/provenance | A typed reference and favorable topology became rendered as “asset used,” although no skill/model/MMM had actually run. | A cited binding lacks a foreign-keyed invocation receipt; severing a fake adapter's declared asset does not HOLD. | Separate `declared`, `resolved`, `bound`, `invoked`, and `receipt_verified`; only receipt-verified invocation can be cited as evidence. |
| Input diversity | Nominally plural councils shared a normalized packet, evidence digest, adapter, prompt, and seed: apparent corroboration was one premise copied three times. | High input/evidence identity or near-identical output; cloned branches retain provenance. | Store context/evidence/lineage/adapter/seed hashes; label correlated branches and deny corroboration credit; test clone and severance controls. |
| State/lineage | Reused deterministic IDs and mutable receipt paths let a retry overwrite or join a different attempt's evidence. | One plan key maps to multiple timestamps/hashes; a sealed result has an incomplete closure. | Separate plan fingerprint from immutable `attempt_id`; content-address raw receipts; append only terminal attempts and HOLD on missing or mutated evidence. |
| Gate non-authority | Adapter `PASS`, model verdict, or reference status became a solver input, so schema and graph checks ratified an assertion-shaped receipt. | Toggling `provider_pass` or model verdict changes settlement; replay works after adapter/raw bytes are missing. | Gate only a whitelisted, freshly reverified FactSet; adapters emit observations, never PASS/promotion; prove noninterference and recompute on replay. |
| Scope creep | Generic framework/adapters/simulation placeholders obscured the finite fixture and turned local success into an implied portability claim. | New dependency/config layer lacks a finite predicate and receipt field; “portable” appears without OS execution evidence. | Freeze a one-wave dependency allowlist and reject PydanticAI, network clients, Heavy/sim packages, and generic agent frameworks in the contained fixture source. |

## Non-negotiable design gates

The implementation is not ready to exercise until all of these are specified and tested:

1. **Immutable execution identity.** A `plan_fingerprint` is distinct from an append-only `attempt_id`. Every adapter observation and raw receipt is content-addressed and foreign-keyed to the attempt.
2. **Explicit many-to-many asset state.** A binding records asset identity/version/digest, role, adapter identity, mode (`reference_only` or `local_fake_invoked`), and its evidence state. `reference_only` cannot satisfy an invocation or authority predicate.
3. **Deterministic settlement boundary.** The final function accepts only local, reverified facts. It rejects model verdicts, provider PASS fields, promotion fields, unknown fields, stale raw bytes, mismatched asset digests, and absent falsifier output.
4. **Independence ledger.** Each probe records packet/context/evidence/lineage/adapter/seed hashes. Identical or correlated input is visible and cannot manufacture corroboration.
5. **Replay as recomputation.** Replay re-executes the local adapters and revalidates raw observations; it does not merely re-read a successful status row.
6. **Dependency ceiling.** The first fixture may use stdlib SQLite, Pydantic/jsonschema, Rustworkx, Z3, and the enumerator already in the Light contract, plus exactly three local fake adapters. It must not import PydanticAI, provider SDKs, network clients, Heavy/simulation packages, or generic agent frameworks.
7. **Literal claim ceiling.** A passing fixture is a local, synthetic, non-authoritative exercise. It does not admit tools, prove portability, invoke a real skill/MMM/model, enable promotion, or establish CB Heavy integration.

## Required falsification controls

| Control | Expected result |
| --- | --- |
| Positive sealed fixture | Local `SETTLED`; `promotion_allowed=false`. |
| Forged provider/model PASS | `REFUSE`; provider/model assertion cannot influence settlement. |
| Missing or altered raw observation | `HOLD`; no stale result reused. |
| Bound-but-uninvoked external asset | `HOLD_UNINVOKED_ASSET`; report never says “used.” |
| Mismatched asset digest / wrong adapter identity | `REFUSE`. |
| Correlated clone of a probe | Visible as correlated; no independent corroboration credit. |
| Replay with a new `attempt_id` | Same deterministic local result only after re-execution and hash verification. |
| Concurrent duplicate plan attempts | Separate immutable attempts; no cross-attempt join or overwrite. |
| PydanticAI/Heavy/network import in fixture source | Build/source-boundary test fails. |
| Remove a required falsifier branch | `HOLD`, never implicit success. |

## Revised execution order

1. Write the sealed schema, state machine, FactSet, and negative-control contract.
2. Implement the smallest contained fixture in `light_runtime/src/constraintbox`, with no legacy-source import.
3. Add the ten controls above, then run source-boundary, clean-wheel, and deterministic replay checks.
4. Only after that, create an adapter boundary for an actually invoked skill/MMM/model; it must earn `invoked` and `receipt_verified` separately.
5. Run macOS, Linux, and Windows evidence lanes before any portable-adoption claim.

## Decision

Proceed only with the narrow fixture described above. Do not implement generic nested-council orchestration, PydanticAI, model-provider execution, or simulation integration as part of this slice.

