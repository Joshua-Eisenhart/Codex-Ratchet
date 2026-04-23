# [Controller-safe] RUNTIME TO STRUCTURE BRIDGE

**Date:** 2026-03-27
**Purpose:** This document enforces strict epistemic reality. It explicitly demarcates what is mathematically secured at the runtime layer versus what remains theoretical hypothesis at the structural 64-state layer.

To prevent premature canonization, developers and controllers must consult this bridge before assuming any structural bit mapping has been validated by a live engine.

---

## 1. What Runtime Fields Are REAL NOW
These runtime layers are implemented and observable in `engine_core.py`, but not all of them should be mistaken for fully recovered higher-layer ontology.

1. **The runtime carrier:** The live engine evolves paired left/right density states together with geometric chart variables like `eta`, `theta1`, `theta2`, and `ga0_level`.
2. **The 8 macro-terrains:** The environment topologies (fiber/base loop, expansion/compression, open/closed) form 8 real, distinct operational zones (`Se`, `Si`, `Ne`, `Ni`, etc.).
3. **The 4 base operators:** The internal execution constraints (`Ti`, `Fe`, `Te`, `Fi`) actively modify the runtime state.
4. **The left/right engine asymmetry:** Type 1 and Type 2 execute non-symmetrically and produce robustly distinct trajectories (type divergence pass rate: 1.0).
5. **The internal Ax0 control (`ga0_level`):** A live runtime control exists, but it is **the weakest runtime surface**. `sim_engine_mass_sweep.py` shows an Ax0 program pass rate of only `0.2917`. The current implementation realizes Ax0 mainly through Hopf-fiber coarse-graining plus blend, not yet as the stronger meta-gradient the architecture requires.
6. **The 64-step runtime path:** The current execution sequence (`8 terrains × 4 operators × 2 engine types`) is real and deterministic. However, the decoder shows it is **highly scripted and seed-invariant** under default controls (100% identical across seeds), meaning the current control regime produces a narrow, deterministic slice, not a richly varied traversal.

---

## 2. What Structural Bits are ONLY HYPOTHESES
These are heavily investigated semantic mappings that fit beautifully into the `[Proposal scaffold]` (the 64-Hexagram State Space) but **have not yet been definitively mathematically coupled** to the LIVE runtime engine. Do not treat them as canon until a structural bridge script successfully reads them back from the live execution.

1. **Ax3 as spinor phase / left vs right:** The spinor-layer lane is promising, but no final automated translation from live runtime variables to an `Ax3 line` is secured.
2. **Ax4 as process traversal (CW vs CCW):** Process-history probes suggest a signal may exist, but no canonical live Ax4 operationalization is secured yet.
3. **Ax5 as torus hysteresis / curvature:** Torus-layer probes are promising. Under **default controls**, Ax5 is dormant (the engine stays on the Clifford torus and the decoder reads 0% active). Torus-programmed runs do move it, so it is **dormant by default**, not structurally absent. The engine's internal operators are not yet classified as `Ax5=0` vs `Ax5=1` inside the live execution array.
4. **The 8×8 structural map:** The `8 Terrains × 8 Signed Operators = 64` decomposition is the strongest current scaffold, but it remains a proposal until the runtime can be decoded back into structural 6-line states on demand. The decoder currently visits only 21–23 of 64 states.

---

## 3. What is NOT YET DECODED
These zones remain entirely experimental.

1. **Holodeck / FEP Integration:** The Holodeck FEP engine currently validates its own internal pipeline on synthetic toy states. A live runtime bridge from engine output to FEP metrics is not yet in place, so the lane remains exploratory.
2. **Non-Canon Axes (Ax7-Ax12):** The Lie algebra representations and structural mappings of the commutator-derived axes are completely untested against the new Phenomenological Design constraints (they still rest on the older density-matrix assumptions).
3. **A2 to A1 Sync Protocol:** The mechanism for translating the 64 geometric states into the jargoned text-graph logic operating in `A1_JARGONED` has not been finalized.

---

## Conclusion
If a document or agent claims "the lanes are fully synchronized" without providing a script that directly translates `engine_core.py` local variables into 6-line structural state arrays at run-time, the claim is false.

**Stabilize the local math first, explicitly bridge it to the structure second, canonize it last.**
