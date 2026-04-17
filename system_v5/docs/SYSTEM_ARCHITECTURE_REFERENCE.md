# System Architecture: Reference

Date: 2026-04-05
Status: Extracted verbatim from v5 docs. Not paraphrased.
Source: CS version of system first draft.md, System tools and plan.md,
        INTENT_SUMMARY copy.md

---

## CS Axiom Translation (EC-1 through EC-7)

| ID | Statement | CS meaning | Forbids |
|---|---|---|---|
| EC-1 | Identity not primitive | Object is "same" only if witnessed by handles/receipts/invariant checks | Assuming sameness after mutation without proof |
| EC-2 | Equality not primitive | Equivalence is contract-based: schema checks, type checks, compatibility checks | Free substitution, semantic smuggling |
| EC-3 | Identity requires boundary | Service/agent/module exists only relative to scope, ownership, interface boundary | Ambient authority, global omniscience |
| EC-4 | Time/causality derived from ordered composition | Causal chain = event log and receipt chain, not a story told afterward | Causal handwaving, time as ordering oracle |
| EC-5 | Geometry/coordinates not primitive | Architecture views are derived projections over state | Global coordinate thinking |
| EC-6 | Closure never assumed | Two APIs compose only if explicit contract says they do | Implicit interoperability, magic composition |
| EC-7 | Every claim needs finite witness | Every action needs evidence: receipt, log, diff, hash, test, measurement | "Trust me," unverifiable state |

---

## 8 CS General Principles

| Principle | CS form |
|---|---|
| Bounded execution | Token budgets, iteration caps, timeouts, memory limits |
| Append-only history | Event logs, immutable receipts, write-ahead records |
| Compensation not erasure | Undo is a new event. Compensating transactions, tombstones |
| Locality | Sandboxing, capability grants, namespace boundaries |
| Contract-first execution | Schemas, typed interfaces, validation gates |
| Fail-closed admission | Unknown means deny. Schema-required execution |
| Evidence-backed progress | Receipts, test results, metrics, state hashes |
| Projection not ontology | Dashboards, summaries, caches are materialized views only |

---

## Graph Topology as First Admissible Geometry

Once identity, equality, geometry, causality are not primitive, what remains:
- finite tokens
- finite relations
- ordered composition
- compatibility / incompatibility

That is graph-native. Graph structure comes EARLIER than metric geometry.

Clean chain:
constraints → finite relations → G=(V,E) → paths → cycles → higher topology

Graph topology is the first admissible geometry:
- before metric space
- before coordinates
- before smooth manifold

Hopf/Weyl/QIT geometry is a later richer realization of the same
constraint-topological structure.

---

## Host Architecture Planes (Lev Stack)

| Plane | Role |
|---|---|
| Topology | Allowable regions, graph connectivity, transitions, gates, terminals |
| Orchestration | Loop policies, traversal strategies, retry, phase advancement |
| Dispatch | Executing transforms, sims, reviewers, validators |
| Event Spine | Append-only: witness traces, evidence, step history |

---

## Runtime Kernel Objects

| Object | Definition |
|---|---|
| RuntimeState | region, phaseIndex, phasePeriod, loopScale, boundaries, invariants, dof, context |
| Probe | State-observation operator → Observation (probeId + features) |
| Transform | Ordered state-evolution: apply(state, input) → next_state |
| Witness | Evidence object (positive/negative/counterexample) + trace of StepEvents |
| StepEvent | Single transition record: at, op, beforeHash, afterHash |

---

## Sim Admission Contract

Every sim must declare:
- sim_class
- tier
- required_tools
- required_inputs
- required_outputs
- allowed_claims
- promotion_blockers

Missing anything → fails closed.

---

## Minimum Clean Stack

| Tool | Role |
|---|---|
| networkx | Graph-backed system structure |
| pydantic | Typed schemas |
| jsonschema | Artifact validation |
| z3 | Proof/admissibility gates |
| pytest | Tiered sim contracts |
| hypothesis | Property-based pressure |

Enough to build graph structure, proof gates, sim contracts, fail-closed promotion.

NOTE (2026-04-06): z3 is installed but not directly imported at module level
in the current codebase (pySMT is the abstraction layer; z3 is backend only).
See TOOLING_STATUS.md for current operational classification. This table
describes the TARGET stack, not the current live state.

---

## 6 Enforcement Principles

1. **Claim Gate**: no prose upgrades results. Only artifact class can.
   diagnostic_only cannot support geometry claims.

2. **No Smoothing Rule**: branch conflicts stored as separate branches.
   Open stays open. Dead marked dead. No "best narrative."

3. **Boot Gate**: boots read only decision log, sim registry, artifact
   registry, tranche ledger. Nothing else is boot-authoritative.

4. **Doc Freeze Rule**: docs are reference only. Runtime truth must be
   machine-readable artifacts. Prose cannot be active substrate.

5. **Concrete Principle**: do not trust LLM to follow process. Make
   process executable. Make violations mechanically visible. Make
   unauthorized success impossible.

6. **Minimal v5 Law**: required step → must have artifact. Required
   tool → output present. Incomplete outputs → not promoted. Open
   branch → cannot narratively close.

---

## Layer 0/1/2 Control Governance

### Layer 0: INVARIANTS (never change)

- The system is a constraint-driven ratchet engine. NOT a proof system.
  Like evolution — branches, dead branches. What survives IS the
  attractor basin.
- Two root constraints: FINITUDE + NONCOMMUTATION. Operational, not
  philosophical. Everything else derives from or is killed by them.
- The machine is the product. Ratchet state is disposable. The machine
  that does ratcheting is what matters.
- Implicit is the enemy. Everything explicit or killed. No narrative
  smoothing. No compression without declaration.
- A2 is the user. User inputs are MOST IMPORTANT content.

### Layer 1: ARCHITECTURE (settled, could evolve)

Thread architecture:
[HISTORICAL — see BOOT_PROMPT_TEMPLATES.md and 15_stack_authority_and_capability_index.md for current execution model]
- A2: high-entropy mining, intent preservation, governance. The user.
- A1: strategy + proposal generation. Creates sims AND negative sims.
- A0: deterministic compiler. No interpretation.
- B: canon enforcement. Accept/reject. 14 rules. Python only.
- SIM: terminal execution. Python only. Never LLM. Produces evidence.

Entropy tiers:
- E3 (high): holodeck, Grok/Gemini, apple notes → A2 mines
- E2 (medium): physics fuel → A2 processes, A1 uses with care
- E1 (low): constraint ladder specs → A1's prime fuel
- E0 (very low): bootpacks, canon state → direct reference

Graveyard-first: everything starts DEAD. 306+ entries seeded at init.
Graveyard is the workspace. Survivors earned their way out. 50% ratio
emerges naturally.

Axes math without axis labels: topology and math can be ratcheted
without Jung/IGT/MBTI/I-Ching terms in Thread B. Labels are Rosetta
overlay only.

### Layer 2: DIRECTION (exploratory, not locked)

(Content varies — build order proposals, current priorities, etc.)

---

## Source

Extracted verbatim from:
- system_v5/READ ONLY Reference Docs/CS version of system first draft. .md
- system_v5/READ ONLY Reference Docs/System tools and plan.md
- system_v5/READ ONLY Reference Docs/INTENT_SUMMARY copy.md
