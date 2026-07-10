# PySINDy / PyKoopman Tool Status

**Date:** 2026-07-09
**Status:** PySINDy admitted for its bounded affine-generator function surface;
PyKoopman admitted only for `Identity + EDMD` with explicit affine
augmentation; full PyKoopman distribution remains quarantined.

## Source And Runtime

Pinned upstream source checkouts:

| Tool | Tag | Commit | Checkout |
|---|---|---|---|
| PySINDy | `v2.1.0` | `1edf31260fc000692776b1f4259877e8b85e56e5` | `/Users/joshuaeisenhart/GitHub/pysindy` |
| PyKoopman | `v1.2.1` | `61d24f765cd4799a3c84413950f43282977fa0e2` | `/Users/joshuaeisenhart/GitHub/pykoopman` |

The source checkouts are clean, detached at their release tags, and remain
third-party source repositories. The Codex-Ratchet domain work belongs in
`system_v7/sims`; no new project repository is justified.

Canonical runtime:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
PySINDy 2.1.0
PyKoopman 1.2.1
NumPy 2.3.4
SciPy 1.17.1
scikit-learn 1.8.0
PyTorch 2.11.0
```

## Upstream Tests

PySINDy uses an isolated Python 3.13 test environment because upstream declares
`pytest<8` and uses `pytest-lazy-fixture`; its test collection also imports JAX
and optional CVXPY optimizers. Six selected upstream core/discrete/polynomial
tests pass.

PyKoopman uses an isolated Python 3.11 environment matching the old release
stack. Five selected upstream Koopman/EDMD tests pass. The isolated minimal
environment intentionally omits documentation, development, and unused neural
packages, so `uv pip check` reports those package-metadata requirements rather
than pretending the complete distribution is clean.

Machine-readable environment and test details:

```text
system_v5/ops/tooling/compatibility/pysindy_pykoopman_20260709.json
```

## Function Receipts

PySINDy capability:

```text
system_v4/probes/sim_pysindy_capability.py
system_v4/probes/a2_state/sim_results/pysindy_capability_results.json
```

`SINDy + PolynomialLibrary(degree=1) + STLSQ` recovers an affine vector field,
predicts held-out derivatives at machine precision, rejects shuffled
derivatives, and preserves a zero-generator boundary.

PySINDy 2.1 API cautions:

- discrete maps use `DiscreteSINDy` with explicit `x_next=`; the older
  `SINDy(discrete_time=True)` form is not valid;
- multi-trajectory data are lists, not `multiple_trajectories=True`;
- `DiscreteSINDy.score` should receive `x_next=` by keyword because the third
  positional argument is control input;
- coefficient width must be checked against `len(get_feature_names())`, not
  only `ParameterizedLibrary.n_output_features_`;
- absolute held-out error must be gated in addition to a shuffled control.

That last point matters to existing evidence. The current trajectory-window
arbiter result has poor absolute mean R2 even though its catastrophic shuffle
is worse. The new perfect affine result uses analytic `x_dot`; it is a clean
function receipt, not evidence that noisy trajectory perception is solved.

A fresh full v7 harness rerun is mechanically green at `123 pass / 0 fail / 0
skip`, but it propagates that poor absolute fit into the evidence envelope:
`formation_loss_sum = 43.546185436758485`. The old low formation-loss reading
is not current evidence. Harness green means the measurement pipeline ran, not
that the perception/object criterion succeeded.

PyKoopman capability:

```text
system_v4/probes/sim_pykoopman_capability.py
system_v4/probes/a2_state/sim_results/pykoopman_capability_results.json
```

`Koopman + Identity + EDMD` recovers an affine discrete map at machine
precision when the constant coordinate is explicit. Erasing that coordinate
is a failing control. This is the only currently admitted PyKoopman surface.

## Quarantine

The canonical PyKoopman package violates its declared old-version constraints.
Its `Polynomial` observable also checks scikit-learn's removed
`n_input_features_` attribute and is blocked under the modern canonical stack.
Top-level import eagerly reaches `NNDMD`, Torch, and Lightning and emits a
deprecated `pkg_resources` warning.

Therefore:

- do not downgrade the canonical stack;
- do not use `Polynomial` in canonical PyKoopman runs;
- do not claim NNDMD or neural-path support;
- use explicit affine augmentation with `Identity + EDMD`;
- keep the exact dependency environment only for upstream compatibility tests.

## Integrated Use

The first load-bearing combined receipt is:

```text
system_v7/sims/stage16x4_system_id_instrument_v0/
```

PySINDy reconstructs the continuous terrain generators. PyKoopman learns the
discrete signed beat maps from those reconstructed flows. Held-out targets come
from the exact house GKSL/channel implementation. Both candidate four-cell
cycle orientations pass all local prediction and destructive-control gates.

This does not admit the four-substage engine interpretation. Four cells, cycle
orientation, canonical-first rotation, source slots, exact derivative access,
and one finite house-map parameterization remain premises. Independent
geometry-first and entropy-first survivor ratchets are still required.
