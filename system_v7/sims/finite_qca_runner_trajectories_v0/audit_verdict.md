# audit_verdict — finite_qca_runner_trajectories_v0

```yaml
classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
does_not_self_upgrade: true
ladder_reached: passes local rerun
box_viii: OPEN -- no multi-model fleet audit was run
```

## What this sim is

Finite reversible binary-ring QCA diagnostic on `N=6`, `alphabet={0,1}`. It builds exact finite transition tables, explicit inverse tables, finite trajectories, cycle/absorbing-set summaries, and a GNVW-style directional index.

The index is computed from conjugated coordinate-observable support: `e_i(tau)=tau_i` is conjugated to `e_i o F^{-1}`, and support is found by exhaustive finite differences of `F^{-1}(y)_i` with respect to output cells `y_j`. The shift label is not read by the index routine.

## Equivalence relation

`tau ~_support tau'` iff the support-flow index across cut `2|3` is equal: `ind_q(tau)=r_R-r_L`. Separately, `tau ~_cycle tau'` iff the finite transition graph cycle-length multisets match.

## Local results

The local rerun passes the required could-fail discriminators:

| rule | computed index units `log(q)` | required |
|---|---:|---:|
| `identity` | `0` | `0` |
| `right_shift` | `+1` | `+1` |
| `left_shift` | `-1` | `-1` |
| `finite_depth_local_circuit` | `0` | `0` |

Every rule has an explicit inverse that composes both ways to identity on all `2^6` states. Absorbing sets are reported from the cycle decomposition of the actual transition table; for a reversible finite map, each cycle is a closed absorbing class.

## Boundary

This earns only a finite scratch witness that the runner derives the support-flow index from conjugated support and can separate the four required controls. It does not earn an infinite-chain GNVW theorem, a canonical QCA classification, or promotion beyond `scratch_diagnostic`.
