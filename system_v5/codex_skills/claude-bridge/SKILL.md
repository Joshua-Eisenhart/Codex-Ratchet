---
name: claude-bridge
description: Run or inspect a bounded Claude Code external-worker route from Codex with moving-alias routing, budget caps, hashed receipts, and explicitly non-gating evidence.
---

# Claude Bridge

Use this repo-held candidate when Codex needs a bounded Claude Code external
worker or needs to inspect how such a call would be routed. Claude output is
advisory evidence. It is never a code, simulation, proof, admission, promotion,
or release gate.

## Authority and safety boundary

- Repo authority remains `AGENTS.md`, `CODEX.md`, and the current process
  contracts. Claude output cannot override them.
- Every receipt has `advisory_only: true`, `gate_authority: false`,
  `evidence_allowed: false`, and false promotion, admission, release, launch,
  and scientific-claim flags.
- Run the deterministic receipt validator before counting an output as external
  worker evidence. A valid receipt proves integrity and routing only; it does
  not prove the worker was correct.
- This candidate does not retry, run an automatic auth diagnostic, or make a
  second provider call after a timeout.
- Tools are disabled unless `--tools` is explicit. Keep write-capable tools out
  of advisory and audit routes unless the current task specifically authorizes
  them.

## Model routing

Claude Code owns backend resolution for moving aliases. Keep these routes:

- `fable`, `fable5`, and `fable-5` route to the moving `fable` alias.
- `opus`, `sonnet`, and `haiku` route to their same-named moving aliases.
- `default` routes to Claude Code's configured `default`; it is not Fable.
- Explicit full model identifiers pass through unchanged.

The CLI output's `modelUsage` keys are the backend truth. Do not infer a
backend version from an alias or freeze a moving alias into this skill.

Inspect routing without loading a prompt, writing a receipt, or invoking
Claude:

```bash
python3 system_v5/codex_skills/claude-bridge/scripts/claude_bridge.py \
  --inspect-route --model fable5
```

## Dry inspection

Use `--dry-run` before a new route. It loads and hashes the prompt, constructs
the exact command, writes a hashed dry-run output and receipt, and never starts
Claude:

```bash
python3 system_v5/codex_skills/claude-bridge/scripts/claude_bridge.py \
  --dry-run \
  --model fable5 \
  --budget 2 \
  --prompt "Review this bounded packet and return risks plus an advisory verdict."
```

Validate the emitted receipt:

```bash
python3 system_v5/codex_skills/claude-bridge/scripts/validate_receipt.py \
  /tmp/codex_claude_bridge/<run>.receipt.json
```

## Live single-worker route

Only make a live call when the current task authorizes it. Always set a budget
for non-trivial work and normally set a wall-clock timeout:

```bash
python3 system_v5/codex_skills/claude-bridge/scripts/claude_bridge.py \
  --model sonnet \
  --budget 2 \
  --timeout-sec 120 \
  --prompt-file /tmp/bounded_prompt.txt
```

Use stream mode only when Agent/Task evidence matters, and explicitly allow the
needed tools:

```bash
python3 system_v5/codex_skills/claude-bridge/scripts/claude_bridge.py \
  --model sonnet \
  --stream \
  --tools Task,Read,Grep,Glob \
  --budget 3 \
  --timeout-sec 180 \
  --prompt-file /tmp/bounded_fanout_prompt.txt
```

Count completed task notifications, not starts or prose claims. Keep Claude
workers classified as external workers, never Codex-native subagents.

## Receipt interpretation

Report the receipt path, output path, requested route, routed alias, backend
models from `modelUsage`, observed cost when present, return code, timeout
state, and completed Task/Agent evidence. Preserve failed and partial receipts.

The receipt validator checks the command, route, budget summary, prompt/output
hashes, and non-gating constants. It deliberately does not judge scientific or
code correctness. Those decisions remain with deterministic repo gates and
current-authority review.

Historical fanout-size measurements from installed copies are intentionally
omitted from this operational candidate. Re-measure fanout in a separate,
dated stress artifact before adopting any concurrency default.
