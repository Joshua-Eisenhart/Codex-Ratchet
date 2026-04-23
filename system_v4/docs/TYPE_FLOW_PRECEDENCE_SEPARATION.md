# [Controller-safe] Type / Flow / Precedence Separation

**Status:** Anti-collapse separation surface.  
**Purpose:** Keep engine family, flow direction, and precedence from being flattened into one sign-like distinction.

---

## Distinct Objects

| Object | What it is | What it is not | Evidence class |
|---|---|---|---|
| `engine_type` | Type 1 vs Type 2 engine-family split | not induction/deduction; not Axis 6; not heating/cooling | owner grammar + runtime family surfaces |
| `flow_direction` | induction vs deduction candidate flow-direction split | not type; not Axis 6 up/down | path/order probes, not static state |
| `precedence` | what operates on what first; ordered composition sidedness | not induction/deduction; not type | operator-order / composition evidence |
| `loop_role` | heating vs cooling role on a loop | not type by itself; not precedence | owner grammar, later constrained runtime |
| `chirality_or_flux_family` | in/out or left/right-oriented family handle | not automatically type; not automatically induction/deduction | geometry/process evidence |

---

## Hard Bans

1. Do not say:
- `Type 1 = deductive`
- `Type 2 = inductive`

2. Do not say:
- `Axis 6 = induction/deduction`

3. Do not say:
- `heating/cooling = engine type`

4. Do not say:
- `up/down = type`

5. Do not say:
- `clockwise/counterclockwise = Axis 6`
unless the evidence is specifically about precedence and not process direction.

---

## Historical Violations This Document Is Meant To Stop

The repo recently contained exactly these collapses:

- `current_engine_type` described as `Deductive or Inductive`
- Weyl chirality labeled as `Type 1 Deductive / Type 2 Inductive`

Those were patched, but this document exists so future runtime/docs do not drift back into the same collapse.

---

## Safe Wording Pattern

Use:

- `engine type`
- `flow direction candidate`
- `precedence / composition sidedness`
- `loop heating/cooling role`
- `chirality/flux candidate`

Do **not** use one of these labels as shorthand for another.
