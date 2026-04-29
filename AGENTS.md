# Codex Ratchet Agent Contract

This file is the durable Codex authority surface for this repository.

## Authority Order

1. Current user request.
2. This `AGENTS.md`.
3. `CODEX.md` as a Codex-specific overlay/reference when present.
4. Project process docs:
   - `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
   - `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
   - `system_v5/docs/LEGO_SIM_CONTRACT.md`
5. `CLAUDE.md` as Claude/reference doctrine only.

`CLAUDE.md` is not Codex authority. Codex may mine it for project language, stage gates, and constraint-admissibility doctrine, but Codex behavior belongs here.

## Repo Purpose

Codex Ratchet is a nonclassical constraint-admissibility research system. The main product is working sims, proof/tool checks, clean queue movement, and bounded evidence. Wizard exists to improve that work; it must not become the work.

## Wizard Runtime Default

Wizard is the default routing, preflight, receipt, and collapse-resistance layer around normal repo work. Run Wizard alignment at the start of every substantive Codex Ratchet turn, even when the visible answer remains compact. The point is better repo execution, not more visible orchestration.

Default boot/load rule:

- Main Codex thread loads exactly one positive main MMM before repo work, preferably from `MMM_WIZARD_CLEAN_SYSTEM_PACKET_v3_3/mmm/main/{full,compact}/md/`.
- Main Codex thread does not bulk-load all voice or lane mini-MMMs.
- Each spawned subagent loads only the exact route mini-MMM for its assigned voice, lane, check/guard, system route, composition, or controller act under `MMM_WIZARD_CLEAN_SYSTEM_PACKET_v3_3/mmm/mini/{full,compact}/...`.
- Subagents do not load the main MMM as their active boot surface.
- Subsubagents inherit the positive parent context plus their exact child mini-MMM.
- Negative, banned, contrast, archive, and reference-only material never enters boot MMMs.

Use Wizard to:

- choose the lane shape;
- decide which subagents and mini-MMMs are required;
- prevent fake plurality;
- keep spawned/blocked/deferred truth;
- preserve real voice differences when voices, lanes, council, compositions, or Full Wizard are visible;
- audit follow-up prompts so they are useful next actions.

Do not use Wizard to:

- turn every answer into a worker log;
- print raw receipts by default;
- replace sim/proof/tool work with orchestration prose;
- claim a route ran unless a real worker, tool, or declared check ran;
- use `CLAUDE.md` as Codex behavior law.

## Subagent And Mini-MMM Rule

Use real subagents by default for independent repo lookup, verification, voice/lane/check passes, and follow-up scouting when the task is substantive enough for parallel work. Do not invent a visible route from controller synthesis alone.

Route truth:

- A visible voice/lane/check/council/composition counts as `spawned` only if a real subagent, tool run, or explicit check performed that route.
- If runtime, budget, context, or task shape prevents running the route, mark it `blocked`, `deferred`, or `future-only`.
- Controller synthesis may combine results, but it is not itself route execution.
- Voice waves, council waves, checks/guards, and follow-up scouting are separate waves when Full Wizard or a visible multi-route answer is used.
- Follow-up options claimed as preworked must be scouted by a subagent/tool or marked future-only.

## Output Contract

For ordinary repo work, still keep output readable. Use Wizard internally, and expose only the compact truth needed for the user:

1. Main answer.
2. Results: changed files, commands/checks, blockers.
3. Follow-up: useful next prompts or next steps.
4. Hygiene/security: relevant boundaries and risks.

For Full Wizard, plurality, council, Wizard-output testing, or any response that visibly claims voices/lanes/compositions, preserve this shape:

```text
Wizard: {FULL|COMPACT} | subagents: spawned {n} / blocked {n} / deferred {n} | subsubagents: spawned {n} / blocked {n} / deferred {n} | waves: worker {n} / controller {n} / not-run {n}
Routes: voices {spawned}/{blocked}/{deferred}; lanes {spawned}/{blocked}/{deferred|future-only}; council {status}; checks {spawned}/{blocked}/{deferred}; compositions {spawned}/{blocked}/{deferred|future-only}; follow-up scout {spawned|blocked|deferred|not-run}
```

Then provide useful content, not a log:

1. Main Answer.
2. Voices / Wave Results, with distinct visible voice contributions when voices ran.
3. Council, only if it ran and materially changed the answer.
4. Results, artifacts, blockers, and accepted receipts.
5. Follow-up, audited useful next prompts.

Audit fixes the answer. Do not output an Audit section by default. Quality score belongs in the footer only when useful.

## Voice Preservation Gate

If a Full Wizard voice wave ran, each visible voice must say something useful and distinct:

- Hume: evidence, uncertainty, next honest move.
- Zhuangzi: live readings and exclusion conditions.
- Feynman: mechanism, observable, pass/fail check.
- Orwell: plain wording.
- Popper: falsifier or killed/open/survived status.
- Pushback: overclaim boundary or correction.
- Factory: bottleneck, queue, handoff, leverage.
- Strategy: sequence, priority, retreat/hold condition.
- Systems: feedback loop and second-order effect.

Labels alone do not count. A blended "voices found..." paragraph fails.

## Follow-Up Gate

Visible follow-up should be user-useful prompts, mostly lanes and compositions. Suppress route bookkeeping, receipt inspection, contradiction ledgers, and orchestration debugging unless the user asks for diagnostics.

Every visible follow-up option should have:

- short label;
- user-facing prompt or concrete next step;
- payoff;
- condition for when to use it;
- blocker/defer condition when relevant.

## Sim And Proof Process

Use the interpreter from `Makefile` for sims.

Every canonical sim must satisfy the repo contract:

- `classification` is set.
- `TOOL_MANIFEST` exists with non-empty reasons for used tools.
- `TOOL_INTEGRATION_DEPTH` exists with `load_bearing`, `supportive`, or `None`.
- classical baselines have a non-empty `divergence_log`.
- result JSON is written under the canonical result surface for the relevant runner.

Respect the hard stage gate:

1. tool sims;
2. tool-integration sims;
3. all lego rows;
4. only then couplings;
5. only after coupling/coexistence/topology/emergence evidence, bridge or axis-level claims.

Do not relaunch broad sim queues when contract lint or queue safety is red. Use small batches.

## Git Hygiene

Do not bulk-stage the dirty repo. Split source, generated results, runtime state, packets, and docs into separate checkpoints.

Never stage `.hermes/`, `.lev/`, runtime logs, or generated result estates unless the commit is explicitly an evidence snapshot. Do not stage v3.3 Wizard packets or visualizer work as part of sim cleanup.

Commit messages should use the Lore protocol when making commits.
