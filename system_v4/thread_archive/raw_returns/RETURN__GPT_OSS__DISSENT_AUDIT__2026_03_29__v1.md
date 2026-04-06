# Dissent Audit – Authority Stack

**Date:** 2026-03-29
**Auditor:** GPT‑OSS (Medium)

---

## 1. Scope
This report reviews the following three authoritative artifacts:

1. `CURRENT_AUTHORITATIVE_STACK_INDEX.md`
2. `THREAD_B_LANE_HANDOFF_PACKET.md`
3. `AXIS0_CURRENT_DOCTRINE_STATE_CARD.md`

The goal is to locate **over‑broad**, **over‑narrow**, or **internally inconsistent** authority definitions **without altering any doctrine**.

---

## 2. Findings

### 2.1 Over‑Broad Authority Surfaces
| Surface | Issue | Evidence |
|---|---|---|
| **Thread B authority** (Stack Index §1.3) | Declares Thread B as an authority for “current Thread B staging status, surviving surfaces, resolved cleanup items, and bounded next steps” while the Lane Handoff Packet (section 1.3) repeatedly stresses that Thread B **remains staging‑only** and **does not own canon, permit, or bridge/cut closure**. The dual wording creates an over‑broad perception of ownership. | Stack Index lines 28‑35 vs. Lane Handoff Packet lines 30‑33. |
| **Ax0 support surfaces** (Stack Index §2.1) | Lists many support documents (e.g., `AXIS0_TYPED_SHELL_CUT_CONTRACT.md`) as “support surfaces” but the Doctrine State Card treats several of these (e.g., typed shell cut contract) as **live but open** rather than purely supportive, blurring the boundary between support and authority. | Stack Index lines 41‑48 vs. Doctrine Card lines 21‑24. |

### 2.2 Over‑Narrow Authority Surfaces
| Surface | Issue | Evidence |
|---|---|---|
| **Controller authority** (Stack Index §1.1) | Described only as authority for “Ax0 integration, bounded worker routing, stop rules, and final integration of compact sync surfaces”. The Lane Handoff Packet shows the controller also reviews **lexeme registry collisions**, **entropy split decisions**, and **review‑shape acceptances** (sections 4.1‑4.4). The controller’s remit is therefore broader than the index states. | Stack Index lines 11‑15 vs. Lane Handoff Packet lines 61‑93. |
| **Bridge‑to‑cut handoff** (Doctrine Card line 23) | Presented as an explicit owned handoff, yet the Stack Index does not list any dedicated authority surface for this handoff, leaving it unaccounted for in the top‑level authority map. | Doctrine Card line 23; absent in Stack Index. |

### 2.3 Internal Inconsistencies
| Area | Conflict | Details |
|---|---|---|
| **Status of `THREAD_B_AXIS_MATH_EXPORT_CANDIDATE.md`** | Stack Index (section 3.2) marks it as a *scratch / retracted* artifact, while the Lane Handoff Packet (section 3) lists a **retraction banner** but also references it in the “Fixes Applied” table as “RETRACTED — SCRATCH ARTIFACT banner added”. The wording suggests it is still being considered, creating ambiguity about its lifecycle. |
| **Open Items – Ax0 vs. Thread B** | Both documents list open items (Stack Index §4.1 & §4.2; Doctrine Card §2). However, the Stack Index claims “final canon `Xi` is open” (line 144) while the Doctrine Card lists “final canon `Xi` still open” (line 34) **and** the Lane Handoff Packet’s “Do Not Smooth” section (lines 136‑138) repeats the same but adds “strongest executable bridge family != final canon `Xi`”. The redundancy is fine, but the Stack Index does not surface the *inequality* statement, which is a critical consistency note. |
| **Superseded vs. Active Surfaces** | Stack Index §3 lists superseded Thread B items, but the Lane Handoff Packet’s active surface table (lines 45‑57) includes `THREAD_B_AXIS_MATH_EXPORT_BLOCK_REVIEW.md` as **REVIEW_ONLY** while the superseded list does not mention this file, potentially causing confusion about its status. |

---

## 3. Summary of Risks
1. **Misinterpretation of authority breadth** – Over‑broad statements may lead downstream agents (e.g., Codex) to treat Thread B as a canonical authority, violating the intended staging‑only constraint.
2. **Missing authority entries** – The bridge‑to‑cut handoff is not represented in the top‑level index, risking omission in governance workflows.
3. **Ambiguous lifecycle of scratch artifacts** – Inconsistent labeling of `THREAD_B_AXIS_MATH_EXPORT_CANDIDATE.md` could cause accidental inclusion in future pipelines.
4. **Redundant open‑item listings** – While not a functional error, duplicated open‑item statements without cross‑reference may hinder audit efficiency.

---

## 4. Recommendations (Non‑Prescriptive)
* **Clarify controller scope** in the Stack Index to align with the Lane Handoff Packet’s review responsibilities.
* **Add an explicit authority entry** for the bridge‑to‑cut handoff in the Stack Index.
* **Standardize status terminology** for scratch/retracted artifacts across all documents (e.g., always use “SCRATCH – RETRACTED”).
* **Create a cross‑reference table** linking open‑item entries between the Stack Index and Doctrine State Card to reduce duplication.

---

*This audit is intentionally **bounded** – it does not propose doctrinal changes, only highlights where the current authority definitions may be too broad, too narrow, or internally inconsistent.*
