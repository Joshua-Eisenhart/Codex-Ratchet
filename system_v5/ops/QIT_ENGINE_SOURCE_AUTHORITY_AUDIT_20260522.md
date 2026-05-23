# QIT Engine Source Authority Audit

**Created:** 2026-05-22
**Status:** source-authority audit package; no implementation promotion
**Related freeze:** `system_v5/ops/QIT_ENGINE_MANIFOLD_AUDIT_FREEZE_20260522.md`

## Purpose

This package replaces the failed "continue building the full engines" direction with a source-authority audit.

The problem is not that the project lacks the operator math. The old docs already spell it out. The failure is that recent sim/runtime work was able to operate on terrain labels such as `Se`, `Ne`, `Ni`, and `Si` while dropping the chart-locked ordered tokens, Axis 5 operator family, Axis 6 left/right action side, Axis 6 precedence/sign, exact channel, and semantic role columns.

No engine, PEPS/PEPS3D, MPDO, Phi0, or attractor-basin promotion is admissible until source-to-runtime conformance is audited and repaired.

## Authority Surfaces

| Surface | Authority role | Key rows |
|---|---|---|
| `system_v5/READ ONLY Reference Docs/outdated system math and geometry.md` | Old formalized stack: root constraints, geometry/carrier, axes 0-6, exact operators, engine type placements | RC/EC table lines 15-23; build order lines 27-29; axes lines 72-88; next move lines 95-103 |
| `system_v5/READ ONLY Reference Docs/Formal constraints and geometry .md` | Parallel formal chain for constraints to geometry to entropy/bridge | use as corroborating formal surface |
| `system_v5/READ ONLY Reference Docs/operator math explicit.md` | Exact four-operator packet; UP/DOWN is not extra operator math by itself | lines 1-6; `Ti` starts 102; `Te` starts 279; `Fi` starts 488; `Fe` starts 646 |
| `system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md` | Local source-authority packet worked out from the four base operators and their two signed variants; includes fenced exploratory overlays | base maps, Bloch actions, generators, signed variants, 16-token matrix, audited Ax4/Ax5/Ax6 status |
| `system_v5/READ ONLY Reference Docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP copy.md` | Separates carrier geometry, function/operator math, and IGT labels; full token law and engine charts | rules lines 18-30; judging table lines 206-211; token table lines 251-256; signed variants lines 269-278; engine charts lines 311-330 |
| `system_v5/READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md` | Axis 4/5/6 anchors, terrain table, signed variants, IGT correlations, engine type charts | Axis 4 lines 380-419; Axis 5 lines 425-464; Axis 6 lines 476-515; terrain lines 569-580; signed variants lines 584-595; engine charts lines 610-626 |
| `system_v5/docs/17_actual_lego_registry.md` | Build guardrail and one-row-per-lego registry | guardrail lines 19-24; placement rows lines 140-159; bridge/axis gate lines 225-240 |
| `system_v5/grok_sim/SCREENSHOTS_INDEX.md` | Screenshot extraction index for operator/terrain/placement evidence | use only as screenshot-backed support, not as replacement for source tables |

## Core Correction

Jungian functions are labels and chart grammar. They do not replace operator math.

The source docs explicitly separate:

- carrier geometry: `S^3`, Hopf projection, nested tori, fiber/base loops, Weyl sheets;
- perceiving terrain/topology labels: `Se`, `Ne`, `Ni`, `Si`;
- judging operators: `Ti`, `Te`, `Fi`, `Fe`;
- ordered tokens: `TiSe`, `NiTe`, `SiTe`, etc.;
- IGT outcome labels: `WIN`, `LOSE`, `win`, `lose`;
- axes: `Ax0` through `Ax6`.

Any runtime row that does not carry these as separate fields is not source-conformant.

## Root And Geometry Stack

| Layer | Source truth | Runtime implication |
|---|---|---|
| `RC-1` / `F01` | finite carrier, finite probes, finite operators, finite paths | no unbounded semantic import; every row has finite witnesses |
| `RC-2` / `N01` | order-sensitive composition; `AB != BA` in general | token order and channel composition order are first-class data |
| `M(C)` | admissible configuration space before geometry | geometry/axes are derived, not primitive |
| Build order | constraints -> `M(C)` -> geometry on `M(C)` -> axes | no axis/engine claim before the lower rows are represented |
| Carrier | `H = C^2`, density states `D(C^2)`, Bloch form | minimal QIT state row must be explicit |
| Geometry | `S^3`, Hopf `S^3 -> S^2`, `T_eta`, `T_(pi/4)`, Hopf connection | terrain/operator work does not replace geometry |
| Loops | fiber loop density-stationary; base loop density-traversing | loop id and loop law must be explicit |
| Weyl sheets | `H_L = +H_0`, `H_R = -H_0` | type/sheet sign must be explicit |

## Exact Operator Packet

The intrinsic operator math is only the four base operators. UP/DOWN is not extra operator math by itself; it appears after a terrain map and precedence choice are chosen.

| Operator | Exact channel | Axis 5 family | Native topology set |
|---|---|---|---|
| `Ti` | `(1-q1) rho + q1(P0 rho P0 + P1 rho P1)` | dephasing / projection | `Se`, `Ne` |
| `Te` | `(1-q2) rho + q2(Q+ rho Q+ + Q- rho Q-)` | dephasing / projection | `Ni`, `Si` |
| `Fi` | `Ux(theta) rho Ux(theta)^dagger` | unitary rotation | `Se`, `Ne` |
| `Fe` | `Uz(phi) rho Uz(phi)^dagger` | unitary rotation | `Ni`, `Si` |

Runtime implication: semantic descriptions such as gradient/descent, Hamiltonian drive, strategy, or topology are companion columns. They cannot replace the exact operator channel.

## Functional-Dependent Gradient Semantics

`Te` does not mean "descent" or "ascent" in isolation. The exact `Te` channel is the `sigma_x` dephasing/projection map: it preserves the `x` Bloch component and damps the transverse components. Its gradient interpretation depends on the functional being read.

| Functional / target | `Te` direction |
|---|---|
| von Neumann entropy `S(rho)` | increases entropy for non-`sigma_x`-diagonal states |
| purity `Tr(rho^2)` | decreases purity for non-`sigma_x`-diagonal states |
| distance to the `sigma_x`-diagonal line | decreases distance |
| distance from a generic non-`sigma_x` pure target | can increase |

Therefore a row cannot be labeled `gradient_descent`, `gradient_ascent`, `push`, or `optimize` unless the runtime row also names:

- the functional being read;
- the target/attractor or invariant set;
- the terrain context (`Ni`/`Si` compression versus `Se`/`Ne` expansion);
- the Axis 6 action side (`left_action` / `A rho` versus `right_action` / `rho A`);
- the Axis 6 precedence representation (`operator_first` versus `terrain_first`);
- the exact ordered token.

Candidate reading to audit, not promote without witnesses:

| Token row | Why it is the relevant descent/ascent audit row |
|---|---|
| `NiTe` | `Te` down, terrain-first, on compression topology `Ni`; candidate compression-attractor descent row |
| `SiTe` | `Te` down, terrain-first, on compression topology `Si`; candidate compression/invariant-strata descent row |
| `TeNi` | `Te` up, operator-first, on compression topology `Ni`; candidate mirror/ascent-or-preconditioned row depending on chosen functional |
| `TeSi` | `Te` up, operator-first, on compression topology `Si`; candidate mirror/ascent-or-preconditioned row depending on chosen functional |

The audit must not generalize a result from these four rows to all 16 placements.

## Axis Map

| Axis | Source role | Runtime field required |
|---|---|---|
| `Ax0` | `Phi0(rho_AB)` with coherent information / conditional entropy / mutual information candidates; bridge `Xi` open | `phi0_candidate`, `rho_ab_bridge`, control status; blocked until bridge conformance |
| `Ax1` | unitary branch vs proper CPTP branch | `channel_class` and CPTP/unitary witness |
| `Ax2` | direct representation vs conjugated representation | `representation_frame` and `V_s` / co-rotating-frame metadata |
| `Ax3` | fiber loop vs lifted-base loop | `loop_class`, `path_law`, `density_law` |
| `Ax4` | coupled loop-channel algebra and engine-direction test | `loop_channel_word`, not just individual stage label |
| `Ax5` | dephasing `{Ti,Te}` vs rotation `{Fi,Fe}` | `operator_family` |
| `Ax6` | left action `A rho` vs right action `rho A`; represented in the token table as operator-first vs terrain-first / up vs down precedence | `axis6_action_side`, `precedence`, `axis6_sign`, ordered token |

## Audited Ax4 / Ax5 / Ax6 Clarification

The current audit does not admit the external `A4 x A5 intersection` grid as
canon. It is at most an exploratory reconstruction.

Source-backed status:

| Axis | Exact anchor | Pair / symbolic layer status |
|---|---|---|
| `Ax4` | loop-order family: `U o E o U o E` versus `E o U o E o U`; implemented as `FeTi` versus `TeFi` | pair-order overlays such as `TiFe`/`FeTi` remain proposed or symbolic |
| `Ax5` | operator-family split: dephasing `{Ti, Te}` versus rotation `{Fi, Fe}` | `FeFi` versus `TiTe` is a recorded correlation layer; `TeTi` versus `FeFi` appears in a stricter candidate/pre-math surface but is not the exact anchor |
| `Ax6` | left action `A rho` versus right action `rho A`; represented as operator-first versus terrain-first / up-down token order | strongest alignment; outward/inward functional sign is still an exploratory hypothesis |

Therefore the safe runtime order is:

```text
1. represent exact operators Ti, Te, Fi, Fe
2. attach Ax5 family = dephasing or rotation
3. attach Ax6 action side = left_action or right_action, plus precedence = operator_first or terrain_first
4. compose Ax4 loop-order family at the loop/engine layer
5. keep any pair-intersection or functional-role labels fenced until tested
```

## Sixteen Ordered Tokens

| Topology | Dephasing up | Dephasing down | Rotation up | Rotation down |
|---|---|---|---|---|
| `Se` | `TiSe` | `SeTi` | `FiSe` | `SeFi` |
| `Ne` | `TiNe` | `NeTi` | `FiNe` | `NeFi` |
| `Ni` | `TeNi` | `NiTe` | `FeNi` | `NiFe` |
| `Si` | `TeSi` | `SiTe` | `FeSi` | `SiFe` |

`NiTe` and `SiTe` are explicit `Te`-down terrain-first tokens on the conjugated `Ni/Si` side. They are not optional, not inferred from `Ni` or `Si` alone, and not replaceable by a generic "Ni gradient" or generic entropy-gradient readout. Their gradient/descent meaning is row-contextual: compression terrain plus `Te` dephasing plus terrain-first precedence plus a named functional/target.

If `Te` carries a gradient/descent semantic role in a Rosetta or screenshot surface, that semantic role must be attached to the `Te` token row while preserving the exact `Te` channel. The runtime must not collapse semantic role, operator channel, and terrain label into one field.

## Engine Chart Rows

### Type 1

| Step | Topology | Outer token | Inner token |
|---|---|---|---|
| 1 | `Se` | `TiSe` | `SeFi` |
| 2 | `Ne` | `NeTi` | `FiNe` |
| 3 | `Ni` | `NiFe` | `TeNi` |
| 4 | `Si` | `FeSi` | `SiTe` |

### Type 2

| Step | Topology | Outer token | Inner token |
|---|---|---|---|
| 1 | `Se` | `FiSe` | `SeTi` |
| 2 | `Si` | `TeSi` | `SiFe` |
| 3 | `Ni` | `NiTe` | `FeNi` |
| 4 | `Ne` | `NeFi` | `TiNe` |

Runtime implication: a stage is not fully identified by `Type`, `loop`, `step`, and `terrain`. It must include the ordered token and the exact operator.

## Current Runtime Nonconformance

| Surface | Status | Reason |
|---|---|---|
| `qit_engine_runtime.py` | `terrain_only_anchor` | stage orders and channel builders are terrain-keyed; ordered token, Ax5, Ax6, and precedence are not load-bearing in the shared runtime row |
| `canonical_qit_engine_specs.py` | `candidate_recovery_anchor` | contains native operator sets, token precedence, and slot specs; needs audit against source tables and then enforcement as runtime source |
| D130 PEPS/PEPS3D depth inventory | `terrain_loop_inventory_only` | covers tiny tensor substrates by sheet/loop/stage/terrain; not proof of all 16 operator-axis token rows |
| Recent sidequest engine sims | `historical_or_sidequest` | useful for ideas only; cannot promote if they ignored source token rows or used class-wrong readouts |

## Required Runtime Event Schema

Every stage event row must include at least:

| Field | Required because |
|---|---|
| `engine_type` | Type 1 / Type 2 chart differs |
| `sheet` | left/right Weyl sign differs |
| `loop_class` | fiber/base loop laws differ |
| `stage_index` | chart order matters |
| `topology` | `Se/Ne/Ni/Si` terrain family |
| `ordered_token` | source token law is load-bearing |
| `operator` | exact `Ti/Te/Fi/Fe` channel |
| `operator_family` | Axis 5 dephasing/rotation split |
| `axis6_action_side` | Axis 6 left-action/right-action side |
| `precedence` | Axis 6 operator-first/terrain-first representation |
| `axis6_sign` | up/down signed variant |
| `exact_channel_family` | dephasing/projector or unitary rotation |
| `semantic_role` | Rosetta/Jung/IGT meaning, kept separate from exact operator |
| `functional_readout` | named functional for any gradient/ascent/descent claim |
| `target_or_attractor` | target line, fixed point, attractor, or invariant stratum for row-level gradient claims |
| `terrain_generator_law` | topology-flow dynamics |
| `path_law` | fiber/base path |
| `density_law` | density-stationary or density-traversing |
| `readout_observable` | class-correct observable for the row |
| `source_refs` | finite witness discipline |

A scout must fail if it cannot populate this schema from source authority.

## Quarantine Rule

Any result depending on a terrain-only runtime can remain as:

- tensor substrate evidence;
- simplified-channel spectral evidence;
- sidequest historical evidence;
- candidate idea generation.

It cannot be used as:

- operator-axis placement evidence;
- proof that all 16 token rows ran;
- PEPS/PEPS3D full-engine evidence;
- Phi0 bridge admission;
- attractor-basin admission;
- final manifold admission.

## Replacement Work Order

1. Build the source-authority matrix from the docs above.
2. Build runtime conformance matrix for `canonical_qit_engine_specs.py`, `qit_engine_runtime.py`, `engine_core.py`, D130, and recent dependent scouts.
3. Quarantine or reclassify every dependent receipt.
4. Specify the repaired runtime event schema and failing conformance tests.
5. Only after that, repair runtime code.
6. Only after runtime conformance tests pass, resume engine/tensor/Phi0/basin work.

The "old doc" next move remains correct: extend the strict format with terrain generators, 16 placements, graph-topology objects, and engine loop ownership. That is an audit/specification task before it is a dynamics task.
