# SYSTEM UPGRADE PLAN — EXTRACTION PASS 5 (MULTI-AXIS)

MODE: STATE_EXTRACTION_ONLY
SCOPE: MULTI-AXIS (ZIP EXTRACTION TOOLING + SYSTEM UPGRADE + PROCESS FAILURES)
NOTE: This document records intent, contradictions, and unresolved points. No fixes.

---

## AXIS A — ZIP-BASED STATE TRANSPORT (GENERAL TOOL)
- ZIPs intended as atomic, deterministic, chatless subagents.
- Docs inside ZIP may shard; ZIP never splits.
- Repeated failure mode observed: conflation of TEMPLATE vs OUTPUT ZIP.
- Repeated requirement: template ZIP must be a reusable specification; output ZIP must be populated from context.
- Drift observed when tool tries to summarize or redesign instead of verbatim extraction.
- Explicit contract introduced to prevent summarization and paraphrasing.

CONTRADICTIONS / AMBIGUITY:
- Whether extraction should be one large doc vs many specialized docs.
- Whether density constraints (>5KB) are realistic for all extracted axes.
- How to reliably force LLM mode compliance across multiple docs in one ZIP.

---

## AXIS B — MAIN SYSTEM UPGRADE (MEGABOOT / THREADS)
- Megaboot is a single document containing all boots; prior work mistakenly treated it as split.
- Desired upgrades are to be applied INSIDE the megaboot, not as external patches.
- ZIP communication is an upgrade to how threads communicate, not a replacement for megaboot.
- Intended thread consolidation:
  - A0 absorbs Thread S and SIM coordination.
  - A1 absorbs Rosetta and Mining.
  - B remains deterministic canon kernel.
  - SIM runs in external terminal only.

CONTRADICTIONS / AMBIGUITY:
- Whether Thread S exists conceptually (demoted vs eliminated).
- Whether FULL++ save is required or only FULL+ for most flows.
- How much Rosetta content should ever be loaded into B.

---

## AXIS C — A1 MODES AND LLM FAILURE CONTAINMENT
- Explicit discussion of LLM failure vectors: hallucination, drift, smoothing, narrative, helpfulness.
- Modes are intended to be REAL behavioral constraints, not labels.
- Mode changes are noncommutative and difficult to enforce deterministically.
- Strong emotional language and model switches were used historically to induce implicit mode changes.

CONTRADICTIONS / AMBIGUITY:
- Whether deterministic confirmation of a mode change is possible.
- Whether mode confirmation should be demanded or merely logged.
- Whether this belongs to system design or operator practice.

---

## AXIS D — SIM PIPELINE
- SIM is strictly mechanical and deterministic.
- Two artifacts per sim:
  - SIM_PROPOSAL_ZIP → approval path to B.
  - SIM_RUN_ZIP → execution in terminal.
- Results return to A0, then evidence to B.
- SIM never invents or interprets.

CONTRADICTIONS / AMBIGUITY:
- How many sims can be staged before ratchet approval.
- Whether Rosetta-originated sims require extra gating.

---

## AXIS E — GRAVEYARD
- Graveyard is mandatory and never dead.
- ≥50% interaction rule when non-empty.
- Graveyard is exploration fuel, not failure.
- Size should be "big enough to be useful," not maximal.

CONTRADICTIONS / AMBIGUITY:
- Exact caps and rotation policies.
- How aggressively A0 should mine graveyard vs fresh space.

---

## AXIS F — PROCESS FAILURE MODES (META)
- Repeated loop failures due to:
  - Over-auditing causing drift.
  - Conflation of tools vs targets.
  - Loss of context due to summarization.
- Explicit desire to capture CONFUSION and CONTRADICTION, not resolve them.
- Recognition that the extraction process itself is valuable system content.

---

## OPEN ITEMS (UNRESOLVED BY DESIGN)
UNSPECIFIED — DO NOT INFER

---

END OF PASS 5
