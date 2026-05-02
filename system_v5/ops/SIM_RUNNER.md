# 24/7 Sim Runner — thermal-safe, zero token cost

Pure Python + shell. No LLM in the loop. Drains tier queues in priority order, pauses when the machine gets hot.

Status: this document describes the live v1 runner. The v2 admission-gate contract is not live yet; its routing law lives in `system_v5/ops/TOOL_STAGE_ROUTING_AND_SKIP_AHEAD.md`, and the draft implementation sketch lives in `system_v5/ops/drafts/sim_runner_v2_stub.sh`.

## Runner taxonomy

Agents and LLM workers may write, repair, audit, or enqueue probes. They do not execute sims. Executable evidence comes from Python runner classes.

The runner layer must distinguish three execution kinds:

1. `classical` — classical baselines, controls, and negative/reference comparisons. These preserve the before-picture and must not be promoted into nonclassical evidence.
2. `nonclassical` — canonical nonclassical-target sims. These use the nonclassical stack where claim-relevant: PyTorch/PyG for tensor and graph dynamics, Clifford for geometric product/spinor/rotor claims, and z3/cvc5 for structural proof or UNSAT claims.
3. `bridge` — sims that connect classical baselines to nonclassical structure, including `bridge`, `Xi`, `rho_AB`, `Phi0`, cut/kernel, pairwise/coupling, and coexistence work. Bridge sims need both sides named: the classical baseline being bridged from and the nonclassical tool plan being bridged to.

Graph and proof tools are not universally valid across all three kinds. A graph/proof surface can be `classical-only`, `bridge-useful`, `nonclassical-support`, or `nonclassical-core`; the runner should admit it only in the matching execution kind.

## Role separation

- **Hermes terminals** (Tier A / B / D) — write probes, enqueue them, monitor the runner's log. They do NOT execute sims.
- **Runner** (this file) — picks next queued probe, runs it at low priority, writes result JSON, logs, repeats.

## What it does per tick

1. Reads queues in priority order: `queue_tier_a.txt` -> `queue_tier_b.txt` -> `queue_tier_d.txt` only when `stage_gate.json` permits Tier D -> `queue_default.txt`.
2. Picks the first un-done probe from the highest-priority non-empty queue.
3. Runs it with `nice -n 19`, captures result.
4. Validates the canonical result JSON with strict executable run-boundary admission.
5. Marks the queue line as `# DONE <timestamp>` only after the Python process exits cleanly and the receipt is admitted; otherwise marks `# FAIL <timestamp>`.
6. Sleeps between sims; cooldown sleep if hot.
7. Repeats forever.

`DONE` is runner execution plus strict receipt-admission evidence. It still does not update the ledger by itself or make coupling rows ready; controller reconciliation must connect the queue row, canonical result JSON, packet scope, and ledger loopback before any downstream claim moves.

## Priority rules

- Tier A queue drains before B. Tier D drains only when `system_v5/ops/stage_gate.json` has `allow_tier_d_launch: true`. Foundation first.
- Within a queue, top-to-bottom order (Hermes terminals append).
- `queue_default.txt` = fail-closed fallback only. It should contain only controller-approved tool/local-lego entries; stage-heavier tool-integration rows belong in Tier A or explicit review. It is allowed to stay empty.
- `queue_default.txt` must not auto-queue pairwise/coexistence/bridge/axis/engine-style probes unless `stage_gate.json` explicitly allows default-queue late-stage work.
- `queue_lego_backlog.txt` and `queue_offlane.txt` are v2 partition surfaces. The live v1 runner does not auto-drain them; `queue_offlane.txt` is never auto-drained.

## Thermal safety

Pause when ANY of:
- `sysctl -n machdep.xcpm.cpu_thermal_level` ≥ 60
- 1-min load avg > `ncpus * 0.75`
- (optional) `osx-cpu-temp` > 85°C

Resume when ALL below their thresholds:
- thermal_level < 40
- load normal
- (optional) temp < 75°C

Cooldown sleep: 120s per cycle while hot.

## Queue file format

One probe basename per line (relative to `system_v4/probes/`, no `.py` suffix). Lines starting with `#` are ignored by the runner. Runner rewrites completed lines to `# DONE <timestamp> <basename> (<dur>s)` only after strict executable receipt admission; process failures, missing receipts, and admission failures become `# FAIL <timestamp> <basename> (<dur>s)`.

Controller reconciliation must happen after this rewrite: match the queue row to the result JSON, result `classification`, `TOOL_INTEGRATION_DEPTH`, and ledger loopback before counting the receipt toward an admission gate.

Before a non-browser sim/controller run, run the fail-closed preflight:

```bash
make runner-preflight
```

If it reports stale `playwright-mcp`, `@playwright/mcp`, or `SkyComputerUseClient` helpers, stop those helpers before launching the runner unless an active browser/computer-use task intentionally owns them.

The live runner also runs `scripts/helper_process_audit.py --strict` at startup and refuses to launch when stale browser/computer-use helpers are present. `ALLOW_HELPER_PROCESSES=1` exists only for an explicitly owned browser/computer-use task; do not use it for ordinary sim runs. The runner also creates `system_v5/ops/.sim_runner.lock`, repairs a stale lock whose recorded PID is not live, and exits if another live runner owns that lock.

Example `queue_tier_a.txt`:
```
# Tier A tool-capability + integration queue
tool_capability_z3
tool_capability_cvc5
tool_capability_sympy
tool_capability_pyg
tool_integration_z3_sympy
tool_integration_sympy_pyg
```

## Hermes enqueue convention

When a Hermes worker writes a new probe:
1. Save `.py` file.
2. `git add` + commit per its tier convention.
3. Append probe basename to its tier queue (e.g. `echo "tool_capability_z3" >> system_v5/ops/queue_tier_a.txt`).

## Monitoring

Hermes terminals tail `overnight_logs/sim_runner_current.log` (symlink to latest) to see progress. Wiki steward cron digests new result JSONs into `~/wiki/concepts/<family>.md` automatically.

## Launch / stop

Launch:
```bash
cd "/Users/joshuaeisenhart/Desktop/Codex Ratchet" && nohup bash system_v5/ops/sim_runner.sh > overnight_logs/sim_runner_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

Stop gracefully:
```bash
touch system_v5/ops/.stop_sim_runner
```

## Rules

1. One sim at a time. No parallelization (keeps laptop cool, keeps logs simple); the live runner enforces this with `system_v5/ops/.sim_runner.lock`.
2. `nice -n 19` always; never `sudo`.
3. Runner only reads queues and executes; never writes probe source.
4. Unhandled probe exception → log, move on, don't retry.
5. 5 consecutive failures → pause 30 min, telegram L3 once.
6. Runner obeys `system_v5/ops/.stop_sim_runner` sentinel file between sims.
7. The hard stage gate wins over stale queue contents: no pairwise/coexistence/bridge/axis/engine probe may run from `queue_default.txt` unless `allow_default_queue_late_stage` is explicitly true.
8. If all tier queues are empty and no safe default queue exists, the runner stays idle rather than generating a generic never-run pile.
9. Runner admission must not treat all sims as one bucket. Before v2 enforcement, use `make runner-taxonomy-audit` to map current probes to `classical`, `nonclassical`, and `bridge` execution kinds and surface routing gaps.
10. Tier D is gated by `stage_gate.json`. If `allow_tier_d_launch` is false, the live runner skips `queue_tier_d.txt` even when rows are present.
11. Coupling readiness must come from reconciled parent receipts, not from aggregate DONE counts.
12. `stage_gate.json` booleans are fail-closed: only literal JSON `true` admits Tier D or default-queue late-stage work. String values such as `"true"` or `"false"` do not admit.
13. `STRICT_RECEIPT_ADMISSION=0` downgrades `DONE` to process-exit evidence for manual recovery only; leave it unset for normal runner use.
14. Receipt admission uses `scripts/find_admitted_result.py` rather than assuming the result file stem matches the probe stem. It checks the exact basename, the `sim_`-stripped basename, literal `*_results.json` paths in the probe source, and result files modified during the run.
