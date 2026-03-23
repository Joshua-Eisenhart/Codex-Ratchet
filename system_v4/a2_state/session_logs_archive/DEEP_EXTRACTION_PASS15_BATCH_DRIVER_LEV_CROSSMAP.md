# Pass 15 — Memo Batch Driver + Planner Tail + Lev OS Cross-Map

**Files read this pass:**
- `a1_adaptive_ratchet_planner.py` lines 2400-2954 (planner tail, graveyard_first/graveyard_recovery, rescue scaffold, full strategy assembly)
- `a1_external_memo_batch_driver.py` (2984 lines, fully read)
- `jp lev web outputs.txt` (698 lines, Lev architecture deep map)
- `lev_nonclassical_runtime_design_audited.md` (first 800 of 2500 lines, shared runtime kernel)

---

## 1. Planner Tail (lines 2400-2954)

### Graveyard-First Widens Kill Surface
When `debate_mode == "graveyard_first"`, the planner **intentionally widens adversarial lanes** to create a dense kill surface before recovery begins. Extra negative items are spawned per-class from `_graveyard_negative_classes_for_mode()`, each parented to the primary adversarial neg ID. Each gets its own evidence token, probe, and marker fields.

### Graveyard-Recovery Consumes Kills as Rescue Attempts
When `debate_mode == "graveyard_recovery"`, the planner pulls `_recent_kill_context(state)` and spawns rescue SIM specs per kill across three families:
- **BOUNDARY_SWEEP** → `OP_REPAIR_DEF_FIELD` 
- **PERTURBATION** → `OP_MUTATE_LEXEME`
- **COMPOSITION_STRESS** → `OP_REORDER_DEPENDENCIES`

Each rescue carries `RESCUE_MODE: GRAVEYARD_RECOVERY`, `RESCUE_FROM: source_id`, `RESCUE_TOKEN`, and linkage string `GRAVEYARD::{source}::{family}::{idx}`.

### Scaffold Rescue Attachment
When `family_slice` provides required `RESCUER` lanes that aren't met by existing rescue items, the planner scaffolds additional rescue specs. Each scaffold carries `RESCUE_MODE: SCAFFOLD_ATTACHMENT` and links to expected failure modes from the family slice.

### Strategy Assembly (the final shape)
The full strategy is: `prereq_items + target_items` = targets, `negative_items` = alternatives. The strategy dict has schema `A1_STRATEGY_v1`, with `self_audit` containing 50+ diagnostic fields: lane branch counts, sim family maps, operator policy sources, rescue linkages. The strategy hash = SHA256 of canonicalized strategy bytes.

### CLI: 3 Debate Modes + 7 Goal Profiles
`--debate-mode`: balanced / graveyard_first / graveyard_recovery  
`--goal-profile`: core / extended / physics / toolkit / refined_fuel / entropy_bridge / entropy_bookkeeping_bridge

---

## 2. External Memo Batch Driver (Full File)

### Architecture: Deterministic Orchestrator with Bounded LLM Inference

This is the **outermost loop** of the ratchet system — a ~3000-line deterministic state machine that coordinates the entire lifecycle, calling LLMs only through bounded memo roles.

### 12 Debate Roles (LLM Inference Scopes)
| Role | Neg Classes | Purpose |
|------|-------------|---------|
| STEELMAN_CORE | COMMUTATIVE, CLASSICAL_TIME | Build strongest substrate first |
| STEELMAN_ALT_FORMALISM | COMMUTATIVE, INFINITE_SET | Alternate formal path |
| DEVIL_CLASSICAL_TIME | CLASSICAL_TIME | Adversarial smuggling, expected to die |
| DEVIL_COMMUTATIVE | COMMUTATIVE | Expected to die |
| DEVIL_CONTINUUM | CONTINUOUS_BATH, INFINITE_SET, etc | Expected to die |
| DEVIL_EQUALS_SMUGGLE | COMMUTATIVE, INFINITE_SET, PRIMITIVE_EQUALS | Expected to die |
| BOUNDARY_REPAIR | COMMUTATIVE, CLASSICAL_TIME | Boundary perturbations with rescue ancestry |
| RESCUER_MINIMAL_EDIT | COMMUTATIVE, CLASSICAL_TIME | Minimal-edit rescues |
| RESCUER_OPERATOR_REFACTOR | COMMUTATIVE, CLASSICAL_TIME | Operator-level refactors |
| ENTROPY_LENS_VN | CLASSICAL_TIME, CONTINUOUS_BATH | Von Neumann entropy lens |
| ENTROPY_LENS_MUTUAL | COMMUTATIVE, CLASSICAL_TIME | Mutual information lens |
| ENGINE_LENS_SZILARD_CARNOT | CONTINUOUS_BATH, CLASSICAL_TIME, INFINITE_SET, CLASSICAL_TEMPERATURE | Engine cycle lens |

### concept_path_rescue: 3-Phase Deterministic Lifecycle
1. **graveyard_seed** — debate_mode=graveyard_first, forbid rescue, broad terms. Transitions when seed_target_terms all appear in graveyard AND fuel/library coverage met.
2. **path_build** — debate_mode=graveyard_first, forbid rescue, focused terms. Transitions when rescue_prereqs met (min_canonical >= 25, min_graveyard >= 80, min_kill_diversity >= 5) AND path_build_max_cycles reached OR novelty stalled.
3. **rescue** — debate_mode=graveyard_recovery, allow rescue, narrow terms. Terminates on rescue_novelty_stall_max or goal reached.

### Phase Transition Triggers (All Deterministic)
- `concept_in_graveyard`: all seed_target_terms must appear in graveyard_terms
- `fuel_coverage`: graveyard must cover fuel_term_set at target ratio
- `library_coverage`: graveyard must cover library_term_set at target ratio
- `rescue_prereqs`: canonical >= 25, graveyard >= 80, kill_diversity >= 5
- `novelty_stall`: unique_structural_digest_count stops increasing
- `goal_reached`: canonical >= 35, graveyard >= 45, sim_registry >= 450

### Rescue Stall Adaptation
When `rescue_novelty_stall` increases, the deterministic rotating subset parameters adapt:
- stall >= 2: `keep_head_terms` shrinks to 1
- stall >= 4: `rotate_width` expands to 3
- stall >= 8: `keep_head` drops to 0, width expands to 4

This forces diversity when the system gets stuck.

### Bootstrap Stall Detection
`_bootstrap_stalled_terms()` scans recent cold_core proposals for repeated identical `need_atomic_bootstrap` patterns. Stalled terms get filtered out and replaced with decomposition support terms (`DECOMPOSITION_SUPPORT_MAP`) and witness activation support terms (`WITNESS_ACTIVATION_SUPPORT_MAP`).

### Two Provider Modes
- **template** — local memo generation via `_write_memos_for_cycle()`, quality-gated by `a1_memo_quality_gate.py`
- **exchange** — external provider integration via request→subprocess→response→ingest→prepack pipeline, with configurable timeout and stub detection

### Post-Run Audits
After the main loop, runs two deterministic audits:
- `run_a1_operational_integrity_audit.py`
- `run_a1_semantic_and_math_substance_gate.py`

---

## 3. Lev OS Architecture Cross-Map

### JP's Core Philosophy (stated directly)
> "Entities and lifecycles move deterministically through a graph. LLMs/agents do inference tasks only. Determinism is always preferred."

### Lev OS Architecture Summary
Lev separates execution into **four planes**:
1. **Policy Plane** (FlowMind) — declarations, constraints, compile/runtime policy
2. **Execution Plane** (Orchestration) — scheduling, DAG traversal, loop control, budget
3. **Dispatch Plane** (A2A) — who executes each step, concurrency, timeout
4. **Event Spine** — append-only LevEvent JSONL, 67+ event types, full replay/recovery

### Three Nested Loop Scales (maps to ratchet loops)
| Lev Loop | Mechanism | Ratchet Equivalent |
|----------|-----------|-------------------|
| Outer (heartbeat) | `runHeartbeat()` with adaptive interval | `concept_path_rescue` outer loop in memo batch driver |
| Middle (orchestration) | `lev loop` discover→validate→promote→budget | `a1_entropy_engine_campaign_runner.py` cycle loop |
| Inner (Tick) | INGEST→OBSERVE→PROPOSE→GATE→APPLY→UPDATE→EMIT | Single A0→B→SIM forward+backward step |

### Entity Lifecycle (maps to term lifecycle)
| Lev Phase | Ratchet Equivalent |
|-----------|-------------------|
| ephemeral | New term enters term_registry |
| captured | Term admitted to survivor_ledger |
| classified | Term gets SIM evidence |
| crystallizing | Term passes probes, approaches canonical |
| crystallized | Term achieves CANONICAL_ALLOWED |
| manifesting | Term participates in master conjunction |
| completed | Full conjunction validated |
| **graveyard** | Term killed by adversarial sim (Lev: "failed" state) |

### CDO Properties (CSS for agent graphs)
Lev uses **Cognitive Dataflow Orchestration** properties as composable overlays — same graph gets different traversal strategies. This maps to the ratchet's `family_slice` system: overlays that control debate_mode, lane requirements, sim tier defaults, and rescue policies without changing the core planner logic.

### Key Lev Patterns Already in Ratchet
| Lev Pattern | Ratchet Implementation | Status |
|-------------|----------------------|--------|
| Deterministic entity lifecycle | KernelState survivor/graveyard/park | Implemented |
| Event-sourced state | kill_log, evidence_tokens, canonical_ledger | Implemented |
| Topology/orchestration/dispatch | A0 compiler / a1_a0_b_sim_runner / sim_dispatcher | Implemented |
| 7 loop exit ramps | goal_reached, rescue_novelty_stall, max_cycles, budget | Implemented |
| Multi-view council (5 roles) | 12 debate roles (STEELMAN/DEVIL/BOUNDARY/RESCUER/LENS) | Implemented |
| Quality gates at every boundary | memo_quality_gate, operational_integrity_audit | Implemented |
| Bounded LLM inference | External memo exchange protocol | Implemented |

### Key Lev Patterns NOT Yet in Ratchet (v4 opportunity)
| Lev Pattern | Gap in v3 |
|-------------|-----------|
| XState FSMs (explicit state machines) | v3 uses implicit conditional logic, not formal FSMs |
| Compile-time determinism (SHA256 topology fingerprints) | v3 hashes strategies but not topology itself |
| A2A universal dispatch (pluggable executors) | v3 hardcodes subprocess calls |
| Progressive execution (pause/resume/inspect) | v3 resumes from checkpoint but can't pause mid-step |
| Fractal config (system→project→module→env) | v3 uses flat CLI args |
| CDO overlays (behavior overlays separate from topology) | v3 uses `family_slice` but it's embedded in planner, not a separate concern |

---

## 4. JP's Determinism Principle Applied to Ratchet

### Good Examples (v3 already follows the principle)
1. **Planner** — `a1_adaptive_ratchet_planner.py` is fully deterministic. Given state + goals + family_slice, it produces exactly one strategy. No LLM involved.
2. **Phase transitions** — graveyard_seed→path_build→rescue transitions are pure threshold logic on canonical_count, graveyard_count, kill_diversity. No inference.
3. **Rescue rotation** — `_deterministic_rotating_term_subset()` and `_deterministic_rotating_rescue_target_subset()` use modular arithmetic on sequence number. Perfectly deterministic.
4. **Strategy assembly** — target_items + negative_items assembled from pure logic on working_goal, SIM families, and operator mappings.

### Bad Examples (where v3 leaks non-determinism)
1. **Memo content** — LLM-generated memo text is unconstrained prose. Only scoped by role claims/risks, not by structural contract.
2. **External provider response format** — `_ingest_exchange_response()` accepts arbitrary JSON dicts from LLM providers with minimal schema enforcement.
3. **Bootstrap companion term selection** — `_fallback_decomposition_support_terms()` uses hardcoded lookup maps rather than deriving support from the graph itself.

### Step 1-N Workflow (applying JP's principle materially)
1. **Define entity schemas** — Every entity (term, kill, rescue, memo, evidence, strategy) gets a formal TypeScript type or Zod schema
2. **Define lifecycle FSMs** — Each entity type gets explicit XState-style state machine (ephemeral→admitted→probed→canonical→graveyard)
3. **Define graph edges** — Valid transitions encoded as topology (.flow.yaml equivalent), not conditional logic
4. **Scope LLM to inference only** — LLM gets: role + claims + terms + constraints → returns: structured memo matching schema. No lifecycle control.
5. **Add deterministic gates** — Every LLM output passes through structural validation before entering the deterministic pipeline
6. **Separate CDO-style overlays** — family_slice logic becomes a composable overlay system separate from the planner core
7. **Add compile-time fingerprints** — Hash the topology + overlay combination at compile time for reproducibility

---

## Concepts Extracted

| ID | Concept | Source |
|----|---------|--------|
| P15_01 | graveyard_first widens adversarial lanes for dense kill surface | planner L2452-2498 |
| P15_02 | graveyard_recovery spawns rescue from recent kills across 3 families | planner L2500-2647 |
| P15_03 | scaffold rescue attachment fills required RESCUER lanes | planner L2649-2731 |
| P15_04 | concept_path_rescue 3-phase lifecycle (seed→build→rescue) | batch_driver L2237-2290 |
| P15_05 | rescue stall adaptation: widening rotation as novelty stalls | batch_driver L2539-2548 |
| P15_06 | bootstrap stall detection with decomposition/witness fallbacks | batch_driver L2550-2604 |
| P15_07 | JP's determinism-first: entities graph-traverse, LLMs inference-only | JP direct instruction |
| P15_08 | Lev topology/orchestration/dispatch maps to A0 compiler / runner / sim_dispatcher | lev_outputs cross-map |
| P15_09 | Lev 3 loop scales map to ratchet outer/middle/inner loops | lev_outputs cross-map |
| P15_10 | Lev entity lifecycle maps to ratchet term lifecycle | lev_outputs cross-map |
| P15_11 | CDO overlays (separation of behavior from topology) = v4 opportunity | lev_nonclassical L1-800 |
| P15_12 | Shared runtime kernel: RuntimeState + Probe + Transform + Witness types | lev_nonclassical L376-463 |
| P15_13 | Finitude + non-commutation as root runtime constraints | lev_nonclassical L256-292 |
| P15_14 | probe-relative equivalence (not primitive equality) | lev_nonclassical L446-462 |
| P15_15 | v4 gap: XState FSMs, compile-time fingerprints, A2A dispatch, fractal config | cross-map analysis |
