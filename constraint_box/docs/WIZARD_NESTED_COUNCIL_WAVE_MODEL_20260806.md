# The Wizard nested-council wave model (2026-08-06)

Read from `hermes-version-current/09_V4_1_LLM_COUNCIL_TOPOLOGY_CORRECTION.md`,
`packet-v4-3-current/taskcards/*`, and `WIZARD_v4_3.md`. This is the
model itself, not a paraphrase of the concept file.

## The correction that defines it

> A v4.1 Wizard run is **not** merely three labels, three
> controller-local phases, or three parent summaries.

```text
Decision Council  ->  Failure Council  ->  Follow-Up Council
     wide parallel work inside each council before the council returns
```

Each council is a **distinct LLM council/wave**. The councils run in
sequence as **write barriers**; the work inside each council is
intentionally **wide and parallel**. This is primary topology, not a
later enhancement.

## Two-level topology, stated exactly

**Level 1 — sequential council barriers**
- Decision completes before Failure starts.
- Failure **consumes** Decision.
- Follow-Up **consumes** Decision and Failure.

**Level 2 — wide intra-council fanout**
- Each council selects multiple member routes.
- Each selected member may spawn child/subchild variants.
- Child variants must produce **distinct deltas**, not copies:
  source-slice scout, falsifier, receipt audit, model/reasoning
  variant, follow-up improver, boundary review, mini-MMM salience
  check.

## The nesting ladder (four levels, each with its own boot rules)

```text
COUNCIL (wave, sequential barrier)
   └── PARENT ROUTE            e.g. decision.move_selection
         └── MEMBER / AGENT    e.g. voice.factory, lane.alternative
               └── SUBAGENT    child worker, own task card + mini-MMM
                     └── SUBSUBAGENT   narrow child check, one source
```

Instantiation surfaces are required, not optional:
`SUBAGENT_BOOT_RULES_v4_3.md`, `SUBSUBAGENT_BOOT_RULES_v4_3.md`,
`PARENT_ROUTE_TASK_CARD_SCHEMA_v4_3.md`,
`CHILD_TASK_CARD_SCHEMA_v4_3.md`, plus fill-in templates.

### Subsubagent boot order (verbatim shape)

1. inherited **positive** parent summary;
2. exact v4.3 child mini-MMM or route/member salience set;
3. child task card;
4. **one** source/check.

Its receipt fields: `status` (spawned | blocked | deferred | not_run |
superseded), `parent_unit_id`, `child_unit_id`, `agent_spec_path`,
`task_card_path`, `positive_mini_mmm_loaded_before_task`, `boot_scope`
= `inherited_positive_summary_then_child_task`, `checked`, `concluded`,
`open`, `evidence`, `parent_effect`, `proof_depth`.

And the rule that keeps the ladder honest:

> Subsubagent proof remains **parent-reported** unless the controller
> can read the raw child artifact.

> A v4.3 agent file is not enough to claim an agent ran. A run receipt
> must name the agent spec, the task card, the MMM/slice preload, the
> runtime target, and the observed output or block/defer reason.

## What a FULL run requires (the conformance bar)

From the topology correction, a run is only full v4.1/v4.3 council
conformance when it proves all of:

- dedicated parent members across the **full selected Decision member set**;
- the same across the **full selected Failure member set**;
- the same across the **full selected Follow-Up member set**;
- **5–10 accepted child/subsubagent receipts per counted parent**
  where the runtime supports children;
- **model-family matrix coverage** — Codex-native / Opus / Sonnet /
  Haiku / Gemini-style;
- **exact mini-MMM slice loading for every member**;
- **member utility receipts for every accepted member**.

## The honesty ladder for scaled-down runs

A runtime may scale down **only by labelling the result honestly**:

| Label | Meaning |
|---|---|
| `SMOKE_FORMAT` | formatting only; no council claim |
| `SMOKE_TOPOLOGY` | minimal topology proof; not council conformance |
| `REAL_ATTEMPT_PARTIAL` | real sequential councils attempted, wide member/child coverage incomplete |
| `REAL_ATTEMPT_FULL` | three barriers + parent/member coverage + child/subchild coverage + validator/scoring |

The recorded precedent: run `runs/20260504-155235/` proved only that
Decision, Failure and Follow-Up parent routes ran in sequence with
correct consumption — so its `PASS` was withdrawn as **too narrow**. It
was a pass for a sequential-parent smoke harness, not for council
conformance.

## Output rule

User-facing output reduces cognitive load — decision and next move
first — but **route truth cannot disappear**. The proof strip or footer
must still state whether the run was full wide-council coverage,
partial sequential coverage, parent-reported child coverage, or
blocked/deferred/not-run for wide child obligations.

## Where the measured envelope meets the topology

`SUBSUBAGENT_SCALING_RUNBOOK_v1.md` supplies the physical limits for
level 2 and level 3 fanout: safe default 8 parents x 12 Sonnet-high
children at concurrency 4 per parent; fast scout 8 x 8 Haiku with
`stop-after-completed 4` and `global-max-active 8`; 8 x 16 Haiku at
concurrency 8 is past the stable child-start envelope. The count law
(only completed receipts count) is what makes "5–10 accepted child
receipts per counted parent" a measurable obligation rather than an
aspiration.

## What CB owes this model

CB does not run councils and does not choose wave shapes. CB consumes
the receipts and enforces four things the model already states:

1. the **count law** — completed receipts only;
2. **proof_depth** — parent-reported is not artifact-verified;
3. **described vs runnable** — an agent file is not a run;
4. the **honesty ladder** — a `SMOKE_TOPOLOGY` run may never be
   reported as council conformance.

## Still unread

`agents/parents/*`, `agents/managers/*`, `agents/wizard-loop/*`,
`agents/voices/*`, `agents/auditors/*`, the task-card schemas
themselves, `mmm/FULL_MMM_v4_3.md` and the mini-MMM registry, the
remaining ~700 lines of `WIZARD_v4_3.md`, and the v4.2 packet.
