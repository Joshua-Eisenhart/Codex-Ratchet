# The Wizard — read, and why CB needs it (2026-08-06)

Read from `~/wiki/wizard/`, not summarized from memory. The owner's
note that "this part of claimgate seemed often lost" is correct, and
the reason it matters is specific: **the Wizard is the exploration
engine, and CB is only the hard wall.** Without it CB reproduces the
v3 failure — gates with no exploration at them.

Current packet: `~/wiki/wizard/packet-v4-3-current/` (v4.3, 2026-06-13),
with runtime adaptations under `hermes-version-current/` and
`claude-version-current/`. Do not boot from v4.2 as law.

## What the Wizard actually is

A **general bounded-work compiler**, explicitly not Codex-specific:

1. councils create judgment, critique, and options;
2. receipts prove what actually ran;
3. MMMs and mini-MMMs shape salience;
4. compile gates decide whether an output is ready for the domain.

### Three sequential councils (waves)

| Wave | Council | Purpose |
|---|---|---|
| 1 | Decision | choose the best bounded move now **while preserving live alternatives** |
| 2 | Failure | kill, quarantine, harden, or pass the selected move |
| 3 | Follow-Up | **generate divergent next prompts** and compile the useful ones into bounded work options |

Parallelism happens *inside* a wave. The waves are sequential barriers.

### Members are salience roles, not one kind of thing

- **Voices:** Hume (evidence/uncertainty), Zhuangzi (live readings,
  alternate interpretations, exclusion condition), Feynman (mechanism,
  observable, pass/fail), Orwell (plain wording, anti-fog), Popper
  (falsifier; killed/open/survived), Pushback (overclaim boundary),
  Factory (bottleneck, queue, leverage), Strategy (sequence, retreat
  condition), Systems (feedback loop, second-order effect).
- **Six Hats:** Blue process, White facts, Red gut alarm, Black risk,
  Yellow upside, Green alternatives.
- **Failure lenses:** premortem, postmortem, security/audit, expert
  failure lens.
- **Expert lenses:** likely critique, outside evaluator, domain
  specialist ("not authority theater").
- **Follow-up lanes:** Direct, Alternative, Reframe, Back, **Wildcard**
  (off-axis probe with a concrete payoff).
- **Compositions:** All-A Build, All-B Divergence, All-C Closeout, Max
  Assembly — explicitly "not a quota to run everything".
- **Guards:** hygiene, security, receipt audit, compile gate.
- **Manager:** resource manager / rerouter — schedules, shrinks,
  reroutes, stops waiting; **not a council member, has no vote.**

### Mini-MMM per member

`family / job / phraselets / question_stems / return_shape / avoid /
compile_relevance`. A role-local salience profile, explicitly "not a
rule list."

## The two rules that make it CB-compatible

**v4.3 minimum run truth.** A claim must name its support level:
`controller_local`, `tool_run`, `spawn_worker` / `spawn_subagent`,
`enqueue_runner`, or `blocked` / `deferred` / `not_run` / `superseded`.
And the line that matters most:

> A council is not a mood or a summary. It needs receipts from the
> runtime's actual worker/model routes, or it is controller-local
> discipline.

**Compile gate primacy:**

> Council agreement, salience lift, and receipts do not imply readiness
> unless the relevant compile gate passes.

Both are the same doctrine CB arrived at independently: a producer's
own verdict is not evidence, and consensus is evidence about the
models, not about the world.

## Why this is the missing half of CB

The v3 failure was not absent gates — deterministic gating existed
(boots; threads a0, a1, b, sim). The failure was that models absorbed
the gate ontology and stopped exploring. The Wizard fixes that
**structurally rather than by hope**:

- **Per-member mini-MMMs mean members do not share one ontology.**
  This is the anti-collapse mechanism. A single MMM primed into every
  agent is exactly how the basin forms.
- **Wave 3 makes divergence a required stage**, with Reframe and
  Wildcard lanes that exist to leave the current framing — the thing
  no single primed model would volunteer.
- **Wave 1 preserves live alternatives by definition**, so choosing a
  move does not destroy the antichain.
- **Zhuangzi and Green Hat are structural roles**, not moods: alternate
  readings and lateral options get produced because a seat exists for
  them, not because a model felt creative.

This addresses the owner's standing problem directly — the model is
probably right and the ORDER is often wrong, and no primed LLM would
explore alternate orders, so he drove them by hand. **Order-space
exploration is exactly what Wave 3 lanes are for.**

## The clean division of labour

| Layer | System | Owns |
|---|---|---|
| Exploration / soft side | Wizard councils, heterogeneous models, per-member mini-MMMs | proposals, critiques, rivals, reframes, wildcards, scores |
| Compile gate | Wizard compile gates (universal + adapter domain profiles) | is this output bounded enough to act on |
| Hard wall | ConstraintBox | admit / park / block / release against named oracle evidence |

CB must not absorb the Wizard, and the Wizard must not promote.
CB's MMM biases the **controlled lane only**; priming explorers with
CB's vocabulary is the v3 collapse.

## Status and next step

The Wizard exists as doctrine and packets in the wiki, with runtime
adaptations for Hermes and Claude Code, conformance harnesses,
schemas, and run logs. It is `adapter_partial` for CB — there is no
CB-side adapter. Building one means supplying, per the packet's own
runtime-independence contract: how members become workers, how worker
receipts are proven, how child hierarchy is represented, how liveness
and reroute are managed, and how output is rendered without logs.

Nothing above is new design. It is recovered, cited, and now sitting
inside the repo instead of only in the vault.
