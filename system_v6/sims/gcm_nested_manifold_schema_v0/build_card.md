# gcm_nested_manifold_schema_v0 Build Card

Scope: controller-substrate schema enforcement for nested result payloads.

Write boundary:

- `scripts/gcm_nested_schema_check.py`
- `system_v6/sims/gcm_nested_manifold_schema_v0/`

Authority:

- tribunal adoption `f65a81010`
- `system_v6/receipts/nesting_plan_tribunal_adopted_20260612.md`
- nesting law `afe7aa57b`
- `system_v6/receipts/nesting_law_final_object_spec_20260612.md`

Acceptance:

- Require all adopted nested schema fields: `exact_relation_status`, `probe_relation_status`, `extension_fiber_size`, `cut_state_available`, `blocked_consumer_enforced`, `what_would_flip`, `negative_control_status`, `cross_pin_stability`, `geometry_delta_stability_class`, `forward_transport_status`, `backward_admissibility_status`, `claim_ceiling`.
- Emit named error codes for missing fields.
- Enforce the geometry-delta flip-control gate: a geometry-delta payload must carry `geometry_delta_stability_class` in `pin_relative`, `probe_relative`, `cross_stable`, or `untested`, and `what_would_flip` must name the alternate registry and alternate probe family, or be exactly `untested`.
- Run the checker against the committed `gcm_nesting_tower_le3q_v0`, `gcm_nesting_tower_le2q_v0`, and `gcm_geometry_attach*` packets and write the honest gap map.
- Keep the ceiling `scratch_diagnostic`: this schema enforces controller substrate fields and does not make manifold claims.

Verification commands:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_nested_manifold_schema_v0/tests
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_manifold_schema_v0/examples/conformant_nested_payload.json
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_manifold_schema_v0/examples/missing_field_payload.json
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_manifold_schema_v0/examples/geometry_delta_without_stability_payload.json
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_nested_manifold_schema_v0/run_schema_gap_report.py
```
