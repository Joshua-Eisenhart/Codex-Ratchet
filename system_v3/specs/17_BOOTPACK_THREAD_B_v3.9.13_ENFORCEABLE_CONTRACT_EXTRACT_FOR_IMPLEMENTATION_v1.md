# BOOTPACK_THREAD_B v3.9.13 — Enforceable Contract Extract for Implementation (v1)
Status: DRAFT / NONCANON (extract only; authority remains `core_docs/BOOTPACK_THREAD_B_v3.9.13.md`)
Date: 2026-02-20

Purpose: provide a single compact implementation reference for:
- message/container discipline
- accepted artifact grammars
- enforceable fences
- state object shapes
- deterministic stage order

Authority source (sole): `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/BOOTPACK_THREAD_B_v3.9.13.md`

Note: the bootpack contains duplicated blocks; this extract targets the earliest occurrence of each rule family.

## 0) Report Metadata (All Kernel REPORT Outputs)
```text
RULE RPT-001 REPORT_METADATA (HARD)
All REPORT outputs emitted by the kernel must include:
- BOOT_ID line
- TIMESTAMP_UTC line (ISO 8601 UTC)
This applies to all outcomes: PASS/FAIL/REJECT and introspection dumps.
No state changes.
```

## 1) Message Discipline (Enforceable)
```text
RULE MSG-001 MESSAGE_TYPE
Each user message must be exactly one of:

(A) COMMAND_MESSAGE:
- one or more lines beginning with "REQUEST "
- no other text

(B) ARTIFACT_MESSAGE:
- exactly one EXPORT_BLOCK vN container, and nothing else
  OR
- exactly one THREAD_S_SAVE_SNAPSHOT v2 container, and nothing else
  OR
- a SIM_EVIDENCE_PACK:
  - one or more complete SIM_EVIDENCE v1 blocks back-to-back
  - no other text before/between/after blocks

Else: REJECT_MESSAGE TAG MULTI_ARTIFACT_OR_PROSE.

RULE MSG-002 NO_COMMENTS_IN_ARTIFACTS
Inside accepted containers, no lines starting with "#" or "//".
Violation: REJECT_BLOCK TAG COMMENT_BAN.

RULE MSG-003 SNAPSHOT_VERBATIM_REQUIRED
THREAD_S_SAVE_SNAPSHOT v2 is admissible only if SURVIVOR_LEDGER contains at least one item header line beginning with:
  "AXIOM_HYP " OR "PROBE_HYP " OR "SPEC_HYP "
Else: REJECT_BLOCK TAG SNAPSHOT_NONVERBATIM.
```

## 2) Canon State Objects (Replayable)
```text
STATE SURVIVOR_LEDGER
- Map ID -> {CLASS, STATUS, ITEM_TEXT, PROVENANCE}
- CLASS ∈ {AXIOM_HYP, PROBE_HYP, SPEC_HYP}
- STATUS ∈ {ACTIVE, PENDING_EVIDENCE}

STATE PARK_SET
- Map ID -> {CLASS, ITEM_TEXT, TAGS, PROVENANCE}

STATE REJECT_LOG
- List {BATCH_ID, TAG, DETAIL}

STATE KILL_LOG
- List {BATCH_ID, ID, TAG}

STATE TERM_REGISTRY
- Map TERM_LITERAL -> {STATE, BOUND_MATH_DEF, REQUIRED_EVIDENCE, PROVENANCE}
- STATE ∈ {QUARANTINED, MATH_DEFINED, TERM_PERMITTED, LABEL_PERMITTED, CANONICAL_ALLOWED}

STATE EVIDENCE_PENDING
- Map SPEC_ID -> set(EVIDENCE_TOKEN)

STATE ACTIVE_MEGABOOT_ID string (optional)
STATE ACTIVE_MEGABOOT_SHA256 string (optional)
STATE ACCEPTED_BATCH_COUNT integer
STATE UNCHANGED_LEDGER_STREAK integer
```

## 3) Rejection Tag Fence (REJECT_* tags only)
```text
RULE BR-000A TAG_FENCE (HARD)
Only the following rejection tags are permitted:
  MULTI_ARTIFACT_OR_PROSE
  COMMENT_BAN
  SNAPSHOT_NONVERBATIM
  UNDEFINED_TERM_USE
  DERIVED_ONLY_PRIMITIVE_USE
  DERIVED_ONLY_NOT_PERMITTED
  UNQUOTED_EQUAL
  SCHEMA_FAIL
  FORWARD_DEPEND
  NEAR_REDUNDANT
  PROBE_PRESSURE
  UNUSED_PROBE
  SHADOW_ATTEMPT
  KERNEL_ERROR
  GLYPH_NOT_PERMITTED
Any other tag is forbidden and triggers REJECT_BLOCK TAG SCHEMA_FAIL.
```

## 4) Global Kernel Rules (Selected; Enforceable)
```text
RULE BR-003 NAME_HYGIENE
- AXIOM_HYP IDs must be structural-neutral.
- Count or construction words are forbidden in AXIOM_HYP IDs.
- Domain/metaphor words are allowed only through TERM_DEF / LABEL_DEF.

RULE BR-004 IMMUTABILITY
Any accepted F* AXIOM_HYP is immutable.
Duplicate ID with different content => KILL TAG SHADOW_ATTEMPT.

RULE BR-005 DEFINITION_OF_DEFINED_ID (DETERMINISTIC)
Within an EXPORT_BLOCK, a dependency ID is DEFINED iff:
- it exists in SURVIVOR_LEDGER (any STATUS), OR
- it appears earlier in the same EXPORT_BLOCK as an item header.
Anything else is UNDEFINED for this batch.

RULE BR-006 FORWARD_REFERENCE
REQUIRES referencing an UNDEFINED ID => PARK TAG FORWARD_DEPEND.

RULE BR-007 NEAR_DUPLICATE
If Jaccard(token_set) > 0.80 with existing item of same CLASS and different ID => PARK TAG NEAR_REDUNDANT.

RULE BR-013 SIMULATION_POLICY
Thread B never runs simulations.
Thread B consumes SIM_EVIDENCE v1 only.
```

## 5) Accepted Containers (Grammar)
```text
CONTAINER EXPORT_BLOCK vN
BEGIN EXPORT_BLOCK vN
EXPORT_ID: <string>
TARGET: THREAD_B_ENFORCEMENT_KERNEL
PROPOSAL_TYPE: <string>
(Optional) RULESET_SHA256: <64hex>
CONTENT:
  (grammar lines only)
END EXPORT_BLOCK vN

CONTAINER SIM_EVIDENCE v1
BEGIN SIM_EVIDENCE v1
SIM_ID: <ID>
CODE_HASH_SHA256: <hex>
OUTPUT_HASH_SHA256: <hex>
METRIC: <k>=<v>
EVIDENCE_SIGNAL <SIM_ID> CORR <TOKEN> (repeatable)
KILL_SIGNAL <TARGET_ID> CORR <TOKEN>  (optional, repeatable)
END SIM_EVIDENCE v1

CONTAINER THREAD_S_SAVE_SNAPSHOT v2
BEGIN THREAD_S_SAVE_SNAPSHOT v2
BOOT_ID: <string>
SURVIVOR_LEDGER:
  <verbatim accepted items>
PARK_SET:
  <verbatim parked items>
TERM_REGISTRY:
  <dump>
EVIDENCE_PENDING:
  <dump>
PROVENANCE:
  <metadata>
END THREAD_S_SAVE_SNAPSHOT v2
```

## 6) Optional Header Gates (Ruleset Hash / Megaboot Hash)
```text
STATE ACTIVE_RULESET_SHA256
- String hex64 or EMPTY
INIT: EMPTY

RULE MBH-010 RULESET_HASH_ACTIVATION (HARD)
If a SIM_EVIDENCE v1 includes:
SIM_ID: S_RULESET_HASH
and METRIC: ruleset_sha256=<hex64>
then set ACTIVE_RULESET_SHA256 to that <hex64>.

RULE MBH-011 RULESET_HASH_GATE (HARD)
If ACTIVE_RULESET_SHA256 is non-empty, then any EXPORT_BLOCK must include header line:
RULESET_SHA256: <hex64>
and it must exactly equal ACTIVE_RULESET_SHA256.
If missing or different => REJECT_BLOCK TAG SCHEMA_FAIL.

RULE MBH-001 SET_ACTIVE_MEGABOOT_HASH (HARD)
When consuming SIM_EVIDENCE v1:
- If SIM_ID == S_MEGA_BOOT_HASH
- And SIM_EVIDENCE contains EVIDENCE_SIGNAL S_MEGA_BOOT_HASH CORR E_MEGA_BOOT_HASH
Then set:
- ACTIVE_MEGABOOT_SHA256 = CODE_HASH_SHA256
- ACTIVE_MEGABOOT_ID = (value from METRIC megaboot_id if present; else EMPTY)

RULE MBH-002 REQUIRE_EXPORT_MEGABOOT_SHA256 (HARD)
Apply ONLY to EXPORT_BLOCK vN containers.
If ACTIVE_MEGABOOT_SHA256 is non-empty:
- require EXPORT_BLOCK header includes line:
  MEGABOOT_SHA256: <64hex>
- require that value equals ACTIVE_MEGABOOT_SHA256
If missing or different => REJECT_BLOCK TAG KERNEL_ERROR.
```

## 7) Item Grammar (Strict)
```text
Allowed headers:
AXIOM_HYP <ID>
PROBE_HYP <ID>
SPEC_HYP  <ID>

Allowed fields:
AXIOM_KIND <ID> CORR <KIND>
PROBE_KIND <ID> CORR <KIND>
SPEC_KIND  <ID> CORR <KIND>
REQUIRES   <ID> CORR <DEP_ID>
ASSERT     <ID> CORR EXISTS <TOKEN_CLASS> <TOKEN>
WITNESS    <ID> CORR <TOKEN>
KILL_IF    <ID> CORR <COND_TOKEN>
DEF_FIELD  <ID> CORR <FIELD_NAME> <VALUE...>

Allowed TOKEN_CLASS:
STATE_TOKEN | PROBE_TOKEN | REGISTRY_TOKEN | MATH_TOKEN | TERM_TOKEN | LABEL_TOKEN | PERMIT_TOKEN | EVIDENCE_TOKEN
```

## 8) Allowed COMMAND_MESSAGE Lines (Exact Prefix Set)
```text
Allowed command lines (COMMAND_MESSAGE only):
REQUEST REPORT_STATE
REQUEST CHECK_CLOSURE
REQUEST SAVE_SNAPSHOT
REQUEST SAVE_NOW
REQUEST MANUAL_UNPARK <ID>
REQUEST DUMP_LEDGER
REQUEST DUMP_LEDGER_BODIES
REQUEST DUMP_TERMS
REQUEST DUMP_INDEX
REQUEST DUMP_EVIDENCE_PENDING
REQUEST HELP
REQUEST REPORT_POLICY_STATE

Any other prefix => REJECT_LINE.
```

## 9) TERM Admission Pipeline (Grammar Shapes)
```text
4.1 MATH_DEF
SPEC_HYP <ID>
SPEC_KIND <ID> CORR MATH_DEF
DEF_FIELD <ID> CORR OBJECTS <...>
DEF_FIELD <ID> CORR OPERATIONS <...>
DEF_FIELD <ID> CORR INVARIANTS <...>
DEF_FIELD <ID> CORR DOMAIN <...>
DEF_FIELD <ID> CORR CODOMAIN <...>
DEF_FIELD <ID> CORR SIM_CODE_HASH_SHA256 <hex>
ASSERT <ID> CORR EXISTS MATH_TOKEN <token>
(Optional) DEF_FIELD <ID> CORR FORMULA "<string>"

4.2 TERM_DEF
SPEC_HYP <ID>
SPEC_KIND <ID> CORR TERM_DEF
REQUIRES <ID> CORR <MATH_DEF_ID>
DEF_FIELD <ID> CORR TERM "<literal>"
DEF_FIELD <ID> CORR BINDS <MATH_DEF_ID>
ASSERT <ID> CORR EXISTS TERM_TOKEN <token>
TERM_DRIFT_BAN: rebinding a term to a different math def => REJECT_BLOCK TAG TERM_DRIFT.

4.3 LABEL_DEF
SPEC_HYP <ID>
SPEC_KIND <ID> CORR LABEL_DEF
REQUIRES <ID> CORR <TERM_DEF_ID>
DEF_FIELD <ID> CORR TERM "<literal>"
DEF_FIELD <ID> CORR LABEL "<label>"
ASSERT <ID> CORR EXISTS LABEL_TOKEN <token>

4.4 CANON_PERMIT
SPEC_HYP <ID>
SPEC_KIND <ID> CORR CANON_PERMIT
REQUIRES <ID> CORR <TERM_DEF_ID>
DEF_FIELD <ID> CORR TERM "<literal>"
DEF_FIELD <ID> CORR REQUIRES_EVIDENCE <EVIDENCE_TOKEN>
ASSERT <ID> CORR EXISTS PERMIT_TOKEN <token>
```

## 10) Lexeme Fence (Underscore Compounds)
```text
STATE L0_LEXEME_SET
- Set of lowercase lexemes permitted to appear as TERM components without prior admission.
- This is a tiny bootstrap set; everything else must be ratcheted.

INIT L0_LEXEME_SET (lowercase):
  "finite" "dimensional" "hilbert" "space" "density" "matrix" "operator"
  "channel" "cptp" "unitary" "lindblad" "hamiltonian" "commutator"
  "anticommutator" "trace" "partial" "tensor" "superoperator" "generator"

RULE LEX-001 COMPOUND_TERM_COMPONENTS_DEFINED (HARD)
Apply ONLY to SPEC_KIND TERM_DEF lines.

If DEF_FIELD <ID> CORR TERM "<literal>" contains "_" then:
- Split <literal> by "_" into components c_i
- For each c_i:
  - if c_i in L0_LEXEME_SET: OK
  - else require TERM_REGISTRY has key c_i with STATE in {TERM_PERMITTED, LABEL_PERMITTED, CANONICAL_ALLOWED}
  - else => PARK TAG UNDEFINED_LEXEME
```

## 11) Undefined-Term Fence (EXPORT_BLOCK CONTENT)
```text
RULE BR-0U3 MIXEDCASE_TOKEN_BAN (HARD)
Apply ONLY to lines inside EXPORT_BLOCK CONTENT outside allowed string contexts (TERM/LABEL/FORMULA).
If any token contains both lowercase and uppercase letters => REJECT_LINE TAG SCHEMA_FAIL.

RULE BR-0U2 ASCII_ONLY_CONTENT (HARD)
Apply ONLY to lines inside EXPORT_BLOCK CONTENT outside allowed string contexts (TERM/LABEL/FORMULA).
If any non-ASCII character is present => REJECT_LINE TAG SCHEMA_FAIL.

RULE BR-0U1 UNDEFINED_TERM_FENCE (HARD)
Apply ONLY to lines inside EXPORT_BLOCK CONTENT outside allowed string contexts (TERM/LABEL/FORMULA).
RULE BR-0U5 CONTENT_DIGIT_GUARD (HARD)
Apply ONLY to lines inside EXPORT_BLOCK CONTENT outside allowed string contexts (TERM/LABEL/FORMULA).

Ignore entire lines that contain:
  DEF_FIELD <ID> CORR SIM_CODE_HASH_SHA256

Scan the original line for lowercase tokens matching:
  [a-z][a-z0-9_]*

For each token T:
- split T by "_" into segments s_i
- for each segment s_i:
  - if s_i matches [0-9]+ : OK (numeric suffix treated as label fragment)
  - else require at least one:
    (1) s_i in L0_LEXEME_SET
    (2) TERM_REGISTRY has key s_i with STATE in {TERM_PERMITTED, LABEL_PERMITTED, CANONICAL_ALLOWED}

If any non-numeric segment fails => REJECT_LINE TAG UNDEFINED_TERM_USE.
```

## 12) Derived-Only Guard (EXPORT_BLOCK CONTENT)
```text
STATE DERIVED_ONLY_TERMS
- Set of TERM_LITERAL strings treated as “derived-only primitives”.
- Not forbidden; forbidden as primitive use until CANONICAL_ALLOWED via term pipeline.

INIT DERIVED_ONLY_TERMS (lowercase literals):
  "equal" "equality" "same" "identity"
  "coordinate" "cartesian" "origin" "center" "frame"
  "metric" "distance" "norm" "angle" "radius"
  "time" "before" "after" "past" "future"
  "cause" "because" "therefore" "implies" "results" "leads"
  "optimize" "maximize" "minimize" "utility"

  "map" "maps" "mapping" "mapped" "apply" "applies" "applied" "application" "uniform" "uniformly" "unique" "uniquely" "real" "integer" "integers" "natural" "naturals" "number" "numbers" "count" "counting" "probability" "random" "ratio" "proportion" "statistics" "statistical" "platonic" "platon" "platonism" "one" "two" "three" "four" "five" "six" "seven" "eight" "nine" "ten" "function" "functions" "mapping_of" "implies_that"
  "complex" "quaternion" "quaternions" "imaginary" "i_unit" "j_unit" "k_unit"
  "set" "relation" "domain" "codomain"

RULE BR-0D1 DERIVED_ONLY_SCAN (HARD, DETERMINISTIC)
Apply ONLY to lines inside EXPORT_BLOCK CONTENT.
For each line L inside EXPORT_BLOCK CONTENT:
- Define L_norm = lowercase(L)
- For each term t in DERIVED_ONLY_TERMS:
  - detect whole-segment occurrences where segments are split on:
    (i) "_" and
    (ii) non-alphanumeric characters
  - ignore occurrences inside:
    (A) DEF_FIELD <ID> CORR TERM "<...>"
    (B) DEF_FIELD <ID> CORR LABEL "<...>"
    (C) DEF_FIELD <ID> CORR FORMULA "<...>"
If a match remains => REJECT_LINE TAG DERIVED_ONLY_PRIMITIVE_USE.

RULE BR-0D2 DERIVED_ONLY_PERMISSION (HARD)
Apply ONLY to lines inside EXPORT_BLOCK CONTENT.
If a derived-only literal t appears in any line outside the allowed contexts above:
- require TERM_REGISTRY[t].STATE == CANONICAL_ALLOWED
Else => REJECT_LINE TAG DERIVED_ONLY_NOT_PERMITTED.
```

## 13) Formula Fences (DEF_FIELD ... FORMULA "<string>")
```text
RULE BR-008 FORMULA_CONTAINMENT
Any "=" character must appear only inside:
  DEF_FIELD <ID> CORR FORMULA "<string>"
Unquoted "=" anywhere => REJECT_LINE TAG UNQUOTED_EQUAL.

RULE BR-0F1 FORMULA_TOKEN_FENCE (HARD)
Apply ONLY to DEF_FIELD <ID> CORR FORMULA "<string>" values.
Let F_norm = lowercase(<string>).
Scan F_norm for tokens matching:
  [a-z][a-z0-9_]*

For each token T:
- split T by "_" into segments s_i
- for each segment s_i:
  - if s_i matches [0-9]+ : OK (numeric suffix treated as label fragment)
  - else require at least one:
    (1) s_i in L0_LEXEME_SET
    (2) TERM_REGISTRY has key s_i with STATE in {TERM_PERMITTED, LABEL_PERMITTED, CANONICAL_ALLOWED}
If any non-numeric segment fails => REJECT_LINE TAG UNDEFINED_TERM_USE.

RULE BR-0F2 FORMULA_DERIVED_ONLY_SCAN (HARD)
Apply ONLY to DEF_FIELD <ID> CORR FORMULA "<string>" values.
If any derived-only literal in DERIVED_ONLY_TERMS appears in the formula string (whole-segment match),
require TERM_REGISTRY for that literal has STATE CANONICAL_ALLOWED.
Else => REJECT_LINE TAG DERIVED_ONLY_NOT_PERMITTED.

RULE BR-0F3 EQUALS_SIGN_GUARD (HARD)
Apply ONLY to DEF_FIELD <ID> CORR FORMULA "<string>" values.
If the formula contains the character "=" then require:
TERM_REGISTRY contains key "equals_sign" with STATE CANONICAL_ALLOWED.
Else => REJECT_LINE TAG DERIVED_ONLY_NOT_PERMITTED.

RULE BR-0F4 FORMULA_ASCII_ONLY (HARD)
Apply ONLY to DEF_FIELD <ID> CORR FORMULA "<string>" values.
If any non-ASCII character is present inside the formula string => REJECT_LINE TAG SCHEMA_FAIL.

RULE BR-0F7 FORMULA_DIGIT_GUARD (HARD)
Apply ONLY to DEF_FIELD <ID> CORR FORMULA "<string>" values.
If any digit character [0-9] appears in the formula string then require:
TERM_REGISTRY contains key "digit_sign" with STATE CANONICAL_ALLOWED.
Else => REJECT_LINE TAG DERIVED_ONLY_NOT_PERMITTED.

STATE FORMULA_GLYPH_REQUIREMENTS
- Map glyph -> required TERM_LITERAL
INIT:
  "+" -> "plus_sign"
  "-" -> "minus_sign"
  "*" -> "asterisk_sign"
  "/" -> "slash_sign"
  "^" -> "caret_sign"
  "~" -> "tilde_sign"
  "!" -> "exclamation_sign"
  "[" -> "left_square_bracket_sign"
  "]" -> "right_square_bracket_sign"
  "{" -> "left_curly_brace_sign"
  "}" -> "right_curly_brace_sign"
  "(" -> "left_parenthesis_sign"
  ")" -> "right_parenthesis_sign"
  "<" -> "less_than_sign"
  ">" -> "greater_than_sign"
  "|" -> "pipe_sign"
  "&" -> "ampersand_sign"
  "," -> "comma_sign"
  ":" -> "colon_sign"
  "." -> "dot_sign"

RULE BR-0F5 FORMULA_GLYPH_FENCE (HARD)
Apply ONLY to DEF_FIELD <ID> CORR FORMULA "<string>" values.
For each glyph g in FORMULA_GLYPH_REQUIREMENTS that appears in the formula string:
- let term = FORMULA_GLYPH_REQUIREMENTS[g]
- require TERM_REGISTRY has key term with STATE CANONICAL_ALLOWED
If any required term is missing or not CANONICAL_ALLOWED => REJECT_LINE TAG GLYPH_NOT_PERMITTED.

RULE BR-0F6 FORMULA_UNKNOWN_GLYPH_REJECT (HARD)
Apply ONLY to DEF_FIELD <ID> CORR FORMULA "<string>" values.
Let F = <string>.
For each character ch in F:
- ignore if ch is alphanumeric or whitespace or '_'
- else require ch is a key in FORMULA_GLYPH_REQUIREMENTS
If any unknown glyph appears => REJECT_LINE TAG GLYPH_NOT_PERMITTED.
```

## 14) Probe Pressure + Utilization
```text
RULE BR-009 PROBE_PRESSURE
Per batch: for every 10 newly ACCEPTED SPEC_HYP, require at least 1 newly ACCEPTED PROBE_HYP.
If violated: PARK new SPEC_HYP items using BR-014 until satisfied. TAG PROBE_PRESSURE.

RULE BR-010 PROBE_UTILIZATION
A newly ACCEPTED PROBE_HYP must be referenced by at least one ACCEPTED SPEC_HYP
within the next 3 ACCEPTED batches.
If not: move PROBE_HYP to PARK_SET TAG UNUSED_PROBE.
```

## 15) KILL_IF Semantics
```text
RULE BR-011 KILL_IF SEMANTICS (CLOSED, IDEMPOTENT)
KILL_IF is declarative only.
An item is KILLED iff:
- item declares KILL_IF <ID> CORR <COND_TOKEN>
AND
- a SIM_EVIDENCE v1 contains KILL_SIGNAL <TARGET_ID> CORR <COND_TOKEN>
AND
- kill binding passes (BR-012)
KILL is idempotent.

RULE BR-012 KILL_BIND (DEFAULT LOCAL)
Default: SIM_EVIDENCE SIM_ID must equal the target ID to kill.
Remote kill is permitted only if target includes:
  DEF_FIELD <ID> CORR KILL_BIND <SIM_ID>
and SIM_EVIDENCE uses that SIM_ID.
```

## 16) Evidence Rules (State Transitions)
```text
RULE EV-000 SIM_SPEC_SINGLE_EVIDENCE (HARD)
A SPEC_HYP whose SPEC_KIND is SIM_SPEC must include exactly one:
  DEF_FIELD <ID> CORR REQUIRES_EVIDENCE <EVIDENCE_TOKEN>
If missing => PARK TAG SCHEMA_FAIL.
If more than one => REJECT_BLOCK TAG SCHEMA_FAIL.

RULE EV-002 EVIDENCE_SATISFACTION
When SIM_EVIDENCE includes EVIDENCE_SIGNAL <SIM_ID> CORR <TOKEN>,
and SPEC_HYP SIM_ID requires that token, clear it from EVIDENCE_PENDING[SIM_ID].
If empty: STATUS ACTIVE.

RULE EV-003 TERM_CANONICAL_ALLOWED
If TERM_REGISTRY[TERM].REQUIRED_EVIDENCE is <TOKEN> and evidence arrives, STATE becomes CANONICAL_ALLOWED.

RULE EV-004 MATH_DEF_HASH_MATCH
If MATH_DEF requires SIM_CODE_HASH_SHA256 H, only SIM_EVIDENCE with matching CODE_HASH_SHA256 counts for term admission tied to that MATH_DEF.
```

## 17) Deterministic Stage Order
```text
STAGE 1 AUDIT_PROVENANCE
STAGE 1.5 DERIVED_ONLY_GUARD (EXPORT_BLOCK CONTENT ONLY)
STAGE 1.55 CONTENT_DIGIT_GUARD (EXPORT_BLOCK CONTENT ONLY)
STAGE 1.6 UNDEFINED_TERM_FENCE (EXPORT_BLOCK CONTENT ONLY)
STAGE 2 SCHEMA_CHECK
STAGE 3 DEPENDENCY_GRAPH
STAGE 4 NEAR_DUPLICATE
STAGE 5 PRESSURE
STAGE 6 EVIDENCE_UPDATE
STAGE 7 COMMIT
```

## 18) Introspection Outputs (Selected; Read-Only)
```text
RULE INT-002 DUMP_TERMS
On COMMAND_MESSAGE line:
REQUEST DUMP_TERMS
Emit exactly one container:

BEGIN DUMP_TERMS v1
BOOT_ID: BOOTPACK_THREAD_B_v3.9.13
TIMESTAMP_UTC: <ISO8601 UTC>

TERM_REGISTRY:
- Output must be a full enumeration (no placeholders).
- Ordering: lexicographic by TERM_LITERAL.
- One line per term:

TERM <TERM_LITERAL> STATE <STATE> BINDS <BOUND_MATH_DEF|NONE> REQUIRED_EVIDENCE <TOKEN|EMPTY>

Allowed STATE values:
QUARANTINED | MATH_DEFINED | TERM_PERMITTED | LABEL_PERMITTED | CANONICAL_ALLOWED

END DUMP_TERMS v1

No state changes.

RULE INT-005 SAVE_SNAPSHOT (HARD, FULLY ENUMERATED)
On COMMAND_MESSAGE line:
REQUEST SAVE_SNAPSHOT
Emit exactly one container:

BEGIN THREAD_S_SAVE_SNAPSHOT v2
BOOT_ID: BOOTPACK_THREAD_B_v3.9.13
TIMESTAMP_UTC: <ISO8601 UTC>

SURVIVOR_LEDGER:
- FULL ITEM BODIES (no headers-only snapshots).
- For each item in SURVIVOR_LEDGER, in lexicographic ID order:
  - Emit ITEM_TEXT verbatim exactly as stored (header line + all field lines).

PARK_SET:
- For each item in PARK_SET, in lexicographic ID order:
  - Emit ITEM_TEXT verbatim exactly as stored.
- If empty, emit:
  EMPTY

TERM_REGISTRY:
- FULL ENUMERATION (no placeholders).
- Ordering: lexicographic by TERM_LITERAL.
- One line per term:
  TERM <TERM_LITERAL> STATE <STATE> BINDS <BOUND_MATH_DEF|NONE> REQUIRED_EVIDENCE <TOKEN|EMPTY>

EVIDENCE_PENDING:
- FULL ENUMERATION (no placeholders).
- One line per pending requirement:
  PENDING <SPEC_ID> REQUIRES_EVIDENCE <EVIDENCE_TOKEN>

PROVENANCE:
ACCEPTED_BATCH_COUNT=<integer>
UNCHANGED_LEDGER_STREAK=<integer>

END THREAD_S_SAVE_SNAPSHOT v2
No state changes.
```

## 19) Initial State (Kernel Seed)
```text
INIT SURVIVOR_LEDGER:
  F01_FINITUDE
  N01_NONCOMMUTATION
INIT PARK_SET: EMPTY
INIT TERM_REGISTRY: EMPTY
```

## 20) Known Internal Inconsistencies (Record Only; Do Not Smooth)
- `TERM_DRIFT` appears as a `REJECT_BLOCK TAG` in the term pipeline shapes, but is not listed in `RULE BR-000A TAG_FENCE`.
- `MEGABOOT_SHA256:` header line is required by `RULE MBH-002 REQUIRE_EXPORT_MEGABOOT_SHA256` when active, but is not listed in the `CONTAINER EXPORT_BLOCK vN` header grammar.

