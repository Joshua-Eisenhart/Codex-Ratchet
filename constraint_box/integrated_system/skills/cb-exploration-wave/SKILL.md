---
name: cb-exploration-wave
description: Multi-branch induction harvest. Zhuangzi leads. Propose rival futures of the present Light object and keep the antichain. Do not falsify, pick a winner, or collapse orders. Use when the user asks for exploration, induction, rival readings, or many possible futures.
---

# CB Exploration Wave

This is induction. It is not Failure and it is not Verify.

Failure is its own full wave. Falsification is deduction. This wave only
proposes. The measure is new rival readings. They should rise, then saturate.
The output is an antichain.

The object may be right while the order is wrong. Live futures constitute
the present until deduction excludes them.

## Children

1. Harvest instances. Deterministic.
2. Name rival readings. `voice-zhuangzi`.
3. List load-bearing assumptions per reading. `assumption-audit`.
4. Compile each reading to a finite packet. `distinguishability-smt`.
   Dualsolve is not a seat here.
5. Keep the antichain. Deterministic. No winner.

Every model-backed cell uses `mmm-preload`. Distinct mini-voice sets.

## Deterministic runner

```text
python3 ~/.codex/skills/cb-exploration-wave/scripts/run_exploration.py \
  --root /path/to/constraint_box \
  --seed fixtures/cr/manifold_time_first_seed_v1.json \
  --out /path/to/exploration.receipt.json
```

The runner writes the receipt and an antichain draft. It never kills a
branch. Asking it to pick a winner or falsify refuses.

## Terminals

- `ANTICHAIN_OPEN` — two or more incomparable readings, no winner
- `HOLD` — fewer than two readings, or diversity collapsed
- `REFUSE` — asked to falsify, pick a winner, or merge into one future
- `CANCELLED`

## Claim ceiling

Rival-reading harvest only. Not a kill. Not a quotient. Not Light
geometry. Not promotion.
