# Free-Length Dual-Ratchet Schedule Selector v0

Status: `scratch_diagnostic`; scientific red; no promotion, admission, or
stage movement allowed.

## Question

The source defines 16 macro slots and provisionally expands every slot across
the four channels `Ti`, `Te`, `Fi`, and `Fe` at one shared Axis-6 sign. This
packet asks whether a primitive four-beat cycle wins when repetition, omission,
and lengths `2..8` are allowed to compete under frozen geometry and Umegaki
objectives.

It does not ask whether the four source channel names exist. It attacks the
stronger claim that dual ratcheting selects four beats and a unique order.

## Frozen Search

- 87,376 rooted words;
- 11,586 oriented necklaces after quotienting cyclic rotation only;
- reversal remains distinct;
- every distinct cyclic phase is evaluated;
- repeated and omitted operators remain legal;
- four-at-length-four receives no special score;
- 36 scenarios per engine type;
- fixed-total-exposure main comparison plus destructive controls;
- JAX `jit`/`vmap`, `jax.scipy.linalg.expm`, and Lineax are load-bearing.

The preregistration and exact hashes are in `spec.json`, `spec.sha256`, and
`preregistration_receipt.json`.

## Run And Validate

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/free_length_dual_ratchet_schedule_selector_v0/free_length_dual_ratchet_schedule_selector_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/free_length_dual_ratchet_schedule_selector_v0/validate_free_length_dual_ratchet_schedule_selector_v0.py
```

Mutation tests:

```text
cd system_v7/sims/free_length_dual_ratchet_schedule_selector_v0
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m unittest -v test_validate_free_length_dual_ratchet_schedule_selector_v0.py
```

The independent validator does not import the producer. It reconstructs the
candidate catalog, decodes and hashes raw score arrays, recomputes winners,
controls, physical preconditions, and the scientific verdict, and binds the
summary to frozen source hashes. Eleven mutation tests reject altered sources,
catalogs, arrays, shapes, winners, controls, verdicts, types, duplicate keys,
nonfinite JSON, and removed blocked consumers.

## Claim Ceiling

The strongest permitted positive result was
`four_selected_under_declared_source_operator_family_only`. The observed result
is red. This packet cannot establish a universal four-operator alphabet,
canonical order, Type-1/Type-2 engine, Axis0, perception, objects, MMMs,
ontologies, mesh behavior, or physics.
