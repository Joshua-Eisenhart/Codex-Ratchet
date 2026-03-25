# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_refinedfuel_axis4_vs_axis5_heat_cold_term_conflict__v1`
Extraction mode: `TERM_CONFLICT_PASS`
Batch scope: next bounded non-sims `constraint ladder` doc in folder order; single-doc Axis-4 versus Axis-5 anti-conflation correction extract
Date: 2026-03-09

## 1) Assigned Root Inventory
- root:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder`
- nontrivial file count:
  - `40`
- folder order around this batch:
  - `Axis 3 math Hopf fiber loop vs lifted base loop.md`
  - `Axis 4 qit mathΓÇ¿ΓÇ¿Good ΓÇö that statement narrows the target exactlyΓÇª.md`
  - `Axis 4 vs axis 5. Heating vs cooling is not Hot vs coldΓÇ¿ΓÇ¿YouΓÇÖre rightΓÇª.md`
  - `Base constraints ledger v1.md`
  - `CANDIDATE_PROPOSAL_v1.md`

## 2) Batch Selection
- selected bounded batch:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder/Axis 4 vs axis 5. Heating vs cooling is not Hot vs coldΓÇ¿ΓÇ¿YouΓÇÖre rightΓÇª.md`
- reason for selection:
  - this is the next unprocessed non-sims `constraint ladder` file in folder order after the Axis-4 QIT note
  - the file is compact and narrowly focused on one correction:
    - Carnot has one loop with two traversal directions
    - `hot` / `cold` are reservoir or state properties, not loop directions
  - the note’s main intake value is semantic conflict preservation:
    - it sharpens the separation between direction and intensity
    - but it still defines Axis-4 as loop direction itself, which conflicts with later refined-fuel canon
  - this makes `TERM_CONFLICT_PASS` the best fit
- deferred next doc in folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder/Base constraints ledger v1.md`

## 3) Source Membership
- source 1:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder/Axis 4 vs axis 5. Heating vs cooling is not Hot vs coldΓÇ¿ΓÇ¿YouΓÇÖre rightΓÇª.md`
  - role in batch: noncanon correction note separating loop direction from drive/intensity in the Axis-4 versus Axis-5 family
  - sha256: `c2cbdc2ad7b7a5eb634e5e8331944519b232c0df1b7c026da4df96abcc4e4219`
  - size bytes: `4057`
  - line count: `132`
  - source class:
    - `NONCANON_NOTES` semantic-correction fuel surface

## 4) Structural Map Of The Source
Source numbering below follows manifest order.

### Segment A: explicit error admission and Carnot correction
- source anchors:
  - source 1: `1-43`
- source role:
  - opens by retracting the earlier `hot vs cold` framing and replaces it with the statement that Carnot has one loop and two traversal directions
- strong markers:
  - mistake explicit
  - one cycle
  - two directions
  - heating cycle
  - cooling cycle
  - not hot vs cold loop

### Segment B: corrected axis mapping
- source anchors:
  - source 1: `46-85`
- source role:
  - maps:
    - Axis-4 to heating-versus-cooling direction of the same loop
    - Axis-5 to energy regime, drive level, and hot-like versus cold-like state property
- strong markers:
  - loop direction
  - ordering of operations
  - forward vs reverse cycle
  - high-drive vs low-drive
  - far from equilibrium vs near it

### Segment C: noncontradictory picture and final lock
- source anchors:
  - source 1: `89-132`
- source role:
  - compresses the corrected picture into a keep-this summary and suggests next steps about opposite orientations on the same cycle or amplitude changes on the same cycle
- strong markers:
  - corrected picture
  - forward vs reverse cycle
  - energy / drive regime
  - same cycle without changing direction
  - final lock

## 5) Source-Class Read
- best classification:
  - high-value noncanon anti-conflation correction note for the Axis-4 versus Axis-5 family
- useful as:
  - a narrow record that explicitly rejects `hot/cold` as loop-direction language
  - a compact pressure surface for separating direction from intensity
  - a direct witness of the family’s midstream correction process
- not best classified as:
  - current Axis-4 canon
  - current Axis-5 canon
  - a standalone thermodynamic law surface
- possible downstream consequence:
  - later A2-mid reduction can reuse this as a clean conflict witness showing why direction and intensity were being separated, but must preserve that the source still overidentifies Axis-4 with loop direction itself rather than with the deeper math-class split used in later refined-fuel canon
