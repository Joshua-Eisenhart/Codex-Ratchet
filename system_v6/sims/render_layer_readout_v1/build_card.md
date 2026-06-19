# BUILD CARD - render_layer_readout_v1

Source request: build the re-pin after `render_layer_readout_v0` was killed as
`BY_CONSTRUCTION_DEGENERACY`, under `system_v6/sims/render_layer_readout_v1/`,
file-disjoint from v0, with no git add/commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=render-layer readout candidate only; no holodeck/FEP/physics/Axis-0 admission`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- Boundary helper: `render_layer_readout_v1_boundary.py` plus shared
  `scripts/builder_audit_boundary.py`.
- This builder card is not an independent audit verdict.

## Authority Read Order

1. `system_v6/sims/render_layer_readout_v0/audit_verdict.md`: v0 used the
   distance pin `norm(realized-render)-norm(render-source)`. On the committed
   carrier, dissipativity forced the positive `reshape_the_render` side
   unreachable across all 198 committed edges and all 33 start cells.
2. `system_v6/receipts/owner_doctrine_holodeck_render_layer_20260612.md`:
   expectation 1 remains earned at scratch ceiling, expectation 2 is void
   pending re-pin, and expectation 3 requires a readout that could vary.
3. `system_v6/sims/fiber_augmented_cover_v1/build_card.md`: witness gate
   before dependent rows, with failed controls refusing downstream tables.

## Re-Pin

v1 pins the polarity as a signed directional comparison on committed dynamics:

```text
direction = unit(render - source)
direction_scalar = dot(realized - render, direction)
                 = dot(realized - source, direction) - dot(render - source, direction)
```

Positive values are `reshape_the_render`; negative values are
`resist_the_update`; zero values stay neutral. This directly addresses the v0
failure because it does not compare two nonnegative distances whose geometry
can be forced one-sided. It asks whether the realized-state flow lands ahead of
or behind the committed render direction.

## Witness Gate

This is the reachability witness gate for the re-pinned polarity.

The packet computes `render_polarity_reachability_witness` over all committed
edge rows before emitting any readout table:

```text
if no committed-edge witness for reshape_the_render
or no committed-edge witness for resist_the_update:
    construction_status = repin_failed_unreachable
    readout_table_ran = false
    no render_readout / Axis-0 boundary rows are emitted
```

The old v0 distance pin is rebuilt as the negative control. It must reproduce
unreachable `reshape_the_render`, fail the v1 witness gate, and refuse readout
rows.

## Expectation 2 Re-Ask

Past the gate, v1 asks whether the render readout is:

- an alias into committed Axis-0 phi;
- its own readout family;
- or no stable distinction.

The scrambled-error control must now be able to break the readout. A constant
`constant-readout-not-breakable-no-stable` species is accepted only in the old
pin regression, never as an earned v1 readout.

## Controls

- Identity-dynamics degeneracy.
- Scrambled-error control.
- No-identity-leak field manifest.
- Positive predicate boundary control.
- v0 distance pin regression.

## Boundaries

Allowed claims:

- finite render/error/update machinery is reused by hash from v0;
- the v1 polarity has committed-dynamics witnesses for both values;
- the readout-boundary question is re-asked at scratch ceiling.

Disallowed claims:

- holodeck admission;
- FEP or physics admission;
- Axis-0 admission or CP.12 rescue;
- formal admission, canonical-by-process status, manifold claim, or bridge claim.

## Expected Commands

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/render_layer_readout_v1/render_layer_readout_v1_jax.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/render_layer_readout_v1/render_layer_readout_v1_pytorch.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/render_layer_readout_v1/render_layer_readout_v1_julia.jl
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/render_layer_readout_v1/render_layer_readout_v1_envelope.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/render_layer_readout_v1/validate_render_layer_readout_v1.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/render_layer_readout_v1/tests
```
