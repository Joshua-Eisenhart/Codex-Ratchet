---
name: cb-wave-author
description: Use when creating or revising an independently callable ConstraintBox wave skill composed of smaller skills, deterministic tools, mini-MMM preloads, bounded loops, and receipt checks.
---

# CB Wave Author

Create one directory per wave. Each wave must run independently before a parent skill may compose, order, or loop it.

## Required files

- `SKILL.md`: trigger, inputs, execution, outputs, negatives, claim ceiling
- `wave.json`: machine-readable topology and completion contract
- optional `scripts/`: deterministic preparation and validation
- `tests/`: positive, refusal, cancellation, and missing-evidence cases

## Recursive composition

- A leaf skill performs one bounded operation.
- A wave skill orders or loops leaf skills.
- A council skill orders or loops wave skills.
- A campaign skill may order or loop councils.

Every level is independently callable and produces its own receipt. A parent does not erase child receipts, substitute for child execution, or turn missing children into a smaller successful wave.

## Authoring sequence

1. Record the manual baseline and its shortcuts.
2. Define the bounded object and exact input digest.
3. List child skills and deterministic tools.
4. Require `mmm-preload` for every model-backed cell. Only mini-voice files are eligible.
5. Define divergence, exchange, convergence, repair, and exact rerun order.
6. Define a finite loop cap and terminal reasons.
7. Define missing, cancelled, disagreement, and tool-failure states.
8. Validate `wave.json` and run adversarial tests.
9. Run the wave alone before admitting it into a parent skill.

Runtime assignments are invocation data, never wave identity.

```bash
python3 scripts/validate_wave.py /path/to/wave.json
python3 scripts/verify_wave_execution.py /path/to/wave.json /path/to/execution.json
```

An authored wave is not an executed wave. The execution verifier requires an exact receipt for every declared child, each bound through mini-MMM preload, call, terminal state, tool observations, and output digest. Nested wave children must retain their own wave receipts.
