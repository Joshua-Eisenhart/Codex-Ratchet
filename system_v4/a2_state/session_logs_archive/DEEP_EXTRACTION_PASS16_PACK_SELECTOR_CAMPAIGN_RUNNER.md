# Pass 16 — Pack Selector + Entropy Engine Campaign Runner

**Files read this pass:**
- `a1_pack_selector.py` (1577 lines, fully read)  
- `a1_entropy_engine_campaign_runner.py` (1511 lines, fully read)

---

## 1. Pack Selector — Term Admissibility & Strategy Assembly

### Role
Takes cold-core proposals (raw LLM-generated term candidates from `a1_cold_core_strip.py`) and deterministically transforms them into a valid `A1_STRATEGY_v1` by:
1. Resolving cold-core source (run-local sandbox → transient fallback → external path) with SHA256 provenance
2. Filtering terms against canonical set, allowed-terms, graveyard-library exclusions
3. Loading family admissibility hints from A1 state markdown (JSON blocks with `A1_ADMISSIBILITY_HINTS_v1` schema)
4. Applying 5-tier readiness classification
5. Building the full admissibility block with process audit warnings
6. Calling `a1_adaptive_ratchet_planner.build_strategy_from_state()` to generate the actual strategy
7. Attaching admissibility, target_terms, family_terms to the strategy

### 5-Tier Term Readiness Hierarchy (deterministic, no LLM)
| Tier | Field | Meaning |
|------|-------|---------|
| HEAD_READY | `executable_head` | Can drive strategy; promotable |
| COMPANION_FLOOR | `active_companion_floor` | Support terms canonical; witness floor |
| PASSENGER_ONLY | `late_passengers` | Ride along but not ready to lead |
| WITNESS_ONLY | `witness_only_terms` | Support/evidence only; not executable |
| RESIDUE_ONLY | `residue_terms` | Background noise; not actionable |
| (also) PROPOSAL_ONLY | selected terms not in any above | Raw cold-core proposal, unclassified |

### Landing Blockers
`landing_blocker_overrides` from family hints can block specific terms from promotion with explicit messages. If non-head selected terms remain, generic blockers fire: "non-head selected terms still require clearer landing support."

### Negative Marker Classes → Concrete Fields
| Neg Class | Marker Fields |
|-----------|--------------|
| CLASSICAL_TIME | `TIME_PARAM=T` |
| INFINITE_SET | `ASSUME_INFINITE=TRUE`, `INFINITE_SET=TRUE` |
| CONTINUOUS_BATH | `CONTINUOUS_BATH=TRUE` |
| PRIMITIVE_EQUALS | `EQUALS_PRIMITIVE=TRUE`, `ASSUME_IDENTITY_EQUIVALENCE=TRUE` |
| EUCLIDEAN_METRIC | `EUCLIDEAN_METRIC=TRUE`, `CARTESIAN_COORDINATE=TRUE` |
| CLASSICAL_TEMPERATURE | `TEMPERATURE_BATH=TRUE`, `TEMPERATURE_PARAM=K` |
| COMMUTATIVE (default) | `ASSUME_COMMUTATIVE=TRUE` |

### Graveyard Fill Policies
- **anchor_replay**: reuse rescue_terms or canonical anchors (builds failure topology around known terms)
- **fuel_full_load**: prioritize unseen fuel terms, deterministic rotation via `offset = ((seq-1) * block) % len(unseen)` to prevent starvation

---

## 2. Entropy Engine Campaign Runner — Single-Cycle Orchestration

### Role
Executes one complete cycle of the ratchet: `pack → strip → select → packetize → run`. This is the "middle loop" in the 3-loop hierarchy (outer=memo batch driver, middle=campaign runner, inner=a1_a0_b_sim_runner).

### Cycle Pipeline (fully deterministic except autofill content)
1. **lawyer_pack** → generates prompt queue from A2 state fuel
2. **WAITING_FOR_MEMOS** → if roles missing, either autofill or return pending status
3. **cold_core_strip** → distills raw cold-core proposals with min-corroboration threshold
4. **pack_selector** → deterministic strategy assembly (described above)
5. **packetize** → `codex_json_to_a1_strategy_packet_zip.py` creates ZIP protocol packet
6. **runner** → `a1_a0_b_sim_runner.py --a1-source packet --steps 1` executes one A0→B→SIM step
7. **prune** → cleanup sandbox artifacts with 8 configurable retention knobs

### Deterministic Autofill (no LLM required)
Two preset autofill functions that can keep campaigns running unattended:
- `_autofill_entropy_lenses7_memos()`: 6 roles with conservative probe-first claims
- `_autofill_graveyard13_memos()`: 12 roles with optional `adversarial_hard_mode` that injects stronger adversarial content (extra neg classes, explicit fail-class injection)

### 6-Dimensional Memo Quality Gate
Every memo passes through `a1_memo_quality_gate.py` with configurable thresholds:
- `min_overall`: 0.70
- `min_role_compliance`: 0.60
- `min_term_specificity`: 0.50
- `min_negative_class_specificity`: 0.60
- `min_rescue_specificity`: 0.40
- `min_classical_boundary_explicitness`: 0.60

### Debate Strategy: graveyard_then_recovery
The campaign runner has its own debate mode transition logic:
1. Starts in `graveyard_first` for `graveyard_fill_cycles` (default 10)
2. Tracks graveyard delta per cycle
3. If delta < `graveyard_fill_min_delta` for `graveyard_fill_max_stall_cycles`, auto-transitions to `graveyard_recovery` via `force_recovery` flag
4. Also stops if canonical delta exceeds `graveyard_fill_max_canonical_delta` (canonicalizing too fast = not adversarial enough)

### 7 Stop Reasons (all deterministic)
| Status | Trigger |
|--------|---------|
| STOPPED__RUN_SIZE_CAP | run_dir > max_run_mb |
| STOPPED__COLD_CORE_SEQUENCE_MISMATCH | strip or selector sequence != expected |
| STOPPED__PACK_SELECTOR_FAILED | selector subprocess fails |
| STOPPED__LOWER_LOOP_PACKET_FAILED | runner subprocess fails |
| STOPPED__GRAVEYARD_FILL_TOO_WEAK | graveyard delta below threshold (fixed strategy) |
| STOPPED__GRAVEYARD_FILL_CANONICALIZING_TOO_FAST | canonical delta too high during fill |
| STOPPED__RECOVERY_NOT_USING_RESCUE | recovery cycle has too few RESCUE_FROM fields |
| STOPPED__NEG_KILL_DELTA_BELOW_MIN | NEG_* kill count not growing |
| MAX_CYCLES_REACHED | hit --max-cycles |

### Sandbox Hygiene (8 pruning knobs)
Prevents run bloat with configurable retention: prompt_queue(6), lawyer_memos(48), incoming_drop(24), incoming_consumed(48), cold_core(48), outgoing(24), failed_packets(40), external_exchange(72).

---

## 3. JP Determinism Principle Validation

Both files are **exemplary implementations of JP's determinism-first philosophy**:

- **Zero LLM dependency in pack_selector**: all term selection, readiness classification, negative marker mapping, strategy assembly is pure deterministic logic
- **Bounded LLM scoping in campaign_runner**: LLMs only enter through autofill memos (conservative, template-based) or external memo drops (quality-gated through 6 dimensions)
- **Explicit stop conditions**: 7+ deterministic stop reasons prevent runaway behavior
- **Provenance tracking**: SHA256 hashes, sequence numbers, source labels at every handoff point
- **State machine transitions**: graveyard_then_recovery is an explicit FSM with counter-based transitions

The one area where v3 could be more deterministic: `setattr(_cycle_once, ...)` pattern for threading config through function objects is a code smell that could be replaced by explicit config dataclass.

---

## Concepts Extracted

| ID | Concept | Source |
|----|---------|--------|
| P16_01 | 5-tier term readiness: HEAD→COMPANION→PASSENGER→WITNESS→RESIDUE | pack_selector L607-911 |
| P16_02 | landing blocker system prevents premature promotion | pack_selector L757-776 |
| P16_03 | negative marker classes → concrete field/value pairs | pack_selector L993-1010 |
| P16_04 | graveyard fill policies: anchor_replay vs fuel_full_load | pack_selector L1152-1396 |
| P16_05 | deterministic rotation prevents term starvation | pack_selector L1384-1387 |
| P16_06 | pack→strip→select→packetize→run single-cycle pipeline | campaign_runner L585-1157 |
| P16_07 | deterministic autofill (no-LLM) for graveyard13 and entropy_lenses7 | campaign_runner L305-582 |
| P16_08 | adversarial_hard_mode injection (extra neg classes, stronger claims) | campaign_runner L526-564 |
| P16_09 | 6-dimensional memo quality gate | campaign_runner L699-739 |
| P16_10 | graveyard_then_recovery auto-transition via stall detection | campaign_runner L1349-1442 |
| P16_11 | 7 deterministic stop reasons with explicit thresholds | campaign_runner L1421-1478 |
| P16_12 | 8 sandbox pruning knobs for run hygiene | campaign_runner L1099-1120 |
| P16_13 | NEG_KILL stats tracking (count + unique classes) per cycle | campaign_runner L67-78, 1414-1420 |
