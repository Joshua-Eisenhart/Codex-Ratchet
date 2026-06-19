BOTTOM LINE: COMMIT_READY at scratch_diagnostic ceiling.

Binding Codex verdict: the carrier-grounded packet DOES earn
"constraint-driven compression on M(C)" in the narrow, probe-relative,
finite-carrier sense. It does not earn physics, Axis0, manifold, literal
retrocausation, canonical status, or promotion of the frozen M(C) carrier.

Claim ceiling:

- classification: scratch_diagnostic
- promotion_allowed: false
- formal_admission_allowed: false
- honest claim: a global co-admissibility compressor on the real frozen
  gcm_constraint_carve_v1 M(C) carrier differs from forward greedy controls, and
  the selected present survivor moves when the constraint/probe family is changed
  while the density matrices are held identical.

What I checked:

- Ran the packet validator with the required interpreter:
  `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/retrocausal_possibility_field_carrier_grounded_v0/validate_retrocausal_possibility_field_carrier_grounded_v0.py`
  Result: ok=true; errors=[].
- Ran packet tests:
  `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/retrocausal_possibility_field_carrier_grounded_v0/tests/test_retrocausal_possibility_field_carrier_grounded_v0.py`
  Result: 6/6 passed.
- Independently compared the observable-sign classes against the frozen carve
  quotient classes, not just the class count.
- Independently reran the constraint-surgery readout from the module functions.
- Checked the partition-dependence report against a fresh population-frequency run.

Fresh facts:

- Frozen carrier: 16 survivors loaded from
  `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_results.json`.
- Frozen carve quotient: 8 classes.
- Observable-sign classes under C=(sigma_x, sigma_z): exactly the same 8 survivor-id
  pairs as the carve quotient:
  `[0,3]`, `[1,4]`, `[2,5]`, `[6,8]`, `[7,9]`, `[10,13]`, `[11,14]`, `[12,15]`.
- Constraint surgery C -> C' by appending `sigma_y` changes the class count from
  8 to 16 while the carrier digest stays fixed.
- Global present survivor before surgery: `b14`.
- Global present survivor after surgery: `b10`.
- Forward controls under C select `b10`; global under C selects `b14`.
- Canonical partition reselects by the deterministic lexicographic-first rule.
- Population-frequency check reports:
  - global-vs-greedy separation fraction: 0.33
  - constraint-surgery move fraction: 0.4495
  - both fraction: 0.1665

Arbiter conclusion:

COMMIT_READY. The packet is a genuine constraint-driven compression receipt on the
real frozen M(C) carrier, with the explicit partition-dependence caveat. The honest
ceiling remains scratch_diagnostic only.

Commit hygiene:

Do not stage `__pycache__/` or `.pyc` files. Stage only intended source, tests,
result JSON, and this audit verdict if committing this packet.
