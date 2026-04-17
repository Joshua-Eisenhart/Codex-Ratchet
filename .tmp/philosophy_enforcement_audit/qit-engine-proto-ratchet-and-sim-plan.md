---
title: Qit Engine Proto Ratchet And Sim Plan
created: 2026-04-07
updated: 2026-04-16
type: summary
tags: [reference, research, system]
sources:
  - raw/articles/new-docs/archive_old/QIT_ENGINE_PROTO_RATCHET_AND_SIM_PLAN.md
framing: mixed
---

# Qit Engine Proto Ratchet And Sim Plan

## Overview
This page translates Carnot-like and Szilard-like QIT engine talk into finite channel language, recurrence language, and basin-testing language.
It is a support/translation page, not a promotion surface: engine language should be read through admitted carrier, probe, and support relations rather than as a primitive ontology.

## Engine As Basin Generator
An engine cycle should be read as an ordered finite composition of admissible channels or instruments on density states, `E = Phi_n o ... o Phi_1`. A basin exists when repeated application of that cycle, together with bounded perturbation, returns nearby trajectories to a stable operational class instead of letting them diffuse into generic noise.

That means:
- the engine is not a primitive explanatory object
- the cycle only counts after the carrier/support/probe layer is admitted
- stronger bridge or identity claims must still be earned by bounded sim/result surfaces

## Basin Types In Engine Language
- State attractor: a family of density matrices that repeated engine cycles approach.
- Process attractor: a stable loop of channels, instruments, or update-order patterns.
- Equivalence attractor: not one literal state, but a probe-equivalence class with the same persistent distinguishability structure.

## Carnot-Like And Szilard-Like Roles
- Carnot-like engine: better model for gradient-shaped process attractors, metastable corridors, and large-scale circulation across entropy or athermality gradients.
- Szilard-like engine: better model for local correction, measurement-feedback steering, and narrow active-maintenance basins that preserve recoverable structure.
- Hybrid engine: the Carnot-like loop shapes the corridor, and the Szilard-like loop keeps trajectories inside the good part of it.

## Repo Status Snapshot
- Pure density-matrix thermodynamics is already strong in `sim_pure_lego_quantum_thermodynamics.py` and `pure_lego_quantum_thermodynamics_results.json`.
- The runtime Carnot analogy is exploratory only; `sim_carnot_gradient_bound.py` is a validated negative result, not a promoted theorem lane.
- Szilard-like engine language currently has one bounded finite bookkeeping row on disk: `sim_qit_szilard_landauer_cycle.py` shows bounded measurement-feedback bookkeeping closing at the kT ln 2 scale, while `szilard_64stage_v2_sim.py` and `sim_szilard_operator_accounting.py` remain exploratory engine-side sidecars. Public promotion should stay aligned with the current truth audit rather than the file's self-classification.
- These classical/QIT-first engine baselines remain separate from the geometry proof spine and do not override geometry-before-axis build order.
- Classical baselines are not outside the larger system: numpy/classical realizations should be treated as real occupants of the same wider manifold, comparison surfaces, and negative/control surfaces rather than a rival ontology. See [[support-first-constraint-manifold-dependency-chain]].
- Basin distinctions are currently supported by `sim_viability_vs_attractor.py`, `sim_axis0_attractor_basin_boundary.py`, and `sim_qit_attractor_basin_recovery.py`; together they support state/process/equivalence basin distinctions without broadening into a universal attractor claim.

Public reading fence:
- keep the stronger status labels attached to the cited artifact or truth-audit surface, not to this page's summary voice
- do not let engine vocabulary silently outrun the narrower basin/equivalence evidence

## Current Evidence Goal
The next earned claim is not "engines are basins" in the abstract. It is: which ordered finite cycles preserve nontrivial distinguishability structure and return perturbed trajectories to the same operational equivalence class.

## Related pages
- [[qit-engine-dev-framing]]
- [[qit-ai-foundations-bridge]]
- [[nominalist-cs-framing]]
- [[stochastic-thermodynamics-reference]]
- [[attractor-basins-formal-reference]]
- [[qit-engine-geometry-entropy-bridge]]
- [[system-architecture-reference]]
