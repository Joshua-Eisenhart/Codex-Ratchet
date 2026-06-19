# Independent Audit Verdict - gcm_ring_checkerboard_runner_v1

Fresh/read-only audit except this file. Auditor: independent Codex audit. No git add/commit.

Bottom line: VERDICT = GENUINE-WITH-CAVEATS, but not literal `strict green` under the current checkout. The core v1 repair survives: the redesigned pinned AABB paired schedule moves 16/16 frozen survivor states with period spectrum `[4]`; the unchanged carved alternating row reproduces period `[2]`; the strict ring-adjacent variant passes the panel-11 one-site-per-half-step witness and is not vacuous. The caveat is decisive: period 4 is earned only as a pinned brickwork/ring-adjacent fixture on the frozen 16-cell object, not as an independent discovery of doctrine periodicity.

Claim ceiling:
`scratch_diagnostic`; `carrier-and-pins-relative`; frozen 16-survivor CA run-surface only; `promotion_allowed=false`; `formal_admission_allowed=false`; not THE manifold; not full CA field dynamics; not QCA/GNVW; not runtime flux; not terrain/axis/physics admission.

Freshness tier: `TIER-3` by the standards codex, because the v0 audit and builder result surfaces were intentionally loaded as binding context. The decisive rows below were independently recomputed read-only with `PYTHONDONTWRITEBYTECODE=1` and the Makefile interpreter `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.

## Periodicity And Design Honesty

Accepted with the above ceiling.

Fresh recomputation from `gcm_ring_checkerboard_runner_v1_common.py`:

| row | moved | fixed | period spectrum | adjudication |
|---|---:|---:|---:|---|
| carved `alternating_AB` | 16 | 0 | `[2]` | unchanged v0 live row reproduced |
| redesigned `paired_nontrivial_AABB` | 16 | 0 | `[4]` | non-identity repair succeeds |
| old/v0 `AABB` refusal | 0 | 16 | `[1]` | honest dead-rule refusal |
| strict `ring_local_AB` | 16 | 0 | `[8]` | nonvacuous strict-local variant |

The v1 paired schedule is derived in-source as four ring-adjacent subphases:
`A_open_ring_pairs`, `A_close_ring_pairs`, `B_open_ring_pairs`, `B_close_ring_pairs`.
This is a legitimate closed pin against the v0 failure mode where `AABB` reused identical involutive A/B maps and collapsed to identity.

But the period-4 row is still implementation-correctness, not discovery. The doctrine/provenance surface supports alternating-vs-paired readout grammar and the standard-math brickwork alignment, while also warning that period-2-vs-4 is a definitional-circularity species when the schedule makes that ratio analytically unreachable. Safe wording is: v1 restores a nonvacuous pinned AABB/brickwork period-4 fixture on the frozen GCM object. Do not cite it as an independently discovered doctrine theorem.

## Panel-11 Locality

Accepted for the strict ring-local variant.

Fresh witness recomputation:

| half-step | disjoint pairs | all cells exactly once | bad cyclic distances | max cyclic distance |
|---|---:|---:|---:|---:|
| A | 8 | yes | 0 | 1 |
| B | 8 | yes | 0 | 1 |

The strict variant therefore passes the two panel-11 teeth: disjoint-pair independence and one-ring-site light-cone speed. It also preserves `M(C)` and moves 16/16 states, so it is not a barely-moving/vacuous locality row.

This does not retroactively make the carved-adjacency A/B row ring-local. The strict row is a separate ring-adjacent variant; the carved row remains local only relative to the carved block graph.

## Presentation Equivalence

Accepted at frozen-object ceiling.

All three rows are present and computed on the frozen object:

- `flat_nested_checkerboard -> nested_rings_torus_loops`
- `nested_rings_torus_loops -> spherical_checkerboard`
- `flat_nested_checkerboard -> spherical_checkerboard`

I recomputed the flat-to-spherical row end-to-end from emitted cells: 16 unique survivor cells, 16 lineage object maps, parity equals `ring_index mod 2`, shell IDs are present for all cells, and the occupied shell count is 5. The declared row matches the recomputation.

This is not a global equivalence theorem for all ring-checkerboard presentations. It is a frozen 16-cell support equivalence receipt.

## Preservation, Controls, Substrate

Accepted mechanically.

Per-rule `M(C)` preservation recomputed green for all five rules: `A_half_step`, `B_half_step`, `alternating_AB`, `paired_nontrivial_AABB`, and `ring_local_AB`. Each maps into 16 images with zero violations under carve predicate hash `9be02933ef7e99fc92e519008528a89a5a6a291120772ae58dc90d76cf5b0747` and constraint ids `C1_finite_density_carrier`, `C2_probe_distinguishability_xz_local_adapter_pin`, `C3_persistence_n01_order_gap`.

Sampled paired AABB images for raw survivor ids 0-7 all preserve `M(C)`, e.g. `0 -> 4`, `1 -> 13`, `2 -> 6`, `3 -> 15`, `4 -> 8`, `5 -> 1`, `6 -> 10`, `7 -> 3`, all with known survivor ids.

Controls carried:

- all-to-all/global successor control: period `[16]`, `carved_edge_subset=false`;
- phase-merge control: period `[1,2]`, changed versus both alternating and paired;
- carve-erasure control: lineage-free negative expected red;
- strict locality obstruction row: `not_needed_passed`;
- GNVW: `named_not_run`, correctly fenced to later 2Q-plus/open-chain QCA work.

Substrate enforcement recomputed semantically green/red: positive lineage payload `ok=true`; lineage-free negative `ok=false`; `negative_failed_as_required=true`.

## Strict Green Caveat

The stored validator result says `ok=true`, but a read-only call to the current validator logic now returns:

```text
would_validate_ok_now=false
errors=[
  "payload drifted: substrate_enforcement",
  "payload drifted: result_sha256",
  "envelope drifted: result_sha256"
]
```

The drift is not a mathematical failure in the runner. It comes from the currently modified `scripts/gcm_substrate_check.py`, which formats the lineage-free negative object-id error as `cited=[] registry=[...]` instead of the stored `cited=None registry='...'`; after normalizing that negative error text, stored and rebuilt payloads are semantically equal. Still, the literal `strict green` claim is stale in this checkout until the result/envelope/validator receipt are regenerated or the helper drift is otherwise reconciled. This audit was not authorized to rewrite those JSON files.

G.2a is clean: the builder did not write this file, the packet uses `scripts/builder_audit_boundary.py`, and pre-audit boundary errors were empty. This header declares independent/read-only audit status, so post-audit idempotency should be acceptable once the validator drift above is repaired.

## Citation Rule

Allowed citation:

`gcm_ring_checkerboard_runner_v1` is a GENUINE-WITH-CAVEATS scratch diagnostic showing a nonvacuous pinned AABB/brickwork paired schedule on the frozen GCM 16-survivor object: paired AABB moves 16/16 states with period `[4]`, alternating AB remains period `[2]`, strict ring-adjacent half-steps pass panel-11 locality witnesses, all scoped rules preserve the C1-C3 carve predicates, and substrate enforcement is semantically green/red.

Required caveats:

- period `[4]` is implementation-correctness for a pinned brickwork/ring-adjacent schedule, not independent doctrine discovery;
- current stored strict-green validator status is stale because `substrate_enforcement` error-text drift changes `result_sha256`;
- frozen 16-cell carrier-and-pins-relative support only;
- presentation equivalence is frozen-object only, not a global theorem;
- strict ring-locality belongs to the new ring-adjacent variant, not the original carved-adjacency A/B row;
- QCA/GNVW is named-not-run; no runtime flux.

Forbidden citation:

Do not cite this as THE manifold, formal admission, full CA field dynamics, global three-presentation equivalence, QCA/GNVW index evidence, runtime/QIT flux, terrain/axis/physics admission, or proof that period-4 was discovered rather than schedule-pinned.
