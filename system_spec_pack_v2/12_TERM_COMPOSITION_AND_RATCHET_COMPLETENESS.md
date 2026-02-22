# Term Composition + Ratchet Completeness (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: encode the project rule that **B ratchets every term**, and larger terms are **composed of ratcheted smaller terms**. Terms must be auditable via sims + negative sims + failed alternatives (graveyard).

Authority notes:
- This is a system-level intent spec for A1/A0/B/SIM coordination.
- Thread B bootpack remains the enforcement authority for container grammar + fences.

==================================================
1) Term Literal Grammar (canon-facing)
==================================================

TERM literal (in `TERM_DEF`):
- lower-case only
- allowed chars: `[a-z0-9_]`
- `_` used only as a component separator
- forbidden:
  - leading `_` or trailing `_`
  - `__` (empty components)

Component (“atom”) = substring between underscores.

==================================================
2) Composition Rule (the core idea)
==================================================

A “complex term” is defined by composing smaller term-atoms:

- term `t = a_b_c_...` is a composition of atoms `{a,b,c,...}`
- each atom must be:
  - an L0 lexeme (from B’s lexeme set), OR
  - a previously admitted TERM literal (via `TERM_DEF`)

This makes the *name* an explicit structural definition:
- a term literal is an auditable declaration of its internal conceptual parts.

==================================================
3) Naming Conventions (audit linkage)
==================================================

To make audit and mining deterministic, A1/A0 should use stable IDs:

- TERM_DEF spec id:
  - `S_TERM_<TERM_UPPER>`
- Positive SIM_SPEC id:
  - `SIM_TERM_<TERM_UPPER>`
  - evidence token: `EV_<TERM_UPPER>`
- Negative SIM_SPEC id (at least one):
  - `SIM_NEG_<TERM_UPPER>` (or `SIM_NEG_<TERM_UPPER>__<SUFFIX>`)
  - evidence token: `NEG_EV_<TERM_UPPER>` (or `NEG_EV_<TERM_UPPER>__<SUFFIX>`)
- CANON_PERMIT id:
  - `S_PERMIT_<TERM_UPPER>`
  - requires evidence token: `EV_<TERM_UPPER>`
- Alternatives (graveyard fuel):
  - `S_ALT_<TERM_UPPER>__<SUFFIX>`

Note:
- If `<TERM_UPPER>` becomes too long for practical spec ids, A0 may use:
  - `S_TERM_H_<HASH8>` style ids
  - while keeping the TERM literal itself explicit
  - and recording a mapping in A2 rosetta (noncanon overlay)

==================================================
4) Evidence Requirements (positive + negative)
==================================================

For a term to be considered “ratcheted” (meaningful, not just admitted):

Minimum evidence bundle:
- Positive SIM evidence exists and is recorded:
  - `SIM_TERM_<TERM>` has evidence token `EV_<TERM>`
- Negative SIM evidence exists and is recorded (at least one):
  - `SIM_NEG_<TERM>` has evidence token `NEG_EV_<TERM>` (or equivalent)
  - each negative sim declares a concrete `failure_mode_id`
  - each negative sim declares expected class:
    - `NEG_EXPECT_FAIL_TARGET` or
    - `NEG_EXPECT_REJECT_ALTERNATIVE`
- At least one plausible nearby alternative failed and is in the graveyard:
  - at least one `S_ALT_<TERM>__*` exists in graveyard with a rejection reason

Operational distinction:
- “admitted term” = TERM_DEF exists in TERM_REGISTRY
- “canonically allowed” = TERM is permitted for protected operations/glyph gates (term state)
- “ratcheted (meaningful)” = admitted + positive evidence + negative evidence + graveyard alternatives

==================================================
5) Term State and Protected Gates (B/SIM contract)
==================================================

Term states (minimal):
- `TERM_PERMITTED`
- `CANONICAL_ALLOWED`

Intended mechanism:
- `CANON_PERMIT` sets TERM_REGISTRY[term].REQUIRED_EVIDENCE = `EV_<TERM>`
- SIM emits evidence token `EV_<TERM>`
- B upgrades term state to `CANONICAL_ALLOWED`

Negative sims:
- do not necessarily unlock gates directly
- but are part of the “ratcheted (meaningful)” audit bar
- must be target-coupled and failure-mode-coupled (not generic failure artifacts)

==================================================
6) Incremental Growth Rule (“every addition is ratcheted”)
==================================================

If a compound term introduces a new atom `x` not previously admitted:
- admit `x` first (TERM_DEF + evidence plan)
- only then admit compounds that include `x`

This forces growth to proceed by explicit ratcheting of the vocabulary itself.

==================================================
7) A1 Obligations (wiggle, but disciplined)
==================================================

For each TERM target, A1 should attempt to produce a complete “term bundle”:
- TERM_DEF
- positive SIM_SPEC (if sim exists or can be authored)
- negative SIM_SPEC (if negative sim exists or can be authored)
- negative sim failure mode ids + expected outcomes
- CANON_PERMIT (to unlock `CANONICAL_ALLOWED`)
- at least one plausible alternative candidate designed to fail

If the bundle cannot be completed, A1 may still propose a TERM_DEF as exploratory,
but must not mark it as “ratcheted” in any reporting layer.
