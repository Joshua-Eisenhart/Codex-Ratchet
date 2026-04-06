# Hermes Repos and Ecosystem Classification

Status: working classification surface
Purpose: classify Hermes-related repos and ecosystem surfaces so they can be planned, installed, referenced, or ignored explicitly instead of remaining a vague cluster

This document is part of the Hermes stack planning layer.
It is not a broad software inventory. It is only about Hermes-related repos and Hermes-adjacent ecosystem surfaces.

---

## 1. Classification labels

Use these labels:

- `core`
  - first-class part of the Hermes stack

- `active_dependency`
  - needed directly for the current active Hermes setup

- `inspect_now`
  - should be read/reviewed now, but not necessarily installed or integrated immediately

- `reference_only`
  - useful to consult, not part of the live stack

- `method_mine`
  - useful as a source of patterns or techniques

- `later_integration_candidate`
  - worth considering later once the current stack is stable

- `not_justified_yet`
  - interesting, but not currently justified for the active plan

---

## 2. Core Hermes surfaces

## 2.1 Hermes Agent
Repo:
- `~/GitHub/hermes-agent`

Classification:
- `core`
- `active_dependency`

Why:
- this is Hermes itself
- Hermes is currently being treated as the A2 high-entropy ingestion plane
- Hermes needs to work cleanly for the broader plan to work

Current role:
- primary operational agent surface
- primary install/use target in the Hermes stack
- base for skills, memory, tools, ingestion, and orchestration workflows

Immediate action posture:
- stabilize
- understand
- classify add-ons around it
- do not treat as optional

---

## 3. Hermes improvement repos

## 3.1 Hermes Agent Self-Evolution
Repo:
- `~/GitHub/hermes-agent-self-evolution`

Classification:
- `inspect_now`
- `method_mine`
- `later_integration_candidate`

Why:
- directly aimed at improving Hermes Agent
- useful for evolving skills, tool descriptions, prompts, and later code
- clearly relevant to the Hermes stack
- but belongs to a second-order optimization phase, not the immediate foundation phase

Current role:
- Hermes improvement research surface
- source of methods/patterns for later bounded self-improvement

Why not first-line right now:
- current higher priority is Hermes core + tool stack + bounded ingestion + QIT proto work
- self-evolution should not outrun core stabilization

Immediate action posture:
- inspect and classify now
- do not make core setup depend on it yet

---

## 4. Hermes ecosystem curation surfaces

## 4.1 awesome-hermes-agent
Repo:
- `awesome-hermes-agent`

Classification:
- `reference_only`
- `method_mine`

Why:
- curated ecosystem/resource surface
- useful for surveying the Hermes ecosystem
- useful for add-on and skills discovery
- not part of the core runtime

Current role:
- ecosystem inventory source
- skill/add-on discovery source

Immediate action posture:
- inspect for ideas and classification
- not part of the required live stack

---

## 5. Hermes-adjacent optional memory surfaces

## 5.1 Honcho
Repo:
- `plastic-labs/honcho`

Classification:
- `reference_only`
- `later_integration_candidate`

Why:
- relevant to memory/stateful-agent concepts
- may be useful conceptually
- but not a first-line requirement for the current plan
- also has stronger licensing obligations than lightweight reference-only material

Current role:
- memory-model reference surface
- comparison point for Hermes memory ideas

Immediate action posture:
- inspect only if memory-side architecture becomes a current blocking issue
- not a core install target right now

---

## 6. Current Hermes stack ordering

The Hermes-related ecosystem should currently be thought of in layers.

### H0 — Hermes core
- `hermes-agent`

### H1 — Hermes workflow discipline
- bounded ingestion protocol
- Hermes stack/add-ons planning
- skills planning
- context handoff surfaces

### H2 — Hermes improvement layer
- `hermes-agent-self-evolution`

### H3 — Hermes ecosystem/reference layer
- `awesome-hermes-agent`

### H4 — optional sidecars
- `Honcho`
- other later memory or sidecar surfaces if justified

---

## 7. Immediate use guidance

### Install / stabilize now
- `hermes-agent`

### Inspect now
- `hermes-agent-self-evolution`

### Reference only now
- `awesome-hermes-agent`
- `Honcho`

---

## 8. Why this ordering matters

The current system is still in foundation/stabilization mode.
That means:
- Hermes core must be solid
- graph/proof/geometry tool stack must be solid
- bounded ingestion must be formalized
- QIT proto sims must become legitimate

Only after that does it make sense to push harder on Hermes self-improvement or extra sidecar ideas.

If the order is reversed, the stack risks becoming more complex before it becomes stable.

---

## 9. What to do with new Hermes-related repos later

Any newly encountered Hermes-related repo should be classified using the same labels:
- core
- active_dependency
- inspect_now
- reference_only
- method_mine
- later_integration_candidate
- not_justified_yet

Questions to ask:
1. Does this improve Hermes core now?
2. Is it required for bounded ingestion now?
3. Is it only a source of ideas?
4. Is it second-order optimization that should wait?
5. Does it create complexity before the stack is stable?

---

## 10. Current best summary

Right now:
- `hermes-agent` is core
- `hermes-agent-self-evolution` is important, but should be inspected rather than deeply integrated yet
- `awesome-hermes-agent` is a useful reference surface
- `Honcho` is a later candidate/reference memory surface, not a first-line install target

This keeps the Hermes ecosystem aligned with the current phase of work: stabilize first, optimize later.
