---
title: "Core Design: System-Level FlowMinds"
owner: lev-core
status: draft
last_reviewed: 2026-02-20
tags:
  - design
  - architecture
  - flowmind
  - kernel
  - epistemic
design_refs:
  - docs/design/core-flowmind.md
  - docs/specs/spec-kernel.md
  - docs/specs/spec-flowmind.md
  - docs/NORTH_STAR.md
---

# Core Design: System-Level FlowMinds

**Status:** draft
**Effective date:** 2026-02-20
**Role:** Self-governing declarations that sit between the kernel evaluator and userland programs

---

## 1. The Insight

FlowMind is the programmable substrate. The North Star says "everything flows through it."

But *what governs FlowMind itself?*

Not hardcoded logic. Not user workflows. **System-level FlowMind declarations** — immutable programs that the kernel loads at boot and evaluates deterministically. The system governs itself through its own substrate.

This is the architectural layer Josh identified as missing: the "epistemic infrastructure" that sits right above the raw kernel evaluator but below any human-authored program.

```
┌─────────────────────────────────────────────────────┐
│ L4: Userland (Skills, Holodeck, Ratchet Runner)     │  Human-authored, semantic
├─────────────────────────────────────────────────────┤
│ L3: Harness (Shadows, Context Assembly, Proposals)  │  Probabilistic, budget-limited
├─────────────────────────────────────────────────────┤
│ ════════════════════════════════════════════════════ │
│ SYSTEM FLOWMINDS (this document)                    │  Immutable, self-governing
│ ════════════════════════════════════════════════════ │
├─────────────────────────────────────────────────────┤
│ L2: Router (Classifier, Workstream, Event Fanout)   │  Bounded probabilistic
├─────────────────────────────────────────────────────┤
│ L1: Kernel (Constraint Validator, Canonicalizer)    │  Pure deterministic
└─────────────────────────────────────────────────────┘
```

System FlowMinds are not a new layer. They're the **kernel's own programs** — loaded at boot, evaluated by the same engine that evaluates user flows, but with elevated privilege and immutability guarantees.

---

## 2. What Are System FlowMinds?

A System FlowMind is a FlowMind declaration that:

1. **Loads at kernel boot** (not discovered at runtime)
2. **Is immutable once admitted** (ratchet admission gates)
3. **Evaluates deterministically** (no LLM, no randomness, no discretion)
4. **Has kernel-level authority** (can deny, can enforce, can halt)
5. **Emits provenance** (every evaluation is auditable)

They are the system's DNA. Users don't write them. The system evolves them through the ratchet — evidence-driven constraint tightening that only moves forward.

### Analogy

| Concept | Traditional OS | Lev |
|---------|---------------|-----|
| Kernel code | C/assembly | L1 evaluator (TypeScript/Rust) |
| Kernel modules | `.ko` / kext | System FlowMinds (YAML declarations) |
| Syscall table | Function pointers | Kernel FlowMind evaluation context |
| User programs | ELF binaries | L4 Userland FlowMind programs |
| Security policy | SELinux/AppArmor | ABAC Policy FlowMinds |

---

## 3. The Seven System FlowMinds

### 3.1 Constraint Manifold

**Purpose:** Enforces the 5 non-negotiable kernel constraints on every execution.

```yaml
type: system-flowmind
name: constraint-manifold
boot_priority: 0  # First to load
immutable: true

constraints:
  C1_finitude:
    evaluate: |
      plan.policy.max_turns OR plan.policy.max_time_ms MUST be declared.
      Violation: E001_FINITUDE_VIOLATION (FATAL).
    rationale: "No infinite structure allowed."

  C2_non_commutation:
    evaluate: |
      Step dependencies form a DAG. No cycles.
      Execution order is explicit, never assumed.
    rationale: "Order matters. Symmetry cannot be assumed."

  C3_nominalized_reality:
    evaluate: |
      Only validated canonical YAML executes.
      Checksum must match canonical form.
    rationale: "Only what is named and validated is real."

  C4_ratchet:
    evaluate: |
      State transitions are irreversible.
      Rollback requires explicit compensation.
      Append-only audit trail.
    rationale: "The ratchet only tightens."

  C5_locality:
    evaluate: |
      Every step has explicit scope.
      No omniscience. No ambient authority.
    rationale: "Scoped, not global. Earned, not assumed."
```

**Josh's mapping:** This IS the "non-commutative finite epistemic engine." The ontological constraint layer that prevents metaphysical leakage.

---

### 3.2 ABAC Policy Engine

**Purpose:** Attribute-based access control. Deny-by-default. Fail-closed.

```yaml
type: system-flowmind
name: abac-policy-engine
boot_priority: 1
immutable: true

invariants:
  - "If no Policy explicitly allows, DENY"
  - "If Policy cannot be evaluated, DENY"
  - "Every evaluation emits Provenance"
  - "Deny overrides Allow"

evaluation_pipeline:
  - stage: keyword_gate        # Aho-Corasick O(n) pre-filter
  - stage: scope_resolve       # Project | Session | Global
  - stage: archetype_filter    # human-authored | llm-generated | fine-tuned | untrusted
  - stage: policy_evaluate     # All applicable policies
  - stage: default_deny        # No match → DENY
```

**Josh's mapping:** This IS the "adversarial robustness" layer — JP's contribution. Injection resistance, tool isolation, minimal authority. But expressed as *declarative policy*, not hardcoded guards.

---

### 3.3 Provenance Chain

**Purpose:** Hash-chained audit trail. Every decision is replayable.

```yaml
type: system-flowmind
name: provenance-chain
boot_priority: 2
immutable: true

schema:
  event:
    timestamp: ISO-8601
    trace_id: UUID
    action: string          # What was attempted
    context:                # ABAC evaluation context
      archetype: string
      capability: string
      scope: string
    decision: allow | deny
    policies_evaluated: PolicyEvaluation[]
    hash: SHA-256           # Chained to previous event
    ruleset_hash: SHA-256   # Recomputed on admission

storage: append-only JSONL
location: .lev/provenance.jsonl
replay: deterministic       # Same inputs + policies = same outputs
```

**Josh's mapping:** This is the "auditability + replay" layer. Deterministic replay means you can reconstruct exactly why any decision was made. The audit trail IS the training data for world models (TELO cycle).

---

### 3.4 Ratchet Admission

**Purpose:** Controls what declarations can enter the kernel. Once admitted, immutable.

```yaml
type: system-flowmind
name: ratchet-admission
boot_priority: 3
immutable: true

admission_gates:
  - gate: schema_validation
    description: "Declaration must conform to kernel FlowMind schema"
    fail_action: reject

  - gate: term_fence
    description: "No undefined terms. Every reference must resolve."
    fail_action: reject

  - gate: near_duplicate
    description: "Jaccard similarity check against existing declarations"
    threshold: 0.85
    fail_action: warn_and_review

  - gate: immutability_check
    description: "Admitted policies cannot be modified. New version = new admission."
    fail_action: reject

  - gate: regression_check
    description: "New declaration must not weaken existing constraints"
    fail_action: reject

advancement:
  trigger: evidence_threshold  # Not time-based, evidence-based
  direction: forward_only      # Ratchet never loosens
  mechanism: |
    When N successful evaluations of a constraint pattern accumulate
    AND zero violations in the evidence window,
    the constraint MAY be promoted to a tighter bound.
    Promotion is itself a new admission through the same gates.
```

**Josh's mapping:** This is the "automated ratchet advancement" — the system that makes the epistemic OS self-improving. Constraints get tighter based on evidence, never looser. This is what makes it *non-commutative* at the meta-level: the system's own evolution is irreversible.

---

### 3.5 Translator Boundary

**Purpose:** The hard boundary between probabilistic (LLM) and deterministic (kernel).

```yaml
type: system-flowmind
name: translator-boundary
boot_priority: 4
immutable: true

contract: |
  The classifier cascade (T0-T3) produces fuzzy intents with confidence scores.
  The Translator converts these to typed EvaluationContext attributes.
  The kernel NEVER sees confidence scores or raw natural language.
  It pattern-matches deterministically.

pipeline:
  input:  ClassifierOutput   # { intent, entities, confidence, raw_text }
  output: EvaluationContext   # { archetype, capability, scope, command }

  stages:
    - resolve_archetype:     # Who generated this? human | llm | fine-tuned | untrusted
    - resolve_capability:    # What does it want to do? shell-exec | file-write | agent-invoke
    - resolve_scope:         # Where? project | session | global
    - strip_probabilistic:   # Remove confidence, raw text, embedding vectors
    - emit_typed_context:    # Pure deterministic attributes only

boundary_rule: |
  Everything above this line is probabilistic.
  Everything below this line is deterministic.
  The Translator IS the LLM/kernel boundary.
  No inference crosses this line.
```

**Josh's mapping:** This is what Josh called "where the LLM classification layer meets the no-inference constraint layer." The clean cut between epistemic (truth-seeking, probabilistic) and operational (constraint-enforcing, deterministic).

---

### 3.6 Perception Frame

**Purpose:** Structured observation of the runtime environment. Input to TELO cycle.

```yaml
type: system-flowmind
name: perception-frame
boot_priority: 5
immutable: false  # Perception sources are configurable

sources:
  terminal:
    watch: [stdout, stderr]
    pattern: "error|warning|success|fatal"

  filesystem:
    watch: ["**/*.ts", "**/*.yaml", "**/*.md"]
    events: [create, modify, delete]

  kernel_events:
    subscribe: [constraint.violation, policy.deny, ratchet.advance, admission.reject]

  external:
    subscribe: [git.commit, bd.task.update, agent.complete, agent.fail]

assembly:
  frame_rate: 1000ms
  aggregation: sliding_window
  window: 5s
  output: PerceptionFrame  # Structured observation, not raw data

frame_schema:
  timestamp: ISO-8601
  observations:
    terminal: string[]
    file_changes: FileEvent[]
    kernel_events: LevEvent[]
    external_events: LevEvent[]
  summary: string  # One-line human-readable
```

**Josh's mapping:** This is the "data ingestion layer" of the Palantir-class system. But instead of ingesting external data, it ingests the system's own runtime behavior. Self-observation.

---

### 3.7 TELO Cycle

**Purpose:** Trial-Error-Learn-Optimize. The system's learning loop.

```yaml
type: system-flowmind
name: telo-cycle
boot_priority: 6
immutable: false  # Learning parameters are tunable

phases:
  trial:
    description: "Execute a validated proposal in a controlled scope"
    constraint: "Must pass constraint manifold before execution"
    output: ExecutionResult

  error:
    description: "Compare prediction to actual outcome"
    inputs: [Prediction, ExecutionResult]
    output: ErrorSignal
    metric: prediction_confidence - actual_outcome

  learn:
    description: "Update context recipes based on error signal"
    mechanism: |
      Analyze provenance log for patterns.
      Identify context recipes that correlate with success.
      Identify constraint patterns that prevent failure.
      Propose recipe updates (NOT direct model weight updates).
    output: RecipeUpdate

  optimize:
    description: "Improve next prediction accuracy"
    mechanism: |
      Apply recipe updates to context assembly.
      Tighten constraints where evidence supports it.
      Submit constraint tightening through ratchet admission.
    output: OptimizationProposal
    gate: ratchet-admission  # Must pass admission to take effect

training_data:
  source: provenance-chain
  schema: |
    perception -> prediction -> reality -> error -> learning
  storage: append-only JSONL
  replay: deterministic
```

**Josh's mapping:** This is the "simulation / hypothesis layer" AND the "self-stabilizing" mechanism. The system observes itself, predicts outcomes, measures errors, and tightens its own constraints. This is what makes it an epistemic OS rather than just an analytics stack.

---

## 4. Boot Sequence

```
KERNEL BOOT
  │
  ├─ 1. Load constraint-manifold         (priority 0)
  ├─ 2. Load abac-policy-engine          (priority 1)
  ├─ 3. Load provenance-chain            (priority 2)
  ├─ 4. Load ratchet-admission           (priority 3)
  ├─ 5. Load translator-boundary         (priority 4)
  ├─ 6. Load perception-frame            (priority 5)
  ├─ 7. Load telo-cycle                  (priority 6)
  │
  ├─ 8. Validate all system flowminds    (constraint manifold self-check)
  ├─ 9. Verify provenance chain integrity (hash chain validation)
  ├─ 10. Emit KERNEL_READY event
  │
  └─ READY: Accept user-level FlowMind programs
```

**Boot invariant:** If any system FlowMind fails to load, the kernel does not start. Fail-closed at the system level.

---

## 5. Why This Matters (For Josh)

### Two Constraint Systems, One Runtime

Josh identified two orthogonal constraint systems converging:

| Dimension | Ontological (Ratchet) | Operational (JP/Lev) |
|-----------|----------------------|---------------------|
| Root | Finitude + Non-commutation | Heuristics + Containment |
| Enemy | Platonic leakage (implicit assumptions) | Adversarial leakage (prompt injection) |
| Equality | Must be ratcheted (earned, not assumed) | Scoped via leases (earned, not granted) |
| State | Append-only, irreversible | Checkpoint/replay, auditable |
| Model | Formal kernel | Adaptive agent |

**System FlowMinds unify both.** They express ontological constraints (constraint manifold, ratchet admission) AND operational constraints (ABAC policies, translator boundary) in the **same declarative substrate**. The kernel evaluator doesn't care whether a constraint prevents metaphysical leakage or prompt injection — it evaluates them identically.

### The Epistemic OS Stack

```
Layer 4: Automated Ratchet Advancement    (TELO cycle + ratchet admission)
Layer 3: Audit + Replay + Evidence        (provenance chain + perception frame)
Layer 2: Tool-Constrained Execution       (ABAC policy engine + translator boundary)
Layer 1: Heuristic Cognitive Router       (L2 Router + classifier cascade)
Layer 0: Kernel (non-commutative law)     (constraint manifold)
```

This IS the "self-stabilizing epistemic operating system" Josh described. Not a dashboard. Not an agent framework. An OS where:

- **Constraints are declarations, not code** — expressible, composable, auditable
- **The system governs itself** — through its own substrate, not external oversight
- **Evolution is evidence-driven** — ratchet advances on proof, never on assumption
- **Every decision is replayable** — hash-chained provenance from boot to shutdown
- **The LLM/kernel boundary is explicit** — probabilistic above, deterministic below

### What This Is NOT

- Not Palantir (dashboards for humans staring at data)
- Not LangChain (chain-of-LLM-calls with no constraints)
- Not Kubernetes (container orchestration without epistemic guarantees)

**It's closer to:** A formally-constrained reasoning substrate where agents earn capabilities through demonstrated competence, constraints only tighten based on evidence, and the entire system's decision history is deterministically replayable.

---

## 6. Implementation Path

| System FlowMind | Status | Depends On | Priority |
|-----------------|--------|------------|----------|
| constraint-manifold | **Designed** (in plan) | L1 Kernel evaluator | P0 |
| abac-policy-engine | **Designed** (ABAC spec) | constraint-manifold | P0 |
| provenance-chain | **Designed** (ABAC spec) | abac-policy-engine | P0 |
| ratchet-admission | **Designed** (ABAC spec) | provenance-chain | P1 |
| translator-boundary | **Designed** (ABAC spec) | L2 Router, T0-T3 cascade | P1 |
| perception-frame | **Designed** (plan L4) | event-bus, poly | P2 |
| telo-cycle | **Designed** (plan World Models) | perception-frame, provenance-chain | P3 |

**Current kernel implementation** (`core/flowmind/src/kernel/`) contains only validation gates (DoR/DoD). The 5 constraint validators, ABAC evaluator, and provenance chain are designed but not implemented.

**Phase 1 target:** constraint-manifold + abac-policy-engine + provenance-chain in TypeScript.
**Phase 2 target:** Rust port to `crates/lev-kernel/` when interfaces stabilize (2+ weeks unchanged).

---

## 7. Relationship to Existing Docs

| Document | Relationship |
|----------|-------------|
| `docs/design/core-flowmind.md` | Parent — system flowminds are a specialization |
| `docs/specs/spec-kernel.md` | Sibling — kernel evaluates system flowminds |
| `docs/specs/spec-flowmind.md` | Sibling — ABAC + parser-at-tip feed into system flowminds |
| `.lev/pm/plans/flowmind-kernel-comprehensive-2026-01-26.md` | Source — L1-L4 architecture, 5 constraints, TELO |
| `.lev/pm/specs/archived.spec-parser-at-tip-abac.md` | Source — ABAC policy engine, ratchet admission |
| `docs/NORTH_STAR.md` | Alignment — "FlowMind as substrate," "the ratchet only tightens" |

---

*Last validated: 2026-02-20 | Branch: `feat/memory-as-flowmind`*
