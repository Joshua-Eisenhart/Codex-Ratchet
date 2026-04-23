# JP Determinism Principle — Materialized for Lev/Ratchet

> **Core rule**: Entities and lifecycles move deterministically through a graph.
> LLMs/agents do inference tasks only. Determinism is always preferred.

---

## The Principle in One Diagram

```
┌─────────────────────────────────────────────────────┐
│                DETERMINISTIC GRAPH                  │
│                                                     │
│  Entity → State₁ → State₂ → ... → StateN           │
│    ↑         │         │         │                  │
│    │    ┌────▼────┐ ┌──▼──┐  ┌──▼──┐               │
│    │    │  GATE   │ │GATE │  │GATE │               │
│    │    └────┬────┘ └──┬──┘  └──┬──┘               │
│    │         │         │        │                   │
│    └─────────┴─────────┴────────┘                   │
│         All transitions are deterministic.          │
│         Gates check invariants. Fail = reject.      │
│                                                     │
│  ┌──────────────────────────────────────┐           │
│  │  LLM (inference-only side channel)  │           │
│  │  • Generates PROPOSALS              │           │
│  │  • Proposals enter the graph as     │           │
│  │    unverified entities              │           │
│  │  • Must pass ALL gates to advance   │           │
│  │  • LLM never moves an entity       │           │
│  └──────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

---

## Good Examples (from actual code)

### ✅ 1. Ratchet: Autowiggle generates strategies WITHOUT any LLM
**File**: `system_v3/runtime/bootpack_b_kernel_v1/a1_autowiggle.py`

The system generates complete strategies (MATH_DEF → TERM_DEF → CANON_PERMIT → SIM_SPEC) using only deterministic combinatorics. No LLM is contacted. The canonical ascent unit is a fixed template with parameterized slots.

**Why good**: The LLM is not needed for this task. A graph traversal + template expansion produces valid strategies. Determinism is preferred.

### ✅ 2. Ratchet: Model selector PREFERS models that don't need a real LLM
**File**: `system_v3/runtime/bootpack_b_kernel_v1/a1_model_selector.py`

Sort key: `needs_real_llm (prefer FALSE) → id_churn → reject_count → ...`

**Why good**: The system actively ranks away from LLM dependence. If a strategy source works without an LLM, it's scored higher.

### ✅ 3. Lev: Entity lifecycle is a deterministic FSM
**File**: `core/event-machines/src/execution.ts`

States: `ephemeral → captured → classified → crystallizing → crystallized → manifesting → completed`

Transitions are explicit XState machine definitions. The entity moves through the graph deterministically. The LLM might propose a classification, but the FSM enforces which transitions are legal.

**Why good**: The lifecycle IS the graph. The LLM proposes, but deterministic code decides what state an entity can reach.

### ✅ 4. Ratchet: SIM engine runs pure math — zero LLM
**File**: `system_v3/runtime/bootpack_b_kernel_v1/sim_engine.py` (2,397 lines)

30+ quantum information theory probes. Each probe is a Python function that builds matrices, computes eigenvalues, checks positivity, traces, etc. All results are deterministic for the same input.

**Why good**: The hardest computational work in the system uses zero LLM. The LLM's role is limited to proposing WHICH entities to test, not HOW to test them.

### ✅ 5. Lev: DAG scheduling uses Kahn's topological sort
**File**: `core/orchestration/src/graph/dag.ts`

Execution order is deterministic. Parallel ordering is explicit. SHA256 fingerprints verify reproducibility.

**Why good**: The execution graph itself is deterministic. Config resolution is deterministic (4-layer cascade, last wins).

---

## Bad Examples (anti-patterns to avoid)

### ❌ 1. Letting an LLM decide entity state transitions
```python
# BAD: LLM decides whether to promote
response = llm.ask("Should we promote entity X to canonical?")
if "yes" in response.lower():
    entity.state = "CANONICAL"  # LLM moved the entity!
```
```python
# GOOD: Deterministic gate checks evidence
if entity.has_sim_evidence and entity.passes_promotion_gates():
    entity.state = "CANONICAL"  # Graph logic moved the entity
```

### ❌ 2. Using LLM to parse structured artifacts
```python
# BAD: LLM parses export blocks
parsed = llm.ask(f"Parse this export block: {text}")

# GOOD: Regex/deterministic parser
parsed = parse_export_block(text)  # containers.py line 58
```

### ❌ 3. LLM generates execution order
```python
# BAD: Ask LLM what to run next
next_task = llm.ask("What SIM should run next?")

# GOOD: Deterministic dispatcher
plan = sim_dispatcher.build_campaign_plan(state)  # sim_dispatcher.py
```

### ❌ 4. Using LLM for dedup/similarity
```python
# BAD: LLM checks if two concepts are duplicates
is_dup = llm.ask(f"Are '{a}' and '{b}' the same concept?")

# GOOD: Structural digest + Jaccard similarity
is_dup = sha256(a) == sha256(b) or jaccard(a, b) > threshold
```

### ❌ 5. LLM validates its own output
```python
# BAD: Self-validation loop
output = llm.generate(prompt)
valid = llm.ask(f"Is this valid? {output}")  # LLM grading LLM

# GOOD: Deterministic schema validation
result = validate_strategy(output, schema_v2)  # a1_strategy.py
if not result.valid:
    reject(result.errors)
```

---

## Step-by-Step Workflow

When building any new feature for Lev/Ratchet, follow this sequence:

### Step 1: Define the Entity and Its States
What thing moves through the system? What are its valid states?
```
Example: A "concept" entity with states:
  SOURCE_CLAIM → CROSS_VALIDATED → STRIPPED → RATCHETED
```
This is a graph. It must be deterministic. Draw it first.

### Step 2: Define the Transitions and Gates
What causes an entity to move between states? What invariants must hold?
```
Example: SOURCE_CLAIM → CROSS_VALIDATED requires:
  - ≥2 independent source documents
  - No unresolved contradictions at the same trust zone
  - Structural digest must differ from all existing CROSS_VALIDATED entities
```
Each gate is deterministic code. No LLM.

### Step 3: Identify Where Inference Is Actually Needed
Only after steps 1-2 are complete, ask: "Where does a human or LLM need to make a judgment that can't be reduced to a rule?"

Typical inference points:
- **Concept extraction** from raw text → LLM reads a doc, proposes concepts
- **Similarity judgment** when structural dedup is ambiguous → LLM breaks ties
- **Strategy proposal** when autowiggle exhausts its template space → LLM proposes new angles

### Step 4: Quarantine All LLM Output
Every LLM output enters the graph as an **unverified entity at the lowest trust zone**. 

```python
# LLM output enters as SOURCE_CLAIM at A2_HIGH_INTAKE
concept = llm.extract_concept(document)
refinery.ingest_document(doc, concepts=[concept])  # Goes to A2_3_INTAKE
# Must pass ALL gates to advance — LLM cannot self-promote
```

### Step 5: Build the Deterministic Pipeline First
Before adding any LLM integration, build and test the full pipeline with synthetic/deterministic inputs:
```
1. Write the FSM (entity states + transitions)
2. Write the gates (invariant checks)  
3. Write the dispatcher (what runs next — deterministic ordering)
4. Write the evidence engine (pure computation — matrices, hashes, etc.)
5. Test with autowiggle/replay (no LLM needed)
6. ONLY THEN add LLM as an optional input source
```

### Step 6: Make LLM Optional, Not Required
The system must be able to run — at reduced capacity — with LLM=off.
- Ratchet does this: autowiggle + replay = full pipeline, no LLM
- Lev does this: FlowMind topology compiles deterministically, LLM is dispatch-layer optional

### Step 7: Contradictions Are Fuel, Not Errors
At A2/A1 layers, contradictions between concepts are **wanted**. They create thermodynamic heat that drives refinement. Only the B+SIM ratchet resolves contradictions by checking which side passes the evidence ladder.

```
A2 layer: "Concept A says X, Concept B says not-X" → BOTH survive
B+SIM layer: Run probes on both → one passes, one gets killed → graveyard
```

---

## Checklist for Every New Feature

- [ ] Entity and states defined as a graph/FSM
- [ ] All transitions have deterministic gate conditions
- [ ] LLM is used ONLY for inference (extraction, proposal, judgment)
- [ ] LLM output enters at lowest trust zone
- [ ] Pipeline runs without LLM (reduced capacity is OK)
- [ ] Contradictions preserved at A2/A1 (not prematurely resolved)
- [ ] Evidence is computational, not LLM-generated
- [ ] Dedup uses structural hashing, not LLM similarity
- [ ] Execution order is deterministic (topological sort, not LLM choice)
- [ ] All artifacts are content-addressed (SHA256) for reproducibility
