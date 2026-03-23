# AXIS FOUNDATION COMPANION (Overlay-only) — v1.5

DATE_UTC: 2026-02-02T00:00:00Z  
AUTHORITY: NONCANON (overlay / rosetta only)

Purpose
- This file is a Rosetta/overlay for axes + external labels.
- It is not Thread‑B kernel math.

Core rule (unchanged)
- Thread‑B = admissible math objects + sims, with no axis labels and no bespoke language.
- Overlay = labels (axes / metaphors) that must verify against Thread‑B evidence, never replace it.

---

## 0) What changed since v1.4

1) Axis‑3 semantic lock
- Axis‑3 is ONLY the engine-family split: **Type‑1 vs Type‑2**.
- Axis‑3 is not a chirality/handedness/spinor/Berry/flux tag.

2) Terrain8 naming lock
- Terrain8 is defined as the bookkeeping cross-product:
  **Terrain8 = Topology4 × Family2**, where **Family2 = {Type‑1, Type‑2}**.

3) Sign-conflation hazard reduced
- Axis‑3 is no longer described as a “sign”. It is a family selector.

---

## 1) Drift hazards + locks (keep these visible)

### H1 — “two-valued” conflation across axes
Multiple slices are 2‑valued; do not collapse them:

- Axis‑0: a two-class partition (see AXIS0_SPEC_OPTIONS_v0.*)
- Axis‑6: UP vs DOWN composition sidedness
- Axis‑5: GEN‑CLASS‑1 vs GEN‑CLASS‑2 (placeholder names)
- Axis‑3: Type‑1 vs Type‑2 engine family

Overlay lock
- Do not call any of these “positive/negative”.
- Axis‑3 must not be relabeled as chirality/handedness/spinor/Berry/flux.

### H2 — “Topology4 is edges” conflation
Overlay lock
- Axis‑1×Axis‑2 defines Topology4 base regimes.
- Edges/adjacency are derived structure layered on Topology4.

### H3 — “Axis‑4 is loop order” conflation
Overlay lock
- Axis‑4 is the variance-order math-class split (DEDUCTIVE vs INDUCTIVE).
- Loop sequences (SEQ01–SEQ04, FWD/REV) are probes, not the definition.

---

## 2) Minimal overlay map (stable)

### 2.1 Topology4 (Axis‑1 × Axis‑2)
Topology4 = four base regimes produced by Axis‑1 × Axis‑2.

- The base regimes are treated as a quartet of classes.
- Do not treat Topology4 as a graph; edges come later.

### 2.2 Family2 (Axis‑3)
Family2 = {Type‑1, Type‑2}

- These are engine-family labels only.
- In CANON: do not attach substrate meaning to the labels.

### 2.3 Terrain8 (Topology4 × Family2)
Terrain8 = Topology4 × Family2

- This is bookkeeping used to index derived structures and sims.
- It is not a claim that geometry primitives are 8‑valued.

---

## 3) Legacy/candidate note (overlay only)

- Older artifacts may use axis‑3 naming tied to Weyl/chirality/spinor/flux language.
- Treat that naming as legacy labeling, not semantic authority.

---

## 4) Practical naming (overlay only)

Recommended overlay tokens
- Axis‑3: `engine_family_type1` / `engine_family_type2`
- Terrain8: `topology4_<base>__type1` / `topology4_<base>__type2`

Forbidden overlay tokens (do not use as meanings)
- `chirality`, `handedness`, `weyl`, `spinor`, `berry`, `flux_sign`
