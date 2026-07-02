# Engine-Priority Runtime Suite - 2026-05-23

Status: local Codex controller run, fresh-rerun validated.

This round keeps getting the operational engines working as the primary task.
Instead of running shell cuts, flux, or IGT selectors as detached toy math, the
first scout consumes the current runtime row schedules from
`canonical_qit_engine_specs.py` and applies the three requested directions to
engine-row histories. A second scout then tightens the weak point by consuming
actual source-aligned runtime stage trajectories from
`source_aligned_qit_engine_runtime.py`.

## Scout

Script:

`system_v5/ops/formal_scouts/sim_runtime_priority_work_suite_probe.py`

Result:

`system_v5/ops/formal_scouts/results/runtime_priority_work_suite_probe_results.json`

Tightening script:

`system_v5/ops/formal_scouts/sim_runtime_trajectory_receipt_coupling_probe.py`

Tightening result:

`system_v5/ops/formal_scouts/results/runtime_trajectory_receipt_coupling_probe_results.json`

The scout has three sections:

1. Runtime shell-cut process entropy:
   - 8-qubit finite density fixture;
   - current runtime rows for both engines;
   - graph-state carrier;
   - finite Kraus branch path entropy;
   - structured/product/order-scramble controls.
2. Runtime current-through-cut flux:
   - flux is read as a current-through-cut history, not a free scalar;
   - controls include product links, order scramble, commuting collapse, and
     label erasure.
3. Runtime two-agent QIT selector:
   - two local state/memory sides;
   - 16 runtime tokens;
   - selectors encoded as QIT payoff/damage selectors:
     minimax, maximax, maximin, minimin;
   - controls include commuting, scrambled, product-memory, and label-erased
     modes.

## Result

All three sections are structurally valid formal scouts, but none currently
survives.

| Section | Candidate Status | Survival | Key Metric |
| --- | --- | --- | --- |
| runtime shell/process | `open_or_nonrobust_runtime_shell_process` | `0.0` | mean path entropy `2.0546207699`, mean shell margin `0.0012494932` |
| runtime cut-current flux | `open_or_nonrobust_runtime_cut_current` | `0.0` | mean margin `-1.2916939225`, mean dependency spread `0.0059531908` |
| runtime two-agent selector | `open_or_nonrobust_runtime_two_agent_selector` | `0.125` | one of eight seeds survives; below threshold |
| source runtime receipts | `source_runtime_receipts_operational` | `true` | 16 tokens, 8 terrain realizations, mean T1/T2 final gap `0.2040662061` |
| source trajectory cut-current | `open_or_nonrobust_source_trajectory_cut_current` | `0.0` | mean margin `-0.0001506408` |
| source trajectory IGT selector | `open_or_nonrobust_source_trajectory_igt_selector` | `0.0` | label-erased controls do not change live selectors |

Interpretation:

- The shell/process section does produce substantial finite path entropy, but
  the runtime shell-cut margin is too small to count as robust.
- The current-through-cut flux formulation is a clean negative in this version:
  live runtime current loses hard to controls.
- The two-agent selector version is the first real move toward IGT game theory,
  but only `1/8` cases survive, so minimax/maximax/maximin/minimin are
  executable but not admitted as stable strategy classes.
- The source-aligned runtime trajectory receipts are operational: the tightened
  scout walks both runtime types, sees all 16 tokens and all 8 terrain
  realizations, validates density states, and confirms the A6 chart-role XOR.
- When the same cut-current and selector ideas are tied to actual source
  trajectories, they still do not survive controls. This is useful: the runtime
  works, but the current flux/IGT readouts are not yet load-bearing.

## Validation

Commands run:

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/sim_runtime_priority_work_suite_probe.py
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/lint_formal_scout_names.py system_v5/ops/formal_scouts/sim_runtime_priority_work_suite_probe.py
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun --fresh-rerun-timeout 180 system_v5/ops/formal_scouts/results/runtime_priority_work_suite_probe_results.json
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/sim_runtime_trajectory_receipt_coupling_probe.py
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/lint_formal_scout_names.py system_v5/ops/formal_scouts/sim_runtime_trajectory_receipt_coupling_probe.py
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun --fresh-rerun-timeout 180 system_v5/ops/formal_scouts/results/runtime_trajectory_receipt_coupling_probe_results.json
```

Validation result:

- filename lint: `all_pass=true`;
- fresh-rerun validation: `all_pass=true`;
- custom-unitary cache bug found and fixed before final validation;
- final fresh rerun reproduces:
  - shell process survival `0.0`;
  - cut-current survival `0.0`;
  - two-agent selector survival `0.125`.
- source-trajectory fresh rerun validates:
  - runtime receipt token count `16`;
  - runtime receipt terrain count `8`;
  - source cut-current survival `0.0`;
  - source IGT selector survival `0.0`.

## Claim Ceiling

Admitted:

- current runtime rows are being consumed by shell/process, cut-current, and
  two-agent selector probes;
- current source-aligned runtime trajectories are executable and receipt-rich;
- finite path entropy and current-through-cut readouts are now wired to runtime
  histories;
- QIT selector translation is executable against two-agent controls.

Not admitted:

- final engines;
- final Axis0 or Xi;
- final flux;
- final IGT game theory;
- final Holodeck/world engine;
- physics, gravity, Standard Model, Yang-Mills, cosmology, or unification.

## Next Engine-Primary Gates

1. Port the source-trajectory receipt shape into the 8-qubit suite, so shell,
   cut-current, and selector readouts consume real runtime stage deltas instead
   of only token rows.
2. Add an `EngineCore` finite boundary/supportive receipt only for
   science-method fields; keep it out of torch-native nonclassical claims until
   the NumPy boundary is repaired.
3. Replace dense 8-qubit shell/flux sections with an MPS/process-tensor carrier
   before attempting 16 qubits.
4. Improve the two-agent selector fixture with real memory update between
   rounds before population dynamics.
5. Keep the shell-cut family as the most promising Axis0-adjacent candidate,
   but only after it survives engine-row coupling and path-history controls.
