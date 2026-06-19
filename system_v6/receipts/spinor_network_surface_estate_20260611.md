# Spinor Network Surface Estate Mining Receipt - 2026-06-11

classification: mining_receipt
promotion_allowed: false
write_scope: exactly_this_file
requested_output: estate table + chart-recoverability proposal + gaps + draft build-card skeleton

## Sweep Contract

Dirs swept:

- Repo: `system_v4/`, `system_v5/`, `system_v6/`
- Wiki: `/Users/joshuaeisenhart/wiki/raw/`, `/Users/joshuaeisenhart/wiki/concepts/`, `/Users/joshuaeisenhart/wiki/codex-ratchet-research/`
- Tool/skill/manifests for package evidence: `system_v5/julia_carrier/Project.toml`, `system_v5/julia_carrier/Manifest.toml`, `system_v5/docs/`, `system_v6/receipts/`, `/Users/joshuaeisenhart/.codex-second/skills/`, `/Users/joshuaeisenhart/.agents/skills/`

Search terms:

- Repo object sweep: `hopfield|qnn|quantum neural|neural net|spinor network|attractor pattern|associative memory`
- Wiki object sweep: same terms plus `surface`
- Absence sweep: `qhopfield|quantum hopfield`
- Tooling sweep: `netket`, `QuantumOptics`, `ITensors`, `torch`, `torch_geometric`, `QNN`, `quantum neural network`

The object-defining hits were read and classified below. Broad `neural` false positives that only state "does not admit neural..." or "not neural training" are not estate objects; representative lines are recorded in the gaps section.

## Doctrine Read First

| Object | Class | Evidence | Surface-relevant content |
|---|---|---|---|
| Owner doctrine for this lane | owner-source | `system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md:3-6` says the goal is to register the surface/frame question: "charts are the linearized shadow of a finite spinor network / quantum-Hopfield-like carrier." | This is the owner root. The build must not start from a smooth manifold; it must test finite carrier -> chart recovery. |
| Spinor-network definition | owner-source | `system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md:10-15` says chart cells are "shadows/projections" of a finite spinor network, with nodes as finite spinor degrees of freedom and edges as entanglement/coupling/admissibility relations. | The packet should consume finite node/edge spinor carriers where available. |
| Quantum-Hopfield definition | owner-source | `system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md:16-21` requires a finite spinor set, Hermitian coupling matrix, dissipative/retrieval dynamics, stored patterns, energy/entropy landscape, basins, and spurious attractors. | This is stronger than earlier Hopfield-bond or finite basin objects. Existing estate can supply pieces; the v0 packet must assemble one complete bounded carrier. |
| QNN-as-channels definition | owner-source | `system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md:22-27` defines a QNN layer as a CPTP/parameterized channel and network as channel composition, with typed information rows. | Generic neural-net analogies do not satisfy this. A v0 QNN row must be a channel row. |
| Chart falsifier | owner-source | `system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md:36-46` requires testing whether Bloch/Hopf charts can be recovered as quotients/projections of one finite carrier, and says failure is informative. | The chart test is not optional; it is the first falsifier. |

## Estate Table

| Found object | Source class | Exact evidence | Carrier / couplings / dynamics | Consume into surface packet | Must still build | Ceiling / caveats |
|---|---|---|---|---|---|---|
| `basin3_hopfield_chiral_quaternion_network` | sim-realization | `system_v5/julia_carrier/basin3_julia.jl:1-15` names the object and asks whether Hopfield-like multistability appears in a finite chiral quaternion spinor network. `system_v5/julia_carrier/basin3_julia.jl:16-34` defines `N=12` quaternion-spinor neurons, `M` stored chiral patterns, finite update map, roots, and four models. | Finite `N=12` quaternion/spinor neuron carrier. Pattern families and update maps are explicit. It has Hopfield-like retrieval dynamics and multistability probes. | Use as the closest existing Hopfield/retrieval packet and as a source for chiral pattern families, L/R divergence checks, and spurious-attractor controls. | Build a strict quantum-Hopfield carrier with Hermitian coupling matrix, stated energy/Lyapunov functional, and CPTP/Lindblad or other admissible dissipative retrieval dynamics. | `system_v5/julia_carrier/basin3_julia.jl:36-56` calls it an exploration probe and says it cannot promote physics/cognition/canonical claims. `system_v5/julia_carrier/basin3_julia_results.json:46-51` leaves open issues: finite-size only, no thermodynamic limit, heuristic update maps, and no EEG/physics bridge. |
| `npc_connection_geometry_julia` | sim-realization | `system_v5/julia_carrier/npc_connection_geometry_julia.jl:1-16` defines a scratch finite `N in {8,16,32}` 2D torus domain with `M=3` noncommuting quaternion Hopf patterns and a geometry readout. `system_v5/julia_carrier/npc_connection_geometry_julia.jl:145-163` defines the Hopfield bond matrix `W_ij = sum_mu xi_i^mu * conj(xi_j^mu)`. | Finite torus graph, L/R Weyl spinor carrier from Hopf angles, Hopfield bonds, quaternion plaquette holonomy, noncommutator, bond-dependent Laplacian. | Consume the Hopfield-bond construction and finite graph/holonomy readout. | Add retrieval dynamics and strict Hermitian/channel semantics if this is used as a quantum-Hopfield seed. | `system_v5/julia_carrier/npc_connection_geometry_julia_results.json:1-28` reports `classification: scratch_diagnostic` and `promotion_allowed: false`. This is connection-geometry evidence, not a full quantum-Hopfield basin. |
| `npc2_connection_geometry_julia` | sim-realization | `system_v5/julia_carrier/npc2_connection_geometry_julia.jl:1-31` hardens the first NPC run with controls over `N in {8,16,32,64}`. `system_v5/julia_carrier/npc2_connection_geometry_julia.jl:111-165` defines Weyl spinors, Hopf patterns, random patterns, and Hopfield weights. `system_v5/julia_carrier/npc2_connection_geometry_julia.jl:262-320` performs structured, random, pure-gauge, and erased controls. | Hardened finite Hopf/Weyl Hopfield-bond connection carrier with controls. | Consume as the best existing finite Hopfield-bond/holonomy carrier. Its pure-gauge and random controls should be copied into v0. | Still build a basin/retrieval layer and a chart-recovery layer. | `system_v5/julia_carrier/npc2_connection_geometry_julia_results.json:1-29` reports surviving channels `holonomy_real_curvature` and `laplacian_bond_dependent`, but failing `n01_noncommutation`. This cannot be treated as full noncommutative success. |
| `foundation_spinor_network_basins` | sim-realization | `system_v5/ops/formal_scouts/foundation_spinor_network_basins_jax.py:45-49` defines finite graph edges and target. `system_v5/ops/formal_scouts/foundation_spinor_network_basins_jax.py:172-190` defines finite states and finite update. `system_v5/ops/formal_scouts/foundation_spinor_network_basins_jax.py:333-346` includes a Z3 basin proof. | Finite +/- spinor-network-like basin scaffold with graph edges, update map, quotient classes, and SMT checks. | Consume the basin-contract harness shape and all-three engine discipline. | Replace the toy finite update with the selected spinor/Hopfield carrier and its retrieval dynamics. | `system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json:43-69` reports `scratch_diagnostic`, all pass, and `promotion_allowed: false`. It is a scaffold, not quantum-Hopfield evidence. |
| `foundation_spinor_network_full_stack_layer` | sim-realization | `system_v5/ops/formal_scouts/foundation_spinor_network_full_stack_layer_jax.py:37-40` defines target, graph, and witness. `system_v5/ops/formal_scouts/foundation_spinor_network_full_stack_layer_jax.py:132-180` builds CD tables and Hopf-related features. | Multi-tool finite spinor-network layer with C/M/S quotient, Hopf/CD table support, and all-three stack. | Consume for integration pattern and tool discipline across JAX, Julia, PyTorch, SMT. | It does not define a quantum-Hopfield carrier or chart recovery test by itself. | `system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json:1-46` is scratch and bounded. |
| `stage_lifted_spinor_shell_n3_v0` | sim-realization | `system_v6/sims/stage_lifted_spinor_shell_n3_v0/stage_lifted_spinor_shell_n3_v0_envelope.py:197-235` declares a scratch n=3 lifted spinor shell with all-three engines and Julia strict carrier. | `n=3`, `C^8`, three-qubit lifted shell. | Consume the strict envelope and n=3 carrier discipline. | Use only if v0 chooses the smallest carrier; it has fewer surface graph degrees than n4. | `system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_envelope_results.json:240-276` shows source-backed claim-path tooling, not canonical promotion. |
| `stage_lifted_spinor_shell_n4_v0` | sim-realization | `system_v6/sims/stage_lifted_spinor_shell_n4_v0/build_card.md:28-36` says the n4 builder expects 4 nodes, 5 edges, 2 filled faces, `d=16` carrier, 256-effect finite IC frame, entropy rows, nesting rows, Cl(8) anticommuting family, leakage, and controls. `system_v6/sims/stage_lifted_spinor_shell_n4_v0/build_card.md:38-80` records fresh all-pass/validate commands. | Best small surface carrier candidate: finite `(\mathbb{C}^2)^{\otimes 4}` with graph/face data, density quotient, IC frame, entropy rows. | Consume as the surface_v0 base carrier if the goal is chart recovery plus one typed information row. | Add Hopfield/QNN dynamics on top of this carrier; the shell alone is not a retrieval system. | `system_v6/sims/stage_lifted_spinor_shell_n4_v0/build_card.md:115-117` keeps it under scratch boundary. |
| `terrain_spinor_flux_nest_n3_v0` | sim-realization | `system_v6/sims/terrain_spinor_flux_nest_n3_v0/terrain_spinor_flux_nest_n3_v0_common.py:33-43` pins a committed n3 `C^8` three-qubit lifted-ladder network and defines edge coupling `g_ij`, current `J_ij`, and k-leaf conditioning. `system_v6/sims/terrain_spinor_flux_nest_n3_v0/terrain_spinor_flux_nest_n3_v0_common.py:157-183` derives the carrier state as an ordered tensor product from per-site `psi_L/psi_R`. `system_v6/sims/terrain_spinor_flux_nest_n3_v0/terrain_spinor_flux_nest_n3_v0_common.py:186-193` defines the Bloch vector helper. | Three-site product spinor carrier with explicit edges, coupling/current, and per-site Bloch extraction. | Consume Bloch extraction and edge-current structure. | Add retrieval dynamics, chart binning, and channel row. | `system_v6/sims/terrain_spinor_flux_nest_n3_v0/results/terrain_spinor_flux_nest_n3_v0_envelope_results.json:102-132` says all pass but leaves hardening caveats and scratch ceiling. |
| `terrain_spinor_flux_nest_n4_v0` | sim-realization | `system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_common.py:16-29` fixes site count 4, dimension 16, 5 edges, 2 faces. `system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_common.py:37-47` pins the `C^16` lifted-ladder network and edge coupling/current rules. `system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_common.py:171-219` derives the carrier state vector from per-site spinors. | Four-site surface-like spinor network with edge currents, faces, carrier state, and chart-adjacent density support. | Consume as the preferred finite surface carrier alongside n4 shell. | Add Hopfield coupling/retrieval and chart-row reproduction. | `system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_envelope_results.json:102-129` reports all pass and density quotient reproduction gate, but the carrier remains scratch. |
| `spinor_network_hopf_weyl_testbed` | sim-realization | `system_v6/sims/spinor_network_hopf_weyl_testbed/audit_verdict.md:1-5` calls it genuine-with-caveats and scratch. `system_v6/sims/spinor_network_hopf_weyl_testbed/audit_verdict.md:18-35` records pin, spinor coordinate map, dual-stack readout, and per-node defects. `system_v6/sims/spinor_network_hopf_weyl_testbed/audit_verdict.md:70-88` says coherent information uses a two-site entangled chord ansatz, not a six-node network joint state. | Hopf/Weyl phase and defect readout over a six-node testbed, with coherent-info chord caveat. | Consume Hopf/Weyl chart/phase readouts and the caveat as a guardrail. | Build typed information row from the actual selected network joint state, not from a chord shortcut. | `system_v6/sims/spinor_network_hopf_weyl_testbed/results/spinor_network_hopf_weyl_testbed_envelope_results.json:1-23` marks tools supportive, not load-bearing proof. |
| `spinor_network_face_readout_taxonomy` | sim-realization | `system_v5/ops/formal_scouts/sim_spinor_network_face_readout_taxonomy.py:1-24` declares scratch `N=5`, `DIM=32`, graph edges, and readout keys. `system_v5/ops/formal_scouts/sim_spinor_network_face_readout_taxonomy.py:45-81` defines graph state and density. `system_v5/ops/formal_scouts/sim_spinor_network_face_readout_taxonomy.py:475-519` defines the carrier primitive as finite spinor network `(\mathbb{C}^2)^{\otimes 5}` with nodes, edges, graph-phase state family, density-derived readouts, and no physics admission. | Five-site finite spinor-network readout taxonomy. | Consume as a menu of readout families and density-derived discipline. | Do not consume its labels as physics; select one typed row only for v0. | `system_v5/ops/formal_scouts/results/spinor_network_face_readout_taxonomy_results.json:60-78` records carrier and claim ceiling; `:87-106` says density is derived and primitive is finite spinor network. |
| `knot_mass_gravity_rung` | sim-realization | `system_v5/ops/formal_scouts/sim_knot_mass_gravity_rung.py:1-30` declares scratch `N=8`, `DIM=256`, chain edges, and weights. `system_v5/ops/formal_scouts/sim_knot_mass_gravity_rung.py:48-60` defines finite knot state with graph phase and amplitude knot. `system_v5/ops/formal_scouts/sim_knot_mass_gravity_rung.py:462-489` records carrier primitive `(\mathbb{C}^2)^{\otimes 8}`, nodes/edges, knot subregion, distance surface, and no physics promotion. | Eight-site finite spinor/knot carrier and radial/distance readouts. | Consume only if v0 needs a radial/knot readout control. | Not needed for first surface_v0 unless chart recovery fails on n4 and needs a larger carrier. | `system_v5/ops/formal_scouts/results/knot_mass_gravity_rung_results.json:147-164` rejects physics promotion. |
| `three_spinor_associator_lifted_bracketing_probe` | sim-realization | `system_v5/ops/formal_scouts/sim_three_spinor_associator_lifted_bracketing_probe.py:1-15` states the bounded question on `psi in (C^2)^3` and octonion-coordinate diagnostics. `system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:83-107` records finite spinor network cell, realization dimension 8, and claim ceiling. | Three-site bracketing/nonassociativity diagnostic over a finite spinor cell. | Consume as an optional bracketing falsifier for network quotient choices. | Do not turn octonion diagnostics into primitive carrier doctrine. | `system_v5/ops/formal_scouts/sim_three_spinor_associator_lifted_bracketing_probe.py:395-405` keeps octonions diagnostic. |
| `manifold_unified_run_v0` | sim-realization | `system_v6/sims/manifold_unified_run_v0/build_card.md:1-8` defines a scratch unified run over the n=3 seed with sequence `leaf-conditioning -> lens quotient -> terrain restriction`. `system_v6/sims/manifold_unified_run_v0/build_card.md:10-20` lists step-dependent and invariant families. | Bounded route/trajectory over an existing n3 seed. | Consume route sequencing only: leaf conditioning, lens quotient, terrain restriction. | It is not a carrier definition and not a Hopfield/QNN packet. | `system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json:84-109` keeps allowed claims bounded. |
| Wiki stage-4 Hopfield inventory | llm-elaboration / inventory | `/Users/joshuaeisenhart/wiki/concepts/claude-code-sim-inventory-2026-06-04.md:1-14` says the file is a read-only inventory and repo JSON is authority. `/Users/joshuaeisenhart/wiki/concepts/claude-code-sim-inventory-2026-06-04.md:78-83` lists `hopfield/neural_on_manifold`, `hopfield/basin_probe_v2_hopfield_spinor`, and `hopfield/deflation_hopfield_basin`; `/Users/joshuaeisenhart/wiki/concepts/claude-code-sim-inventory-2026-06-04.md:99-101` says one changed network structure and one deflated. | Evidence that an older stage-4 Hopfield lane existed, but the current repo path is not present under `system_v5/julia_carrier/`. | Use as a pointer only; current repo files/results are authority. | Locate archived old results only if the owner wants historical recovery. | Because the inventory itself says repo JSON is authority, do not consume it as current evidence. |
| Attractor-basins reference | llm-elaboration / reference | `/Users/joshuaeisenhart/wiki/concepts/attractor-basins-formal-reference.md:62-65` defines Hopfield networks as symmetric weights, energy decreasing, stored memories as minima, basin of attraction, capacity about `0.14N`, and spurious attractors. | Formal background for the quantum-Hopfield acceptance test. | Consume as test vocabulary: energy monotone, minima, basin, capacity, spurious attractors. | The v0 packet must implement these on the selected finite carrier rather than cite them. | Reference, not repo result. |
| QNN/PQC channel doc | llm-elaboration / reference | `system_v5/docs/new content/quantum_computing_applications.md:288-299` defines QNN/PQC layers as parameterized unitaries with noise channels and full circuit as channel composition. `system_v5/docs/new content/quantum_computing_applications.md:300-304` records parameter-shift exactness for Pauli generators. | QNN-as-channels mechanics exist as reference language. | Consume for parameterized CPTP/channel build semantics and gradient test if a variational layer is added. | There is no finished surface-specific QNN packet in this sweep. | Reference only. |
| AI/ML density-matrix bridge | llm-elaboration / reference | `/Users/joshuaeisenhart/wiki/concepts/ai-ml-density-matrix-connections.md:40-53` says a lifted linear layer is CP but not trace-preserving unless constrained, nonlinearity breaks CPTP, dropout resembles dephasing, and NTK/kernel analogies are structural. `system_v5/docs/new content/ai_ml_density_matrix_connections.md:168-178` says exact bridges are narrow and unsupported claims should be killed. | Prevents overclaiming ordinary neural layers as quantum channels. | Consume as a guard: QNN row must be CPTP/channel-native or explicitly post-selected. | Need a concrete CPTP layer in v0 if QNN is claimed. | Reference only. |
| QIT AI foundations bridge | llm-elaboration / reference | `/Users/joshuaeisenhart/wiki/concepts/qit-ai-foundations-bridge.md:18-25` says finite density-state/channel language supports bounded predictive/world-model and coordination slices. `/Users/joshuaeisenhart/wiki/concepts/qit-ai-foundations-bridge.md:58-64` says the repo has not earned a general AGI theorem or claim that every AI object is naturally a density matrix/channel. | Guardrail for QNN/AI language. | Consume only as cautionary claim ceiling. | No surface carrier implementation here. | Reference only. |
| Sequential universe spinor network page | llm-elaboration / reference | `/Users/joshuaeisenhart/wiki/concepts/sequential-universe-spinor-network-physics-model.md:170-223` frames finite support, spinor state, entangled spinor network cell, density readouts, probes, quotients, channels/paths/histories, and says the minimum nontrivial bracketing cell is three spinor sites `(\mathbb{C}^2)^3`. | Useful language for finite support -> readout -> quotient. | Consume as conceptual scaffolding only, not evidence. | The surface packet must route through current repo carriers. | Reference only. |
| Current QIT engine bridge page | llm-elaboration / reference | `/Users/joshuaeisenhart/wiki/concepts/qit-engine-geometry-entropy-bridge.md:25-28` says PEPS/PEPS3D references are stale/retired and current carrier surfaces include ITensors-MPS, exact dense/TensorKit, QuantumClifford, spinor-native trajectories; JAX/Julia primary and PyTorch/autograd only with current receipt. | Blocks stale PEPS-first reinvention. | Consume current-carrier preference: dense/spinor-native first; PEPS later only if revalidated. | v0 should not start from retired PEPS claims. | Reference only. |
| Model convergence spinor-network page | llm-elaboration / reference | `/Users/joshuaeisenhart/wiki/concepts/model-convergence-qit-engine-full-stack.md:45-57` maps root constraints to finite admissibility object, finite carrier/support spinor network, L/R Weyl sheets, density/probe readouts, and proposed geometry. | Good owner-language bridge from constraints to finite carrier/readout. | Consume vocabulary only. | Not implementation evidence. | Reference only. |

## Tooling Estate

| Tool / package surface | Source class | Evidence | What it provides | Use / avoid in surface_v0 |
|---|---|---|---|---|
| Julia `QuantumOptics`, `ITensors`, `ITensorMPS` | sim-realization / manifest | `system_v5/julia_carrier/Project.toml:10-11` lists `ITensorMPS` and `ITensors`; `system_v5/julia_carrier/Project.toml:18` lists `QuantumOptics`. `system_v5/julia_carrier/Manifest.toml:1264-1296` records ITensor packages; `system_v5/julia_carrier/Manifest.toml:2646-2652` records `QuantumOptics`. | Dense/operator/channel and tensor-network machinery on the Julia side. | Use Julia as the strict carrier/channel reference for finite `C^16` state, reduced density, channel, and entropy checks. |
| Stage n4 all-three tool manifest | sim-realization | `system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_envelope_results.json:1-45` lists JAX, Julia, and PyTorch tools including `diffrax`, `e3nn_jax`, `gudhi`, `quimb`, `qutip`, `rustworkx`, `toponetx`, `xgi`, `z3`, `cvc5`, `CliffordAlgebras`, `ITensors`, `QuantumClifford`, `QuantumOptics`, `torch`, `torch.func`, and `torch_geometric`. | Proven local all-three package availability for n4 shell work. | Reuse for v0. Do not claim a tool is load-bearing unless the v0 function actually uses it. |
| Terrain n3/n4 tool manifests | sim-realization | `system_v6/sims/terrain_spinor_flux_nest_n3_v0/results/terrain_spinor_flux_nest_n3_v0_envelope_results.json:1-23` and `system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_envelope_results.json:1-23` list `QuantumOptics`, `ITensors`, `ITensorMPS`, `torch.func`, `torch_geometric`, `jraph`, and related support/load-bearing entries. | Existing graph/spinor carrier machinery for terrain current/coupling rows. | Reuse terrain graph/coupling code and density extraction. |
| PyTorch / `torch.func` / `torch_geometric` | sim-realization | `system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json:500-560` records PyTorch-side tool calls including `torch.func` and `torch_geometric` adjacency/edge-index use. | Graph carrier, autograd, and energy descent support. | Use for independent energy-gradient/descent checks, not as proof of quantum-channel semantics. |
| JAX / Dynamiqs / Diffrax / Quimb | sim-realization | `system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json:203-260` records JAX-side tool calls including `diffrax.diffeqsolve` and `dynamiqs.mesolve`. | Batched dynamics and Lindblad/ODE checks. | Use for batched retrieval/channel sweeps after Julia defines the reference channel. |
| NetKet | sim-realization / skill guard | `system_v6/receipts/toolset_expansion_20260610.md:29` says `netket` 3.21.0 is present. `system_v6/receipts/toolset_expansion_20260610.md:50` says a tiny spin Hilbert/Ising target worked, but continuous Bloch affine basin/fixed-point is not natural and NetKet is "not useful for S5 basin/fixed-point"; possible later QMB variational only. `/Users/joshuaeisenhart/.codex-second/skills/three-engine-sim/SKILL.md:76` repeats this guard. | Installed spin Hilbert/Ising variational machinery. | Do not use for v0 basin/fixed-point. Keep as later QMB variational option only. |
| Julia graph-neural packages | manifest/evidence | `system_v5/evidence/sim_tool_library_coverage_20260608.json:338-343` records `GraphNeuralNetworks` and `GraphNeuralNets` missing from the current Julia path. | No current Julia GNN package surface. | Do not plan v0 around Julia GNN libraries unless installed and probed later. |

## Chart-Recoverability Proposal Map

This is a proposal table, not an admission decision.

| Target chart rows | Proposed quotient of found carrier | Required math | Found support | Current status |
|---|---|---|---|---|
| 33-cell Bloch chart rows | Quotient of the n4 finite spinor network carrier by single-site reduced density matrices: `rho_i = Tr_{rest}(|Psi><Psi|)`, then Bloch vector `r_i = (Tr rho_i sigma_x, Tr rho_i sigma_y, Tr rho_i sigma_z)`, then bin into the existing 33-cell A-chart rows. | A normalized finite state on `(\mathbb{C}^2)^{\otimes 4}`, partial trace, Pauli expectations, and exact cell classifier. | `stage_lifted_spinor_shell_n4_v0/build_card.md:28-36` provides `d=16`, 4 nodes, 5 edges, 2 faces, and 256-effect IC frame. `terrain_spinor_flux_nest_n4_v0_common.py:171-219` derives the n4 state vector from per-site spinors. `terrain_spinor_flux_nest_n3_v0_common.py:186-193` already defines a Bloch vector helper. | Supported in pieces. The exact 33-cell row reproduction has not been run. |
| Hopf-chart rows | Quotient of the same n4 carrier by per-site Hopf coordinates and two-site phase/edge holonomy: site spinor -> Hopf base point plus fiber phase; edge pair -> relative phase/holonomy row. | Hopf map `S^3 -> S^2`, phase/fiber coordinate, two-site phase structure, and edge holonomy/classifier. | `npc2_connection_geometry_julia.jl:111-165` defines Weyl spinors and Hopf patterns; `npc2_connection_geometry_julia.jl:262-320` runs structured/random/pure-gauge controls. `spinor_network_hopf_weyl_testbed/audit_verdict.md:18-35` records spinor coordinate map and per-node phase defects. | Partially supported. Need a single-carrier Hopf row recovery test, not a cross-file analogy. |
| Quantum-Hopfield basin rows | Terminal-state quotient of a finite spinor/Hopfield carrier under retrieval dynamics: initial state -> attractor class, energy decrease, spurious attractor class, escape/trapping predicates. | Hermitian coupling matrix, energy or Lyapunov function, dissipative/retrieval map, finite basin partition, negative controls. | `basin3_julia.jl:16-34` has finite chiral quaternion Hopfield patterns and update maps. `npc2_connection_geometry_julia.jl:111-165` has Hopfield weights. `foundation_spinor_network_basins_jax.py:172-190` has finite states/update scaffold and `:333-346` has SMT basin proof shape. | Not yet complete. Existing objects supply patterns/bonds/scaffold, but no single strict quantum-Hopfield v0 packet was found. |
| QNN/channel rows | Channel quotient of selected carrier: `rho -> E_theta(rho)` with one typed information row measured before/after retrieval. | CPTP map or explicitly declared post-selected non-TP map, channel composition, trace/positivity checks, one typed information observable. | `quantum_computing_applications.md:288-299` defines PQC layers as noisy channels. `ai_ml_density_matrix_connections.md:40-53` warns ordinary NN layers are not generally CPTP. Julia/JAX/PyTorch tool surfaces exist. | Missing as a surface-specific implementation. Build exactly one channel row in v0. |
| Typed information row family | Use one row only: recommended first row is coherent information or conditional entropy on the actual selected network joint state and retrieval channel. | Network joint density state, subsystem split, entropy calculation, control split. | Face taxonomy has density-derived readouts; Hopf-Weyl testbed has coherent-info chord but warns it is not full network joint-state evidence. | Build from actual v0 joint state. Do not reuse the two-site chord ansatz as final evidence. |

## Gaps And Absence Evidence

Absence claims below include the grep or directory sweep that supports them.

1. No pre-doctrine `qhopfield` / `quantum hopfield` implementation was found in swept repo/wiki dirs.

Command swept: `rg -n -i "qhopfield|quantum hopfield" system_v4 system_v5 system_v6 ~/wiki/raw ~/wiki/concepts ~/wiki/codex-ratchet-research`

Only hits returned:

```text
system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md:4:- Owner registered a new target frame: the Bloch/Hopf chart estate should be re-read as shadows of a finite spinor network / quantum-Hopfield-like carrier, not as the substrate itself.
system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md:16:## Doctrine: Quantum Hopfield / QNN Surface Reading
system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md:33:1. finite quantum-Hopfield / spinor-network carriers;
```

2. The old inventory's `hopfield/...` paths were not present under the current `system_v5/julia_carrier` directory sweep.

Directory sweep: `find system_v5/julia_carrier -maxdepth 2 -type d | sort | rg -i "hopfield|basin|carrier"` plus `find system_v5/julia_carrier -maxdepth 3 -type f | rg -i "hopfield|basin|npc|neural"`.

Current files returned were the live basin/NPC surfaces such as `system_v5/julia_carrier/basin3_julia.jl`, `system_v5/julia_carrier/npc_connection_geometry_julia.jl`, `system_v5/julia_carrier/npc2_connection_geometry_julia.jl`, `system_v5/julia_carrier/chiral_quat_spinor_basin_explore.jl`, and related results. No `system_v5/julia_carrier/hopfield/` directory was returned.

3. No completed strict quantum-Hopfield carrier was found.

The closest pieces are:

- `basin3_julia.jl:16-34`: finite chiral quaternion Hopfield patterns and update maps.
- `npc2_connection_geometry_julia.jl:111-165`: Hopf/Weyl Hopfield weights.
- `foundation_spinor_network_basins_jax.py:172-190`: finite basin update scaffold.

Missing from one packet: Hermitian coupling matrix, CPTP/dissipative retrieval dynamics, energy/Lyapunov monotone, basin partition, and chart recovery from the same carrier.

4. No completed surface-specific QNN-as-channels implementation was found.

Positive references are channel doctrine and mechanics:

- `system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md:22-27`
- `system_v5/docs/new content/quantum_computing_applications.md:288-299`
- `/Users/joshuaeisenhart/wiki/concepts/ai-ml-density-matrix-connections.md:40-53`

But the generic neural hits are mostly negative ceilings. Representative false-positive lines:

```text
system_v6/sims/round3_s6s7_heavy_discriminator_v0/round3_s6s7_heavy_discriminator_v0_pytorch.py:215: "no training/autograd/message-passing neural claim"
system_v6/sims/round3_s6s7_heavy_discriminator_v0/round3_s6s7_heavy_discriminator_v0_envelope.py:160: PyTorch/PyG is honestly scoped to finite graph-carrier N-sweeps, not neural training or promotion
system_v5/ops/formal_scouts/sim_multiqubit_qit_reservoir_global_structure_probe.py:30: learned dynamics and does not admit intelligence, neural capability, canonical
```

5. Chart recoverability is still unproven.

The estate has density quotient, Bloch helper, Hopf/Weyl patterns, and finite carrier states. It does not yet have a single command/result proving that the n4 or NPC carrier reproduces the 33-cell Bloch chart rows and Hopf chart rows as quotients.

## Draft Build Card Skeleton: `spinor_network_surface_v0`

classification: scratch_diagnostic
promotion_allowed: false
scope: one finite carrier, one basin contract, one A-chart recoverability test, one typed-information row family

### Build Inputs To Consume

- Owner doctrine: `system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md:3-48`
- Preferred finite surface carrier: `stage_lifted_spinor_shell_n4_v0` plus `terrain_spinor_flux_nest_n4_v0`
- Hopfield/retrieval pieces: `basin3_julia.jl`, `npc2_connection_geometry_julia.jl`, `foundation_spinor_network_basins`
- Chart/readout pieces: n4 density quotient, n3/n4 Bloch helper, Hopf-Weyl testbed, face readout taxonomy
- Tool discipline: Julia `QuantumOptics`/`ITensors`; JAX `dynamiqs`/`diffrax`/batching; PyTorch `torch.func`/`torch_geometric`; SMT `z3`/`cvc5`

### Carrier Choice

Use one finite carrier:

```text
carrier_id: n4_lifted_spinor_surface
state_space: (C^2)^{tensor 4}, dimension 16
support_graph: 4 nodes, 5 edges, 2 filled faces
source_paths:
  - system_v6/sims/stage_lifted_spinor_shell_n4_v0/build_card.md:28-36
  - system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_common.py:16-47
  - system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_common.py:171-219
```

Reason: n4 is the smallest found carrier with a surface-like graph/face structure, density quotient support, finite IC frame, and existing all-three evidence. n3 is useful for controls; n5/n8 readout scouts are larger and should wait.

### Quantum-Hopfield Layer

Build one bounded retrieval layer on the n4 carrier:

- Pattern family: 3 or 4 stored product-spinor patterns derived from the committed per-site spinors and Hopf perturbations.
- Coupling: Hermitian edge coupling matrix derived from the NPC Hopfield formula and restricted to the n4 support graph. Require explicit symmetrization check.
- Energy: declare and test a finite energy/Lyapunov observable.
- Dynamics: one CPTP or explicitly dissipative retrieval channel. Preferred reference implementation in Julia `QuantumOptics`; JAX batches the same parameter grid; PyTorch checks graph energy descent/autograd shape only.
- Controls: random patterns, pure-gauge/erased carrier, shuffled edges, sign-flipped pattern, flat state, and spurious-attractor probe.

### Basin Contract

Acceptance checks:

1. finite carrier normalized and dimension checked;
2. Hermitian coupling check passes;
3. retrieval channel preserves trace and positivity or is explicitly marked post-selected;
4. energy/Lyapunov non-increase holds on the tested update schedule;
5. at least one stored pattern has a nonempty basin;
6. at least one spurious attractor check is reported, whether found or not;
7. controls do not pass the same predicates by tautology;
8. result writes canonical envelope with `classification`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, and `promotion_allowed:false`.

### A-Chart Recoverability Test

For every terminal basin class:

1. compute `rho_i = Tr_{rest}(|Psi_terminal><Psi_terminal|)` for each site;
2. compute Bloch vector `r_i`;
3. assign the vector to existing 33-cell A-chart bins;
4. report recovered rows, missing rows, duplicate rows, and ambiguous rows;
5. fail the chart-recovery predicate if no nontrivial row structure is recovered.

This is a recoverability test, not a proof that charts are the substrate.

### Hopf-Chart Recoverability Test

For each terminal or stored pattern:

1. compute per-site Hopf base coordinates from spinor;
2. compute fiber/relative phase where available;
3. compute two-site edge phase or holonomy on the n4 graph;
4. compare to Hopf chart row vocabulary;
5. report whether rows are recovered, collapsed, or unsupported.

### Typed Information Row Family

Pick exactly one for v0:

```text
typed_information_family: coherent_information_or_conditional_entropy
state_source: actual n4 network joint state after retrieval channel
forbidden_shortcut: two-site chord ansatz unless explicitly marked as a control
```

The first row should measure one subsystem split before and after retrieval. Do not add every face/knot/mass/gravity readout in v0.

### Tool Plan

- Julia reference: state, coupling, channel, reduced density, entropy.
- JAX worker: batched initial states and channel parameters; optional `dynamiqs`/`diffrax` dynamics where appropriate.
- PyTorch worker: graph edge tensors, energy-gradient/descent sanity, `torch.func` vectorization.
- SMT: finite predicates for trapping/escape/control sanity where booleanized.
- NetKet: excluded for v0 basin/fixed-point per `system_v6/receipts/toolset_expansion_20260610.md:50` and skill guard; possible later QMB variational lane only.

### First-Pass Stop Conditions

- Stop if the selected carrier cannot produce valid single-site reduced densities.
- Stop if Hermitian coupling cannot be constructed without arbitrary new degrees of freedom.
- Stop if trace/positivity fails for the proposed retrieval channel.
- Stop if chart recovery returns only trivial or constant rows; report that as an informative falsifier instead of widening scope.

## Mining Receipt Ceiling

This receipt inventories source objects and proposes a bounded build shape. It does not promote the spinor-network surface reading, does not claim chart recovery has passed, and does not claim a completed quantum-Hopfield/QNN implementation exists.


---

## Path-repair note (controller, 2026-06-11)

Six artifact path references were WRONG in the original mine (Hermes disk-audit catch, controller-verified): the foundation_spinor_network_basins / full_stack_layer sources+results live under `system_v5/ops/formal_scouts/` (not `system_v6/sims/`), and the knot/taxonomy scouts have no `_probe` suffix. All six repaired above. Lesson: mining receipts are build authorities — their path refs must be existence-checked before a build card consumes them.
