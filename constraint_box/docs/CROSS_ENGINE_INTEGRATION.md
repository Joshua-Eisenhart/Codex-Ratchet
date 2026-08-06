# Cross-engine integration

CB verifies an already-installed foreign workload; it does not contain that
workload. This page describes bounded cross-engine verification, not an engine
install or a general sim-stack readiness claim. Install external runtimes first;
see [SIM_SETUP.md](SIM_SETUP.md).

## First packet

`constraintbox engine-test` runs the first fixed packet:

```text
controller-selected Python
  -> JAX grad/vmap/jit row
  -> PyTorch jacrev row
  -> PySINDy fit/predict row
  -> controller-built identified-rate JSON
  -> controller-selected Julia strict-carrier ODE solve
  -> deterministic receipt validation
```

The PySINDy-to-Julia JSON is a real bounded producer/consumer handoff. The JAX
and PyTorch rows are independently checked components in the same packet; they
are not claimed to consume peer output.

```bash
PYTHONPATH=src python -m constraintbox engine-test --output /tmp/cb-packet.json
```

An unavailable compatible runtime returns `PARKED`; it does not fall back to a
different executable. An injected alternate runtime returns `FAIL` with
`runtime_selection_override_rejected`.

## Full fixed capability suite

`constraintbox capability-suite` records two independent facts for each fixed
profile:

1. `disposition`: whether the named bounded operation executed and replayed
   locally.
2. `runtime_contract_report`: whether the adapter has a controller-selected
   profile or remains host-bound.

Each row is dispatched in one fresh controller-selected child and independently
replayed in a second fresh child. A crash, timeout, malformed output, or replay
failure produces a non-eligible component; it cannot be turned into a green
aggregate by an LLM or a hand-written receipt.

## Evidence ceiling

A passing receipt establishes only its named operation and controls. It does
not establish general engine readiness, simultaneous mass integration, CR
truth, scientific validity, release, or promotion. Nine direct profiles have a
controller-selected profile but no clean external-install proof; the other four
remain host-bound. An LLM may explain a parked or failed receipt, but never
selects a runtime, package version, worker, gate, or disposition.
