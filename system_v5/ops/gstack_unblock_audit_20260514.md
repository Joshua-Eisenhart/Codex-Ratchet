# GStack / Constraint-Manifold Unblock Audit

Generated: 2026-05-14

Scope: decide what is actually blocking advancement in the formal/current sim
workstream, using current repo evidence plus independent Grok/Gemini audits.
This is an exploration-plan artifact, not canonical mathematical admission.

Correction: `system_v5/grok_sim` is a separate informal experiment. It is not
the formal sim surface and not "our sim here." Its receipts and candidates may
be mined for ideas, failure patterns, and rough proposed constructions only.
They do not define the workstream substrate.

## Current Evidence

The latest sidequest receipts already show the rough tower is possible:

- `system_v5/grok_sim/loop_runner/receipts/20260514T005446Z/phase_02_gstack_results.json`
  - `observable.phase_pass = true`
  - Weyl chirality: `bloch_z_L = 1.0`, `bloch_z_R = -1.0`
  - flux holonomy: `pi`, stable on repeat
  - 4 layers present with dependencies `(1,0), (2,1), (3,2)`
  - Hopf north/south distances both `0.0`
  - Clifford product count `2`

- `system_v5/grok_sim/loop_runner/receipts/20260514T005423Z/phase_46_constraint_manifold_foundation_results.json`
  - `observable.phase_pass = true`
  - carrier dimension `16`
  - manifold dimension `6`
  - 7 named tangent slots present
  - flux holonomy `pi`
  - initial state satisfies constraints
  - transforms stay on manifold

- `system_v5/grok_sim/loop_runner/receipts/20260514T005423Z/phase_47_gstack_layered_entropy_results.json`
  - `observable.phase_pass = true`
  - 4 layers
  - admissible entropy set sizes `[8, 6, 4, 2]`
  - strict subset chain reported consistent
  - base entropy readout finite for `8/8`

These receipts are `side_quest_only`, `promotion_allowed: false`. They show
that a rough tower-like construction is possible in the separate informal
experiment. They are useful as proposal evidence only; they do not become the
formal/current substrate.

## External Audit Summary

Grok and Gemini both identified the same process problem:

- strict promotion gates are being used as if they must block all exploratory
  tower assembly;
- `system_v5/grok_sim` can continue as a loose external proposal generator as
  long as it imports and calls existing formal legos instead of hardcoding their
  outputs;
- formal/canonical promotion remains blocked until legos, proofs, receipts, and
  graveyards close.

Grok's strongest point:

- use the current rough tower as scout evidence for candidate assembly ideas and
  keep failures as scout evidence instead of stopping formal exploration.

Gemini's strongest point:

- split integrity gates from canonization gates. Data shape, dimensions,
  non-NaN numerics, parent links, and callable-lego import are integrity gates;
  uniqueness, full proof, optimality, and analytic isomorphism are promotion
  gates.

Gemini assumed the old parent-link and Hopf north-pole failures were still live.
Current receipts show those specific failures are resolved for the latest
sidequest candidate.

## Actual Blockers

1. The rough sidequest tower is being confused with the formal exploratory
   substrate. It should only inform proposals; formal/current sims need their
   own clean harness or adapter.

2. `build_constraint_manifold_assembly()` exists as a sidequest assembly
   proposal, but
   phase contracts expect `build_constraint_manifold()` and
   `build_gstack_over_manifold()` style APIs. The API bridge between assembly
   proposal and runner phases is still uneven.

3. The system has no explicit "exploratory tier can advance" contract. Current
   language overuses promotion fences (`no GStack promotion`, `no nonclassical
   admission`) and under-specifies what scout work is allowed to do next.

4. Some proposed/candidate files still carry contaminated names or old axis/
   engine language. That should block reuse in formal/current sims unless the
   names and claims are cleaned at the point of reuse.

5. Existing formal legos are abundant, but there is not yet one clean
   executable tower harness whose name and API say exactly what it does:
   nested finite geometry assembly with noncommutation and finitude probes.

## Gates To Keep Hard

These block even exploratory runs:

- imported lego path exists;
- callable import succeeds or returns an explicit `NOT_YET_TESTED` /
  `lego_load_error`;
- no hardcoded constants substituted for failed lego calls;
- density matrices are Hermitian, PSD within tolerance, trace one;
- matrix dimensions agree;
- parent links exist for nested layers;
- entropy outputs finite, not NaN/inf;
- result is fenced as `side_quest_only` or `exploratory`;
- promotion fields say `promotion_allowed: false`.

## Gates That Should Not Block Exploration

These block promotion, not rough tower work:

- uniqueness of manifold ordering;
- proof that the nesting is the final correct nesting;
- full 120-pair placement distinguishability;
- full physical-evolution graveyard sweep;
- bridge or target-system interpretation;
- canonical naming of every historical artifact;
- complete proof that every entropy layer is the right layer;
- final relationship between flux/chirality/inner-outer.

## Next Prototype Target

Build a formal/current scout harness or adapter with a literal name. It may mine
`grok_sim` for proposed construction patterns, but it must not import the
sidequest candidate as authority.

`sim_nested_finite_geometry_holonomy_noncommutation_probe.py`

Location:

Prefer a new fenced formal-scout surface under `system_v5/ops/` or a clearly
noncanonical formal proposal path, not `system_v4/probes/` and not by treating
`system_v5/grok_sim` as the sim surface.

Purpose:

- translate the useful ideas from the latest sidequest candidate into a clean
  formal-scout harness;
- import formal geometry legos through callable paths named in
  `COMPONENT_MAP.md`;
- assemble a finite nested geometry stack;
- run two loop/transport operations in both orders;
- compute a commutator/holonomy-difference readout;
- compute finite entropy/coherent-info readouts on the resulting density states;
- write a fenced scout receipt with explicit graveyards.

Minimum observables:

- layer parent links and layer count;
- Hopf projection convention check;
- stable nonzero holonomy;
- commutator norm for two transports;
- finite entropy vector by layer;
- density validity residuals;
- graveyard outcomes for identity layers, zero holonomy, missing parent,
  order-swap collapse, and dimension mismatch.

## Division Of Labor

Codex local work:

- keep `grok_sim` separate from the formal/current sim surface;
- clean the API bridge and runner shape for formal/current scout work;
- verify actual receipts;
- reject hardcoded proposals;
- write or patch the minimal formal-scout harness if proposals fail;
- keep source/result names literal and math-first;
- decide what is promotion-blocked versus exploration-allowed.

Grok/Gemini work:

- propose alternate tower assemblies and graveyard variants;
- propose noncommutation/finitude readouts;
- propose layer order alternatives;
- produce divergent recipes and failure cases, not canonical claims or formal
  source;
- never write into `system_v4/probes`.

## Immediate Plan

1. Treat `candidate_with_gstack_20260514T005417Z.py` as separate sidequest
   evidence only, not as the current formal substrate.

2. Build/adapt a separate formal-scout harness around nested geometry +
   noncommutation + finitude, using sidequest output only as design input.

3. Keep formal promotion blocked until the scout harness survives graveyards and
   the API can be converted into a clean formal sim.

4. Continue naming cleanup only where it directly affects reused files.
   Do not let naming cleanup become the main work.
