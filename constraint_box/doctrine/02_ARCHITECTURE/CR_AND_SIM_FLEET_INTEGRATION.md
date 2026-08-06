# CR and Simulation Fleet Integration

ConstraintBox, the Sim Fleet, and Codex-Ratchet may live together while
remaining independently installable.

## Dependency direction

```text
ConstraintBox core
     |
     +--> optional numeric/SMT profiles
     |
     +--> Sim Fleet adapter ----> isolated JAX / science / GPU workers
     |
     +--> CR adapter -----------> quotient/manifold/object research
```

The full engines are not imported into the lean controller process.

## Sim worker contract

| Controller owns | Worker reports |
|---|---|
| profile and version | raw observation |
| executable and source digest | output artifact |
| environment/lock digest | device/runtime facts |
| input/output schemas | process stdout/stderr |
| timeout/memory limits | resource usage |
| checker/tolerance | no verdict |
| positive/negative fixtures | no admission |
| severance and mutation controls | no `load_bearing` self-label |
| claim ceiling | no promotion |

Integration proceeds function by function. A JAX, Julia, Torch or symbolic
worker becomes usable only after its named finite function passes its own
profile.  “Installed” does not mean “integrated.”

The active pack exercises JAX, Diffrax, quimb, cotengra, PySINDy, PyDMD and
pymdp in separate environments. Julia and Torch are candidate extensions, not
active local dependencies.

## CR adapter boundary

The first CR boundary is the finite observation bundle implemented in
`runtime/src/constraintbox/ratchet.py`:

1. controller freezes presentations and probes;
2. a worker provides a response matrix;
3. ConstraintBox derives partitions;
4. active demand edges filter candidates;
5. only candidates with a shared nesting witness are ranked;
6. non-nested rivals remain live and uncompared;
7. the result is packet-relative.

No manifold layer, engine stage, Weyl/Hopf carrier, nonassociative algebra, or
scientific object claim is admitted by this fixture.

## Later engine use

Full engine schedules should be external experiment objects containing:

- explicit loop as a cycle, with no privileged computational start unless a
  task profile selects one;
- ordered stage maps and bracketed composition;
- unreset state handoff where required;
- rival schedules retained;
- numerical observation artifacts;
- analytic/exact-small controls;
- independent engine witnesses;
- controller-owned discriminators.

ConstraintBox can establish that a named implementation ran under a named
contract.  It cannot make the engine structure canonical.
