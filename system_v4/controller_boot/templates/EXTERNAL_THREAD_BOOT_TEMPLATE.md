# External Thread Boot Template

**Lane ID:** `<LANE_ID>`
**Date:** `<YYYY-MM-DD>`
**Status:** ACTIVE BOOT PACKET
**Controller:** `<controller surface>`

---

## 1. Purpose

`<one-sentence bounded task>`

---

## 2. Authority And Scope

Authority surface:

- `<authoritative packet 1>`
- `<authoritative packet 2>`

Scope:

- `<what this lane may do>`
- `<what this lane must not do>`

---

## 3. Files To Read

Required:

- `<absolute path>`
- `<absolute path>`

Optional:

- `<absolute path>`

Forbidden:

- `<absolute path or category>`

---

## 4. Deliverable

Write exactly one return packet to:

`<absolute return path>`

If you need a supporting doc, create at most one supporting file and list it in the return packet.

---

## 5. Output Schema

Your return packet must contain:

1. status: `completed`, `partial`, `blocked`, or `aborted`
2. files read
3. files written
4. core findings or deliverable summary
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
- the required repo files conflict
- the task grows beyond the bounded scope

---

## 8. Success Condition

`<what counts as done>`
