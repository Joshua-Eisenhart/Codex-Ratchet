# A1 Design (strategy + expansion)

Status: NONCANON | Updated: 2026-02-18
Implementation: `ratchet_core/a1_protocol.py`, `ratchet_core/a1_llm.py`

## Architecture: two halves

A1 is split into a nondeterministic half (LLM) and a deterministic half (Python).

### Nondeterministic half (LLM in Cursor)

The Cursor LLM acts as the A1 strategist. It reads a briefing and produces a strategy JSON.

**Briefing** (`a1_llm.py --briefing`): presents the LLM with:
- Current lexeme set (19 words)
- Derived-only fence (84 words)
- Survivors (what passed B)
- Admitted terms (what vocabulary exists)
- Graveyard (what died and why)
- Pending evidence (what needs sims)
- Rosetta mappings (jargon ↔ B-term)
- Fuel queue preview (what A2 has extracted)

**Strategy JSON** (what the LLM outputs):
```json
{
  "terms_to_admit": ["entropy", "purity"],
  "compounds_to_try": ["density_entropy"],
  "math_defs": [{"id": "S_DM_001", "objects": "density matrix trace operator"}],
  "probes": [{"id": "S_P_001", "objects": "identity operator", "expect_fail": true}]
}
```

### Deterministic half (Python expander)

`a1_protocol.py` reads the strategy and expands each entry into B-grammar:

- `expand_strategy(strategy, state)` → list of (spec_id, lines) tuples
- `compile_batch(items, state)` → EXPORT_BLOCK string for B

The expander handles:
- Auto-seeding S_L0_MATH if missing (the foundation math_def)
- TERM_DEF generation with REQUIRES chains and paired SIM_SPECs
- Compound term validation (all parts must be admitted or lexemes)
- MATH_DEF generation from objects strings
- Probe generation for graveyard fuel
- Probe count enforcement (1 per 10 specs)

## Vocabulary admission rules

B has 19 lexemes. New vocabulary enters ONLY through TERM_DEF:

- **Single-segment** terms (no underscore) bypass the lexeme fence directly
- **Compound** terms require all parts to be lexemes or already-admitted terms
- **Derived-only** words (84 total: identity, function, equal, domain, etc.) CANNOT appear as primitives — they must enter via TERM_DEF first
- Content fields (DEF_FIELD OBJECTS, etc.) only allow lexemes or admitted terms

This means A1 must plan multi-step admission chains.

## A1 philosophy (CRITICAL — read memory.jsonl last 10 entries)

A1 is NOT conservative. Classical proof conservatism is inverted here. A1:
- Explores wildly, dumps to graveyard freely
- Creates proposed sims AND negative sims (not just references pre-made ones)
- Processes constraint ladder docs as FUEL (strips jargon, reformulates for B)
- Seeks likely things to work — the user's model gives direction, not certainty
- Builds tiered sims: small → compound → master sim (the real proof)

LLMs default to classical thinking. This system must resist that.

## Graveyard architecture

Everything starts DEAD in the pool. `state.pool` tracks each concept with status
(DEAD/ATTEMPTING/RESURRECTED), attempt history, and B rejection reasons.

Each term produces:
- **1 correct TERM_DEF** (survivor candidate)
- **1 positive SIM_SPEC** (proves the right definition works)
- **1 negative SIM_SPEC** (proves the wrong definition fails)
- **N alternatives** (graveyard relatives — similar but wrong)

Alternatives die via two mechanisms:
- **B kills**: use derived-only words, undefined terms, or bad schema
- **SIM kills**: syntactically valid but mathematically wrong (sim exits 1 → SIM_FAIL)

## Strategy rules for the LLM

- Each term must have 2-3 alternatives that die at B
- Don't re-propose items already RESURRECTED in the pool
- Prioritize terms that unblock downstream math_defs
- Check the graveyard for failure patterns before retrying similar proposals
- Compound terms are built from admitted terms — plan the admission order
- Graveyard ratio targets >= 50% naturally from alternatives, not from garbage probes
- Constraint ladder is high-quality ore (E0-E1) — process it through A1, don't dump raw
- Axes math ratchets without axis labels — labels are Rosetta overlay only

## Validation

`a1_llm.py --validate <file>` checks strategy JSON format before running.

## What A1 does NOT do

- Never sends directly to B (only through A0/runner)
- Never emits EXPORT_BLOCKs (compile_batch wraps in containers.py format)
- Never runs sims
- Never decides canon
