# Audit Gates + Success Criteria (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: make “success” and “stall” explicit, and define audit gates that prevent paperclip / meaningless token-churn.

==================================================
1) Definitions (explicit)
==================================================

- “Admitted”:
  - B accepted a candidate into canonical state (AXIOM_HYP or SPEC_HYP).

- “Term exists”:
  - TERM literal is present in TERM_REGISTRY (via TERM_DEF).

- “Canonically allowed term”:
  - TERM literal state is `CANONICAL_ALLOWED` (evidence-gated).

- “Ratcheted (meaningful)”:
  - a term/spec is admitted AND
  - positive sim evidence exists AND
  - negative sim evidence exists (>= 1) AND
  - at least one plausible nearby alternative failed and is present in graveyard

==================================================
2) Audit Gate: Evidence Coverage
==================================================

For each meaningful survivor term bundle:
- TERM_DEF exists
- SIM_SPEC exists and is ACTIVE with evidence token recorded
- NEG_SIM_SPEC exists and is ACTIVE with evidence token recorded
- CANON_PERMIT exists and TERM is upgraded to `CANONICAL_ALLOWED` (when applicable)

Fail conditions:
- TERM admitted but no possible positive sim path exists (per binding or sim builder)
- TERM admitted but negative sim path missing while term is used downstream as a primitive
- only one nominal "happy-path" sim exists with no boundary/perturbation/adversarial coverage

==================================================
2A) Audit Gate: Stress and Breadth
==================================================

For each meaningful survivor target class:
- baseline sim exists
- boundary sweep sim exists
- perturbation sim exists
- adversarial negative sim exists
- composition stress sim exists (where tier dependencies exist)

Fail conditions:
- stress families are missing
- stress outputs are non-replayable or non-deterministic
- stress suite is present but not target-coupled (generic unrelated runs)

==================================================
3) Audit Gate: Graveyard Coverage
==================================================

For each meaningful survivor:
- at least one alternative candidate exists and failed (graveyard)
- the graveyard record includes `raw_lines`

Fail conditions:
- graveyard ratio is artificially inflated (junk content not structurally tied to a target term)
- graveyard entries lack raw lines

==================================================
4) Audit Gate: Overlay/Jargon Leakage
==================================================

Fail conditions:
- overlay/jargon terms appear as TERM literals in canon
- overlay/jargon tokens appear unquoted in B-scanned fields

==================================================
5) Audit Gate: Determinism + Replay
==================================================

Required:
- deterministic state serialization + stable hash
- deterministic logs/outbox sharding
- sim manifests include input hash + output hash + code hash + manifest hash

Fail conditions:
- evidence cannot be replayed (missing manifest / missing code hash / missing output hash)
- state hash differs between identical runs with identical inputs

==================================================
6) Stall Conditions (explicit)
==================================================

Stall is detected if any of the following holds over a configured window:
- no new admissions for N cycles
- > 90% of generated candidates are rejected for the same structural reason (suggests a systemic mismatch)
- evidence pending grows without bound (sims not runnable / missing / never satisfied)
- parked set grows without bound (dependency deadlock)

==================================================
7) Meaningful Progress Conditions (explicit)
==================================================

Progress is not “more terms”; it is evidence-backed structure formation.

Positive progress signals:
- increasing count of `CANONICAL_ALLOWED` terms with positive+negative evidence
- increasing depth of compound terms whose atoms are all evidence-backed
- emergence of stable sim composition chains (small sims reused by larger sims)
- graveyard reasons diversify (not stuck on one fence)

==================================================
8) Paperclip / Goodhart Alerts (explicit)
==================================================

High-risk failure modes:
- optimizing for admissions count rather than evidence + alternatives
- generating “alternatives” that are trivially invalid (junk) to pad graveyard ratio
- admitting terms that are never used or never evidence-backed
- allowing classical primitives (identity/equality/metric/time/probability) to leak in without evidence gates

When any alert triggers:
- freeze the run directory as noncanon evidence
- record the failure mode in A2 memory (append-only)
