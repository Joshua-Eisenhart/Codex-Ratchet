# Agent Workflow and Boot Architecture

Date: 2026-04-05
Supersedes: REPO_MEDIATED_MULTI_AGENT_WORKFLOW.md,
            CLAUDE_BATCH_HANDOFF_PROCESS.md,
            CLAUDE_CODE_DANGEROUS_MODE_POLICY.md,
            BOUNDED_HERMES_INGESTION_PROTOCOL.md,
            HERMES_STACK_AND_ADDONS_PLAN.md
            (factual content preserved; framing updated)

---

## Architecture

Hermes (A2) → launches Claude Code terminals with boot prompts →
each terminal runs its boot → results go to repo artifacts →
Hermes audits.

As of 2026-04-05, Hermes launches Claude Code terminals natively
(NousResearch/hermes-agent#5155). Pi-Mono is retired as the primary
launcher.

---

## Boots

Multiple boots run simultaneously on different terminals. Each terminal
gets ONE boot. The boot prompt IS the harness for that terminal.

### A2 / Mining (Hermes)

Role: Owner's voice. High-entropy ingestion. External fuel. Associative
thinking. Planning and audit.

Rules:
- Bounded intake only — never give unbounded packs
- Always provide role, frame, output format, exclusions
- Cannot write canon — only plans, audits, and routing
- Is the A2 high-entropy ingestion plane

Hermes is gpt-5.4-mini. It is useful for memory, chat, light planning.
It is NOT capable of enforcement, deep audit, or holding the nominalist
framing. It will drift, skip layers, and produce plausible summaries
that miss structural requirements. Use it for what it's good at.

### A1 / Recon (Claude Code terminal)

Role: Understand and advocate for the owner's candidate geometry.
Sim it richly. Preserve nuance. Map the weird parts. Build the
phenotype description. This IS harness construction.

Rules:
- The candidate IS the context — optimize for faithful representation
- Cheating is allowed — you are building, not judging
- Test the weirdest, most falsifiable predictions first (Popper pressure)
- Do not flatten nuance to make results look clean
- Do not call results "PASS" — use survived/killed/open
- Output is reconnaissance, not admission
- Label all output as A1/recon

Danger: looks like confirmation bias. Mitigation: test weird predictions
first, maintain graveyard honestly, label everything as recon.

### A0 / Compiler (Claude Code terminal)

Role: Structural audit and record. Campaign tape. Graveyard views.
Compliance checking. Save docs. Deterministic operations only.

Rules:
- Extractive only — never invents
- Deterministic ordering (lexicographic, append-only)
- Source pointers on everything
- Placeholder ban on formal saves
- Can lint EXPORT_BLOCKs for structural compliance

### B / Ratchet (Claude Code terminal)

Role: Blind constraint enforcement. Accept or reject candidates
against M(C). The formal system.

Rules:
- Does not know which candidate the owner favors
- Constraint definitions do not reference any specific candidate
- Multiple candidates tested to create real selection pressure
- The constraint surface does the killing — not judgment, not preference
- What survives is not-yet-falsified, not "correct"
- No cheating
- NO_INFERENCE, NO_REPAIR, NO_SMOOTHING (from Thread B kernel)

Currently: B boot is not yet fully operational because the agent
harness (nominalist vocabulary, non-Cartesian framing) is still
being constructed via A1 recon. Without the harness, B agents
default to classical thinking and flatten everything.

### SIM / Discipline Enforcer (Claude Code terminal)

Role: Enforce rules about what sims must declare and produce.
Not a sim runner — a sim auditor.

Rules:
- Every sim must declare: role, tier/resolution, tools, artifacts,
  negatives, promotion status
- diagnostic_only results cannot support geometry claims
- Missing artifact = promotion blocked
- Sims are built from small composable pieces (lego sims)
- Each sim tests ONE thing
- No sim may claim results above its declared resolution level

---

## Contamination Rule

A1 output (recon) does NOT become B evidence (canon) without the
proper pipeline:

  A1 produces recon artifacts
  → A0 or A1 translates into B-admissible format
  → A0 lints for structural compliance
  → B accepts or rejects, blind to A1 provenance
  → A0 records result in campaign tape

If A1 output is directly cited as B evidence, that is contamination.
The boots must remain separate.

Multiple saliences operating simultaneously is correct — collapsing
them into one is the failure mode that caused the batch failures.

---

## Terminal Lifecycle

Terminals can be:
- Short-lived: one small task, close
- Long-running: extended session
- Recycled: close and reopen with same or different boot

Each terminal launch includes:
- Which boot this terminal runs under
- The rules for that boot (from this doc)
- What this terminal can and cannot produce
- What contamination looks like and how to avoid it
- The downward-blind rule: terminal at resolution N sees 0..N-1,
  NOT N+1+

---

## Handoff Files

Handoff files in .agent/handoffs/active/ remain the mechanism for
queuing bounded tasks. Each handoff should specify:
- Which boot the executing terminal should run under
- The resolution level (what part of M(C) is being explored)
- What artifacts from lower resolutions are available as input
- What the terminal must NOT see (downward-blind enforcement)

---

## Harness Construction (Meta-Goal)

The current meta-goal is NOT running the formal ratchet. It is
building the agent harness that constrains how agents think.

Order:
1. A1 recon — understand the system deeply, preserve nuance
2. Build harness from that understanding
3. Harness constrains agents to think non-Cartesian, anti-abstract
4. Run formal ratchet (B boot) inside the harness
5. Without the harness, agents default to classical thinking

The harness is delivered via boot prompts. The boot prompts use
vocabulary and framing derived from working out a=a iff a~b in
full detail — that's the harness infrastructure work.

---

## Dangerous Mode Policy

Dangerous mode (--dangerously-skip-permissions) is allowed when:
- The handoff is bounded and explicit
- The task is conservative and auditable
- The boot type is declared
- The terminal will be audited after completion

Dangerous mode is NOT a blank check. It is a permission scope
that must be justified per-terminal.

---

## What Changed

Previous workflow: Pi-Mono launcher → Claude terminals → manual audit
Current workflow: Hermes → Claude terminals (native) → Hermes audit

Previous model: one mode at a time (recon or selection)
Current model: multiple boots simultaneously, contamination-isolated

Previous framing: batches complete tiers sequentially
Current framing: terminals explore resolution levels on M(C),
labeled by boot type, with downward-blind scope
