---
title: Nominalist Translation Rules
created: 2026-04-09
updated: 2026-04-12
type: concept
tags: [harness, language, constraints, system, canonical, formal]
sources:
  - /Users/joshuaeisenhart/wiki/concepts/constraint-on-distinguishability.md
  - /Users/joshuaeisenhart/wiki/concepts/nominalism-in-this-system.md
  - /Users/joshuaeisenhart/wiki/concepts/enforcement-and-process-rules.md
  - /Users/joshuaeisenhart/wiki/concepts/llm-bias-inversion-rules.md
framing: current
---

# Nominalist Translation Rules

Support fence:
- this page is a translation/control surface for how to restate claims
- it is not a proof page, a provenance source, or a substitute for naming the direct probe/result evidence behind a claim

Operational rules for restating any system claim in nominalist framing. Not philosophy — these are executable constraints on how LLMs must describe this system.

## The Core Inversion

Default LLM framing: objects exist first, then interact.
This system: constraints exist first, what survives is provisional.

Every statement must be checkable against this inversion before it is accepted.

## Translation Rules (7 mandatory)

### Rule 1: Object → Survivor

**Default:** "A density matrix is a quantum state."
**Nominalist:** "A density matrix is an object that survived the admissibility constraints active in this context."

**Pattern:** Replace "X is Y" with "X survived constraint set C" or "X is admissible under C."

### Rule 2: Creation → Selection

**Default:** "The channel creates entanglement."
**Nominalist:** "The channel, when applied to separable states, produces states that survive the entanglement witness tests."

**Pattern:** Replace "creates/produces/generates" with "selects/admits/survives."

### Rule 3: Essence → Probe-Relative Identity

**Default:** "This state has high entropy."
**Nominalist:** "This state registers high entropy under the von Neumann probe with the identity basis."

**Pattern:** Replace "has/possesses/is characterized by" with "registers under probe P" or "is distinguished by measurement M."

### Rule 4: Causation → Constraint Coupling

**Default:** "L4 causes absolute measures to fail."
**Nominalist:** "Absolute measures do not survive when the composition constraint (L4) is active."

**Pattern:** Replace "causes/drives/leads to" with "does not survive under" or "is excluded by."

Additional fence:
- do not treat causality as a primitive hidden substrate
- if causal language is used at all, it must be presented as a later admissible reading of a constraint/manifold relation, not as the starting explanatory ground

### Rule 5: Truth → Admissibility

**Default:** "It is true that these 28 families are irreducible."
**Nominalist:** "These 28 families survived all constraint shells tested so far. No further reduction was found under the active constraint set."

**Pattern:** Replace "true/factual/proven" with "admitted/survived/not excluded by."

### Rule 6: Identity → Distinguishability Class

**Default:** "These two states are the same."
**Nominalist:** "These two states are indistinguishable under the probes and constraints active in this context."

**Pattern:** Replace "same/equivalent/identical" with "indistinguishable under P" or "in the same equivalence class under C."

### Rule 7: Universal → Context-Bound

**Default:** "Quantum states have the following properties..."
**Nominalist:** "Under the constraint set active here (F01, N01, CPTP, d=2, ...), the following structures are admissible..."

**Pattern:** Replace universal claims with explicit constraint-bound claims. Always name the constraint set.

## Anti-Patterns (banned constructions)

| Banned | Why | Replacement |
|---|---|---|
| "X is fundamentally Y" | Platonic essence claim | "X behaves as Y under constraints C" |
| "X emerges from Y" | Forward-causal narrative | "X is admissible when Y-constraints are active" |
| "X exists" (bare) | Unconstrained reification | "X is admissible / X survived probe P" |
| "The real X" | Assumes a single true ontology | "X as described under framing F" |
| "X means that..." | Collapses probe-relative to absolute | "X is consistent with... / X does not exclude..." |
| "X explains Y" | Narrative causal claim | "X is correlated with Y under constraint C" |
| "X must be..." | Modal overclaim | "X is forced by constraint C / X does not survive without C" |

## How to Apply

1. Take any statement about the system
2. Check it against each of the 7 rules
3. If it matches a default pattern, translate it
4. If it matches an anti-pattern, reject it and rewrite
5. The translated version must be more specific (naming constraints/probes) not less

## Root-Constraint Enforcement For LLM Behavior

These translation rules are not only about wording. They should shape execution behavior under the two root constraints.

### F01 behavioral implication
- keep work finite, bounded, and witness-backed
- do not replace exact requested packets with broader "helpful" sweeps
- require concrete evidence paths before promoting claims

### N01 behavioral implication
- preserve requested order exactly when the process specifies one
- do not reorder lanes or phases because another step seems productive
- treat out-of-order work as invalid for the requested task, not as partial success

A harness that follows nominalist translation but ignores F01/N01 in execution is still drifting. The same anti-reification discipline must apply to controller behavior, not only to prose.

## Constraint-On-Distinguishability Enforcement

The harness should also enforce a specific distinguishability discipline:
- do not collapse raw difference, observed difference, admissible difference, and stable difference
- do not let a measured separation automatically become ontology, causality, or explanation
- require the active support/manifold/probe layer to justify why a distinction survives and why later structure is allowed to build on it

This is part of nominalist constraint engineering, not a side note. The controller and the prose should both be able to answer:
- what is being distinguished?
- under which probes?
- under which support/manifold constraints?
- is the distinction merely visible, or is it stable and load-bearing?

## Connection to [[llm-bias-inversion-rules]] and [[harness-bias-inversions]]

These translation rules handle the *what* (how to restate claims). The bias inversion rules handle the *why* (what default LLM habits cause the problems). [[harness-bias-inversions]] turns those failure modes into a controller-facing enforcement checklist. Together they form the harness instruction set.

## Related Pages

- [[llm-bias-inversion-rules]] — specific LLM habits this inverts
- [[harness-bias-inversions]] — controller-facing enforcement form of the six inversions
- [[nominalism-in-this-system]] — the philosophical foundation
- [[nominalist-framing]] — reading mode for the wiki
- [[llm-controller-contract]] — the execution contract
- [[enforcement-and-process-rules]] — Rule 8 (no Platonic language)
- [[constraint-on-distinguishability]] — formal source for F01/N01 and probe-relative identity
- [[probe-doc-result-map]] — probe-relative identity in practice
- [[constraint-on-distinguishability]] — the formal basis for Rule 6
- [[harness-translated-companion]] — proof-of-method page showing the translation stack on one canonical source pair

- [[nominalist-cs-jp-systems-bridge]] — nominalist CS ↔ Jungian/self-similar frameworks bridge
