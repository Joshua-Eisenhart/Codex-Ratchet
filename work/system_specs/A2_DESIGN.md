# A2 Design (high-entropy processor)

Status: NONCANON | Updated: 2026-02-18
Implementation: `work/a2_state/fuel_queue.json`, `work/a2_state/memory.jsonl`

## What A2 does

A2 reads raw high-entropy documents and produces structured fuel for A1.
It quarantines hazardous content and extracts candidate math objects.

## Input documents (current fuel set)

### Constraint ladder (40 docs, structured)
- Format: `[ASSUME/DERIVE/OPEN] ID LABEL: body` or `ID:/STATEMENT:` format
- Content: admissibility constraints for composition, geometry, metric, obstruction, etc.
- Entropy level: E0-E1 (already structured, low hazard)

### Axis specifications (structured)
- `AXES_MASTER_SPEC_v0.2.md` — axis definitions as functions on M(C)
- `AXIS0_SPEC_OPTIONS_v0.1-v0.3.md` — 4 math options for computing Axis-0
- `CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.0.md` — constraint manifold definition
- Entropy level: E0-E1 (canon or near-canon)

### Rosetta/overlay docs (structured but noncanon)
- `AXIS_FOUNDATION_COMPANION_v1.4.md` — Topology4, Terrain8, channel families
- `AXIS0_PHYSICS_BRIDGE_v0.1.md` — physics narrative → QIT bridge
- Entropy level: E1-E2 (overlay, some hazard)

### Physics fuel (high entropy)
- `PHYSICS_FUEL_DIGEST_v1.0.md` — extracted candidates + quarantine list
- Grok/TOE chat transcripts — raw high entropy
- Entropy level: E2-E3 (high hazard, quarantine-first)

## Output: structured fuel entries

Each entry is a tuple:

- `ID`: unique identifier
- `TAG`: ASSUME / DERIVE / OPEN / QUARANTINE
- `LABEL`: semantic label (e.g., FINITUDE, ENTROPY_RESPONSE)
- `BODY`: one-line mathematical description
- `SOURCE`: which document, which section
- `MATH_OBJECTS`: list of QIT objects referenced (density_matrix, channel, etc.)
- `NEW_VOCABULARY`: words not in current lexeme set that would need admission
- `CONSTRAINT_REFS`: which CAS/GEA/MTA constraints this relates to
- `QUARANTINE_FLAGS`: any hazardous content detected

## Quarantine rules

A2 quarantines any entry containing:

- Teleology/deity language (god, destiny, purpose)
- Time-first narratives (future causes present, retrocausality as primitive)
- FTL signaling claims (must separate from non-signaling correlations)
- Consciousness-as-primitive claims
- Anthropic reasoning
- DMT/alien transmission content

Quarantined entries go to A2 fuel only. They can be de-quarantined later
if rewritten as pure operator statements with simulation-extractable observables.

## Processing pipeline

Current state: A2 fuel extraction has been run. `fuel_queue.json` contains 306 entries
from 18 constraint ladder docs, processed by `work/rebaseline/build_a2_fuel_extract_toe.py`.

Pipeline steps:
1. Read document, classify entropy level
2. Extract entries using format-specific parser (TAG format or ID/STATEMENT format)
3. For each entry: detect quarantine flags, extract math objects, identify new vocabulary, map to constraints
4. Output to `work/a2_state/fuel_queue.json` for A1 consumption

In practice, A2 = the user + Cursor LLM conversation. The user's intent is captured
in `memory.jsonl` (append-only) and `SESSION_STATE.md` (rewritten per session).

## What A2 does NOT do

- A2 never produces B-grammar (that's A1 → A0)
- A2 never runs sims
- A2 never decides what to propose (that's A1)
- A2 never smooths over contradictions between sources (report them, don't resolve)
- A2 never compresses working logs prematurely
