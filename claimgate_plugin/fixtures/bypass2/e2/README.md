# E2 — import severance without operation severance

`capability_worker.py` imports and touches JAX, then computes the complete
`jax_density` answer with Python's standard-library `math` module. The dispatch
list names JAX operations that never execute.

- Should happen: acceptance should fail because the claimed JAX operation did
  not produce the witness.
- Current behavior: the estate CLI reports `jax_density` as `READY`.
- Exact reach: `EstateRunner.run_capability()` runs import severance because
  `CAPABILITIES["jax_density"].block_import == "jax"`. It does not run the
  `operation` control because `sever_operation` is empty, and `operation` is
  absent from `expected_controls`.

`numpy_density` and `scipy_channel` are not used: both already register a
specific `sever_operation`. The genuinely open capability captured here is
`jax_density`.
