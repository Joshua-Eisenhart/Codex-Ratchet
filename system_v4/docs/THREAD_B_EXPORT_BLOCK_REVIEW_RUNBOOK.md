# Thread B Export Block Review Runbook

**Date:** 2026-03-29
**Status:** SUPERSEDED. Older generic export-block review runbook retained for audit context only. Do not use as the current Thread B review launch surface.
**Superseded by:** [THREAD_B_STACK_AUDIT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_STACK_AUDIT.md), [THREAD_B_STAGING_VALIDATION_PACKET.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_STAGING_VALIDATION_PACKET.md), and [THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md).
**Purpose:** Reusable bounded launch surface for reviewing or refining candidate `EXPORT_BLOCK v1` wrappers before any real Thread B submission attempt.

---

## 1. Owner Stack

Read in this order:

1. [THREAD_B_TERM_ADMISSION_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_TERM_ADMISSION_MAP.md)
2. [THREAD_B_ENTROPY_EXPORT_CANDIDATES.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_ENTROPY_EXPORT_CANDIDATES.md)
3. [THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md)

---

## 2. Reusable Prompt

```text
$codex-autoresearch
Mode: plan
Run a strict Thread-B export-block review round. Use system_v4/docs/THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md as the owner packet. Scope only: kernel grammar fidelity, lexeme risk, token placeholder cleanup, and whether the coherent_information permit stub should stay in the same batch or be split out. Do not widen beyond the four entropy terms. Do not treat review wrappers as ready-to-submit artifacts. Output only updates to export-review docs in system_v4/docs/.
```

---

## 3. Do Not Smooth

- Do not turn export review into actual export submission.
- Do not let a single batch hide the controversial permit stub.
- Do not let token placeholders pass as real registry-safe choices.
