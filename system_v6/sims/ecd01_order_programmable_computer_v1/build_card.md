# BUILD CARD - ecd01_order_programmable_computer_v1

Status: builder packet, not independent audit.

Write boundary: `system_v6/sims/ecd01_order_programmable_computer_v1/` only. NO git add/commit. Builder must not write `audit_verdict.md`; builder prose goes in `builder_self_assessment.md`.

## Authority

- v0 audit verdict: `system_v6/sims/ecd01_order_programmable_computer_v0/audit_verdict.md`, committed `6e73efa2f`.
- ECD registry contract: `system_v6/receipts/engine_capability_differentiators_20260612.md`, committed `7c3f4b48d`.
- Classical-baseline row: `system_v6/sims/engines_run_with_axes_v0`, audited `de243459e`.
- Standards: `system_v6/receipts/audit_standards_codex_v1.md`.
- Boundary helper: `scripts/builder_audit_boundary.py`.

## Repair

Carry forward the v0 QIT order-channel witness by hash and source lock, not as an earned v0 discriminator:

- registered words `UEUE`, `UUEE`, `UEEU`;
- three distinct label-free channel outputs on the committed 33-state Axis-4 carrier;
- pairwise distances `5.61`, `5.61`, `11.22`;
- commuting-collapse control;
- z3/cvc5 diversity inequality rows.

Replace the v0 hardcoded Szilard baseline with a computed strongest-form plain Szilard table:

- enumerate all `24` permutations of `measure_record_one_bit`, `feedback_isothermal_expansion`, `erase_record`, and `reset_boundary`;
- admit only schedules preserving the plain loop dependency `measure < feedback < erase`;
- let `reset_boundary` float because it is boundary bookkeeping, not an added D/I loop;
- compute every admitted schedule with the same label-free output-multiset fingerprint family as the QIT rows;
- expose a positive predicate: if computed Szilard diversity reaches or exceeds QIT diversity, ECD.01 dies.

## Expected Verdict Surface

The result is the computed discriminator outcome either way:

- if the computed Szilard maximum is `>= 3`, record ECD.01 as killed;
- if the computed Szilard maximum is below `3`, record the max and margin.

For this builder run, the computed baseline maximum is expected to be `2`, so the earned scratch discriminator margin is `1`.

## Controls

- Commuting collapse stays from the QIT side.
- Deliberately weakened enumeration control drops half the admitted schedules and must report sensitivity.
- No identity leak between schedule labels and channel fingerprints.
- Synthetic stronger-baseline control must show the positive predicate would kill ECD.01 if the baseline caught up.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd01_order_programmable_computer_v1/ecd01_order_programmable_computer_v1_jax.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=system_v5/julia_carrier system_v6/sims/ecd01_order_programmable_computer_v1/ecd01_order_programmable_computer_v1_julia.jl
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd01_order_programmable_computer_v1/ecd01_order_programmable_computer_v1_pytorch.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd01_order_programmable_computer_v1/ecd01_order_programmable_computer_v1_envelope.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd01_order_programmable_computer_v1/validate_ecd01_order_programmable_computer_v1.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/ecd01_order_programmable_computer_v1/results/ecd01_order_programmable_computer_v1_envelope_results.json
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/ecd01_order_programmable_computer_v1/tests
```
