# SIM Runbook v1.5 (simpy/simson integration)

This runbook is operational hygiene only.
Goal: keep SIM runs repeatable and paste-safe.

---

## 0) One rule that prevents most failures

Thread‑B only accepts:
- one EXPORT_BLOCK, or
- one SAVE_SNAPSHOT, or
- a SIM_EVIDENCE pack (one or more SIM_EVIDENCE blocks back-to-back)

…and nothing else.

When pasting SIM evidence: paste only the SIM_EVIDENCE blocks (no extra text).

---

## 1) Fast-start checklist (repeatable)

1) Boot Thread‑B (kernel pinned).
2) Replay a tape or load a snapshot (as applicable).
3) Run sims locally (archived simpy/simson harnesses or updated harnesses).
4) Paste SIM_EVIDENCE blocks back into Thread‑B (no extra text).
5) If Thread‑B halts: isolate the failing SIM_ID and rerun just that script.

---

## 2) Axis scope (tight)

- Axis‑4 = variance‑order math-class split (two kinds of math), not “loop order”.
- Axis‑1 × Axis‑2 = Topology4 base regimes, not “graph edges”.
- Axis‑3 = engine-family split (Type‑1 vs Type‑2), not chirality/handedness/spinor/Berry/flux.

Terrain8 bookkeeping
- Terrain8 = Topology4 × (Axis‑3 family)

---

## 3) Minimal suite (order of execution)

1) Axis‑4 seq both dirs (SEQ01–SEQ04 plus any variance-order check harness)
2) Axis‑0 trajectory correlation / mutual-info suite
3) Axis‑12 Topology4 harnesses
4) Stage16 Axis‑6 mixes (control + sweep)
5) ULTRA runs (end-to-end)

Note
- Older “Axis‑3” runs in the archived snapshot may use legacy naming in SIM_IDs.
  Treat those identifiers as labels only.

---

## 4) Paste hygiene (copy/paste exact)

Correct
```
BEGIN SIM_EVIDENCE v1
...
END SIM_EVIDENCE v1
BEGIN SIM_EVIDENCE v1
...
END SIM_EVIDENCE v1
```

Incorrect
- any prose above/between blocks
- Markdown code fences when pasting into Thread‑B
- “here’s the evidence: …”

---

## 5) Where the artifacts live (in this bundle)

- SIM_CATALOG_v1.4.md = catalog pointer (archived filenames)
- ARCHIVE/REFERENCE_RATCHET_BUNDLE_v2.0.12.zip = archived simpy/simson runs + results
