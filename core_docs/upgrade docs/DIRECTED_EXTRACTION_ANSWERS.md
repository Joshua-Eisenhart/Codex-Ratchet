
# DIRECTED EXTRACTION — ANSWERS FROM THREAD CONTEXT
MODE: STATE_EXTRACTION_ONLY

NOTE
This document answers the directed extraction questions using ONLY material present in the preceding thread.
No redesign. No invention. Ambiguities preserved.
If something was not explicitly resolved, it is marked:
UNSPECIFIED — DO NOT INFER

---

## QUESTION SET A — ZIP ENUMERATION

The following ZIP types were explicitly discussed or repeatedly implied in the thread:

1. MEGABOOT_ZIP
- Producer: Human / A1
- Consumer: A1 (initial load), A0
- Purpose: Single authoritative boot document containing all thread definitions and constraints.

2. RATChet_BUNDLE_ZIP
- Producer: Human / A0
- Consumer: A0, B
- Purpose: Transport of ratcheted canon terms and structure.

3. FULL_LEDGER_ZIP (also called FULL+)
- Producer: B
- Consumer: A0
- Purpose: Complete deterministic canon state sufficient to restore B.

4. FULL++_ARCHIVE_ZIP
- Producer: A1 (Rosetta + Mining)
- Consumer: A0, A1 (reload)
- Purpose: FULL+ plus Rosetta overlays, mining artifacts, ambiguity, graveyard context.

5. ZIP_JOB (generic)
- Producer: A0 / A1 / SIM
- Consumer: A0 / B / SIM TERMINAL
- Purpose: Deterministic chatless subagent carrier.

6. SIM_PROPOSAL_ZIP
- Producer: A0
- Consumer: B
- Purpose: Request approval to run a simulation.

7. SIM_RUN_ZIP
- Producer: A0
- Consumer: SIM TERMINAL
- Purpose: Execute an approved simulation.

8. SIM_RESULTS_ZIP
- Producer: SIM TERMINAL
- Consumer: A0
- Purpose: Raw outputs of a simulation run.

9. SIM_EVIDENCE_ZIP
- Producer: A0
- Consumer: B
- Purpose: Deterministic evidence ingestion after sim execution.

No additional ZIP types were enumerated without ambiguity.

---

## QUESTION SET B — A0 BATCH SCALE

Extracted statements:

- A0 was failing due to *small batches*.
- A0 must produce *massive batches*, not conservative ones.
- Numbers like “1000 items” were mentioned as scale intuition, not locked constants.
- Batch size discussion was qualitative, not numeric.
- Batch scale is tied to:
  - Exploration vs convergence phase
  - Graveyard size
  - Acceptance ratio trends

Explicit numeric thresholds:
UNSPECIFIED — DO NOT INFER

---

## QUESTION SET C — SHARDING HEURISTICS

Explicitly stated constraints:

- LLMs do not handle very long files well.
- ZIPs must not split.
- Documents inside ZIPs must shard.
- Sharding is for *LLM usability*, not system correctness.

Heuristics discussed:
- Shard by manageability, not semantics.
- Sharding limits were discussed qualitatively ("LLMs hate long files").

No explicit heuristics like token counts or topic-based sharding were finalized.

UNSPECIFIED — DO NOT INFER further rules.

---

## QUESTION SET D — FULL+ CONFIRMATION

Extracted intent:

- FULL+ can be produced by B.
- FULL+ is sent to A0.
- A0 must "confirm" FULL+ before proceeding.

What confirmation means:
- Structural sanity
- Completeness

Whether A0 can refuse:
- YES, refusal was explicitly discussed.

Refusal consequences:
UNSPECIFIED — DO NOT INFER

---

## QUESTION SET E — FULL++ CONFIRMATION

Extracted intent:

- FULL++ includes Rosetta and mining overlays.
- FULL++ is produced by A1.
- A0 must confirm FULL++ formatting and structure.

Nature of confirmation:
- Structural only
- Content-blind

Whether FULL++ can exist without confirmation:
- YES, but flagged as unconfirmed.

Failure handling:
UNSPECIFIED — DO NOT INFER

---

## QUESTION SET F — PHASE TRANSITION SIGNALS

Explicit discussion:

- Exploration → convergence is real and important.
- No deterministic signal was finalized.
- Indicators discussed informally:
  - Acceptance ratio trends
  - Graveyard churn
  - Recurrence of structures
- Human judgment remains part of the loop.

Explicit rule:
UNSPECIFIED — DO NOT INFER deterministic transition criteria.

---

## EXTRACTION NOTES

- Multiple contradictions were preserved, especially around:
  - Role of Thread S
  - Save vs archive responsibility
- Mode drift and LLM behavior control were repeatedly discussed as unresolved.
- Extraction process itself was identified as a system feature.

END OF DOCUMENT
