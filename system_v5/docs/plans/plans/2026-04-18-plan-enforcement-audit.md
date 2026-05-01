# 2026-04-18 Plan Enforcement Audit

Status: SAVED ENFORCEMENT AUDIT

Goal: explain why the user's hard stage-gated plan keeps getting softened, identify the exact repo/wiki surfaces that support it versus blur it, and state the smallest set of enforcement fixes needed so LLMs follow process instead of default planning instincts.

## The Hard Stage Rule

The user's plan, in its simplest enforced form:

1. tool sims
2. tool-integration sims
3. all legos, one by one, until the lego stage is complete across the registry
4. only then couplings
5. only after coupling/coexistence/topology/emergence evidence, bridge or axis-level claims

This is a hard gate, not a tendency.

## What Already Supports The Rule

- tools first:
  - `/Users/joshuaeisenhart/wiki/hermes-current/hermes-memory-offload.md`
  - `system_v5/docs/plans/lanes.md`
- tool capability + tool integration + lego coverage are foundational:
  - `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/axis_hypothesis_and_lego_authority.md`
- one-row-per-lego exhaustive registry:
  - `system_v5/docs/17_actual_lego_registry.md`
- pairwise/coupling is later than local lego:
  - `system_v5/docs/plans/plans/sim_backlog_matrix.md`
  - `/Users/joshuaeisenhart/wiki/harness/06_coupling_program_order.md`

## Where The Rule Gets Softened

### 1. The phrasing keeps saying "after local legos are real"

That is weaker than "after the lego stage is complete."

Examples:
- `system_v5/docs/plans/plans/sim_backlog_matrix.md`
- `/Users/joshuaeisenhart/wiki/hermes-current/hermes-memory-offload.md`
- `/Users/joshuaeisenhart/wiki/harness/06_coupling_program_order.md`

Why this matters:
- models interpret "local legos are real" as permission to start pairwise work once some local anchors exist
- the user's actual rule is stricter: finish the lego stage, then couplings

### 2. The grouped ledger rewards successor thinking too early

`system_v5/docs/16_lego_build_catalog.md` currently includes:
- `Best Next Successor`
- `ready_for_pairwise`
- `safe_for_coexistence`
- queue rows targeting `coexistence`

Why this matters:
- even if the doctrine says lego-first, the working ledger reads like per-row successor advancement is already authorized
- that trains planners and LLMs to move upward as soon as a row looks locally good

### 3. The saved plan packet I wrote still softened the user's rule

`system_v5/docs/plans/plans/2026-04-18-sim-estate-audit-and-plan.md` framed Phase 3 as successor work off earned locals instead of preserving the harder all-legos-first gate.

### 4. The boot/runtime surfaces do not state the exhaustive lego gate bluntly enough

Examples:
- `CLAUDE.md`
- `system_v5/docs/plans/lanes.md`
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/read-first.md`
- `/Users/joshuaeisenhart/wiki/harness/06_coupling_program_order.md`

Why this matters:
- these are the surfaces LLMs or operators load first
- if they do not explicitly say "no couplings until the lego registry stage is complete," models default to partial-progress advancement

### 5. Operational launch and queue surfaces still leave room for early successor work

Examples:
- `system_v5/docs/plans/plans/launch-ready-automated-run-manifest.md`
- `system_v5/docs/plans/plans/corrected-bounded-automation-plan.md`
- `system_v5/ops/queue_default.txt`

Why this matters:
- the scheduler can still pull mixed-stage work
- that reintroduces the exact drift the user is rejecting

## Repo-Level Fixes Needed

1. Root session boot must say the hard stage order exactly.
2. The live queue must say no pairwise/coexistence queue before lego-stage completion.
3. The exhaustive registry must say it is the gate for ending the lego stage.
4. The grouped ledger must say successor columns are placeholders only, not permission.
5. Launch prompts must stop offering pairwise fallback before lego-stage completion.
6. Saved planning packets must stop translating the rule into softer multi-lane language.

## Wiki-Level Fixes Needed

These are the highest-value wiki patch points. All four were patched or explicitly routed in this pass:

- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/read-first.md`
- `/Users/joshuaeisenhart/wiki/harness/06_coupling_program_order.md`
- `/Users/joshuaeisenhart/wiki/hermes-current/hermes-memory-offload.md`
- `/Users/joshuaeisenhart/wiki/hermes-current/skills-and-agent-rules.md`

Each should say some version of:

> Tool sims first. Tool-integration sims next. Then all lego rows, one by one, until the lego stage is complete. No coupling stage before that.

## Meaning Now

The system rules are present. The real failure is that several live planning and boot surfaces still translate the hard gate into softer successor language, so LLMs keep obeying the softened version instead of the actual rule.
