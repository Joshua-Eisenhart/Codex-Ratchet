# Wizard v4.3 — read from the actual packet (2026-08-06, corrected)

**Correction of record.** An earlier version of this note was written
from `wizard/09-universal-three-council-model.md` (a v3.5-era concept
file) plus the v4.3 read-first. That is not the Wizard. The read-first
gives an explicit boot order and the runnable runtime is
`packet-v4-3-current/WIZARD_v4_3.md` — 1,014 lines, marked
`authority_status: canonical-runtime`, which states outright: "This is
the runnable shared Wizard v4.3 runtime file. It is not a summary."
This note is written from that file.

## What v4.3 is

A **dual-processing runtime**: it processes the immediate user prompt
and the broader context/strategy state at the same time. Its own stated
goal — "not more orchestration… better decisions, stronger failure
checks, and dense human-readable answers."

Authority order: current user request is highest; the packet defines
Wizard behavior *beneath* the active environment and repository
instructions.

## The Route-Truth Field Contract (this is the load-bearing part)

Every visible route, council member, child worker, tool call, follow-up
scout, or adapter handoff resolves to five explicit fields:

| Field | Values |
|---|---|
| `action_class` | controller_local, tool_run, spawn_worker, spawn_subagent, enqueue_runner, blocked, deferred, not_run, superseded |
| `execution_claim_state` | future_choice, prechecked, completed, partial, blocked, deferred, not_run, superseded |
| `proof_depth` | controller_local, parent_reported, controller_visible, artifact_verified, test_passed |
| `receipt` | the file/tool/worker/model output proving the route claim, or the explicit block/defer reason |
| `evidence_boundary` | what the receipt proves **and what it does not prove** |

And the discipline stated flatly:

> A route not run stays `not_run`; a proposed follow-up is not a
> completed branch; a parent-reported child is not raw child proof; a
> validator selftest is not a task run.

**`proof_depth` is finer than anything CB currently has.** CB
distinguishes recomputed-from-bytes vs producer-asserted. The Wizard
already separates *parent_reported* from *controller_visible* from
*artifact_verified* from *test_passed* — four grades of witness. CB's
receipt grammar should adopt this ladder rather than invent one.

## Described role vs runnable route

> A role named only in this runtime file is a **described role**. It
> becomes a **runnable route** only when a current task card names an
> agent spec and the run returns a receipt with MMM/slice preload,
> proof depth, output, and evidence boundary.

This is `HANDOFF_DESCRIBED_BUT_ABSENT` stated years before CB's SDG
fixture named it — and it is the exact defect both agents committed on
this project. The Wizard had the rule already.

## The nine parent routes (not "three councils" loosely)

**Decision Council**
- `decision.context_strategy` — children voice.strategy, voice.systems, voice.hume, voice.feynman. Outputs prompt intent, larger context, strategy state to carry forward, **local-overoptimization risk**, what must not be lost in synthesis.
- `decision.move_selection` — voice.factory, voice.orwell, voice.hume, lane.direct, lane.alternative. Outputs selected move, why now, **rejected alternatives**, operating boundary.
- `decision.evidence_boundary` — voice.hume, voice.popper, voice.feynman, guard.receipt_audit. Outputs evidence boundary, falsifier, observable pass/fail check, receipt truth boundary.

**Failure Council**
- `failure.premortem` — skill.premortem + hume/factory/systems. Outputs most likely failure, most dangerous failure, hidden assumption, early warnings, revised plan, **novel findings beyond user-named issues**. Explicitly must not produce reports, HTML, transcripts, docs, browser actions or web pages.
- `failure.falsifier` — popper, pushback, feynman, guard.boundary_check. Outputs killed/open/survived, overclaim correction, boundary failure, minimal fix.
- `failure.loophole_auditor` — runs the confidence loop: *"Are you 100% confident in this strategy? If not, find all possible loopholes, suggest proper fixes and run this loop until you are factually 100% confident."* With the interpretation fixed: 100% means **no known unresolved loophole under the declared evidence standard, not omniscience.**

**Follow-Up Council**
- `follow_up.next_move_selector` — outputs next-move category, why, what context it preserves, **what kind of follow-up would be wasteful**.
- `follow_up.lane_builder` — lane.direct, lane.reframe, lane.back, lane.wildcard, lane.all_of_the_above. Outputs lane set, payoff, use condition, stop/block condition.
- `follow_up.compile_gate` — target, action, owner, success check, stop condition, artifact surface, status.

Councils are strictly sequenced: parallelize only *inside* the current
council; a later council cannot start until the previous accepts or is
explicitly blocked.

## Management parents (required, non-voting)

- `manager.run_controller` — enforces council sequence and wave boundaries.
- `manager.child_health` — liveness, timeouts, reroutes, thread pressure, with **concrete intervention verbs**: kill, demote, reroute, shrink, override, block_full, accept_with_reason, no_intervention_needed.
- `manager.route_truth` — prevents fake FULL, mixed-run receipts, missing MMM loads, controller-only voices.
- `manager.output_compiler` — receipts into human output; removes logs unless diagnostics requested.
- `manager.strategy_memory` — carries prompt intent, standing context, strategy state, risks, killed assumptions, follow-up rationale across loops. Session scratchpad, **not** a long-term archive.

## The Sim/Proof/Source-Lock overlay

Active when the task touches Codex Ratchet sims, proofs, terrain/operator
math, workflow-stage formulas, result claims, or Claude-derived updates.
It adds no fourth council; it adds child/skill obligations inside the
existing routes. Rule 1 is directly relevant to this session:

> External Claude material is source material only. Use
> `skill.claude_pattern_intake` to port mechanics; reject
> Claude-as-authority, unreceipted route truth, and completion language
> without a claim gate.

## Instantiation surfaces that must exist for a route to be real

`agents/AGENTS_MANIFEST_v4_3.md`; `agents/parents/*`; `agents/managers/*`;
`agents/wizard-loop/*` (route truth, evidence mapping, scouting,
sequencing, compiling); `agents/voices/*`; `agents/auditors/*`
(collapse/shared-premise audits); `taskcards/TASKCARDS_MANIFEST_v4_3.md`
plus schemas and templates.

**`agents/auditors/` — collapse and shared-premise audits — is the
structural anti-conservatism organ.** It is the thing that detects the
v3 failure mode (members converging on one premise) as a run property
rather than as a hope.

## What CB should take, and what it must not

Take: the route-truth five-field contract; the `proof_depth` ladder;
described-role vs runnable-route; the intervention verb set; the
described/runnable distinction applied to CB's own receipts.

Do not take: council authority. The Wizard proposes and compiles;
CB admits. And CB must not prime the exploration lane with its own
vocabulary — the mini-MMM-per-member design exists precisely so members
do not share one ontology.

## Still unread in this pass (named, not glossed)

`mmm/FULL_MMM_v4_3.md` and the mini-MMM registry, `agents/` specs,
`taskcards/`, `skills/`, `adapters/`, `schemas/`, and the remaining
~700 lines of `WIZARD_v4_3.md`. Also unread: the Hermes and Claude
runtime adaptations, and `SUBSUBAGENT_SCALING_RUNBOOK_v1.md`.
