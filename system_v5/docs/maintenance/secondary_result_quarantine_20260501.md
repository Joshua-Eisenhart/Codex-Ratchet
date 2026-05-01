# Secondary Result Quarantine - 2026-05-01

## Decision

Move the legacy secondary result root out of active sim result routing.

## Moved

- `system_v4/probes/sim_results/lego_pauli_algebra_results.json`
  -> `work/hygiene_quarantine/secondary_duplicate_results/20260501T062300Z/lego_pauli_algebra_results.json`
- 28 unique `system_v4/probes/sim_results/*.json`
  -> `work/hygiene_quarantine/secondary_unique_results/20260501T062329Z/`

## Kept Active

- `system_v4/probes/a2_state/sim_results/lego_pauli_algebra_results.json`

## Evidence

The active `a2_state` Pauli result is the safer canonical copy:

- classification: `classical_baseline`
- has `tool_integration_depth`
- has truth-audit demotion fields
- SHA-256: `a933e4d46cf43247c350e1ecaa58a89d16f95f25a431a6bbd91b2d73f386d703`

The secondary Pauli result was quarantined because it was a conflicting active duplicate:

- classification: `canonical`
- missing `tool_integration_depth`
- missing truth-audit demotion fields
- SHA-256: `c17bae394251fbe22d4b2a57106b82ff7766a59093bab4a8c109f2acc63294ef`

## Verification

- `python3 system_v4/probes/system_hygiene_repair.py --include-secondary-unique --apply`
- `find system_v4/probes/sim_results -maxdepth 1 -type f -name '*.json' -print`

The secondary result root has no remaining active JSON files after the move.
