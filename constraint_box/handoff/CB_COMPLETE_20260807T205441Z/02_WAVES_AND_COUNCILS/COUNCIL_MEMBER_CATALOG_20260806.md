# COUNCIL MEMBER CATALOG — every possible member, by kind (2026-08-06)

Owner requirement: enumerate all possible council members — skills,
formal agents, MMMs — so the tools are structured together and
**actually run**. Plus auditing and management that keeps things
working.

Owner boundary, load-bearing: oversight systems **are not overseeing
the content** — they oversee the machinery, whether agents are stuck
or processes broken.

## FIVE MEMBER KINDS

A council member is not necessarily an LLM. Members differ by
**determinism class**, and that difference is what lets a council mix
judgment with proof.

| Kind | What it is | Can drift? | Loaded with |
|---|---|---|---|
| `voice` | LLM primed with pre-language salience | yes | its own MMM |
| `formal_agent` | LLM agent with spec + task card | yes | MMM slice + task card |
| `skill` | packaged procedure, may wrap either | partly | skill definition |
| `deterministic` | tool whose output is a function of its input | **no** | nothing |
| `sim_lane` | external engine under a capability adapter | no, but environment-bound | lock/profile |

**Deterministic members are the anchor.** A council containing z3, a
rustworkx cycle check, and a sympy recompute alongside three voices
has members that cannot be talked into anything.

## KIND 1 — VOICES (9)

`hume` evidence/uncertainty · `zhuangzi` alternate readings, exclusion
condition (**and prompt generator for other LLMs**) · `feynman`
mechanism/observable/pass-fail · `orwell` plain wording, anti-fog ·
`popper` falsifier, killed/open/survived · `pushback` overclaim
boundary · `factory` bottleneck/queue/leverage · `strategy`
sequence/retreat · `systems` feedback/second-order.

Source: `~/Codex-Ratchet/.claude/agents/voice-*.md`, packet copy at
`wizard/packet-v4-3-current/agents/voices/`.

## KIND 2 — FORMAL AGENTS

**Parent routes (9)** decision.{context_strategy, move_selection,
evidence_boundary}, failure.{premortem, falsifier, loophole_auditor},
follow_up.{next_move_selector, lane_builder, compile_gate}.

**Wizard-loop (9)** evidence-mapper, falsifier-agent, premortem-agent,
prompt-packetizer, route-sequencer, route-truth-agent, scope-keeper,
scout-runner, selector-compiler.

**Managers (5, non-voting — machinery only)** run_controller,
child_health, route_truth, output_compiler, strategy_memory.

**Auditors (1)** council-collapse-auditor.

**Project agents (13)** crossover-proof-runner, fabrication-auditor,
fresh-audit-runner, jax-audit-lane-runner, jax-sim-runner,
julia-carrier-builder, julia-sim-runner, process-stage-gate-steward,
pytorch-sim-runner, repo-doc-archaeologist, sim-contract-gatekeeper,
smt-proof-engineer, council-collapse-auditor.

## KIND 3 — SKILLS

**Codex (44)** — 5 Wizard generations; 5 council-member skills
(factory-handoff, follow-up-selector, loophole-auditor, strategy-loop,
systems-strategy); claude-bridge + claude-pattern-intake; sim lane
(jax-sim, julia-sim, pytorch-sim, three-engine-sim, lego-sim-classifier,
sim-stack-maintenance, sim-audit-spine, terrain-operator-math-lock);
thread control (dispatch-controller, run-monitor, closeout-auditor,
automation-controller, primary-runtime, safe-run-maintenance,
env-agent-coordination, deep-stack-stress, tool-status-auditor);
memory (a1-from-a2-distillation, a2-a1-memory-admission-guard,
a2-brain-refresh, ratchet-a2-a1, brain-delta-consolidation, chronicle,
bounded-hermes-intake, closeout-result-ingest); research (refinery-
launcher, return-ingest, pro-return-instant-audit,
karpathy-bounded-improve, skill-agent-upgrader, brev-cli, premortem).

**Claude Code (7)** aligned-mmm, claude-wizard-loop-engineering,
codebase-memory, codex-first, brev-cli, govuk-style, test-skill.

**Packet-local** claude-bridge, claude-pattern-intake, premortem,
sim-audit-spine, source-math-lock, council-members/{collapse-auditor,
factory-handoff, follow-up-selector, loophole-auditor, strategy-loop,
systems-strategy}.

## KIND 4 — DETERMINISTIC MEMBERS (the new part)

These sit **in** councils, not beside them. Each is measured.

| Member | Council contribution | Evidence |
|---|---|---|
| `z3` | bounded satisfiability with erased control | 21 call sites, 16 test files |
| `cvc5` | independent second decider; AGREE or UNRESOLVED | triple-decider verified live |
| `enumeration` | third decider, no solver | part of crosscheck registry |
| `sympy` | exact symbolic recompute | 25 call sites |
| `rustworkx` | cycle, order, reachability verdicts | 0.61 ms on the real 5-job DAG; cycle canary BLOCKED |
| `maude` | rewriting-logic transitions | 18 call sites |
| `portion` | admissible-range membership; unfalsifiable-box detection | refused D<0 and CPTP modulus>1 |
| `msgspec` | strict receipt decode, typed errors | 0.06 ms; 3 canaries refused |
| `pygit2` | lease tree custody | identical tree id, 65x faster |
| `sqlite3` (stdlib) | exact receipt lookup | 0.017 ms point lookup; 54,055x context reduction |
| `rfc8785` | canonical bytes before hashing | frozen spec |
| `input_diversity_gate` | root-input dissimilarity across a wave | COLLAPSED/DIVERSE self-test |
| `strict_receipt_consumer` | recompute from bytes | caught 15 drifted hashes |
| `member_coverage_auditor` | machinery coverage/staleness/liveness | self-test 2/2 |

## KIND 5 — SIM LANES

`jax`, `julia`, `pytorch`, `qutip/numpy reference`, plus
diffrax/quimb/cotengra/pysindy/pydmd/pykoopman/pymdp under the
external capability adapters. Environment-bound, lock-pinned,
**outside CB's runtime closure** — reached through capability
dispatch, never imported by the gate.

## THE MMM LAYER

Every non-deterministic member is primed with **its own** MMM slice.
Available: the seven CB/packet MMM packs (claimgate, cr-ratchet,
lev-os, constraint-programming, smt, nominalist, constraint-box),
plus the v4.3 `mmm/FULL_MMM_v4_3.md` and the member mini-MMM registry.
Rule: many MMMs, genuinely diverse from each other, coupled to the
operationalist/nominalist/sentimentalist bias. Deterministic members
take no MMM — there is nothing to bias.

## THE OVERSIGHT LAYER — machinery, never content

Built: `member_coverage_auditor.py`, stdlib only. It answers exactly
three questions and refuses the fourth:

- **COVERAGE** — which declared members have never appeared in a receipt
- **STALENESS** — which have not run inside the declared window
- **LIVENESS** — which routes started and never returned (**stuck**)

Its claim ceiling, stamped in every receipt: *machinery coverage,
staleness and liveness only; says nothing about output content,
correctness or quality.* A member that runs and returns garbage is
COVERED here. Judging the garbage is a different gate.

Self-test: a registry of four members against one receipt correctly
reported `maude` NEVER_RUN and `voice-zhuangzi` STUCK (spawned, never
returned).

This is the same separation the Wizard already draws with
`manager.child_health`, whose verbs are all machinery — kill, demote,
reroute, shrink, override, block_full, accept_with_reason,
no_intervention_needed — and none of them content.

## WHAT THIS MAKES POSSIBLE

A declared registry plus a coverage auditor turns "all the skills are
actually used" from an intention into a **measurement**. Any skill,
agent, voice or tool that never appears in a receipt is visible as
NEVER_RUN; anything that stops appearing goes STALE; anything that
starts and never returns is STUCK. The integration system becomes
checkable rather than aspirational, and the check itself never touches
what the members said.
