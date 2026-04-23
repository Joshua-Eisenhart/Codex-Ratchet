# External Thread Boot Packet

**Lane ID:** `DOC_CLEANUP_AUDIT`
**Date:** `2026-03-29`
**Status:** ACTIVE BOOT PACKET
**Controller:** `CURRENT_AUTHORITATIVE_STACK_INDEX.md`

---

## 1. Purpose

Audit `system_v4/docs/` for stale, duplicated, superseded, or scratch-level surfaces that should not read as active authority.

---

## 2. Authority And Scope

Authority surface:

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/CURRENT_AUTHORITATIVE_STACK_INDEX.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/THREAD_CONSOLIDATION_CONTROLLER.md`

Scope:

- detect stale or duplicated doc surfaces
- recommend `keep`, `supersede`, `scratch`, or `archive_only`
- compare secondary packets against the current authority stack

Do not:

- change doctrine
- rewrite owner rankings
- promote review or staging surfaces

---

## 3. Files To Read

Required:

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/CURRENT_AUTHORITATIVE_STACK_INDEX.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/THREAD_CONSOLIDATION_CONTROLLER.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/AXIS0_CURRENT_DOCTRINE_STATE_CARD.md`

Optional:

- any `system_v4/docs/*.md` files needed to evaluate duplication or stale status

Forbidden:

- runtime code edits
- probe edits
- canon or permit decisions

---

## 4. Deliverable

Write exactly one return packet to:

`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/thread_returns/RETURN__<MODEL>__DOC_CLEANUP_AUDIT__2026_03_29__v1.md`

If you need a supporting doc, create at most one:

`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/DOC_CLEANUP_AUDIT_PACKET.md`

---

## 5. Output Schema

Your return packet must contain:

1. status: `completed`, `partial`, `blocked`, or `aborted`
2. files read
3. files written
4. exact docs recommended for `keep`, `supersede`, `scratch`, or `archive_only`
5. open risks
6. controller recommendation

---

## 6. Hard Rules

- Do not use thread memory over repo files.
- Do not promote staging to canon.
- Do not change doctrine ranking.
- Do not smooth open items into closure.
- Do not edit files outside the allowed scope.

---

## 7. Stop Rules

Stop and write `blocked` if:

- the task would require changing bridge/cut doctrine
- the task would require canon or permit decisions
- current authority surfaces conflict in a way that needs controller judgment

---

## 8. Success Condition

One bounded cleanup recommendation packet that reduces repo-reading noise without changing the live doctrine stack.
