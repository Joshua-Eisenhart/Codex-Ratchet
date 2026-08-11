# Deterministic Gates with Wide LLM Exploration

This is the core product principle.

Wide LLM exploration is useful, but only at bounded gates. LLMs propose:

- narrower claims
- stronger falsifiers
- useful tests
- caveat rewrites
- human reviewer briefs

The deterministic gate engine decides:

- blocked
- rework_required
- passed_with_caveats
- passed

## Noncommutative Order

Do not flatten the process.

```text
claim → effect → gates → exploration requests → next tick
```

is not the same as:

```text
exploration → narrative → claim → gate
```

The order matters because early narrative contaminates later admission.
