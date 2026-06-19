# Assembled Engine v0 Design Receipt - 2026-06-12

claim_ceiling: design_receipt_only
promotion_allowed: false
sims_run: false
git_mutation: none

## Bottom Line

The smallest honest v0 is a tiny running object with all four owner-required parts present:

1. eight terrain spaces, one for each `Topology4 x Flux2` terrain realization;
2. sixteen stage regions, two per terrain, with the chart-locked signed operator acting only on states resident in that region;
3. two independent engine traversals, Type 1 / L and Type 2 / R, each running both MAX/major and min/minor loops through those stage spaces;
4. seven axis probe families measured on the resulting trajectories, not on a static carrier table.

The v0 should use a finite Hopf-torus / cell-complex chart carrier as the default substrate because that is the smallest source-faithful assembly surface already supported by the terrain, Family B, dynamic-chart, and homology feedstock. The ring-checkerboard/QCA reading is real feedstock for locality and flux index work, but forcing it into v0 would make the first assembled object larger than needed. The chart/surface/QCA substrate choice remains an explicit owner-choice point.

The raw owner sources do not define the four topology classes as `sphere / torus / nested / Mobius`. The source-locked four are `Se`, `Ne`, `Ni`, `Si`, realized as flow/topology families over the Hopf/Weyl terrain system: Funnel/Cannon, Vortex/Spiral, Pit/Source, Hill/Citadel after crossing with flux orientation.

## Read Authority Surfaces

- `system_v6/receipts/owner_architecture_requirement_20260612.md` at `0ff763858`: binding four-part definition of "simmed".
- `system_v6/receipts/doc_router_axes_terrains_operators_20260609.md` and the routed owner terrain sources.
- `system_v5/READ ONLY Reference Docs/ENGINE_64_SCHEDULE_ATLAS.md`.
- `system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md`.
- `system_v5/READ ONLY Reference Docs/Older Legacy/grok unified phuysics nov 29th.txt`.
- `system_v6/receipts/terrain_operator_map_20260609.md`.
- `system_v6/foundations/working_math_scaffold_20260609.md`.
- `system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md`.
- `system_v6/sims/source_locked_operator_base_packet/audit_verdict.md`.
- `system_v6/sims/terrain_generator_sheet_packet/audit_verdict.md`.
- `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md`.
- `system_v6/receipts/dynamic_manifold_upgrade_design_20260612.md`.
- `system_v6/sims/manifold_dynamic_chart_v0/audit_verdict.md`.
- `system_v6/sims/manifold_dynamic_chart_v1/audit_verdict.md`.
- `system_v6/sims/engines_run_with_axes_v0/audit_verdict.md`.
- `system_v6/receipts/owner_doctrine_axes_as_existence_probes_20260612.md`.
- `system_v6/sims/manifold_family_b_integrated_v0/audit_verdict.md` and `weld_feedstock_inventory_20260611.md`.
- `system_v6/sims/fiber_augmented_cover_v2/audit_verdict.md` and `axis_work_order_20260612.md`.
- `system_v6/receipts/ring_checkerboard_provenance_20260611.md`.
- `system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md`.
- `system_v6/sims/ring_checkerboard_qca_v3/audit_verdict.md`.
- `system_v6/receipts/coupling_law_family_table_20260611.md`.

## Object Definition

`AssembledEngineV0` is not the existing Matrix64, not the 33-cell dynamic chart alone, not the Family B Hopf packet alone, and not the Carnot/Szilard stroke baseline alone.

Minimal data object:

| object | required v0 fields |
|---|---|
| `TerrainSpace` | `terrain_id`, `topology_family`, `flux_orientation`, `carrier_cells`, `marked_regions`, `terrain_generator`, `homology_certificate_ref`, `source_packet_refs` |
| `StageRegion` | `stage_id`, `terrain_id`, `loop_region`, `loop_kind`, `operator_token`, `base_operator`, `precedence`, `legal_readouts`, `residency_predicate` |
| `EngineState` | `engine_id`, `trajectory_step`, `terrain_id`, `stage_id`, `cell_id`, `chart_coords`, `rho`, `entropy`, `source_chart`, `lineage_hash` |
| `TransportMap` | `from_stage`, `to_stage`, `from_chart`, `to_chart`, `cell_map`, `rho_map`, `validity_checks` |
| `AxisProbeRow` | `axis_id`, `trajectory_step`, `measurement_input`, `readout`, `control_readout`, `status`, `claim_ceiling` |

The state must physically reside on the terrain geometry. A stage operator can act only after the stage residency predicate proves that the state is inside the stage region. Moving to the next stage is a chart-to-chart transport row, not a table-label jump.

## 1. The Eight Terrains

Source reading: `Topology4 = {Se, Ne, Ni, Si}` and `Flux2 = {in, out}`. The eight named realizations are:

| terrain id | topology family from owner source | flux | source name | concrete v0 space | committed feedstock | new build needed |
|---|---|---:|---|---|---|---|
| `Se-in` | `Se`: radial expansion / CPTP expansion class | in / Type 1 | Funnel | small marked Hopf-torus cell complex with an expansion/funnel flow law on two shell bands; outer and inner subcomplexes both marked | terrain generator sheet, apple terrain formulas, Family B Hopf carrier, source-locked operator packet | instantiate finite cell object, region masks, generator-on-cells, topology certificate, in-flux orientation row |
| `Se-out` | `Se`: same topology family | out / Type 2 | Cannon | same v0 cell-complex template, but separate terrain object with outward/chiral sign and Cannon generator row | same as above plus flux/QCA doctrine for sign boundary | separate object id, opposite orientation witness, erasure control proving not just relabeling |
| `Ne-in` | `Ne`: tangential Hamiltonian circulation on `S3` / Hopf fiber class | in / Type 1 | Vortex | small fiber/annular cell complex with circulation around the Hopf fiber direction | terrain generator sheet, Hopf connection/loop formulas, Family B Hopf torus | pick pure vs weak-dissipative Ne policy, encode circulation direction, certify fiber loop class |
| `Ne-out` | `Ne`: same topology family | out / Type 2 | Spiral | same finite fiber/annular template as a distinct object with opposite handedness/sign | same as above | opposite circulation witness and sign-erasure collapse control |
| `Ni-in` | `Ni`: contraction/cooling / attractor class | in / Type 1 | Pit | two-shell contraction cell complex with sink/attractor marker; `sigma_-` terrain law | terrain generator sheet, apple formulas, Family B nested tori | finite sink/source region, contraction liveness check, residency-preserving update |
| `Ni-out` | `Ni`: same topology family | out / Type 2 | Source | two-shell source/emitter cell complex; `sigma_+` terrain law | same as above | source row, opposite sign witness, sink/source control |
| `Si-in` | `Si`: retained strata / invariant subspace class | in / Type 1 | Hill | finite stratified cell complex with retained/invariant subcomplexes and projector frame | terrain generator sheet, operator-stage parent, CW certificate machinery | choose/pin projector frame, invariant-region masks, stratum-retention certificate |
| `Si-out` | `Si`: same topology family | out / Type 2 | Citadel | finite stratified cell complex with opposite sheet/projector orientation | same as above | separate sheet/projector row and opposite-orientation control |

Important boundary: the eight spaces can share a tiny cell-complex template only if each emitted `TerrainSpace` has its own object id, marked regions, generator, flux orientation, and certificate. A shared template is acceptable; eight labels over one unmarked carrier are below the owner requirement.

Terrain-topology certificate in v0 should not overclaim distinct Betti profiles unless the built complexes really have them. The certificate should record:

- chain complex and boundary matrices;
- Betti/Euler/orientability where applicable;
- marked region topology;
- fiber/base loop class or shell/stratum witness;
- terrain generator class witness;
- flux orientation witness;
- erasure controls.

## 2. The Sixteen Stages

Source reading: the owner structure is `8 terrains x 2 loop regions = 16 stage contexts`. It is not `16 = 16 separate topology families`. Both engine types carry the same four topology families and both feedback modes; chirality/flux decides the assignment.

Common legal readouts for every stage:

- `state_entered_region`: true only if the state cell belongs to that stage's marked region;
- `rho_before`, `rho_after`, entropy/purity/trace-distance rows;
- signed precedence gap when applicable: `Delta_T_O(rho) = Phi_T(O(rho)) - O(Phi_T(rho))`;
- transport row to the next stage;
- trajectory lineage row;
- chart token readout such as `WIN`, `LOSE`, `win`, `lose`.

Forbidden v0 readouts:

- payoff, selection, psychology, physics, bridge, or canonical axis admission from the win/loss labels;
- claiming all 64 Matrix64 schedule cells are a running engine;
- claiming a stage operator acted without a region-residency row.

### Type 1 / L Engine Stage Contexts

Type 1 source lock: flux IN / left Weyl. MAX/major loop is Deductive / `FeTi`; min/minor loop is Inductive / `TeFi`.

| stage id | terrain | region | loop | order | token | base operator | precedence | signed op | chart readout |
|---|---|---|---|---|---|---|---|---|---|
| `L.MAX.1` | `Se-in` | outer/base | MAX/major | Deductive | `TiSe` | `Ti` | operator first | `Ti_up` | `LOSE` |
| `L.MAX.2` | `Ne-in` | outer/base | MAX/major | Deductive | `NeTi` | `Ti` | terrain first | `Ti_down` | `WIN` |
| `L.MAX.3` | `Ni-in` | outer/base | MAX/major | Deductive | `NiFe` | `Fe` | terrain first | `Fe_down` | `LOSE` |
| `L.MAX.4` | `Si-in` | outer/base | MAX/major | Deductive | `FeSi` | `Fe` | operator first | `Fe_up` | `WIN` |
| `L.min.1` | `Se-in` | inner/fiber | min/minor | Inductive | `SeFi` | `Fi` | terrain first | `Fi_down` | `win` |
| `L.min.2` | `Si-in` | inner/fiber | min/minor | Inductive | `SiTe` | `Te` | terrain first | `Te_down` | `win` |
| `L.min.3` | `Ni-in` | inner/fiber | min/minor | Inductive | `TeNi` | `Te` | operator first | `Te_up` | `lose` |
| `L.min.4` | `Ne-in` | inner/fiber | min/minor | Inductive | `FiNe` | `Fi` | operator first | `Fi_up` | `lose` |

Traversal schedules:

- `L.MAX`: `Se-in -> Ne-in -> Ni-in -> Si-in -> Se-in`.
- `L.min`: `Se-in -> Si-in -> Ni-in -> Ne-in -> Se-in`.
- Nov-29 pattern carried: Type 1 MAX is the `FeTi`/major loop and Type 1 min is the `TeFi`/minor loop. The atlas supplies the terrain/token order above.

### Type 2 / R Engine Stage Contexts

Type 2 source lock: flux OUT / right Weyl. MAX/major loop is Inductive / `TeFi`; min/minor loop is Deductive / `FeTi`.

| stage id | terrain | region | loop | order | token | base operator | precedence | signed op | chart readout |
|---|---|---|---|---|---|---|---|---|---|
| `R.MAX.1` | `Se-out` | outer/base | MAX/major | Inductive | `FiSe` | `Fi` | operator first | `Fi_up` | `WIN` |
| `R.MAX.2` | `Si-out` | outer/base | MAX/major | Inductive | `TeSi` | `Te` | operator first | `Te_up` | `WIN` |
| `R.MAX.3` | `Ni-out` | outer/base | MAX/major | Inductive | `NiTe` | `Te` | terrain first | `Te_down` | `LOSE` |
| `R.MAX.4` | `Ne-out` | outer/base | MAX/major | Inductive | `NeFi` | `Fi` | terrain first | `Fi_down` | `LOSE` |
| `R.min.1` | `Se-out` | inner/fiber | min/minor | Deductive | `SeTi` | `Ti` | terrain first | `Ti_down` | `lose` |
| `R.min.2` | `Ne-out` | inner/fiber | min/minor | Deductive | `TiNe` | `Ti` | operator first | `Ti_up` | `win` |
| `R.min.3` | `Ni-out` | inner/fiber | min/minor | Deductive | `FeNi` | `Fe` | operator first | `Fe_up` | `lose` |
| `R.min.4` | `Si-out` | inner/fiber | min/minor | Deductive | `SiFe` | `Fe` | terrain first | `Fe_down` | `win` |

Traversal schedules:

- `R.MAX`: `Se-out -> Si-out -> Ni-out -> Ne-out -> Se-out`.
- `R.min`: `Se-out -> Ne-out -> Ni-out -> Si-out -> Se-out`.
- Nov-29 pattern carried: Type 2 MAX is the `TeFi`/major loop and Type 2 min is the `FeTi`/minor loop.

## 3. The Two Engines

The two engines are not two labels on one merged automaton.

| engine | source identity | required v0 traversal | independence requirement |
|---|---|---|---|
| `L` / Type 1 | left Weyl, flux IN | runs `L.MAX` and `L.min` as two stacked loops over `Se-in`, `Ne-in`, `Ni-in`, `Si-in` stage spaces | no merge with R; shared comparison rows are readouts only |
| `R` / Type 2 | right Weyl, flux OUT | runs `R.MAX` and `R.min` as two stacked loops over `Se-out`, `Si-out`, `Ni-out`, `Ne-out` stage spaces | no merge with L; opposite flux/chirality must be carried |

Minimal traversal mechanics:

1. seed one valid density/spinor-derived state on the first terrain region of each loop;
2. verify stage residency;
3. apply the stage operator/terrain composition;
4. emit `rho_after`, entropy, purity, signed order gap, and local readouts;
5. transport the state through an explicit chart-to-chart map into the next terrain region;
6. repeat until loop closure;
7. emit trajectory rows and axis probe rows on the trajectory.

The weld machinery for v0 is the chart-to-chart transport between terrain spaces. This is not yet the full Family A/B super-weld. It must still carry:

- source and target stage ids;
- cell/region map;
- chart coordinate map;
- density-validity check;
- lineage hash;
- roundtrip or identity controls where available.

Closure boundary:

- v0 can close at the density/terrain-stage level after one full four-stage loop per loop family.
- spinor-level 720-degree closure is a v1+ row unless the owner chooses to make it a v0 acceptance gate.

## 4. Axes On The Running Engines

Axes are existence probes on the running trajectory. v0 may record null or partial probe outcomes, but every axis row must bite or report why it did not.

| axis | v0 measurement on trajectory | enabling feedstock | v0 status | v1+ defer |
|---|---|---|---|---|
| `Axis0` response | perturb a state/entry condition, run the loop, classify spread/damp/return on the trajectory using dynamic-chart protocol | dynamic chart v0/v1, owner existence-probe doctrine | measurable as candidate/null/partial; not admitted unless probe-bite criteria pass | stable contender registry, `rho_AB`/`Xi` bridge, stronger perturb family |
| `Axis1` legality/branch | read terrain law class over trajectory: unitary/Hamiltonian vs CPTP/dissipative/bath-gated behavior, currently source-framed around `{Se,Ni}` vs `{Ne,Si}` alternatives | working scaffold, terrain sheet packet | recordable as source-labeled trajectory readout | dedicated discriminator and independence controls |
| `Axis2` frame/directness | read direct vs conjugated/frame/connection behavior across transported stages, with `{Se,Ne}` vs `{Si,Ni}` candidate split preserved | working scaffold, Hopf connection sources | recordable as candidate frame readout | dedicated adapter and chart-frame discriminator |
| `Axis3` placement/flux overlay | measure inner/fiber vs outer/base residency and gamma-in/gamma-out behavior; separately record L/R flux orientation | Family B Hopf loops, terrain generator sheet, axis work order | strongest v0 axis surface because stage residency already uses it | disentangle fiber/base, Type1/Type2 inversion, chirality, and in/out flux if stronger claims are wanted |
| `Axis4` composition order | read Deductive vs Inductive traversal order, compute order-shuffle control, compare trajectory signatures | Nov-29 loop source, atlas, ring floor, order receipts | measurable as traversal-order row | full coupling/order law beyond per-engine loops |
| `Axis5` operator family | read `{Ti,Te}` dephasing/pinching vs `{Fi,Fe}` rotation/unitary family at each stage, with entropy/purity side observations | source-locked operators, operator-stage packets | family readout measurable | full substage product blocked on substage-transition convention |
| `Axis6` precedence | compute `Phi_T(O(rho))` vs `O(Phi_T(rho))` and `Delta_T_O(rho)` at the actual stage state | terrain_operator_precedence_64_matrix, source-locked operators | directly measurable on stages | stronger generic-state SMT/64 runtime closure |

Axis v0 acceptance should require:

- at least one trajectory row per axis per engine, even if the result is null;
- a control row for each probe family;
- no static-carrier-only axis claims;
- every axis label tied to a trajectory step and stage id.

## 5. The v0 Cut

Minimum v0 that is still the assembled object:

| requirement part | smallest acceptable v0 |
|---|---|
| eight terrains | eight `TerrainSpace` objects over a finite Hopf/cell carrier, each with region masks, terrain law, flux orientation, and certificate |
| sixteen stages | the exact sixteen chart-locked stage rows above, each as a `StageRegion` with residency and operator action |
| two engines | L and R run their MAX and min loops independently, producing trajectory rows over stage spaces |
| axes on running engines | Axis0-Axis6 probe rows computed from those trajectories, with controls and claim ceilings |

Not enough:

- a static `8 terrains x 8 signed operators` matrix with no moving state;
- a dynamic 33-cell chart with no eight terrain spaces;
- a two-engine stroke baseline with no stage-region residency;
- axis readouts copied from parent tables rather than measured on the new trajectory;
- one engine only;
- dropping either MAX/major or min/minor loops.

Deliberate v0 reductions:

- one tiny seed set is acceptable if controls exist;
- one full pass per loop is acceptable if closure and liveness are checked;
- one finite-time policy is acceptable if declared;
- local von Neumann entropy / purity / trace distance are enough for v0 entropy readouts;
- the full Matrix64 schedule lattice is not required as runtime closure;
- a chart-level finite cell substrate is enough unless the owner chooses surface or QCA as a v0 gate.

v1+ deferrals:

- final chart/surface/QCA substrate choice;
- QCA/open-chain index as the primary flux invariant;
- spinor-level 720 double-cover closure as a required engine gate;
- full 64 schedule-cell runtime traversal;
- full Axis0 admission and `rho_AB`/`Xi` bridge;
- full Axis5 substage product;
- global axis independence proof;
- bridge, physics, biology, scientific coupling, or promotion above scratch/design;
- Family A/B/C integrated weld as a prerequisite for this v0. The assembled engine can consume their feedstock without claiming the super-weld is complete.

## 6. Witness Gates For The Build

### Gate A - Terrain topology certificates

For each terrain:

- emit the finite cell complex / chain complex;
- recompute boundary validity;
- record Betti/Euler/orientability where scoped;
- record marked region topology;
- record fiber/base/shell/stratum witness as applicable;
- prove the terrain generator and flux orientation are wired to that terrain object;
- run label-erasure and sign-erasure controls.

Pass condition: all eight terrain objects have real certificates, not only labels.

### Gate B - Stage-operator residency

For every stage action:

- check `state.cell_id in stage.region`;
- check `state.terrain_id == stage.terrain_id`;
- apply only the stage's chart-locked token;
- emit `rho_before`, `rho_after`, and density-validity checks;
- refuse out-of-region application.

Pass condition: every operator action is tied to a valid resident state.

### Gate C - Traversal liveness

For L and R:

- each required stage is visited in exact order;
- state is transported by an explicit map between stages;
- loop closure is recorded;
- identity/no-op rows are classified honestly;
- order-shuffle controls change the traversal signature where order matters.

Pass condition: both engines produce moving or honestly stationary trajectory rows through all required stage spaces.

### Gate D - Probe bite

For each axis:

- measurement references a trajectory row;
- null or near-constant outcomes are allowed only if reported as null/partial;
- at least one control can fail;
- static parent readbacks are forbidden as positive evidence.

Pass condition: all seven axis families either bite or emit an explicit bounded null/partial row.

### Gate E - Transport/weld sanity

For each inter-stage transport:

- source and target chart ids are recorded;
- cell and coordinate maps are explicit;
- `rho` remains valid;
- lineage hash changes only where expected;
- roundtrip/identity controls run where available.

Pass condition: the running state moves by declared chart transport, not by relabeling.

## 7. Reuse Map

| existing component | feeds v0 | boundary |
|---|---|---|
| owner architecture requirement | acceptance target and claim ceiling | design receipt only until built |
| source router + apple/atlas/Nov-29 sources | terrain taxonomy, stage table, loop schedules | do not substitute guessed topology names |
| source-locked operator base packet | `Ti`, `Te`, `Fi`, `Fe` base operators | signed variants are precedence roles, not new base operators |
| four-operator signed math packet | operator pair semantics and stage map formulas | exploratory role language remains exploratory unless functional tested |
| terrain generator sheet packet | eight terrain laws and sixteen placements | scratch-diagnostic feedstock, not assembled engine |
| terrain operator precedence 64 matrix | order-gap mechanics and Matrix64 schedule feedstock | not runtime closure; not the assembled object |
| Family B integrated Hopf machinery | shared Hopf-torus chart carrier, nested geometry, trajectory lineage lessons | not two-engine evidence; not A/B weld |
| CW cellular cover / homology machinery | finite cell-complex certificate style and future homology consumer pattern | cover law result is about b6 row, not terrain proof by itself |
| dynamic chart v0/v1 | evolving state rows, state-derived entropy, perturb/watch/classify protocol | existing near-null results do not earn Axis0 admission |
| engines_run_with_axes_v0 | pattern for trajectory plus axis readouts over running transitions | classical baseline only; no terrain-stage residency |
| ring-checkerboard provenance | finite local support and microstate/substrate candidate | support reading and cosmology/substrate reading remain separate |
| ring-checkerboard QCA v3 | open-chain local-unitary fixture showing opposite L/R extracted indices at scratch ceiling | not finite-ring QCA admission; not required for minimal chart v0 |
| axes-as-existence-probes doctrine | probe-bite gates and contender discipline | axes remain probes, not primitive coordinates |
| coupling-law family table | L/R independence, flux as L/R DoF, order preservation | engine-on-engine coupling is v1+ unless owner chooses otherwise |

## Build Ladder

| rung | target | concrete output | effort estimate | stop/block condition |
|---|---|---|---|---|
| 0 | this design receipt | `assembled_engine_v0_design_20260612.md` | done | no sims in this lane |
| 1 | terrain spaces | eight small `TerrainSpace` fixtures with chain/cell certificates and terrain law refs | M: 1-2 focused days | blocked if Topology4 is redefined as four distinct homology types without owner choice |
| 2 | stage residency | sixteen `StageRegion` rows plus residency validator and operator dispatch table | S/M: 0.5-1.5 days | blocked if signed operator convention changes |
| 3 | traversal | L/R trajectory runner over MAX and min loops with chart transport rows | M/L: 2-3 days | blocked if transport/weld convention is not pinned |
| 4 | axis probes | Axis0-Axis6 readouts from the trajectory with controls and null reporting | M/L: 2-4 days | blocked if axis readouts are imported from parent tables instead of measured |
| 5 | assembled witness validator | one validator enforcing all four owner requirement parts | M: 1-2 days | blocked if any of the four parts is absent |
| 6 | optional substrate widening | QCA/surface/ring-checkerboard variant or 720 closure row | L: 3+ days | owner-choice or v1+ only |

Effort key: `S` = small, `M` = medium, `L` = larger bounded packet. These are design estimates, not commitments.

## Owner-Choice Points

1. Substrate: default v0 is chart-level finite Hopf/cell complex. Owner may require surface/QCA now, but that widens v0.
2. Topology4 meaning: current sources say `Se/Ne/Ni/Si`, not `sphere/torus/nested/Mobius`. If four distinct homology types are intended, that is a new owner choice before build.
3. Flux invariant: default v0 uses source-locked in/out chirality/sign rows. QCA open-chain index can become a v1 flux invariant, not the default v0 gate.
4. Ne policy: pure Hamiltonian circulation vs weak dissipator must be pinned for build.
5. Si projector frame: v0 needs one declared projector/strata convention.
6. Finite-time policy: v0 needs one declared `tau`/step-size policy.
7. Closure: density-level loop closure is enough for smallest v0 unless spinor-level 720 closure is promoted to a v0 gate.
8. Matrix64: v0 uses the sixteen chart-locked stages. Full `8 terrains x 8 signed operators = 64` runtime traversal is v1+ unless explicitly required.

## Final Design Verdict

Build the assembled engine v0 as a tiny source-locked chart object first:

`8 TerrainSpace objects -> 16 StageRegion objects -> 2 independent engine trajectories -> Axis0-Axis6 trajectory probes`.

That is the smallest version that satisfies all four owner requirement parts. Anything smaller drops one of the required parts and is below the "simmed" bar. Anything larger, especially QCA/locality or full Matrix64 runtime closure, is valuable but belongs after the first assembled object exists.
