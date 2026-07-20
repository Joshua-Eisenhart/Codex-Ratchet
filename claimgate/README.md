# ClaimGate

A deterministic receipt validator. It gates claims with code, never LLM judgment.

## What it checks

`claimgate.py` reads one `receipt.json` and runs six checks. Every failing
check is reported; the process never asks a model to grade the receipt.

1. `classification_missing` / `classification_not_allowed` — the top-level
   `classification` field must be present and in the allowed set.
2. `promotion_without_canonical_evidence` — if `promotion_allowed` is `true`,
   the receipt must carry canonical-by-process evidence
   (`accepted_status_label` in `{"passes local rerun", "canonical by process"}`).
3. `verdict_inflation` — flags any object where `pass: false` sits next to a
   string field reading `INTEGRATED` or `GREEN`, or where `all_pass: true`
   sits above a nested `pass: false`. This is the verdict-inflation detector.
4. `controls_missing` / `controls_copy_of_main_run` — only enforced on
   receipts claiming a high-tier status (`accepted_status_label` in the
   canonical-tier set, or `promotion_allowed: true`). Requires a `controls`
   section, and flags any control whose numeric leaves are an exact multiset
   match to the main run's numeric leaves (copy-paste detection).
5. `negative_mutual_information` — any key matching `*mutual_info*` with a
   value below `-1e-9` (floating-point noise around zero is not flagged).
6. `preregistration_missing` — same high-tier gate as (4); requires some key
   matching `preregist*` anywhere in the receipt.

Exit codes are the only interface:
- `0` = admitted, nothing printed.
- `1` = rejected, a JSON reasons array printed to stdout.

## How to run

Single receipt:

```
python3 claimgate/claimgate.py system_v8/unified/results/manifold_unified_v1/receipt.json
```

Full sweep over every `system_v8/**/receipt.json`:

```
python3 claimgate/run_sweep.py
```

Writes `claimgate/results/first_sweep.json` (per-receipt admit/reject + reasons).

Sweep result (2026-07-20, 109 receipts): 62 admit, 47 reject. Both known-tainted
receipts reject for real, general defects — not path-special-cased:
- `system_v8/unified/results/manifold_unified_v1/receipt.json` claims
  `accepted_status_label: "passes local rerun"` but has no preregistration
  header reference anywhere → `preregistration_missing`.
- `system_v8/nested_manifold/results/stage64/receipt.json` reports
  `all_pass: true` over a 64-candidate tournament but never declares a
  `classification` field → `classification_missing`.

## Lev wiring

`lev exec` can invoke claimgate.py as a loop-exit verifier and record the
pass/fail branch as a durable Lev evidence event:

```
lev exec "noop: report OK" \
  --until="verifier passes" \
  --verifier="python3 claimgate/claimgate.py <path/to/receipt.json>" \
  --surface shell --max-iterations=1
```

Confirmed working (`execId=473cd6c1e00e`, run against
`manifold_unified_v1/receipt.json`): `runtime-events.jsonl` records an
`exec.gate.run` event with `kind: "verifier"`, `branch_taken: "fail"`,
`exit_code: 1`, and the exact claimgate reasons JSON is captured at
`~/.local/share/lev/execution-ledger/artifacts/exec/473cd6c1e00e/loop-verifier/iteration-1/stdout.txt`.

Grep the event:

```
grep '473cd6c1e00e' ~/.local/share/lev/events/runtime-events.jsonl
```

Note: `--verifier` alone (without `--until`) does not execute the verifier —
it is only invoked as part of the `--until` loop-exit condition. The bare
`--verifier` flag with no `--until` produces a receipt with a placeholder
`passed: true` that never actually ran claimgate; this was confirmed as a
first attempt (`execId=4b834881e6b2`) before finding the working invocation
above.

## Plugin contract

ClaimGate is an independent plugin that consumes Lev — it is not part of Lev
core. Lev upstream moves on its own lifecycle; this plugin is reworked to
match whatever the current Lev CLI surface is, per update. Never patch Lev
core to make ClaimGate work.
