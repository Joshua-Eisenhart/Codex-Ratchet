---
name: cb-capability-probe-map-wave
description: Compose the existing public structured open/bind exact and dual probes with the existing finite path-mass operation and exact replay, emitting an inactive capability map.
---

# CB capability/probe-map candidate wave

This directory is an authored `NEW_CANDIDATE`, not an active wave. It binds
public operations already present in the repository; it does not add a new
mathematical operation, edit an active manifest, or change a launcher.

## Invocation

From the repository root, declare the external interpreter explicitly:

```bash
python3 constraint_box/integrated_system/skills/cb-capability-probe-map-wave/scripts/run_probe_map.py \
  --root "$PWD" \
  --jax-python /absolute/path/to/jax-qit-stack/bin/python3 \
  --out /absolute/path/to/candidate.receipt.json
```

The runner uses the public `structured_open_bind_probe.py` script for exact
and dual engines. The dual process is launched by the declared external JAX
interpreter with `-I`; the controller never imports JAX for that child. It
uses the public `run_constraint_path_mass.py` wrapper, requiring its declared
external JAX crossing, then calls that same wrapper's `--replay` path. Source,
fixture, interpreter, API-symbol, stdout/stderr, child result, and replay
digests remain in the receipt.

Before any child call it binds the controller executable and prefix, Z3 and
CVC5 versions, and the declared external JAX interpreter's executable,
prefix, JAX/JAXLIB, Z3, and CVC5 versions. Each identity has a visible
`-I` invocation, source digest, and minimal environment projection. The
external runtime is accepted only when its observed `sys.prefix` differs from
the controller prefix; a path alias alone cannot bypass that check. Child
source and fixture hashes are checked against those bound rows before a PASS
is possible.
The public path-mass wrapper is pinned by its registry digest and is checked
both at bind time and in the child receipt; wrapper drift refuses the
candidate. A malformed or null path-mass request is a typed `HOLD`, never an
implicit successful replay.

## Bound object and controls

The finite object is the supplied structured fixture and the contained
Mini-Lev reference-policy fixture. Positive child evidence is required for:

1. `structured_open_bind_probe.evaluate(..., engine="exact")`;
2. `structured_open_bind_probe.evaluate(..., engine="dual")` under the
   declared external JAX interpreter; and
3. `constraint_path_mass.v1` plus `replay_receipt` with the exact stored
   request and source/fixture digests.

The runner also records exactly six reason-specific controls: structured
missing observation, structured promotion true, path missing row, unknown
probe, foreign policy, and tampered replay. Missing, duplicate, or unexpected
IDs hold or refuse the candidate; a partial matrix cannot become `all_pass`.
These controls are expected refusals or holds and do not write authority
state. The optional 6,144-row manifold campaign is deliberately not required
and is recorded as an unused scratch surface; no manifold claim is made.

## Terminals and claim ceiling

`PASS` means the finite child calls and exact replay passed on this invocation;
`HOLD` means required external runtime or evidence was unavailable or
disagreed; `REFUSE` means a declared source, input, or receipt boundary was
invalid. Every terminal keeps `candidate_state: NEW_CANDIDATE`,
`activated: false`, and `promotion_allowed: false`.

The receipt proves only the bounded call/API observations and deterministic
replay. It does not prove a general capability, a manifold, an attractor
basin, chirality, physical time, provider dispatch, portability, or activation.
