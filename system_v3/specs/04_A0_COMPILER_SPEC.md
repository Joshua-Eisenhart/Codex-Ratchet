# A0 Compiler Specification
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-030..RQ-039`

## Role
A0 is deterministic bridge from A1 strategy to B artifacts.
A0 never declares canon truth.
A0 also:
- dispatches approved SIM work to the SIM executor boundary
- validates B full-state snapshot artifacts before state adoption

Law (explicit boundary):
- Only A0 compiler output is eligible to touch B.
- A1/A2 may be nondeterministic; A0/B/SIM must be deterministic given identical inputs.

## Inputs
- `A1_STRATEGY_v1` (YAML or JSON source)
- current B state snapshot
- run policy defaults
- optional pinned provenance values (e.g., header-gate hashes)

## Canonicalization (`RQ-030`)
Normalization pipeline:
1. parse strategy
2. drop forbidden/non-kernel fields (nominalized-reality meta rule):
   - `confidence`, `probability`, `embedding`, `hidden_prompt`, `raw_text`
3. normalize scalar types
4. sort object keys
5. normalize list ordering where order is declared non-semantic
6. serialize canonical JSON
7. hash (`strategy_hash`)

Required outputs:
- `strategy_canonical.json`
- `strategy_hash.txt`

## Compile Preflight (`RQ-038`)
A0 blocks compile on:
- schema mismatch (`A1_STRATEGY_v1` violation)
- missing required fields
- unresolved sim references (path/template missing)
- forbidden overlay token in B-scanned fields
- forbidden strategy fields present outside the above-boundary authoring layer
- unsupported item kind
- missing required pinned provenance when a header gate is known-active (if the run is configured to pin provenance)

Preflight writes deterministic result object:
- `preflight_status`
- `preflight_errors[]`
- `preflight_warnings[]`

## Compile Ordering (`RQ-031`, `RQ-032`)
Deterministic bucket order:
1. anchor prerequisites
2. primary target items
3. alternatives
4. pressure/probe support
5. sim/evidence permit items

Within-bucket order key:
`(dependency_depth, priority_rank, target_group, lexical_id)`

No randomization allowed in A0 ordering.

## EXPORT_BLOCK Compilation (Deterministic Mapping to Bootpack Grammar)
A0 emits `EXPORT_BLOCK vN` as the only kernel-facing artifact type it produces.

Container header (bootpack B authority):
- `BEGIN EXPORT_BLOCK vN`
- `EXPORT_ID: <string>`
- `TARGET: THREAD_B_ENFORCEMENT_KERNEL`
- `PROPOSAL_TYPE: <string>`
- optional header gates (if pinned/required):
  - `RULESET_SHA256: <hex64>`
  - `MEGABOOT_SHA256: <hex64>`
- `CONTENT:`
- `END EXPORT_BLOCK vN`

CONTENT lines:
- contain only item header lines and field lines (no prose, no comments).
- must use only prefixes allowed by the bootpack item grammar:
  - `AXIOM_HYP`, `PROBE_HYP`, `SPEC_HYP`
  - `AXIOM_KIND`, `PROBE_KIND`, `SPEC_KIND`
  - `REQUIRES`, `ASSERT`, `WITNESS`, `KILL_IF`, `DEF_FIELD`

Structured-item compilation mapping (from `A1_STRATEGY_v1` item objects):
- `item_class: AXIOM_HYP`:
  - header: `AXIOM_HYP <ID>`
  - field: `AXIOM_KIND <field_id> CORR <KIND>`
- `item_class: PROBE_HYP`:
  - header: `PROBE_HYP <ID>`
  - field: `PROBE_KIND <field_id> CORR <KIND>`
- `item_class: SPEC_HYP`:
  - header: `SPEC_HYP <ID>`
  - field: `SPEC_KIND <field_id> CORR <KIND>`

For each `requires[]` entry:
- emit: `REQUIRES <id> CORR <DEP_ID>` (one line per dep, in deterministic order)

For each `def_fields[]` entry:
- `value_kind: BARE`:
  - emit: `DEF_FIELD <field_id> CORR <NAME> <VALUE>`
- `value_kind: TERM_QUOTED`:
  - emit: `DEF_FIELD <field_id> CORR <NAME> "<VALUE>"`
  - required usage: `<NAME>` must be `TERM`
- `value_kind: LABEL_QUOTED`:
  - emit: `DEF_FIELD <field_id> CORR <NAME> "<VALUE>"`
  - required usage: `<NAME>` must be `LABEL`
- `value_kind: FORMULA_QUOTED`:
  - emit: `DEF_FIELD <field_id> CORR <NAME> "<VALUE>"`
  - required usage: `<NAME>` must be `FORMULA`

For each `asserts[]` entry:
- emit: `ASSERT <assert_id> CORR EXISTS <TOKEN_CLASS> <TOKEN>`

Deterministic ordering within an item:
1. kind line(s) (`AXIOM_KIND|PROBE_KIND|SPEC_KIND`)
2. `REQUIRES` lines (sorted)
3. `DEF_FIELD` lines (sorted by `(name, value_kind, value)`)
4. `ASSERT` lines (sorted)

Prohibition:
- A0 must not output any field line that introduces free English into B-scanned contexts.
## Dependency Graph Output (`RQ-033`, `RQ-037`)
A0 must emit a dependency report:
- nodes
- directed edges
- unresolved edges
- forward-reference candidates (park-intent)

Artifact:
- `dependency_report_<seq>.json`

## Budget Enforcement (`RQ-034`)
Budgets:
- `max_items`
- `max_sims`
- `max_wall_ms`

Overflow handling uses deterministic truncation.

## Deterministic Truncation (`RQ-036`)
When budget overflow occurs:
1. drop lowest-priority bucket first
2. inside bucket, drop reverse lexical order
3. if tie, drop highest dependency depth first
4. if tie, drop latest branch id

Dropped items are appended to carryover queue with reason `BUDGET_TRUNCATED`.

## Sequencing and Naming (`RQ-039`)
Within run scope:
- monotonic `batch_seq` integer
- monotonic outbox file suffix
- monotonic report file suffix

No reuse of sequence id after failure.

`RQ-039` also requires:
- deterministic SIM dispatch sequencing (batch-linked sim queue order)
- deterministic validation of `THREAD_S_SAVE_SNAPSHOT v2` container structure when loaded from B

## Header Gate Support (Bootpack-Driven)
Thread B may activate header gates (ruleset hash, megaboot hash). A0 must support injecting header lines into `EXPORT_BLOCK vN` when required.

Inputs (run-scope; deterministic):
- `pinned_ruleset_sha256` (optional)
- `pinned_megaboot_sha256` (optional)

Behavior:
- If `pinned_ruleset_sha256` is present, include:
  - `RULESET_SHA256: <hex64>`
- If `pinned_megaboot_sha256` is present, include:
  - `MEGABOOT_SHA256: <hex64>`

Prohibitions:
- A0 must not invent or guess hash values.
- A0 must not include header fields with invalid hex length.

Logging:
- compile report must record which headers were injected and from which pinned inputs.

## Persistence (`RQ-035`)
A0 writes append-only:
- `outbox/export_block_<seq>.txt`
- `reports/compile_report_<seq>.json`
- `reports/dependency_report_<seq>.json`
- `reports/preflight_report_<seq>.json`
- `logs/events.<shard>.jsonl`

Event record (JSONL; deterministic field set):
- `seq` (monotonic int within shard)
- `ts_utc` (ISO-8601 UTC)
- `stage` (`A0|B|SIM|FEEDBACK`)
- `event` (string)
- `inputs_hash` (sha256 hex, when applicable)
- `outputs_hash` (sha256 hex, when applicable)
- `state_hash_before` (optional)
- `state_hash_after` (optional)
- optional hash chaining:
  - `prev_event_hash`
  - `event_hash = SHA256(prev_event_hash || canonical_json(event_without_hashes))`

Sharding:
- fixed max bytes/file
- monotonic shard number
- no in-place rewrite of closed shard

## Failure Modes
- `HALT_SCHEMA`: invalid strategy schema
- `HALT_POLICY`: policy/gate violation
- `HALT_NONDETERMINISM`: unstable ordering/hash mismatch
- `HALT_DEPENDENCY`: unresolved mandatory prereq with no park route
- `HALT_SNAPSHOT_INVALID`: B snapshot fails structural validation
