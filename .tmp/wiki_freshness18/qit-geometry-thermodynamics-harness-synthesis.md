---
title: QIT Geometry Thermodynamics Harness Synthesis
created: 2026-04-10
updated: 2026-04-16
type: concept
tags: [simulation, thermodynamics, geometry, harness, quantum, canonical]
sources:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_qit_attractor_basin_recovery.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_viability_vs_attractor.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_carnot_gradient_bound.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_qit_szilard_landauer_cycle.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/LLM_CONTROLLER_CONTRACT.md
framing: current
---

# QIT Geometry-Thermodynamics-Harness Synthesis

This page binds together four live surfaces that should not be collapsed into one story: the doubly-quantum-mechanics support note, the basin / attractor / viability synthesis, the Carnot negative probe, and the Szilard bookkeeping row. It also records the controller-contract vocabulary that governs how these claims are reported.

## 1. Current Truth

The evidence separates into four distinct candidates.

1. `[[doubly-quantum-mechanics]]` is a support note for a geometry-quantized extension candidate. It says the geometrical configurations themselves may acquire quantum features. It is exploratory and should stay in the support lane.
2. `[[qit-basin-engine-synthesis]]` includes artifact-backed basin/attractor rows, with canonical recovery/viability rows and a separate classical-baseline basin-boundary row, rather than a single exact-density-matrix recovery story.
3. `[[stochastic-thermodynamics-reference]]` carries two engine-facing contrasts that must stay separate: the Carnot runtime probe did not establish a stable Carnot-like bound at the tested parameterization, while the Szilard lane has one clean bookkeeping row plus bounded companion/bridge rows on the same two-qubit carrier.
4. The controller contract defines the four-label vocabulary used in the current wiki: `exists`, `runs`, `passes local rerun`, and `canonical by process`. The current drift inventory still flags the controller contract as not current, so this should be read as contract vocabulary rather than fresh page-to-page alignment.

The contradiction to preserve is simple: Carnot is a useful negative probe here, not a promoted bound, while Szilard is a narrow bookkeeping row with a canonical-on-disk artifact, not a generic engine doctrine.

## 2. Math Worked Out

### Geometry-quantized candidate

Let a candidate configuration space G carry the geometric structure that the supporting note wants to quantize. The claim is not that G is already the final ontology; the claim is that the geometry itself may become part of the admissible carrier, not only the state values on top of it.

### Basin / equivalence class

Let ρ be a density matrix and let E = Φ_n ∘ ... ∘ Φ_1 be an ordered composition of CPTP maps.

Define a probe-relative equivalence relation ~_P by

ρ ~_P σ iff the active probe family P cannot distinguish them within the tested tolerance and measurement family.

The strongest earned object is not a point attractor but a stable equivalence class [ρ]_P under ordered noncommuting update.

### Carnot-like gradient loop

The Carnot probe is a gradient-shaped process circulator. At the tested parameterization, the checked validation did not establish a stable Carnot-like bound. That is a negative result on the probe, not a universal impossibility theorem.

### Szilard-like measurement-feedback loop

The Szilard row is the finite measurement-branch-update-reset loop:

probe → branch → conditional act → reset cost

That loop earns bookkeeping language for one-bit measurement-feedback-erasure. It does not yet earn a broader basin doctrine.

### Harness label grammar

The controller contract maps artifacts into a finite classification vocabulary. This is not physical math, but it is part of the evidence grammar:

artifact → {exists, runs, passes local rerun, canonical by process}

That grammar is load-bearing because it stops a candidate from being promoted just because the prose sounds complete.

## 3. Translation

### Doubly quantum mechanics

Translate as a geometry-first support candidate, not as a settled layer. Use it when the claim is about the carrier geometry itself becoming active.

### Basin synthesis

Translate as ordered-channel recovery, recurrence behavior, and probe-relative distinguishability class stability. Do not flatten recurrence, basin, and viability into one term unless the evidence closes the gap.

### Carnot engine

Translate as a negative control for gradient-shaped loops. The current checked validation says the loop did not establish a stable Carnot-like runtime bound at the tested parameterization.

### Szilard engine

Translate as finite measurement-feedback control with explicit bookkeeping. The on-disk canonical artifact is real but narrow: one-bit measurement-feedback-erasure, not a global engine theorem.

### Harness rules

Translate as classification discipline. The controller contract is there to keep support notes, canonical rows, and negative probes from being reported as if they were the same kind of evidence.

## 4. What Is Already Earned

| Claim | Evidence | Classification |
|---|---|---|
| Doubly quantum mechanics support note exists and is routed as exploratory geometry support | `concepts/doubly-quantum-mechanics.md` | `exists` |
| Equivalence-class recovery under ordered noncommuting channels | `sim_qit_attractor_basin_recovery.py` + `qit_attractor_basin_recovery_results.json` | artifact-side classification: `canonical` |
| Viability-preserving vs attractor collapse are distinct candidates | `sim_viability_vs_attractor.py` + result JSON | artifact-side classification: `canonical` |
| Carnot runtime bound does not emerge at the tested parameterization | `sim_carnot_gradient_bound.py` + `carnot_gradient_bound_validation.json` | `passes local rerun` |
| Bounded Szilard measurement-feedback-erasure row on disk | `sim_qit_szilard_landauer_cycle.py` + `qit_szilard_landauer_cycle_results.json` | `exists` (public promotion remains under truth-audit review) |
| The controller contract defines the current 4-label vocabulary, while the drift inventory still flags that contract as not current | `llm-controller-contract.md`, `controller_doc_drift_inventory.json`, `llm-ingest-policy.md`, `harness-boot-pack.md`, `controller-prompt-rules.md`, `probe-doc-result-map.md` | `exists` |

## 5. What Is Still Open

1. Does the doubly-quantum-mechanics candidate change the geometry layer, or only rename a geometry-first support intuition?
2. Does equivalence-class recovery generalize beyond the one ordered noncommuting cycle already tested?
3. Does a Szilard-style feedback loop sharpen the basin, or only maintain the bookkeeping surface already earned?
4. Can any Carnot-like gradient loop earn a positive bound on some other parameterization, or is the current negative result the stable behavior for this family?
5. Are there bridge claims between geometry-quantized carriers and engine bookkeeping, or are those still separate support surfaces?

## 6. One Next Proposal Lane Only

Proposed next sim: `sim_qit_szilard_basin_feedback_generalization.py`

What it tests:
- reuse the ordered noncommuting recovery protocol
- insert a Szilard-style branch / conditional update / reset step
- compare the recovery class width before and after the feedback step
- keep the same probe family and the same bounded perturbation model

Why this lane:
- it binds the strongest basin claim to the narrow canonical Szilard row
- it stays inside one ordered-cycle family instead of starting a new thermodynamics doctrine
- it can return one result file and one classification without expanding the program scope

If a later bounded rerun/audit passes cleanly, candidate public label: `canonical by process`

## 7. Optional Dependencies

Optional means optional; none of these are required for the next lane.

- QuTiP: if spectral gap and Lindblad bookkeeping become necessary
- OQuPy: if non-Markovian memory effects become necessary
- CVXPY: if basin admissibility needs an optimization witness
- Hypothesis: if pathological perturbation families need stress testing

## Related Pages

- [[doubly-quantum-mechanics]] — geometry-quantized support candidate
- [[qit-basin-engine-synthesis]] — basin / attractor / viability synthesis
- [[stochastic-thermodynamics-reference]] — Carnot and Szilard owner surface
- [[qit-vocabulary-discipline-reference]] — public-term routing discipline
- [[current-research-overlays]] — research routing surface
- [[llm-controller-contract]] — live status-label contract
- [[llm-ingest-policy]] — retrieval and label discipline
- [[controller-prompt-rules]] — controller reporting rules
- [[probe-doc-result-map]] — evidence bridge
