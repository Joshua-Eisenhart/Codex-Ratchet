# v7 Foundation Sims — In-Sandbox Cross-Check (2026-07-02)

Owner directed: "check my repo for more stuff to test and explore ... follow the natural
process." The repo `system_v7/sims/` holds 33 foundation-rung sims. The 11 with the full
three-engine structure (julia + jax + pytorch legs + a separate agreement/validator) were
run fresh in-sandbox. julia legs are registry-TLS-blocked here, so committed julia result
JSONs were used where present; jax and pytorch legs were re-executed live.

Environment prep this session (to honor the three-engine dependency contract):
  - jaxcarrier: added z3-solver, cvc5, networkx
  - torchcarrier: added z3-solver, cvc5
  - the sims' sibling `_core` modules require the sim dir on PYTHONPATH.

## Result: 10 / 11 agree; 1 correctly held back by the freshness gate

| Sim (foundation rung) | jax | pytorch | agreement |
|---|---|---|---|
| distinguishability_quotient_floor_v0 (root axiom a=a iff a~b) | OK | OK | AGREE |
| finite_distinguishability_quotient_forced_or_installed_carrier_v0 | OK | OK | AGREE (verdict=installed) |
| finite_probe_quotient_inverse_limit_tower_1q_through_4q | OK | OK | AGREE |
| finite_ring_block_partition_reversible_qca_gnvw_index_v0 | OK | OK | AGREE |
| forced_or_installed_carrier_comparison_v0 | OK | OK | AGREE (build PASS) |
| independent_survivor_restriction_noncommutation_verify_v0 | OK | OK | AGREE |
| mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0 | OK | OK | AGREE |
| ordered_channel_maps_noncommutation_matrix_v0 | OK | OK | AGREE (4 engines) |
| ring_checkerboard_axis2_kt_holonomy_v0 | OK | OK | AGREE |
| ring_checkerboard_euler_conversion_axis2_frame_v0 | OK | OK | AGREE |
| cut_lattice_schmidt_entropy_v0 | OK | OK | HELD (stale exact+julia JSONs, ~13d) |

## What each confirms (invariants that agree across legs)

- **Root axiom / probe-relative quotient.** distinguishability_quotient_floor: S/~_M gives 4
  classes under full M={X,Y,Z}, 3 under erased M={X,Y}; z3+cvc5 flip SAT->UNSAT over exact
  rational expectations. The inverse-limit tower lifts this 1q->4q with quotient counts
  full/erased = {1q:[6,6], 2q:[12,10], 3q:[15,14], 4q:[10,10]} agreeing across legs.
- **Forced vs installed carrier.** verdict=installed, MinSurv={C1}, SMT flip z3+cvc5 unsat/sat.
- **Noncommutation floors.** independent_survivor_restriction: GNVW index {left:-1, right:+1,
  identity:0}, parity_all=True, SMT flip confirmed. ordered_channel_maps: four code paths
  (numpy/jax/pytorch/julia) agree on the noncommutation matrix -- self-noted as a code-path
  cross-check, not an independent-algorithm one (jax+julia share svdvals).
- **Ring-checkerboard / Axis-2.** KT holonomy and Euler-conversion frame both agreement_ok.
- **Z2-equivariance.** mixed_radix: T(sigma(s)) != sigma(T(s)) SAT for nonequivariant map,
  UNSAT for equivariant -- z3+cvc5 agree, a real structural flip not a count tautology.

## Honest findings

1. **cut_lattice_schmidt_entropy correctly HELD.** The agreement gate flagged the committed
   `exact` and `julia` result JSONs as ~13 days older than the freshly-run jax/pytorch legs
   and refused to certify -- exactly the fail-closed staleness discipline. The live jax and
   pytorch legs DO agree exactly (GHZ vs W entanglement gap 0.0817, n4 max-cut S=2.0, product
   state neg 0.0); the HOLD is a freshness-provenance flag, not a numerical disagreement.
   To clear it, the exact+julia legs must be re-run on a machine with the Julia registry.
2. **julia legs are laptop-side.** Same registry-TLS blocker documented earlier; the sims are
   designed to tolerate it (committed julia JSONs + two live legs). Not a correctness issue.

## Verdict

The repo's own foundation rungs independently reproduce, across live jax + pytorch legs, the
same erased-control-that-flips discipline the audit_engines proof lane uses -- and the root
axiom, the distinguishability quotient (through 4 qubits), the noncommutation/GNVW floors, and
the ring-checkerboard Axis-2 holonomy all cross-check clean. The one HOLD is the gate working
as intended, not a failure. Foundations corroborated from two independent codebases.
