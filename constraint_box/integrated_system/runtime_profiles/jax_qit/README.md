# JAX/QIT runtime profile

This is the optional, project-neutral numerical profile for ConstraintBox. It
is an external runtime profile: it is installed beside the product and is
never imported into the Light controller or copied into the ZIP as a virtual
environment.

The profile supplies one pinned Python environment for batched JAX work,
quantum-information micro-engines, tensor-network operations, Lie/spinor
support, finite topology, and deterministic solver controls. It does not
contain CB source, provider code, model credentials, Julia, PyTorch, or any
project checkout.

## Install after extracting the product

From this directory:

```text
python3 bootstrap_jax_qit.py plan
python3 bootstrap_jax_qit.py install
python3 bootstrap_jax_qit.py probe
```

The default target is `${XDG_DATA_HOME:-~/.local/share}/jax-qit-stack`. Set
`CB_JAX_QIT_ROOT` or pass `--target` to choose another location. The installer
uses `uv` when available and otherwise uses the selected Python's `venv` and
`pip`; both paths install exactly `requirements.lock`.

The target receives:

- `requirements.in` and `requirements.lock`;
- the probe source;
- `PROBE_RECEIPT.json` after a successful probe; and
- `STACK_MANIFEST.json` containing the target, lock digests, runtime identity,
  and claim ceiling.

An existing non-profile directory is refused rather than overwritten. A
previously marked profile may be reinstalled. `probe` never installs or
upgrades anything. A normal probe of an unowned existing directory returns
`HOLD_TARGET_NOT_OWNED` without writing to it. If an already-installed,
external environment is intentionally selected, use the explicit adoption
path:

```text
python3 bootstrap_jax_qit.py probe --adopt-existing --target /path/to/env
```

Adoption is still not an install operation. It first inspects the target
interpreter's installed distribution metadata and requires every exact pin in
`requirements.lock` to match, then runs all 12 API probes. Only after both
checks pass does it add the profile's declarative files, state marker, receipt,
and manifest.

## Claim ceiling

`PASS` means the named APIs ran in this local profile and their negative or
invariant checks passed. It does not establish a physical manifold, quantum
advantage, a production simulation engine, portability to every platform, or
semantic authority over CB. CB Light remains the deterministic controller;
this profile is an external worker runtime.
