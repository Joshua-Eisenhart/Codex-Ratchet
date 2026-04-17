---
title: QIT Basin Engine Synthesis
created: 2026-04-10
updated: 2026-04-16
type: concept
tags: [simulation, system, constraints, quantum, canonical]
sources:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_qit_attractor_basin_recovery.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_viability_vs_attractor.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_attractor_basin_boundary.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_carnot_gradient_bound.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_qit_szilard_landauer_cycle.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_phase_damping_fixed_point_geometry.py
framing: current
---

# QIT Basin Engine Synthesis

Source-grounded synthesis of QIT-aligned attractor basins, Carnot/Szilard QIT engines, and the repo-backed evidence cited below. Viability, basin, engine, and equivalence-class language are treated as distinct unless the evidence closes the gap.

## 1. Current Truth

The cited repo evidence includes three basin-related sims and one negative-result row. The narrowest earned claim is equivalence-class recovery under ordered noncommuting channels. Viability remains the broader survival primitive. Basin language must be earned for specific ordered families, not assumed universal. For repo-facing wording, the safer public parent terms are operational equivalence class, recurrence behavior, metastable class, and stability region; reserve stronger basin-of-attraction phrasing for better dynamical characterization.

## 2. Basin Math

### State Attractor

A density-matrix family A such that, under repeated ordered channel composition E = Phi_n o ... o Phi_1, nearby trajectories converge toward A.

**Formal:** rho_{t+1} = E(rho_t). A is a state attractor for basin B if for all rho_0 in B, lim_{t->inf} d(rho_t, A) = 0 for some distance d.

**Repo evidence:** Partial. The basin recovery sim shows convergence to a specific equivalence class, not to one exact matrix. The terminal trace gap (0.008) shows states land near each other, not at a single point. So the repo evidence is closer to equivalence attractor than state attractor.

**Constraint set:** {finite d, CPTP channels, bounded perturbation, specific ordered cycle}.

### Process Attractor

A stable loop of channels, instruments, or update-order patterns such that the ordered cycle E repeats indefinitely without diverging.

**Formal:** E composed with itself n times has a fixed-point algebra F(E^n) = {rho : E^n(rho) = rho}. The process attractor is the recurrent cycle structure, not the states it visits.

**Repo evidence:** Present in two places:
- `sim_viability_vs_attractor.py` shows a viability-preserving update that keeps trajectories bounded vs an attractor update that collapses them. Classification: `canonical by process`.
- `sim_axis0_attractor_basin_boundary.py` shows process-specific basin-boundary behavior. Classification: `passes local rerun`.

**Key distinction:** The process attractor is about the channel composition structure, not the states it happens to visit. Different orderings of the same channels can define different process attractors. This is directly tested: the basin recovery sim shows chosen order beats swapped order (class hits: 2 vs 0, gap: 0.029).

**Constraint set:** {finite d, CPTP channels, ordered composition, bounded perturbation}.

### Equivalence Attractor

Not one exact state, but a probe-equivalence class: states sharing the same persistent distinguishability structure under admissible probes.

**Formal:** Define equivalence relation ~_P on states: rho ~_P sigma iff for all probes pi in P, pi(rho) = pi(sigma). The equivalence attractor is a class [rho]_P that is stable under E: E maps elements of [rho]_P to elements of [rho]_P (or to indistinguishable classes).

**Repo evidence:** This is the strongest earned claim. From `sim_qit_attractor_basin_recovery.py` (classification: `canonical by process`):
- Two nearby perturbed density states (different initial excited populations) both converge to the same recovery class defined by: excited_population < 0.2, coherence_magnitude < 0.02, z_bias > 0.6.
- Terminal trace gap between the two recovered states: 0.008 — they are near each other but not identical. They are in the same probe-equivalence class.
- The chosen noncommuting order produces 2 class hits; the swapped order produces 0.
- A commuting control schedule produces order gap ~0 — the order effect disappears entirely.
- A mismatched (different channel) schedule produces 0 class hits — different channels don't recover the same class.

**This is the identity logic of the system operationalized:** a = a iff a ~ b. The attractor is not a point. It is a distinguishability class.

**Constraint set:** {finite d, CPTP channels, specific ordered noncommuting cycle, bounded perturbation, probe set defining equivalence}.

### The Three Are Distinct

| Type | What stabilizes | Repo status |
|---|---|---|
| State attractor | One exact density matrix (or tight family) | Partial — convergence to class, not point |
| Process attractor | The channel cycle structure itself | Earned — order matters, boundary behavior is process-specific |
| Equivalence attractor | A probe-equivalence class | Canonical — best earned claim |

## 3. Engine Translation

### Carnot-Like Engine

Gradient-shaped process circulator. Couples to high-entropy and low-entropy sectors, transfers distinguishability cyclically.

**Repo status:** `sim_carnot_gradient_bound.py` + `carnot_gradient_bound_validation.json`. Classification: validated negative result (3/3 gates passed, score 1.0). No stable Carnot-like runtime bound emerged at the tested parameterization.

**Translation:** The Carnot runtime analogy did not earn basin or attractor claims. It is useful as a negative result: the tested parameterization does not produce a Carnot-like circulation. This constrains what engine cycles can claim basin behavior without proving it.

**Do not over-promote.** Carnot-like loops are a conceptual frame for gradient circulators. The repo has not earned a Carnot basin claim.

### Szilard-Like Engine

Measurement-feedback local stability shaping. Distinguishes, branches on probe outcome, applies conditional channel, and steers trajectories back into an organized recurrence regime.

**Repo status:** One bounded bookkeeping row exists on disk, and broader engine-side Szilard surfaces remain exploratory:
- `sim_qit_szilard_landauer_cycle.py` + `qit_szilard_landauer_cycle_results.json`: bounded finite measurement-feedback-erasure row on disk; public process promotion remains under truth-audit review.
- `szilard_64stage_v2_sim.py` + `szilard_64stage_v2_results.json`: exploratory super-additivity surface.
- `sim_szilard_operator_accounting.py`: exploratory operator-role bookkeeping.

**Translation:** Szilard-like loops are still the better conceptual match for measurement-feedback basin maintenance. What is now earned is narrow but real: the repo has a bounded bookkeeping row on disk for finite ordered measurement-feedback-erasure. What is not yet earned is a broader Szilard basin claim, a promoted engine-totality doctrine, or a public `canonical by process` label beyond the current truth-audit surface.

### Hybrid Engine

Carnot shapes the corridor; Szilard keeps the trajectory inside the good part of it.

**Repo status:** No hybrid sim exists. This is a conceptual design, not an earned claim. The next canonical lane should target this if the basin recovery row can be extended.

## 4. What Is Already Earned

| Claim | Evidence | Status / note |
|---|---|---|
| Equivalence-class recovery under ordered noncommuting channels | `sim_qit_attractor_basin_recovery.py` + `qit_attractor_basin_recovery_results.json` | `canonical by process` |
| Order matters: chosen order beats swapped | `sim_qit_attractor_basin_recovery.py` + `qit_attractor_basin_recovery_results.json` | same result packet; ordered noncommuting schedule beats swapped order |
| Commuting control loses order effect | `sim_qit_attractor_basin_recovery.py` + `qit_attractor_basin_recovery_results.json` | same result packet; negative control |
| Viability-preserving vs attractor collapse | `sim_viability_vs_attractor.py` + `viability_vs_attractor_results.json` | `canonical by process` |
| Process-specific basin boundary | `sim_axis0_attractor_basin_boundary.py` + `axis0_attractor_basin_boundary_results.json` | `passes local rerun` |
| Pure quantum thermodynamics (Landauer, free energy, Carnot bound) | `sim_pure_lego_quantum_thermodynamics.py` + `pure_lego_quantum_thermodynamics_results.json` | `canonical by process` |
| Phase damping fixed point geometry | `sim_phase_damping_fixed_point_geometry.py` + `phase_damping_fixed_point_geometry_results.json` | support geometry row; status not re-audited in this page |
| Carnot runtime bound does not emerge | `sim_carnot_gradient_bound.py` + `carnot_gradient_bound_validation.json` | `passes local rerun` (negative) |

**Not earned:** Carnot basin, Szilard basin, hybrid basin, universal attractor ontology, basin as general identity of survival.

## 5. What Is Still Open

1. **Does the equivalence-class recovery generalize beyond one ordered cycle?** The basin recovery sim tests one specific noncommuting schedule. Whether other orderings produce basins is untested.

2. **Is there a spectral gap or mixing time for the basin?** The sim shows convergence within ~7 rounds. Whether this is a mixing-time phenomenon or a finite-dimension artifact is untested.

3. **Does the basin survive stronger perturbation?** The sim uses bounded depolarizing noise. Basis-rotated dephasing, partial measurement disturbance, and random unitary kicks are untested.

4. **What is the relationship between viability and basin?** Viability-vs-attractor shows they are distinct. Whether viability is the general case and basin the special case (or vice versa) is open.

5. **Can a Szilard-like feedback loop sharpen a basin?** The conceptual claim is measurement-feedback creates narrower basins. No sim demonstrates this yet.

6. **Can a Carnot-like gradient loop create a basin where none existed?** The negative result says "not at tested parameterization," not "never."

7. **Is there a resource-theoretic monotone that tracks basin depth?** Resource theories contract under channels. Whether contraction rate predicts basin recovery speed is open.

## 6. One Next Proposal Lane Only

**Proposal target:** Extend the basin recovery sim to test whether equivalence-class recovery depends on the specific channel family or generalizes to other noncommuting ordered cycles.

**Probe:** `sim_qit_attractor_basin_generalization.py`

**What it tests:**
- Same basin recovery protocol with 3 different noncommuting channel pairs
- Same perturbation model
- Recovery class defined by the same probe set
- Order-sensitivity test for each pair
- Commuting control for each pair

**What it would support (if it passes):**
- Equivalence-class recovery is a property of noncommuting ordered composition, not a one-off artifact of one specific channel pair

**What it would rule out (if it fails):**
- The basin claim is channel-specific, not general — which is still a finding but weaker

**Why this and not Szilard/hybrid:**
- It extends the strongest existing basin claim rather than starting a new thermodynamics or coordination lane
- It uses the same probe infrastructure (density states, CPTP channels, trace distance)
- It is bounded — one sim, one result, one classification
- The repo now does have a clean Szilard bookkeeping row, but that row does not by itself establish a broader basin or hybrid-engine claim

## 7. Optional Next-Tier Dependencies

**Marked optional. Not needed for the next lane. Would enable later lanes.**

| Tool | What it adds | When to add |
|---|---|---|
| QuTiP | Master equation, Lindblad, fixed-point algebra, spectral gap | When testing mixing time or metastability |
| CVXPY | SDP for CPTP constraints, Choi positivity, witness optimization | When testing basin admissibility via optimization |
| JAX/Dynamiqs | Differentiable engine cycles, gradient search over basins | When optimizing basin depth or recovery speed |
| OQuPy | Non-Markovian process tensors, memory effects | When testing order-sensitive memory in basins |
| Hypothesis | Property-based testing with pathological inputs | When stress-testing basin robustness |

**Not recommended now:** NetKet (many-body, not relevant yet), Qiskit Dynamics (hardware-adjacent, not relevant yet).

## Related Pages

- [[qit-vocabulary-discipline-reference]] — public-term routing and usage discipline
- [[attractor-basins-formal-reference]] — formal definitions and live evidence
- [[distinguishability-formal-reference]] — equivalence-class backbone
- [[distance-metrics-state-space]] — recovery metrics and contractive distances
- [[cptp-maps-and-channels]] — channel/update formalism
- [[qit-engine-proto-ratchet-and-sim-plan]] — engine-as-basin-generator framing
- [[stochastic-thermodynamics-reference]] — thermodynamics backbone
- [[viability-vs-attractor]] — the viability/basin distinction
- [[probe-doc-result-map]] — evidence bridge
- [[qit-engine-geometry-entropy-bridge]] — the open bridge
- [[qit-geometry-thermodynamics-harness-synthesis]] — harness-shaped synthesis of the geometry / thermodynamics split
- [[resource-theories-quantum-reference]] — resource monotone framing
