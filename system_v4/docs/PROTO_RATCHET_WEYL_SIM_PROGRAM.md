# Proto-Ratchet Weyl Sim Program

**Date:** 2026-03-29

## 1. Status

This is a controller-facing sim-program packet for the Weyl-manifold shift.

- proposal only
- not canon
- not a doctrine promotion packet
- not a replacement for current geometry or axis authority surfaces

It exists to turn the Weyl-manifold shift into discriminating simulation work instead of leaving it as prose.

---

## 2. Purpose

The purpose of this packet is to test a stronger proposal:

- left/right Weyl spinors are ambient manifold-side structure outside the engines
- the engines are degrees of freedom running on that geometry
- nested Hopf tori are a strong but potentially intermediate realization rung
- `Axis 0` remains a later cut-state functional after a bridge into `rho_AB`

The sim program should discriminate:

1. ambient geometry versus engine overlay
2. direct carrier geometry versus intermediate torus realization
3. operational axis locks versus deeper geometric bindings

The sim program should not:

- collapse geometry into `Axis 0`
- treat current operational axis locks as final metaphysical truth
- use raw local `L|R` as a sufficient `Axis 0` bridge

---

## 3. Existing Sim Ground

The current sim base already gives a strong starting floor.

### Geometry-validity ground

- `sim_L0_s3_valid.py`
  - validates `S^3`, `SU(2)`, Hopf map, fiber invariance, Berry phase, toroidal coordinates, and Bloch round-trip
- `axis0_full_constraint_manifold_guardrail_sim.py`
  - tests the full object with explicit left/right Weyl spinors on nested Hopf tori, fiber/base loops, terrain cycles, and `L|R` readout
  - establishes the guardrail that local-only evolution should not create nontrivial mutual information from a product state

### Axis 0 bridge/cut discrimination ground

- `axis0_xi_strict_bakeoff_sim.py`
  - cleanest current full-stack bridge discriminator
  - keeps `Xi_LR_direct`, `Xi_shell_cq`, and `Xi_hist_cq` separate
  - already supports the current rule that raw `L|R` is only control, not finished `Axis 0`

### Current operational axis ground

- `sim_Ax3_density_path.py`
  - supports the fiber/base density split
- `sim_Ax4_commutation.py`
  - supports the current Ax4 ordering distinction at the operator-sequence level
- `sim_Ax5_TF_kernel.py`
  - supports the corrected T/F operator family
- `sim_64_address_audit.py`
  - supports the structural addressing and Ax6 closure

So the new program should extend from a real base, not start from zero.

---

## 4. Sim Lane A

### Name

Weyl Ambient Versus Engine Overlay

### Question

Is left/right Weyl structure ambient to the engines, or mostly an engine-indexed working overlay on the current realization?

### Minimal design

1. construct matched geometric samples with the same carrier/Hopf/NHT placement
2. vary engine DOF while holding Weyl ambient variables fixed
3. vary Weyl ambient variables while holding engine DOF fixed
4. record which observables change under each variation

### Suggested observables

- sheet-sensitive invariants on `(psi_L, psi_R, rho_L, rho_R)`
- carrier-level invariants on `S^3`, Hopf image, and torus placement
- engine-side outputs from terrain/order/operator evolution
- control `L|R` MI and any bridge-candidate readouts kept strictly separated

### What would count as signal

- if Weyl-side changes alter structure even when engine DOF are held fixed, that supports ambient status
- if Weyl-side changes only appear through engine labels, that supports overlay status

### Reuse from existing sims

- geometry generation from `sim_L0_s3_valid.py`
- honest full-object construction from `axis0_full_constraint_manifold_guardrail_sim.py`

---

## 5. Sim Lane B

### Name

Ax3 / Ax4 Rebinding Stress Test

### Question

Do current Ax3 and Ax4 bindings survive when the engine is explicitly treated as DOF on Weyl ambient geometry rather than as the deepest available structure?

### Minimal design

1. keep the current fiber/base split intact as the direct carrier-geometry baseline
2. add Weyl ambient labels and winding/chirality-aware observables
3. compare current Ax3/Ax4 classification against alternative ambient-aware classifications
4. identify where the current bindings are invariant versus where they are only operational proxies

### Suggested observables

- density-stationary versus density-traversing behavior
- operator-order distinguishability
- chirality-aware phase / winding summaries
- stability of current Ax3/Ax4 labels under ambient perturbation

### What would count as signal

- Ax3 remains robust if fiber/base still dominates the classification under ambient-aware perturbation
- Ax4 remains robust if the current ordering split still predicts the main distinguishability class
- either becomes suspect if ambient chirality/winding structure explains more than the current binding

### Reuse from existing sims

- path classification from `sim_Ax3_density_path.py`
- ordering probe from `sim_Ax4_commutation.py`

---

## 6. Sim Lane C

### Name

Full Ratcheting Geometry Ladder Audit

### Question

Which rung in the proposed ladder is real, which is merely naming, and which first becomes unstable?

### Ladder to test

```text
constraints
-> admissible math
-> probe/state layer
-> spinor carrier
-> Hopf/Bloch
-> nested Hopf tori
-> Weyl ambient sheets
-> engine DOF
-> bridge candidates
-> Axis 0 kernels
```

### Minimal design

1. assign one explicit witness or invariant to each rung
2. require each rung to constrain the next rung in a detectable way
3. track where the chain becomes underdetermined or purely notational

### Suggested rung checks

- roots to admissible math: finite/noncommutative witness discipline
- admissible math to carrier geometry: state/probe realization validity
- carrier geometry to Hopf/NHT: geometric invariants
- Weyl ambient sheets to engine DOF: nontrivial ambient-versus-overlay separation
- bridge candidates to `Axis 0`: nontrivial cut-state behavior beyond raw local `L|R`

### What would count as signal

- first rung with no independent witness marks the current weak point
- first rung where two non-equivalent constructions give the same outputs marks overcompression risk
- first rung where current engine law no longer tracks the deeper structure marks a rebinding target

### Reuse from existing sims

- geometry validation from `sim_L0_s3_valid.py`
- full-object guardrail from `axis0_full_constraint_manifold_guardrail_sim.py`
- bridge discrimination from `axis0_xi_strict_bakeoff_sim.py`

---

## 7. Mechanical Verify Targets

This packet should be considered mechanically complete only if all of the following are explicit.

1. three sim lanes are named and bounded
2. each lane states one exact question
3. each lane states minimal design steps
4. each lane states observables
5. each lane states what would count as positive signal
6. each lane reuses current sim ground where possible
7. no lane promotes doctrine
8. `Axis 0` remains bridge-late in the whole program

Suggested future verify commands for implementation runs:

- lane-local result JSON existence
- expected evidence-token emission
- explicit guardrail that raw local `L|R` remains control-only
- compile guard for `engine_core.py`

---

## 8. Controller Read

Best current controller read:

- do not jump straight from the Weyl-manifold proposal to new doctrine
- first test whether the proposal changes layer placement, axis binding, or only interpretation
- keep current operational axis locks usable
- use the new sim program to find where the current stack is genuinely too shallow

Priority order for implementation:

1. Lane A
2. Lane B
3. Lane C

Reason:

- Lane A tests the main proposal directly
- Lane B tells us whether Ax3/Ax4 are merely operational or actually deep
- Lane C gives the full ladder audit only after the two sharper discriminators exist

This is the right next step if the goal is to turn the Weyl-manifold shift into executable pressure without prematurely rewriting the canon stack.
