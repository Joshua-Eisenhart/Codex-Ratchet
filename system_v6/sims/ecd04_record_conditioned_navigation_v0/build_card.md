# BUILD CARD - ecd04_record_conditioned_navigation_v0

You are codex1 (high). Repo: `/Users/joshuaeisenhart/Codex-Ratchet`. Build in
`system_v6/sims/ecd04_record_conditioned_navigation_v0/` (file-disjoint).
NO git add/commit. Card into `build_card.md`; use the packet boundary helper;
the standards codex binds, including G.2a from birth.

## Authority

- `system_v6/receipts/engine_capability_differentiators_20260612.md`, row
  `ECD.04`, commit hint `7c3f4b48d`.
- `system_v6/receipts/ecd_registry_supplement_1_20260612.md`, including all
  five addenda: two-sided search, equal information, fair metrics, the ECD.03
  scope lesson, and deaths as results.
- `system_v6/receipts/audit_standards_codex_v1.md`, including G.2a and
  no-identity-leak.
- Audited Szilard fixture `six_bit_two_trigram_szilard_fixture_v0`
  (`7bb60051d`) for record-cost ledgers only.
- Basin feeds: `basin_dof_perturb_and_read_v0`, `carnot_szilard_basin_cycle_v0`,
  `z4_syndrome_record_v0`, and `attractor_basin_criterion_20260611.md`.

## Discriminator

Record-conditioned basin navigation on the committed 33-cell basin estate:

- Shared environment: same pinned start, target terminal basin, RETURN-row
  action success sets, basin partition, and ledger floor rows are exposed to
  both sides.
- Witness gates first:
  - basin nontriviality: multiple reachable terminal/boundary classes exist in
    the shared basin dynamics;
  - information parity: the validator checks that both sides consume the same
    environment manifest before any score is admitted.
- Engine side: searched over admissible committed typed record rows for the
  RETURN action family (`G0`, `G2`, `stage_shift_Rx_to_Rz`).
- Baseline side: searched over fair classical record policies under the same
  environment and Landauer accounting, including no-record, one-bit/parity-like,
  and full branch-identity ledgers.
- Engine scope pin: this v0 means searched configurations over committed typed
  memory rows, not a committed-rigid singleton schedule. Widening to weighted or
  full-engine strategy schedules would be a new registered question.

## Metric

Primary comparison is gated success-weighted record cost:

1. A candidate is primary-eligible only when `target_success_rate == 1.0`.
2. Among primary-eligible candidates, compare `record_cost_nats /
   target_success_rate`.
3. Failed candidates still report `penalized_success_weighted_cost_nats =
   record_cost_nats / max(success_rate, epsilon) + miss_penalty_nats *
   (1 - success_rate)` so deaths and near-misses remain visible.

This avoids rewarding trivially cheap non-navigation. Trivially injective
readouts are allowed only when their full record entropy is paid; they are not
rewarded as metric shortcuts.

## Controls

- Record-erasure regression: erasing engine records must degrade target success.
- Scrambled-records regression: scrambling record/action assignments must
  degrade target success.
- Order-blind collapse: collapsing the RETURN action family to one fixed action
  must fail the primary success gate.
- Dropped-half sensitivity on both sides.
- No identity leak: branch identity recovery is reported and excluded from the
  non-identity predictor row.

## Standard Contract

Use all three engines where scoped, with envelope, validator, tests, and
`builder_self_assessment.md`.

- Julia: `Graphs` and `Z3`.
- JAX/Python: `jax`, `networkx`, `sympy`, `z3`, and `cvc5`.
- PyTorch: `torch`, `torch.func`, `torch_geometric`, `sympy`, `z3`, and `cvc5`.

Expected commands:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd04_record_conditioned_navigation_v0/ecd04_record_conditioned_navigation_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd04_record_conditioned_navigation_v0/ecd04_record_conditioned_navigation_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd04_record_conditioned_navigation_v0/ecd04_record_conditioned_navigation_v0_pytorch.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/ecd04_record_conditioned_navigation_v0/ecd04_record_conditioned_navigation_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd04_record_conditioned_navigation_v0/ecd04_record_conditioned_navigation_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd04_record_conditioned_navigation_v0/validate_ecd04_record_conditioned_navigation_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/ecd04_record_conditioned_navigation_v0/tests/test_ecd04_record_conditioned_navigation_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/ecd04_record_conditioned_navigation_v0/results/ecd04_record_conditioned_navigation_v0_envelope_results.json
```

## G.2a Boundary

G.2a is binding from birth. Validators and tests delegate audit-file handling
to `scripts/builder_audit_boundary.py`; they must not hard-require permanent
absence of `audit_verdict.md`. This builder must not author an audit verdict.

## Ceiling

`scratch_diagnostic`; no QIT-engine admission, basin theorem, thermodynamic
heat/work/bath claim, physical Landauer engine, axis/manifold/physics claim,
or formal admission. Either outcome is the result.
