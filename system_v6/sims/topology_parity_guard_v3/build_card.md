# Build Card - topology_parity_guard_v3

Source request: build `topology_parity_guard_v3` under
`system_v6/sims/topology_parity_guard_v3/`, file-disjoint, with no `git add`
or commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=scratch_diagnostic_consumer_guard_only_no_new_construction`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- Single-engine Python is allowed.
- This packet is an adjudicating consumer over hash-pinned
  `fiber_augmented_cover_v2_1` complexes. It introduces no replacement cells,
  no target Betti fitting, and no work-order update.
- NO new construction.
- Boundary helper: `topology_parity_guard_v3_boundary.py` plus
  `scripts/builder_audit_boundary.py`.
- G.2a from birth: validators and tests delegate audit-file handling to the
  shared helper and never require permanent absence of `audit_verdict.md`.

## Authority Read Order

1. `system_v6/sims/fiber_augmented_cover_v2_1/build_card.md` and
   `system_v6/sims/fiber_augmented_cover_v2_1/audit_verdict.md` at
   `eb96d0e87`: v2.1 emits four metadata hash-pinned complexes; the audit
   caveat is that the three controls are mutually isomorphic expected data and
   all unthreaded. The required addition is a math-content separability check
   hashing only boundary matrices, not metadata.
2. `system_v6/sims/topology_parity_guard_v2/audit_verdict.md` at
   `2137ae3e8`: old v2 computed product homology with no torsion and forced
   the torsion-aware v3 pre-registration.
3. `system_v6/receipts/axis_work_order_20260612.md`: the two-reading section
   says guard v3 adjudicates whether the repaired shifted complex earns a real
   finite certificate or whether cover labels must re-issue.
4. `system_v6/receipts/audit_standards_codex_v1.md`: standards codex and G.2a
   bind from birth.

## Pre-Registration Before Computation

Expected shifted-repair complex:

- input row: `v2_1_shifted_degree_one_mod3`
- stored chain hash:
  `6afe8ea8f778ae9f470354a641a8989e40868df5efa8c9792fcdd2eb25c3c75a`
- expected Betti: `[1,0,0,1]`
- expected torsion: `H1 = Z/3`; `H0`, `H2`, and `H3` have no torsion
- interpretation: lens-space `L(3,1)` profile, the mod-3 generator clutching's
  homology

Expected controls:

- `zero_shift_product_control`
  (`5315bd250363ab44ed209f9102f9f00f8a7aad72105fdb95452d9b1a5ae5bd76`)
- `wrong_gluing_generator_not_threaded_control`
  (`856ae6b070b7227dfff272c7e587f08d63cf06563d0a8394084baef782f64b8d`)
- `old_v2_regression_coboundary_control`
  (`151c47084f246e24665e80728a6c5492fdbe7feaecd96cbcdb6e94242b68d0d5`)
- expected Betti for each: `[1,1,1,1]`
- expected torsion for each: none
- expected mutual relation: their pure boundary matrices are identical and
  therefore mutually chain-isomorphic as expected unthreaded product controls.

Adjudication rule:

- If shifted computes the lens-space profile `[1,0,0,1]` with `H1=Z/3`, then
  `READING_A_REPAIRED_WINS`: the finite SECOND certificate is earned as guard
  data by homology torsion, the instrument the degree-2 trap taught.
- If shifted computes the product profile `[1,1,1,1]` with no torsion, then
  `READING_B_WINS`: even the generator re-pin loses structure in this encoding,
  and the cover labels must re-issue.
- Anything else is reported straight as `UNEXPECTED_PROFILE`.

## Packet Requirements

1. Load all four v2.1 complexes by stored hash; any mismatch is a stop.
2. Add the math-content separability row: boundary-matrix-only hashes must
   produce exactly two pure complexes, one shifted and one shared control class.
3. Run the reference gate before cover rows:
   - explicit `S3` reference;
   - explicit `S2xS1` reference;
   - explicit lens-space `L(3,1)` reference that recomputes `[1,0,0,1]` plus
     `H1=Z/3` through the same machinery.
   If the lens reference fails, the result is `machinery_insufficient`.
4. Compute full `H_*` with Smith normal form torsion for all four consumed
   complexes.
5. Carry the degree-2 torsion trap and Euler cross-checks.
6. Emit result JSON, envelope JSON, packet validator receipt, tests, and
   `builder_self_assessment.md`.

## Boundaries

Allowed claims:

- scratch-diagnostic consumer homology of the four hash-pinned v2.1 complexes;
- torsion-aware integer homology from explicit boundary matrices;
- math-content separability of the emitted complexes by boundary-matrix-only
  hashes;
- adjudication of the two readings under the pre-registered rule.

Disallowed claims:

- new construction;
- target Betti fitting;
- formal admission;
- canonical by process;
- work-order update;
- topology admission beyond this consumer guard;
- bridge, physics, manifold, or axis-level closure.

## Expected Commands

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_guard_v3/topology_parity_guard_v3.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_guard_v3/topology_parity_guard_v3_envelope.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_guard_v3/validate_topology_parity_guard_v3.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/topology_parity_guard_v3/tests
```
