# State Schema (all persistent state files)

Status: NONCANON | Updated: 2026-02-18
Implementation: `ratchet_core/state.py`, `ratchet_core/zip_protocol.py`, `ratchet_core/feedback.py`

## 1. KernelState (state.json in run_dir)

The canonical ratchet state. Created by `runner.py --init`, updated every cycle.

```
{
  "axioms": [{"id": str, "kind": str, "raw_lines": [str]}],
  "specs": [{"id": str, "kind": str, "deps": [str], "raw_lines": [str],
             "evidence_tokens": [str], "status": str}],
  "terms": [{"term": str, "spec_id": str, "binds": str, "state": str}],
  "survivor_order": [str],
  "graveyard": [{"id": str, "reason": str, "raw_lines": [str]}],
  "parked": [mixed],
  "evidence_pending": {"spec_id": ["token"]},
  "counts": {"spec": int, "probe": int},
  "active_ruleset_sha256": str,
  "active_megaboot_sha256": str,
  "active_megaboot_id": str,
  "sim_run_count": int
}
```

Key fields:
- `axioms`: F01_FINITUDE and N01_NONCOMMUTATION (the two foundation axioms)
- `specs`: all proposed specs with kind (MATH_DEF, TERM_DEF, SIM_SPEC, PROBE_HYP)
- `terms`: admitted vocabulary with bindings
- `graveyard`: everything B rejected, with reason
- `evidence_pending`: specs waiting for SIM evidence

Status is disposable. The machine is the product.

### Pool (graveyard workspace)

`state.pool` is a dict of concept_id → concept info. Seeded from fuel_queue.json at init.

```
{
  "concept_id": {
    "status": "DEAD|ATTEMPTING|RESURRECTED",
    "source": "source_doc.md",
    "label": "SEMANTIC_LABEL",
    "body": "one-line description",
    "chain_needs": ["dependency_concept_ids"],
    "attempts": [
      {"spec_id": "S_...", "reason": "DERIVED_ONLY_PRIMITIVE_USE", "cycle": 1}
    ],
    "current_spec_id": "S_..." or null
  }
}
```

Everything starts DEAD. A1 picks items to try resurrecting. B rejection reasons are logged
per attempt. When something passes B + SIM, status → RESURRECTED.

## 2. fuel_queue.json (work/a2_state/)

Structured fuel extracted from constraint ladder documents.

```
{
  "version": 1,
  "entries": [
    {
      "id": "F0001",
      "tag": "ASSUME|DERIVE|OPEN|CONSTRAINT",
      "label": "SEMANTIC_LABEL",
      "body": "one-line description",
      "source_doc": "filename.md",
      "concepts_needed": [str]
    }
  ]
}
```

306 entries from 18 constraint ladder docs. Read-only input to A1.

## 3. rosetta.json (work/a2_state/)

Bidirectional mappings between jargon and B-admitted terms.

```
{
  "version": 1,
  "mappings": {
    "term_literal": {
      "b_spec_id": "S_TERM_X",
      "binds": "S_L0_MATH",
      "state": "TERM_PERMITTED",
      "admitted_cycle": true
    }
  }
}
```

Updated by `feedback.py` after each cycle. Starts empty, grows as B admits terms.

## 4. memory.jsonl (work/a2_state/)

Append-only A2 persistent memory. One JSON object per line.

```
{"ts": "ISO8601", "type": "decision|learned|failed|intent", "content": "..."}
```

Types:
- `decision`: architectural choices that are settled
- `learned`: things discovered during sessions
- `failed`: approaches that didn't work (so we don't retry)
- `intent`: user's core goals and principles

Updated at end of session. Never rewritten.

## 5. constraint_surface.json (work/a2_state/)

Written by `feedback.py`. Graveyard analysis for A2.

```
{
  "total_graveyard": int,
  "total_survivors": int,
  "ratio": float,
  "rejection_reasons": {"reason": count},
  "blocked_concepts": [{"id": str, "reason": str}]
}
```

## 6. ZIP envelope (run_dir/zips/)

Universal container for thread-crossing artifacts. Written by `zip_protocol.py`.

```
{
  "kind": "A1_STRATEGY|A1_BATCH|EXPORT_BLOCK|SIM_REQUEST|SIM_EVIDENCE|FEEDBACK",
  "source": "thread_name",
  "target": "thread_name",
  "timestamp_utc": "ISO8601",
  "payload": {mixed},
  "manifest_sha256": "hex64"
}
```

Filename: `{kind}_{hash_prefix}.json`. Integrity verified on read.

## 7. constraint_sim_binding.json (ratchet_core/)

Maps constraint spec IDs to sim scripts.

```
{
  "SIM_TERM_X": {
    "sim_id": "sim_name",
    "sim_path": "work/ratchet_core/sims/sim_name.py"
  }
}
```

Used by `runner.py _load_sim_binding()` to route evidence requests to sims.

## 8. SESSION_STATE.md (work/)

Human-readable session state. Rewritten (not appended) at end of each session.
Max 1 page. Contains: what works, what's broken, what's next, key decisions.
