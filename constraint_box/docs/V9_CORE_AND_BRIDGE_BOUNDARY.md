# ConstraintBox v9 core and bridge boundary

The v9 default command is deliberately smaller than the imported 0.3.x
candidate. It loads only the five core tools: Z3, CVC5, SymPy, Rustworkx, and
Maude.

`constraintbox-legacy` temporarily exposes the previous wide CLI so existing
receipts remain reproducible. That legacy surface contains Java/TLC/Apalache,
JAX, PyTorch, Julia, PySINDy, provider, and external-estate routes. Their
presence is recorded debt; they are not CB core and must not be used to report
the v9 core as integrated with those systems.

The migration rule is process isolation:

```text
CB finite request
  -> serialized bridge job
  -> external product process
  -> source/input-bound observation
  -> CB recomputation and gate
```

The external process never becomes a CB library. The repository-root
ClaimGate remains independent and receives artifacts through `cb-to-claimgate`.

The v9 `exercise` command is a bounded product test, not a scientific claim. It
uses a finite fixture to exercise one named API family from each of the five
tools and emits observations that the test suite recomputes.
