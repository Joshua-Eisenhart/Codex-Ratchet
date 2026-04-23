# Legacy Context and Genealogy

Date: 2026-04-05
Status: Extracted from legacy v5 docs (dated 2026-03-01 to 03-22).
        Content is ~4 weeks old. Some framing is STALE (see flags).
        Structural content and genealogy are STILL VALID.
        Nothing here is current canon — it is context and history.

Source: MODEL_CONTEXT copy.md (2026-03-07), INTENT_SUMMARY copy.md
        (2026-03-22), lev_nonclassical_runtime_design_audited.md

---

## Staleness Flags

These docs predate this session's corrections. Known stale items:

| Item | Legacy says | Current says |
|---|---|---|
| Vocabulary | accept/reject | survived/killed/open |
| Causality | "causes drift" (39+ instances in lev doc) | nominalist: "drifts under this assumption" |
| Identity | unqualified "IS" in descriptive passages | probe-relative correspondence |
| Run telemetry | dated 2026-03-01, uses old vocabulary | evidence artifacts, not current benchmarks |
| A2 references | v3 paths (system_v3/a2_state/) | v5 paths |

What IS still valid: structural claims, nominalist positioning,
constraint methodology, genealogy, entropy classification, retooling
template, adversarial run evidence.

---

## Academic Genealogy (from MODEL_CONTEXT)

Traditions aligned with the system, with what to keep and what
classical residue to strip:

| Tradition | Key figure(s) | What's aligned | What to strip |
|---|---|---|---|
| QIT reconstruction | Hardy, D'Ariano, Chiribella | Operational foundations, no hidden variables | Still uses classical probability |
| Relational QM | Rovelli | No observer-independent state | Still uses continuous spacetime |
| Constructor theory | Deutsch, Marletto | Tasks as fundamental, counterfactuals | Still classical computation substrate |
| Twistor theory | Penrose | Hopf fibration native territory | Classical spacetime background |
| Ruliad / computational universes | Wolfram | Ruliad ≈ constraint manifold | Determinism, classical rules |
| Cellular automaton QM | 't Hooft | Discreteness at base layer | Determinism, fixed lattice |
| FEP / active inference | Friston | Prediction-first, Markov blankets | Classical probability, continuous time |
| Bioelectric networks | Michael Levin | Multi-scale probe-induced partitions | Standard developmental bio framing |
| Interface theory | Hoffman | Perception as interface, not mirror | Dualism (evolution separate from consciousness) |
| Entropic gravity | Verlinde | Gravity as emergent from entropy | Classical thermodynamic framing |
| Cosmological natural selection | Smolin | Evolutionary instinct for universes | Classical spacetime, black holes as seeds |
| Causal set theory | Sorkin, Dowker | Discreteness + partial order | Classical probability measure |
| IIT | Tononi | Integrated information, Phi | Potentially unfalsifiable |
| Irrational Game Theory | Owner (Eisenhart) | Symmetric win/lose, 4F mapping | Original work — IS the system |

Wolfram critique (specific): "Wolfram's rule application becomes Axis-0
Feynman path integrals acting on jk fuzz field shells. Each step is not
a single rule firing — it is a sum over Kraus-history indices across
nested shell boundaries."

Smolin inversion: white holes (not black holes) are the seed. Time
direction flipped. Potential creates the present.

Hoffman critique: "Hoffman sees the interface correctly but doesn't see
that the interface IS the evolutionary landscape, not something shaped
by it."

---

## Entropy Classification System (from INTENT_SUMMARY)

| Tier | Content type | Processing |
|---|---|---|
| E0 | Root constraints, bootpacks, canon state | Direct reference, no processing |
| E1 | Constraint ladder specs, axis specs, contracts | A1's prime fuel. Strip jargon, reformulate for B |
| E2 | Physics fuel digests, refined extracts | A2 processes, A1 uses with care |
| E3 | Holodeck docs, Grok/Gemini digests, apple notes | A2 mines. High entropy — extract structure, quarantine hazards |

---

## A2 Control Hierarchy (from INTENT_SUMMARY)

Authority ranking (what outranks what):

1. User corrections outrank everything
2. INTENT_SUMMARY outranks MODEL_CONTEXT
3. A2_SYSTEM_UNDERSTANDING_UPDATE outranks both
4. A2_TERM_CONFLICT_MAP handles contradictions
5. Recency does NOT outrank authority

---

## Graveyard-First Doctrine (from INTENT_SUMMARY)

Everything starts DEAD in the pool. 306+ fuel entries seeded at init.
The graveyard is the workspace — items actively trying to be resurrected.
Survivors earned their way out. The 50% ratio emerges naturally from
real exploration, not random padding.

---

## LLM Failure Mode Warning (from INTENT_SUMMARY)

"THIS IS THE PRIMARY FAILURE MODE. The system is explicitly designed
to be non-classical, non-conventional, and to resist exactly the kind
of pattern-completion LLMs are trained to do."

LLMs default to classical thinking and classical methods. This system
must resist that constantly.

---

## Adversarial Run Evidence (from INTENT_SUMMARY)

Key finding from March 2026 hardening runs:
- Parameter-only hardening didn't increase rejects
- Content-level adversarial injection was needed (classical-time smuggling,
  commutation traps, ontology traps)
- NEG kill gating finally produced reject growth at cycle 11:
  rejected=17, accepted=23
- Memo-level adversarial pressure beats parameter tuning

---

## Retooling Template (from lev_nonclassical)

Systematic pattern for retooling external methods:

1. Concept — what is the method?
2. Why it matters — what does it offer?
3. Classical assumption that drifts — what's smuggled in?
   (STALE: original says "causes drift" — reframed here)
4. Retooled interpretation — how to use it without the classical residue
5. Integration with Lev — where it fits in the architecture
6. Implementation sketch — concrete code/interface

Applied to 13+ methods including: nested Hopf tori, topology/orchestration/
dispatch, graph topology thinking, nonclassical state space, phase/loop-scale
runtime, Karpathy design philosophy, nanochat, autoresearch.

---

## Concrete Runtime Interface (from lev_nonclassical)

HopfLikeState extends RuntimeState:
- fiberId: string (optional)
- phaseIndex: number
- phasePeriod: number
- loopScale: LoopScale (micro/meso/macro)

Phase-band logic: phase position determines behavior.
"Not all moments are the same" — operationalized.

---

## What This Doc Does NOT Claim

- These legacy docs are NOT current canon
- The run telemetry is evidence, not current benchmark
- The vocabulary is stale (accept/reject → survived/killed/open)
- The causal language needs reframing
- The structural content is valid; the framing may need updating
- Nothing here overrides this session's corrections
