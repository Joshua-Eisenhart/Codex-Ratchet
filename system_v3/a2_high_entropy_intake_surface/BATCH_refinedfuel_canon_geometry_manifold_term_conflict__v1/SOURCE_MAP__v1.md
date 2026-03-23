# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_refinedfuel_canon_geometry_manifold_term_conflict__v1`
Extraction mode: `TERM_CONFLICT_PASS`
Batch scope: next bounded non-sims refined-fuel doc in folder order; single-doc geometry/axis foundation lock extract with direct comparison to overlay drift surfaces
Date: 2026-03-08

## 1) Assigned Root Inventory
- root:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel`
- nontrivial top-level file count:
  - `8`
- ignored filesystem noise:
  - `.DS_Store`
- folder order:
  - `AXES_MASTER_SPEC_v0.2.md`
  - `AXIS0_PHYSICS_BRIDGE_v0.1.md`
  - `AXIS0_SPEC_OPTIONS_v0.1.md`
  - `AXIS0_SPEC_OPTIONS_v0.2.md`
  - `AXIS0_SPEC_OPTIONS_v0.3.md`
  - `AXIS_FOUNDATION_COMPANION_v1.4.md`
  - `CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.0.md`
  - `PHYSICS_FUEL_DIGEST_v1.0.md`

## 2) Batch Selection
- selected bounded batch:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.0.md`
- reason for selection:
  - this is the next nontrivial top-level file in folder order after `AXIS_FOUNDATION_COMPANION_v1.4.md`
  - the file is compact and formal, with most of its value concentrated in hard semantic fences:
    - geometry as constraint manifold
    - manifold before axes
    - axes as slices rather than primitives
    - Axis-3 engine-family split only
    - engines derived from the manifold rather than primitive
  - the dominant intake value is preserving these semantic locks and their conflicts with nearby overlay surfaces, not broad structure mapping
  - this makes `TERM_CONFLICT_PASS` the best fit
- deferred next doc in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/PHYSICS_FUEL_DIGEST_v1.0.md`

## 3) Source Membership
- source 1:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.0.md`
  - role in batch: refined-fuel compact geometry/axis foundation lock surface
  - sha256: `6f436f63f370f7e323f3a44a771c2decc3e110c424ee8cbc0b990f6719e6920d`
  - size bytes: `1574`
  - line count: `41`
  - source class:
    - refined-fuel formal spec surface

## 4) Structural Map Of The Source
Source numbering below follows manifest order.

### Segment A: identity and hard locks
- source anchors:
  - source 1: `1-11`
- source role:
  - declares the surface as canon in-file and sets the main geometry/axis/engine hard locks
- strong markers:
  - geometry is a constraint manifold
  - geometry exists before axes
  - axes are functions / slices
  - Axis-3 only engine-family split
  - engines are not primitives

### Segment B: core object definitions
- source anchors:
  - source 1: `13-17`
- source role:
  - defines the minimal objects `C`, `M(C)`, and coordinate-free geometry induced by constraints
- strong markers:
  - admissibility statements
  - admissible configurations
  - no metric assumed as primitive

### Segment C: axes-as-slices formalization
- source anchors:
  - source 1: `19-24`
- source role:
  - states the general form for every axis and demotes axis labels to bookkeeping over the manifold
- strong markers:
  - `A_i : M(C) -> V_i`
  - small codomain
  - axis labels do not define `M(C)`

### Segment D: Axis-3 definition and engine-family placement
- source anchors:
  - source 1: `26-35`
- source role:
  - narrows Axis-3 to engine-family admissibility and defines engines as derived equivalence classes
- strong markers:
  - `{Type-1, Type-2}`
  - no additional semantics
  - engines derived objects

### Segment E: compliance checklist
- source anchors:
  - source 1: `37-41`
- source role:
  - closes with concise anti-drift fences for later docs
- strong markers:
  - no axis as primitive substrate
  - no axis before the manifold
  - no Axis-3 chirality / Berry / flux language in canon

## 5) Source-Class Read
- best classification:
  - compact refined-fuel geometry/axis foundation lock surface
  - strong term-conflict and nonconflation anchor
- useful as:
  - cleanest local source for manifold-before-axes and axes-as-slices language
  - direct formal anchor for Axis-3 engine-family-only semantics
  - concise compliance checklist against overlay and substrate drift
- not best classified as:
  - lower-loop earned truth merely because of the in-file authority label
  - a full geometry derivation
  - a sim-ready substrate specification
- possible downstream consequence:
  - later A2-mid reconciliation can reuse this as a compact high-value fence surface when checking overlay pressure, especially where axis or engine language risks being reified into primitive structure
