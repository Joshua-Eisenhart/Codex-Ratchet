# NESTED LLM COUNCILS — full enumeration (2026-08-06)

Every name below was read off disk. Paths given so each is checkable.

## PART 1 — THE NESTING

A council's **members are councils**. That is the whole point, and it
is what earlier notes in this directory failed to show.

```
WAVE n                                    sequential barrier; loops within
  |                                       itself and with other waves
  +-- COUNCIL A          (an LLM council)
  |     +-- MEMBER 1  ---> IS ITSELF AN LLM COUNCIL
  |     |     +-- sub-member a  -> SKILL  or FORMAL AGENT   <- deterministic floor
  |     |     +-- sub-member b  -> SKILL  or FORMAL AGENT
  |     |     +-- sub-member c  -> SKILL  or FORMAL AGENT
  |     +-- MEMBER 2  ---> IS ITSELF AN LLM COUNCIL
  |     |     +-- ... skills / formal agents
  |     +-- MEMBER 3  ---> IS ITSELF AN LLM COUNCIL
  |
  +-- COUNCIL B          (an LLM council)
  |     +-- MEMBER 1 ... (council) ... skills / formal agents
  |
  +-- COUNCIL C
        +-- ...
                     |
                [wave barrier: converge, accept or block]
                     |
WAVE n+1  consumes the accepted output of wave n
```

**Three living layers, one deterministic floor:**

| Layer | What it is | Loaded with |
|---|---|---|
| Wave | a set of LLM councils, sequenced and loopable | wave-level task framing |
| Council | an LLM council | its own MMM |
| Member | **itself an LLM council** | a *different* MMM |
| Floor | skills + formal agents | deterministic, no MMM needed |

Rules that make the nesting work rather than merely deep:
- every node gets a **different MMM**, loaded as pre-language, not rules;
- every node gets **constrained inputs**; minimize similar root inputs;
- **what each council and wave does is arbitrary** — the harness is
  content-agnostic;
- divergence is driven downward, convergence upward, wave by wave;
- `input_diversity_gate.py` proves the spread was real, deterministically.

## PART 2 — THE VOICES (9)

Pre-language salience profiles. Two installations, same roster.

`~/Codex-Ratchet/.claude/agents/voice-*.md` (source) and
`wizard/packet-v4-3-current/agents/voices/*.md` (packet, scrubbed):

| Voice | Drives |
|---|---|
| `voice-hume` | evidence, uncertainty, honest next move |
| `voice-zhuangzi` | live readings, alternate interpretations, exclusion condition — **generator of prompts for other LLMs** |
| `voice-feynman` | mechanism, operation, observable, pass/fail check |
| `voice-orwell` | plain wording, anti-fog |
| `voice-popper` | falsifier; killed / open / survived |
| `voice-pushback` | overclaim boundary and correction |
| `voice-factory` | bottleneck, queue, handoff, leverage |
| `voice-strategy` | sequence, priority, retreat/hold condition |
| `voice-systems` | feedback loop, second-order effect |

## PART 3 — THE FORMAL AGENTS

### Wizard-loop agents (9)
`~/.claude/agents/wizard/` and `packet-v4-3-current/agents/wizard-loop/`:
`evidence-mapper`, `falsifier-agent`, `premortem-agent`,
`prompt-packetizer`, `route-sequencer`, `route-truth-agent`,
`scope-keeper`, `scout-runner`, `selector-compiler`.

### Parent routes (9) — `packet-v4-3-current/agents/parents/`
`decision.context_strategy`, `decision.move_selection`,
`decision.evidence_boundary`, `failure.premortem`, `failure.falsifier`,
`failure.loophole_auditor`, `follow_up.next_move_selector`,
`follow_up.lane_builder`, `follow_up.compile_gate`.

### Managers (5, non-voting) — `agents/managers/`
`manager.run_controller`, `manager.child_health`,
`manager.route_truth`, `manager.output_compiler`,
`manager.strategy_memory`.

### Auditors (1) — `agents/auditors/`
`council-collapse-auditor` (also at
`~/Codex-Ratchet/.claude/agents/council-collapse-auditor.md`).

### Codex-Ratchet project agents (14) — `~/Codex-Ratchet/.claude/agents/`
`council-collapse-auditor`, `crossover-proof-runner`,
`fabrication-auditor`, `fresh-audit-runner`, `jax-audit-lane-runner`,
`jax-sim-runner`, `julia-carrier-builder`, `julia-sim-runner`,
`process-stage-gate-steward`, `pytorch-sim-runner`,
`repo-doc-archaeologist`, `sim-contract-gatekeeper`,
`smt-proof-engineer`, plus the nine voices above.

### General agents — `~/.claude/agents/`
`core/`: code-archaeologist, code-reviewer, documentation-specialist,
performance-optimizer. `orchestrators/`: project-analyst,
team-configurator, tech-lead-orchestrator. `universal/`: api-architect,
backend-developer, frontend-developer, tailwind-css-expert. Plus
`elite-ai`, `meta-agent`, `specialized/react/`.

## PART 4 — THE SKILLS

### Codex skills — `~/.codex/skills/` (44)

**Wizard lineage (5 generations installed side by side):**
`three-council-wizard`, `three-council-wizard-v4`,
`three-council-wizard-v4-1`, `three-council-wizard-v4-2`,
`three-council-wizard-v4-3`.

**Wizard council-member skills (5):** `wizard-factory-handoff`,
`wizard-follow-up-selector`, `wizard-loophole-auditor`,
`wizard-strategy-loop`, `wizard-systems-strategy`.

**Bridge / fanout:** `claude-bridge` (holds `claude_bridge.py`,
`claude_child_fanout.py`, `gemini_child_fanout.py`,
`fanout_receipt_summary.py`), `claude-pattern-intake`.

**Sim lane:** `jax-sim`, `julia-sim`, `pytorch-sim`, `three-engine-sim`,
`lego-sim-classifier`, `sim-stack-maintenance`,
`codex-ratchet-sim-audit-spine`, `terrain-operator-math-lock`.

**Thread / run control:** `thread-dispatch-controller`,
`thread-run-monitor`, `thread-closeout-auditor`,
`codex-automation-controller`, `codex-primary-runtime`,
`safe-run-maintenance`, `codex-ratchet-env-agent-coordination`,
`codex-ratchet-deep-stack-stress`, `codex-ratchet-tool-status-auditor`.

**Memory / distillation:** `a1-from-a2-distillation`,
`a2-a1-memory-admission-guard`, `a2-brain-refresh`, `ratchet-a2-a1`,
`brain-delta-consolidation`, `chronicle`, `bounded-hermes-intake`,
`closeout-result-ingest`.

**Research / intake:** `external-research-refinery-launcher`,
`external-research-return-ingest`, `pro-return-instant-audit`,
`karpathy-bounded-improve`, `codex-skill-agent-upgrader`, `brev-cli`,
`premortem`.

### Claude Code skills — `~/.claude/skills/` (7)
`aligned-mmm`, `claude-wizard-loop-engineering`, `codebase-memory`,
`codex-first`, `brev-cli`, `govuk-style`, `test-skill`.

### Packet-local skills — `packet-v4-3-current/skills/`
`claude-bridge`, `claude-pattern-intake`, `premortem`,
`sim-audit-spine`, `source-math-lock`, and
`council-members/`: `collapse-auditor`, `factory-handoff`,
`follow-up-selector`, `loophole-auditor`, `strategy-loop`,
`systems-strategy`.

## PART 5 — THE ASYMMETRY, STATED

Codex carries the full estate: 5 Wizard generations, 5 council-member
skills, the whole sim lane, thread control, memory distillation.
Claude Code carries 7 skills, of which 2 are Wizard-relevant
(`aligned-mmm`, `claude-wizard-loop-engineering`) — **no council-member
skills installed on the Claude side**, though the 9 wizard-loop agents
are there under `~/.claude/agents/wizard/`.

So: Claude Code can run the loop agents but has no installed council
members; Codex can run councils but reaches Claude for children through
`claude_child_fanout.py`. That is why the stable swarm path runs
Codex-parent → Claude-child, and why the Claude side is the thinner
half of the nesting today.
