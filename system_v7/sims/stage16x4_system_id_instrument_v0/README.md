# Stage 16 x 4 System-ID Instrument v0

This packet executes the next bounded rung after
`four_substages_dual_product_v0`.

It parses the 16 signed source macro slots, rotates each of the two conditional
product-square orientations so the slot's canonical operator is first, and
executes all four beats under the slot's one inherited Axis-6 composition-order
sign.

The two external system-identification tools have different jobs:

- PySINDy fits each continuous terrain generator from exact held-out derivative
  data and reconstructs its affine time-one flow.
- PyKoopman `Identity + EDMD` fits each discrete signed beat map with an explicit
  affine bias coordinate, then rolls the four learned maps forward on held-out
  states.

Ground-truth held-out transitions always come from the existing exact house
GKSL/channel implementation. The learned PySINDy flow generates the PyKoopman
training transitions, so both tools are load-bearing in the prediction path.

Controls remove or duplicate every beat, reverse the candidate cycle, flip the
shared sign, erase terrain action, erase operator action, corrupt the source
table in memory, and verify that an identity boundary is order insensitive.

A post-run audit extension also clusters the exact map signatures after
operator, terrain, and joint erasure. This control was added after the first
green run to test a specific identity-leak confound; it is not represented as
preregistered evidence.

## Ceiling

This is a fenced `scratch_diagnostic`. The four cells and their cycle remain a
conditional input, and canonical-first rotation is a candidate stage
architecture. A green run can show that a concrete 16 x 4 schedule executes,
is identifiable, and survives local destructive controls under one finite
parameterization. It cannot show that dual ratcheting derived four substages,
that the engines perform business/object work, or that Axis0, perception,
personality, manifold, entropy, and physics claims are earned.

Run with the canonical simulation interpreter:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/stage16x4_system_id_instrument_v0/stage16x4_system_id_instrument_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/stage16x4_system_id_instrument_v0/validate_stage16x4_system_id_instrument_v0.py
```

Or run the same deterministic gate graph through Leviathan FlowMind:

```bash
lev exec "verify the stage16x4 system-ID packet" --flow system_v7/sims/stage16x4_system_id_instrument_v0/lev_verify.flow.yaml
```
