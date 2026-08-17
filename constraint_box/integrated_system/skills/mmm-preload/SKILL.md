---
name: mmm-preload
description: Use when any root agent, worker, child, council member, or nested member must receive a real combination of mini-voice MMM bytes before work and leave a verifiable preload and call receipt.
---

# MMM Preload

Bind actual mini-voice MMM bytes into the prompt sent to an agent. MMMs are salience material, never rules, authority, or proof that a model attended to them.

## Operational mini-MMM set

Operational preloads use exactly the nine mini voices:

- voices: Factory, Feynman, Hume, Orwell, Popper, Pushback, Strategy, Systems, Zhuangzi, each full and compact

`FULL_MMM_v4_3.md` and `COMPACT_MMM_v4_3.md` are tuning/reference sources, not operational preload material. Registry cards, lane cards, guards, compositions, and system routes are also excluded. Do not silently include any of them.

## Required route

1. Before doing task analysis, run `scripts/mmm_preload.py prepare`.
2. Give the produced `composed_prompt.md` bytes—not merely file paths—to the actual agent/provider call.
3. Preserve `preload_receipt.json` beside the call receipt.
4. Use `verify-content` for local byte checks only. It never counts as a dispatched cell.
5. Run `scripts/mmm_preload.py verify` with the provider call receipt and controller-expected invocation identity before counting that cell as MMM-equipped.
6. Run `verify-round` over all member receipts before dispatch when the wave requires distinct combinations.
7. After context compaction or a nested spawn, prepare and bind a new preload. Parent preload does not cover children.

Example:

```bash
python3 scripts/mmm_preload.py prepare \
  --task-file task.md --output-dir /tmp/cb-cell-01 \
  --run-id run-01 --agent-id cell-01 --parent-id council-a \
  --seed 81423 --voice-count 3 \
  --voice-variant mixed --max-bytes 240000

python3 scripts/mmm_preload.py verify-content \
  --receipt /tmp/cb-cell-01/preload_receipt.json

python3 scripts/mmm_preload.py verify \
  --receipt /tmp/cb-cell-01/preload_receipt.json \
  --call-receipt /tmp/cb-cell-01/provider_call_receipt.json \
  --expect-run-id run-01 --expect-agent-id cell-01 \
  --expect-parent-id council-a --expect-wave-id failure-wave \
  --expect-round 1 --expect-depth 2

python3 scripts/mmm_preload.py verify-round \
  --receipts /tmp/cb-cell-*/preload_receipt.json
```

## Dispositions

- `CONTENT_BOUND`: selected bytes and task bytes were read and compiled into the recorded prompt.
- `REFUSE_MMM_BUDGET_EXCEEDED`: exact selection is too large. Do not substitute compact files silently; choose a new recorded configuration.
- `REFUSE_MMM_SOURCE_DRIFT`: a selected source no longer matches the receipt.
- `REFUSE_COMPOSED_PROMPT_DRIFT`: compiled prompt bytes changed.

`CONTENT_BOUND` is not `PROVIDER_DISPATCH_PROVED`. The provider adapter must additionally bind the composed-prompt digest to its own request/call receipt. Never claim cognition or behavioral influence from preload evidence.

`receipt_self_checksum` detects accidental inconsistency only. It is not a signature, custody anchor, or protection against a writer who can change the receipt and recompute it.

## Randomness

Record the seed, algorithm version, resolved paths, and ordering. The v2 selector uses digest ordering rather than runtime sampling, so its exact selection is replayable. Different cells in a round must have different resolved mini-MMM path sets unless the wave explicitly tests repetition.

## Completion check

A cell counts as MMM-equipped only when `MMM_CALL_VERIFIED` is returned and:

- the receipt verifies;
- every selected file is one of the nine mini voices in a full-mini or compact-mini form;
- `included_bytes == source_bytes` for every selection;
- composed prompt digest verifies;
- the provider call receipt, when one exists, names that same prompt digest;
- the cell was not cancelled, skipped, or substituted.
