# UFPO v1 Preregistration Design State

Current state: `registry_designed_not_sealed`.

The new namespace, exclusions, exact objects, splits, challenge pairs, views,
seeds, architecture, controls, metrics, and thresholds are tracked. No v1 test
view, embedding, prediction, retrieval score, pair decision, or control score
has been generated.

The seal remains blocked until all of these source files exist in Git:

- `run_julia.jl`
- `run_jax.py`
- `run_pytorch.py`
- `recompute_metrics.py`
- `validate_results.py`
- `validate_preregistration.py`

The future seal must bind the exact Git commit and SHA-256 of every source,
`spec.json`, `object_manifest.json`, `generate_manifest.py`, and this design
note. Every test runner must reject an absent or drifting seal, a dirty source,
an existing result path, or a second test invocation.

The v0 learner attempt, metrics, objects, views, seeds, and weights are not v1
evidence. V0 may inform architecture repair only because v1 uses wholly new
deterministic objects and a new view namespace.
