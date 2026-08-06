# Maintenance and Update Protocol

## Boot sequence

Every requested estate layer performs:

1. hash the controller policy, worker source, fixture and active lock;
2. confirm the intended interpreter and executable paths;
3. compare installed versions with the active tested lock;
4. run the layer's cheap positive witness;
5. run the declared wrong-answer control;
6. confirm the required library was load-bearing through severance;
7. emit a bounded health receipt;
8. refuse the major run on `DRIFT`, `FAILED`, or required `UNAVAILABLE`.

Only the requested layer is booted. Starting a ConstraintBox intake job must not
load the cloud or science-field estate.

## Update sequence

“Current” means **latest candidate that passed**, not newest upstream package.

```text
check upstream
    -> build isolated candidate environment
    -> freeze exact resolved versions and artifact hashes
    -> run positive, negative, severance, mutation and replay controls
    -> run cross-layer compatibility fixtures
    -> compare resource budgets
    -> promote the candidate lock atomically or retain the prior lock
```

The active environment is never upgraded in place.

## Cadence

| Trigger | Work |
|---|---|
| every boot | hashes, versions and cheap witness for requested layer |
| before every major run | full acceptance for every participating capability |
| weekly | upstream-version availability report; no automatic promotion |
| after any lock change | complete affected layer plus adjacent-layer contracts |
| monthly | rebuild from empty environment and compare receipts |
| before cloud spend | local CPU golden, container digest and cost ceiling |

## Compatibility direction

A higher estate layer depends on receipts from lower layers. Lower layers do not
become dependent on higher ones:

```text
E0 <- E1 <- E2
       ^
       |
      E3
```

`E3` accelerates selected `E1` or `E2` work. It is not a fourth mathematical
truth source.
