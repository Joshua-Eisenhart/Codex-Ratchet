# Codex Ratchet Sim Build Plan

Status: MASTER REFERENCE PLAN — not the live queue surface. Use `docs/plans/sim_backlog_matrix.md` for the live queue, `docs/plans/sim_truth_audit.md` for truth labels, `docs/plans/tool_integration_maintenance_matrix.md` for tool depth, and `docs/plans/controller_maintenance_checklist.md` for live run operations.

> For Hermes: use this plan to build the sim estate in bounded phases. Do not collapse `exists`, `runs`, `passes local rerun`, and `canonical by process`.

Goal: build the simulation stack in the documented order, with the classical engine lane kept separate from the geometry-manifold lane, and with promotion gates tied to process-compliant tool integration.

Architecture: this plan uses two coordinated lanes. Lane A builds classical Carnot/Szilard baselines clearly and fully, then bridges them into the system only after the bridge objects are ready. Lane B builds the geometric constraint manifold from carrier admission upward, decomposing geometry into explicit local legos on the same admitted carrier before any late bridge or axis work. Both lanes share the same truth labels, tool-honesty rules, and negative-test requirements.

Tech stack: PyTorch, z3, cvc5, sympy, clifford, geomstats, e3nn, rustworkx, XGI, TopoNetX, GUDHI, PyG, hypothesis/pytest/pydantic where relevant, existing `system_v4/probes/SIM_TEMPLATE.py` contract, repo docs in `new docs/`.

---

## 0. Authority and non-negotiable rules

Use these docs first:
- `new docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `new docs/LLM_CONTROLLER_CONTRACT.md`
- `new docs/07_model_math_geometry_sim_plan.md`
- `new docs/08_aligned_sim_backlog_and_build_order.md`
- `new docs/16_lego_build_catalog.md`
- `new docs/17_actual_lego_registry.md`
- `new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md`
- `new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md`

Plan-wide rules:
1. Use standard mathematical terms in sims and result files. Do not use engine shorthand as the computation surface.
2. Keep the build order: constraint/probe -> carrier -> geometry -> operators/channels -> bipartite/correlation -> entropy -> axes.
3. Geometry is not one task. Each concrete geometry object gets its own bounded lego or explicit grouped packet with named sub-results.
4. Classical engine work is a baseline lane, not permission to skip the geometry lane.
5. A result is not `canonical by process` unless it satisfies the current process rules, including tool manifest honesty and at least one nontrivial load-bearing tool outside the numeric baseline.
6. The geometry-manifold lane is the spine. Complete the full local geometry stack first, then layer those admitted geometries on each other and run coexistence/stacking work on that spine before any axis work.
7. Flux is an open derived candidate family, not a primitive. It may enter only after its dependency chain is built through carrier, geometry, transport, chirality/differential machinery, and negatives.
8. Tool use must be actively expanded and maintained. Presence/import is not enough; recurring maintenance work must keep the newer tools from regressing back to decorative use.
9. Pairwise/coexistence work comes only after the local lego is real.
10. Every batch must include positive, negative, and boundary tests.
11. Multi-track execution is expected: use bounded subagent workstreams for independent audits, tool-integration passes, and lane-separated sim packets, but keep one controller truth surface and one queue.
12. System cleanliness is part of the work: routing, manifests, validators, and stale-classification cleanup must be maintained alongside new sims.

Truth labels to use everywhere:
- `exists`
- `runs`
- `passes local rerun`
- `canonical by process`

---

## 1. Lane split

### Lane A: Classical engine lane

Purpose:
- simulate Carnot and Szilard engines fully and clearly as classical/QIT baseline systems
- make the thermodynamic and information-theoretic mechanics explicit in both directions of the loop, not just one forward summary
- make the mechanics deep and nuanced: staged heat/work bookkeeping, irreversible and finite-time variants, ordered substeps, failure modes, topology-sensitive and graph-sensitive variants
- then build bounded bridge sims from those baselines into the system geometry

Objects in scope:
- Carnot engine and refrigerator loops, each run as full closed loops in both directions
- hot isotherm / cold isotherm / adiabatic segments, finite-time and irreversibility sweeps, hold-policy and asymmetric variants
- Szilard / Landauer loops with explicit measurement, memory, feedback, reset, wrong-order and blind-reset negatives, plus bidirectional protocol variants
- graph/proof/topology alignment of the baseline family where the claim genuinely depends on those structures
- later bridge objects connecting the engine lane to Weyl/geometry objects and extracting useful mechanics for the QIT engine family

Required outputs for this lane:
- one forward-loop packet and one reverse-loop packet for Carnot
- one forward-loop packet and one reverse-loop packet for Szilard/Landauer
- per-stage and per-substep mechanics, not only aggregate endpoint summaries
- explicit statement of which behaviors transfer to the QIT engine family and which fail because of topology or admissibility differences

Not in scope for this lane:
- treating Carnot/Szilard baseline outputs as direct proof of the geometric manifold
- using engine-lane completion to skip local geometry legos

### Lane B: Geometry-manifold lane

Purpose:
- simulate the full documented geometric constraint manifold layer by layer on the same admitted carrier
- treat this lane as the spine of the super-sim: once the local layers are real, they can be stacked, nested, and run on each other as a constrained whole
- keep the geometry decomposed into explicit math objects
- use the full proof/graph/topology/tool stack in the actual execution path

Spine objects to make explicit before any axis work:
- finite carrier and density-state admission
- `S^3` spinor carrier
- Hopf map `S^3 -> S^2`
- Hopf fibers and fiber equivalence under density-matrix measurements
- torus and nested-Hopf-torus geometry
- Clifford and spinor geometry
- left/right Weyl spinors running on the nested Hopf tori
- chiral density bookkeeping `rho_L`, `rho_R`, and joint local bookkeeping
- Pauli matrices/operators acting on the left/right Weyl layer
- loop laws, connection form, holonomy, and transport grammar
- differential/chirality machinery and candidate flux only as a derived downstream layer

Additional objects in scope:
- graph, hypergraph, cell-complex, persistence geometry
- metric/phase geometry families: Bures, Fubini-Study, Berry, Berry curvature, QFI, QGT, transport/holonomy
- operator and channel geometry compatibility
- local bipartite/correlation legos below bridge promotion

Not in scope for this lane until later:
- broad bridge closure claims
- entropy-first summaries
- axis promotion before lower layers are real

---

## 2. Build phases

## Phase 1: Process repair, inventory freeze, and maintenance surface

Objective: create a clean execution surface before new sims are added, and make tool/process maintenance a recurring part of the system rather than an afterthought.

Deliverables:
- one machine-readable sim backlog grouped by lane, layer, and lego id
- one current-state audit marking each candidate as `exists`, `runs`, `passes local rerun`, or `canonical by process`
- one gap list for files that claim canonical status but fail current process rules
- one tool-integration maintenance matrix tied to the newer tool stack
- one recurring controller-maintenance checklist for manifests, validators, stale classifications, and queue hygiene

Files to create/update:
- Create: `docs/plans/sim_backlog_matrix.md`
- Create: `docs/plans/sim_truth_audit.md`
- Create: `docs/plans/sim_process_gap_log.md`
- Create: `docs/plans/tool_integration_maintenance_matrix.md`
- Create: `docs/plans/controller_maintenance_checklist.md`
- Create: `docs/plans/wiki_ingest_and_lego_maintenance.md`

Required checks:
- confirm every active target maps to `07`, `08`, `16`, and `17`
- separate Lane A and Lane B explicitly
- identify legacy result files that are useful but not promotion-grade
- tie claims to the repo's current tool-role contract in `new docs/TOOLING_STATUS.md`, `new docs/TOOL_MANIFEST_AUDIT.md`, and `new docs/LLM_RESEARCH_GAP_MATRIX.json`
- keep validator surfaces in play, including `system_v4/skills/llm_research_enforcement_validator.py`
- treat `new docs/16_lego_build_catalog.md` and `new docs/17_actual_lego_registry.md` as living maintenance surfaces that must be updated as new docs appear and sims land
- keep the wiki in sync with the current-docs lane by ingesting new/updated docs and sim-result-facing summaries as they are produced
- use the wiki as an active research surface during execution, not only as an archive after the fact

Exit gate:
- no new sim work starts until the backlog is split into Lane A / Lane B, each row has a build stage and truth label, and the recurring maintenance surfaces exist

---

## Phase 2: Carrier and root-admission legos

Objective: make the lower substrate explicit and stable.

Primary Lane B targets:
- `constraint_probe_admissibility`
- `carrier_admission_density_matrix`

Math objects:
- finite state/probe families
- admissibility fences
- `H = C^2`, `D(C^2)`, positivity, trace-one normalization
- probe-relative distinguishability and noncommutation boundaries

Preferred tools:
- load-bearing: `z3`, `pytorch`
- supportive: `cvc5`, `sympy`

Required sim behaviors:
- prove or disprove admissibility with explicit constraint checks
- keep the same carrier fixed while later geometry is layered on top
- emit exact failure reasons for rejected carrier/probe variants

Exit gate:
- at least one carrier-admission sim is `canonical by process`
- at least one root-admission/boundary sim reaches `passes local rerun`
- later geometry work uses this admitted carrier instead of silently redefining the state space

---

## Phase 3: Same-carrier geometry packet

Objective: exhaust the local geometry families on the admitted carrier before operator or bridge inflation, and explicitly build the spine chain from density states through `S^3`, Hopf, nested tori, Weyl, and Pauli action.

Primary Lane B targets:
- `carrier_admission_density_matrix`
- `sphere_geometry`
- `hopf_geometry`
- `torus_geometry`
- `nested_torus_geometry`
- `clifford_geometry`
- `spinor_geometry`
- `hopf_map_s3_to_s2`
- `hopf_fiber_equivalence`
- `hopf_connection_form`
- `fiber_loop_law`
- `base_loop_law`
- `berry_holonomy`
- `weyl_chirality_pair`
- `chiral_density_bookkeeping`
- `pauli_generator_basis`
- `left_right_asymmetry`
- `bures_geometry`
- `fubini_study_geometry`
- `berry_phase_geometry`
- `berry_curvature`
- `holonomy_geometry`
- `qfi_geometry`
- `qgt_geometry`
- `transport_geometry`

Required spine chain:
- density matrices on the admitted carrier
- `S^3` spinor carrier realization
- Hopf projection `S^3 -> S^2`
- nested Hopf torus stratification
- left/right Weyl spinors on the nested Hopf tori
- Pauli action on the left/right Weyl layer
- connection / loop / transport objects on that same carrier

Required design rule:
- hold one admitted carrier fixed and compare all geometry families on that same carrier

Preferred tools:
- load-bearing: `geomstats`, `clifford`
- strong supportive: `sympy`, `pytorch`, `z3`, `gudhi`
- optional where relevant: `e3nn`

Negative tests required in every geometry packet:
- carrier flattening
- metric smuggling
- real-only collapse
- flat-geometry-only collapse
- fiber/base loop swap
- torus scrambling or degenerate torus substitutions where relevant

Exit gate:
- one canonical same-carrier geometry packet covering Hopf/torus/Clifford/spinor families
- explicit sub-results for loop laws and connection/holonomy objects
- no entropy or bridge claims elevated from this phase alone

---

## Phase 4: Graph and topology geometry packet

Objective: encode the same admitted carrier and local geometry in graph-native and higher-order topological forms.

Primary Lane B targets:
- `graph_geometry`
- `hypergraph_geometry`
- `cell_complex_geometry`
- `persistence_geometry`
- `graph_shell_geometry`
- `hypergraph_shell_geometry`
- `dual_hypergraph_geometry`
- `state_class_binding_geometry`

Preferred tools:
- load-bearing: `xgi`, `toponetx`, `pyg`
- supportive: `rustworkx`, `gudhi`, `pytorch`

Required design rule:
- graph/topology encodings must be of the same lower admitted carrier, not free-floating unrelated structures

Negative tests:
- adjacency treated as metric distance
- path collapse
- topology-to-identity smuggling
- shell graph substitutions that destroy the preserved geometry

Exit gate:
- at least one graph-native canonical sim and one higher-order topology canonical sim
- clear statement of which structures survive graph/hypergraph/cell-complex translation and which do not

---

## Phase 5: Operator and channel admission

Objective: admit local operators and channels only after the carrier and geometry surface is stable.

Primary Lane B targets:
- `pauli_generator_basis`
- `clifford_generator_basis`
- `local_operator_action`
- `commutator_algebra`
- `left_right_asymmetry`
- `composition_order_sensitivity`
- `channel_cptp_map`
- `unitary_channel_map`
- `kraus_operator_sum`
- `lindbladian_evolution`
- `measurement_instrument`
- `povm_measurement_family`
- `blackwell_style_comparison`

Preferred tools:
- load-bearing: `clifford`, `sympy`, `z3`
- supportive: `pytorch`, `cvc5`, `e3nn`

Required design rule:
- operators act on already-admitted carriers/geometries; they do not silently choose a new ontology

Negative tests:
- commuting collapse
- symmetric-only left/right action
- composition-order erasure
- fake CPTP legality via normalization hacks

Exit gate:
- one canonical local operator packet
- one canonical local channel packet
- explicit local evidence for noncommutation and left/right asymmetry where claimed

---

## Phase 6: Weyl/chiral local packet

Objective: complete the chirality/differential layer locally before engine promotion or broad bridge claims, and only then test candidate flux as a derived family.

Primary Lane B targets:
- `weyl_chirality_pair`
- `chiral_density_bookkeeping`
- `terrain_family_fourfold` only if written in math-first channel language
- `loop_vector_fields`
- `engine_type_split`
- `placement_law`
- `composition_order_noncommutation`
- one explicit `flux_candidate_family` packet sourced from the documented dependency chain, only after the lower differential/transport/chirality objects are real

Preferred tools:
- load-bearing: `clifford`, `sympy`, `z3`
- supportive: `geomstats`, `pytorch`, `rustworkx`

Required caution:
- if a row is still phrased in system shorthand, rewrite the sim/result surface in proper mathematical language first

Exit gate:
- local chirality packet reaches at least `passes local rerun`
- any flux packet remains explicitly classified as a derived candidate family unless and until the dependency-chain and negative gates are met
- engine-family and placement work are still classified as local geometry/dynamics objects, not yet axis closure

---

## Phase 7: Bipartite and correlation local packet

Objective: build the local two-party objects needed before honest bridge and entropy work.

Primary targets:
- `partial_trace_operator`
- `reduced_state_object`
- `joint_density_matrix`
- `correlation_tensor_object`
- `schmidt_decomposition`
- `concurrence_measure`
- `negativity_measure`
- `werner_local_structure`
- local mutual/coherent information only as subordinate comparisons

Preferred tools:
- load-bearing: `gudhi` or `pyg` depending on claim, plus `pytorch`
- supportive: `sympy`, `z3`

Exit gate:
- local bipartite packet is real before any bridge-weighted or shell-history summaries are promoted

---

## Phase 8: Classical engine baseline packet

Objective: complete the side lane clearly, as a baseline lane.

Primary Lane A targets:
- Carnot baseline packet
- Szilard/Landauer baseline packet
- finite-time, irreversibility, ordering, reset, and substep variants as bounded extensions

Required cleanup:
- re-audit current engine result files that claim `canonical` but use no relevant nontrivial load-bearing tool
- downgrade or rebuild as needed under the current process rules

Preferred tools by role:
- `sympy` for exact thermodynamic identities and balance checks
- `z3`/`cvc5` for impossibility or ordering constraints where structurally relevant
- `rustworkx`, `xgi`, `toponetx`, `pyg`, `gudhi` for graph/proof/topology variants when the claim is explicitly about that structure
- `pytorch` if the computation substrate is to be promotion-grade

Required outputs:
- one explicit Carnot packet that stays classical/QIT-first
- one explicit Carnot reverse/refrigerator packet with equally explicit loop mechanics
- one explicit Szilard/Landauer packet that stays classical/QIT-first
- one explicit reverse or inversion-sensitive Szilard packet where the order logic is stressed in the opposite direction
- each packet clearly distinguishes baseline thermodynamic findings from later bridge findings
- each packet includes stagewise/substep mechanics, not only endpoint efficiency or information-balance summaries
- each packet attempts deeper PyTorch use and tries to make graph/proof/topology tools load-bearing where the claim supports it

Exit gate:
- engine baselines are process-honest, mechanically rich in both directions, and clearly separated from system-geometry claims

---

## Phase 9: Bridge packet from engines into system geometry

Objective: bridge the completed classical baselines into the admitted local system geometry, without skipping lower layers.

Inputs required before start:
- Phase 3 geometry packet complete
- Phase 6 chirality packet at least `passes local rerun`
- Phase 8 engine baseline packet process-clean

Allowed bridge scope:
- compare baseline engine families against local Weyl/geometry objects
- test bounded bridge objects only
- keep bridge meaning open unless the bridge-specific gates are met

Forbidden in this phase:
- axis closure claims
- entropy treated as primitive
- using bridge success to rewrite lower-layer ambiguity as solved canon

Exit gate:
- bridge files exist and run, but promotion remains narrow and object-specific

---

## Phase 10: Entropy and axis work only after lower-layer admission

Objective: make entropy and axis work late and subordinate.

Prerequisites:
- Phases 2 through 9 complete to the required gate level

Targets:
- local entropy family cross-checks on fixed state sets
- later bridge-weighted or shell-history summaries only after honest bridge objects exist
- axis families only after lower objects are admitted and negatively tested

Exit gate:
- none by default; this phase is explicitly blocked until lower packets are real

---

## 3. Required execution format for every new sim

Each new sim should be built from `system_v4/probes/SIM_TEMPLATE.py` and must include:
- classification field
- tool manifest with `tried`, `used`, and non-empty `reason`
- tool integration depth with `load_bearing`, `supportive`, or `None`
- positive tests
- negative tests
- boundary tests
- failure reasons
- artifact paths
- explicit statement of build stage and lane

Minimum metadata additions recommended for this repo:
- `lane`: `classical_engine` or `geometry_manifold`
- `build_phase`: one of the phases in this plan
- `lego_id` or `lego_ids`
- `same_carrier_reference`: explicit pointer to the carrier object used
- `promotion_blockers`: list of unmet gates, if any

---

## 4. Queue order for immediate implementation

Run next, in order:
1. Phase 1 inventory freeze, truth audit, and maintenance-surface creation
2. Phase 2 carrier/root-admission repair where still thin
3. Phase 3 same-carrier geometry packet
4. Phase 4 graph/topology geometry packet
5. Phase 5 operator/channel packet
6. Phase 6 Weyl/chiral local packet
7. Phase 8 classical engine baseline cleanup and rebuild where process-incomplete
8. Phase 7 bipartite local packet if still needed for the chosen bridge scope
9. Phase 9 bridge packet
10. Phase 10 late entropy/axis packet

Parallel execution policy:
- use bounded subagent workstreams for independent tasks only
- safe parallel pair examples:
  - geometry truth audit + engine truth audit
  - tool-integration matrix build + validator/maintenance checklist build
  - graph/topology packet audit + operator/channel packet audit
- do not run parallel implementers on the same file set
- controller session owns the queue, truth labels, and final scope discipline

Reason for this order:
- it keeps the documented geometry work early
- it prevents the engine lane from hijacking the geometry lane
- it delays bridge/entropy/axis inflation until the lower math objects are real
- it turns tool integration and maintenance into a standing part of the build program instead of a cleanup pass that never happens

---

## 5. Verification checklist

Before promoting any result above `exists`:
- does it stay in the correct lane?
- is the claimed math object explicit and math-first?
- does it use the admitted carrier rather than silently changing state space?
- does it include positive, negative, and boundary tests?
- are tool roles honest and at least one relevant nontrivial tool load-bearing?
- is the truth label correct and non-collapsed?
- does it avoid premature bridge or axis closure language?

Before promoting any result to `canonical by process`:
- fresh rerun passes
- result file is non-empty and current
- SIM_TEMPLATE contract fields are present
- tool manifest is honest and complete
- at least one relevant non-baseline tool is load-bearing
- claim scope matches the actual sim scope

---

## 6. First concrete implementation batch

Batch 1 should be only this:
1. audit current geometry and engine result files against the truth labels
2. write the backlog matrix and truth audit docs
3. choose one admitted carrier anchor
4. build or repair one same-carrier geometry packet
5. do not start bridge or axis work in the same batch

Definition of success for Batch 1:
- the repo has one explicit source of truth for what gets simmed next
- the geometry lane is back in front of the engine/bridge drift
- at least one current geometry packet is clearly process-honest
