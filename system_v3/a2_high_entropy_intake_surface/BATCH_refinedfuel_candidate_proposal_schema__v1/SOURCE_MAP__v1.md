# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_refinedfuel_candidate_proposal_schema__v1`
Extraction mode: `PROPOSAL_SCHEMA_PASS`
Batch scope: next bounded non-sims `constraint ladder` doc in folder order; single-doc candidate-document schema extract for frozen proposal format and witness discipline
Date: 2026-03-09

## 1) Assigned Root Inventory
- root:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder`
- nontrivial file count:
  - `40`
- folder order around this batch:
  - `Base constraints ledger v1.md`
  - `CANDIDATE_PROPOSAL_v1.md`
  - `COMPLETENESS_ADMISSIBILITY_v1.md`
  - `COMPOSITION_CLASS_ADMISSIBILITY_v1.md`
  - `CONSTRAINT_MANIFOLD_DERIVATION_v1.md`

## 2) Batch Selection
- selected bounded batch:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder/CANDIDATE_PROPOSAL_v1.md`
- reason for selection:
  - this is the next unprocessed non-sims `constraint ladder` file in folder order after `Base constraints ledger v1.md`
  - the file is a compact frozen schema for what a candidate proposal document is allowed to contain:
    - fixed header-token identity
    - explicit declaration and frozen-symbol usage lists
    - witness block requirements
    - compatibility-claim form
    - explicit failure conditions
    - no patching and no backflow into the frozen stack
  - the main intake value is the proposal-document format itself rather than object-level math
  - this makes `PROPOSAL_SCHEMA_PASS` the best fit
- deferred next doc in folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder/COMPLETENESS_ADMISSIBILITY_v1.md`

## 3) Source Membership
- source 1:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder/CANDIDATE_PROPOSAL_v1.md`
  - role in batch: frozen schema for finite candidate proposal documents over the admitted stack
  - sha256: `bb894886798837768afc579fa009a56dbcb8b9f431e2bed6e952180473ff98d2`
  - size bytes: `5161`
  - line count: `41`
  - source class:
    - canonical constraint-ladder proposal-format spec

## 4) Structural Map Of The Source
Source numbering below follows manifest order.

### Segment A: frozen-stack authority and candidate identity discipline
- source anchors:
  - source 1: `3-11`
- source role:
  - declares that frozen admissibility layers outrank candidate docs and fixes candidate identity as an uninterpreted header token with token-only versioning
- strong markers:
  - frozen stack authority
  - finite plain-text document
  - header token
  - no renaming
  - versioning as token only

### Segment B: declaration discipline for new and frozen symbols
- source anchors:
  - source 1: `13-18`
- source role:
  - forces candidate docs to enumerate exactly which new symbols they propose and which frozen symbols they use
- strong markers:
  - declaration block required
  - exact set of new symbols
  - exact set of frozen symbols used
  - finite token registries
  - relation or classifier symbols only

### Segment C: witness discipline
- source anchors:
  - source 1: `19-24`
- source role:
  - requires witness blocks for otherwise ungrounded claims and restricts witnesses to finite syntactic bindings rather than semantic or evidentiary objects
- strong markers:
  - witness block required
  - non-commutation
  - obstruction
  - order-sensitivity
  - witness syntax only
  - explicit witness typing

### Segment D: compatibility-claim form and no implied admissibility
- source anchors:
  - source 1: `25-30`
- source role:
  - constrains candidate claims to finitely checkable compatibility statements against the frozen stack and forbids any appeal to implicit or standard admissibility
- strong markers:
  - compatibility claim block required
  - finite declarative statement
  - finite inspection
  - no implied admissibility

### Segment E: failure, elimination, non-backflow, and forbidden primitive imports
- source anchors:
  - source 1: `31-37`
- source role:
  - defines explicit failure conditions, forbids patching within the candidate format, protects the frozen stack from candidate failure, and blocks primitive imports
- strong markers:
  - failure condition block
  - no patching
  - candidate eliminated
  - non-backflow guarantee
  - no time-like / probability-like / causality-like / optimization-like / ontological / teleological primitives

### Segment F: bounded open extensions
- source anchors:
  - source 1: `39-41`
- source role:
  - leaves only two controlled openings:
    - non-binding candidate-family header-token listings
    - future format refinements that do not alter frozen layers
- strong markers:
  - OPEN-only candidate-family listing
  - non-binding placeholders
  - future format refinements
  - no alteration of frozen layers

## 5) Source-Class Read
- best classification:
  - compact high-value frozen proposal-format fence for candidate docs over the constraint-ladder stack
- useful as:
  - the clearest repo-local schema for what a candidate document is allowed to be
  - a strong boundary against:
    - renaming
    - implicit admissibility
    - witnessless nontriviality claims
    - patching or partial salvage inside the candidate format
    - backflow into frozen layers
  - a concise bridge between frozen admissibility surfaces and later proposal packaging
- not best classified as:
  - an object-level math-class spec
  - permission to alter frozen specs from inside a candidate doc
  - a semantic theory of versioning or candidate preference
- possible downstream consequence:
  - later A2-mid reduction can reuse this as the cleanest candidate-doc format fence in the constraint-ladder family, especially when distinguishing proposal packaging from frozen stack authority
