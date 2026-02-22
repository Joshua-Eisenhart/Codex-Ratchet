# SYSTEM UPGRADE PLAN — EXTRACT PASS 6

This document is a raw extraction of intent, constraints, problems, partial solutions,
and unresolved contradictions from the conversation. It is NOT a design, solution,
or proposal. It preserves confusion, disagreement, repetition, and drift as data.

---

## AXIS OF EXTRACTION
Process-level failures, meta-process failures, and loop mechanics.

---

## CORE INTENT (REPEATED, VERBATIM-DERIVED)

- The goal is to UPGRADE the existing system, not redesign it.
- The megaboot is authoritative and singular.
- Bootpacks are derived from the megaboot.
- ZIP-based transport is an upgrade to communication, not a replacement of logic.
- Deterministic vs non-deterministic boundaries are essential.
- A1 exists as a boundary and mode controller.
- A0, B, and SIM TERMINAL must remain deterministic.
- The system must scale to massive size.
- Human usability and future automation are first-class constraints.

---

## PROCESS FAILURES IDENTIFIED

- Context drift across long conversations.
- LLM silently switching modes (analysis, narrative, helpfulness).
- Conflation of:
  - template vs extracted output
  - design vs transport
  - audit vs fix
- Loss of authoritative document reference.
- Accidental invention of architecture during audit.
- “Goodhart paperclip” behavior when size metrics dominate.
- Over-summarization when raw extraction was required.

---

## META-LEVEL INSIGHT (IMPORTANT)

- The act of extracting context is itself a non-deterministic process.
- Therefore, context extraction must:
  - be loop-based
  - preserve ambiguity
  - record instability
  - not converge prematurely
- This extraction process may need to be formalized as a reusable system tool.

---

## LOOP MECHANICS DISCUSSED

- Multiple extraction passes, each with a different focus.
- Each pass should:
  - produce a downloadable artifact
  - preserve contradictions
  - not overwrite previous passes
- “Go on” should trigger another loop, not re-analysis.
- Loops should report:
  - what axis was extracted
  - how many loops ran
  - rough completeness estimate (non-authoritative)

---

## ZIP EXTRACTION TOOL (STATUS)

- A general ZIP-based context extraction tool is being developed.
- It is separate from the system upgrade itself.
- ZIP = deterministic, chatless sub-agent.
- Docs inside ZIP = sub-sub agents with distinct rules.
- Redundancy across docs is acceptable to reduce drift.
- A META document inside the ZIP may be required to enforce rules across docs.
- Mode control during extraction remains unsolved.
- Friend’s graph/intent prompt may act as “reins” rather than hard constraints.

---

## A1 MODE DISCUSSION (RAW)

- “Mode” refers to the LLM’s implicit behavioral state.
- Failures discussed explicitly:
  - hallucination
  - drift
  - smoothing
  - narrative bias
  - helpfulness bias
- Modes are not labels; they are intended constraints.
- Deterministic mode switching may not be possible.
- Confirmation of mode change may be the only enforceable signal.
- Mode instability must be logged, not hidden.

---

## UNRESOLVED QUESTIONS (DO NOT RESOLVE)

- How to deterministically lock an LLM into a mode.
- Whether mode confirmation is sufficient.
- Whether extraction tools can be fully generalized.
- How many docs is “enough” without collapse.
- When to use thinking vs instant safely.
- How to prevent conflation across long sessions.

---

## CONTRADICTIONS PRESERVED

- Desire for determinism vs acceptance of non-determinism.
- Need for massive exploration vs bounded graveyard size.
- Wanting fewer docs vs needing redundancy.
- Wanting no redesign vs discovering implicit redesign needs.
- Using emotional pressure to shift modes vs wanting explicit control.

---

## STATUS ESTIMATE (NON-AUTHORITATIVE)

- Extraction completeness (overall): ~45–55%
- Major axes still remaining:
  - SIM-specific extraction
  - Megaboot vs bootpack confusion timeline
  - Exact upgrade list already “decided” vs still open
  - Failure taxonomy across attempts

---

END OF EXTRACT PASS 6
