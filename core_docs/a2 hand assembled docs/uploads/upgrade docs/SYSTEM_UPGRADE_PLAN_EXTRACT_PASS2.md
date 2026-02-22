# SYSTEM UPGRADE PLAN — STATE EXTRACTION (PASS 2)

MODE: STATE_EXTRACTION_ONLY

This document is a continuation of PASS 1.
It does not fix, redesign, or resolve anything.
It records contradictions, drift, and unresolved intent exactly as observed.

---

## 1. CONTRADICTIONS IDENTIFIED

- Megaboot described as:
  - A single document containing all boots
  - AND later treated as split ZIP-based artifacts
  - This contradiction was not noticed for an extended period

- ZIPs described as:
  - Deterministic chatless subagents
  - AND later confused with extraction templates and transport tools
  - Boundary between ZIP-as-agent and ZIP-as-container repeatedly collapsed

- Thread S:
  - Declared unnecessary / absorbed
  - Later required for save, graveyard, or rosetta
  - Role never stabilized

---

## 2. FAILURE VS NON-ATTEMPT

Observed failures:
- A0 outputting small batches instead of mass batches
- Save process requiring excessive manual steps
- LLM drifting into narrative/proof-first modes

Not actually attempted:
- True megaboot upgrade (core file unchanged)
- Unified ZIP-first communication baked into megaboot
- Deterministic restore path using ZIPs only

---

## 3. MODE CONFUSION (LLM VS SYSTEM)

- “Mode” used in two distinct senses:
  - Implicit LLM internal state (hallucination, smoothing, narrative drift)
  - Explicit system-enforced constraint frames

- A1 modes discussed extensively, but:
  - Not cleanly separated from extraction tooling
  - Not cleanly separated from rosetta/mining discussion

---

## 4. THINKING VS INSTANT

Empirical observations:
- Instant works better for extraction passes
- Thinking tends to:
  - Collapse structure
  - Invent coherence
  - Skip contradictions

Unresolved:
- Exact criteria for safely invoking Thinking
- Whether Thinking can be constrained reliably

---

## 5. DRIFT SOURCES RECORDED

- LLM defaults to classical proof/narrative
- Repeated reintroduction of “design” framing
- Confusion between:
  - Transporting state
  - Fixing state
  - Designing new systems

---

## 6. UNRESOLVED / UNSPECIFIED

UNSPECIFIED — DO NOT INFER:
- Final role of Rosetta relative to canon
- Exact boot-time verification handshake
- Whether A1 mode confirmation can be enforced deterministically
- Whether ZIP templates should self-audit or be externally audited

---

## PROCESS TRACE

- PASS 2 performed after PASS 1
- Extraction only
- No deletions from PASS 1
- Confidence: moderate
- Drift risk: still high

END OF PASS 2
