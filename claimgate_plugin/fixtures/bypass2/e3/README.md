# E3 — capability names manufacture independence

`same_formula.py` computes one closed-form density result once and emits three
receipts whose only meaningful difference is `capability_id`:
`numpy_density`, `jax_density`, and `torch_density`.

- Should happen: parity should refuse three labels backed by one computation.
- Current behavior: the `estate-parity` CLI reports `READY`.
- Exact reach: `parity.compare_density_receipts()` keys `sources` by
  `capability_id`, infers independent families from those strings, and never
  checks producer or computation identity.

The runner writes the generated receipts to a temporary directory and drives
the real CLI. This fixture captures the gap; it does not close it.
