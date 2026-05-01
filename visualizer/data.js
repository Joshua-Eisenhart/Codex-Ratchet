// Codex Ratchet — static snapshot data, extracted from repo docs.
// All paths and status labels are verbatim from system_v5/ and system_v4/.
// This is a VIEW surface; the backing artifacts live in the repo.

window.RATCHET_DATA = {
  meta: {
    snapshot: "2026-04-14T00:00Z",
    repo: "Joshua-Eisenhart/Codex-Ratchet",
    commit: "ce0480e1",
    doctrine: "constraint-admissibility / nonclassical ratchet",
    vocab: ["survived", "killed", "open", "not_yet_tested"],
    forbidden: ["verified", "confirmed", "all pass", "28/28 PASS", "canonical (without process)"],
  },

  // The three lanes never merge progress.
  lanes: [
    {
      id: "foundation",
      name: "Foundation migration",
      subtitle: "28 families · numpy → torch",
      status: "open",
      note: "C2_graph_topology: 11/28 non-null, 0 mismatches. Migration registry still NOT_STARTED.",
      artifact: "system_v5/new docs/MIGRATION_REGISTRY.md",
    },
    {
      id: "seam",
      name: "Seam proof depth",
      subtitle: "z3 / cvc5 load-bearing",
      status: "survived",
      note: "Phi0 seam closed 2026-04-08. Axis 6 open.",
      artifact: "system_v4/probes/a2_state/sim_results/bridge_phi0_proof_integration_results.json",
    },
    {
      id: "stack",
      name: "Stack / nesting sims",
      subtitle: "shell-local → coupling → coexistence",
      status: "open",
      note: "Layer triple catalog done; coupling matrix in progress.",
      artifact: "system_v5/new docs/16_lego_build_catalog.md",
    },
  ],

  // Resolution ladder on M(C). Not floors — exploration levels.
  resolutions: [
    { r: 0, name: "F01 + N01", what: "Finitude + Noncommutation", status: "doctrinal", sims: 0, note: "z3 predicates exist, never run", artifact: "ROOT_CONSTRAINT_EXTENDED_FOUNDATIONS.md" },
    { r: 1, name: "Admissibility charter", what: "24 constraints", status: "doctrinal", sims: 0, note: "Charter written, no executable validator", artifact: "Formal constraints and geometry.md" },
    { r: 2, name: "M(C) characterization", what: "Constraint manifold", status: "doctrinal", sims: 0, note: "Prose only, no computation", artifact: "CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md" },
    { r: 3, name: "Geometry / operator basis", what: "Type1/Type2 crosscheck", status: "open", sims: 6, note: "B3.1–B3.4 survived. Type1 survived. Type2 Weyl inversion OPEN.", artifact: "operator_basis_search_results.json" },
    { r: 4, name: "Weyl working layer", what: "Holonomy / ladder audit", status: "open", sims: 3, note: "Inherits Type2 gap from Resolution 3.", artifact: "weyl_geometry_ladder_audit_results.json" },
    { r: 5, name: "Bridge family Ξ", what: "History vs pointwise", status: "open", sims: 5, note: "Chiral 0.80; no single bridge winner selected.", artifact: "xi_bridge_bakeoff_results.json" },
    { r: 6, name: "Cut / entropy / entanglement", what: "C2 entropy + C1 witness", status: "split", sims: 8, note: "C2 SURVIVED (8/8 VN-positive). C1 OPEN — 8/16 mispair unresolved (Fe/Fi family).", artifact: "c1_entanglement_object_search_results.json" },
    { r: 7, name: "Kernel Φ₀(ρ_AB)", what: "Discriminator", status: "embargoed", sims: 1, note: "K1_Ic wins 5/6. Embargoed until Resolution 6 closes.", artifact: "a0_kernel_discriminator_results.json" },
    { r: 8, name: "Edge writeback", what: "Ring topology / 64-lookup", status: "survived", sims: 1, note: "P1–P5 all survived. 7/7 dynamic slot columns nonzero.", artifact: "edge_state_writeback_results.json" },
  ],

  // Boots — separate terminals, contamination-isolated.
  boots: [
    { id: "A2", name: "Mining", runner: "Hermes", role: "High-entropy ingestion, owner voice, planning, audit", canWrite: "plans / audits", canNotWrite: "canon", color: "amber" },
    { id: "A1", name: "Recon", runner: "Claude Code", role: "Candidate geometry advocate; preserve nuance; Popper weirdest first", canWrite: "recon artifacts", canNotWrite: "B evidence directly", color: "cyan" },
    { id: "A0", name: "Compiler", runner: "Claude Code", role: "Deterministic, extractive, append-only, lints EXPORT_BLOCKs", canWrite: "campaign tape, graveyard views", canNotWrite: "invented claims", color: "paper" },
    { id: "B",  name: "Ratchet", runner: "Claude Code", role: "Blind constraint enforcement. Accepts or rejects M(C).", canWrite: "verdicts", canNotWrite: "anything with candidate preference", color: "rose" },
    { id: "SIM", name: "Discipline", runner: "Claude Code", role: "Sim auditor (NOT runner). Enforces declared tier/tools/artifacts.", canWrite: "audit reports", canNotWrite: "sim results", color: "paper" },
  ],

  // Entropy tiers - fuel classification.
  entropyTiers: [
    { e: 3, label: "high", src: "holodeck / Grok / Gemini / Apple Notes", owner: "A2 mines" },
    { e: 2, label: "medium", src: "physics fuel", owner: "A2 processes, A1 uses with care" },
    { e: 1, label: "low", src: "constraint ladder specs", owner: "A1 prime fuel" },
    { e: 0, label: "very low", src: "bootpacks / canon state", owner: "direct reference" },
  ],

  // 7 active axes (0–6). Axes 7–12 are candidate only.
  axes: [
    { n: 0, role: "entropy drive, cut-state functional", math: "torus seat + Φ₀(ρ_AB)", status: "open", grounding: "chart-level candidate only" },
    { n: 1, role: "derived terrain branch split", math: "Se/Ni vs Ne/Si", status: "derived", grounding: "source-grounded factor, not closed" },
    { n: 2, role: "direct vs conjugated frame", math: "ρ̃=ρ vs ρ̃=V†ρV", status: "active", grounding: "source-grounded, under reconstruction" },
    { n: 3, role: "fiber vs lifted-base loop", math: "density-stationary vs density-traversing", status: "open", grounding: "UNRESOLVED — chirality/flux vs outer/inner" },
    { n: 4, role: "loop-order family", math: "UEUE vs EUEU", status: "derived", grounding: "strongest source-grounded operator axis" },
    { n: 5, role: "operator family", math: "dephasing vs rotation", status: "active", grounding: "chart / IGT correlation only" },
    { n: 6, role: "precedence order", math: "operator-first vs terrain-first", status: "derived", grounding: "partially source-grounded" },
  ],

  candidateAxes: [
    { n: 7, domain: "spin / chirality", basis: "Weyl handedness; CW/CCW ring orientation" },
    { n: 8, domain: "local gauge invariance", basis: "U(1) Wilson loop invariance" },
    { n: 9, domain: "topological winding", basis: "homotopy π₁ integer-valued" },
    { n:10, domain: "entanglement structure", basis: "Schmidt rank; GHZ vs separable" },
    { n:11, domain: "CPT / discrete symmetry", basis: "CPT theorem" },
    { n:12, domain: "RG flow", basis: "coupling runs with scale" },
  ],

  // 4 base operators (Kraus / Lindblad families)
  operators: [
    { id: "Ti", kind: "dissipative", gen: "σ_z dephasing", family: "T-kernel", effect: "destroys off-diagonal coherence in Z basis" },
    { id: "Te", kind: "dissipative", gen: "σ_x dephasing", family: "T-kernel", effect: "destroys coherence in X basis; changes populations" },
    { id: "Fi", kind: "unitary",     gen: "σ_x rotation", family: "F-kernel", effect: "rotates Bloch vector around x-axis; preserves purity" },
    { id: "Fe", kind: "unitary",     gen: "σ_z rotation", family: "F-kernel", effect: "rotates Bloch vector around z-axis; preserves purity" },
  ],

  // Real chart terrain IDs (ENGINE_64_SCHEDULE_ATLAS §4).
  // NOTE: outer order is Se-out, Si-out, Ni-out, Ne-out (NOT a mirror of inner).
  terrains: ["Se-in", "Ne-in", "Ni-in", "Si-in", "Se-out", "Si-out", "Ni-out", "Ne-out"],
  terrainFamilies: ["Se", "Ne", "Ni", "Si", "Se", "Si", "Ni", "Ne"],
  terrainFlux:     ["IN", "IN", "IN", "IN", "OUT", "OUT", "OUT", "OUT"],
  terrainEngine:   ["T1", "T1", "T1", "T1", "T2", "T2", "T2", "T2"],

  // Real signed-op order (ENGINE_64_SCHEDULE_ATLAS §5 + §10).
  signedOps: [
    { id: "Ti↑", op: "Ti", order: "operator-first", tokens: ["TiSe","TiNe"] },
    { id: "Ti↓", op: "Ti", order: "terrain-first", tokens: ["NeTi","SeTi"] },
    { id: "Te↑", op: "Te", order: "operator-first", tokens: ["TeNi","TeSi"] },
    { id: "Te↓", op: "Te", order: "terrain-first", tokens: ["SiTe","NiTe"] },
    { id: "Fi↑", op: "Fi", order: "operator-first", tokens: ["FiNe","FiSe"] },
    { id: "Fi↓", op: "Fi", order: "terrain-first", tokens: ["SeFi","NeFi"] },
    { id: "Fe↑", op: "Fe", order: "operator-first", tokens: ["FeSi","FeNi"] },
    { id: "Fe↓", op: "Fe", order: "terrain-first", tokens: ["NiFe","SiFe"] },
  ],

  // The exact 16 chart-locked cells from ENGINE_64_SCHEDULE_ATLAS §10
  // (starred in the 8×8 grid). Keys are "row,col" where row = terrain index,
  // col = signed-op index (both 0-based in the order above).
  // Also carries the S-slot id (S01..S64) and the token that realizes it.
  scheduleAtlas: [
    // Se-in (row 0)
    { slot: "S01", row: 0, col: 0, token: "TiSe", outcome: "LOSE", role: "T1 outer" },
    { slot: "S06", row: 0, col: 5, token: "SeFi", outcome: "win",  role: "T1 inner" },
    // Ne-in (row 1)
    { slot: "S10", row: 1, col: 1, token: "NeTi", outcome: "WIN",  role: "T1 outer" },
    { slot: "S13", row: 1, col: 4, token: "FiNe", outcome: "lose", role: "T1 inner" },
    // Ni-in (row 2)
    { slot: "S19", row: 2, col: 2, token: "TeNi", outcome: "lose", role: "T1 inner" },
    { slot: "S24", row: 2, col: 7, token: "NiFe", outcome: "LOSE", role: "T1 outer" },
    // Si-in (row 3)
    { slot: "S28", row: 3, col: 3, token: "SiTe", outcome: "win",  role: "T1 inner" },
    { slot: "S31", row: 3, col: 6, token: "FeSi", outcome: "WIN",  role: "T1 outer" },
    // Se-out (row 4)
    { slot: "S34", row: 4, col: 1, token: "SeTi", outcome: "lose", role: "T2 inner" },
    { slot: "S37", row: 4, col: 4, token: "FiSe", outcome: "WIN",  role: "T2 outer" },
    // Si-out (row 5)
    { slot: "S43", row: 5, col: 2, token: "TeSi", outcome: "WIN",  role: "T2 outer" },
    { slot: "S48", row: 5, col: 7, token: "SiFe", outcome: "win",  role: "T2 inner" },
    // Ni-out (row 6)
    { slot: "S52", row: 6, col: 3, token: "NiTe", outcome: "LOSE", role: "T2 outer" },
    { slot: "S55", row: 6, col: 6, token: "FeNi", outcome: "lose", role: "T2 inner" },
    // Ne-out (row 7)
    { slot: "S57", row: 7, col: 0, token: "TiNe", outcome: "win",  role: "T2 inner" },
    { slot: "S62", row: 7, col: 5, token: "NeFi", outcome: "LOSE", role: "T2 outer" },
  ],

  // Derived: which cells are chart-locked (for O(1) lookup).
  lockedCells: (() => {
    const atlas = [
      [0,0],[0,5],[1,1],[1,4],[2,2],[2,7],[3,3],[3,6],
      [4,1],[4,4],[5,2],[5,7],[6,3],[6,6],[7,0],[7,5],
    ];
    const locked = new Set();
    atlas.forEach(([r,c]) => locked.add(`${r},${c}`));
    return locked;
  })(),

  // Macro-stage blocks (ENGINE_64_SCHEDULE_ATLAS §12).
  //   32 microsteps per engine = 8 macro-stages × 4 operator slots
  //   Every terrain row has exactly TWO macro-stages:
  //     one ↑-signed (spans cols {Ti↑, Te↑, Fi↑, Fe↑} = {0,2,4,6})
  //     one ↓-signed (spans cols {Ti↓, Te↓, Fi↓, Fe↓} = {1,3,5,7})
  //   The "named" operator within each block is the Ax6 naming handle
  //   (e.g. TiSe is named by Ti↑ but the stage uses all 4 UP operators).
  //   Token + outcome come straight from the atlas §8.
  //
  //   block columns are ordered so the NAMING operator is first.
  macroStages: [
    // Se-in (row 0)
    { row: 0, sign: "UP",   named: 0, cols: [0,2,4,6], token: "TiSe", outcome: "LOSE", role: "T1 outer", slot: "S01" },
    { row: 0, sign: "DOWN", named: 5, cols: [5,1,3,7], token: "SeFi", outcome: "win",  role: "T1 inner", slot: "S06" },
    // Ne-in (row 1)
    { row: 1, sign: "DOWN", named: 1, cols: [1,3,5,7], token: "NeTi", outcome: "WIN",  role: "T1 outer", slot: "S10" },
    { row: 1, sign: "UP",   named: 4, cols: [4,0,2,6], token: "FiNe", outcome: "lose", role: "T1 inner", slot: "S13" },
    // Ni-in (row 2)
    { row: 2, sign: "UP",   named: 2, cols: [2,0,4,6], token: "TeNi", outcome: "lose", role: "T1 inner", slot: "S19" },
    { row: 2, sign: "DOWN", named: 7, cols: [7,1,3,5], token: "NiFe", outcome: "LOSE", role: "T1 outer", slot: "S24" },
    // Si-in (row 3)
    { row: 3, sign: "DOWN", named: 3, cols: [3,1,5,7], token: "SiTe", outcome: "win",  role: "T1 inner", slot: "S28" },
    { row: 3, sign: "UP",   named: 6, cols: [6,0,2,4], token: "FeSi", outcome: "WIN",  role: "T1 outer", slot: "S31" },
    // Se-out (row 4)
    { row: 4, sign: "DOWN", named: 1, cols: [1,3,5,7], token: "SeTi", outcome: "lose", role: "T2 inner", slot: "S34" },
    { row: 4, sign: "UP",   named: 4, cols: [4,0,2,6], token: "FiSe", outcome: "WIN",  role: "T2 outer", slot: "S37" },
    // Si-out (row 5)
    { row: 5, sign: "UP",   named: 2, cols: [2,0,4,6], token: "TeSi", outcome: "WIN",  role: "T2 outer", slot: "S43" },
    { row: 5, sign: "DOWN", named: 7, cols: [7,1,3,5], token: "SiFe", outcome: "win",  role: "T2 inner", slot: "S48" },
    // Ni-out (row 6)
    { row: 6, sign: "DOWN", named: 3, cols: [3,1,5,7], token: "NiTe", outcome: "LOSE", role: "T2 outer", slot: "S52" },
    { row: 6, sign: "UP",   named: 6, cols: [6,0,2,4], token: "FeNi", outcome: "lose", role: "T2 inner", slot: "S55" },
    // Ne-out (row 7)
    { row: 7, sign: "UP",   named: 0, cols: [0,2,4,6], token: "TiNe", outcome: "win",  role: "T2 inner", slot: "S57" },
    { row: 7, sign: "DOWN", named: 5, cols: [5,1,3,7], token: "NeFi", outcome: "LOSE", role: "T2 outer", slot: "S62" },
  ],

  // Selected sims — hand-picked from sim_results/ for the event spine.
  events: [
    { t: "2026-04-08T09:12Z", lane: "seam", boot: "A1", status: "survived", label: "Phi0 proof integration closed", path: "bridge_phi0_proof_integration_results.json", size: 10120 },
    { t: "2026-04-08T11:40Z", lane: "seam", boot: "A0", status: "survived", label: "cvc5 cross-check accepted", path: "cvc5_cross_check_results.json", size: 3635 },
    { t: "2026-04-09T02:14Z", lane: "stack", boot: "A1", status: "open", label: "C1 mispair: 8/16 unresolved (Fe/Fi)", path: "c1_mispair_probe_results.json", size: 21879 },
    { t: "2026-04-09T06:55Z", lane: "stack", boot: "A1", status: "survived", label: "C2 entropy structure: 8/8 VN-positive", path: "c2_entropy_structure_search_results.json", size: 6340 },
    { t: "2026-04-09T14:03Z", lane: "foundation", boot: "SIM", status: "killed", label: "Shannon shortcut killed on stage 3", path: "c2_entropy_polarity_graph.json", size: 4128 },
    { t: "2026-04-10T01:22Z", lane: "stack", boot: "A1", status: "open", label: "Bridge Ξ bakeoff — no single winner", path: "axis0_xi_bakeoff_results.json", size: 12489 },
    { t: "2026-04-10T09:41Z", lane: "stack", boot: "B", status: "killed", label: "Shell path I_c negative — weak, not killed", path: "axis0_through_shells_results.json", size: 16055 },
    { t: "2026-04-11T03:28Z", lane: "stack", boot: "A1", status: "survived", label: "Edge writeback P1–P5 survived", path: "edge_state_writeback_results.json", size: 1010 },
    { t: "2026-04-11T15:09Z", lane: "foundation", boot: "A0", status: "open", label: "C2_graph_topology: 11/28 non-null", path: "MANIFEST_CHECK_REPORT.json", size: 737660 },
    { t: "2026-04-12T07:33Z", lane: "stack", boot: "A1", status: "open", label: "Axis 6 canonical order still open", path: "axis6_canonical_results.json", size: 28833 },
    { t: "2026-04-12T22:47Z", lane: "stack", boot: "SIM", status: "killed", label: "classical_baseline_szilard_onebit — expected kill", path: "classical_baseline_szilard_onebit_results.json", size: 2620 },
    { t: "2026-04-13T05:12Z", lane: "stack", boot: "A1", status: "survived", label: "contact_symplectic_kahler coexistence survived", path: "contact_symplectic_kahler_coexistence_results.json", size: 15157 },
    { t: "2026-04-13T11:58Z", lane: "stack", boot: "A1", status: "open", label: "bridge_cut_perturbation stability — partial", path: "bridge_cut_perturbation_stability_results.json", size: 45167 },
    { t: "2026-04-14T00:04Z", lane: "foundation", boot: "A0", status: "open", label: "MIGRATION_REGISTRY still NOT_STARTED in doc", path: "MIGRATION_REGISTRY.md", size: 11789 },
  ],

  // Graveyard: everything starts dead. Survivors earn out.
  graveyard: {
    seeded: 306,
    survived: 42,
    killed: 211,
    open: 53,
    sample: [
      { id: "shannon_purity_shortcut", outcome: "killed", at: "R6/C2", reason: "insufficient to separate VN-positive stages" },
      { id: "MI_mispair_test", outcome: "killed", at: "R6/C1", reason: "fake_coupling_kill_count = 0" },
      { id: "raw_local_LR_cut", outcome: "killed", at: "R3", reason: "doctrine object; never earned as final cut" },
      { id: "runtime_ga0_doctrine", outcome: "killed", at: "R3", reason: "doctrine object, no witness" },
      { id: "concurrence_fake_coupling", outcome: "survived", at: "R6/C1", reason: "16/16 stages killed fake coupling" },
      { id: "chiral_bridge_composite", outcome: "survived", at: "R5", reason: "score 0.80, I_c>0 on all 6 configs" },
      { id: "edge_writeback_ring", outcome: "survived", at: "R8", reason: "P1–P5 all survived; 64-lookup populated" },
      { id: "vn_entropy_necessity", outcome: "survived", at: "R6/C2", reason: "Shannon/purity shortcuts insufficient" },
      { id: "type2_weyl_inversion", outcome: "open", at: "R3", reason: "fiber/base grammar inverted; unresolved" },
      { id: "axis0_final_bridge_Xi", outcome: "open", at: "R5", reason: "no single winner selected" },
      { id: "kernel_phi0_unlock", outcome: "open", at: "R7", reason: "embargoed pending R6 closure" },
      { id: "Fe_Fi_mispair_family", outcome: "open", at: "R6/C1", reason: "universally entangling operator family; structural" },
    ],
  },

  // Enforcement principles — show as a static reference strip.
  enforcement: [
    { n: 1, name: "Claim Gate", rule: "Prose cannot upgrade results. Only artifact class can." },
    { n: 2, name: "No Smoothing", rule: "Branch conflicts stored as separate branches. Open stays open." },
    { n: 3, name: "Boot Gate", rule: "Boots read only decision log, sim registry, artifact registry, tranche ledger." },
    { n: 4, name: "Doc Freeze", rule: "Docs are reference only. Runtime truth must be machine-readable." },
    { n: 5, name: "Concrete", rule: "Do not trust LLM to follow process. Make violations mechanically visible." },
    { n: 6, name: "Minimal v5 Law", rule: "Required step → must have artifact. Open branch → cannot narratively close." },
  ],

  // =========================================================================
  // G-STACK (geometry stack = constraint ratchet IFF non-commutative)
  // Source: system_v5/new docs/plans/geometry_stack_ratchet_doctrine.md
  //         system_v5/new docs/plans/G_TOWER_HOPF_WEYL_INTEGRATION_SPEC.md (CANDIDATE, not canon)
  //         system_v5/new docs/CONSTRAINT_SURFACE_AND_PROCESS.md
  //         system_v5/new docs/references/FIBER_BUNDLES_AND_SPIN_GEOMETRY_REFERENCE.md
  //
  // Discipline:
  //   - M(C) is PRIMARY. All shells below are illustrative charts on M(C), not M(C) itself.
  //   - G-tower is CANDIDATE math, not canon. Its cells render dashed/hollow.
  //   - A stack is a RATCHET only if A∘B ≠ B∘A. Commuting couplings are decorative.
  // =========================================================================
  gStack: {
    // The nested-shell candidate chart. Each shell is its own geometry.
    // `kind` controls how the shell is rendered in 3D.
    // `citation` field = sim file that anchors this layer locally.
    layers: [
      {
        id: "MC",
        name: "M(C)",
        subtitle: "Constraint surface (primary)",
        status: "doctrinal",
        kind: "surface",
        role: "canon",
        description: "Surface of admissibility: every point satisfies F01+N01 and all derived constraints simultaneously. Not a manifold we can fully chart — we chart REGIONS of it via candidate shells. Watermark all shells below as illustrative.",
        witness: "F01 (finitude) + N01 (noncommutation) + 24-constraint charter",
        anchorSim: null,
        color: "#d9a24b",
      },
      {
        id: "S3",
        name: "S³",
        subtitle: "Spinor carrier (Hopf total space)",
        status: "covered",
        kind: "sphere3",
        role: "canon",
        description: "3-sphere. Qubit state space; unit quaternions; SU(2) ≅ Spin(3). Total space of the Hopf bundle S¹ → S³ → S².",
        witness: "density_hopf_geometry_results.json · canonical_by_process",
        anchorSim: "sim_density_hopf_geometry.py",
        color: "#e8ebee",
      },
      {
        id: "HOPF",
        name: "S¹ → S³ → S²",
        subtitle: "Hopf fibration (U(1)-bundle)",
        status: "covered",
        kind: "hopf",
        role: "canon",
        description: "Principal U(1)-bundle. Fiber over each point of S² is a great circle in S³. Generator of π₃(S²)=Z. Bloch sphere = S³/U(1). Curvature F = (i/2) sinθ dθ∧dφ; first Chern c₁=1.",
        witness: "foundation_hopf_torus_geomstats_clifford_results.json · canonical_by_process",
        anchorSim: "sim_foundation_hopf_torus_geomstats_clifford.py",
        color: "#7ec4d8",
      },
      {
        id: "TORI",
        name: "T_η",
        subtitle: "Nested Hopf tori in S³",
        status: "covered",
        kind: "toriFoliation",
        role: "canon",
        description: "Foliation (z₁,z₂)=(cosη·e^{iξ₁}, sinη·e^{iξ₂}), η∈[0,π/2]. Boundary circles at η=0,π/2 = Hopf fibers over N/S poles. Clifford torus at η=π/4: unique Heegaard splitting, flat, minimal. Hopf fibers on T_η are (1,1)-curves.",
        witness: "pure_geometry_hopf_tori_results.json · 12/12 pass · canonical_by_process",
        anchorSim: "sim_pure_geometry_hopf_tori.py",
        color: "#a78bd9",
      },
      {
        id: "WEYL",
        name: "ψ_L ⊕ ψ_R",
        subtitle: "Weyl spinors (associated bundle sections)",
        status: "partial",
        kind: "weyl",
        role: "candidate",
        description: "Sections of E = S³ ×_{SU(2)} C². Chirality projectors P_L=(1-γ⁵)/2, P_R=(1+γ⁵)/2. Weyl equation D̸ψ=0 on left-handed component. H_L=+H₀, H_R=-H₀. Parity P: L↔R. Candidate structure; spin-survival across full G-chain is open.",
        witness: "lego_weyl_hopf_spinor_bridge_results.json · exists (self-declared canonical, not locally rerun)",
        anchorSim: null,
        color: "#d87a69",
      },
      {
        id: "GTOWER",
        name: "GL→O→SO→U→SU→Sp",
        subtitle: "G-structure tower (CANDIDATE)",
        status: "partial",
        kind: "gtower",
        role: "candidate",
        description: "Reduction chain of structure groups. Each step tightens. 5/6 adjacent reductions rigid; G₂ exceptional open. z3 UNSAT on reversed chains = ratchet signature. Marked CANDIDATE per user doctrine: axes math hypothetical, shell-local probes only, no full-chain pairwise coupling sim yet.",
        witness: "g_structure_tower_results.json + sim_gtower_order_z3_unsat_invalid_reduction_order",
        anchorSim: "sim_gtower_full_chain.py",
        color: "#f0c674",
      },
      {
        id: "HOLONOMY",
        name: "Hol(γ) = e^{iΩ/2}",
        subtitle: "Holonomy / Berry phase",
        status: "open",
        kind: "holonomy",
        role: "candidate",
        description: "Holonomy of canonical Hopf connection is U(1); spin promotion requires double cover SU(2). Berry phase γ=−½Ω where Ω = enclosed solid angle on Bloch S². Probed shell-locally; Connes-bridge cross-check NOT YET RUN.",
        witness: "sim_holonomy_group_classifies_gtower_shell.py (shell-local)",
        anchorSim: "sim_hopf_deep_u1_holonomy_equivariance.py",
        color: "#9acd68",
      },
      {
        id: "CONNES",
        name: "d_Connes",
        subtitle: "Spectral-triple distance",
        status: "open",
        kind: "connes",
        role: "candidate",
        description: "d(φ₁,φ₂) = sup{|φ₁(a)−φ₂(a)| : ‖[D,a]‖≤1}. For Dirac on S² restricted to Hopf bundle, should recover geodesic on base. Rosetta R3 prediction (Connes ↔ geodesic ↔ trace) — predicted agreement, NOT confirmed.",
        witness: "sim_spectral_triple_connes_distance.py (exists, unbridged)",
        anchorSim: "sim_spectral_triple_connes_distance.py",
        color: "#c78bd9",
      },
    ],

    // Couplings between layers. The ratchet test = non-commutativity.
    // `type`: "noncomm" (ratchet), "commuting" (decorative/control), "open" (not yet run).
    // `order`: which pair of layer ids was tested "A∘B vs B∘A".
    // `evidence`: sim file or z3 artifact backing the coupling.
    couplings: [
      {
        id: "HOPF_WEYL",
        a: "HOPF", b: "WEYL",
        type: "noncomm",
        status: "survived",
        claim: "Weyl-projection then Hopf-fiber-reduction ≠ Hopf-then-Weyl on probe states. Reversed chain = z3 UNSAT.",
        evidence: "sim_geom_noncomm_weyl_then_hopf_vs_hopf_then_weyl.py · sim_geom_noncomm_hopf_fiber_then_weyl_projector.py",
      },
      {
        id: "GTOWER_HOPF",
        a: "GTOWER", b: "HOPF",
        type: "noncomm",
        status: "survived",
        claim: "U(1) fiber reduction from SU(2) on Hopf bundle requires the specific G-tower order. Reversed = UNSAT.",
        evidence: "sim_gtower_u1_hopf_fiber_reduction.py · sim_gtower_couple_so3_x_u1_fiber.py",
      },
      {
        id: "S3_HOPF",
        a: "S3", b: "HOPF",
        type: "derived",
        status: "survived",
        claim: "S² = S³/U(1). Hopf quotient is the definition of the base; commuting question is degenerate here.",
        evidence: "sim_geom_layer_1_2_3.py · 10/10 fibers independent (drift ~1e-16)",
      },
      {
        id: "HOPF_TORI",
        a: "HOPF", b: "TORI",
        type: "derived",
        status: "survived",
        claim: "Hopf fibers on T_η are (1,1)-curves; torus foliation is compatible with fiber structure by construction.",
        evidence: "sim_pure_geometry_hopf_tori.py · 12/12",
      },
      {
        id: "GTOWER_WEYL",
        a: "GTOWER", b: "WEYL",
        type: "noncomm",
        status: "open",
        claim: "Does Weyl chirality projector before vs after SU(2)→SO(3) produce different surviving families? Missing sim: sim_weyl_chirality_g_reduction_noncomm.py.",
        evidence: "MISSING · sim_weyl_chirality_g_reduction_noncomm.py (not in repo 2026-04-14)",
      },
      {
        id: "HOLONOMY_CONNES",
        a: "HOLONOMY", b: "CONNES",
        type: "rosetta",
        status: "open",
        claim: "Rosetta R3 prediction: holonomy ranking and Connes distance ranking agree on loop families on S². Pairwise coupling sim NOT YET RUN.",
        evidence: "MISSING · sim_holonomy_connes_bridge.py (not in repo 2026-04-14)",
      },
      {
        id: "GTOWER_HOLONOMY",
        a: "GTOWER", b: "HOLONOMY",
        type: "noncomm",
        status: "open",
        claim: "Does canonical Hopf connection survive full G-chain reduction with consistent Chern number? Missing deep probe.",
        evidence: "MISSING · sim_g_tower_hopf_canonical_connection_deep.py (not in repo 2026-04-14)",
      },
      {
        id: "MC_ALL",
        a: "MC", b: "*",
        type: "admissibility",
        status: "open",
        claim: "Every layer above must chart points ON M(C). Off-surface points = graveyard. Fail-closed.",
        evidence: "constraint charter (C1–C8 + X1–X8) · no executable validator yet (R1 sims=0)",
      },
    ],

    // The 10 legos from 16_lego_build_catalog.md.
    // Each lego is a small local math object that must exist BEFORE pairwise couplings.
    legos: [
      { id: "constraint_probe_admissibility", name: "Constraint & probe admissibility",   stage: "lego", status: "needs_deeper_lego_work", queue: "blocked_on_lego",       tools: ["z3","cvc5","sympy"], anchor: "bridge_entropy_inequality_guardrails_results.json", feeds: ["MC"] },
      { id: "carrier_admission_density_matrix", name: "Carrier / density matrix",         stage: "lego", status: "partial",                 queue: "ready_now",             tools: ["pytorch","sympy","z3"], anchor: "density_hopf_geometry_results.json",                feeds: ["S3"] },
      { id: "g_structure_tower",               name: "G-structure tower",                  stage: "lego", status: "partial",                 queue: "ready_now",             tools: ["z3","sympy","geomstats"], anchor: "g_structure_tower_results.json",                  feeds: ["GTOWER"] },
      { id: "geometry_crosschecks_same_carrier",name: "Geometry cross-checks (one carrier)",stage: "lego",status: "covered",                 queue: "ready_now",             tools: ["geomstats","clifford","sympy","gudhi"], anchor: "foundation_hopf_torus_geomstats_clifford_results.json", feeds: ["HOPF","TORI"] },
      { id: "operator_family_admission",       name: "Operator family admission",          stage: "lego", status: "needs_deeper_lego_work", queue: "blocked_on_lego",       tools: ["clifford","sympy","z3","e3nn"], anchor: "local_operator_action_results.json",              feeds: ["WEYL"] },
      { id: "graph_cell_complex_geometry",     name: "Graph / cell-complex geometry",      stage: "lego", status: "covered",                 queue: "ready_now",             tools: ["xgi","toponetx","pyg","gudhi"], anchor: "xgi_family_hypergraph_results.json",              feeds: [] },
      { id: "bipartite_structure_local",       name: "Bipartite structure (local)",        stage: "lego", status: "covered",                 queue: "ready_now",             tools: ["gudhi","pyg","sympy"], anchor: "gudhi_concurrence_filtration_results.json",       feeds: [] },
      { id: "entropy_family_crosschecks",      name: "Entropy cross-checks",               stage: "lego", status: "needs_deeper_lego_work", queue: "blocked_on_lego",       tools: ["sympy","pytorch"], anchor: null,                                              feeds: [] },
      { id: "gauge_group_falsifier",           name: "Gauge-group falsifier",              stage: "boundary", status: "covered",             queue: "blocked_from_assembly", tools: ["sympy"], anchor: "geom_cp1_u1_projective_results.json",             feeds: [] },
      { id: "quantum_metric_nonuniqueness",    name: "Quantum metric non-uniqueness",       stage: "boundary", status: "covered",             queue: "blocked_from_assembly", tools: ["geomstats","sympy"], anchor: "geomstats_shell_metrics_results.json",            feeds: [] },
    ],

    // Rosetta predictions — pairs of tool families that SHOULD agree on the same invariant.
    // These are PREDICTED agreements, not confirmed.
    rosettas: [
      { id: "R1", name: "Holonomy ↔ Chern ↔ Curvature integral", tools: ["geomstats","sympy","z3"], status: "open", claim: "Winding/contractibility of Hopf-base loops agrees across all three." },
      { id: "R2", name: "Weyl grades ↔ Parity irreps ↔ L/R UNSAT", tools: ["clifford","e3nn","z3"], status: "open", claim: "Chirality projection excludes the same states under grade decomposition and irrep decomposition." },
      { id: "R3", name: "Connes d ↔ Geodesic d ↔ Trace d",        tools: ["spectral-triple","geomstats","sympy"], status: "open", claim: "Distances on Bloch-embedded states agree up to positive monotone rescaling. Disagreement = shell boundary." },
    ],
  },
};
