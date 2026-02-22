# Translator Boundary + Policy (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: adopt the *useful* parts of “translator boundary / nominalized reality / locality” as **meta rules** for A1/A2, without contaminating B or changing root constraints.

==================================================
1) Boundary Statement (hard cut)
==================================================

Everything above the boundary is probabilistic/high-entropy:
- A2 mining/drafting/indexing
- A1 exploration (“wiggle room”)

Everything below the boundary is deterministic/low-entropy:
- A0 compilation + packaging
- B adjudication
- SIM execution + evidence emission

The boundary is implemented as:
- `A1_STRATEGY_v1` (A1 output declaration)
  -> deterministic parsing + canonicalization
  -> deterministic compilation into B artifacts (`EXPORT_BLOCK`)

==================================================
2) Nominalized Reality (meta rule)
==================================================

Operational meaning:
- Only canonical, validated artifacts are admissible for B.
- Raw natural language and confidence scores are never passed to B.

Minimum enforcement:
- A0 must reject strategy inputs that cannot be canonicalized.
- A0 must strip/discard these fields before compilation:
  - `confidence`, `probability`, `raw_text`, `embedding`, `hidden_prompt`

==================================================
3) Locality (meta rule)
==================================================

Operational meaning:
- Every action is scoped.
- No ambient authority.

Minimum enforcement targets:
- A1 can propose, but cannot modify canon.
- A0 can write only inside the active run directory.
- SIM can read code and write only to run-local outputs.
- No writes to `core_docs/`.

==================================================
4) Capability Policy (ABAC-like, minimal)
==================================================

Define a small capability set and fail-closed on missing capability declarations.

Capability examples:
- `read_core_docs`
- `read_a2_state`
- `write_run_dir`
- `emit_export_block`
- `execute_sim`
- `ingest_sim_evidence`

Policy default:
- deny-by-default
- if policy cannot be evaluated: deny

==================================================
5) Root Constraints Remain Only Two
==================================================

This document does not introduce new ontological root constraints.

Root constraints remain:
- `F01_FINITUDE`
- `N01_NONCOMMUTATION`

All other “constraints” in this doc are operational harness rules.

