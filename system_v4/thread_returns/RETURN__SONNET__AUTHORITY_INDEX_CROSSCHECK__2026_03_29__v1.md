# Authority Index Cross-Check Report

**Thread return:** `RETURN__SONNET__AUTHORITY_INDEX_CROSSCHECK__2026_03_29__v1.md`  
**Date:** 2026-03-29  
**Task:** Cross-check `CURRENT_AUTHORITATIVE_STACK_INDEX.md` against `THREAD_CONSOLIDATION_CONTROLLER.md` and `AXIS0_CURRENT_DOCTRINE_STATE_CARD.md`.  
**Scope:** Report mismatch, omission, or overbreadth only. No doctrine change.

---

## Summary

**3 mismatches, 2 omissions, 1 overbreadth finding.** Details below.

---

## 1. Mismatches

### M1 — `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md` listed in authority index §1.2 but absent from controller and Ax0 state card owner stacks

**Index claim (§1.2, line 25–26):**
> `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md` — "compact operator handoff card for the current kernel → bridge → cut read; compressed surface only, not a replacement for owner packets"

**Controller §2.1 Ax0 stack enumeration** lists:
- geometry / Ax0 separation
- bridge owner packets
- cut owner packets
- typed shell cut contract
- typed history-window cut contract
- Xi_hist emission packet
- typed cut sync card
- compact handoff / closeout / bridge-owner sync

"Compact handoff / closeout / bridge-owner sync" nominally covers this file, but the controller does not name `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md` explicitly — it is subsumed under indirect language.

**Ax0 state card §6 (Owner Stack)** does not list `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md` at all. The state card lists 8 owner surfaces; this file is not among them.

**Finding:** The authority index promotes `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md` to a named authority surface in §1.2. The Ax0 state card omits it from the owner stack entirely. The controller mentions the function ("compact handoff") but not the file. There is a cross-document naming gap that leaves the file's authority tier ambiguous: the index implies §1 authority; the state card implies at most §2 support status.

---

### M2 — `AXIS0_CURRENT_DOCTRINE_STATE_CARD.md` is absent from the authority index entirely

**Controller §1 (implicitly):** The controller packet is listed in the authority index at §1.1 correctly. However, the Ax0 state card (`AXIS0_CURRENT_DOCTRINE_STATE_CARD.md`) is itself a controller-grade integration surface that owns the "earned / open / killed / unvalidated" summary the controller is directed to produce (controller §6). This file is not listed in the authority index under any tier — not §1 (authority), not §2 (support), not §3 (superseded).

**Finding:** `AXIS0_CURRENT_DOCTRINE_STATE_CARD.md` is unrepresented in the authority index. Given that the controller (§6) explicitly designates the "earned / open / killed / unvalidated" packet as the immediate next controller deliverable, and the state card is precisely that deliverable, its omission from the index is a structural omission. The index does not classify it, which creates an authority void: a controller-grade surface that has no tier assignment in the stack index.

---

### M3 — Killed/demoted list mismatch between index §3.3 and state card §3

**Index §3.3** lists:
1. raw local `L|R` as sufficient bridge doctrine — killed as sufficient; control only
2. uncoupled pure-product `L|R` as final doctrine cut — demoted to control only
3. old shell-strata pointwise implementation / old shell-strata pointwise cut — killed
4. single-spinor, single reduced density, and raw `eta`-only cut stand-ins — killed

**State card §3** lists:
1. raw local `L|R` as sufficient bridge doctrine — `KILL` ✓
2. uncoupled pure-product `L|R` as final doctrine cut — `DEMOTE` to control only ✓
3. old shell-strata pointwise **bridge** — `KILL`
4. old shell-strata pointwise **cut shortcut** — `KILL`
5. single-spinor, single reduced density, or raw `eta` as final cut object — `KILL` ✓
6. **runtime `GA0` as doctrine object — `DEMOTE` to proxy only**

**Finding:** The authority index §3.3 omits item 6: "runtime `GA0` as doctrine object — `DEMOTE` to proxy only." This kill/demote entry exists in the Ax0 state card §3 but has no counterpart in the index's §3.3 list. The index is understating the kill/demote register relative to the state card. This is not a supersede issue but a live-doctrine-status omission from the index.

Additionally, the index §3.3 conflates the two distinct shell-strata kills (pointwise bridge kill vs. pointwise cut shortcut kill) into a single line item. The state card distinguishes them as separate kills. This conflation is imprecise but not a substantive doctrine error.

---

## 2. Omissions

### O1 — `AXIS0_BRIDGE_RELATION_PACKET.md` is in the index §2.1 but absent from both the controller layer enumeration and the state card §6 owner stack

**Index §2.1** lists `AXIS0_BRIDGE_RELATION_PACKET.md` as a support surface for "bridge-family relation locks."

**State card §6** does not list it.  
**Controller §2.1** does not enumerate it.

**Finding:** `AXIS0_BRIDGE_RELATION_PACKET.md` has support-surface status in the index but is absent from both the controller stack enumeration and the state card owner stack. This is a mild omission from the state card/controller rather than an index error, but it produces an inconsistency: the index grants it a live support tier that neither of the other two documents acknowledges. Since this file is not superseded and is not in §3, it occupies a gray zone.

---

### O2 — `shell/history unification` is open in the state card but has no corresponding open-item entry in the authority index §4

**State card §2 (Live But Open)** includes:
> "shell/history unification — still open; typed sync exists but not one theorem"

**Index §4.1 (Ax0 open items)** lists:
- final canon `Xi` is open
- final doctrine-level cut `A|B` is open
- exact shell algebra for `A_r|B_r` is open
- exact microscopic meaning of `I_r|B_r` is open
- typed shell cut contract exists, but exact shell algebra is still open
- typed history-window cut contract exists, but exact family is still open
- final doctrinal role of the point-reference cut family is open and secondary

**Finding:** The shell/history unification open item — explicitly registered in the state card as a distinct unresolved claim — is absent from the authority index §4.1. The individual shell and history items are listed, but the composite unification question (one theorem encompassing both) is not separately registered. This is an omission from the open-items register.

---

## 3. Overbreadth

### OB1 — `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md` is listed under §1.2 (authority tier), which is too broad given its stated role

**Index §1.2** places this file at authority tier alongside `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md`, and `AXIS0_CUT_TAXONOMY.md` — all of which are genuine owner packets.

**The index itself qualifies** the handoff card as "compressed surface only, not a replacement for owner packets."

**The state card §6** does not include it in the owner stack at all; the state card lists only 8 files, all genuine owner or typed-contract surfaces.

**Finding:** The handoff card is self-described in the index as "not a replacement for owner packets," and the state card corroborates this by omitting it from the owner stack. But the index places it in §1 (authority surfaces) rather than §2 (support surfaces). This is overbreadth: the file is indexed at a tier higher than its stated role and its absence from the state card owner stack justify. It belongs in §2 (support surfaces), consistent with its own description as a "compact" read surface, not an owner packet.

---

## 4. No-Finding Items (Confirmed Clean)

The following were checked and found to be consistent across all three documents:

- Controller §1.1 authority claim: consistent with index §1.1 ✓
- Thread B staging-only status: consistent across index §1.3, §2.2, §4.2 and controller §2.2, §4.2 ✓
- Thread B open items (permit block, deferred signed Ax0, lexeme registry, axis export promotion): consistent between index §4.2 and controller §2.2 / §4.2 ✓
- Ax0 "earned" ranked read (kernel/bridge/cut/pointwise): index §3.3 controls/kills match controller §2.1 and state card §1 ✓
- Controller stop rules (§5): not referenced in index (appropriately: process rules, not stack surfaces) ✓
- State card anti-smoothing reads (§5): not required in index (appropriately: doctrine-facing not index-facing) ✓

---

## 5. Register of Findings

| ID | Type | Source document | Finding |
|---|---|---|---|
| M1 | Mismatch | Index §1.2 vs state card §6 | `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md` present in index §1, absent from state card owner stack |
| M2 | Mismatch / Omission | Index (all sections) | `AXIS0_CURRENT_DOCTRINE_STATE_CARD.md` not assigned any tier in the index |
| M3 | Mismatch | Index §3.3 vs state card §3 | Index §3.3 omits `runtime GA0 as doctrine object — DEMOTE`; conflates two distinct shell-strata kills into one |
| O1 | Omission | State card §6, controller §2.1 | `AXIS0_BRIDGE_RELATION_PACKET.md` in index §2.1 but absent from both state card and controller enumerations |
| O2 | Omission | Index §4.1 vs state card §2 | `shell/history unification` open item in state card not registered in index §4.1 |
| OB1 | Overbreadth | Index §1.2 | `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md` indexed at §1 authority tier; its stated role and absence from state card owner stack indicate §2 support tier is correct |

---

## 6. Constraints Observed

- No doctrine changed.
- No surface rankings altered.
- No open items silently closed.
- No staging surfaces promoted.
- This report records findings only.
