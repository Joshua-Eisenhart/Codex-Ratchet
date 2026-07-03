# Reference docs — key source material from the repos

These files are the primary source material behind the formal spec, pulled from
the two source repos (Joshua-Eisenhart-Wiki and Codex-Ratchet) so this bundle is
self-contained for a fresh thread with no repo access. They are **source /
support material**, not the formal spec — read them as the substrate the spec
formalizes, not as independently audited claims. Provenance tiers (candidate /
witness / current-support) are stated inside each file's own front-matter and in
the crosswalk's evidence split; honor them.

The spec (`spec_and_reports/CONSTRAINT_CORE_FORMAL_SPEC.md`) is the audited layer;
`spec_and_reports/PURE_MATH_CORE.md` is the de-jargoned proposition ledger;
`data_json/rosetta_layer.json` is the label layer. These reference docs sit
*below* all three — they are where the terrain names, operator families, science
method, and holodeck model come from.

--------------------------------------------------------------------------------
## engine_math/  — the primary math the spec formalizes
--------------------------------------------------------------------------------
- **engine-math-reference.md** — the four base operators (Ti/Te σz,σx dephasing;
  Fi/Fe σx,σz rotation), the two loop vector fields (Y_in = dφ fiber/
  density-stationary; Y_out = −cos2η dφ + dχ base/density-traversing), and the
  **16 placements** = terrain families {Se,Ne,Ni,Si} × chirality {L,R} × loop
  {in,out}. This is the direct source for spec §7q–§7s (the 16 stages, the two
  native operators per terrain, the eight-of-sixteen access law) and §7g's
  operator definitions. UP/DOWN are composition orders, not new operators.
- **igt-pattern-explicit-math-reference.md** — the explicit Bloch maps per
  terrain, the operator table (Ti/Te/Fi/Fe native terrains, lines the spec cites
  for the W-covariance / direct↔conjugated law §7t), the 360°/720° spinor loop
  structure (§7l), and the deductive/inductive loop families.
- **TERRAIN_LAW_LEDGER.md** — the locked terrain law: Axis-6 rule b₆ = −b₀·b₃,
  the H_L=+H₀ / H_R=−H₀ chirality split, the GKSL dissipator convention. Source
  for the spec's terrain generators and the §7o gauge-breaking work.
- **QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md** — the signed four-operator
  math in full (Kraus forms, λ eigenvalues, the signed Axis-6 order). Source for
  §7q's "two native operators, signed" and the fusion split.
- **ENGINE_64_SCHEDULE_ATLAS.md** — the 64 = 2 engines × 8 terrains × 4 operators
  schedule. Source for §7g (and the two-64s AUDIT FLAG the spec carries: 64 as
  2×8×4 vs 16 native stages × 4 sub-stages — an owner decision, not resolved).

--------------------------------------------------------------------------------
## science_method/  — the bidirectional science method (engine ↔ science process)
--------------------------------------------------------------------------------
The owner's claim this bundle records: **each engine stage matches a stage in the
science process, and the deductive science method is the inductive one run in
reverse order.** This maps directly onto the spec's own loop structure:

- spec §7l / igt-pattern: **Deductive = UEUE**, **Inductive = EUEU** — the same
  four sub-steps (Unitary/Entropic) in reversed order. The engine's two loop
  senses (inner fiber vs outer base, and the 360°→−ψ / 720°→+ψ double cover) are
  the geometric carrier of that forward/reverse relation.
- so "deductive science = inductive science reversed" is the science-process
  reading of the same order-reversal the spec measures as the N01 order-sensitivity
  (order-blind → 11/64 collapse; order-sensitive → 64/64 distinct).

Files:
- **recursive-science-methodology-reference.md** — Leviathan's science method as a
  recursive bounded-update discipline (state → evidence surface → delta → update →
  rerun), across person/org/ecosystem/architecture scales. The PROPOSE→OBSERVE→
  GATE→APPLY runtime crosswalk.
- **leviathan-science-method-qit-engine-crosswalk.md** — the hub: the candidate
  synthesis that the Leviathan science method, holodeck perception/memory loop,
  FEP prediction-first loop, and QIT engines are different surfaces of one
  recursive engine grammar. Also carries the Type-1/Type-2 (left/right Weyl
  chirality) ↔ engine-type reading. Read the evidence split at the top: these are
  candidate/support lanes, not closed integration.
- **leviathan-v3.2-word.txt** — the raw legacy Leviathan v3.2 source (large;
  ~2200 lines) that both wiki pages extract from. Included as the primary source
  of record.

--------------------------------------------------------------------------------
## holodeck/  — the perception/memory model
--------------------------------------------------------------------------------
The holodeck model: a prediction-first perception/memory implementation where a
standing generative model predicts first, world input corrects it, and memory is
stored as compressed nonliteral traces re-activated by contextual triggers. It is
the candidate implementation model for the perception side of the engine loop
(the FEP-style prediction/error interpretation).

- **holodeck-doctrine.md** — the core doctrine.
- **projective-holodeck-memory-model.md** — the fuller memory model (largest,
  ~177 lines).
- **holodeck-qit-fep-leviathan-integration.md** — the cleaner dev-facing page
  tying holodeck ↔ QIT engines ↔ FEP ↔ Leviathan.
- **prediction-first-processing-and-holodeck-memory.md** — the prediction-first
  processing subclaim.

--------------------------------------------------------------------------------
## How the reference docs relate to the spec's open ledger
--------------------------------------------------------------------------------
- The engine_math docs are the *validation targets* for the still-open thread
  "run the owner's real Julia/JAX/PyTorch engines" — the per-stage fingerprints
  in `data_json/` (sixteen_stage_engine.json, terrain_fingerprints.json) are what
  those real engines should reproduce.
- The science_method bidirectionality is the process-level reading of the spec's
  UEUE/EUEU deductive/inductive loop; making each of the 16 stages *do* a distinct
  science-process step is the "engines running / unique computation per stage"
  goal, still on the substrate side (numpy stand-ins here; JAX/Julia/PyTorch are
  the aligned targets).
- The holodeck lane is a fenced connected lane in the spec's ledger (memory /
  perception), recorded but deliberately not expanded into the audited core.
