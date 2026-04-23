---
title: Stochastic Thermodynamics Reference
created: 2026-04-07
updated: 2026-04-16
type: concept
tags: [reference, geometry, research, planning, entropy, quantum]
sources:
  - raw/articles/new-docs/references/STOCHASTIC_THERMODYNAMICS_REFERENCE.md
  - raw/articles/new-docs/references/FEP_AND_ACTIVE_INFERENCE_REFERENCE.md
  - raw/articles/new-docs/references/INFORMATION_GEOMETRY_REFERENCE.md
  - /Users/joshuaeisenhart/wiki/raw/papers/open_access/meta/webui_deepresearch_candidate_sources_2026_04_10.json
framing: mixed
---

# Stochastic Thermodynamics Reference

## Overview
This reference covers trajectory-level thermodynamics, fluctuation theorems, information-thermodynamic costs, NESS, and the connection to Fisher information.

## Main points
- Stochastic thermodynamics extends thermodynamics to individual fluctuating trajectories of mesoscopic systems far from equilibrium. Defines work, heat, entropy along SINGLE stochastic trajectories, not just ensemble averages. The second law emerges as an inequality on averages; individual trajectories can transiently violate it.
- Jarzynski Equality (1997): <exp(-βW)> = exp(-β ΔF). Exponential average of nonequilibrium work exactly recovers equilibrium free energy difference. By Jensen's inequality: <W> ≥ ΔF (second law as inequality). Individual trajectories can have W < ΔF.
- Crooks Fluctuation Theorem (1999): P_F(W) / P_R(-W) = exp(β(W - ΔF)). Ratio of forward to reverse work distributions exponential in dissipated work. Crossing point at W = ΔF exactly.
- Detailed Fluctuation Theorem: P(Σ_tot) / P(-Σ_tot) = exp(Σ_tot / k). Trajectories producing positive entropy are exponentially more likely. Most fundamental definition: entropy production = log-ratio of forward to time-reversed path probabilities.
- Information-thermodynamics coupling: Landauer's Principle (1961): erasure of one bit costs at least kT ln 2 (experimentally verified, Bérut et al., Nature 2012). Szilard engine: measure which side particle is on (1 bit), extract work W = kT ln 2, erasure closes the books. Sagawa-Ueda generalized second law (2010): <W> ≥ ΔF - kT · I — demon can extract extra work up to kT times information gained.
- NESS: stationary distribution with constant driving, nonzero probability currents, constant entropy production. Housekeeping entropy (maintaining NESS) vs excess entropy (transitions between steady states). FEP's NESS is best treated here as a formal analogy/support bridge to stochastic-thermodynamic NESS language, not as a settled literal identity claim. FEP's surprise `-ln p(x)` is useful adjacent support vocabulary for trajectory-level stochastic entropy, but this page should not collapse the two frameworks into one earned theorem.
- Thermodynamic Uncertainty Relation (Barato-Seifert, 2015): ε² · <Σ_tot>/k ≥ 2. To measure/transmit a current with high precision, you must pay thermodynamic cost. Fundamental trade-off between precision and dissipation. Cannot have precise molecular clock, motor, or sensor without dissipating energy.
- Thermodynamic length (Crooks 2007): excess work bounded by L²/τ. Optimal protocols are geodesics of the thermodynamic metric. The TUR is a special case of Cramér-Rao where Fisher information = total entropy production. Links thermodynamic dissipation directly to information geometry.

## Quantum extensions

### Quantum Jarzynski and Crooks relations
Classical fluctuation theorems extend to quantum systems via two-point measurement (TPM) scheme: measure energy at t=0 and t=tau, define work as difference W = E_n(tau) - E_m(0). The quantum Jarzynski equality holds: <exp(-beta W)> = exp(-beta Delta F), identical in form to classical but work is now a stochastic quantum variable from projective measurements.

Key difference: quantum coherence affects the work distribution. If the initial state has coherence in the energy basis, the TPM scheme destroys it (measurement backaction). Deffner & Lutz (2011) showed that coherence modifies the generalized second law: <W> >= Delta F + kT S(rho||rho_diag), where the extra term is the relative entropy between the state and its diagonal (dephased) version.

### Quantum fluctuation theorems with coherence
- Tasaki-Crooks theorem (2000): quantum version holds for driven quantum systems when work is defined via TPM
- Quantum detailed fluctuation theorem: P(+Sigma)/P(-Sigma) = exp(Sigma/k) still holds at trajectory level
- Role of coherence: systems starting in energy eigenstates satisfy classical fluctuation theorems exactly; coherent initial states show deviations tied to the Wigner-Yanase skew information

### Quantum Landauer's principle
Landauer's bound kT ln 2 per erased bit extends to quantum regime:
- Quantum Landauer (Reeb & Wolf, 2014): for erasure of a quantum system with initial state rho, the minimum heat dissipated is Q_min = kT S(rho), where S is von Neumann entropy. Classical bound kT ln 2 is the special case for a maximally mixed bit.
- Experimental verification in quantum systems: Yan et al. (2018) verified quantum Landauer in a single-electron quantum dot.
- Implications for quantum computation: reversible quantum gates (unitaries) cost zero thermodynamic entropy; irreversible operations (measurements, resets) have irreducible costs.
- Strong-coupling correction: arXiv:1006.1420 argues that apparent Landauer / Clausius violations in the quantum domain come from inconsistent bookkeeping when the subsystem is strongly correlated with its bath. The reduced subsystem is no longer Gibbs-thermal on its own, so interaction and correlation terms must remain in the heat / entropy / work accounting.

### Maxwell's demon in this system
Maxwell's demon is not treated as a free work source here. In the repo-side reference framing used by this wiki, measurement can create one-bit system-memory correlation, ordered feedback can convert that correlation into one-bit free-energy gain in a bounded model, and erasure closes the books at the same kT ln 2 scale. The demon paradox is therefore treated here as bookkeeping, not miracle extraction.

A useful repo-side split in the cited audit surfaces:
- `sim_qit_szilard_landauer_cycle.py` is the bounded owner candidate for finite measurement-feedback-erasure bookkeeping; the file self-classifies as canonical on disk, but public promotion should still follow the applicable truth-audit surface.
- `demon_fixed_sim.py` is an older supporting sidecar that contrasts eigenbasis-sensitive measurement against the broken computational-basis version and still respects the Landauer-side bound.

### Thermodynamic resource theory (TOA framework)
The resource-theoretic approach (Brandao, Horodecki et al., 2013-2015) treats thermodynamics as a resource theory with:
- Free operations: thermal operations (energy-conserving unitaries + access to thermal bath)
- Free states: thermal Gibbs states rho_th = exp(-beta H)/Z
- Resources: states with "athermality" (negative relative entropy to thermal state)

Key results:
- Second laws of thermodynamics: not just one second law but a whole FAMILY of constraints, given by monotones under the stated thermal-operation assumptions. Majorization is the complete set of conditions only in the relevant constrained transition settings, not as a universal shortcut for every thermodynamic transition.
- Catalyst-assisted transformations: strict advantage over unassisted transitions (Brandao et al., 2015)
- Quantum coherence as a thermodynamic resource: coherence in energy basis enables transitions impossible without it (Lostaglio et al., 2015)

### Finite-time quantum thermodynamics
- Geometric approach to quantum speed limits: Mandelstam-Tamm bound gives minimum time for state transitions, directly connected to quantum Fisher information
- Optimal control in quantum heat engines: finite-time Carnot bound requires quantum geometric tensor as cost function
- Quantum TUR (Timpanaro et al., 2019; Hasegawa, 2020): thermodynamic uncertainty relation extends to quantum regime, with quantum coherence reducing the TUR bound -- quantum systems can achieve higher precision at lower dissipation than classical TUR predicts


## 2026-04-10 intake upgrades (audited WebUI return snapshot)
These additions are queued as candidate citations and wording fences, not as downloaded proof surfaces.

- Best next citation adds for this lane: Reeb-Wolf (finite-size Landauer corrections), Faist et al. (minimal work cost of information processing), Sagawa-Ueda (measurement / feedback / erasure cost), and Parrondo-Horowitz-Sagawa on information thermodynamics.
- Best wording fence from the audited return: do not call an abstract entropy drop a physical Landauer erasure unless the memory, reset map, bath temperature, and logical irreversibility are explicit.
- Strong-coupling guardrail to keep: apparent Landauer or Clausius failure at strong coupling is a reduced-bookkeeping artifact unless interaction and correlation terms are retained.
- The previously targeted stochastic double-well erasure lane is also present as a repo row: `sim_stoch_doublewell_landauer_erasure.py` with `stoch_doublewell_landauer_erasure_results.json`. It is still exploratory and needs rerun / intake discipline before promotion.

## Repo Thermodynamics Snapshot (dated audit note)
The strongest thermodynamics row in this snapshot is pure density-matrix language, not engine analogy.

- `sim_pure_lego_quantum_thermodynamics.py` with `pure_lego_quantum_thermodynamics_results.json` is the clean QIT owner surface for thermal states, free energy, Landauer, extractable work, and the Carnot upper bound.
- `sim_qit_strong_coupling_landauer.py` with `qit_strong_coupling_landauer_results.json` is the clean finite owner row for the `1006.1420` correction: reduced-system bookkeeping can look wrong at strong coupling, while full joint system-bath bookkeeping still closes.
- `sim_carnot_gradient_bound.py` plus `carnot_gradient_bound_validation.json` is a runtime analogy probe only. It is useful because it fails honestly: no stable Carnot-like runtime bound emerged at the tested parameterization.
- `sim_qit_carnot_two_bath_cycle.py` with `qit_carnot_two_bath_cycle_results.json` is on disk as a bounded two-bath cycle row whose file metadata self-classifies as canonical. Until there is a fresh rerun in this lane, keep the public status at `exists` rather than silently promoting it higher.
- `sim_qit_carnot_finite_time_companion.py` and `sim_qit_carnot_hold_policy_companion.py` are research-support companions that narrow finite-time and hold-policy behavior without replacing the bounded two-bath owner row.
- Szilard coverage now has one bounded owner candidate row plus multiple bounded support rows. `sim_qit_szilard_landauer_cycle.py` is the bounded owner surface for one-bit measurement-feedback-erasure bookkeeping, but public status should stay aligned with the applicable truth audit rather than the file's self-classification; `sim_qit_szilard_record_companion.py` and `sim_qit_szilard_substep_companion.py` are research-support companions; `szilard_64stage_v2_sim.py` and `sim_szilard_operator_accounting.py` remain exploratory engine-side probes.
- `demon_fixed_sim.py` plus `demon_fixed_results.json` is a supporting Maxwell-demon sidecar, not the owner row. It is still useful because it shows that eigenbasis-sensitive measurement avoids the broken computational-basis demon story while leaving the Landauer-side bookkeeping intact.
- `sim_stoch_doublewell_landauer_erasure.py` and `sim_stoch_harmonic_carnot_cycle.py` are also present as exploratory stochastic rows. They are useful because they move the lane closer to trajectory-level bookkeeping rather than a pure engine analogy.
- `sim_engine_lab_matrix.py` with `engine_lab_matrix_results.json` is a controller-facing comparison surface across Carnot and Szilard rows. It is exploratory and organizational, not itself an owner proof row.
- For engine interpretation, the useful snapshot-level split is: Carnot-like loops behave like bounded two-bath or gradient-shaped process circulators, while Szilard-like loops behave like measurement-feedback local stability shaping or local recurrence maintenance.

## 2026-04-10 arXiv source additions

These are support additions for the stochastic-thermodynamics lane.

### 1810.05583v5 — Thermodynamic length in open quantum systems
- Shows how dissipation can be characterized by a metric on Gibbs states in open quantum systems.
- Strong fit for thermodynamic length, geometric protocols, and information-geometry coupling.
- Best fit pages: [[stochastic-thermodynamics-reference]], [[information-geometry-reference]], [[distance-metrics-state-space]].

### 1210.5071v1 — Stochastic Thermodynamics, Reversible Dynamical Systems and Information Theory
- Connects stochastic thermodynamics with reversible dynamical systems and information-theoretic quantities.
- Useful for trajectory-level bookkeeping and the dynamics/information interface.
- Best fit pages: [[stochastic-thermodynamics-reference]], [[qit-basin-engine-synthesis]], [[research-support-bibliography]].

### 2309.13408v2 — On the unraveling of open quantum dynamics
- Gives a trajectory-picture for open quantum dynamics via unraveling.
- Useful where the wiki needs an open-system dynamics support row rather than a closed-system idealization.
- Best fit pages: [[stochastic-thermodynamics-reference]], [[cptp-maps-and-channels]], [[current-research-overlays]].

## 2026-04-10 arXiv source addition

### 1006.1420 — Landauer’s principle in the quantum domain
- Argues that apparent strong-coupling violations of Landauer are bookkeeping errors when correlations and interaction terms are handled correctly.
- Useful for strong-coupling guardrails, Holevo-bound bookkeeping, and the boundary between reduced and joint-system thermodynamics.
- Best fit pages: [[stochastic-thermodynamics-reference]], [[quantum-information-measures]], [[qit-vocabulary-discipline-reference]].

## Why it matters
This reference sits near the junction of thermodynamics, inference, and distinguishability geometry. The Fisher-Rao metric connects thermodynamic length to the system's geometry layer. The quantum extensions are directly relevant to the system's entropy architecture: quantum coherence as a resource parallels the system's treatment of entanglement as a structural feature, not noise. See [[information-geometry-reference]] for the geometric foundation, [[fep-and-active-inference-reference]] for the bounded NESS/support analogy, and [[entanglement-theory]] for the coherence/entanglement resource structure.

## Related pages
- [[qit-vocabulary-discipline-reference]]
- [[resource-theories-quantum-reference]]
- [[fep-and-active-inference-reference]]
- [[information-geometry-reference]]
- [[distinguishability-formal-reference]]
- [[viability-theory-reference]]
- [[quantum-information-measures]]
- [[quantum-fisher-information-geometry]]
- [[entanglement-theory]]
- [[density-matrix-mathematics]]
- [[entropy-sweep-protocol]]
- [[qit-geometry-thermodynamics-harness-synthesis]]
