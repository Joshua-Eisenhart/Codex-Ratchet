# FOLDER MAP

One line per folder. No nesting descriptions. If a folder isn't here, it shouldn't exist.

```
Codex Ratchet/
  core_docs/                    — SOURCE OF TRUTH. Never modified by the system. Read-only fuel.
  work/
    SESSION_STATE.md            — Current status. ONE file. Rewritten each session.
    A2_BOOT.md                  — Boot sequence for new threads.
    FOLDER_MAP.md               — This file. Structure reference.
    ratchet_core/               — THE MACHINE. All executable code lives here.
      b_kernel.py               — B enforcement
      state.py                  — Canonical state + graveyard pool
      runner.py                 — Cycle orchestrator (--full-cycle mode)
      containers.py             — EXPORT_BLOCK format
      validator.py              — Lexeme/derived-only fences
      a0_generator_v2.py        — A0 deterministic compiler
      a1_protocol.py            — A1 strategy format + expander (alternatives + neg SIM_SPECs)
      a1_llm.py                 — A1 briefing generator for Cursor LLM
      zip_protocol.py           — Universal container
      feedback.py               — B results → A2 state
      sim_builder.py            — Sim registry + builder (22+3 sims)
      adversarial_test.py       — B enforcement test suite
      spec_ci.py                — Spec/code drift checker (9 checks)
      constraint_sim_binding.json — Sim routing table (36 bindings)
      sims/                     — Pure Python sims. One file per math property. Positive + negative.
    a2_state/                   — A2 persistent state. Updated by feedback loop.
      memory.jsonl              — Append-only persistent memory (decisions, intents, learnings)
      fuel_queue.json           — Structured fuel for A1 (306 entries from constraint ladder)
      rosetta.json              — Jargon↔B-term mappings
      doc_index.json            — What A2 has read
      constraint_surface.json   — Graveyard analysis (written by feedback.py)
    runs/                       — Ephemeral. Cycle outputs, ZIPs, state snapshots. Can be deleted.
    system_specs/               — Design docs. Reference only. Do not let these explode.
    rebaseline/                 — Verbatim bootpack extracts. Read-only reference.
  archive/                      — Old stale specs + failed attempts. Read-only reference.
```

## Rules

- `SESSION_STATE.md` is rewritten, never appended. Max 1 page.
- `a2_state/` has 5 operational files. If it grows past 5, something is wrong.
- `sims/` grows when new math properties are validated. Positive AND negative sims.
- `runs/` is ephemeral. Delete freely.
- `system_specs/` must not exceed 15 files. Compress or merge if approaching limit.
- `core_docs/` is never modified by the system. It is FUEL, not validated input.
- No file in `ratchet_core/` should exceed 500 lines. Split if approaching.
