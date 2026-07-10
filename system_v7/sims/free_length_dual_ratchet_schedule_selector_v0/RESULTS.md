# Free-Length Dual-Ratchet Schedule Selector v0 Results

Status: deterministic local rerun and independent validation pass; scientific
selection gate fails.

## Verdict

```text
RED_no_shared_primitive_length4_cycle_meets_preregistered_cross_type_frequency_uniqueness_margin_and_control_gate
```

No primitive length-four cycle using all four operators exactly once qualifies
for either engine type. The observed aggregate winners are repeated or omitted
operator cycles of lengths two and three:

- Type 1: `Fi>Fi`, `Te>Fi`, and `Ti>Fi>Fi` across the scenario grid;
- Type 2: `Fi>Fi` throughout the main grid;
- qualifying primitive length-four winner counts: empty for both types;
- shared qualifying cycle IDs: empty;
- required count: 35 of 36 scenarios per engine.

All physical preconditions and preregistered destructive controls pass. That
means the red result is not caused by a dead carrier or missing control flip.
It means the declared objectives do not select four.

## Reproducibility

The local rerun is byte-identical to the retained artifacts:

```text
candidate_catalog.json  19480a92baafee069f66928fde10f2fa26309742ddd8d9ad29839c85950c4163
raw_scores.json          8193955d34153c1625876bfd9777d57cc0b0f6e5fd8f9a49459bb87965186300
results.json             f14cca8e5007367c32bf0168ccdb177da1c349b0e868ff788bdc8b5eee364aac
```

Independent validation passes all 10 semantic groups over all 11,586
candidates and both engines. Its 11 mutation tests pass.

## Post-Hoc Length-Bias Audit

An external Fable review noted that the length-2-to-length-4 MDL gap is `0.006`,
slightly larger than the required winner margin `0.005`. A non-preregistered
reanalysis therefore removed the MDL penalty directly from the retained raw
geometry and entropy arrays. Length-four repeated-operator cycles sometimes
win, but no primitive length-four cycle using all four operators exactly once
qualifies for either engine.

The existing fixed-per-beat-exposure control was also ranked independently.
Its winners are a repeated length-six Type-1 cycle and a repeated length-five
Type-2 cycle; again, no qualifying all-four-once cycle appears.

This post-hoc result cannot promote or replace the preregistered verdict. It
does show that the red survives the two obvious length-coupled scoring terms.

## Meaning For 16 x 4

The source-faithful structural schedule still exists: 16 source slots, each
expanded across four named source channels at one shared Axis-6 sign. This
result blocks the stronger statement that the multiplier four or a unique
four-beat order emerged from the tested dual-ratchet objectives.

The correct current label is `source-defined 16 x 4 candidate, four not yet
earned`.
