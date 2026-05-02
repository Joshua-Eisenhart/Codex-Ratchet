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

1. Reads queues in priority order: `queue_tier_a.txt` → `queue_tier_b.txt` → `queue_tier_d.txt` → `queue_default.txt`.
2. Picks the first un-done probe from the highest-priority non-empty queue.
3. Runs it with `nice -n 19`, captures result.
4. Marks the queue line as `# DONE <timestamp>` or `# FAIL <timestamp>`.
5. Sleeps between sims; cooldown sleep if hot.
6. Repeats forever.

## Priority rules

- Tier A queue drained before B, B before D. Foundation first.
- Within a queue, top-to-bottom order (Hermes terminals append).
- `queue_default.txt` = fail-closed fallback only. It should contain only controller-approved tool/tool-integration/local-lego entries, and it is allowed to stay empty.
- `queue_default.txt` must not auto-queue pairwise/coexistence/bridge/axis/engine-style probes.
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

One probe basename per line (relative to `system_v4/probes/`, no `.py` suffix). Lines starting with `#` are ignored. Runner rewrites completed lines to `# DONE <timestamp> <basename> (<dur>s)`.

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

1. One sim at a time. No parallelization (keeps laptop cool, keeps logs simple).
2. `nice -n 19` always; never `sudo`.
3. Runner only reads queues and executes; never writes probe source.
4. Unhandled probe exception → log, move on, don't retry.
5. 5 consecutive failures → pause 30 min, telegram L3 once.
6. Runner obeys `system_v5/ops/.stop_sim_runner` sentinel file between sims.
7. The hard stage gate wins over stale queue contents: no pairwise/coexistence/bridge/axis/engine probe may run from `queue_default.txt`.
8. If all tier queues are empty and no safe default queue exists, the runner stays idle rather than generating a generic never-run pile.
9. Runner admission must not treat all sims as one bucket. Before v2 enforcement, use `make runner-taxonomy-audit` to map current probes to `classical`, `nonclassical`, and `bridge` execution kinds and surface routing gaps.
