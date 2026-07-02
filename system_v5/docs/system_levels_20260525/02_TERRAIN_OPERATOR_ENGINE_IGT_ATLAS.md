# Terrain Operator Engine IGT Atlas

Status: repair atlas, not final engine closure and not source-conformant Fe
closure.

## 1. Separate The Objects

Several neighboring objects were being collapsed:

```text
terrain family       != local judging/operator family
terrain generator    != ordered token
loop field           != engine type
stage placement      != operator substage
IGT result grammar   != manifold proof
I Ching schedule tag != ontology
Axis0 readout        != terrain square
```

The engine can only be geometric when the local carrier and maps are geometric.
The substages are not automatically manifold geometry because their names are
operator slots. They become geometric only if each operator slot is realized as
a finite PEPS3D-carried local cell, tensor, or channel action on the spinor
network.

## 2. Terrain Families

The current four terrain families are best read as local generator/channel
families after the spinor/Hopf/Weyl carrier is active:

```text
Se = outward/open dissipative family
Ne = circulation/noncommuting Hamiltonian family
Ni = inward/open dissipative family
Si = stratified/commuting Hamiltonian family
```

The source-native square that must not be erased is:

```text
A0+ / N-side = {Ne, Ni}
A0- / S-side = {Se, Si}
```

That is not final Axis0. It is a terrain-square polarity that later Axis0
readouts may need to respect or explain.

## 3. Loop And Sheet Placements

The terrain family is not the placement. A placement includes:

```text
sheet s in {L, R}
loop ell in {fiber, base}
terrain tau in {Se, Ne, Ni, Si}
generator X_(tau,s)
loop field Y_ell
source token and sign
```

Counts:

```text
4 terrain families
x 2 Weyl sheets
x 2 loop fields
= 16 terrain placements
```

The 16 placements are real candidate dynamical objects only after the carrier,
loop field, and sheet maps are explicit.

## 4. Operators

The four operator families are local action families, not terrain labels:

```text
Ti = introverted thinking family, usually z/dephasing or projective distinction
Te = extraverted thinking family, usually x/dephasing or externalized split
Fi = introverted feeling family, usually rotation/Hamiltonian family
Fe = extraverted feeling family, source/runtime mismatch currently open
```

Do not lock this paragraph as final operator physics. The current source and
runtime surfaces still disagree around `Fe`. Until that mismatch is fixed, the
safe claim is:

```text
the four operator slots exist as an engine grammar target
the exact Fe channel law is not closed
```

## 5. Ordered Tokens Versus Placements

There are at least two nearby 16-count objects:

```text
16 ordered tokens:
  terrain/topology family x judging/operator family x precedence

16 terrain placements:
  terrain family x Weyl sheet x loop field
```

They are related, but they are not identical. A sim must say which object it is
testing. A schedule that proves row-count preservation for tokens does not prove
placement law, and a placement scout does not prove all ordered-token dynamics.

## 6. Macro Stages And Substages

The current runtime scaffold target is:

```text
2 engine types
x 8 macro stages per engine
x 4 operator substages per macro stage
= 64 substages total
```

But the current repair audit says:

```text
16 macro-stage sites + 4 operator rows per site
!= 64 manifold cells by itself
```

For a substage to count as geometric, it must provide:

```text
cell key:
  (engine_type, macro_stage, loop_field, terrain, operator_slot)

cell carrier:
  finite PEPS3D site/bond/face/cell slice

cell state:
  spinor/Hopf/Weyl local state or projection from richer carrier

cell action:
  local operator/channel/tensor update

cell evidence:
  F01 finite witness
  N01 order witness
  negative/control
  result path or blocked reason
```

## 7. IGT Layer

IGT is a stage/result grammar and strategy surface. It can guide which stage
rows are expected, how signs and precedence should be interpreted, and which
win/lose or strategy distinctions matter. It does not prove the geometry.

Safe:

```text
IGT names stage grammar, result classes, and strategic order.
IGT can propose schedule constraints for the engine.
```

Unsafe:

```text
IGT label = admitted operator
IGT stage = geometric manifold cell
IGT result = Axis0 or flux proof
```

## 8. I Ching / 64-Schedule Layer

The 64 schedule surface has multiple meanings:

```text
runtime 64:
  2 engines x 8 macro stages x 4 operator slots

chart atlas 64:
  8 terrains x 8 signed operators

hexagram tag 64:
  optional symbolic index family
```

Those are schedule/index surfaces, not ontology. A hexagram or row number is
useful only if it indexes a finite cell/action already defined by the lower
manifold carrier.

## 9. What A Correct Engine Sim Must Show

A future engine sim should ratchet in this order:

```text
finite effect/probe identity
finite PEPS3D spinor-network carrier
spinor/Hopf/Weyl local states
terrain generator + loop-field placement
operator family action on the same carrier
macro-stage schedule preservation
substage cell action
controls for collapse, commuting-only, wrong sheet, erased Hopf, erased PEPS3D
```

Only after that can the engine be treated as more than a source-conformant
schedule scaffold.

## 10. Current Claim Ceiling

Current formal scouts support bounded pieces:

```text
finite effect/SIC/Weyl substrate scout: formal_scout only
explicit spinor 8/16/32/64 rows: formal_scout only
64-substage grammar row: formal_scout only
MPS/PEPS/PEPS3D portability rows: formal_scout only
IJK flux row: formal_scout only
```

None of those, alone or in suite, admits final manifold closure, final flux,
Axis0, Xi/Phi0, Holodeck proof, attractor-basin convergence, or physics.

