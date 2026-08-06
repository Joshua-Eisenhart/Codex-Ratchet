# Agent Containment and Object Orchestration

ConstraintBox orchestrates constrained finite presentations.  Agents are
temporary processors, not owners of project state.

## Deployment modes

| Mode | Boundary |
|---|---|
| human/CLI | human submits a bounded object directly |
| delegated service | an external LLM calls ConstraintBox; only inner work is contained |
| wrapped agent | ConstraintBox launches and owns the outer LLM tool surface |
| host adapter | LevOS, Codex, an IDE, or another runtime submits objects |

An external caller can ignore a returned verdict unless its host routes all
consequential capabilities through ConstraintBox.  This limitation must remain
visible.

## LLM-visible capabilities

| Capability | Meaning |
|---|---|
| `inspect_scoped` | read an approved object projection |
| `propose_candidate` | append a candidate branch |
| `propose_discriminator` | add an experiment or falsifier proposal |
| `request_capability` | request a registered controller operation |
| `submit_repair` | add a child branch preserving the failed parent |
| `query_obligations` | read active constraints without editing them |
| `request_write` | create a staged artifact proposal |
| `appeal_or_reoffer` | provide new evidence or changed contract |

The LLM does not receive general `bash`, unrestricted filesystem write, policy
write, verdict write, or raw credential access.

## Model-neutral interface

```text
propose(object_view, allowed_actions) -> proposal
criticize(candidate, evidence)        -> critique
repair(candidate, counterexample)     -> proposal
explain(decision, evidence)           -> non-authoritative draft
```

Pi, direct provider APIs, Codex, Claude, Gemini, or local models may implement
this interface.  No agent framework is required by the core.

## Compaction rule

Context compaction must preserve:

- every live or parked candidate;
- parent/child lineage;
- unresolved discriminators;
- rival operation orders and brackets;
- evidence and obstruction references;
- re-offer conditions;
- current `HOLD`/frontier result;
- claim ceilings.

A consensus summary cannot replace the branch complex.
