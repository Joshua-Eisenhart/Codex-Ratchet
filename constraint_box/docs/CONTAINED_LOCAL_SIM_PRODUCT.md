# Contained CB product with local simulation bindings

The product ZIP contains ConstraintBox source, ClaimGate, Mini-LevOS, the
attractor-basin controller, the 14-profile capability suite, the four-runtime
parity fixture, tests, and verification scripts. It deliberately excludes
CPython, Python packages, Julia packages, GPU drivers, credentials, remote
providers, and the broad external simulation estate.

`scripts/run_contained_local_sim_product.py` is the execution bridge between
those two boundaries. It takes explicit paths to a local Python environment,
Julia executable, Julia project, and external simulation-estate directory; it then runs the capability suite, the
JAX/Julia/PyTorch attractor-basin controller, ClaimGate's typed evidence
admission, and the same-fixture NumPy/JAX/PyTorch/Julia parity check. It can
also retain a separately produced Lev evaluation result through CB's strict
observer.

Example after extracting the ZIP:

```sh
PYTHONPATH=constraint_box/src \
  /path/to/python -B constraint_box/scripts/run_contained_local_sim_product.py \
  --output-dir /new/output-directory \
  --worker-python /path/to/python \
  --julia /path/to/julia \
  --julia-project /path/to/julia-project \
  --external-sim-estate /path/to/external_sim_estate
```

The runner will not install, select, or silently substitute a local runtime.
It requires every output directory to be new and emits one retained receipt.
Neither the ZIP nor the receipt claims complete engine portability, CR truth,
scientific proof, release, or promotion.

Java, TLC, and Apalache are not part of this product's execution surface. A
historical temporal adapter may remain in the source history, but no contained
verification or local-simulation run calls it.
