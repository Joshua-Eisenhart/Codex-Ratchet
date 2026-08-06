# Mini-Lev provider runtime

This is the runtime boundary for CB's actual proposal loop.  It is separate
from both the contained-core verification and the external simulation estate.

## What is contained

`constraintbox._provider_harness` is carried in the CB source package.  It
contains the receipt types, local-process, OpenRouter, and NVIDIA provider adapters, the
executor/notary split, per-producer signing, and the deterministic provider
gate.  `constraintbox.agentrun` imports that package directly; it does not
import `scripts.llm_harness` from a surrounding Ratchet checkout.

The package includes no credential, no model runtime, no hidden host path, and
no writable default under a user's home directory.

## One explicit runtime directory

Before running a Mini-Lev proposal flow, select a writable absolute directory:

```bash
export CONSTRAINTBOX_RUNTIME_DIR=/absolute/path/to/constraintbox-runtime
```

CB creates its provider-notary key files below that directory with restrictive
permissions when the platform permits.  The keys are not placed in the ZIP,
receipts, prompt, or simulation estate.  You can instead supply an absolute
`CONSTRAINTBOX_PROVIDER_KEY_FILE` for the default producer or an absolute
`CONSTRAINTBOX_PROVIDER_KEY_DIR` for per-producer keys.

If none of those locations (or an explicit provider key environment value) is
configured, notarization fails closed and the proposal flow becomes `PARKED`.
It does not fall back to `~`, a source checkout, or a different Python
installation.

## Current proposal path

The public command remains controller-owned:

```bash
PYTHONPATH=src python -m constraintbox run \
  --box-run-dir /absolute/verified-box-run \
  --run-dir /absolute/new-agent-run
```

It first verifies the frozen box input, uses the compiled MMM text and digest
in the untrusted proposal prompt, and then runs the fixed
`topology-preflight -> proposal-observation -> proposal-gate -> ClaimGate`
Mini-Lev graph.  The provider can only supply candidate bytes.  Rustworkx,
the controller, SMT checks, the lease lifecycle, and ClaimGate select all
transitions and terminals.

The public proposal route is chosen only from CB's static controller registry.
There is no request field, model output, or `constraintbox run` flag that can
select a provider or a model. The deployer may select an exact registered route
before startup:

```bash
# Default: controller-owned local tool route; requires `codex` on PATH.
unset CONSTRAINTBOX_PROPOSAL_PROVIDER

# Explicit remote routes. Each has a fixed model in CB source.
export CONSTRAINTBOX_PROPOSAL_PROVIDER=openrouter
export OPENROUTER_API_KEY=...

export CONSTRAINTBOX_PROPOSAL_PROVIDER=nvidia
export NVIDIA_API_KEY=...
```

The fixed remote models are `openrouter/free` and
`nvidia/nemotron-3-nano-30b-a3b`. CB records the static policy digest, route,
requested model, and non-secret credential configuration in the proposal-flow
binding. It uses bounded standard-library HTTPS transport; credentials never
enter prompts, receipts, or the ZIP. An explicit remote route with a missing
key becomes `PARKED`; CB does not fall back to the local Codex route or silently
change provider. The routes are offline-tested adapters, not evidence that a
live provider, free quota, or a particular upstream model is available.

## What the contained test proves

`tests/test_contained_provider_harness.py` runs the public `run_agent()` entry
through a real local subprocess, contained provider/notary/gate, controller,
SMT refusal, and bounded retry path. It also proves that a selected remote
route without its key parks before any local-provider fallback. The separate
policy test exercises both remote adapters against an offline transport fixture.
None of this is a live-model, provider-availability, engine-readiness, release,
promotion, or scientific claim.
