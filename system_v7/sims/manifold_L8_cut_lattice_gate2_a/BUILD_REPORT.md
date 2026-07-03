# manifold_L8_cut_lattice_gate2_a Build Report

Status: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

Source spec: `system_v7/sims/GATE2_SPEC_EXTRACTION_20260703.md`.

## Scope

L8 cut lattice only. The owner-tunable bundling choice was followed as:
`OPEN-CHOICE followed: do not bundle L9/L10`.

## Cut Count Pin

Chosen formula: `2^(n-1)-1`.

Reason: the referee addendum identifies this as the contract L8 unordered-bipartition wording. For `n=3`, the enumeration is the 3 labelled-party unordered cuts:

- `q0__q12`
- `q1__q02`
- `q2__q01`

The rejected alternative `2^n-2 = 6` counts ordered non-trivial party subsets. Cuts are party-indexed, but the quotient acts on states only, never cut labels.

## Enumeration

- finite Gate 1 roster states consumed: 40
- Gate 1 full quotient classes consumed: 40
- full Pauli quotient classes recomputed: 40
- coarse `ZII` quotient classes recomputed: 3
- L8 unordered cut count: 3
- nonempty subset lattice nodes: 7
- per-cut side marginal records: 240
- compatibility checks: 760
- extension-fiber nodes: 7

Gate 1 note: the consumed R4 observable quotient gate is clear; Gate 1 global `all_pass` remains false because `Xi_ref` coarse quotient-lift is demoted.

## Controls

- product/separable negativity zero: PASS, `[0.0, 0.0, 0.0]`
- finite roster entangled nonzero negativity: PASS, `stage_6_Fe_operator_first` on `q1__q02`, negativity `0.17584356530183354`
- perturbed marginal rejected: PASS
- alternate probe family changes quotient: PASS, full `40` vs coarse `3`
- lineage removed rejected: PASS
- cut-lattice divergence control: PASS
- label-echo seam control: PASS; label echo would pass, computed partial trace rejects `terrain_0_fixed` paired with `stage_0_Ti_terrain_first` marginal
- coarse epoch lift not promoted: PASS, Gate 1 status `demoted_to_raw_carrier_discriminator`

## Parity

NumPy and Julia legs pass independently. Agreement parity:

- tolerance: `1e-9`
- max absolute difference: `2.220446049250313e-16`
- failures: none

## Artifacts

- `manifold_L8_cut_lattice_gate2_a_numpy.py`
- `manifold_L8_cut_lattice_gate2_a_julia.jl`
- `check_agreement.py`
- `spec.json`
- `results/manifold_L8_cut_lattice_gate2_a_numpy_results.json`
- `results/manifold_L8_cut_lattice_gate2_a_julia_results.json`
- `results/manifold_L8_cut_lattice_gate2_a_agreement_results.json`
