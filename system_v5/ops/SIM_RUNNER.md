# Sim Runner — strict admission, parallel-safe where rows are independent

Pure Python + shell. No LLM in the loop. Drains admitted queues, pauses or
blocks when safety gates fail, and preserves controller-owned reconciliation.

Status: this document describes two live runner surfaces:

- `system_v5/ops/sim_runner.sh` — legacy single-worker tier-file drain.
- `scripts/overnight_two_runner.sh` — parallel worker-pool runner using
  atomic queue claims under `system_v4/probes/a2_state/queue/`.

The older v1 tier-file runner is conservative. It is not the architecture
ceiling. Lego, micro-lego, tool-function, and admitted independent coupling
rows are innately parallel when their queue claims, result paths, fixtures,
logs, and ledger loopbacks do not collide.

## Runner taxonomy

Agents and LLM workers may write, repair, audit, or enqueue probes. They do not execute sims. Executable evidence comes from Python runner classes.

The runner layer must distinguish three execution kinds:

1. `classical` — classical baselines, controls, and negative/reference comparisons. These preserve the before-picture and must not be promoted into nonclassical evidence.
2. `nonclassical` — canonical nonclassical-target sims. These use the nonclassical stack where claim-relevant: PyTorch/PyG for tensor and graph dynamics, Clifford for geometric product/spinor/rotor claims, and z3/cvc5 for structural proof or UNSAT claims.
3. `bridge` — sims that connect classical baselines to nonclassical structure, including `bridge`, `Xi`, `rho_AB`, `Phi0`, cut/kernel, pairwise/coupling, and coexistence work. Bridge sims need both sides named: the classical baseline being bridged from and the nonclassical tool plan being bridged to.

Graph and proof tools are not universally valid across all three kinds. A graph/proof surface can be `classical-only`, `bridge-useful`, `nonclassical-support`, or `nonclassical-core`; the runner should admit it only in the matching execution kind.

## Role separation

- **Hermes terminals** (Tier A / B / D) — write probes, enqueue them, monitor the runner's log. They do NOT execute sims.
- **Runner** — claims admitted queued probes, runs them, writes result JSON,
  logs, and records terminal queue state. Runner success is still not ledger
  acceptance.

## Parallel execution model

Run many workers when rows are independent. Parallelism is allowed for:

- separate tool/function MICRO rows;
- independent classical baselines;
- independent lego rows with distinct result JSONs and fixtures;
- independent admitted coupling rows after the stage gate allows them and exact
  parent receipts are named;
- variants of the same triple when each writes its own artifact namespace.

Parallelism is blocked for:

- shared queue mutation without atomic claims;
- shared result paths or fixture directories;
- ledger reconciliation or promotion;
- rows with prior-receipt dependencies not yet satisfied;
- bridge/coupling/axis/engine rows blocked by `stage_gate.json`;
- any row lacking strict Wizard queue admission when strict admission is on.

The parallel worker-pool runner uses atomic file claims, so many workers can
claim distinct rows safely. Controller synthesis, admission writes, ledger
loopback, Git/index mutation, and promotion remain serial.

## Legacy tier-file runner tick

1. Reads queues in priority order: `queue_tier_a.txt` -> `queue_tier_b.txt` -> `queue_tier_d.txt` only when `stage_gate.json` permits Tier D -> `queue_default.txt`.
2. Picks the first un-done probe from the highest-priority non-empty queue.
3. Runs it with `nice -n 19`, captures result.
4. Validates the canonical result JSON with strict executable run-boundary admission.
5. Marks the queue line as `# DONE <timestamp>` only after the Python process exits cleanly and the receipt is admitted; otherwise marks `# FAIL <timestamp>`.
6. Sleeps between sims; cooldown sleep if hot.
7. Repeats forever.

`DONE` is runner execution plus strict receipt-admission evidence. It still
does not update the ledger by itself or make coupling rows ready; controller
reconciliation must connect the queue row, canonical result JSON, packet scope,
and ledger loopback before any downstream claim moves.

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

`FAIL` and `INELIGIBLE` are not wasted when they expose the exact contract miss,
missing artifact, demotion condition, or boundary failure. They support the
ratchet as exclusions and next-packet constraints. They never self-promote into
readiness.

## Autoresearch queue clients

Autoresearch clients are adapter/runtime clients, not runner authorities. They
may propose or enqueue bounded packets only when the packet references
`system_v5/ops/codex_autoresearch_contract.md`, has `launch_mode=owner_authorized`,
and records `guardrail_check=PASS`. They must not self-promote pre-run output
to queue readiness, write `admitted_by`, or treat runner DONE as accepted
evidence. The controller still has to read the cited queue row, result JSON,
stage gate, ledger loopback, and admission artifact.

Before a non-browser sim/controller run, run the fail-closed preflight:

```bash
make runner-preflight
```

If it reports stale `SkyComputerUseClient` helpers, stop those helpers before launching the runner unless an active computer-use task intentionally owns them.

Both runner surfaces run `scripts/helper_process_audit.py --strict` at startup
and refuse to launch when stale browser/computer-use helpers are present.
`ALLOW_HELPER_PROCESSES=1` exists only for an explicitly owned
browser/computer-use task; do not use it for ordinary sim runs. The legacy
tier-file runner creates `system_v5/ops/.sim_runner.lock` and exits if another
legacy tier-file runner owns that lock. The parallel worker-pool runner uses
`/tmp/codex_ratchet_overnight.lock` for one controller process plus many
worker children.

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

Parallel dry-run:
```bash
make parallel-runner-dry MINUTES=1 LANE_A_PARALLEL=2 LANE_B_PARALLEL=4
```

Parallel admitted run:
```bash
make parallel-runner MINUTES=30 LANE_A_PARALLEL=2 LANE_B_PARALLEL=4
```

Stop gracefully:
```bash
touch system_v5/ops/.stop_sim_runner
```

## Rules

1. Use parallel worker pools for independent admitted rows. Use the legacy
   single-worker tier-file runner only when debugging, conserving heat, or when
   queue/result isolation has not been proved.
2. `nice -n 19` always; never `sudo`.
3. Runner only reads queues and executes; never writes probe source.
4. Unhandled probe exception → log, move on, don't retry.
5. 5 consecutive failures → pause 30 min, telegram L3 once.
6. The legacy runner obeys `system_v5/ops/.stop_sim_runner` sentinel file
   between sims. The parallel runner obeys its minute budget and stops worker
   pools at the budget boundary.
7. The hard stage gate wins over stale queue contents: no pairwise/coexistence/bridge/axis/engine probe may run from `queue_default.txt` unless `allow_default_queue_late_stage` is explicitly true.
8. If all tier queues are empty and no safe default queue exists, the runner stays idle rather than generating a generic never-run pile.
9. Runner admission must not treat all sims as one bucket. Before v2 enforcement, use `make runner-taxonomy-audit` to map current probes to `classical`, `nonclassical`, and `bridge` execution kinds and surface routing gaps.
10. Tier D is gated by `stage_gate.json`. If `allow_tier_d_launch` is false, the live runner skips `queue_tier_d.txt` even when rows are present.
11. Coupling readiness must come from reconciled parent receipts, not from aggregate DONE counts.
12. `stage_gate.json` booleans are fail-closed: only literal JSON `true` admits Tier D or default-queue late-stage work. String values such as `"true"` or `"false"` do not admit.
13. `STRICT_RECEIPT_ADMISSION=0` downgrades `DONE` to process-exit evidence for manual recovery only; leave it unset for normal runner use.
14. Receipt admission uses `scripts/find_admitted_result.py` rather than assuming the result file stem matches the probe stem. It checks the exact basename, the `sim_`-stripped basename, literal `*_results.json` paths in the probe source, and result files modified during the run.
15. **Wizard v4.2 fanout guard:** Workers inside a Wizard v4.2 parallel fanout wave must not append directly to any `queue_*.txt` file. They return proposed queue entries in their receipt under a `proposed_queue_entries` field. The controller serializes the actual append to the correct tier queue after all fanout receipts return. The Hermes single-terminal enqueue convention (`echo "probe" >> queue_tier_a.txt`) remains valid only for non-fanout, single-worker Hermes terminals where no parallel wave is active.
16. `STRICT_WIZARD_QUEUE_ADMISSION=1` is the live default. A row can be selected only when `scripts/wizard_sim_admission.py` finds a v4.2 queue-ready admission artifact under `system_v5/ops/wizard_admissions/` or `system_v5/wizard/admissions/`. Missing or bad admission becomes `INELIGIBLE`, not `FAIL`; it is structural gate evidence, not a scientific result. Legacy v4.1 admission artifacts are reference-only unless a recovery run explicitly names v4.1.
    The validator enforces this boundary by requiring `wizard_sim_admission_v4_2` by default; `--allow-legacy-v4-1` is recovery-only and must not be used by unattended runners.
17. A Wizard sim admission must be written by an independent non-runner/non-manager route, cite controller-read artifacts, pass the universal bounded-work gate, pass the strict sim packet gate, name one exact packet, and include the formal sim profile fields. Pre-runs, runner output, council agreement, manager receipts, or route salience do not admit a queue row by themselves.
18. **Sim heartbeat rule:** a clean helper preflight plus empty `lane_A`, `lane_B`, and `claimed` counts is not a successful loop by itself. The controller must either enqueue/select the smallest admissible micro tool/function move or write a tracked blocked-reason artifact under `system_v5/ops/lego_scaling/` or `system_v5/ops/wizard_admissions/`. Blocked-reason artifacts must be JSON with `kind: "blocked_reason"`, an ISO `created_at` or `generated_at`, a non-empty reason/scope, and a concrete `next_admissible_step` or `recommended_next_move`. `scripts/wizard_v4_2_runtime_audit.py` treats idle queues with no blocked reason as a runtime failure.
19. **Worker-pool receipt rule:** mixed Codex, Claude, Gemini, OMX, tmux, and tool receipts must validate with `scripts/validate_wizard_worker_receipts.py` before any count is used in Wizard topology or council claims. External pools remain external worker evidence; they do not become Codex-native subagents.
20. **Bypass receipt rule:** if `STRICT_RECEIPT_ADMISSION=0` or `STRICT_WIZARD_QUEUE_ADMISSION=0` is used for bounded recovery, the runner requires the recovery sentinel and writes a timestamped `bypass_*.json` receipt under `system_v5/ops/wizard_admissions/`. Remove the sentinel before returning to normal sim runs.
21. **Helper and bypass recheck rule:** long-running sim loops rerun helper-process preflight every `STATS_EVERY` completed sims and stop if a non-strict admission recovery run loses its sentinel mid-run. `ALLOW_HELPER_PROCESSES=1` is only for a same-session browser/computer-use task with an explicit human note; do not leave it exported for unattended sim work.
