# Independent Audit Verdict - gcm_nested_manifold_schema_v0 + scripts/gcm_nested_schema_check.py

audit_mode: independent fresh audit; repo read-only except this file
freshness_tier: TIER-2 live-source audit with scratch adversarial controls
auditor: Codex controller/local-tools audit
audit_date: 2026-06-13
route_truth: partial Wizard v4.2 only; controller/local-tools audit, no full parent/child subagent topology claimed
standards_codex: system_v6/receipts/audit_standards_codex_v1.md
binding_references: system_v6/receipts/nesting_plan_tribunal_adopted_20260612.md; commit f65a81010; system_v6/sims/gcm_object_id_freeze_v0/audit_verdict.md

Bottom line: VERDICT = PASS AS A SCRATCH-DIAGNOSTIC PRESENCE/SHAPE SCHEMA CHECKER, NOT PASS AS A TRUTH CHECKER OR FULL FLIP-CONTROL ENFORCEMENT CORE.

The gate bites on the advertised field contract: all 12 tribunal fields are required, missing fields get distinct named codes, invalid `geometry_delta_stability_class` enum values fail, and a non-empty `what_would_flip` string that does not name `alternate_registry` and `alternate_probe_family` fails. The self-tests are genuine.

But the checker still has two important ceilings:

1. `what_would_flip` can pass as the bare string `alternate_registry and alternate_probe_family`, with no actual alternate registry value and no actual alternate probe-family value.
2. `cross_stable` can pass as a label with no evidence fields showing that alternate-pin / alternate-probe reruns actually happened.

Accepted claim ceiling: `scratch_diagnostic_controller_schema_presence_and_metadata_shape_check`. Passing this checker means field carriage plus minimal flip-control metadata shape, not that a geometry delta is true, stable, cross-stable, or recomputed. Geometry-delta truth remains the job of the geometry-delta packet and its independent audit.

## Binding Standard

The tribunal adoption says the deepest gate is geometry-delta falsification: every geometry-delta / nested-geometry packet must carry a flip control rerun with an alternate registry pin and alternate probe family; if the delta moves it is pin-relative, and if stable across pins/probes it earns more weight. It also says no geometry-delta may be cited without its stability class (`system_v6/receipts/nesting_plan_tribunal_adopted_20260612.md:16-24`).

The adopted schema fields are the 12-field controller substrate for `gcm_nested_manifold_schema_v0` (`system_v6/receipts/nesting_plan_tribunal_adopted_20260612.md:26-31`). The build card repeats the same 12 fields and the flip-control acceptance rule (`system_v6/sims/gcm_nested_manifold_schema_v0/build_card.md:17-23`).

G.2a requires builder/audit file separation and idempotency from birth: new packet validators/tests must not hard-code permanent absence of `audit_verdict.md`; they must delegate audit-verdict handling to the shared builder/audit boundary helper when they have such a check (`system_v6/receipts/audit_standards_codex_v1.md:158-177`).

## Gate Bite Results

Fresh adversarial controls were run from scratch with `PYTHONDONTWRITEBYTECODE=1` and results saved only under `/tmp`.

| Control | Expected | Actual |
| --- | --- | --- |
| All 12 fields present, `geometry_delta_stability_class = garbage_cross_magic` | fail | fail with `GCM_NESTED_GEOMETRY_DELTA_STABILITY_CLASS_INVALID` |
| Geometry-delta claim with `what_would_flip = rerun on another pin and another probe family` | fail | fail with `GCM_NESTED_GEOMETRY_DELTA_FLIP_CONTROL_MISSING` |
| Geometry-delta claim with `what_would_flip = alternate_registry and alternate_probe_family` | should fail if structured values are required | passes |
| `geometry_delta_stability_class = cross_stable`, `cross_pin_stability = cross_stable`, no backing evidence fields | should not prove truth | passes |

Implementation reason:

- The enum check is real: `GEOMETRY_DELTA_STABILITY_CLASSES` contains exactly `pin_relative`, `probe_relative`, `cross_stable`, and `untested`, and invalid values add `GCM_NESTED_GEOMETRY_DELTA_STABILITY_CLASS_INVALID` (`scripts/gcm_nested_schema_check.py:28-33`, `:149-155`).
- The missing-field codes are generated per field by `_missing_code(field)` and are emitted for every missing required field (`scripts/gcm_nested_schema_check.py:13-26`, `:70-71`, `:145-147`).
- The flip-control string path only checks that the lowercase string contains the literal substrings `alternate_registry` and `alternate_probe_family` (`scripts/gcm_nested_schema_check.py:110-115`).
- The dict path only checks that one alternate-registry key and one alternate-probe key are present and non-empty; it does not require a status, receipt path, result hash, command, or alternate run result (`scripts/gcm_nested_schema_check.py:118-127`).
- The checker docstring is honest that it does not validate or promote any manifold, tower, or geometry claim (`scripts/gcm_nested_schema_check.py:130-136`).

## Named-Code Coverage

Fresh scratch deletion of each required field confirmed every one of the 12 missing-field cases yields its own named code, not a generic failure:

- `exact_relation_status` -> `GCM_NESTED_MISSING_EXACT_RELATION_STATUS`
- `probe_relation_status` -> `GCM_NESTED_MISSING_PROBE_RELATION_STATUS`
- `extension_fiber_size` -> `GCM_NESTED_MISSING_EXTENSION_FIBER_SIZE`
- `cut_state_available` -> `GCM_NESTED_MISSING_CUT_STATE_AVAILABLE`
- `blocked_consumer_enforced` -> `GCM_NESTED_MISSING_BLOCKED_CONSUMER_ENFORCED`
- `what_would_flip` -> `GCM_NESTED_MISSING_WHAT_WOULD_FLIP` plus the geometry-delta flip-control error when a geometry-delta claim is present
- `negative_control_status` -> `GCM_NESTED_MISSING_NEGATIVE_CONTROL_STATUS`
- `cross_pin_stability` -> `GCM_NESTED_MISSING_CROSS_PIN_STABILITY`
- `geometry_delta_stability_class` -> `GCM_NESTED_MISSING_GEOMETRY_DELTA_STABILITY_CLASS` plus `GCM_NESTED_GEOMETRY_DELTA_WITHOUT_STABILITY` when a geometry-delta claim is present
- `forward_transport_status` -> `GCM_NESTED_MISSING_FORWARD_TRANSPORT_STATUS`
- `backward_admissibility_status` -> `GCM_NESTED_MISSING_BACKWARD_ADMISSIBILITY_STATUS`
- `claim_ceiling` -> `GCM_NESTED_MISSING_CLAIM_CEILING`

## Gap-Map Honesty

The checked-in gap report is honest. I recomputed the target packet checks in memory without rewriting the report. Fresh recomputation matched the stored report exactly: `pass_count = 0`, `fail_count = 10`, `report_matches_fresh = true`.

The report says the failures are expected backfill, not contradiction: `Existing tower/geometry packets predate the tribunal schema; failures are backfill targets, not mathematical refutations` (`system_v6/sims/gcm_nested_manifold_schema_v0/results/gcm_nested_schema_gap_report.json:359-363`). It lists the missing fields and named codes for every packet (`system_v6/sims/gcm_nested_manifold_schema_v0/results/gcm_nested_schema_gap_report.json:10-340`).

This matches the builder self-assessment: the older tower/geometry packets carry `claim_ceiling` but predate the tribunal fields and are missing the other required schema fields (`system_v6/sims/gcm_nested_manifold_schema_v0/builder_self_assessment.md:27-31`).

## G.2a

G.2a is not violated by this schema packet as audited:

- The build card declares the builder write boundary as `scripts/gcm_nested_schema_check.py` and `system_v6/sims/gcm_nested_manifold_schema_v0/` (`system_v6/sims/gcm_nested_manifold_schema_v0/build_card.md:5-8`).
- Before this audit, no `audit_verdict.md` existed in the packet directory.
- I found no hard audit-absence gate in `scripts/gcm_nested_schema_check.py` or the packet-local schema files.

Caveat: this packet does not appear to have a packet-local validator that delegates audit-verdict handling to `scripts/builder_audit_boundary.py`; it has pytest tests and a gap-report runner. That is acceptable for this narrow schema-helper packet only because there is no hard absence check to repair, but any future packet-local validator for this directory should use the shared boundary helper from birth.

## Self-Tests

The builder self-tests are genuine:

```text
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/gcm_nested_manifold_schema_v0/tests
```

returned:

```text
4 passed in 0.03s
```

The advertised CLI checks also behaved as claimed:

- conformant fixture: `ok = true`
- missing-field fixture: `ok = false`, `GCM_NESTED_MISSING_CROSS_PIN_STABILITY`
- geometry-delta-without-stability fixture: `ok = false`, `GCM_NESTED_MISSING_GEOMETRY_DELTA_STABILITY_CLASS` and `GCM_NESTED_GEOMETRY_DELTA_WITHOUT_STABILITY`

The tests exercise the advertised fixtures, including the flip-control-missing case (`system_v6/sims/gcm_nested_manifold_schema_v0/tests/test_gcm_nested_schema_check.py:22-53`).

## Limitation

This checker enforces presence and coarse structure. It does not verify claim truth.

Specifically, it does not recompute that:

- a `cross_stable` geometry delta actually survived alternate pins;
- a `cross_stable` geometry delta actually survived an alternate probe family;
- `negative_control_status` names a real negative-control result;
- `cross_pin_stability` is backed by a receipt path, command, payload hash, result hash, or pass/fail matrix;
- `what_would_flip` points to actual alternate-registry and alternate-probe-family artifacts.

This is useful as a controller substrate, but it is not the deepest gate by itself. The deepest gate becomes load-bearing only when geometry-delta packets must show the alternate-registry and alternate-probe-family runs, with receipts, and independent audit verifies the claimed stability class against those receipts.

## Repo-State Caveat

At audit time, the schema helper and packet directory were untracked in this checkout:

```text
?? scripts/gcm_nested_schema_check.py
?? system_v6/sims/gcm_nested_manifold_schema_v0/
```

This audit verifies the live files present in the working tree. It does not assert that the schema helper is already committed/canonical in Git.

## Commands Run

```text
sed -n '1,260p' /Users/joshuaeisenhart/.codex/skills/three-council-wizard-v4-2/SKILL.md
rg -n "gcm_nested|nested_manifold|tribunal|f65a81010|G\\.2a|gcm_substrate_check|substrate-helper|substrate" /Users/joshuaeisenhart/.codex/memories/MEMORY.md
sed -n '1,260p' AGENTS.md
sed -n '1,240p' CODEX.md
sed -n '1,260p' scripts/gcm_nested_schema_check.py
sed -n '1,220p' system_v6/sims/gcm_object_id_freeze_v0/audit_verdict.md
sed -n '1,220p' system_v6/sims/gcm_nested_manifold_schema_v0/build_card.md
sed -n '1,220p' system_v6/sims/gcm_nested_manifold_schema_v0/builder_self_assessment.md
sed -n '1,220p' system_v6/sims/gcm_nested_manifold_schema_v0/tests/test_gcm_nested_schema_check.py
sed -n '1,180p' system_v6/sims/gcm_nested_manifold_schema_v0/run_schema_gap_report.py
sed -n '1,430p' system_v6/sims/gcm_nested_manifold_schema_v0/results/gcm_nested_schema_gap_report.json
sed -n '150,185p' system_v6/receipts/audit_standards_codex_v1.md
sed -n '1,90p' system_v6/receipts/nesting_plan_tribunal_adopted_20260612.md
git show --stat --oneline --decorate --no-renames f65a81010 -- system_v6/receipts/nesting_plan_tribunal_adopted_20260612.md system_v6/sims/gcm_nested_manifold_schema_v0 scripts/gcm_nested_schema_check.py
git status --short -- scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_manifold_schema_v0
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/gcm_nested_manifold_schema_v0/tests
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_manifold_schema_v0/examples/conformant_nested_payload.json
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_manifold_schema_v0/examples/missing_field_payload.json
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_manifold_schema_v0/examples/geometry_delta_without_stability_payload.json
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# scratch adversarial controls; wrote /tmp/gcm_nested_schema_audit_controls.json
PY
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# in-memory gap-report recomputation; wrote /tmp/gcm_nested_gap_report_fresh_check.json
PY
```

No `git add` or commit was run.
