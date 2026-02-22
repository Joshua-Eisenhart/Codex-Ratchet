# Professional Glossary Overlay (rosetta; canon-gated)

Status: NONCANON | Updated: 2026-02-18  
Intent: Keep Thread B canon readable to professionals without smuggling derived-only primitives or metaphoric jargon into canon.

## Scope

This is an overlay protocol (A1/A0 workspace), not a Thread B artifact.

## Gate (hard, project policy)

An overlay entry may only reference:

- A Thread B item ID present in `SURVIVOR_LEDGER`, and
- A term literal whose `TERM_REGISTRY[term].STATE == CANONICAL_ALLOWED`.

If not, keep the entry in A2 fuel only (quarantine) or mark it `UNKNOWN`.

## Minimal record shape

Each mapping is a tuple:

- `TERM_LITERAL` (snake_case)
- `PRO_SYNONYM` (mainstream math/physics wording)
- `SCOPE_NOTE` (one short disambiguation line)
- `CANON_POINTERS` (IDs / tokens in B that justify the mapping)

## Non-goals

- No attempts to “define” math here.
- No metaphors (“axes”, “consciousness”, “oracle”, etc.) unless explicitly admitted as canon terms.
- No policy changes to B fences.

## Pointer

Megaboot readability guidance lives in:

- `core_docs/a2 hand assembled docs/uploads/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md` (Section 0.2)
