# gcm_nesting_tower_le4q_v0 Build Card

Build the <=4Q carrier-and-pins-relative inverse-limit nesting tower over the committed 4Q cut states.

## Scope

- Exact all-cut compatibility and probe-relative compatibility are separate relations.
- Input authority is `gcm_4q_freeze_and_cuts_v0` with `cut_state_available=true` and `546 * 7 = 3822` stored reduced cut-matrix pairs.
- Claim ceiling is `scratch_diagnostic_le4q_tower_carrier_and_pins_relative`.
- No manifold, terrain, engine, Axis0, bridge, or formal admission claim is made.

## Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_nesting_tower_le4q_v0/gcm_nesting_tower_le4q_v0_common.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_nesting_tower_le4q_v0/validate_gcm_nesting_tower_le4q_v0.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_nesting_tower_le4q_v0/tests
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_substrate_check.py system_v6/sims/gcm_nesting_tower_le4q_v0/results/gcm_nesting_tower_le4q_v0_results.json --registry system_v6/sims/gcm_4q_freeze_and_cuts_v0/results/gcm_4q_freeze_and_cuts_v0_registry.json
```
