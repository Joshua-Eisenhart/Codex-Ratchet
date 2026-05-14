# Geometric Constraint Manifold Formal-Scout Contract

Status: working support doc
Scope: exploratory manifold/tower assembly before canonical promotion

## Purpose

Build the geometric constraint manifold as a rough executable object early
enough to guide exploration, without pretending the final proof or final layer
order is closed.

This contract defines the allowed middle:

- stricter than free-form `grok_sim` sidequest output;
- weaker than canonical `system_v4/probes` admission;
- useful for building candidate towers and killing bad orderings.

## Location

Formal-scout manifold harnesses live outside `system_v4/probes`, currently under:

`system_v5/ops/formal_scouts/`

They may read formal legos from `system_v4/probes`. They may not modify them.

## Minimum Object

A geometric-constraint-manifold scout must expose or write a result containing:

- finite carrier description;
- density-state validity check;
- nested layer list with parent links;
- Hopf projection readout;
- U(1) holonomy or connection readout;
- spinor or Weyl/chirality readout if available;
- at least one noncommuting transport/order readout;
- finite entropy or finite truncation readout;
- graveyard outcomes;
- explicit open choices.

## Hard Exploration Gates

These block even scout execution:

- missing result receipt;
- no claim ceiling;
- no `promotion_allowed: false`;
- hardcoded constants substituted for failed formal lego calls;
- no negative/graveyard controls;
- invalid density matrix if density claims are made;
- dimension mismatch hidden or ignored;
- missing parent links in a nested layer claim;
- no finite witness.

## Promotion Gates

These block formal promotion but do not block scout exploration:

- unique final layer order;
- full proof that the nesting is final;
- complete physical-evolution graveyard sweep;
- target-system interpretation;
- bridge/cycle/axis admission;
- all historical naming cleanup;
- final status of flux/chirality/inner-outer.

## Required Immediate Graveyards

Each scout tower should include nearby failures:

- identity layer stack: all layers identical;
- missing parent link: layer has no parent;
- zero holonomy: connection collapses;
- commuting transports: order readout collapses;
- invalid density: non-Hermitian, negative eigenvalue, or trace not one;
- dimension mismatch: operator and state dimensions disagree.

## Naming

Executable names must be literal math descriptions.

Good:

- `sim_nested_finite_geometry_holonomy_noncommutation_probe.py`
- `sim_hopf_connection_density_transport_order_probe.py`
- `sim_layered_entropy_strict_subset_parent_link_probe.py`

Bad:

- `sim_axis3_*`
- `sim_engine_*`
- `sim_gstack_*`
- `sim_rosetta_*`
- `sim_type1_type2_*`

Historical files may still have old names. Rename only when reused.

## Relationship To Grok/Gemini

Grok/Gemini may propose tower orders and attacks. Codex translates useful
proposal content into this formal-scout surface only after checking:

- formal lego paths;
- callable APIs;
- no-hardcoding;
- open-choice honesty;
- immediate graveyards.

Scout success means "worth hardening," not "admitted."
