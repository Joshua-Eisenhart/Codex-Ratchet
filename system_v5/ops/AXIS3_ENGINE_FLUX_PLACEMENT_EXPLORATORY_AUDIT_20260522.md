# Axis 3 / Engine Type / Flux Placement Exploratory Audit

**Created:** 2026-05-22
**Status:** exploratory audit; not canon; not source authority; no runtime promotion

## Non-Admission Rule

This packet audits a live hypothesis:

```text
flux might live at the manifold layer, while A3/A4/A5/A6 generate the
engine-internal 16 placements.
```

It does not canonize that hypothesis.

It does not rename axes.

It does not promote flux to a root constraint.

It preserves source anchors and separates them from possible repairs.

## Source Anchors Read For This Audit

Primary source slices:

```text
READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md
READ ONLY Reference Docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP copy.md
READ ONLY Reference Docs/Weyl Flux.md
READ ONLY Reference Docs/terrain math.md
READ ONLY Reference Docs/Formal constraints and geometry .md
docs/17_actual_lego_registry.md
```

Strong source anchors found:

| Object | Current strongest anchor |
|---|---|
| `Axis 3` | fiber-loop versus lifted-base-loop path class |
| `Axis 3` chart correlation | inner token set versus outer token set |
| `Axis 4` | loop-order family: `U o E o U o E` versus `E o U o E o U`, currently correlated with `FeTi` versus `TeFi` |
| `Axis 5` | operator-family split: dephasing `{Ti, Te}` versus rotation `{Fi, Fe}` |
| `Axis 6` | up/down token position; older/formal math also demands left/right action audit |
| flux | open derived candidate family, not primitive and not currently admitted as an axis |
| engine type | arrangement of sheet/path/order/token tables; not reducible to one pasted name without a matrix check |

## Immediate Verdict On The Pasted Hypothesis

The pasted hypothesis has useful direction but overstates two things.

### Partly Right

```text
A3 is not chirality.
A3 is not flux.
Flux should not be stuffed into Axis 6.
Flux is better treated outside the four-operator math until tested.
```

This agrees with the atlas line:

```text
Axis 3 = fiber versus lifted-base loop class
```

and with the flux packet:

```text
flux is open / derived / candidate-family work
```

### Too Strong

The pasted hypothesis says:

```text
flux is a manifold-level global property / pre-axial constraint
```

That is not source-admitted.

The source flux packet says the opposite boundary:

```text
flux is not one object yet
flux is a candidate family
flux placement remains to be classified
```

So the safe version is:

```text
manifold-level flux is a serious candidate placement, not a locked
pre-axial constraint.
```

### Also Too Strong

The pasted hypothesis says:

```text
(A3, A4, A5, A6) = 16 placements
```

This is plausible as a bookkeeping grid, but it is not yet an earned source
identity.

The current source has:

```text
4 topologies x 2 operator families x 2 token precedences = 16 ordered tokens
```

and separately:

```text
A3 = fiber/base or inner/outer token-set correlation
A4 = loop-order family
A5 = operator-family split
A6 = up/down token position
```

Those structures overlap, but the exact `A3 x A4 x A5 x A6 -> 16 tokens`
claim needs a row-by-row matrix, because the existing token table is generated
from topology, operator family, and precedence, while A3 appears through
loop/path placement and engine chart membership.

## Axis 3: Correct Current Anchor

The active math anchor is:

```text
fiber:
  gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)
  rho_fiber^s(u) = rho_fiber^s(0)

lifted base:
  gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)
  rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|
```

This is not merely "outer versus inner."

The deeper distinction is:

| A3 side | Geometry | Density law | Meaning |
|---|---|---|---|
| fiber | vertical Hopf-fiber motion | density-stationary | phase changes without Bloch-density motion |
| lifted base | horizontal lifted-base motion | density-traversing | Bloch density moves along the base projection |

The source says this is stronger than older left/right or flux-only readings.

Therefore the safest Axis 3 wording is:

```text
Axis 3 = fiber/density-stationary path versus lifted-base/density-traversing path.
```

The inner/outer words are current chart correlations, not the deepest math.

## Inner / Outer Is Not A Standalone Math Primitive

Source charts use:

```text
outer loop = WIN / LOSE in capital letters
inner loop = win / lose in lower-case letters
```

and the atlas records inner/outer token sets.

But source terrain tables also say:

```text
fiber terrains:
  engine type one inner
  engine type two outer

lifted-base terrains:
  engine type one outer
  engine type two inner
```

So "outer" does not globally mean "lifted base" unless engine type is fixed.

The correct relation is:

```text
path class is geometry-level: fiber vs lifted base
inner/outer is engine-chart placement
engine type decides how path class is named as inner/outer
```

This is exactly why A3 cannot be reduced to a loose "outer/inner" label.

## Axis 4: Loop-Order Family

The atlas gives:

```text
deductive:
  Phi_deductive = U circle E circle U circle E

inductive:
  Phi_inductive = E circle U circle E circle U
```

with current runtime correlation:

```text
deductive -> FeTi family
inductive -> TeFi family
```

This is stronger than the pasted shorthand "A4 picks operator pair."

Safer wording:

```text
Axis 4 selects the loop-order family over unitary and non-unitary branches.
FeTi / TeFi are current token-family correlations for those loop orders.
```

It should not be treated as a primitive pair-selector until the row matrix
proves the pair-selector reading preserves the exact source loop order.

## Engine Type: What The Source Actually Shows

The source charts show engine type one:

```text
outer loop: deductive order on lifted base
inner loop: inductive order on fiber
```

with rows:

| Step | Topology | Outer token | Inner token |
|---|---|---|---|
| 1 | `Se` | `TiSe` | `SeFi` |
| 2 | `Ne` | `NeTi` | `FiNe` |
| 3 | `Ni` | `NiFe` | `TeNi` |
| 4 | `Si` | `FeSi` | `SiTe` |

The source charts show engine type two:

```text
outer loop: inductive order on fiber
inner loop: deductive order on lifted base
```

with rows:

| Step | Topology | Outer token | Inner token |
|---|---|---|---|
| 1 | `Se` | `FiSe` | `SeTi` |
| 2 | `Si` | `TeSi` | `SiFe` |
| 3 | `Ni` | `NiTe` | `FeNi` |
| 4 | `Ne` | `NeFi` | `TiNe` |

Therefore engine type is not currently reducible to:

```text
A4 alone
flux alone
operator pair alone
```

It is at least an arrangement over:

```text
sheet / chirality bookkeeping
path class: fiber or lifted base
loop chart placement: inner or outer
loop-order family: deductive or inductive
operator family and token order
topology order through the four rows
```

The pasted claim that `(A3,A4)` "carry engine-type structure" is directionally
right if read as:

```text
engine type is heavily constrained by how path class and loop-order family
are paired.
```

It is too strong if read as:

```text
engine type is fully determined by A3 and A4 alone.
```

That needs a discriminator test.

## Flux: Current Source Status

The strongest source statement is:

```text
flux is an open derived object, not a primitive.
```

The flux packet lists a chain:

```text
C -> M(C) -> H -> S3 -> T_eta -> (psi_L, psi_R)
-> (rho_L, rho_R) -> (gamma_f, gamma_b)
-> Delta-surfaces -> J -> flux placement
```

Candidate flux families include:

| Candidate | Meaning |
|---|---|
| `J_geom` | geometric transport flux |
| `J_chi` | chirality separation flux |
| `J_Bloch` | differential Bloch current |
| `J_ent` | entropic asymmetry |
| `J_cut` | cut-state information current |
| `J_axis` | axis-internal readout |
| `J_cross` | coupled multi-axis observable |

This means:

```text
manifold-level flux is one candidate among several.
```

The source has not admitted:

```text
F0?_FLUX as a root or pre-axial constraint.
```

The correct audit label is:

```text
flux placement: OPEN
best current prior: derived manifold/change-surface candidate, not operator-internal axis
```

## Why Manifold-Level Flux Is Still A Serious Candidate

The manifold-level reading has real support:

1. Flux candidates are built from:

```text
stagewise deltas
left/right density divergence
Bloch currents
loop swaps
chirality ablations
transport gaps
```

These are not single-operator properties.

2. The source requires testing:

```text
no-chirality
loop-swap
base/fiber flattening
axis-internal alternatives
cross-axis alternatives
```

That puts flux above local operator math.

3. Engine type uses left/right Weyl sheet realization:

```text
H_left = +H0
H_right = -H0
```

and path/loop arrangements.

That gives a natural place for a global orientation or flux-like asymmetry.

So this hypothesis should survive as:

```text
flux may be a manifold-level change-surface or chirality/transport current
that binds engine type.
```

But not as:

```text
flux is already a new pre-axial root.
```

## Discriminator Tests

### Test 1: Engine-Bound Versus Stage-Bound Flux

Question:

```text
Can flux sign be flipped for one stage while retaining a coherent engine?
```

If yes:

```text
flux is stage/axis-level or at least locally selectable.
```

If no:

```text
flux is engine-bound or manifold-bound.
```

Required controls:

```text
canonical T1
canonical T2
T1 with one stage flux flipped
T2 with one stage flux flipped
all-stage flux flipped
sheet sign flipped but token table held fixed
token table flipped but sheet sign held fixed
```

Readouts:

```text
CPTP validity
fixed-point identity
schedule basin cluster
left/right density divergence D_chi
Bloch current J_Bloch
entropy current J_ent
cut current J_cut if rho_AB exists
```

### Test 2: Does `(A3,A4)` Determine Engine Type?

Build a row matrix with columns:

```text
engine_type
sheet
topology
path_class: fiber | lifted_base
chart_loop: inner | outer
loop_order_family: deductive | inductive
operator_family: dephasing | rotation
token_precedence: operator_first | terrain_first
token
```

Then test:

```text
Can engine_type be recovered from only (path_class, loop_order_family)?
Can engine_type be recovered from only (chart_loop, loop_order_family)?
Can engine_type be recovered only if sheet or flux sign is included?
```

Possible outcomes:

| Outcome | Meaning |
|---|---|
| `(A3,A4)` uniquely recovers engine type | pasted claim survives |
| `(A3,A4)` does not recover engine type, but `(A3,A4,sheet)` does | engine type needs manifold sheet/chirality |
| `(A3,A4)` does not recover engine type, but `(A3,A4,flux_candidate)` does | flux is engine-binding |
| no compact projection recovers engine type | engine type remains a full table-level grammar |

### Test 3: Is A3 Outer/Inner Or Fiber/Base?

Take the source terrain table:

```text
fiber: type one inner, type two outer
base: type one outer, type two inner
```

Falsifier for "A3 = outer/inner":

```text
if the same path class maps to both inner and outer depending on engine type,
then outer/inner is not the geometry-level A3 primitive.
```

The current source already triggers this warning.

So the safer A3 primitive is:

```text
fiber/base
```

with:

```text
inner/outer = engine-chart correlation.
```

### Test 4: Flux Placement Classification

For each flux candidate `J`, test:

```text
survives before rho_AB?
survives on geometry variables alone?
collapses under no-chirality?
collapses under loop-swap?
collapses under base/fiber flattening?
explained by one axis alone?
requires multi-axis coupling?
```

Classify:

```text
pre-axis geometric
chirality differential
Bloch current
entropy current
cut-state current
axis-internal readout
cross-axis observable
```

No candidate becomes "flux" without this classification.

## Corrected Stack For Exploration

Current lowest-risk exploratory stack:

```text
Root constraints:
  F01 finitude
  N01 noncommutation

Manifold geometry:
  S3 spinor carrier
  S2 Hopf base
  nested Hopf tori
  Weyl sheet pair with H_left=+H0, H_right=-H0
  fiber/base loop laws

Open derived flux family:
  J_geom, J_chi, J_Bloch, J_ent, J_cut, J_axis, J_cross
  placement not decided

Lower active axes:
  A3 = fiber/base path class, chart-correlated with inner/outer
  A4 = loop-order family, currently correlated with FeTi/TeFi
  A5 = dephasing {Ti,Te} vs rotation {Fi,Fe}
  A6 = up/down token position, requiring left/right action audit

Engine type:
  table-level arrangement over sheet, path class, loop order, operator
  family, token precedence, and topology order.
```

## Claims To Keep Open

| Claim | Status |
|---|---|
| flux is not Axis 6 | survived source audit |
| flux is not Axis 3 | survived source audit |
| A3 is fiber/base, not chirality | source-backed |
| A3 can be called outer/inner without qualification | weak; source warns against it |
| flux is manifold-level | plausible candidate, not admitted |
| flux is pre-axial/root-like | not admitted |
| engine type is determined by A3 and A4 alone | open; needs row-matrix test |
| engine type needs flux/sheet sign beyond A3/A4 | plausible; needs discriminator |
| 16 placements are exactly A3 x A4 x A5 x A6 | plausible bookkeeping, not yet row-proven |

## Required Next Probe

The next useful probe is not another narrative rewrite.

It is a row-matrix audit:

```text
16 ordered tokens
8 terrain/path rows
2 engine type charts
```

with explicit columns:

```text
engine_type
sheet / H sign
topology
path_class
chart_loop
loop_order_family
operator
operator_family
token_precedence
axis6_action_side if implemented
token
```

Then run three projections:

```text
projection_1: (A3,A4,A5,A6) -> token uniqueness
projection_2: (A3,A4) -> engine type recoverability
projection_3: (A3,A4,sheet_or_flux) -> engine type recoverability
```

That is the clean way to decide whether Claude's hypothesis is right, partly
right, or overcompressed.

## Bottom Line

This intake improves the model only if it is weakened into a testable form:

```text
A3 is source-backed as fiber/base path class, with inner/outer as chart
correlation.

Flux is source-backed as open derived candidate-family work, not an axis and
not a root constraint.

Engine type may require a manifold-level sheet/flux selector in addition to
A3/A4, but that must be proven by row-matrix projection.
```

Do not canonize:

```text
F0?_FLUX
A3 = outer/inner without path-class qualification
engine type = A3 x A4
16 tokens = A3 x A4 x A5 x A6
```

until the row-matrix audit passes.
