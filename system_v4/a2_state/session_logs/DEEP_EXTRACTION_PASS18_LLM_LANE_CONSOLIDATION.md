# Pass 18 — LLM Lane Driver + Consolidation Prepack

**Files read this pass:**
- `a1_llm_lane_driver.py` (709 lines, fully read)
- `run_a1_consolidation_prepack_job.py` (709 lines, fully read)

---

## 1. LLM Lane Driver — Fail-Closed External LLM Interface

### Role
The **only place in v3 where an external LLM surface is expected to interact**. It packages ratchet prompts into a ZIP request artifact that an operator drops into a ChatGPT Pro / Codex chat session, then ingests the role output JSONs back.

### Key Design: LLM is an External File-Based Subagent
- The "LLM" is **not** an API call — it's a process executed inside a host LLM surface using ZIP request/return artifacts
- The driver **never** falls back to deterministic autofill or deterministic pack selection
- Exit code 2 = "I need host LLM outputs, stop until provided"
- Exit code 0 = "I consumed outputs and advanced one step"

### ZIP Request Artifact Structure
```
{sequence}__A1_LLM_LANE_REQUEST__v1.zip
├── COMBINED_PROMPT__A1_LLM_LANE__v1.md
├── README__HOW_TO_RUN.txt
├── MANIFEST.json (A1_LLM_LANE_REQUEST_v1 schema)
├── context/ (sharded base prompt .md files)
└── prompts/ (*_A1_PROMPT.txt files)
```

Expected return: ZIP containing `role_outputs/*.json` (one JSON per prompt .txt)

### Inbox Quarantine System
Quarantines out-of-sequence A1 strategy packets to maintain contiguous sequence consumption:
- Reads `a1_inbox/sequence_state.json` for last consumed sequence
- Keeps only contiguous prefix starting at expected next sequence
- Moves gaps to `a1_inbox/quarantine/` with README explaining why

### Autogen Mode (Smoke Tests Only)
`--autogen` flag generates role outputs locally via `a1_autogen_role_outputs_attractor.py` — for testing the pipeline without external LLM. Still fail-closed on errors.

---

## 2. Consolidation Prepack — Multi-Worker Output Merger

### Role
Takes **many** A1 worker outputs (memos from different LLM sessions, external responses, or direct strategies) and consolidates them into **one** deterministic pre-A0 strategy through the standard pipeline.

### Input Modes
1. **memo_consolidation**: Multiple `A1_LAWYER_MEMO_v1` and/or `A1_EXTERNAL_MEMO_RESPONSE_v1` → sink → cold_core_strip → pack_selector
2. **direct_strategy_passthrough**: Single `A1_STRATEGY_v1` → validate → pass through (no merging of multiple strategies — fail closed)

### Input Collection
Accepts JSON files, ZIP bundles, or directories (recursively). Deduplicates by resolved path. Refuses mixed memo + strategy inputs.

### External Memo Response Expansion
`A1_EXTERNAL_MEMO_RESPONSE_v1` contains a `memos` array. Each memo is:
- Stamped with `A1_LAWYER_MEMO_v1` schema
- Tagged with run_id and sequence
- Role uppercased
- Sanitized against `--allowed-terms` filter (proposed_terms clamped, rescue targets clamped)

### Allowed-Terms Sanitization
When `--allowed-terms` is set:
- `proposed_terms` filtered to only allowed terms
- `graveyard_rescue_targets` filtered using TARGET_ID_TERM_SUFFIX regex → extracted term must be in allowed set

### Pipeline (deterministic)
1. Expand external memo responses into individual memos
2. Stamp all memos with run_id + sequence
3. Ingest each via `a1_lawyer_sink.py`
4. Strip to cold core via `a1_cold_core_strip.py`
5. Route through `a1_pack_selector.py` with full config propagation
6. Emit `A1_CONSOLIDATION_PREPACK_RESULT_v1` + markdown report

### Sequence Management
Uses `a1_sandbox/sequence_counter.json` for deterministic monotone sequence tracking. Supports explicit sequence override.

---

## 3. JP Determinism Principle Assessment

### LLM Lane Driver
This is the **cleanest example of JP's principle** in v3:
- LLM interaction is **file-based, asynchronous, external** — not embedded in the pipeline
- The driver deterministically prepares the request and deterministically ingests the response
- The LLM's only job is inference (generate role output JSONs matching a strict contract)
- Everything else — sequencing, quarantine, validation, packetization — is deterministic
- **Exactly matches JP's philosophy: "LLMs do inference tasks only. Determinism is always preferred."**

### Consolidation Prepack
- Zero LLM — takes already-generated outputs and merges them deterministically
- Sanitization of terms against allowlist is pure set filtering
- Fail-closed on mixed inputs, multiple strategies, sequence mismatches

---

## Concepts Extracted

| ID | Concept | Source |
|----|---------|--------|
| P18_01 | LLM as external file-based subagent, not API call | llm_lane L3-28 |
| P18_02 | ZIP request/return artifact protocol for host LLM surface | llm_lane L164-279 |
| P18_03 | Inbox quarantine system for sequence integrity | llm_lane L286-367 |
| P18_04 | Fail-closed exits: 2 = needs LLM, 0 = step consumed | llm_lane L703-704 |
| P18_05 | Multi-worker output consolidation pipeline | prepack L348-354 |
| P18_06 | External memo response expansion into individual memos | prepack L241-268 |
| P18_07 | Allowed-terms sanitization (proposed_terms + rescue targets) | prepack L203-238 |
| P18_08 | Sandbox sequence_counter.json for monotone tracking | prepack L56-85 |
| P18_09 | direct_strategy_passthrough vs memo_consolidation modes | prepack L412-416 |
