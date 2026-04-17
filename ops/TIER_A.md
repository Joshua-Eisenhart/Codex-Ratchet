# Tier A — Tool Foundation (capability → integration → serializer → rename)

> **Worker spawn preamble (mandatory):** every spawned Claude worker receives Block B (140-word) from `~/wiki/harness/SALIENCE_PREAMBLE.md` prepended to its system prompt before any task description. See `ops/HERMES_RULES.md` §0. Probe-tested 2026-04-17 on fresh Haiku.


Preconditions: read `ops/HERMES_RULES.md` and `ops/SIM_RUNNER.md`. Run preflight. Verify harness at `~/wiki/harness/00_READ_FIRST.md`. Verify runner is live: `pgrep -f ops/sim_runner.sh` returns a PID.

## Role

Hermes spawns multiple Claude Code terminals across domains. Each Claude writes probes and appends them to `ops/queue_tier_a.txt`. The runner executes. Hermes monitors `overnight_logs/sim_runner_current.log`.

Workers never run sims themselves.

## Reality (verified 2026-04-16)

- 1266 canonical result artifacts; 88 lack `tool_integration_depth`
- 4 shared result-writer helpers: `_doc_illum_common.py`, `_couple_common.py`, `_triple_common.py`, `_quad_common.py`
- All 4 define `TOOL_INTEGRATION_DEPTH` but `write_results()` does not inject it
- `axis0_full_constraint_manifold_{audit,guardrail_sim}.py` contain `Se/Ne/Si` leaks

## Track 0 — Tool-capability sims (HARD GATE, per harness/05)

Seven Haiku Claudes, one tool each, parallel worktrees. Each writes ONE canonical probe proving the tool works in isolation.

| Worker | Tool | Probe path |
|---|---|---|
| A0.1 | z3 | `system_v4/probes/tool_capability_z3.py` |
| A0.2 | cvc5 | `system_v4/probes/tool_capability_cvc5.py` |
| A0.3 | sympy | `system_v4/probes/tool_capability_sympy.py` |
| A0.4 | PyG | `system_v4/probes/tool_capability_pyg.py` |
| A0.5 | TopoNetX | `system_v4/probes/tool_capability_toponetx.py` |
| A0.6 | Clifford (clifford/geometric_algebra) | `system_v4/probes/tool_capability_clifford.py` |
| A0.7 | torch (autograd) | `system_v4/probes/tool_capability_torch.py` |

### Worker template (A0.*)

Read: `~/wiki/harness/00_READ_FIRST.md`, `~/wiki/harness/05_four_sim_kinds.md`, `system_v4/probes/SIM_TEMPLATE.py`.

Task: write ONE canonical probe demonstrating your tool solves a non-trivial task in isolation. `classification = "canonical"`, `TOOL_MANIFEST` lists only your tool, `TOOL_INTEGRATION_DEPTH` = `{"<tool>": "load_bearing"}`. Positive + negative + boundary sections.

After saving the file: `git add` + commit `"tier-a/A0.<n>: tool-capability <tool>"`. Append basename to `ops/queue_tier_a.txt`. Do NOT execute the sim.

## Track 1 — Serializer fix + backfill

### A1.serializer (Haiku)

Read: the 4 helpers in `system_v4/probes/_*.py`.

Task: modify `write_results()` in each helper to inject `TOOL_INTEGRATION_DEPTH` if absent (one-line change per helper). Commit: `"tier-a/A1: serializer injects TOOL_INTEGRATION_DEPTH"`.

No queue append — this change affects future runner output automatically.

### A1.backfill (Haiku)

Task: append the 88 probes missing depth to `ops/queue_tier_a.txt`. Generator:

```python
import json, glob, os
for p in sorted(glob.glob('system_v4/probes/a2_state/sim_results/*.json')):
    try: d = json.load(open(p))
    except: continue
    if d.get('classification') == 'canonical' and 'tool_integration_depth' not in d:
        base = os.path.basename(p).replace('_results.json', '')
        if os.path.exists(f'system_v4/probes/{base}.py'):
            print(base)
```

Pipe output appending to queue. Do NOT execute. Runner will process.

## Track 2 — Rename pass (Haiku)

Scope: `system_v4/probes/axis0_*.py` only.

Read: `~/wiki/harness/00_READ_FIRST.md`, `~/wiki/harness/03_language_discipline.md`.

Renames:
- `Fe` → `bridge_12` (when on q1,q2)
- `XX_23` → `relay_23`
- `Fi, Ti, Te, Ne, Ni, Se, Si` → delete (labels belong to Axis 4+)

If deletion breaks a sim → flag and STOP that file; do not fake a pass.

Audit: `grep -E "\b(Fe|Fi|Te|Ti|Ne|Ni|Se|Si)\b" system_v4/probes/axis0_*.py` returns zero.

Commit: `"tier-a/A2: strip judging-function labels from axis0_*"`. Re-enqueue touched probes to `ops/queue_tier_a.txt` so runner re-verifies.

## Track 3 — Conformance audit (Haiku, read-only)

Task: for each of the 88 missing-depth probes, classify:
- (a) probe sets depth, helper doesn't serialize → fixed by A1.serializer
- (b) probe doesn't set `TOOL_INTEGRATION_DEPTH` at all → needs source-level fix
- (c) probe sets empty dict → non-canonical, reclassify

Output: `system_v4/probes/a2_state/sim_results/tier_a_audit.json`. Commit: `"tier-a/A3: depth-missing audit"`. Probes classified (b) get appended to `ops/queue_tier_a.txt` after source-level fix PRs.

## Track 4 — Tool-pair integration sims (Sonnet)

Six Sonnet Claudes, one pair each, parallel worktrees.

| Worker | Pair | Probe path |
|---|---|---|
| A4.1 | z3 + sympy | `system_v4/probes/tool_integration_z3_sympy.py` |
| A4.2 | sympy + PyG | `system_v4/probes/tool_integration_sympy_pyg.py` |
| A4.3 | PyG + torch | `system_v4/probes/tool_integration_pyg_torch.py` |
| A4.4 | Clifford + Weyl (sympy) | `system_v4/probes/tool_integration_clifford_weyl.py` |
| A4.5 | TopoNetX + PyG | `system_v4/probes/tool_integration_toponetx_pyg.py` |
| A4.6 | cvc5 + sympy | `system_v4/probes/tool_integration_cvc5_sympy.py` |

### Worker template (A4.*)

Read: `~/wiki/harness/00_READ_FIRST.md`, `~/wiki/harness/05_four_sim_kinds.md`, `system_v4/probes/SIM_TEMPLATE.py`.

Requirements: `classification = "canonical"`, both tools in `TOOL_MANIFEST`, ≥1 `load_bearing`. Tests demonstrate actual interop — output of one feeds the other, not parallel use.

Commit: `"tier-a/A4.<n>: tool-integration <pair>"`. Append basename to `ops/queue_tier_a.txt`.

## Auditor (Haiku, 30-min cron)

Tail `overnight_logs/sim_runner_current.log`. Verify each claimed commit against `git log`. Flag discrepancies at `~/wiki/projects/codex-ratchet/tier_a_audit_log.md`.

## Gate

- ✓ 7 tool-capability probes exist, runner reports DONE for all
- ✓ Serializer change committed
- ✓ All 88 backfill probes re-run (runner DONE lines in queue)
- ✓ `axis0_*.py` rename audit: 0 leaks
- ✓ 6 tool-integration probes exist, runner reports DONE for all
- ✓ Auditor log clean

## Save + Report

`~/wiki/projects/codex-ratchet/tier_a.md` with gate evidence. Telegram L3 once: gate pass OR blocker.
