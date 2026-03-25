# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_refinedfuel_axis0_spec_options_v03_qit_bridge__v1`
Extraction mode: `QIT_BRIDGE_PASS`
Batch scope: next bounded non-sims refined-fuel doc in folder order; single-doc Axis-0 v0.3 extract compressing the family into a cleaner measurement-proposal surface with explicit nondecision quarantine
Date: 2026-03-08

## 1) Assigned Root Inventory
- root:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel`
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
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/AXIS0_SPEC_OPTIONS_v0.3.md`
- reason for selection:
  - this is the next nontrivial top-level file in folder order after `AXIS0_SPEC_OPTIONS_v0.2.md`
  - compared to v0.2, this version compresses the family into a cleaner operational measurement surface:
    - minimal finite-dimensional QIT setup
    - four compact option families
    - practical derivative-estimation notes
    - an explicit `what this does not decide` quarantine
  - it also changes the option mix materially:
    - Option B becomes variance-control over pairwise weights
    - Option C becomes total correlation rather than conditional-entropy / coherent-information machinery
    - the shell bookkeeping and admission-order scaffolding from v0.2 is mostly removed
  - the dominant intake value remains the QIT bridge from Axis-0 language to testable measurement objects
  - this keeps `QIT_BRIDGE_PASS` as the best-fit extraction mode
- deferred next doc in folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/AXIS_FOUNDATION_COMPANION_v1.4.md`

## 3) Source Membership
- source 1:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/AXIS0_SPEC_OPTIONS_v0.3.md`
  - role in batch: refined-fuel Axis-0 v0.3 compact measurement-proposal surface
  - sha256: `394f81ce9ac38daeedb005a834d9abf7f0ac0b463a9835043d769593a846b659`
  - size bytes: `5584`
  - line count: `160`
  - source class:
    - refined-fuel draft option surface

## 4) Structural Map Of The Source
Source numbering below follows manifest order.

### Segment A: identity, canon anchor, and proposal-only guard
- source anchors:
  - source 1: `1-13`
- source role:
  - declares the document as draft noncanon, then locks a canon-anchor phrasing while explicitly quarantining the rest as measurement proposal only
- strong markers:
  - draft noncanon
  - Axis-0 only
  - canon anchor
  - testable options, not canon

### Segment B: minimal QIT-native setup
- source anchors:
  - source 1: `17-33`
- source role:
  - reduces the setup to the minimum objects needed for finite-dimensional perturbation-response measurement
- strong markers:
  - density operator
  - finite-dimensional Hilbert space
  - fixed subsystem decomposition
  - CPTP perturbation family
  - diversity / spread of correlations across subsystem pairs

### Segment C: pairwise correlation-spread and variance-control options
- source anchors:
  - source 1: `37-81`
- source role:
  - provides the first two compact operational routes:
    - effective number of correlated links
    - variance control over pairwise weights
- strong markers:
  - pairwise mutual information
  - normalized pair weights
  - Shannon entropy
  - effective diversity
  - deviation damping as variance control

### Segment D: total-correlation option
- source anchors:
  - source 1: `84-98`
- source role:
  - swaps the prior negative-conditional-entropy emphasis for a global total-correlation scalar
- strong markers:
  - multi-information
  - total correlation
  - global scalar caveat

### Segment E: `jk fuzz` path-ensemble and global order-parameter option
- source anchors:
  - source 1: `101-139`
- source role:
  - turns unraveling/path intuition into path-entropy and clock-like global-order-parameter proposals
- strong markers:
  - Kraus-index histories
  - path entropy
  - admissible histories
  - global monotone `G(rho)`
  - `i := G(rho)`

### Segment F: sim recipe and explicit nondecision boundary
- source anchors:
  - source 1: `142-160`
- source role:
  - closes with a generic numerical recipe and an explicit statement of what interpretive questions remain deferred
- strong markers:
  - approximate derivatives with epsilon
  - many seeds and channel families
  - does not decide negative entropy / entangled spacetime / holographic bookkeeping
  - does not decide best clock-like invariant

## 5) Source-Class Read
- best classification:
  - refined-fuel Axis-0 compact QIT bridge surface
  - proposal-side cleanup version that prioritizes operational measurement options over admission-order scaffolding
- useful as:
  - cleanest compact measurement proposal in the Axis-0 options family so far
  - direct record of the family shift from coherent-info / boundary-bookkeeping emphasis toward pairwise spread, variance control, total correlation, and path entropy
  - bounded source for later sim-facing comparison without importing physics interpretation
- not best classified as:
  - active kernel law
  - settled canonical Axis-0 implementation
  - full replacement for the richer shell/bookkeeping scaffolding in v0.2
- possible downstream consequence:
  - later A2-mid or A1 proposal reduction can reuse this as a compact option-family checkpoint, especially when a cleaner measurement-facing summary is needed without treating the cleaned-up option set as fully settled
