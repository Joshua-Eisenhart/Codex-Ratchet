# A1/A2 Conformance Checklist (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: provide a deterministic checklist to audit whether A1/A2 outputs are fit for A0/B/SIM processing.

==================================================
Checklist
==================================================

Use this checklist before long runs.

1. Root constraints present
- `F01_FINITUDE` admitted
- `N01_NONCOMMUTATION` admitted

2. A2 state integrity
- `work/a2_state/` contains only expected fixed files
- `memory.jsonl` append-only format valid (one JSON object per line)
- `fuel_queue.json` schema valid and sorted deterministically

3. A1 strategy validity
- strategy schema is `A1_STRATEGY_v1`
- budget fields present and finite
- overlay bans present
- no unsupported fields required by downstream compiler

4. B boundary safety
- no raw NL intended for B-scanned fields
- no unsupported SPEC_KIND planned
- no direct YAML submission to B

5. Term bundle completeness
- each target term includes:
  - TERM_DEF plan
  - positive sim reference
  - negative sim reference (>=1) when required
  - at least one plausible alternative

6. Evidence path completeness
- positive and negative evidence tokens are explicitly declared
- sim references resolve to scripts or known templates
- CANON_PERMIT path exists where protected term states are needed
- each negative sim includes explicit `failure_mode_id` + expected outcome class

7. Graveyard integrity
- alternatives are structurally tied to targets
- expected failure tags are explicit
- graveyard entries include `raw_lines` after B rejection
- graveyard alternatives are not used as a substitute for negative sim evidence

8. Determinism + replay
- A0 canonicalization hash for strategy is recorded
- run logs/outbox are append+shard
- sim manifests include input/code/output hashes

9. Stall guardrails
- stall conditions configured
- repair operators configured
- unresolved targets are written back to A2 fuel with reason tags

10. Tiered sim architecture
- each sim target has an explicit tier (`T0`..`T6`)
- no tier skip in promotion plan
- tier dependencies are explicit and acyclic
- stress families are declared (`BASELINE`, `BOUNDARY_SWEEP`, `PERTURBATION`, `ADVERSARIAL_NEG`, `COMPOSITION_STRESS`)

11. Master sim gating
- whole-system sim target is defined but gated (no bypass)
- promotion gates `G1`..`G5` are declared
- whole-system negative sim + graveyard alternatives are required

==================================================
Result
==================================================

Conformance result should be recorded as:
- `PASS` only if all checklist items pass
- otherwise `FAIL` with explicit failed item ids
