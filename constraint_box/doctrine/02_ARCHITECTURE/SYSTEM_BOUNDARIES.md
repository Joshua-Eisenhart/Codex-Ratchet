# System Boundaries

ConstraintBox is independently runnable.  One repository may contain
ConstraintBox, CR and simulation work without turning them into one dependency
graph or authority domain.

## Planes

| Plane | Input | Output | Explicit non-authority |
|---|---|---|---|
| ConstraintBox controller | task kind and immutable payload | operational disposition and evidence refs | scientific truth |
| Agent proposal plane | bounded object view | candidates, attacks and repairs | commands, tolerances, verdicts |
| Deterministic worker plane | controller ticket | observation artifact | admission |
| Finite constraint plane | finite IR and bound | witness, bounded exhaustion or unknown | unrestricted theorem |
| Relative Ratchet plane | frozen bundle, demand and nests | plural frontier or `HOLD` | absolute MSS |
| CR plane | admitted bounded observations | scientific candidates and falsifiers | platform policy |
| Sim Fleet | named finite function | numeric/symbolic observation | self-certification |
| LevOS adapter | public Lev execution/eval surface | host observation | ConstraintBox trust root |

## Trust topology

```text
human or host
    |
    v
controller-owned policy root
    |
    +--> untrusted agent view --> proposal only
    |
    +--> capability ticket --> isolated worker --> artifact
    |                                      |
    +<------------- independent evaluator-+
    |
    +--> ledger + branch complex + disposition
```

The policy root, capability registry, checker, tolerance, resource budget, and
claim ceiling are not writable through an untrusted request.

## Controller lifecycle

```text
RECEIVED
  -> NORMALIZED
  -> PROPOSED
  -> AUTHORIZED
  -> RUNNING
  -> OBSERVED
  -> EVALUATED
  -> ELIGIBLE | PARKED | BLOCKED | HOLD
```

An agent proposal never skips directly to an evaluated state.
