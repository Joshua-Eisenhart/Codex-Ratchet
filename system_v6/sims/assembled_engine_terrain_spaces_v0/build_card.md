# Build Card - assembled_engine_terrain_spaces_v0

Source request: build `assembled_engine_terrain_spaces_v0` under
`system_v6/sims/assembled_engine_terrain_spaces_v0/`, file-disjoint, with
NO git add/commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=rung_1_terrain_spaces_component_only_no_stage_or_engine_claim`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- Rung-1 component only: this packet is `terrain spaces`, not the terrains
  simmed, not stage residency, not an engine traversal, and not axis evidence.
  Boundary phrase: not the terrains simmed.
- Three-engine scope: not scoped for this rung because the claim-bearing work is
  exact finite integer cell-chain/SNF certification. An envelope is still
  emitted.
- Boundary helper: `assembled_engine_terrain_spaces_v0_boundary.py` plus
  `scripts/builder_audit_boundary.py`.
- G.2a from birth: validators and tests delegate audit-file handling to the
  shared helper and never hard-require permanent absence of `audit_verdict.md`.

## Authority Read Order

1. `system_v6/receipts/assembled_engine_v0_design_20260612.md` at
   `100653354`: rung 1 says eight small TerrainSpace fixtures with chain/cell
   certificates and terrain law refs. Topology4 = Se/Ne/Ni/Si and Flux2 = in/out.
2. `system_v6/receipts/owner_architecture_requirement_20260612.md` at
   `0ff763858`: terrains must be actual geometric/topological spaces; anything
   less uses component names only.
3. `system_v6/sims/fiber_augmented_cover_v2/audit_verdict.md` at
   `cc2f61b2a`: reuse the CW cellular-complex pattern, committed cells,
   boundary matrices, `d^2=0`, and chi gates.
4. `system_v6/sims/topology_parity_guard_v3/`: reuse the current SNF homology
   consumer pattern, exact integer rank, torsion, and Euler cross-checks.
5. `system_v6/receipts/audit_standards_codex_v1.md`: standards codex and G.2a
   bind from birth.

## Pre-Registered Construction

Terrain ids:

- `Se-in`, `Se-out`
- `Ne-in`, `Ne-out`
- `Ni-in`, `Ni-out`
- `Si-in`, `Si-out`

Topology4 = Se/Ne/Ni/Si. Flux2 = in/out. The owner may override any pinned
default; such an override changes machine-visible flags and requires rerun.

Default flags carried in result JSON:

- substrate: chart-level finite Hopf/cell complex;
- Topology4 meaning: Se/Ne/Ni/Si, not sphere/torus/nested/Mobius;
- flux invariant: source-locked in/out chirality/sign rows;
- Ne policy: pure Hamiltonian circulation;
- Si projector frame: `Si-in` z-projector strata, `Si-out` x-projector strata;
- finite-time policy: `tau=0.4`, one small residency step;
- closure: density-level loop closure is enough for smallest v0;
- Matrix64: sixteen chart-locked stages only; full 64 traversal deferred.

## Packet Requirements

1. Emit eight `TerrainSpace` objects with their own object id, marked regions,
   terrain generator, flux orientation, and certificate.
2. Emit explicit cells and sparse boundary matrices for each terrain.
3. Recompute `d^2=0`, Euler/chi, and homology through the same SNF machinery.
4. Compute flux orientation from committed structure data, not from labels.
5. Record terrain law references as rung-2 residency contracts:
   Se/Si = dissipative side, Ne/Ni = circulation side.
6. Emit an 8x8 pairwise distinctness row as 28 unordered pair rows and report
   homology-only indistinguishable pairs honestly.
7. Emit result JSON, envelope JSON, packet validator receipt, tests, and
   `builder_self_assessment.md`.
8. Emit scoped `jax`, `pytorch`, and `julia` lane wrapper files/results only as
   packet-invariant checks. Do not call the envelope `all_three_full_sims`.

## Boundaries

Allowed claims:

- scratch-diagnostic construction of eight finite TerrainSpace fixtures;
- chain/cell certificate data, `d^2=0`, Euler, and SNF homology;
- computed flux/law/marked-region distinctness at rung-1 ceiling;
- machine-visible design defaults and owner-choice flags.

Disallowed claims:

- the terrains simmed;
- sixteen stages constructed;
- operator residency;
- engine traversal;
- axis probe result;
- formal admission;
- canonical by process;
- bridge, physics, manifold, or axis-level closure.

## Expected Commands

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/assembled_engine_terrain_spaces_v0/assembled_engine_terrain_spaces_v0.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/assembled_engine_terrain_spaces_v0/assembled_engine_terrain_spaces_v0_jax.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/assembled_engine_terrain_spaces_v0/assembled_engine_terrain_spaces_v0_pytorch.py
/opt/homebrew/bin/julia system_v6/sims/assembled_engine_terrain_spaces_v0/assembled_engine_terrain_spaces_v0_julia.jl
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/assembled_engine_terrain_spaces_v0/assembled_engine_terrain_spaces_v0_envelope.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/assembled_engine_terrain_spaces_v0/validate_assembled_engine_terrain_spaces_v0.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/assembled_engine_terrain_spaces_v0/tests
```
