# Governance (specs maintenance + space budget)

Status: NONCANON | Updated: 2026-02-18

## Folder budget

- `work/system_specs/`: max 15 files, max 250 KB total, max 40 KB per file
- `work/ratchet_core/`: no file exceeds 500 lines
- `work/a2_state/`: exactly 3 operational files (doc_index, fuel_queue, rosetta)
- `work/ratchet_core/sims/`: one file per validated math property

## Growth rules

- No new spec file unless it replaces or merges existing files
- Prefer updating DOC_ENTROPY_REGISTRY.md over adding one-off docs
- If folder exceeds budget: keep E0/E1, collapse E2, move bulk to rebaseline/

## Entropy tiers

| Tier | Description | Example |
|------|-------------|---------|
| E0 | Verbatim contracts, quotes, invariants | Bootpack extractions |
| E1 | Mechanically-derived tables citing E0 | Allowed/forbidden matrices |
| E2 | A2 fuel extracts (snippets + quarantine) | Candidate rewrites |
| E3 | Raw source pointers (stored elsewhere) | Chat transcripts, docx dumps |

Rule: Any upward move (E3→E0) must reduce ambiguity and reduce size.

## Refinement loop

1. Register new input in DOC_ENTROPY_REGISTRY.md (one line; tier; hazards; pointers)
2. If high entropy: produce at most one E2 fuel extract
3. If it defines a contract: extract verbatim to E0, derive E1 tables
4. Periodic compaction: collapse multiple notes into one pointer + one invariant list

## Update discipline

- Prefer appending `DELTA:` sections over rewriting history
- If rewrite necessary: create `*_v2.md`, keep `*_v1.md`
- Every E1/E2 doc must contain pointers back to source
- No "because I remember" claims: if not in pointers, mark UNKNOWN

## Auditability

- Every spec must state: Status (NONCANON/CANON), Last updated date
- Every spec must point to its authority source (bootpack, code file, or design decision)
- Specs are updated at end of session when the underlying code changes
