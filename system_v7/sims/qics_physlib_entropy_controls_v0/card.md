# card — qics_physlib_entropy_controls_v0

Lane: external-review immediate item 4 — wire QICS + Physlib as CONTROLS for associative entropy claims.
Date: 2026-07-10. Classification: scratch_diagnostic. promotion_allowed: false.

## Obligation

A finite control battery for Umegaki relative entropy DPI on 1-qubit CPTP channels drawn
from the repo's own 16-stage contract, verified numerically via QICS, plus one
deliberately-false variant (a non-CPTP map) where DPI must FAIL and the instrument must
detect the failure. Separately: record the exact scope of the machine-checked DPI
statement in Physlib (Lean 4), if checkable tonight.

## Sources (read-only inputs)

- Channel contract: /Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/engines/targets.json
  (READ-ONLY — never write to anything under constraint_core). 16 stages = 8 terrain
  GKSL generators (t0..t7: damp/depol/proj Lindblad terms + coherent H = eps(sx+sy+sz)/sqrt3,
  G=0.35, KAP=1.0, T_FLOW=1.0, RK4 N_STEPS=400) x 2 native operators
  (Ti/Te = pinching with Q=1-e^-1; Fi/Fe = unitary rotation TH=pi/4).
  Math spec: constraint_core/engines/oracle_targets.py (read for the math, re-implement
  locally; do not import from constraint_core at runtime).
- QICS checkout: /Users/joshuaeisenhart/GitHub/qics (qics 1.1.3), PYTHONPATH pattern per
  /Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/qics_entropy_dpi_numeric_oracle_v0/run_all.sh
  (working example — read first).
- Python: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 (verified: imports qics 1.1.3
  with PYTHONPATH=/Users/joshuaeisenhart/GitHub/qics).
- Physlib checkout: /Users/joshuaeisenhart/GitHub/physlib (Lean 4, leanprover/lean4:v4.31.0,
  oleans built 2026-07-09). Target theorem: QuantumInfo/Entropy/DPI.lean
  `sandwichedRenyiEntropy_DPI (hα : 1 ≤ α) ... : D̃_α(Φ ρ‖Φ σ) ≤ D̃_α(ρ‖σ)` with
  `qRelativeEnt = D̃_1` (Umegaki) by definition in Entropy/Relative.lean.

## Battery (all pure math, seed 0, deterministic, standalone)

Channels under test (28 total, all as 4x4 Choi matrices + Bloch-affine action):
1. 8 terrain flows exp(T_FLOW * L_t), t=0..7 (RK4, N_STEPS=400, float64).
2. 4 operator channels Ti, Te, Fi, Fe.
3. 16 composed stages op∘flow (the contract's 'down' composition).

Anchor to the repo contract: for each of the 16 stages, applying the local
re-implementation to the standard probe (0.55,0.35,0.25) must reproduce
targets.json bloch_down within 1e-6 (bloch_abs tolerance). If any stage misses,
the battery ABORTS — the channels are then not "the repo's channels".

State pairs per channel: (probe, maximally mixed), (probe, terrain fixed-point-like
state), and 4 seeded random full-rank qubit pairs (numpy default_rng(0)). All sigma
full-rank so S(rho||sigma) finite.

Checks per channel:
- CPTP structure: Choi matrix PSD (min eig >= -1e-9), partial trace = I (trace preserving).
- DPI: S(rho||sigma) >= S(N(rho)||N(sigma)) - 1e-9, entropy evaluated by QICS
  (qics quantum relative entropy routine — load-bearing; the exact callable per the
  qics_entropy_dpi_numeric_oracle_v0 packet), cross-checked against a local
  eigendecomposition Umegaki formula (agreement <= 1e-8).

## False variant (the instrument must catch it)

A trace-preserving, unital, NON-CP Bloch expansion: r_bloch -> c * r_bloch with c = 1.5,
applied to state pairs pre-shrunk into the Bloch ball so outputs remain valid states.
Required detections, both mandatory:
- Choi matrix has a negative eigenvalue (structural non-CPTP detection).
- At least one pair with S(N(rho)||N(sigma)) > S(rho||sigma) + 1e-6 (DPI violation detection).
If either detection fails, exit nonzero. A battery that cannot fail is not a control.

## Physlib control (separate check, run by lane runner, not codex1)

`lake env lean` on a scratch file importing QuantumInfo.Entropy.DPI with
`#print axioms sandwichedRenyiEntropy_DPI`. Record: axiom footprint (must be free of
sorryAx), exact statement scope (finite-dimensional MState, CPTPMap, sandwiched Renyi
alpha >= 1; Umegaki as the alpha = 1 instance by definition). If the check cannot be run
tonight, record as open item — do not fake it.

## Ceiling (explicit)

These are associative-entropy CONTROLS on matrix-algebra (associative) quantum channels.
No exceptional/Jordan-algebra DPI inference is licensed by any result here. Umegaki
relative entropy and CPTP structure as used are associative-algebra objects; nothing in
this packet admits, supports, or excludes any DPI claim for exceptional Jordan algebras.
Classification: scratch_diagnostic. promotion_allowed: false.

## Deliverables

- qics_physlib_entropy_controls_v0.py (battery, --output result.json)
- run_all.sh (self-test, run, validate, deterministic rerun compare, per the
  qics_entropy_dpi_numeric_oracle_v0 pattern, but with the sim-stack python)
- result.json + rerun_result.json (append-only; never overwrite existing results — version)
- physlib_dpi_axiom_check.txt (lane-runner-produced Lean receipt or open-item note)
- RESULTS.md written last, from measured outputs only
