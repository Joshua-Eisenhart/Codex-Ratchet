# Pass 19 — Complete v3 Tools Pipeline (Wave 4: 9 Files)

**Files read this pass:**
- `a1_exchange_serial_runner.py` (479 lines)
- `a1_memo_quality_gate.py` (243 lines)
- `a1_cold_core_strip.py` (484 lines)
- `a1_lawyer_pack.py` (430 lines)
- `a1_lawyer_sink.py` (194 lines)
- `codex_json_to_a1_strategy_packet_zip.py` (128 lines)
- `a1_request_to_codex_prompt.py` (475 lines)
- `a1_selector_warning_snapshot.py` (343 lines)
- `bootstrap_seeded_continuation_run.py` (241 lines)

---

## 1. Exchange Serial Runner — Local Stub Loop

Wraps the memo batch driver in a serial request/response loop. When the driver stops with `WAITING_FOR_MEMOS`, it auto-generates deterministic local stub responses:
- Reads unanswered `A1_EXTERNAL_MEMO_REQUEST__*.json` from `a1_sandbox/external_memo_exchange/requests/`
- Generates `A1_EXTERNAL_MEMO_RESPONSE_v1` with `_build_memo()` using augmented term lists
- Replay stall detection: if a 2nd loop produces zero executed cycles after consuming existing responses, it errors
- Emits `A1_EXCHANGE_SERIAL_RUNNER_REPORT_v1` with full timeline

---

## 2. Memo Quality Gate — Weighted 5-Dimension Scoring

**Pure deterministic quality filter — zero LLM.**

| Dimension | Weight | Scoring Logic |
|-----------|--------|---------------|
| role_compliance | 30% | claims + risks + valid neg classes + role-expected negs + DEVIL_ adversarial keywords |
| term_specificity | 20% | unique valid terms / target (4-12 depending on focus_term_mode) |
| negative_class_specificity | 20% | valid/total ratio × diversity bonus (≥2 unique = 1.0, else 0.8) |
| classical_boundary_explicitness | 20% | markers in neg classes + text keywords (≥3 = 1.0, 2 = 0.8, 1 = 0.5) |
| rescue_specificity | 10% | RESCUER/BOUNDARY roles need targets; others get 1.0 |

### 8 Valid Negative Classes (canonical set)
COMMUTATIVE_ASSUMPTION, CLASSICAL_TIME, CONTINUOUS_BATH, INFINITE_SET, INFINITE_RESOLUTION, PRIMITIVE_EQUALS, EUCLIDEAN_METRIC, CLASSICAL_TEMPERATURE

### 7 Role→Expected Negative Mappings
DEVIL_CLASSICAL_TIME → {CLASSICAL_TIME}, DEVIL_COMMUTATIVE → {COMMUTATIVE_ASSUMPTION}, DEVIL_CONTINUUM → {CONTINUOUS_BATH, INFINITE_SET, INFINITE_RESOLUTION, EUCLIDEAN_METRIC}, etc.

---

## 3. Cold Core Strip — Memo→Proposals Transform

Extracts ratchet-safe tokens from lawyer memos into `A1_COLD_CORE_PROPOSALS_v1`:
- **Corroboration threshold** (`min_corroboration`, default 2): terms must appear in ≥N memos to be admissible
- **Compound term decomposition**: splits `foo_bar_baz` → checks if all components are canonical/L0
- **Atomic bootstrap tracking**: records which new atoms need T0 bootstrap
- **Hard cap**: compounds requiring >6 new atomics are rejected
- **Mining witness integration**: accepts `EXPORT_CANDIDATE_PACK_v1` and `FUEL_DIGEST_v1` as support-side evidence
- **Rescue target fallback**: if memos provide no rescue hints, falls back to recent kills (last 16)
- **SHA256 provenance**: cold core proposals are hash-stamped

---

## 4. Lawyer Pack — Role-Based Prompt Assembly

Emits sequential role prompts into the A1 sandbox. 6 preset configurations:
- **lawyer4** (4 roles): STEELMAN → DEVIL → BOUNDARY → PACK_SELECTOR
- **entropy_lenses7** (7 roles): LENS_VN → LENS_MUTUAL_INFO → LENS_CONDITIONAL → LENS_THERMO_ANALOGY → DEVIL_CLASSICAL_SMUGGLER → RESCUER → PACK_SELECTOR
- **graveyard13** (13 roles): 2 steelmen + 4 devils + BOUNDARY_REPAIR + 2 rescuers + 2 entropy lenses + ENGINE_LENS + PACK_SELECTOR
- **substrate5** (6 roles): core substrate focused
- **mass_wiggle_1000** / **attractor_wiggle_1000** (5 mass roles): ≥400 steelman + ≥250 adversarial + ≥200 rescue + ≥150 alt formalism + PACK_SELECTOR with BRANCH_TRACK requirements

Context sharding: base prompt split into 64KB / 2000-line chunks for MEGABOOT compatibility.

---

## 5. Lawyer Sink — Memo/Strategy Ingestion

Validates and routes incoming JSON:
- **Memos** → `work/a1_transient_lawyer/{run_id}/lawyer_memos/`
- **Strategies** → `a1_sandbox/outgoing/` (clears stale strategies first)
- **Strategy substance validation**: every alternative must have `BRANCH_TRACK` DEF_FIELD with one of 6 exact tokens, ≥4 tracks used, ≥20 candidates per track

### 6 Required BRANCH_TRACK Tokens
TRACK_IGT_TYPE1_ENGINE, TRACK_IGT_TYPE2_ENGINE, TRACK_AXIS0_PERTURBATION, TRACK_CONSTRAINT_LADDER, TRACK_PHYSICS_OVERLAY_OPERATORIZATION, TRACK_GRAVEYARD_RESCUE

---

## 6. Strategy Packet ZIP Writer

Wraps validated `A1_STRATEGY_v1` into `{seq}_A1_TO_A0_STRATEGY_ZIP.zip` via `zip_protocol_v2_writer`. Placed in `a1_inbox/` for runtime consumption. Sequence tracked independently from runtime ZIP journal.

---

## 7. Request-to-Codex Prompt — Deterministic Context Builder

Builds the full deterministic prompt for A1 LLM consumption:
- **Run context**: run_id, step, state_hash, next_inbox_sequence, last_reject_tags
- **Term surfaces**: canonical terms, L0 lexemes, derived-only terms
- **Graveyard surface**: recent kills (last 8) + parked items (last 8)
- **Fuel docs**: prioritized A2 surfaces first (system understanding, term conflicts, distillation inputs, brain slice), then fuel docs from `core_docs/a1_refined_Ratchet Fuel/` with 64KB max per doc
- **Rosetta index**: full rosetta.json embedded
- **A1 brain tail**: last 12 events from `a1_brain.jsonl` (bounded to 24KB)
- **Wiggle profiles**: micro5 (1 target + 4 alternatives, strict) vs mass1000 (follow role prompt quotas)

### Jargon Quarantine Rule
Jargon/labels/metaphors ONLY allowed in LABEL_DEF items (TERM → LABEL mapping); MATH_DEF/TERM_DEF/CANON_PERMIT/SIM_SPEC DEF_FIELD values must use only L0 lexemes or canonical terms.

---

## 8. Selector Warning Snapshot — Warning Categorization

Shared library consumed by all tools for structured warning handling:
- **10+ warning codes**: minimum_content_incomplete, movement_over_throughput_failed, evidence_gated_promotion_failed, sim_boundary_weak, sim_evidence_not_hash_anchored, transient_cold_core_fallback, external_cold_core_path, cold_core_basename_sequence_mismatch, target_scope_family_context_split, noncanon_mining_support_only
- **Warning categories**: content_shape, content_balance, promotion_boundary, sim_boundary, sim_provenance, cold_core_provenance, cold_core_sequence, scope_boundary, support_boundary
- **Priority ordering**: cold_core_sequence (0) > cold_core_provenance (1) > support_boundary (2) > scope_boundary (3) > other (4)

---

## 9. Bootstrap Seeded Continuation — Run Forking

Creates a clean continuation run from an existing one:
- **Preserves**: state.json, state.heavy.json, sequence_state.json (lower-loop state)
- **Resets**: a1_inbox, a1_sandbox (all 9 subdirs), reports, b_reports, sim, tapes, zip_packets, logs
- **Driver phase state**: compacts the driver report to last timeline entry with stall counters zeroed
- **SHA256 verification**: produces state.json.sha256 for integrity check

---

## Complete v3 Pipeline Data Flow

```
a1_request_to_codex_prompt.py (fuel + context)
       ↓
a1_lawyer_pack.py (role prompts + sharded context)
       ↓
a1_llm_lane_driver.py (ZIP request → host LLM → ZIP response)
       ↓
a1_lawyer_sink.py (validate + route memos/strategies)
       ↓
a1_cold_core_strip.py (corroborate + extract proposals)
       ↓
a1_pack_selector.py (term readiness → strategy assembly)
       ↓
codex_json_to_a1_strategy_packet_zip.py (ZIP packet)
       ↓
a0_b_sim_runner.py (runtime consumption)
       ↓
a1_memo_quality_gate.py (quality verification)
       ↓
run_a1_autoratchet_cycle_audit.py (structural verification)
```

**Parallel orchestration paths:**
- `a1_external_memo_batch_driver.py` → drives the cycle+exchange loop
- `a1_exchange_serial_runner.py` → wraps driver with local stub responses
- `a1_entropy_engine_campaign_runner.py` → wraps with autofill memos
- `run_graveyard_first_validity_campaign.py` → wraps with profile presets
- `run_a1_consolidation_prepack_job.py` → multi-worker merger

**Run management:**
- `bootstrap_seeded_continuation_run.py` → fork runs preserving state

---

## Concepts Extracted

| ID | Concept | Source |
|----|---------|--------|
| P19_01 | Exchange serial runner local stub loop | serial_runner L92-137 |
| P19_02 | 5-dimension weighted memo quality scoring | quality_gate L190-203 |
| P19_03 | 8 valid negative classes (canonical set) | quality_gate L10-19 |
| P19_04 | Cold core corroboration threshold (≥2 memos) | cold_core L376-393 |
| P19_05 | Compound term decomposition + atomic bootstrap tracking | cold_core L394-419 |
| P19_06 | 6 preset role orders (lawyer4→attractor_wiggle_1000) | lawyer_pack L20-143 |
| P19_07 | Context sharding (64KB/2000 lines) for MEGABOOT | lawyer_pack L235-281 |
| P19_08 | 6 BRANCH_TRACK tokens as strategy substance gates | lawyer_sink L68-75 |
| P19_09 | Jargon quarantine: LABEL_DEF only for human labels | request_prompt L387-394 |
| P19_10 | Fuel prioritization: A2 surfaces first, then core_docs | request_prompt L159-188 |
| P19_11 | Warning priority ordering (sequence > provenance > support > scope) | warning_snapshot L166-181 |
| P19_12 | Bootstrap preserves lower-loop state, resets A1 surfaces | bootstrap L136-148 |
