# BUILD CARD - discrete_axis3_placement_v0

Source request: build the second axis packet from committed work order `f6112e407`, file-disjoint
inside `system_v6/sims/discrete_axis3_placement_v0/`, with no git add/commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=axis_readout_candidate_only`
- `promotion_allowed=false`
- `formal_admission_allowed=false`

## Authority Read Order

1. `system_v6/receipts/axis_work_order_20260612.md`
2. `system_v6/foundations/working_math_scaffold_20260609.md`
3. `system_v6/sims/discrete_axis0_field_v0/audit_verdict.md`
4. Family B Hopf object at commit hint `29e133f2f`
5. `hopf_base_section_phase_recovery_v0` at commit hint `7e78f3829`
6. Axis-0 response packet at commit hint `5d330b427`
7. Sequencing doctrine at commit hint `fcf1b3858`

## Object

Build a finite Axis-3 placement readout candidate on the committed Hopf carrier:

- `gamma_in`: density-stationary inner/fiber loop.
- `gamma_out`: density-traversing outer/base loop satisfying the computed horizontal condition
  `A(dot gamma_out)=0`.
- placement polarity: `-1` for fiber-placed, `+1` for base-placed, `0` for degenerate neutral.

The packet must keep the three-polarities discipline:

- Axis-3 placement is not Axis-0 response.
- Axis-3 placement is not Axis-6 precedence.
- Type1/2 inversion, L/R chirality, and flux in-out remain staged alternatives needing later
  discriminators.

## Required Checks

- Pin loop families before classification.
- Compute density stationarity for `gamma_in`.
- Compute horizontal condition and density traversal for `gamma_out`.
- Include placement-degenerate controls.
- Include shuffled-connection controls.
- Run one falsifier branch.
- Check nontrivial/nonfrozen loop dynamics.
- Carry independence rows against committed Axis-0 response data both directions where computable.
- Emit SMT computed bindings with real erased flips.
- Use the standard envelope helper and builder/audit boundary helper.
- Run local validator, generic three-engine validator, and pytest.
