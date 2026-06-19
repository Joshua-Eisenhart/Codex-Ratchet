# Independent Audit Verdict - assembled_engine_terrain_spaces_v0

Bottom line: VERDICT = GENUINE-WITH-CAVEATS at SCAFFOLDING-TIER only. The packet is valid feedstock as eight finite terrain-space fixtures with exact cell-chain/SNF checks, honest homology-only collisions, owner-choice flags, G.2a builder/audit separation, and non-claim-bearing engine wrappers. It does not earn terrain residency, stage, engine traversal, manifold, bridge, axis, canonical, promotion, or admission language.

Claim ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; `claim_ceiling=rung_1_terrain_spaces_component_only_no_stage_or_engine_claim`.

## Findings

G1 - Label fence literal vocabulary caveat. `rg -i "manifold|terrain-of-the-manifold|carv"` over the packet found `manifold` in negative/disallowed boundary rows only:

- `assembled_engine_terrain_spaces_v0_boundary.py:63`
- `assembled_engine_terrain_spaces_v0_common.py:848`
- `build_card.md:97`
- `builder_self_assessment.md:36`
- `results/assembled_engine_terrain_spaces_v0_results.json:1290`

No row I inspected promotes these fixtures as manifold terrain, terrain-of-the-manifold, carved manifold, stage residency, engine traversal, bridge, or axis evidence. However, the re-anchor said the manifold vocabulary should appear nowhere, so the literal vocabulary fence is not perfectly clean. This is a wording/label-fence caveat, not a mathematical kill row.

G2 - Flux computation caveat. The flux rows are computed from committed signed rows and have sign-erasure controls, but the signed rows are seeded by each spec's `flux` / `flux_row` field rather than derived from a rung-2 residency map or dynamics. That is acceptable for scaffolding-tier distinctness, and not acceptable for any later claim that the terrain dynamics themselves produced the in/out orientation.

## Recomputed Checks

Fresh read-only recomputation from committed result JSON:

- Sampled `d1*d2=0`, SNF, Betti, Euler, and flux rows for `Se-in`, `Ne-in`, and `Si-out`.
- Results matched:
  - `Se-in`: `d1_snf=[1,1,1]`, `d2_snf=[1]`, Betti `[1,0,0]`, Euler `1=1`, flux sum `-3 -> in`.
  - `Ne-in`: `d1_snf=[1,1,1]`, `d2_snf=[]`, Betti `[1,1,0]`, Euler `0=0`, flux sum `-3 -> in`.
  - `Si-out`: `d1_snf=[1,1]`, `d2_snf=[]`, Betti `[2,0,0]`, Euler `2=2`, flux sum `2 -> out`.

Pairwise distinctness:

- Result table has 28 unordered pair rows.
- Recomputed six pairs and each matched the reported distinguishing fields:
  - `Ne-in` / `Ne-out`: flux, law type, marked-region witness.
  - `Ni-in` / `Se-in`: law type, marked-region witness.
  - `Si-in` / `Si-out`: flux, law type, marked-region witness.
  - `Ne-in` / `Ni-in`: homology, law type, marked-region witness.
  - `Se-in` / `Si-in`: homology, law type, marked-region witness.
  - `Ni-out` / `Se-out`: law type, marked-region witness.
- The 8 homology-only collisions are reported explicitly as data, not hidden.

Law refs:

- Spot-checked cited owner/reference lines against source files.
- `terrain math.md:76-83` contains the eight terrain generator formulas.
- `terrain math.md:89-90` contains the left/right projector definitions.
- `terrain rosetta strong math.md:63-70` contains the left/right `Se/Ne/Ni/Si` generator rows.

Machine-visible design conformance:

- `design_conformance.owner_choice_flags` is present for substrate, topology4 meaning, flux invariant, Ne policy, Si projector frame, finite-time policy, closure, and Matrix64.
- Each sampled flag has `owner_override_allowed=true`.
- `stage_movement_allowed=false`, `component_boundary` refuses terrain-simmed/stage/engine/axis/bridge/physics/admission language.

G.2a:

- `builder_gates.g2a_boundary_from_birth=true`.
- `no_builder_audit_verdict=true`.
- `scripts/builder_audit_boundary.py` accepts a later audit file only if the header declares fresh/independent audit status.
- Before this audit file was written, `audit_verdict.md` was absent.

Engine lanes:

- Envelope mode is `scoped_integer_homology_packet_with_lane_wrappers`, not `all_three_full_sims`.
- `three_engine_scope.scoped=false`.
- JAX/PyTorch/Julia lanes are wrapper/parity/hash surfaces only; exact SNF authority remains Python/SymPy. I found no parity theater claiming independent JAX/PyTorch/Julia terrain simulation.

## Commands / Evidence

- `rg -n -i "manifold|terrain-of-the-manifold|carv(ed|e|ing)|these are|are the terrains|terrain spaces are|terrain-space scaffolding|scaffolding|scaffold" system_v6/sims/assembled_engine_terrain_spaces_v0`
- Read-only Python recomputation of sampled `d1*d2`, SNF, Euler, flux, and six pairwise rows from `results/assembled_engine_terrain_spaces_v0_results.json`.
- `jq '{ok:.ok, errors:.errors}' system_v6/sims/assembled_engine_terrain_spaces_v0/results/assembled_engine_terrain_spaces_v0_validator_results.json` returned `ok=true`, `errors=[]`.
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/assembled_engine_terrain_spaces_v0/tests` returned `4 passed in 4.01s`.

## Citation Rule

At scaffolding-tier, citations can support source lineage, owner-choice defaults, and rung-2 law-residency contracts only. They do not certify that the terrain dynamics ran, that stages exist, that engines traversed stage spaces, or that any manifold-level claim is admitted.

Accepted use: cite source rows for fixture labels, formulas, and owner defaults.

Rejected use: cite source rows as proof that these hand-built complexes are the actual terrains, the manifold, or a promoted/canonical assembled engine.
