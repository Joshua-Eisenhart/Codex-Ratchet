# CB as swarm driver — recovered design, and the failure it must avoid

Written in the repo, 2026-08-06. Sources are the owner's own prior
work, located rather than invented; paths cited so nothing here is a
new claim.

## What already exists (recovered, not designed)

From `Joshua-Eisenhart-Wiki/projects/ai-agent-harnesses/claimgate-standalone-product-boundary-2026-06-20.md`:

**The extracted architecture, in the owner's words:**

```text
soft side: model/council fanout proposes, critiques, scores
hard wall: deterministic gate checks named oracle evidence
promotion: only deterministic gate can admit
loop exit: gate-clean tied to oracle, not consensus
```

**A live 3x3x3 swarm was actually run, model-agnostic and advisory:**

```text
product:run swarm attempted=27 completed=13 failed=14 providers=3 models=7
self:run    swarm attempted=27 completed=14 failed=13 providers=3 models=7
hard wall: external model lanes cannot promote
honesty audit: admitted_on_synthesized_evidence=0
```

Accepted providers spanned openrouter, xai, google and openai-codex;
accepted models spanned fusion, deepseek, qwen, kimi, glm, minimax,
grok, gemini and codex-native. Failures were recorded, not hidden.

**And the anti-fake-swarm rule already existed:**

> tests that reject same-provider fake swarms and accept arbitrary
> provider names when returned receipts are diverse

That is the crucial mechanism: a swarm is only a swarm if its
receipts are *diverse*. Nine calls to one model wearing nine hats is a
single opinion with extra steps.

Related prior art in the same corpus: Wizard v4.3 recorded as
`adapter_partial`, the v19 Harness Author intake as `adapter_partial`,
oh-my-openagent as `pattern_extracted` — i.e. the Wizard/Hermes/
Leviathan systems are explicitly **source mines, not product
dependencies**, with live model pools required but provider identities
treated as per-run capabilities.

## Why this matters for CB specifically

The v3 failure was not missing gates. Deterministic gating existed by
v3 (boots; threads a0, a1, b, sim — all non-LLM). The failure was that
**no exploration happened at the gates**: models absorbed the gate's
ontology, became hyper-conservative, and stopped sending anything out
to explore. The owner had to drive order changes by hand.

Swarm diversity is the direct countermeasure, and it is a countermeasure
to a *specific* mechanism: when every agent reads the same prompt, the
same MMM, and the same gate vocabulary, they collapse into one basin
and the system loses its capacity to propose an order it has not
already accepted. Different models under different prompts cannot
collapse the same way.

So CB's swarm role has a precise shape:

| Layer | Who | May do | May never do |
|---|---|---|---|
| Exploration lane | heterogeneous models, deliberately NOT sharing one prompt or one MMM | propose orders, rivals, reframings, counterexamples | be scored for conformity to the gate vocabulary |
| Council / wave | nested councils, sequential waves, formal agents + skills embedded | critique, score, rank proposals against each other | promote anything |
| Hard wall | CB, deterministic | admit, park, block, release against named oracle evidence | decide truth, or infer quality from consensus |

**Loop exit is tied to the oracle, not to agreement.** Consensus is
evidence about the models, not about the world.

## Rules this imposes on CB, stated so they can be tested

1. **Prompt diversity is a measurable property, not an intention.** A
   swarm receipt must record provider, model, and prompt-hash per lane,
   and a run whose lanes share a prompt hash is a single-opinion run
   and must be labelled as such.
2. **PARKED means "keep exploring", never "stop".** Every PARKED verdict
   names the missing artifact; the exploration lane is free to attack
   that gap by any route, including routes the gate vocabulary cannot
   express.
3. **The MMM biases the controlled lane only.** Priming every explorer
   with CB's vocabulary is precisely how the v3 collapse happened. The
   exploration lane gets the problem, not the ontology.
4. **Order-space is explorable.** The owner's standing observation is
   that the model is probably right while the ORDER of things is often
   wrong. A swarm that cannot propose a different order is not doing
   the one job most needed here.
5. **Diversity of receipts, not of labels.** Reuse the existing test:
   reject same-provider fake swarms; accept arbitrary provider names
   when the returned receipts genuinely differ.

## Status

This document is recovery and specification only. No swarm driver
exists in `constraint_box/` today. The nearest running code is the
ClaimGate-era `tools/live-swarm-run.js` referenced in the wiki
checkpoint, which is Node and legacy. A CB-side driver would be a
sequencer over the existing lease/capability machinery, emitting one
receipt per lane with provider, model and prompt hash — and would sit
in the exploration lane, outside the custody kernel.
