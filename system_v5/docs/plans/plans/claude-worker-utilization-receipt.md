# Claude Worker Utilization Receipt

Status: checked live receipt
Date: 2026-04-20
Purpose: record what is actually proved about Claude-first worker usage on this machine and in this repo, so model policy is grounded instead of guessed.

## Checked Claude CLI capability fact
- `claude auth status --text`
- result:
  - authenticated Claude CLI session available

## Checked machine/runtime facts
- `claude` present: `/usr/local/bin/claude`
- Claude Code version: `2.1.112`
- `codex` present: `/usr/local/bin/codex`
- Codex version: `0.118.0`
- `tmux` absent
- `mngr` absent
- `omc` absent
- `omx` absent
- logical CPU count: `10`

## Proved Claude paths now

### 1. Direct Claude print-mode worker path — PROVED
Initial direct Claude print-mode read-only workers were launched successfully with:
- `--model sonnet`
- `--effort xhigh`
- `--allowedTools Read`
- `--output-format json`
- `--max-turns 3`

Observed outputs:
- worker A: lane row extraction
- worker B: controller/harness worker-model extraction
- worker C: smoke-test plan extraction

Observed model usage:
- `claude-sonnet-4-6` used in all three direct worker runs
- helper routing also showed `claude-haiku-4-5-20251001` in `modelUsage`

Observed evidence files:
- `/tmp/claude_smoke_a.json`
- `/tmp/claude_smoke_b.json`
- `/tmp/claude_smoke_c.json`

### 1A. Reusable launcher/receipt tooling — PROVED
Added:
- `system_v5/ops/cli_worker_scale_probe.py`

This launcher can run bounded parallel CLI worker probes for:
- `claude`
- `gemini`

and write machine-readable receipts.

### 1B. Tuned Claude scaling probes — PROVED
Using the launcher with:
- `--provider claude`
- `--model sonnet`
- `--effort high`
- `--max-turns 5`

bounded read-only extraction probes succeeded at:
- `4/4`
  - `/tmp/claude_probe_4_summary.json`
- `6/6`
  - `/tmp/claude_probe_6_summary.json`
- `8/8`
  - `/tmp/claude_probe_8_summary.json`
- `10/10`
  - `/tmp/claude_probe_10_summary.json`

### 2. Direct Claude Opus synthesis path — PROVED
One direct Claude print-mode synthesis worker was launched successfully with:
- `--model opus`
- `--effort max`
- `--allowedTools Read`
- `--output-format json`
- `--max-turns 4`

It exited `subtype=success`.

Observed model usage:
- `claude-opus-4-7`

Observed evidence file:
- `/tmp/claude_opus_policy.json`

## Not yet proved

### 3. Claude-routed delegate_task ACP path — NOT YET PROVED
A `delegate_task` run was attempted with:
- `acp_command: claude`
- `acp_args: --acp --stdio --model sonnet --effort xhigh`

But the returned task metadata still labeled the child results as `model: gpt-5.4`.
That means the Claude ACP route is currently ambiguous from the controller side.

Operational rule:
- do not treat Claude-routed `delegate_task` as a proved Claude path yet
- treat direct `claude -p` workers as the proved Claude path right now

## Current admitted scaling rule
What is proved today:
- initial `3` parallel direct Claude print-mode workers succeeded
- tuned direct Claude Sonnet read-only probes succeeded at `4/4`, `6/6`, `8/8`, and `10/10`
- `1` direct Claude Opus synthesis worker succeeded

What that honestly proves:
- `10` parallel direct Claude print-mode workers are now proved for this bounded read-only extraction task family
- this is real evidence for Claude-first scaling on this machine
- it is not yet the same as proving `10` parallel write-producing or mixed maintenance packets

What the current repo docs already admit:
- on this 10-core machine, tool-capability waves may scale up to `8` top-level Claude workers if file sets/results/maintenance surfaces remain non-overlapping and Hermes can still reread every touched artifact/doc before promotion

So the honest current stance is:
- `10` parallel direct Claude workers are proved for bounded read-only extraction packets
- `8` was already conditionally admitted by repo docs and is now exceeded by direct receipt evidence for this safer packet family
- `10` is still not yet a proved default for write-producing packets touching live repo surfaces

## Observed 4-way scaling probe
A first 4-worker direct Claude Sonnet `high` probe was tried with:
- `--json-schema`
- `--max-turns 3`

Observed result:
- `1/4` worker succeeded
- `3/4` workers failed with `subtype=error_max_turns`
- `api_error_status=null` on those failures
- no rate-limit/overload signal appeared in the returned JSON

Follow-up checks:
- rerunning one of the failed extraction tasks with the same settings but `--max-turns 5` succeeded immediately
- then the tuned launcher probes succeeded at `4/4`, `6/6`, `8/8`, and `10/10`

Operational reading:
- the apparent "cap" here was not proved to be rate pressure
- the first real failure mode found was under-budgeted `max_turns` for file-read + structured-output tasks
- for extraction tasks on non-trivial files, prefer `--max-turns 5` over `3`

## Claude-first model policy

### If multiple Claude workers are available
Use:
- `sonnet` with `xhigh` or `high` for most bounded packet workers
- reserve one `opus` / `opus-4-7` `max` worker for:
  - hardest packet
  - synthesis
  - arbitration
  - post-batch reconciliation on the most confusing surface

### If only one Claude worker is effectively available
Use:
- `opus` / `opus-4-7` with `max`
- put it on the hardest/highest-leverage packet, not routine extraction

### GPT usage rule for now
- GPT-5.4 high remains available as overflow/supportive capacity
- good fits:
  - secondary falsifier audits
  - controller summarization
  - non-primary side work
- but Claude is the primary worker family to maximize first

## Immediate next test if we want to push harder
Now that read-only direct Claude scaling is proved through `10/10`, the next useful test is:
1. choose a small non-overlapping write-producing maintenance packet set
2. use direct `claude -p` print-mode workers first
3. capture per-worker `modelUsage`, exit state, duration, and any rate-limit/overload signals
4. check whether Hermes can still reread and reconcile every touched surface without losing truth discipline

## One-sentence summary
Claude is no longer just underused-by-policy; the directly proved path is now parallel `claude -p` print-mode workers through `10/10` on bounded read-only extraction packets, while Claude-routed `delegate_task` remains ambiguous and write-producing high-parallel waves are still not yet separately proved.
