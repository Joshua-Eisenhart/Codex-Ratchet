# THE WIZARD WAVE MODEL — owner-minted structure (2026-08-06)

**Provenance: owner canon.** Stated by the owner directly. Prior notes
in this directory described the v4.3 *instantiation* (nine parent
routes, 33 agent specs) and missed the general model. This file is the
general model. Where they disagree, this file wins.

## The nesting

```
WAVE                     sequential; loops within itself and with other waves
 └── COUNCIL SET          a wave is made of a set of LLM councils
      └── LLM COUNCIL     whose MEMBERS ARE THEMSELVES LLM COUNCILS
           └── LLM COUNCIL (member-level)
                └── SKILLS + FORMAL AGENTS      the deterministic floor
```

Three living layers, then a deterministic floor:

1. **Wave** — sequential barrier; may loop internally and across waves.
2. **Council** — a set of LLM councils.
3. **Member council** — each member of a council is a council in its
   own right, not a single model call.
4. **Skills and formal agents** — the third layer down is actual
   skills and formal agents, deterministic, not LLM judgment.

**What each council and each wave does is arbitrary.** The structure is
content-agnostic. That is the point: it is a general harness, not a
fixed pipeline. v4.3's Decision/Failure/Follow-Up is one instantiation
of the model, not the model.

## Why the nesting is the mechanism, not decoration

The nesting is what lets the system **embed many LLMs, many skills, and
many formal agents, then drive them to unify.**

- **Diversity is structural.** Every node is loaded with a *different*
  MMM and *constrained inputs*. The explicit design rule: **minimize
  all the LLMs having similar root inputs.** Shared root inputs are
  what collapse a swarm into one opinion.
- **Divergence and convergence are both driven.** Highly diverse LLM
  council debate produces spread; the wave barriers and the compile
  gate produce unification. Neither is left to chance.
- **Waves loop.** A wave can loop within itself and with other waves,
  so convergence is iterative rather than single-pass.
- **Waves can be formalized** while council membership stays flexible —
  the skeleton is checkable even though the seats are swappable.

## What the Wizard was originally for

The first Wizards **created the very next formal prompt for an LLM
thread**. The Wizard is a prompt engineer.

And critically:

> It not only created possible future prompts. **It even runs them
> before the output.** So the options are not arbitrary — actually run
> and tested.

That is the difference between a menu of guesses and a menu of
measured options. The candidate next-prompts are executed, and their
results are what make the choice non-arbitrary.

Cost and consequence, as stated:

- **It is resource consuming.**
- **It places much of the work of a prompt in the prompt before it** —
  embedded context, context management.
- **Driving things into many LLMs reduces context rot.** It **burns the
  entropy in short-running LLMs.**

That last line is the load-bearing insight. Entropy accumulates in a
long-lived context; a long thread degrades. Spawning many short-lived
children means each child accumulates and then dies, and only a
distilled receipt returns to the parent. The long thread stays lean
because the disorder was spent somewhere disposable.

## Consequences for the rest of the stack

**For CB.** CB does not run councils and does not choose wave shapes.
CB's jobs are: enforce the count law on returned receipts; enforce
proof depth; refuse described-but-not-run routes; and — new from this
model — **verify input diversity**, because "minimize similar root
inputs" is a property that must be measured, not intended. A wave whose
nodes share a root-input hash is one opinion wearing many hats, and
should be labelled as such regardless of how many receipts it returns.

**For the MMM.** One MMM primed into every node is the failure mode.
Per-node MMMs are the anti-collapse mechanism. CB's own MMM biases the
controlled lane only, never the exploration lane.

**For context rot.** Two independent mechanisms now serve the same
goal: the receipt index (measured: 54,055x fewer tokens for a bounded
question than a directory dump) constrains what enters the context, and
the wave model burns entropy in disposable short-running children so it
never enters the long thread at all.

**For the sim/manifold work.** The owner's standing problem — the model
is probably right, the ORDER is often wrong, and no LLM would explore
alternate orders, so he drove them by hand — is exactly what a
divergent wave with tested candidate prompts is built to solve.

## Status

The general model above is owner canon. The v4.3 packet is one
formalization of it. Known gaps between the two, from the packet read:
`voice.zhuangzi` (alternate readings) has an agent spec but no required
seat in any of the nine v4.3 routes; and the packet's member layer is
specified as agents rather than as councils-of-councils, so the
member-level nesting the owner describes is thinner in v4.3 than in the
model.
