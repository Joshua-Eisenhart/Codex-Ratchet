# Read this first

Constraint Box is a proposed standalone control plane from the ClaimGate lineage. It accepts untrusted claims, selects controller-owned checks, records bounded evidence, and refuses to turn a local result into scientific truth. ClaimGate began as a practical barrier against LLM-generated code that claims more than it does.

This directory is not promoted. `promotion_allowed: false`. Its unit-suite status is only `passes local rerun` on one host. It is not `canonical by process`.

The open defect register is [`../PROVENANCE.md`](../PROVENANCE.md). It is the authority on what is broken, unmeasured, duplicated, or awaiting an owner decision.

## This document set

- `00_READ_FIRST.md`: orientation, claim ceiling, and reading order.
- `01_THEORY.md`: why producer-visible receipt checks fail and what that implies.
- `02_ARCHITECTURE.md`: built modules, claim flow, exit codes, and live gaps.
- `03_PROCESSES.md`: commands run on this host and procedures for checks and fixtures.
- `04_FOR_LLM_AGENTS.md`: testable rules for agents working in this tree.
- `05_FINDING_SLOP.md`: the repo-root slop scanner, regression, CI report, and limits.

Read them in order. Keep `PROVENANCE.md` open while changing code.

## The other files in this directory

Six pre-existing files are the inherited 2026-07-25 handoff-pack documentation:

- `01_ARCHITECTURE.md`
- `02_SIM_SETUP_TIERS.md`
- `03_CLAIMGATE_FOUNDATION_FROM_MANIFOLD.md`
- `04_INSTALL_BOOT_MAINTENANCE.md`
- `05_CR_MANIFOLD_FIXTURES.md`
- `06_LIMITS_AND_DEFERRED.md`

Current source and tests still support their broad separation of the control plane, estate, and adapters; strict intake; controller-owned dispatch; finite solvers; branch retention; evidence translation; S1-S4 as installation tiers; and proposal-only promotion ceiling.

This lane did not recheck their historical package receipts, installed-version claims, cloud state, lock freshness, suggested installation steps, archive contents, or proposed M0-M8 completion. Some inherited statements overstate current wiring: applicability is reachable but gates nothing, and the retained ledger head is not an independent trust root.

Trust this numbered set and `PROVENANCE.md` for current behavior and defects. Use the inherited set for 2026-07-25 design context, then remeasure before relying on a claim.
