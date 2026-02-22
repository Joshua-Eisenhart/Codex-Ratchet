# ARCHIVE_AUDIT_v1

Timestamp (UTC): 2026-02-21T04:46:33Z

## What this zip is
A **larger “system_v3” bundle** containing:
- A detailed spec set for A2/A1/A0/B/SIM boundaries (`specs/`)
- A B-kernel conformance fixture set (`conformance/`)
- Tooling scripts for gates and index generation (`tools/`)
- A2 state scaffolding / derived indices (`a2_state/`, `a2_derived_indices/`)
- Some public-facing docs

## Contents (high level, non-MacOS)
Top-level folders:
- tools: 40 entries
- specs: 40 entries
- conformance: 19 entries
- a2_derived_indices_noncanonical: 8 entries
- a2_state: 8 entries
- public_facing_docs: 4 entries
- WORKSPACE_LAYOUT_v1.md: 1 entries

## What is most valuable here
- `specs/03_B_KERNEL_SPEC.md` + `specs/04_A0_COMPILER_SPEC.md` + `specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `conformance/` fixtures: this can become your **must-pass test suite** for B parsing/fences.
- `tools/run_artifact_grammar_gate.py` and related “gate” scripts: good scaffolding for the deterministic boundary.

## Red flags / cleanup needed before treating it as authoritative
- Contains **MacOS zip metadata** (`__MACOSX/`, `.DS_Store`) — should be excluded from future packs.
- Some docs contain **environment-specific absolute paths** (e.g., `/Users/...`) — should be removed/parameterized for a repo.
- Some docs contain **template placeholders** (e.g., “vN”) and large lexeme bootstrap sets; treat them as *spec language*, not literal parsing rules, unless you ratchet them into B.

## Recommendation
Treat this archive as an **A2-level implementation pack**: use it to build conformance tests + gates, but keep BOOTPACK_THREAD_B_v3.9.13 as the authoritative kernel contract unless you explicitly version-bump.
