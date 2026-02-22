# A2 YAML Usage + Entropy Compaction (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: use YAML where it improves A2/A1 authoring and comprehension, while keeping deterministic canon interfaces safe.

==================================================
1) Canonical vs Authoring Formats
==================================================

Canonical (deterministic, append-friendly):
- `memory.jsonl` remains the canonical A2 event log store.
- canonical A2 registries remain JSON:
  - `doc_index.json`
  - `fuel_queue.json`
  - `rosetta.json`

Authoring (human/LLM-friendly):
- YAML is permitted for:
  - A1 strategies (`A1_STRATEGY_v1`)
  - A2 drafts/notes/manifests

Rule:
- YAML is treated as input/authoring.
- A0/A2 must canonicalize YAML into deterministic JSON before hashing or downstream use.

==================================================
2) What YAML Improves (practical)
==================================================

YAML is preferred above the boundary for:
- long structured objects (targets, alternatives, sim refs)
- inline comments and rationale
- multi-line notes/excerpts that must be quarantined above B

==================================================
3) Entropy Compaction (derived artifacts)
==================================================

“Entropy compaction” outputs are derived summaries of `memory.jsonl`:
- human-readable
- noncanon
- regenerable

Examples (single-file targets; do not explode docs):
- `INTENT_SUMMARY.md` (already exists)
- optional: `INTENT_COMPACT.yaml` (derived; structured bullet form)

Storage rule:
- derived compactions should live outside canonical A2 state if strict file sets are enforced,
  e.g. in a run-local folder or a drafts folder.

==================================================
4) Determinism Guardrails for YAML
==================================================

If YAML is used:
- no anchors/aliases
- no custom tags
- no implicit typing relied upon (A0 must coerce types explicitly)
- canonicalization step must:
  - sort keys
  - normalize lists
  - normalize newlines
  - produce a canonical JSON hash

