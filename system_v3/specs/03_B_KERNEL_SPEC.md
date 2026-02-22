# B Kernel Specification
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-020..RQ-029`, `RQ-060..RQ-064`

## Authority
Behavior is anchored to:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/BOOTPACK_THREAD_B_v3.9.13.md`

If boot text is ambiguous, result is `UNKNOWN` and admission is blocked.

## Implementer Reference Extract (Non-Owner Helper)
For a compact, implementer-facing extract of enforceable grammar + fences, see:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md`

## Accepted Containers (`RQ-020`)
- `EXPORT_BLOCK vN`
- `SIM_EVIDENCE v1`
- `THREAD_S_SAVE_SNAPSHOT v2`

Any other container shape -> `REJECT` (`SCHEMA_FAIL` class).

## Rejection Tag Fence (`RQ-021`)
Allowed tags (verbatim class set):
- `MULTI_ARTIFACT_OR_PROSE`
- `COMMENT_BAN`
- `SNAPSHOT_NONVERBATIM`
- `UNDEFINED_TERM_USE`
- `DERIVED_ONLY_PRIMITIVE_USE`
- `DERIVED_ONLY_NOT_PERMITTED`
- `UNQUOTED_EQUAL`
- `SCHEMA_FAIL`
- `FORWARD_DEPEND`
- `NEAR_REDUNDANT`
- `PROBE_PRESSURE`
- `UNUSED_PROBE`
- `SHADOW_ATTEMPT`
- `KERNEL_ERROR`
- `GLYPH_NOT_PERMITTED`

Any out-of-fence tag -> `REJECT_BLOCK SCHEMA_FAIL`.

## Enforceable Rule Index (Bootpack Rule IDs)
This file does not redefine bootpack semantics; it indexes what must be implemented to satisfy `RQ-020..RQ-029`.

- Message/container discipline: `MSG-001..MSG-003`, `RPT-001`
- Tag fence: `BR-000A`
- Dependency definition + forward refs: `BR-005`, `BR-006`
- Near-duplicate parking: `BR-007`
- Formula containment + formula fences: `BR-008`, `BR-0F1..BR-0F7`
- Lexeme fence for underscore compounds: `LEX-001`
- Undefined-term + ASCII/mixedcase fences (CONTENT): `BR-0U1..BR-0U5`
- Derived-only scan + permission: `BR-0D1`, `BR-0D2`
- Probe pressure + utilization: `BR-009`, `BR-010`
- SIM-only execution policy: `BR-013`
- KILL_IF semantics: `BR-011`, `BR-012`
- Deterministic parking priority: `BR-014`
- Optional header gates: `MBH-010`, `MBH-011`, `MBH-001`, `MBH-002`
- Evidence state transitions: `EV-000`, `EV-002..EV-004`
- Deterministic stage order: `STAGE 1..7`
- Snapshot enumeration requirements: `INT-002`, `INT-005`

## Item Header/Field Grammar (`RQ-021`)
Allowed item headers:
- `AXIOM_HYP <ID>`
- `PROBE_HYP <ID>`
- `SPEC_HYP <ID>`

Allowed fields:
- `AXIOM_KIND <ID> CORR <KIND>`
- `PROBE_KIND <ID> CORR <KIND>`
- `SPEC_KIND <ID> CORR <KIND>`
- `REQUIRES <ID> CORR <DEP_ID>`
- `ASSERT <ID> CORR EXISTS <TOKEN_CLASS> <TOKEN>`
- `WITNESS <ID> CORR <TOKEN>`
- `KILL_IF <ID> CORR <COND_TOKEN>`
- `DEF_FIELD <ID> CORR <FIELD_NAME> <VALUE...>`

## Term Pipeline Shapes (minimum operational set)
Supported target kinds in system_v3 pipeline:
- `MATH_DEF`
- `TERM_DEF`
- `LABEL_DEF`
- `CANON_PERMIT`
- `SIM_SPEC`

Unknown kind behavior in boot text is not fully explicit; system_v3 policy: treat as `SCHEMA_FAIL` until explicitly admitted by boot-backed extension.

## Deterministic Stage Order (`RQ-029`)
Kernel stage order is fixed:
1. `STAGE 1 AUDIT_PROVENANCE`
2. `STAGE 1.5 DERIVED_ONLY_GUARD (EXPORT_BLOCK CONTENT ONLY)`
3. `STAGE 1.55 CONTENT_DIGIT_GUARD (EXPORT_BLOCK CONTENT ONLY)`
4. `STAGE 1.6 UNDEFINED_TERM_FENCE (EXPORT_BLOCK CONTENT ONLY)`
5. `STAGE 2 SCHEMA_CHECK`
6. `STAGE 3 DEPENDENCY_GRAPH`
7. `STAGE 4 NEAR_DUPLICATE`
8. `STAGE 5 PRESSURE`
9. `STAGE 6 EVIDENCE_UPDATE`
10. `STAGE 7 COMMIT`

No stage reordering is permitted.

## Fence Contracts
Undefined-term fence (`RQ-022`):
- scan lowercase tokens in `EXPORT_BLOCK CONTENT` outside exempt string contexts
- segments must exist in L0 lexeme set or term registry

Derived-only fence (`RQ-023`):
- derived-only literals are forbidden as primitive usage outside exempt contexts until canonical allowed

Lexeme fence (`RQ-024`):
- for `TERM_DEF` compounds, each underscore component must be in L0 set or admitted term registry

Glyph/formula guards (`RQ-025`):
- formula/content glyphs require admitted gate terms (`equals_sign`, `digit_sign`, glyph map terms)

Probe pressure (`RQ-026`):
- per 10 newly accepted `SPEC_HYP`, require >= 1 newly accepted `PROBE_HYP`
- unmet pressure parks lowest-priority spec items by deterministic parking rule

## Scan-Exempt Contexts (`RQ-021`)
Undefined/derived scans ignore literals inside:
- `DEF_FIELD ... TERM "<...>"`
- `DEF_FIELD ... LABEL "<...>"`
- `DEF_FIELD ... FORMULA "<...>"`

And ignore full lines containing:
- `DEF_FIELD ... SIM_CODE_HASH_SHA256`

## Lexeme Bootstrap Set (`RQ-024`)
Initial lexeme set (verbatim bootstrap):
- `finite`, `dimensional`, `hilbert`, `space`, `density`, `matrix`, `operator`
- `channel`, `cptp`, `unitary`, `lindblad`, `hamiltonian`, `commutator`
- `anticommutator`, `trace`, `partial`, `tensor`, `superoperator`, `generator`

## Outcome Semantics (`RQ-027`)
- `ACCEPT`: append survivor order; mutate canon state.
- `PARK`: not admitted; retained for deterministic replay/unpark.
- `REJECT`: not admitted; write graveyard record.

## Graveyard Write Contract (`RQ-028`, `RQ-060..RQ-064`)
Every rejection record must include:
- `candidate_id`
- `reason_tag`
- `raw_lines`
- `failure_class` (`B_KILL` or `SIM_KILL`)
- `target_ref` (if alternative/negative linked)

Meaningful survivors must carry explicit links to:
- negative sim ids
- graveyard alternative ids

Forbidden:
- no-raw-line rejects
- untied junk alternatives used for ratio inflation

## Evidence Ingestion
On `SIM_EVIDENCE`:
- verify target/sim id exists
- verify evidence token match policy
- update evidence pending and term state transition
- keep deterministic transition logs

Invalid target/token -> `REJECT`.

## State Invariants
- root constraints immutable (`RQ-001`, `RQ-002`)
- append-only survivor order
- append-only graveyard
- deterministic state serialization
