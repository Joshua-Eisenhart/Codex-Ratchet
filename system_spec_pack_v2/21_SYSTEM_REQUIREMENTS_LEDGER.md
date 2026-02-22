# System Requirements Ledger (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: capture the full multi-document requirement surface (not only recent prompts) as explicit requirement IDs for traceability.

Primary sources:
- `system_v2/core_docs/BOOTPACK_THREAD_A_v2.60.md`
- `system_v2/core_docs/BOOTPACK_THREAD_B_v3.9.13.md`
- `system_v2/work/system_specs/A0_CONTRACT.md`
- `system_v2/work/system_specs/A1_DESIGN.md`
- `system_v2/work/system_specs/A2_DESIGN.md`
- `system_v2/work/system_specs/THREAD_BOUNDARIES.md`
- `system_v2/work/system_specs/PIPELINE_SPEC.md`
- `system_v2/work/a2_state/memory.jsonl`

==================================================
1) Root Constraint Requirements
==================================================

- `RQ-001` (MUST): `F01_FINITUDE` and `N01_NONCOMMUTATION` are non-negotiable root constraints.
- `RQ-002` (MUST): survivor order is canonical state; noncommutative order is never discarded.
- `RQ-003` (MUST): only B admits/rejects canon; no other layer may claim canon.
- `RQ-004` (MUST): A2/A1/A0/B/SIM role boundaries remain explicit and enforced.

==================================================
2) Layer Role Requirements
==================================================

- `RQ-010` (MUST): A1 has nondeterministic exploration ("wiggle") and deterministic compile handoff.
- `RQ-011` (MUST): A0 is deterministic packaging/compilation and not canon authority.
- `RQ-012` (MUST): B is deterministic staged adjudication.
- `RQ-013` (MUST): SIM is deterministic execution evidence producer.
- `RQ-014` (MUST): high-entropy docs are mined by A2; they are not direct B input.
- `RQ-015` (MUST): constraint ladder is fuel for A1 transformation, not direct canon dump.

==================================================
3) Batch and Exploration Requirements
==================================================

- `RQ-020` (MUST): batch policy is non-conservative exploration, not classical proof-only sequencing.
- `RQ-021` (MUST): A1 must explore alternatives/branches and preserve failed branches as information.
- `RQ-022` (MUST): when B rejects, rejection reasons feed deterministic repair operators.
- `RQ-023` (MUST): proposals must stay B-grammar valid; free prose never enters B artifacts.

==================================================
4) Term Ratchet Requirements
==================================================

- `RQ-030` (MUST): every admitted concept is represented by explicit ratcheted terms.
- `RQ-031` (MUST): compound terms are built from ratcheted smaller terms; additions are incremental.
- `RQ-032` (MUST): derived-only and lexeme fences are respected; no primitive smuggling.
- `RQ-033` (MUST): symbol/glyph usage (including `=`) is gated by admitted term policy.
- `RQ-034` (MUST): jargon labels (axis/Jung/IGT overlays) are noncanon overlays unless explicitly ratcheted as terms.

==================================================
5) Evidence and SIM Requirements
==================================================

- `RQ-040` (MUST): meaningful survivor status requires dynamic evidence, not static acceptance alone.
- `RQ-041` (MUST): each meaningful target has positive sim evidence.
- `RQ-042` (MUST): each meaningful target has negative sim evidence.
- `RQ-043` (MUST): each meaningful target has plausible failed alternatives in graveyard.
- `RQ-044` (MUST): SIM evidence is tokenized and ingested through B containers only.
- `RQ-045` (MUST): sim manifests use deterministic hashes (input/code/output/manifest).
- `RQ-046` (MUST): sims are tiered and compositional from small units to whole-system.
- `RQ-047` (MUST): a single whole-system sim target exists and is promotion-gated.
- `RQ-048` (MUST): sims include breadth/stress families (baseline, boundary sweep, perturbation, adversarial negative, composition stress).

==================================================
6) Graveyard Requirements
==================================================

- `RQ-050` (MUST): graveyard is structural and dynamic (resurrection space), not trash.
- `RQ-051` (MUST): graveyard entries are tied to real targets/alternatives, not ratio padding.
- `RQ-052` (MUST): each graveyard entry keeps replayable `raw_lines` and failure reason tags.
- `RQ-053` (MUST): both B-kills and SIM-kills are tracked for audit.

==================================================
7) Persistence and Doc-System Requirements
==================================================

- `RQ-060` (MUST): doc surface is controlled/lean; avoid uncontrolled file explosion.
- `RQ-061` (MUST): canonical operational logs are append-only with deterministic sharding.
- `RQ-062` (MUST): core source docs remain read-only; generated output is isolated to run/work areas.
- `RQ-063` (MUST): provenance/replay chain is maintained across A2/A1/A0/B/SIM events.
- `RQ-064` (MUST): A2 persistent brain keeps fixed-state files + append-only memory discipline.
- `RQ-065` (MUST): thread context is sealed as artifacts; do not rely on volatile chat memory.

==================================================
8) Governance and Safety Requirements
==================================================

- `RQ-070` (MUST): unknown/underdetermined facts are marked `UNKNOWN` instead of guessed.
- `RQ-071` (MUST): contradictions are recorded; they are not smoothed away.
- `RQ-072` (MUST): no direct policy bypass of B fences for convenience.
- `RQ-073` (MUST): no "paperclip" metric gaming (e.g., fake graveyard inflation, fake evidence).
- `RQ-074` (MUST): model-switch boundary is explicit per task (thinking vs coding execution).

==================================================
9) Long-Run System Intent Requirements
==================================================

- `RQ-080` (MUST): ratchet defines legal structures; sims execute structures; evidence feeds ratchet state.
- `RQ-081` (MUST): convergence is assessed via stable survivors, graveyard pressure, and tier promotion coverage.
- `RQ-082` (MUST): attractor-basin claims require cumulative evidence across tiers, not narrative assertion.
