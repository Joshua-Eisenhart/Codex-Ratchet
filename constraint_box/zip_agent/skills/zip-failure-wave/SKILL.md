---
name: zip-failure-wave
description: Use when falsifying a ConstraintBox ZIP Agent packet through the independently executable three-child ZIP failure wave.
---

# ZIP Agent Failure Wave

Run the wave as a ZIP tree. Do not substitute a prose council.

## 1. Bind one target

Use an existing ZIP_JOB, or create the deterministic demo:

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent build-demo \
  --out /tmp/cb-zip-demo.zip
```

Validation: record the target SHA-256 from command output.

## 2. Run all three child packets and compile

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent failure-wave \
  --target /tmp/cb-zip-demo.zip \
  --wave-packet /tmp/cb-zip-failure-wave.zip \
  --return-zip /tmp/cb-zip-failure-wave.return.zip \
  --cache-dir /tmp/cb-zip-cache
```

Required children:

- structure: replay, registry, task order, required-output equality
- counterexample: tamper, undeclared member, duplicate, traversal, unknown op,
  unproduced output
- authority-collapse: unknown-op refusal, input binding, byte replay

Validation: all three child return ZIPs exist inside the parent return ZIP.
Missing, refused, or cancelled child means the parent is not PASS.

## 3. Verify the parent return

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent verify-return \
  /tmp/cb-zip-failure-wave.return.zip --input /tmp/cb-zip-failure-wave.zip
```

Validation: `ZIP_RETURN_INTEGRITY_BOUND` and compiled verdict is `PASS` or
`REVISE`; never infer a missing verdict.

## 4. Repair and rerun, at most twice

If verdict is REVISE, patch only the exact failed boundary, run the full test
suite, rebuild the target, and rerun every child. Maximum two repair rounds.
Stopping because the loop cap was reached is `HOLD_LOOP_CAP`, not PASS.

Validation:

```bash
PYTHONPATH=src ../.venv/bin/python -m pytest -q -p no:cacheprovider
```

## Rationalization guard

| Shortcut | Why it is false |
|---|---|
| "Two members passed." | The wave requires all declared children. |
| "The parent summarized the missing child." | A summary cannot replace a child return ZIP. |
| "The test suite is green." | The compiled wave report and child receipts are separate evidence. |
| "Self-audit proved security." | Self-audit is bounded falsification, not independent proof. |
| "The loop ended." | Only a compiled PASS is PASS; cap exhaustion is HOLD. |

Claim ceiling: prototype self-falsification only; not an independent model
council, host-hook proof, admission, promotion, or release.
