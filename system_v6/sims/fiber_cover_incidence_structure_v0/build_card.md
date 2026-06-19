# BUILD CARD - fiber_cover_incidence_structure_v0

Source request: build the topology guard repair prerequisite under
`system_v6/sims/fiber_cover_incidence_structure_v0/`, file-disjoint from
`topology_parity_cell_model_v1`, with no `git add` or commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=scratch_diagnostic_committed_incidence_structure_plumbing_only_no_betti`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- NO Betti computation in this packet.
- Boundary helper: `fiber_cover_incidence_structure_v0_boundary.py` plus shared
  `scripts/builder_audit_boundary.py`.
- G.2a from birth: validators/tests delegate builder/audit idempotency to the
  shared helper and do not hard-require permanent absence of `audit_verdict.md`.

## Authority Read Order

1. `0207fecaf`: `system_v6/sims/topology_parity_cell_model_v1/audit_verdict.md`
   rejects the old topology guard because its 33-face cellular boundary model
   was packet-introduced rather than derived from committed cover incidence.
2. `80860aa4f`: `system_v6/sims/fiber_augmented_cover_v1/` supplies the
   committed construction: 33 base states, 198 directed generator adjacency
   rows, `|F|=3`, and seam shifts `[1,1,1,0]` on the committed loop.
3. `system_v6/receipts/audit_standards_codex_v1.md`: G.2a binds from birth.

## Derivation Rule

The packet derives 2-cells only from committed cover-v1 construction rows:

```text
base C0 = committed 33 carrier cells
base C1 = committed 198 directed generator-labelled carrier edges
base C2 = all simple committed directed non-self 4-cycles in that adjacency
```

Every emitted 2-cell carries its four source edge ids, source vertices,
generator labels, and committed fiber-shift rows. No face is added by target
topology, desired Betti profile, or "sphere must close" reasoning.

Honesty boundary:

```text
derivation_introduced_count = 0
derivation_incomplete = true
exhaustive_for_declared_cycle_rule = true
exhaustive_as_base_s2_cell_structure = false
```

The packet therefore commits incidence plumbing, not an earned S2 homology
certificate. The Betti consumer remains blocked until an independent source-side
exhaustive 2-cell incidence structure is admitted.

## Total-Space Rule

The total chain complex is emitted as base cells x finite fiber cells:

```text
C0 = cover states = base vertices x fiber phase vertices
C1 = committed base-lift edges plus committed fiber-cycle edges
C2 = lifted base 2-cells plus edge x fiber squares
C3 = base 2-cell x fiber edge prisms
```

The gluing data is exactly the committed `chart_transition_rows` from
`fiber_augmented_cover_v1`: a base edge `a -> b` with shift `s` maps fiber phase
`p` to `p+s mod |F|`. The seam shifts are `[1,1,1,0]`; no Betti lane consumes
them here.

## Required Checks

- Every 2-cell traces to committed source rows.
- `derivation_introduced_count` is `0`.
- Explicit sparse boundary matrices are emitted and hash-pinned.
- `d1*d2=0` for the base complex.
- `d1*d2=0` and `d2*d3=0` for the total-space complex.
- Euler characteristic is reported as a derived check only, not as a target.
- No Betti field or Betti computation is emitted.

## Expected Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_cover_incidence_structure_v0/fiber_cover_incidence_structure_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_cover_incidence_structure_v0/fiber_cover_incidence_structure_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_cover_incidence_structure_v0/validate_fiber_cover_incidence_structure_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/fiber_cover_incidence_structure_v0/tests
```
