# External Thread Ingest And Cleanup

**Date:** 2026-03-29  
**Purpose:** Define how this controller thread should process raw external-thread returns after they land in the repo.

---

## 1. Ingest Rules

Raw return packets are never authority by themselves.

They must be processed in this order:

1. read the boot packet
2. read the return packet
3. check whether the lane stayed in scope
4. classify the return
5. ingest only accepted parts into owner or support surfaces

---

## 2. Return Classification

Use one of these classes:

- `accepted`
  - bounded, correct, in scope
- `accepted_with_fence`
  - useful, but only if controller preserves an explicit fence
- `partial`
  - some useful work, but not a full accepted result
- `rejected`
  - out of scope, contradictory, or unsafe
- `archive_only`
  - useful as history, not for live stack use

---

## 3. Cleanup Rules

After ingest:

- move raw worker returns that are no longer active to `system_v4/thread_archive/raw_returns/`
- mark stale boot packets as superseded if they should not be reused
- do not delete useful audit history unless explicitly requested

---

## 4. Controller Discipline

- do not let external worker returns outrank local owner packets
- do not let external wording silently change doctrine
- do not let multiple external returns blur together without an explicit controller decision

---

## 5. Best Current Use

Use this workflow for:

- high-parallel audit batches
- Thread B registry checks
- stale-doc cleanup
- bounded review-only derivation passes

Do not use it to outsource final authority decisions.
