# Thread B Entropy Math Term Runbook

**Date:** 2026-03-29
**Status:** SUPERSEDED. Older entropy math-term runbook retained for audit context only. Do not use as the current Thread B staging runbook.
**Superseded by:** [THREAD_B_STACK_AUDIT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_STACK_AUDIT.md), [THREAD_B_TERM_ADMISSION_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_TERM_ADMISSION_MAP.md), and [THREAD_B_ENTROPY_EXPORT_RUNBOOK.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_ENTROPY_EXPORT_RUNBOOK.md).

---

## 1. Goal

Repeat a bounded Thread B entropy round that:

- starts from root-first fences already locked upstream
- keeps entropy work at pure `MATH_DEF + TERM_DEF`
- avoids permit stubs
- avoids token-placeholder drift
- keeps bridge/cut dependence visible

---

## 2. Inputs

Read first:

- [THREAD_B_CONSTRAINT_RATCHET_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_CONSTRAINT_RATCHET_CARD.md)
- [THREAD_B_TERM_ADMISSION_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_TERM_ADMISSION_MAP.md)
- [THREAD_B_STACK_AUDIT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_STACK_AUDIT.md)
- [THREAD_B_ENTROPY_EXPORT_VALIDATION.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_ENTROPY_EXPORT_VALIDATION.md)
- [THREAD_B_ENTROPY_MATH_TERM_PACKET.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_ENTROPY_MATH_TERM_PACKET.md)

Keep below the richer local owner surfaces:

- [PROTO_RATCHET_ENTROPY_ALIGNMENT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ENTROPY_ALIGNMENT.md)
- [AXIS_MATH_BRANCHES_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_MATH_BRANCHES_MAP.md)
- [PROTO_RATCHET_ADMISSIBLE_BRANCH_SPACE.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ADMISSIBLE_BRANCH_SPACE.md)
- [PROTO_RATCHET_RIVAL_REALIZATION_CANDIDATES.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_RIVAL_REALIZATION_CANDIDATES.md)

---

## 3. Allowed Moves

- tighten pure entropy `MATH_DEF` wording
- tighten pure entropy `TERM_DEF` wording
- strip risky lexemes from objects/invariants/domain/codomain fields
- add design-only notes about downstream dependence
- improve owner-stack rank warnings

---

## 4. Forbidden Moves

- no `CANON_PERMIT`
- no evidence-satisfied wording
- no bridge or cut closure
- no geometry reopening
- no attempt to make the B-thread packet the local owner surface
- no placeholder tokens presented as registry-safe

---

## 5. Safe Lane Split

Use bounded lanes for:

1. boot-fence audit
2. entropy-term keep/fence audit
3. lexeme/token cleanup
4. owner-stack authority audit
5. packet drafting

---

## 6. Good Output Shape

The clean output of the round is:

- one owner packet for pure entropy `MATH_DEF + TERM_DEF`
- optionally one review-only note about later permit separation

Not the output:

- a submission-ready export block
- a permit batch
- a bridge/cut decision packet

---

## 7. Launch Prompt

```text
$codex-autoresearch
Mode: plan
Run a strict Thread B entropy math/term cleanup round only. Keep the scope to pure MATH_DEF + TERM_DEF for von_neumann_entropy, mutual_information, conditional_entropy, and coherent_information. Use system_v4/docs/THREAD_B_ENTROPY_MATH_TERM_PACKET.md as the owner packet. Read system_v4/docs/THREAD_B_STACK_AUDIT.md and system_v4/docs/THREAD_B_ENTROPY_EXPORT_VALIDATION.md first. Use bounded parallel lanes for boot-fence audit, keep/fence audit, lexeme cleanup, owner-stack authority audit, and packet drafting. Do not add CANON_PERMIT. Do not imply evidence satisfaction. Do not hide bridge/cut dependence. Output only doc updates in system_v4/docs/.
```
