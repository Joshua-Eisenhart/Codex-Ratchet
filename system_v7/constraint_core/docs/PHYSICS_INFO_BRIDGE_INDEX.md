# Layer 16 — Physics / Information Bridges (index)

Ten confirmed physics/information results reproduced from the constraint core's own axioms
(noncommutation, finitude, distinguishability a=a iff a~b). NOT ToE validation -- external
grounding: the model agrees with nature wherever nature already has an answer. Every sim is
numpy/scipy-only and runs in the harness (constraintcore full: 44 pass).


## [AUDIT FLAG 2026-07-02 — attribution correction (sixth audit)]
These ten results are theorems of the INSTALLED CARRIER (the C^2/C^8 Hilbert-space
QIT realization, admitted as a candidate under U-1), not derivations from
F01/N01/T01 alone. The axioms did not produce Tsirelson 2sqrt2 or F=5/6; standard
finite-dimensional QM did, and the realization layer IS standard QM by
construction. What Layer 16/17 EARNS is therefore realization faithfulness: the
encoded carrier is bug-free standard QIT (two real encoding bugs were caught by
exactly this discipline) and hence inherits QIT's empirical record. What it does
NOT earn: external grounding for the constraint framework itself — that would
require the axioms to select this carrier uniquely (U-1, open) or a prediction
that differs from standard QM. The line "reproduced from the constraint core's
own axioms" should be read with this flag attached.

## The architecture (not a flat list)

These ten are NOT independent. The DATA-PROCESSING INEQUALITY (16.9) is the spine:
information can only decrease under any physical channel. Most of the others descend from it.

    16.9  DATA-PROCESSING INEQUALITY  (the directional monotone; co-ratchet arrow)
      |
      +-- 16.1  Landauer            erasure costs kT ln2         (info->energy)
      +-- 16.2  Einselection         pointer states = fixed pts   (attractor selection)
      +-- 16.6  Decoherence scaling  ~n / ~n^2 rate growth        (quantum->classical)
      +-- 16.8  Holevo bound         accessible info <= log2 d    (finitude of readout)

    NONCOMMUTATION axiom:
      16.4  Quantum speed limit      [H,rho]!=0 <=> evolution; Levitin-Toffoli speed
      16.7  Uncertainty + CHSH       Maassen-Uffink (bits); Tsirelson 2sqrt2 > classical 2
      16.10 No-cloning               copyable iff orthogonal; UQCM F=5/6 (store, not copy)

    FINITUDE axiom:
      16.5  Holographic / Bekenstein S <= log2 d; Page area law S(A)<=min(|A|,|B|)

    NONEQUILIBRIUM:
      16.3  Jarzynski + Crooks       <e^-bW>=e^-bdF exact; fluctuation theorems

## The two axiom-arcs

NONCOMMUTATION generates, across layers:
  - the PRECONDITION for dynamics (16.4: [H,rho]!=0 <=> the state evolves)
  - the SPEED bound (16.4: Levitin-Toffoli)
  - the UNCERTAINTY bound in bits (16.7: Maassen-Uffink, tight at mutually-unbiased)
  - the CLASSICAL-LIMIT breaker (16.7: CHSH excess to Tsirelson 2sqrt2)
  - PAULI exclusion / the chemical bond (17.1: fermionic antisymmetry)
  - the NO-CLONING limit (16.10: copyable iff distinguishable)

FINITUDE generates:
  - information CAPACITY (16.5: S<=log2 d, saturated by maximally-mixed)
  - the AREA LAW (16.5: Page curve, boundary-limited entanglement)
  - decoherence SCALING (16.6: bigger => faster einselection)
  - READOUT capacity (16.8: Holevo, 4 symbols in a qubit still 1 bit)
  - duplication FIDELITY cap (16.10: F=5/6 < 1)

## Files
| Layer | sim | figure |
|---|---|---|
| 16.1-16.2 | physics_bridge_sim.py | physics_bridge.png |
| 16.3 | fluctuation_theorem_sim.py | fluctuation_theorem.png |
| 16.4 | quantum_speed_limit_sim.py | quantum_speed_limit.png |
| 16.5-16.6 | holographic_bound_sim.py, decoherence_scaling_sim.py | holographic_decoherence.png |
| 16.7 | noncommutation_bounds_sim.py | noncommutation_bounds.png |
| 16.8 | holevo_bound_sim.py | holevo_bound.png |
| 16.9 | data_processing_sim.py | data_processing.png |
| 16.10 | no_cloning_sim.py | no_cloning.png |

## Method notes (per the owner's "report the full process")
- Every constant is COMPUTED, not asserted: Tsirelson 2sqrt2, Holevo log2 d, cloner 5/6,
  Landauer kT ln2 are all measured from constructed operators/states.
- The construct-and-measure discipline caught real bugs mid-build: an un-normalized Bloch
  vector giving Holevo chi>1 (16.8), and a malformed partial trace + non-orthogonal cloner
  branches giving cloner F>1 (16.10). Both fixed; assertions now guard the class of error.
- Findings logged, not hidden: Landauer erases only 0.845 bits under a competing coherent
  drive (full saturation needs pure dissipation); the DPI figure's cross-panel tick overlap
  was re-fixed to a verified 0 after an auditor flag.
