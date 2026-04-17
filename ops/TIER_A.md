# Tier A — Tools + Serializer + Rename

Preconditions: read `ops/HERMES_RULES.md`. Run preflight. Verify harness at `~/wiki/harness/00_READ_FIRST.md`.

## Objective

Unblock "canonical by process" verification and complete tool foundation.

Three tracks, parallel workers, disjoint scopes.

## Reality (verified 2026-04-16)

- 1266 canonical result artifacts under `system_v4/probes/a2_state/sim_results/`
- 88 lack `tool_integration_depth` (not 28 — earlier number was wrong)
- 4 shared result-writer helpers: `_doc_illum_common.py`, `_couple_common.py`, `_triple_common.py`, `_quad_common.py` — all define `TOOL_INTEGRATION_DEPTH` but `write_results()` does not inject it
- `axis0_full_constraint_manifold_{audit,guardrail_sim}.py` contain `Se/Ne/Si` label leaks

## Workers

### T1 (Haiku) — serializer fix + backfill

Scope: the 4 helpers + re-run of 88 probes.

Read: `~/wiki/harness/00_READ_FIRST.md`, the 4 helpers.

Task:
1. Modify `write_results()` in each helper to inject `TOOL_INTEGRATION_DEPTH` if absent. One-line change.
2. Re-run the 88 probes missing depth. List them with:

```python
import json, glob
for p in glob.glob('system_v4/probes/a2_state/sim_results/*.json'):
    try: d=json.load(open(p))
    except: continue
    if d.get('classification')=='canonical' and 'tool_integration_depth' not in d:
        print(p.replace('a2_state/sim_results/','').replace('_results.json','.py'))
```

Use `Makefile` target for single-probe re-run. If absent, document and escalate.

Gate: every canonical result JSON has `tool_integration_depth` key.
Commit: `"tier-a/T1: backfill TOOL_INTEGRATION_DEPTH in result JSON"`.

### T2 (Haiku) — rename pass on axis0

Scope: `system_v4/probes/axis0_*.py` only.

Read: `~/wiki/harness/00_READ_FIRST.md`, `~/wiki/harness/03_language_discipline.md`.

Renames:
- `Fe` → `bridge_12` (when on q1,q2)
- `XX_23` → `relay_23`
- `Fi, Ti, Te, Ne, Ni, Se, Si` → delete (these labels belong to Axis 4+)

If deletion breaks a sim → flag and STOP that file; do not fake a pass.

Audit: `grep -E "\b(Fe|Fi|Te|Ti|Ne|Ni|Se|Si)\b" system_v4/probes/axis0_*.py` must return zero hits.
Commit: `"tier-a/T2: strip judging-function labels from axis0_*"`.

### T3 (Haiku) — SIM_TEMPLATE conformance audit

Read: `~/wiki/harness/00_READ_FIRST.md`, `system_v4/probes/SIM_TEMPLATE.py`.

Audit the 88 probes missing depth. Classify each:
- (a) probe sets depth, helper doesn't serialize → T1 fixes
- (b) probe doesn't set `TOOL_INTEGRATION_DEPTH` at all → needs source-level fix
- (c) probe sets empty dict → non-canonical, reclassify

Output: `system_v4/probes/a2_state/sim_results/tier_a_t3_audit.json` with per-probe classification.
Commit: `"tier-a/T3: depth-missing audit report"`.

### T4–T9 (Sonnet) — tool-pair integration sims

One worker per pair: `z3_sympy`, `sympy_pyg`, `pyg_torch`, `clifford_weyl`, `toponetx_pyg`, `cvc5_sympy`.

Read: `~/wiki/harness/00_READ_FIRST.md`, `~/wiki/harness/05_four_sim_kinds.md`, `system_v4/probes/SIM_TEMPLATE.py`.

Task: write ONE canonical sim at `system_v4/probes/tool_integration_<pair>.py`.

Requirements per `SIM_TEMPLATE.py`:
- `classification = "canonical"`
- `TOOL_MANIFEST`: both tools present with non-empty reasons
- `TOOL_INTEGRATION_DEPTH`: at least one tool `load_bearing`
- Positive + negative + boundary test sections
- Tests demonstrate actual interop — output of one tool feeds the other, not parallel

Run the sim; confirm result JSON written. Commit: `"tier-a/T<n>: tool-integration <pair>"`.

### Auditor (Haiku, 30-min cron)

Verify each in-flight worker's claimed commits against `git log`. Flag discrepancies in `~/wiki/projects/codex-ratchet/tier_a_audit_log.md`.

## Gate

- ✓ All 88 canonical results now have `tool_integration_depth`
- ✓ `axis0_*.py` grep for judging-function labels: 0 hits
- ✓ 6 new `tool_integration_<pair>.py` files exist, canonical, pass local rerun
- ✓ Auditor log has no unresolved discrepancies

## Save

`~/wiki/projects/codex-ratchet/tier_a.md` with gate evidence.

## Report

Telegram L3 once: gate pass OR specific blocker.
