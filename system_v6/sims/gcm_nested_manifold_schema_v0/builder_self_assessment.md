# Builder Self Assessment - gcm_nested_manifold_schema_v0

Status: built as `scratch_diagnostic` controller substrate.

What this packet does:

- Adds `scripts/gcm_nested_schema_check.py`, a shared JSON checker for the tribunal-adopted nested-result fields.
- Enforces missing-field failures with named error codes.
- Enforces the geometry-delta flip-control gate: stability class plus alternate registry/probe-family naming, or explicit `untested`.
- Provides fixtures for conformant, missing-field, and geometry-delta-without-stability cases.
- Writes `results/gcm_nested_schema_gap_report.json` over the current <=3Q tower, <=2Q tower, and geometry-attach packets.

Claim boundary:

- This checker does not validate a manifold, tower geometry, G2, Spin(7), F4, or embedding claim.
- Passing the checker means the controller substrate fields are present and the flip-control metadata shape is admissible.
- Failing current older packets is expected backfill evidence because those packets predate the tribunal schema.

Verification run:

- `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_nested_manifold_schema_v0/tests` -> 4 passed.
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_manifold_schema_v0/examples/conformant_nested_payload.json` -> pass.
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_manifold_schema_v0/examples/missing_field_payload.json` -> fail closed with `GCM_NESTED_MISSING_CROSS_PIN_STABILITY`.
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_manifold_schema_v0/examples/geometry_delta_without_stability_payload.json` -> fail closed with `GCM_NESTED_MISSING_GEOMETRY_DELTA_STABILITY_CLASS` and `GCM_NESTED_GEOMETRY_DELTA_WITHOUT_STABILITY`.
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_nested_manifold_schema_v0/run_schema_gap_report.py` -> exits 1 by design because all 10 audited current packets fail the new schema; wrote `results/gcm_nested_schema_gap_report.json`.

Gap-map result:

- pass: 0
- fail: 10
- reason: the audited <=3Q tower, <=2Q tower, and geometry-attach result/envelope packets carry `claim_ceiling` but predate the tribunal fields and are missing the other required schema fields.
