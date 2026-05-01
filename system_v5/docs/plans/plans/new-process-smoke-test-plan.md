# New Process Smoke-Test Plan

Status: bounded controller-process test plan
Date: 2026-04-20
Goal: make the new multi-part process reliable enough that it stops “working sometimes” by pressure-testing the controller side before more sim-stage widening.

Architecture: treat the process as a stack of separate surfaces — selector, closure/writeback, reporting, worker parity, and wiki reconciliation. Test them in that order. Do not treat a later successful run as proof that earlier control surfaces were honest.

Tech stack: Hermes controller surfaces, repo docs, Python controller scripts, Telegram entrypoint, wiki automation contract.

---

## Test 1: Live-surface selector test

**Objective:** verify the controller really chooses work from the declared live control surfaces rather than only from fallback batch rotation.

**Files:**
- Read: `system_v4/probes/live_queue_controller.py`
- Read: `system_v5/docs/plans/plans/on-demand-telegram-runner.md`
- Read: `system_v5/docs/plans/plans/controller-harness-integration-status.md`

**Command:**
- inspect `audit_green()` and `choose_batch()` behavior under current red audits

**Pass condition:**
- controller choice is demonstrably tied to the declared live surfaces

**Fail signal:**
- controller keeps selecting fallback batch logic regardless of live-surface state

---

## Test 2: Closure writeback path test

**Objective:** verify maintenance closure writes to the live `system_v5/docs/plans/plans/...` surfaces rather than stale paths.

**Files:**
- Read: `system_v4/probes/maintenance_closure.py`
- Read: `system_v5/docs/plans/plans/local-launch-checklist-bounded-geometry-first-run.md`
- Read: `system_v5/docs/plans/plans/controller-harness-integration-status.md`

**Command:**
- inspect closure target paths and compare them to the live docs paths

**Pass condition:**
- closure target paths match the live control surfaces

**Fail signal:**
- closure still points at dead/stale locations like `system_v5/new docs/...`

---

## Test 3: Heartbeat truth test

**Objective:** verify run reporting tracks a real worker/process state rather than only a launched controller pid.

**Files:**
- Read: `telegram_bot.py`
- Read: `system_v5/docs/plans/plans/on-demand-telegram-runner.md`
- Read: `system_v5/docs/plans/plans/controller_maintenance_checklist.md`

**Command:**
- inspect live run launch path and compare it with the documented heartbeat truth contract

**Pass condition:**
- reported run state is grounded in a checked live worker/process state

**Fail signal:**
- launch ack can say “run started” without a later real worker/heartbeat truth path

---

## Test 4: Worker parity test

**Objective:** verify Codex has a bounded-launch contract parallel to the Claude launch-ready contract.

**Files:**
- Read: `system_v5/docs/plans/plans/launch-ready-claude-worker-orchestration-spec.md`
- Read: `system_v5/docs/plans/plans/subagent-wiki-harness-integration-contract.md`
- Read: `system_v5/docs/plans/plans/skills-and-tooling-controller-stack.md`

**Pass condition:**
- Codex worker launch/read-order/stop-rule/reconciliation contract exists and matches live machine facts

**Fail signal:**
- Codex is installed but only implied, not governed by a launch-ready contract

---

## Test 5: Wiki shared-surface isolation test

**Objective:** verify concept-local worker edits and Hermes shared-surface reconciliation stay separated.

**Files:**
- Read: `system_v5/docs/plans/plans/wiki-automation-run-contract.md`
- Read: `system_v5/docs/plans/plans/wiki-automation-claude-terminal-orchestration.md`
- Read: `~/wiki/hermes-current/read-first.md`

**Pass condition:**
- concept-local work and shared-route reconciliation are explicitly separated and operationally usable

**Fail signal:**
- worker packets are still allowed to blur concept-local edits with shared-route reconciliation

---

## Recommended execution order
1. Test 1 — selector
2. Test 2 — closure/writeback
3. Test 3 — heartbeat truth
4. Test 4 — worker parity
5. Test 5 — wiki isolation

## Stop rule
If Tests 1–3 fail, do not treat any later “successful run” as proof that the new process works. Fix the control plane first.

## Success condition
The new process is meaningfully more reliable only when:
- selector is live-surface-grounded
- closure writes to live surfaces
- reporting is worker-truth-grounded
- Codex parity is explicit
- wiki reconciliation is separated from worker-local edits
