# Tier A — Tool Foundation (capability → integration → serializer → rename)

Historical April 2026 Hermes tier plan. Do not execute or treat
`classification = "canonical"` language below as current formal-scout readiness
or promotion without a fresh repo preflight, current user authorization, and the
current v5 readiness/sim-estate indexes.

> Historical worker preamble from the old Hermes plan, not current Codex
> instruction: spawned Claude workers received Block B from
> `~/wiki/harness/SALIENCE_PREAMBLE.md`.


Preconditions: read `system_v5/ops/HERMES_RULES.md` and `system_v5/ops/SIM_RUNNER.md`. Run preflight. Verify harness at `~/wiki/harness/00_READ_FIRST.md`. Verify runner is live: `pgrep -f system_v5/ops/sim_runner.sh` returns a PID.

## Role

Hermes spawns multiple Claude Code terminals across domains. Each Claude writes probes and appends them to `system_v5/ops/queue_tier_a.txt`. The runner executes. Hermes monitors `overnight_logs/sim_runner_current.log`.

Workers never run sims themselves.

## Child/subsubagent status ceiling

Claude, Gemini, Codex child, and autoresearch lanes may draft, falsify, audit,
or sharpen Tier A MICRO/BOUND packets. Their agreement is not queue readiness.
Only the controller can move a row to queue-visible status after reading the
strict packet fields, cited prior receipts, stage gate, queue row, and expected
result path.

Child/subsubagent receipts may support `salience_only`, `proposal`,
`bounded_work_candidate`, `queue_candidate`, `partial`, or `blocked`. They do
not write `admitted_by`, do not convert runner DONE into accepted evidence, and
do not promote tool-stage work into lego, coupling, bridge, axis, or engine
claims.

Tier A should be broad before it is admitted. Many tools, functions, fixtures,
coverage legos, negative cases, and model variants can be drafted in parallel.
Most are expected to fail the strict ratchet. That is useful when the failure
names the exact function surface, missing receipt, demotion condition, or claim
ceiling. Failed or rejected candidates inform the next packet; they do not make
the queue row ready.

## Reality (verified 2026-04-18)

- 1266 canonical result artifacts; 88 lack `tool_integration_depth`
- 4 shared result-writer helpers: `_doc_illum_common.py`, `_couple_common.py`, `_triple_common.py`, `_quad_common.py`
- All 4 define `TOOL_INTEGRATION_DEPTH` but `write_results()` does not inject it
- `axis0_full_constraint_manifold_{audit,guardrail_sim}.py` contain `Se/Ne/Si` leaks
- the repo now contains a broader tool-stage estate than the original Tier A surface reflected:
  - 34 capability-style probes
  - 47 integration-style probes
- use `system_v5/docs/plans/plans/2026-04-18-tool-stage-plan.md` as the dated tool-stage normalization and second-wave packet plan; current status must be checked against the live v5 readiness/sim-estate indexes
- fresh 2026-04-18 execution confirmed:
  - `sim_rustworkx_capability.py`
  - `sim_geomstats_capability.py`
  - `sim_xgi_capability.py`
  - `sim_e3nn_capability.py`
- fresh 2026-04-18 executed baseline/reference integrations:
  - `sim_integration_networkx_rustworkx_crosscheck.py`
  - `sim_integration_geomstats_constraint_manifold.py`
- `sim_integration_toponetx_gtower_chain_complex.py` also executed on 2026-04-18, but it is now treated as a stage-heavier reference packet rather than the clean default next Tier A move
- hdbscan/umap no longer count as missing capability probes:
  - `sim_capability_hdbscan_isolated.py`
  - `sim_capability_umap_isolated.py`
  - dedicated integration files also exist and need truth-label reconciliation, not new capability authoring

## Track 0 — Tool-capability sims (HARD GATE, per harness/05)

Seven Haiku Claudes, one tool each, parallel worktrees. Each writes ONE capability probe. `classification = "canonical"` applies only to the bounded capability claim: this tool can carry this check. It does not admit downstream lego, coupling, bridge, axis, or engine work.

### Micro packet rule

Tier A is micro-first. A capability packet should test one named tool function or API surface, not the whole library. The accepted packet shape is:

1. one tool;
2. one function/API surface;
3. one tiny claim;
4. one useful bounded lego target or minimal fixture;
5. positive, negative, and boundary tests;
6. one demotion condition;
7. one ledger loopback.

Each tool should find legos that expose its real value. A z3 packet should prefer fence/impossibility/synthesis legos; a sympy packet should prefer symbolic-identity/derivation legos; graph/topology tools should prefer graph, hypergraph, cell-complex, filtration, or graph-dynamics legos; geometry tools should prefer rotor, spinor, metric, geodesic, holonomy, or equivariance legos. These are still tool-stage packets. They receipt-validate the tool/function fit, not the lego.

Broad candidate generation is encouraged here: many candidate tools, fixtures,
and negative cases may be drafted before one packet is accepted. Each accepted
packet still keeps one uncertainty and one claim ceiling. Rejected candidates
are useful only when they name why they failed or how the next packet should be
smaller.

Do not debug multiple unknowns at once. If a worker cannot tell whether failure came from the tool call, the lego object, or another tool coupling, split the packet before queueing it.

Queue preface: Stage-3 and Stage-4 Tier A rows should carry the `MICRO` fields from `TOOL_STAGE_ROUTING_AND_SKIP_AHEAD.md`. Tool-pair rows additionally name prior receipts for both exact functions. Missing receipts mean the worker writes the missing micro proof first, not the pair packet.

| Worker | Tool | Probe path |
|---|---|---|
| A0.1 | z3 | `system_v4/probes/tool_capability_z3.py` |
| A0.2 | cvc5 | `system_v4/probes/tool_capability_cvc5.py` |
| A0.3 | sympy | `system_v4/probes/tool_capability_sympy.py` |
| A0.4 | PyG | `system_v4/probes/tool_capability_pyg.py` |
| A0.5 | TopoNetX | `system_v4/probes/tool_capability_toponetx.py` |
| A0.6 | Clifford (clifford/geometric_algebra) | `system_v4/probes/tool_capability_clifford.py` |
| A0.7 | torch (autograd) | `system_v4/probes/tool_capability_torch.py` |

Naming note: older `tool_capability_<tool>.py` rows and newer `sim_<tool>_capability.py` rows both exist in this repo. Do not infer coverage from filename style. Use the ledger row, exact function/API surface, and current receipt path.

## Track 0b — Extension capability normalization

These are still tool-stage packets, not lego work:

| Worker | Tool | Probe path |
|---|---|---|
| A0.8 | rustworkx | `system_v4/probes/sim_rustworkx_capability.py` |
| A0.9 | geomstats | `system_v4/probes/sim_geomstats_capability.py` |
| A0.10 | XGI | `system_v4/probes/sim_xgi_capability.py` |
| A0.11 | e3nn | `system_v4/probes/sim_e3nn_capability.py` |

Coverage note:
- isolated capability probes are not the whole tool-stage story
- prefer real bounded coverage legos when they exercise the tool more honestly than a sterile capability packet
- the current best coverage-lego families are Hopf / same-carrier geometry, Weyl local shells, G-tower local obstruction/filtration, constraint/distinguishability, and graph/cell-complex locals

### Worker template (A0.*)

Read: `~/wiki/harness/00_READ_FIRST.md`, `~/wiki/harness/05_four_sim_kinds.md`, `system_v4/probes/SIM_TEMPLATE.py`.

Task: write ONE canonical probe demonstrating your tool solves a non-trivial task in isolation. `classification = "canonical"`, `TOOL_MANIFEST` lists only your tool, `TOOL_INTEGRATION_DEPTH` = `{"<tool>": "load_bearing"}`. Positive + negative + boundary sections.

After saving the file: `git add` + commit `"tier-a/A0.<n>: tool-capability <tool>"`. Append basename to `system_v5/ops/queue_tier_a.txt`. Do NOT execute the sim.

## Track 1 — Serializer fix + backfill

### A1.serializer (Haiku)

Read: the 4 helpers in `system_v4/probes/_*.py`.

Task: modify `write_results()` in each helper to inject `TOOL_INTEGRATION_DEPTH` if absent (one-line change per helper). Commit: `"tier-a/A1: serializer injects TOOL_INTEGRATION_DEPTH"`.

No queue append — this change affects future runner output automatically.

### A1.backfill (Haiku)

Task: append the 88 probes missing depth to `system_v5/ops/queue_tier_a.txt`. Generator:

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

Commit: `"tier-a/A2: strip judging-function labels from axis0_*"`. Re-enqueue touched probes to `system_v5/ops/queue_tier_a.txt` so runner re-verifies.

## Track 3 — Conformance audit (Haiku, read-only)

Task: for each of the 88 missing-depth probes, classify:
- (a) probe sets depth, helper doesn't serialize → fixed by A1.serializer
- (b) probe doesn't set `TOOL_INTEGRATION_DEPTH` at all → needs source-level fix
- (c) probe sets empty dict → non-canonical, reclassify

Output: `system_v4/probes/a2_state/sim_results/tier_a_audit.json`. Commit: `"tier-a/A3: depth-missing audit"`. Probes classified (b) get appended to `system_v5/ops/queue_tier_a.txt` after source-level fix PRs.

## Track 4 — Tool-pair integration sims (Sonnet)

Six Sonnet Claudes, one pair each, parallel worktrees.

Do not start a tool-pair integration until the specific function/API surface for each tool has its own micro receipt. A valid pair packet names both prior receipts and demonstrates real interop: output of one feeds the other, or both independently cross-check the same tiny claim. Two tools imported into the same file is not integration.

| Worker | Pair | Probe path |
|---|---|---|
| A4.1 | z3 + sympy | `system_v4/probes/tool_integration_z3_sympy.py` |
| A4.2 | sympy + PyG | `system_v4/probes/tool_integration_sympy_pyg.py` |
| A4.3 | PyG + torch | `system_v4/probes/tool_integration_pyg_torch.py` |
| A4.4 | Clifford + Weyl (sympy) | `system_v4/probes/tool_integration_clifford_weyl.py` |
| A4.5 | TopoNetX + PyG | `system_v4/probes/tool_integration_toponetx_pyg.py` |
| A4.6 | cvc5 + sympy | `system_v4/probes/tool_integration_cvc5_sympy.py` |

## Track 4b — Second-wave bounded tool integrations

Only use packets that stay below lego coupling claims:

| Worker | Pair / surface | Probe path |
|---|---|---|
| A4.7 | networkx + rustworkx | `system_v4/probes/sim_integration_networkx_rustworkx_crosscheck.py` |
| A4.8 | geomstats + sympy + z3 | `system_v4/probes/sim_integration_geomstats_constraint_manifold.py` |
| A4.9 | TopoNetX + torch + z3 | `system_v4/probes/sim_integration_toponetx_gtower_chain_complex.py` |

Do not treat bridge-shaped or coexistence-shaped `sim_integration_*` files as Tier A defaults.
After the 2026-04-18 run, treat A4.9 as executed reference material only until it is thinned back below tower-order / shortcut-law semantics.

## Track 4c — Coverage-lego tool-stage runs

These are tool-stage coverage rows anchored to real bounded lego families. They answer one tool question and update the tool ledger; they do not count as lego-stage completion or successor permission.

| Worker | Coverage lego | Probe path |
|---|---|---|
| A4.10 | G-tower local obstruction | `system_v4/probes/sim_gtower_reduction_obstruction_z3.py` |
| A4.11 | Hopf TopoNetX crosscheck | `system_v4/probes/sim_toponetx_hopf_crosscheck.py` |
| A4.12 | Hopf persistent homology | `system_v4/probes/sim_gudhi_deep_s3_hopf_torus_persistent_homology.py` |
| A4.13 | Hopf manifold / Clifford geometry | `system_v4/probes/sim_foundation_hopf_torus_geomstats_clifford.py` |

Rule:
- these are still tool-stage / coverage-stage work
- they do not authorize broad higher-stage promotion
- if they expose a strong local parent, record that parent as a future candidate only; coupling selection still needs the active stage gate to permit it

### Worker template (A4.*)

Read: `~/wiki/harness/00_READ_FIRST.md`, `~/wiki/harness/05_four_sim_kinds.md`, `system_v4/probes/SIM_TEMPLATE.py`.

Requirements: `classification = "canonical"`, both tools in `TOOL_MANIFEST`, ≥1 `load_bearing`. Tests demonstrate actual interop — output of one feeds the other, not parallel use.

Commit: `"tier-a/A4.<n>: tool-integration <pair>"`. Append basename to `system_v5/ops/queue_tier_a.txt`.

## Auditor (Haiku, 30-min cron)

Tail `overnight_logs/sim_runner_current.log`. Verify each claimed commit against `git log`. Flag discrepancies at `~/wiki/projects/codex-ratchet/tier_a_audit_log.md`.

## Gate

Do not call Tier A green from the old 7-capability / 6-integration checklist alone. The later plan-era gate was broader, and current gate language must be refreshed from live repo/status preflight:

- 22 capability probes exist and their current status is reflected in `system_v5/docs/plans/plans/TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md`
- hdbscan and umap are not missing-capability tools; their remaining debt is integration/truth-label reconciliation
- second-wave capability reruns and bounded integration/reference packets are reconciled in the ledger and maintenance matrix
- `sim_integration_toponetx_gtower_chain_complex.py` remains reference material until thinned below tower-order / shortcut-law semantics
- serializer/backfill/rename work remains separately required when the corresponding source/result evidence is staged
- active queue rows must be runnable probe basenames; work-item labels stay commented until a matching probe exists
- auditor log is clean for the exact queue/probe batch being closed
- demotion, classical-only, and boundary-failure outcomes may support gate evidence, but only as exclusions or next-packet constraints, not promotions

## Save + Report

`~/wiki/projects/codex-ratchet/tier_a.md` with gate evidence. Telegram L3 once: gate pass OR blocker.
