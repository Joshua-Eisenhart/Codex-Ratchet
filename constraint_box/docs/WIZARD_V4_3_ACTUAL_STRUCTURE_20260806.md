# WIZARD v4.3 — THE ACTUAL STRUCTURE

Enumerated from `agents/AGENTS_MANIFEST_v4_3.md` (33 agent specs) and
the required-children lists in `WIZARD_v4_3.md`.

## The shape

```
                        RUN
                         |
   +---------------------+---------------------+
   |            MANAGERS (5, no vote, span all waves)         |
   |  run_controller · child_health · route_truth ·           |
   |  output_compiler · strategy_memory                       |
   |            AUDITOR (1): council-collapse-auditor         |
   +---------------------+---------------------+
                         |
   WAVE 1 ===== DECISION COUNCIL ===== (barrier: must accept or block)
     |                    |                        |
   decision.              decision.                decision.
   context_strategy       move_selection           evidence_boundary
     |                    |                        |
     +- voice.strategy    +- voice.factory         +- voice.hume
     +- voice.systems     +- voice.orwell          +- voice.popper
     +- voice.hume        +- voice.hume            +- voice.feynman
     +- voice.feynman     +- lane.direct           +- guard.receipt_audit
                          +- lane.alternative
                         |
                    [consumes Decision]
                         |
   WAVE 2 ===== FAILURE COUNCIL ===== (barrier)
     |                    |                        |
   failure.premortem    failure.falsifier        failure.loophole_auditor
     |                    |                        |
     +- skill.premortem   +- voice.popper          +- skill.loophole_auditor
     +- voice.hume        +- voice.pushback        +- voice.strategy
     +- voice.factory     +- voice.feynman         +- voice.systems
     +- voice.systems     +- guard.boundary_check  +- voice.hume
                         |
              [consumes Decision + Failure]
                         |
   WAVE 3 ===== FOLLOW-UP COUNCIL ===== (barrier)
     |                    |                        |
   follow_up.           follow_up.               follow_up.
   next_move_selector   lane_builder             compile_gate
     |                    |                        |
     +- voice.strategy    +- lane.direct           +- compile_gate.target
     +- voice.factory     +- lane.reframe          +- .action
     +- voice.orwell      +- lane.back             +- .owner
     +- voice.hume        +- lane.wildcard         +- .success_check
                          +- lane.all_of_the_above +- .stop_condition
                                                   +- .artifact_surface
                                                   +- .status
```

**Inside each parent route**, every member may fan out further:

```
PARENT ROUTE -> MEMBER/AGENT -> SUBAGENT -> SUBSUBAGENT
                                  |            |
                          own task card   inherited positive summary
                          + mini-MMM      + child mini-MMM slice
                                          + child task card
                                          + ONE source/check
```

Conformance target: **5–10 accepted child/subsubagent receipts per
counted parent**, across a **Codex-native / Opus / Sonnet / Haiku /
Gemini** model-family matrix.

## The 33 agent specs, by family

**Parents (9)** — three per council, listed above.

**Voices (9)** — `factory`, `feynman`, `hume`, `orwell`, `popper`,
`pushback`, `strategy`, `systems`, `zhuangzi`.
Seeded from `Codex-Ratchet/.claude/agents/voice-*.md`, scrubbed so
project-specific engine policy stays adapter-local.

**Wizard-loop (9)** — `evidence-mapper`, `falsifier-agent`,
`premortem-agent`, `prompt-packetizer`, `route-sequencer`,
`route-truth-agent`, `scope-keeper`, `scout-runner`,
`selector-compiler`. Seeded from `~/.claude/agents/wizard/`.

**Managers (5)** — `run_controller` (enforces council sequence and wave
boundaries), `child_health` (liveness, timeouts, reroutes, thread
pressure; verbs: kill, demote, reroute, shrink, override, block_full,
accept_with_reason, no_intervention_needed), `route_truth` (prevents
fake FULL, mixed-run receipts, missing MMM loads, controller-only
voices), `output_compiler` (receipts to human output, strips logs),
`strategy_memory` (prompt intent, standing context, killed
assumptions, follow-up rationale across loops — session scratchpad,
not archive).

**Auditors (1)** — `council-collapse-auditor`.

**Templates** — `agents/templates/AGENT_SPEC_v4_3.md`.

## Voice load, counted from the required-children lists

| Voice | Required in |
|---|---:|
| hume | **6** routes (all three councils) |
| strategy | 3 |
| systems | 3 |
| feynman | 3 |
| factory | 3 |
| orwell | 2 |
| popper | 2 |
| pushback | 1 |
| **zhuangzi** | **0** |

**Finding worth checking:** `voice-zhuangzi` — live readings, alternate
interpretations, exclusion condition — has an agent spec but appears in
none of the nine required-children lists. It is the alternate-framing
voice, and it is the one voice with no required seat. Given the v3
failure was *loss of exploration at the gates*, a divergence voice that
is specified but never required is exactly the kind of gap that
reintroduces conservatism. (Caveat: I read the required-children lists
for the nine routes; selected/optional member sets may appear in the
~700 unread lines of `WIZARD_v4_3.md`.)

## Lanes and guards (referenced as children, not in the agent manifest)

Lanes: `direct`, `alternative`, `reframe`, `back`, `wildcard`,
`all_of_the_above`. Guards: `receipt_audit`, `boundary_check`.
Skills: `premortem`, `loophole_auditor` (packet-local skills exist at
`skills/premortem/SKILL.md` and
`skills/council-members/loophole-auditor/`).

## The rule that governs all of it

> An agent file is not a run receipt. A route counts as run only when
> the current run receipt names the agent spec, task card, MMM/slice
> preload, runtime target, output, and proof depth.

Required taskcard surfaces: `TASKCARDS_MANIFEST_v4_3.md`,
`PARENT_ROUTE_TASK_CARD_SCHEMA_v4_3.md`,
`CHILD_TASK_CARD_SCHEMA_v4_3.md`, `SUBAGENT_BOOT_RULES_v4_3.md`,
`SUBSUBAGENT_BOOT_RULES_v4_3.md`.
