# CB Light contract — first layer

Light is a simplified reflection of the advanced model, not a second model.
Same laws. Smaller carrier.

## Live object

```text
F starts as the time-first seed
  S0 = {z_left, z_right} under Z (not scalar 0)
  W ∈ {2, 4, 8}
  K = log2 W ∈ {1, 2, 3}     Hartley / Rényi-0 only
  ΔK = (1, 1)                the one time gradient

  L = bind ∘ open
  R = open ∘ bind
  L(S0) ≠ R(S0)              proto-chiral; not painted chirality
```

After probes P and constraints C:

```text
X_C = (S_C / ~_P, μ_C)
```

Fuzz = pairs P did not split. Geometry = that relation, not a metric.
Three capacities stay typed: support / fibre / record. Do not sum them.

## Three nouns

| Noun | Meaning |
|------|---------|
| Probe | named observation, finite domain; split or fail. No split ≠ identity |
| Constraint | finite predicate. SAT / UNSAT / UNKNOWN. UNKNOWN ≠ UNSAT |
| Basin | static leftover of S_C. Not an attractor. Not an engine |

## Light verbs

1. Validate the form (schema). Extra fields → refuse.
2. Recompute K and ΔK. Mismatch → refuse.
3. Refuse collapsed open/bind.
4. Dualsolve. Keep disagreement.
5. Record append-only.
6. Quotient / components only from bound observation rows.

ZIP / waves / councils are how models fill forms. They are not a second geometry.

## Light must not

- treat solver-chosen `obs__*` as measured probes
- call a static component an attractor or engine
- import Heavy, FEP, personality, or spinor as Light geometry
- rewrite the first layer from a Heavy receipt

Heavy deforms this F and returns observations. Light asks whether K or the quotient moved.

## How to run the first verb

```text
sh seed-check
```

No venv required. Stdlib + the seed + `manifold_foundation`.
`ADMIT` means the seed still has a positive gradient and two uncollapsed hands.
It does not mean contained Light, chirality, or promotion.

Solver SAT is `finite_probe_assignment_feasibility.v1`.
A quotient is `bound_observation_quotient.v1` and needs complete bound rows.
