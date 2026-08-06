# Basic external engine packet

This packet is outside ConstraintBox. ConstraintBox may start it and check its
receipts, but the engines are not part of the ConstraintBox decision kernel.

The packet asks four installed tools to do small, real operations:

| Row | Exact operation | Positive check | Wrong claim that must be rejected | Boundary check |
|---|---|---|---|---|
| JAX | `jax.jit(jax.vmap(jax.grad(...)))` | derivative of a cubic at four points | an all-zero derivative | derivative at zero |
| PyTorch | `torch.func.jacrev` | Jacobian of a two-output map | an identity Jacobian | Jacobian at the zero vector |
| PySINDy | `pysindy.SINDy.fit(..., x_dot=...)` and `predict` | identify a supplied linear law and predict held-out derivatives | the opposite-sign law | derivative at the zero state |
| Julia | `DifferentialEquations.ODEProblem`, `solve`, and `Tsit5` | integrate a scalar linear flow and compare with its analytic terminal value | the opposite-sign flow | a zero-rate flow |

Each tool runs in a separate process. The broker sends canonical JSON through
standard input, independently recomputes the expected values, and records hashes
of the executable, worker source, input, and output. Missing runtimes or exact
APIs are `PARKED`; bad math, bad JSON, source drift, or other execution failures
are `FAIL`.

After all four rows pass, one integration runs. The broker freezes PySINDy's
identified rate into canonical JSON and binds its digest to the PySINDy input,
output, and worker source. A new Julia process reads that exact artifact and
uses the identified rate in `DifferentialEquations.solve`. The broker rejects a
missing artifact, changed bytes, or a canonical artifact with a substituted
rate before the consumer can count as passing.

A passing row means only that the named local operation passed these small
checks. It does not mean the whole engine is ready, that CR is true, or that the
worker is secure against hostile code.

Run it from the repository root with the canonical Python:

```sh
PYTHONPATH=constraint_box/src \
  /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  -m constraintbox.external_engine_packet --output /tmp/basic-packet.json
```
