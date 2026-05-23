# Claude Axis Expansion Audit

Status: audited against source packets and executable finite checks.

Audited object: pasted Claude expansion beginning "Axes 0-6 - deep expansion
with math substance".

Audit receipt:

```text
system_v5/ops/axis_audits/axes_deep_math_audit_20260522.json
```

Audit script:

```text
system_v5/ops/axis_audits/audit_axes_deep_math_20260522.py
```

## Verdict

Classification:

```text
audit_pass_with_correction
```

The pasted expansion is materially stronger than the previous shallow axis
layout: it restores entropy math, frame laws, path equations, operator channel
forms, Liouville action, gap formulas, and projection identities.

However, it contains one hard source error:

```text
Claude's A_0 x A_2 derivation table inverts the direct-frame rows.
```

## Finding 1: A0 x A2 Direct-Frame Rows Are Inverted

Terminology note:

```text
"upper" and "lower" are source/Bloch-chart aliases:

A0+ / N-side = eta < pi/4 = r_z > 0
A0- / S-side = eta > pi/4 = r_z < 0

They are not model-native terrain names and are not Axis 6 up/down.
```

Source Axis 0 sets:

```text
A0+ / N-side / white = {Ne, Ni}
A0- / S-side / black = {Se, Si}
```

Source Axis 2 sets:

```text
direct     = {Se, Ne}
conjugated = {Ni, Si}
```

Set intersections:

```text
A0+ / N-side + direct      -> Ne
A0+ / N-side + conjugated  -> Ni
A0- / S-side + direct      -> Se
A0- / S-side + conjugated  -> Si
```

Claude pasted:

```text
A0+ + direct -> Se
A0+ + conjugated -> Ni
A0- + direct -> Ne
A0- + conjugated -> Si
```

Rows 1 and 3 fail. Rows 2 and 4 survive.

Corrected table:

| A0 region | A2 frame | Source-correct topology | A1 branch |
|---|---|---|---|
| A0+ / N-side | direct | `Ne` | `Ne/Si` |
| A0+ / N-side | conjugated | `Ni` | `Se/Ni` |
| A0- / S-side | direct | `Se` | `Se/Ni` |
| A0- / S-side | conjugated | `Si` | `Ne/Si` |

The deep axis packet has been patched with this correction:

```text
system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md
```

## Finding 2: Projection Identities Survive

Executable check confirms:

```text
A1 x A2 x A5 x A6 -> 16 unique ordered tokens
A3 x A4 x A5 x A6 -> 8 paired loop-placement signatures
terrain x sheet x path -> separate 16 terrain placements
```

This part of Claude's corrected projection is sound.

## Finding 3: Axis 0 Entropy Math Survives

Executable check confirms:

```text
b_0 = sign(cos(2 eta))
S(rho_bar(pi/4)) = log 2
dS/deta > 0 before pi/4
dS/deta < 0 after pi/4
```

with:

```text
dS/deta = -sin(2 eta) log(tan^2 eta)
```

## Finding 4: Axis 3 Path Math Survives

Executable check confirms:

```text
fiber density is stationary
lifted-base density traverses
lifted-base path is horizontal: A_Hopf(dot gamma_base) = 0
```

This supports the source anchor:

```text
A3 = fiber versus lifted-base path class
```

not loose inner/outer.

## Finding 5: Axis 5 Operator Family Math Survives

Executable check confirms:

```text
Ti contracts D_z
Te contracts D_x
Fi preserves Bloch norm
Fe preserves Bloch norm
```

So the safe Axis 5 anchor remains:

```text
{Ti, Te} dephasing/pinching
versus
{Fi, Fe} rotation/unitary
```

Gradient/spectral language remains explanatory only unless it reduces to these
maps.

## Finding 6: Axis 6 Left/Right Gap Math Survives

Executable check confirms:

```text
gap_sigma_x(rho) = sqrt(2) sqrt(y^2 + z^2)
gap_sigma_z(rho) = sqrt(2) sqrt(x^2 + y^2)
```

So the two-layer Axis 6 audit remains required:

```text
axis6_token_precedence
axis6_action_side
closure_type
```

Token precedence and left/right primitive action are related but not
automatically identical.

## Finding 7: A6 XOR Uses Chart Role, Not Raw Path

The source-aligned engine smoke found an exact failure mode:

```text
raw fiber/base XOR:
  Type 1 passes
  Type 2 fails on every row

chart inner/outer XOR:
  Type 1 passes
  Type 2 passes
```

Receipt:

```text
system_v5/ops/axis_audits/axis_corrected_qit_engine_smoke_20260522.json
```

Reason:

```text
Type 1: outer = lifted base, inner = fiber
Type 2: outer = fiber, inner = lifted base
```

So the XOR relation:

```text
b_6 = - b_0 b_3
```

must read `b_3` as the chart-role bit:

```text
outer -> +1
inner -> -1
```

not the raw geometry path bit. The runtime receipt must keep both:

```text
A3_geometry_path = fiber | lifted_base
A3_chart_role    = inner | outer
```

This does not demote the fiber/base geometry. It prevents the chart-role sign
law from being applied to the wrong A3 readout.

## What The Script Tests

The script tests:

```text
Axis 0 entropy and b0 sign
A0 x A2 source intersections against Claude's pasted table
Axis 3 fiber/base path behavior and horizontal condition
Axis 5 operator family invariants
Axis 6 noncommutation gap formulas
16-token and 16-terrain-placement projection identities
```

It writes:

```text
classification = audit_pass_with_correction
TOOL_MANIFEST = python_stdlib with reason
TOOL_INTEGRATION_DEPTH = supportive
```

## Bottom Line

Keep from Claude:

```text
deep equation-rich axis expansion
projection identity correction
dual-layer Axis 6 audit requirement
gradient/spectral admission caution
```

Correct from Claude:

```text
A0 x A2 derivation table
```

The source-correct derivation is:

```text
A0+ + direct = Ne
A0+ + conjugated = Ni
A0- + direct = Se
A0- + conjugated = Si
```
