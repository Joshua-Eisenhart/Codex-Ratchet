# True-State Map - codex2 - 2026-06-12

## Bottom line

Against the owner architecture in `0ff763858` plus the GCM re-anchor in `393c5147a`, the assembled object is still **0/4 parts admitted** and **0/33 top-level required objects admitted on a carved `M(C)`**: 0/8 terrain regions, 0/16 resident stage regions, 0/2 traversing engines, and 0/7 axis probe families measured on those engines.

The repo does have real feedstock. The honest reusable-machinery estimate is still about **20-35%**, with a center estimate near **30% effort reuse**, but that is not architecture completion. The current gap is assembly and re-anchoring: existing complexes, operators, dynamics, welds, and audits have to be rebuilt as strata, regions, traversals, and probes of a constraint-carved `M(C)`.

The closest new frontier is `system_v6/sims/gcm_constraint_carve_v0/`, but it is **local and untracked**, not landed. Its result file reports a first carve candidate with 125 carrier states, 8 survivors, and 4 quotient classes; it also reports only a partial macro-terrain match, not the 4-family/8-realization terrain atlas.

## Evidence boundary

Fresh checks in this lane were read-only except this receipt. I checked `git status --short`, the binding commits `0ff763858`, `393c5147a`, `100653354`, `16597b231`, the named receipts, and the existing JSON/result files under the untracked frontier dirs. I did not run validators or mutate git state.

Route truth: this is controller/local-tool synthesis only. No Codex-native subagent or council receipts are claimed for this lane.

## 1. Four requirement parts

Reference target: `100653354` defines the assembled-engine ladder and the smallest v0 as `8 TerrainSpace objects -> 16 StageRegion objects -> 2 independent engine trajectories -> Axis0-Axis6 trajectory probes`. `393c5147a` changes the first rung: terrain spaces must be read off a constraint-carved `M(C)`, not hand-built as scenery.

| Part | Current admitted architecture coverage | Genuine feedstock toward it | Feedstock coverage estimate | Missing for owner architecture | Build distance from today | Evidence |
|---|---:|---|---:|---|---|---|
| 1. Eight terrains as regions/spaces of carved `M(C)` | `0/8 = 0%` admitted. The first carve has 4 quotient classes, not 8 terrain regions. | `gcm_constraint_carve_v0` local candidate; `terrain_generator_sheet_packet` (`d8e035186`); `terrain_operator_precedence_64_matrix` (`38bdd65de`); Family B Hopf-torus object (`29e133f2f`, `1eba97ac2`); cover/topology certificates (`cc2f61b2a`, `2964cdd64`). | About `35-45%` reusable machinery for constructing/certifying regions; `0%` admitted terrain coverage. | Pin accepted carrier and constraint set `C`; compute and audit `M(C)`; derive regions from survivors; show the 8 terrain realizations or explicitly revise the terrain atlas; give each region certificates and controls. | Serial first: land or replace `gcm_constraint_carve_v0`. Then old rung 1 from `100653354` becomes 1-3 focused days if the partial macro match is accepted/refinable. If the carve genuinely does not match the atlas, add an unknown refinement loop, likely 2-6 focused days per carrier/constraint redesign. | `0ff763858` requirement receipt; `393c5147a` re-anchor receipt; `100653354` design ladder; `gcm_constraint_carve_v0/results/gcm_constraint_carve_v0_envelope_results.json` says 125 states, 8 survivors, 4 quotient classes, `terrain_atlas_not_claimed:true`; `git status` shows this dir untracked. |
| 2. Sixteen stages as regions/charts with resident operators | `0/16 = 0%` admitted. Local 16-stage packet is a mismatch diagnostic, not admission. | `source_locked_operator_base_packet` (`95627d803`); `terrain_generator_sheet_packet` (`d8e035186`); `terrain_operator_precedence_64_matrix` (`38bdd65de`); local `engine_16_stage_definition_correspondence_v0`. | About `35-50%` reusable operator/stage formula feedstock; `0%` admitted stage-region coverage. | Define `StageRegion` objects inside carved terrain regions; prove operator residency on those regions; settle substage convention; show operators preserve, move, or exit regions as claimed; rerun controls on `M(C)`. | Depends on Part 1. Once terrain regions exist, `100653354` rung 2 is still plausibly 1-2 focused days for a v0, but only after the carve/region schema is fixed. | `100653354` stage table; local `engine_16_stage_definition_correspondence_v0/results/engine_16_stage_definition_correspondence_v0_envelope_results.json` reports `correspondence_result:"MISMATCH"`, 16 defined stages, 12 distinct defined components, 16 discovered components, 0 exact matches; `git status` shows the packet untracked. |
| 3. Two engines as running traversals over stages | `0/2 = 0%` admitted. No L/R engine currently traverses carved `StageRegion`s. | `engines_run_with_axes_v0` (`de243459e`); `manifold_super_sim_v2_weld` (`d6815079e`); two-engine/readout source lock named by `gcm_constraint_carve_v0` (`dd9ec4999`); `100653354` L/R MAX/min traversal design. | About `20-30%` reusable dynamics/transport machinery; `0%` admitted engine coverage. | Build engine state objects on carved stage regions; implement L/R MAX/min loops over those regions; prove closure/liveness or report exits; record trajectory IDs and transports. | Depends on Parts 1-2. `100653354` rung 3 stays about 2-3 focused days for a v0 after stage residency exists. L/R engines can be built partly in parallel after the common transport contract is fixed. | `100653354` engine table; `de243459e` full 33-row Carnot-stroke baseline with caveats; `d6815079e` finite chart-to-chart weld bookkeeping; `0ff763858` says engines were not run as engines in the owner sense. |
| 4. Axes measured on the running object | `0/7 = 0%` admitted. Axis work exists, but not on carved engine trajectories. | `manifold_dynamic_chart_v0` (`d6031772a`, `eb51339c0`); `manifold_dynamic_chart_v1` (`1231dbbd9`); local `manifold_dynamic_chart_v2`; `engines_run_with_axes_v0` (`de243459e`); axis probe acceptance design in `100653354`. | About `25-35%` reusable probe/control protocol; `0%` admitted axis coverage. | Attach Axis0-Axis6 probes to actual trajectory rows `(engine_id, stage_id, region_id, time/window)`; include controls and null outcomes; rerun chart-v2-style separations on carved survivor states instead of a side carrier. | Depends on Parts 1-3. `100653354` rung 4 remains 2-4 focused days after engine trajectories exist; axes can fan out by family once the trajectory table is stable. | `100653354` Axis0-Axis6 table; local `manifold_dynamic_chart_v2/results/manifold_dynamic_chart_v2_envelope_results.json` reports `separation_found`, 115 earned rows, but `claim_ceiling:scratch_diagnostic_axis0_experiment_v2_no_admission`; `git status` shows v2 untracked. |

Composite score: **architecture admitted = 0/33 = 0%**. Feedstock score: **about 30% reusable effort**, not a completed fraction of the owner object.

## 2. S1-S11 layer map

This map uses `system_v6/receipts/geometry_program_status_20260611.md` as the layer inventory, then re-asks whether each layer can become a stratum of a carved `M(C)`.

| Layer | Scratch earned now | Can attach as a stratum of carved `M(C)`? | Nesting status | What attaching requires | Evidence |
|---|---|---|---|---|---|
| S1 exactness / Hopf / qubit floor | Real scratch exactness and qubit-ladder feedstock. | Yes, but only as carrier/coordinate structure after a map from `M(C)` survivor classes to the S1 coordinates exists. | Genuine nesting evidence exists in Hopf fiber/base and qubit ladder families, but it is not yet nested under carved `M(C)`. | Define the carrier map from survivor or quotient classes into the S1 coordinate object; show exactness survives quotienting. | Geometry status S1 commits `6489a6929`, `e02c8a9d`, `6ed5e961e`, `afd38093c`, `5dacc1eff`, `b27d22317`, `236b33b5d`, `53bff741b`, `8a0b9e9d3`, `e0eb52ec3`, `f578b7181`; `393c5147a` requires carved origin. |
| S2 connection / flux / foliation | Real positive and negative models, mode sweep, two/three-shell ratchets. | Yes if carved regions admit leaves, shells, or induced connections. | Genuine nesting evidence: fixed-eta disintegration, iterated disintegration, and shell ratchets. | Compute induced leaves/shells on `M(C)` survivors; recompute flux/connection on those leaves, not on imported side spaces. | Geometry status S2 commits `5d8a6f1de`, `f023ebe16`, `529f1a918`, `6ba8b7d6c`, `15b1d1899`, `de783dc79`; disintegration tower commits `a0a673e93`, `b79036b1f`, `8a46c8627`. |
| S3 density / observable | Density/observable packets exist; first carve uses a 33-cell Bloch-ball density subcarrier. | Strongly attachable, but current use is carrier-relative, not full manifold admission. | Mostly carrier-side, not a nested stratum yet. | Define density observables as quotient/probe fields over `M(C)`; show controls bite and survive refinement. | Geometry status S3 commits `1badd60d4`, `028bcb0ca`; local `gcm_constraint_carve_v0` result reports `density_subcarrier_count:33`. |
| S4 operators | Source-locked and diagnostic operator formulas exist. | Yes after stage residency exists. | Mostly side-by-side formulas; no standalone S4 ratchet. | For each resident stage region, prove operator domain/codomain, preservation/transition, and noncommutation on carved states. | Geometry status S4 commits `cff1d7e3f`, `307b8ddf1`, `028bcb0ca`; `source_locked_operator_base_packet` (`95627d803`); `terrain_operator_precedence_64_matrix` (`38bdd65de`). |
| S5 terrain generators | Terrain generator formulas and sheet packets exist. | Yes, but only if regions are read from `M(C)` first. | Mostly side-by-side terrain catalog today. | Derive terrain generator action on survivor regions; do not relabel hand-built terrain flows as carved regions. | Geometry status S5 commits `d26b49f59`, `6ba8b7d6c`, `76597c8a8`, `826e716d1`; `terrain_generator_sheet_packet` (`d8e035186`); `393c5147a` explicitly rejects scenery-first terrain admission. |
| S6 stacked terrain / operator / Hopf | Stacked terrain/operator/Hopf feedstock exists. | Yes after S1/S2/S4/S5 are attached to the same carved object. | Partial genuine nesting through shell/order ratchets; still not a single `M(C)` stack. | Build one object where Hopf coordinates, shell leaves, terrain regions, and operators share the same survivor IDs. | Geometry status S6 commits `7dc512454`, `62cd3921a`, `76597c8a8`, `826e716d1`; disintegration/shell evidence `a0a673e93`, `b79036b1f`, `8a46c8627`. |
| S7 finite discretization / topology | Real finite certification, cover, SNF/homology feedstock. | Yes as the finite witness layer for `M(C)` or for refinements of it. | Genuine finite-topology evidence, but sidecar until applied to the carved survivor quotient. | Run the certification pattern on the carved quotient/regions; record Betti, H1, components, controls, and refinement behavior. | Geometry status S7 commits `3e8fc4c8d`, `9ce356bd4`, `ece5fa4ae`, `62cd3921a`; `fiber_augmented_cover_v2` (`cc2f61b2a`); `topology_parity_guard_v3` (`2964cdd64`) with independent SNF H1=`Z/3`. |
| S8 three-spinor / Clifford floor | Three-spinor and Clifford scratch floor exists. | Possibly, but not required for the smallest assembled v0 unless selected as the carrier. | Genuine qubit/Clifford ladder evidence; not nested under `M(C)` yet. | Show the carved carrier lifts into or is generated by the three-spinor/Clifford floor; otherwise keep it optional. | Geometry status S8 commits `0bd1cdf8`, `3a53d16af`, `30d21022e`, `4047dc73b`, `0f47decd5`, `70fe9aa68`, `08037882e`, `56e0376ed`. |
| S9 division algebra / nonassociative containment | Division algebra and Hopf-containment scratch exists. | Optional/conditional for first v0; it can attach only if the carved object selects that algebraic carrier. | Genuine containment evidence exists, especially Hopf containments, but currently beside the carve. | Prove the S9 carrier is induced by or faithfully hosts `M(C)`; otherwise use it as a later widening lane. | Geometry status S9 commits `33dc2323f`, `17d4698ab`, `c668fe9ae`, `a5637cb0f`, `6c356d275`; status names S9 Hopf containments. |
| S10 G-structure | G-structure and G2-family scratch exists. | Not for first v0 unless S9/S8 carrier choice forces it. | Mostly side-by-side structural catalog today. | First attach S8/S9 to `M(C)`; then compute any induced G-structure and controls on the carved object. | Geometry status S10 commits `77a4f5d19`, `b5649217c`. |
| S11 `M(C,t)` / dynamic carved manifold | Scratch/advisory M(C,t) work exists. The new carve has a small C-to-C-prime hook. | This is now the dynamic extension of the core object, but not yet built. | Advisory only; current `gcm_constraint_carve_v0` hook is a first transition, not a dynamic manifold. | After `M(C)` is admitted, define time/update law on survivor states and quotient classes; rerun stability, leakage, basin, and terrain-change checks. | Geometry status S11 commits `439624ec9`, `6c356d275`, `eee9a7c41`, `287084d80`; local `gcm_constraint_carve_v0` result reports `M(C,t)` hook with 4 survivors and 2 quotient classes under C5 orientation pin. |

Layer verdict: the nesting evidence is real in several lanes, especially the disintegration tower, shell ratchets, S9 Hopf containments, and qubit ladder. The missing move is not "more catalog." It is attaching those nested structures to one carved object with shared survivor/quotient/region IDs.

## 3. Feedstock ledger

The 20-35% estimate is precise in this sense: these artifacts can reduce build effort, but none currently counts as an admitted terrain/stage/engine/axis object on carved `M(C)`.

| Reusable machinery | What is reusable | What it feeds in assembly | Current numeric gap | Evidence |
|---|---|---|---|---|
| Certified-complex pattern | Chain/cover/cell certification, independent recomputation discipline, admissibility gates. | Terrain-region certificates, quotient topology, stage-boundary certification, witness validator. | Reusable certification pattern exists; certified owner terrain regions remain `0/8`. | `fiber_augmented_cover_v2` (`cc2f61b2a`); `topology_parity_guard_v3` (`2964cdd64`); geometry status S7. |
| SNF / homology certification | Independent SNF recompute and torsion/Betti readouts. | Topological invariants for `M(C)` quotient, region boundary checks, negative controls. | H1 and Betti were proved for prior objects, not for current carved `M(C)`; carved homology rows are `0`. | `topology_parity_guard_v3` (`2964cdd64`) reports H1=`Z/3`, Betti `[1,0,0,1]`, lens-like `L(3,1)`; `axis_work_order_20260612.md` names the two instruments. |
| Operator formulas | Source-locked base operators, terrain generators, 64-cell precedence diagnostics. | `StageRegion.operator_set`, operator residency checks, noncommutation/order polarity tests. | Operator feedstock is real; resident operators on carved stages are `0/16`. | `source_locked_operator_base_packet` (`95627d803`); `terrain_generator_sheet_packet` (`d8e035186`); `terrain_operator_precedence_64_matrix` (`38bdd65de`); local 16-stage result has 0 exact matches. |
| Dynamics protocol | Perturb, watch, classify, control, and report nulls; v2 stability-axis sweep machinery. | Axis0-Axis6 probe rows measured on engine trajectories. | Dynamic chart v2 has 115 earned chart-relative rows, but admitted axes on engine trajectories are `0/7`. | `manifold_dynamic_chart_v0` (`d6031772a`, `eb51339c0`); `manifold_dynamic_chart_v1` (`1231dbbd9`); local `manifold_dynamic_chart_v2` result. |
| Transport / weld bookkeeping | Finite typed chart-to-chart weld accounting, SMT-flip controls, cross-family bookkeeping. | Engine traversal transports and region-to-region weld checks. | Weld bookkeeping exists; engine trajectory transports over carved stages are `0/2` engines. | `manifold_super_sim_v2_weld` (`d6815079e`) says A+B weld earned as finite chart-to-chart bookkeeping, not a surface-level manifold. |
| Engine readout baseline | Carnot-stroke style run rows and classical baseline discipline. | Two engine loops and trajectory tables. | A run baseline exists, but no run is over carved `StageRegion`s. | `engines_run_with_axes_v0` (`de243459e`); `100653354` L/R engine traversal table. |
| Existence-test battery | Positive/negative controls, empty/overconstrained controls, source locks, multi-engine agreement fields. | First-carve admission gate, terrain mismatch diagnosis, witness gates A-E. | Local first carve reports controls biting and validator ok, but it is untracked and unaudited; admitted carve object remains `0`. | `gcm_constraint_carve_v0/results/gcm_constraint_carve_v0_envelope_results.json`; `100653354` witness gates; `393c5147a` constraint-carve rule. |
| Audit instruments | Validity campaign, family audits, validator surfaces, do-not-promote discipline. | Keeps scratch, shallow, fake, and admitted claims separate while assembly work proceeds. | Packet validity was about 60%; owner manifold completion remains 0%. | `validity_campaign_synthesis_20260612.md` (`16597b231`) reports about 60% valid scratch at ceilings; `0ff763858` says genuine feedstock about 20-35% and assembled manifold 0%. |
| Nested-strata feedstock | Disintegration tower, shell ratchets, Hopf containments, qubit ladder. | Later strata of `M(C)`: leaves, shells, carrier coordinates, optional S8-S10 widening. | Genuine nesting exists, but shared IDs with carved `M(C)` are not built. | Geometry status disintegration tower `a0a673e93`, `b79036b1f`, `8a46c8627`; S8/S9 commit rows in geometry status. |

## 4. Frontier state

| Item | Landed or in flight? | What exists now | What it becomes after manifold exists | Evidence |
|---|---|---|---|---|
| `gcm_constraint_carve_v0` | In flight. Local/untracked, not landed. | First computed-carve candidate: 125 carrier states, 33 density-subcarrier cells, constraints C1-C4, 8 survivors, 4 quotient classes, all three engines agree, validator result ok. Terrain readout is partial macro match only. | Either the first accepted `M(C)` foundation or a killed/refined carrier/constraint attempt. If accepted, its survivor and quotient IDs become the substrate for terrain regions, stages, engines, and axes. | `git status --short` shows `?? system_v6/sims/gcm_constraint_carve_v0/`; build card says scratch diagnostic and no git add/commit; result JSON says `not_THE_manifold:true`, `promotion_allowed:false`, `terrain_atlas_not_claimed:true`. |
| `gcm_constraint_carve_floor_v0` | In flight. Local/untracked, not landed. | Smaller floor candidate: 24 states, 6 survivors, 6 singleton quotient classes, one connected six-state finite object, no 8 terrain regions. | A floor/negative-control lane or reduced carrier diagnostic, not the assembled object by itself. | `git status --short` shows `?? system_v6/sims/gcm_constraint_carve_floor_v0/`; result JSON reports one connected six-state object and no 8 terrain regions. |
| `manifold_dynamic_chart_v2` | Parked/in flight. Local/untracked, not landed. | Axis0 experiment v2 finds chart-relative separation: 115 earned rows out of 960 sweep rows, but ceiling is scratch diagnostic and no Axis0 admission. | Rerun the protocol on carved survivor states and engine trajectories. It becomes an axis-probe candidate only after `(engine_id, stage_id, region_id, time/window)` rows exist. | `git status --short` shows `?? system_v6/sims/manifold_dynamic_chart_v2/`; result JSON says `positive_boundary_result:"separation_found"` and `claim_ceiling:scratch_diagnostic_axis0_experiment_v2_no_admission`. |
| `engine_16_stage_definition_correspondence_v0` | Parked/in flight. Local/untracked, not landed. | Proposed 16 macro-stage finite maps do not match discovered components: 16 defined stages, 12 distinct defined components, 16 discovered components, 0 exact matches. | Rebuild stage definitions as resident regions/operators on carved `M(C)`. Current mismatch becomes a useful falsifier and convention-pin source, not a stage object. | `git status --short` shows `?? system_v6/sims/engine_16_stage_definition_correspondence_v0/`; result JSON says `correspondence_result:"MISMATCH"` and `perfect_bijection:false`. |
| Chart v2's unclaimed separation | Parked. | It is a real chart-relative separation experiment, but substrate choice remains open and identity-leak risk/control issues are explicitly fenced. | After `M(C)` exists, it should be rerun as Axis0/axis-family measurement over carved trajectories, with the old chart carrier only as a comparison/control. | Local v2 result disallows Axis0 admission, bridge, physics, canonical Axis0, manifold promotion, final substrate choice, spinor-network surface closure, and QCA/local-update closure. |
| The 16-stage packet | Parked. | It is a negative correspondence/proposal packet with 0 exact matches to discovered components. | After `M(C)` exists, the packet's operator formulas and convention choices can seed a resident-stage rebuild; the current 16 labels should not be assumed correct. | Local 16-stage build card fences it as proposal only; result JSON disallows engine-stage, Matrix64, QIT-engine, axis, bridge, manifold, and physics admission. |

## 5. Distance to first assembled v0

Smallest target remains: one carved `M(C)` satisfying the owner four-part architecture, with terrains, stages, engines, and axes all attached to that same object.

| Rung | Status today | Serial or parallel | Honest effort from today | Unknowns | Evidence |
|---|---|---|---|---|---|
| R0. Design and acceptance shape | Done as design, not implementation. | Serial/controller. | Already present. | None for design; implementation may still revise details. | `100653354` design receipt; `0ff763858` owner requirement. |
| R1a. Pin carrier and constraints, compute first accepted `M(C)` | Local candidate exists but is untracked and unaudited. | Serial foundation. Other work can scout, but cannot replace this gate. | 1-3 focused days if current `gcm_constraint_carve_v0` is accepted after audit or lightly repaired. | The terrain question is live: current carve has 4 quotient classes and partial macro terrain match, not full atlas. | `393c5147a` re-anchor receipt; local `gcm_constraint_carve_v0` result; `git status` untracked. |
| R1b. Read terrain regions from `M(C)` | Not done. | Mostly serial until region schema is fixed; region certification can parallelize afterward. | 1-3 focused days after accepted carve. Add 2-6+ days per failed carrier/constraint redesign loop. | The carved structure may not match the atlas. If so, options are refine `C`, refine carrier, weaken/restate terrain atlas, or accept a different first v0. Owner choice may be needed if multiple readings survive. | `393c5147a` says terrains must be read off survivors; `gcm_constraint_carve_v0` says `terrain_atlas_not_claimed:true`. |
| R2. Build 16 resident `StageRegion`s and operators | Not done; current local packet mismatches. | Parallel by terrain/stage once region IDs exist; shared schema serial. | 1-2 focused days after R1. | Operator residency may fail for some regions; substage convention may not align with carved quotient. | `100653354` rung 2/stage table; local 16-stage result reports `MISMATCH` and 0 exact matches. |
| R3. Run two engines as traversals | Not done. | L/R can parallelize after common transport and stage schema; trajectory ledger serial. | 2-3 focused days after R2. | Traversals may exit, collapse, or fail independence on carved regions. | `100653354` rung 3/engine table; `de243459e` and `d6815079e` are feedstock only; `0ff763858` says engines were not run as engines. |
| R4. Measure Axis0-Axis6 on trajectories | Not done. | Parallel by axis family after trajectory table exists. | 2-4 focused days after R3. | Chart-v2 separation may not survive carved trajectory controls; substrate choice remains open. | `100653354` rung 4/axis table; local chart v2 result says no Axis0 admission. |
| R5. Assembled witness validator and audit | Not done. | Serial admission gate with parallel pre-audit possible. | 1-2 focused days after R4. | Validator may expose missing lineage, stale hashes, weak controls, or packet-result mismatch. | `100653354` witness gates A-E; `16597b231` validity campaign shows packet validity is not manifold admission. |

Optimistic distance if the current carve is accepted/refined locally: about **7-13 focused days** to a first assembled v0. If the carve/terrain mismatch is real, the honest range becomes **10-20+ focused days**, because R1 becomes an unknown loop rather than a fixed build step.

Parallelizable work now, without pretending R1 is solved:

- Audit `gcm_constraint_carve_v0` and `gcm_constraint_carve_floor_v0` independently.
- Prepare region-certificate templates using the certified-complex and SNF machinery.
- Prepare operator residency tests using the source-locked operator base.
- Prepare dynamic-axis protocol wrappers that wait for carved trajectory IDs.
- Prepare do-not-promote validators for chart-v2 and 16-stage reruns.

Serial gates:

- Accepting or rejecting the first `M(C)` carrier/constraint set.
- Choosing what to do if carved terrain regions do not match the atlas.
- Writing the canonical result/receipt and git checkpoint, if/when authorized.

## 6. What no current evidence supports

Do not say the assembled manifold/engine exists. The owner object is still `0/4` admitted and `0/33` top-level objects admitted on carved `M(C)` (`0ff763858`, `393c5147a`, `100653354`).

Do not say packet-level validity is manifold completion. The validity campaign found about 60% valid scratch at ceilings, while the owner architecture receipt says assembled manifold admission is 0% and genuine feedstock is about 20-35% (`16597b231`, `0ff763858`).

Do not say terrain spaces are landed as regions of `M(C)`. Current `gcm_constraint_carve_v0` is untracked, scratch, and reports partial macro match but no full terrain atlas.

Do not say the 16 stages are real stage regions. The local 16-stage correspondence packet reports 0 exact matches and is proposal-only.

Do not say engines ran as owner engines. Existing runs and welds are useful feedstock, but no engine traverses carved resident stages.

Do not say Axis0 or any axis is admitted. Chart v2 found a chart-relative separation, not an axis measured on a running carved engine.

Do not say hand-built terrain complexes are acceptable substitutes after the GCM re-anchor. `393c5147a` requires the constraint set and the carved survivor object.

Do not say `gcm_constraint_carve_v0` is THE manifold, canonical, committed, audited, or promoted. Its own result says `not_THE_manifold:true`, `promotion_allowed:false`, `formal_admission_allowed:false`, and `carrier_and_pins_relative:true`.

Do not say chart v2 chose the substrate. Its own result keeps substrate choice open and disallows manifold promotion.

Do not say the 16-stage packet matched. It reports `MISMATCH`, `perfect_bijection:false`, and 0 exact matches.

Do not say the 64 matrix or any packet alone equals the assembled object. The owner requirement is an object with terrain regions, resident stages, traversing engines, and axis probes on those trajectories.

Do not say the b6 law is supported. The topology/cover audits explicitly fence unsupported b6-style claims.

Do not say stale hash validators prove freshness. For admission, run fresh commands and cite exact outputs.

Do not say S8/S9/S10 algebraic carriers are forced by the root constraints or required for first v0. They are real feedstock and possible widening strata, not current foundation proof.

Do not say there is no work. There is real feedstock, real diagnostics, and a local first-carve candidate. The failure is not fabrication; it is that the owner architecture has not yet been assembled on a carved `M(C)`.

## Checked artifacts

- `git status --short`: frontier dirs are untracked: `gcm_constraint_carve_v0`, `gcm_constraint_carve_floor_v0`, `manifold_dynamic_chart_v2`, `engine_16_stage_definition_correspondence_v0`.
- `git show` for `0ff763858`, `393c5147a`, `100653354`, `16597b231`.
- `system_v6/receipts/owner_architecture_requirement_20260612.md`.
- `system_v6/receipts/gcm_reanchor_requirement_20260612.md`.
- `system_v6/receipts/assembled_engine_v0_design_20260612.md`.
- `system_v6/receipts/validity_campaign_synthesis_20260612.md`.
- `system_v6/receipts/geometry_program_status_20260611.md`.
- Local frontier result files under the four untracked dirs named above.
