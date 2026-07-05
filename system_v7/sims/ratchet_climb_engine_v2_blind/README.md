# ratchet_climb_engine_v2_blind

Capstone repair for `ratchet_climb_engine_v1_drive`.

Status: `DRAFT_UNAUDITED`
Classification: `scratch_diagnostic`
Promotion: `promotion_allowed=false`

This sim removes rung identity from the drive path. The drive stream emits only measured facts:

- reduced-state mixedness values;
- commutator norms;
- order-gap norms;
- persistence counts.

The blinded selector enumerates candidate lifts across the ladder, tests whether those facts make the current quotient lossy, and admits only the weakest repairing lift. The append-only lock ledger contains admitted receipts only; refusals live in `rejected_frontier_attempts` and `rejected_unforced`.

Run:

```bash
python3 system_v7/sims/ratchet_climb_engine_v2_blind/ratchet_climb_engine_v2_blind_numpy.py
python3 system_v7/sims/ratchet_climb_engine_v2_blind/ratchet_climb_engine_v2_blind_jax.py
julia system_v7/sims/ratchet_climb_engine_v2_blind/ratchet_climb_engine_v2_blind_julia.jl
python3 system_v7/sims/ratchet_climb_engine_v2_blind/check_agreement.py
python3 scripts/lint_sim_contract.py
```
