# Wizard — wave structures, councils, and the skills that exist (2026-08-06)

Corrected read. Prior notes in this directory were written from a
v3.5 concept file and one partial pass of the v4.3 runtime. This one is
written from the packet skills manifest, the subsubagent scaling
runbook, and the installed skill trees on disk.

## 1. The skills DO exist, on disk, in two runtimes

**Codex — `~/.codex/skills/` (44 skills).** Wizard lineage installed as
separate versioned skills:
`three-council-wizard`, `three-council-wizard-v4`,
`three-council-wizard-v4-1`, `three-council-wizard-v4-2`,
`three-council-wizard-v4-3` — five generations side by side.
Council members as their own skills: `wizard-factory-handoff`,
`wizard-follow-up-selector`, `wizard-loophole-auditor`,
`wizard-strategy-loop`, `wizard-systems-strategy`.
Supporting: `claude-bridge`, `claude-pattern-intake`, `premortem`,
`codex-ratchet-sim-audit-spine`, `terrain-operator-math-lock`,
`lego-sim-classifier`, `thread-dispatch-controller`,
`thread-run-monitor`, `thread-closeout-auditor`,
`codex-automation-controller`, `jax-sim`, `julia-sim`, `pytorch-sim`,
`three-engine-sim`, `a2-a1-memory-admission-guard`,
`a1-from-a2-distillation`, `ratchet-a2-a1`, and others.

**Claude Code — `~/.claude/skills/` (7 skills):** `aligned-mmm`,
`claude-wizard-loop-engineering`, `codebase-memory`, `codex-first`,
`brev-cli`, `govuk-style`, `test-skill`.

**Asymmetry worth naming:** Codex carries the full Wizard skill estate
including per-member council skills and the sim lane; Claude Code
carries two Wizard-relevant skills (`aligned-mmm`,
`claude-wizard-loop-engineering`) plus `codex-first`. The council
members are not installed on the Claude side.

**Packet-local skills** (`packet-v4-3-current/skills/`):
`claude-bridge`, `claude-pattern-intake`, `premortem`,
`sim-audit-spine`, `source-math-lock`, and
`council-members/{collapse-auditor, factory-handoff,
follow-up-selector, loophole-auditor, strategy-loop,
systems-strategy}`.

## 2. The wave structure is MEASURED, not theoretical

From `SUBSUBAGENT_SCALING_RUNBOOK_v1.md`. This is the swarm operating
envelope, established by running it.

### Path truth

```text
UNSTABLE: Codex parent -> Claude Bridge stream mode -> Claude Task/Agent fanout
STABLE:   Codex parent -> claude_child_fanout.py -> bounded Claude child calls
                       -> fanout_receipt.json
```
Fixes required: hard timeout control, one parent-readable receipt, and
**cross-parent child throttling** — without a shared model-level slot
limiter, 7–8 parents stampede the Claude CLI with 28–32 simultaneous
starts and produce false failures.

### Count Law

Count only completed receipts. Do **not** count started processes,
prompt files, pending children, timed-out children, stream starts,
orphaned calls, or direct main-thread calls. A child counts only when
the parent returned a receipt, `fanout_receipt.json` exists, child
status is completed, the child bridge receipt path exists, and the
output is usable.

### Measured ladder (selected rows, all parent-run)

```text
1 x 1 Sonnet high, t60                  : 1 completed,  8.5s
1 x 4 Sonnet high, t60,  conc 4         : 4 completed, 52.5s
1 x 8 Sonnet high, t150, conc 4         : 8 completed, 113.6s
1 x 12 Haiku,      t90,  conc 6         : 12 completed, 73.7s (2 clarification-style)
4 x 4  Haiku,      t75,  conc 4 each    : 16 completed, 18.3-21.5s
4 x 6  Sonnet high,t180, conc 4 each    : 24 completed, 31.1-36.6s
4 x 8  Haiku,      t100, conc 4 each    : 32 completed, quality drift increased
8 x 8  Sonnet high,t210, conc 4 each    : 64 completed, 34.3-131.3s
8 x 12 Haiku,      t130, conc 6 each    : 96 completed after 3 parent-return reroutes
8 x 12 Sonnet high,t260, conc 4 each    : 96 completed, 57.3-143.1s
8 x 16 Haiku,      t180, conc 8 each    : 118 completed, 14 TIMED OUT — beyond envelope
8 x 8  Haiku, stop-after-completed 4, global-max-active 8
                                        : 32 completed, 18 abandoned, 14 not launched
mixed parent wave (by model)            : Sonnet 6, Haiku 8, Gemini 2, Opus 1 = 17
```

### The four named wave shapes

| Shape | Configuration |
|---|---|
| **Safe default** | 8 parents x 12 Sonnet-high children, t260, conc 4/parent |
| **Aggressive default** | 8 parents x 8 Sonnet-high children, t210, conc 4/parent |
| **Fast scout** | 8 parents x 8 Haiku, stop-after-completed 4, t120, conc 4/parent, global-max-active 8 |
| **Fast scout edge** | 4 parents x 8 Haiku, t100, conc 4/parent — watch output quality |
| *(edge, not a default)* | 8 x 16 Haiku at conc 8 — finishes many children but timeout tails and parent drain make it a poor default |

### Limiter and model-role rules

- **Add parents before raising per-parent concurrency.** Keep Claude
  per-parent concurrency at 4; keep `global-max-active` near 8 until a
  higher CLI start limit is proven.
- **Use `stop-after-completed`** for useful-subset scouting so slow
  tails are abandoned *with receipts*.
- **Gemini** = two-child fallback lane; 4 parents x 2 Gemini stable at
  120s cap, with CLI warning noise.
- **Opus** = rare arbitration or doctrine-conflict review, **not** a
  wide scout pool.
- **Reroute rule:** on timeout, keep the parent receipt, do not count
  the timed-out child, spawn a smaller replacement with a narrower
  prompt.

### The running tools

```text
~/.codex/skills/claude-bridge/scripts/claude_bridge.py
~/.codex/skills/claude-bridge/scripts/claude_child_fanout.py
~/.codex/skills/claude-bridge/scripts/gemini_child_fanout.py
~/.codex/skills/claude-bridge/scripts/fanout_receipt_summary.py
```
`fanout_receipt_summary.py --route-prefix <p> --show-routes` reports
accepted completed children, timed-out children, abandoned tails, and
not-launched jobs — run it before writing Wizard headers or comparing
parent waves.

## 3. What this means for CB

The swarm is not a design problem. It is **installed, measured, and
already governed by a count law that matches CB's doctrine**: only
completed receipts count, timed-out children are not evidence, a
parent-reported child is not raw child proof.

CB's job is therefore narrow and clear: consume `fanout_receipt.json`
under the route-truth five-field contract, apply the count law as a
gate rather than a convention, and refuse any wave summary whose
completed count exceeds its receipt count. The wave shapes above are
the exploration lane's operating envelope; CB never chooses them, and
never promotes on consensus across them.

## 4. Still unread, named honestly

`mmm/FULL_MMM_v4_3.md` and the mini-MMM registry; the ~700 remaining
lines of `WIZARD_v4_3.md`; `agents/` specs; `taskcards/`; `adapters/`;
`schemas/`; the v4.2 packet (which per the owner is where v4.3's
substance actually comes from — v4.3 is a small mod of it); the Hermes
and Claude runtime adaptations; and the last 80 lines of the scaling
runbook.
