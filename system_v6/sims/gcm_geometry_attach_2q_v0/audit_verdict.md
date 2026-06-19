# Independent Audit Verdict - gcm_geometry_attach_2q_v0

fresh audit / read-only audit. Auditor: independent Codex controller with three read-only
Codex sidecar lanes. Authorized live write: this file only. No git add/commit.

Bottom line: VERDICT = PASS_WITH_CAVEATS, not strict green.

The packet genuinely attaches a bounded 2Q geometry readout to the 544 survivors from
`gcm_constraint_carve_2q_v0`: 528 product rows factor through the committed 1Q attach
realization rule, 16 purification-boundary entangled rows carry subunit marginal radii and
Schmidt-angle/correlation-witness readouts, the cross-rung shell map lands in occupied 1Q
eta shells, substrate green/red passes, and G.2a is wired from birth.

The strict-green claim is rejected for three reasons:

1. The entangled rows are formulaic purification-boundary marginal-coordinate readouts.
   They recompute from `first_bloch` / `second_bloch`, not from stored 4x4 `rho_AB`,
   state-vector, amplitude, or actual-state hash rows in this packet.
2. Product marginal radii pass exact-class/tolerance control, but not literal JSON
   exactness: 600/1056 product A/B radii are literal `1.0`; all 1056 are within
   `1e-12`, with max error `9.992007221626409e-16`.
3. The 2Q freeze/cut registry is not landed. The provisional geometry IDs are
   content-derived and rename-matchable by row content, but they are not the exact planned
   `gcm2qsurv_*` IDs from the freeze lane and cannot be cited as landed registry IDs.

Accepted ceiling:
`scratch_diagnostic_carrier_and_pins_relative_2q_geometry_attach`.
`promotion_allowed=false`; `formal_admission_allowed=false`; not THE manifold; not
canonical geometry; not bridge/axis/stage/physics/formal admission evidence.

## Bound Inputs

- Standards codex: `system_v6/receipts/audit_standards_codex_v1.md`.
- NESTED definition: `system_v6/receipts/gcm_layer_stack_reference_20260612.md:45-49`.
- 1Q attach authority: commit `748fca97c`, especially the realization rule and mandatory
  G1 caveat.
- 2Q carve authority: commit `218fac1a1`, especially 544 survivors, 528 product + 16
  purification-boundary entangled split, and the prior rejection of strict-green wording.
- Current packet: `system_v6/sims/gcm_geometry_attach_2q_v0/*`.

## What Passed

Counts and no-write validation passed. Fresh in-process recomputation with the Makefile
interpreter returned:

```text
fresh_all_pass = True
validate_live_errors = []
fresh_counts = {
  survivor_count: 544,
  product_survivor_count: 528,
  entangled_survivor_count: 16,
  quotient_class_count: 8,
  entangled_fiber_count: 16,
  one_q_geometry_class_count: 8
}
result_sha256 recomputes against the live payload.
```

The live result records the same counts and controls
(`results/gcm_geometry_attach_2q_v0_results.json:60-105`), including substrate positive
green and lineage-free negative red (`:45843-45864`).

Product realization passes as a 1Q-authority factorization. The source applies the 2Q
first/second raw Bloch pins through `carve2q.probe_signature(...)` and then through
`attach1q.spinor_from_probe_signature(...)`
(`gcm_geometry_attach_2q_v0_common.py:268-287`, `:290-322`). A sidecar recomputed all 528
product rows against that actual source rule with `factorization_errors_actual_source=0`.
My sample of product rows `0,1,2,17,68,137,255,527` also matched the 1Q attach Bloch
directions within `2e-15`.

Cross-rung shell map passes. The occupied 1Q eta shells are
`0`, `pi/8`, `pi/4`, `3pi/8`, `pi/2`, and every product/entangled shell label in the
current 2Q cross-rung map lands inside that set
(`results/gcm_geometry_attach_2q_v0_results.json:284-319`). Sample rows:

```text
product sid 0: A=3pi/8, B=pi/4
product sid 1: A=3pi/8, B=3pi/8
product sid 17: A=3pi/8, B=0
entangled sid 528: A=3pi/8, B=0
entangled sid 529: A=pi/4, B=0
entangled sid 530: A=pi/8, B=0
entangled sid 531: A=3pi/8, B=0
```

G1 pattern honesty passes. The result explicitly says any shell/fiber pattern is a
`carved_support_signature_reading_until_proven_more` and forbids promotion to independent
manifold geometry (`results/gcm_geometry_attach_2q_v0_results.json:280-283`;
`gcm_geometry_attach_2q_v0_common.py:617-619`).

G.2a passes. The standards codex requires builder/audit separation and idempotency from
birth through `scripts/builder_audit_boundary.py`
(`audit_standards_codex_v1.md:152-178`). This packet carries
`no_builder_audit_verdict=true`, `no_builder_audit_verdict_envelope_gate=true`, and helper
delegation (`gcm_geometry_attach_2q_v0_common.py:648-658`; result `:60-69`). This file has
an independent/fresh/read-only audit header, so post-audit validation should remain
idempotent.

The three coordinates pass at scratch scope: `layers 3-12 + 17-18`,
`integrated-onto-the-carve`, `2Q` (`build_card.md:3-5`;
`gcm_geometry_attach_2q_v0_common.py:79-88`; result `:45865-45878`).

## Entangled Rows

The entangled rows pass as formulaic purification-boundary readouts, not as actual-state
rows.

The source path for each entangled row is `schmidt_row(row)`, which reads only
`row["first_bloch"]` and `row["second_bloch"]`, computes marginal radii, then derives
`theta`, `lambda_plus`, `lambda_minus`, and `sin_2theta`
(`gcm_geometry_attach_2q_v0_common.py:325-350`). The correlation witnesses are analytic
Schmidt-frame phase fixtures, and the fiber routine buckets rows by
`marginal_position["D_C2_x_D_C2"]` while copying those phase witnesses
(`gcm_geometry_attach_2q_v0_common.py:403-424`).

I recomputed six entangled rows from the freeze lane's density construction without writing
files. For survivor IDs `528,529,530,531,532,543`, the partial traces from
`density_for_survivor(...)` matched the emitted reduced Bloch vectors/radii and Schmidt
angles within tolerance. Example state/hash handles that can be recomputed but are not
carried by this packet:

```text
sid 528: rho_AB_id rhoAB2q_c3086b6709f4bfab6dd2; theta 0.261799387799149; sin2 0.5
sid 529: rho_AB_id rhoAB2q_0e5ee89b4947c13836fc; theta 0.392699081698724; sin2 0.707106781186547
sid 530: rho_AB_id rhoAB2q_2d347836f51d8e13895d; theta 0.261799387799149; sin2 0.5
sid 531: rho_AB_id rhoAB2q_2093a9fa866ca62dc2cc; theta 0.261799387799149; sin2 0.5
sid 532: rho_AB_id rhoAB2q_8c84a2fb009337d61790; theta 0.392699081698724; sin2 0.707106781186547
sid 543: rho_AB_id rhoAB2q_5aafcc40c72b62ef61b2; theta 0.261799387799149; sin2 0.5
```

Those handles come from the freeze lane's actual density path
(`gcm_2q_freeze_and_cut_v0_common.py:306-342`) and are not emitted in
`gcm_geometry_attach_2q_v0`. So the user-facing claim "from actual 2Q states by hash" is
not earned by this packet.

The marginal-pair fiber claim is computed, but its data ceiling is narrow. The current
result has 16 fibers and every one has `finite_carved_member_count=1`; no entangled
survivors share a marginal pair as carved members. Non-determination by marginals is shown
by analytic same-marginal/distinct-correlation phase witnesses, not by multiple carved
survivor rows over the same marginal pair (`results/gcm_geometry_attach_2q_v0_results.json:
321-360` for representative rows).

## Product Rows

Product rows pass the realization rule and fail only the strict literal reading of
"exact".

The mathematical/product-control reading is good: product rows use the verified 1Q attach
spinors by lineage, and all sampled rows have recomputed unit radii within `2e-15`. The
packet-wide control reports `all_exact_within_tolerance=true` with
`max_error=9.992007221626409e-16`
(`results/gcm_geometry_attach_2q_v0_results.json:92-96`).

But the emitted JSON is not literally exact for every product radius. Example:
row 0 side A has `pure_radius=0.999999999999999`, not `1.0`. Across all 1056 product
side-radii, a sidecar found 600 literal `1.0` values and 1056 within `1e-12`. Future
citations must say "unit-radius exact-class/tolerance control", not "every JSON radius is
literal 1.0".

## Provisional 2Q IDs

The freeze lane is not landed, and the current packet records that honestly:
`two_q_registry_dependency.status = not_landed_provisional_ids_derived`,
`sha256 = null` (`results/gcm_geometry_attach_2q_v0_results.json:46454-46458`).

The provisional geometry IDs recompute from the local source rule, but that rule is not the
same identifier rule as the freeze lane's planned survivor IDs:

- Attach geometry IDs use `gcm2qgeom_*` / `gcm2qent_*` over `family`, `candidate_id`,
  `first`, and `second`
  (`gcm_geometry_attach_2q_v0_common.py:301-304`, `:341-344`).
- Freeze survivor IDs use `gcm2qsurv_*` over the derived 2Q object id, raw survivor id,
  candidate id, family, scaled coordinates, probe signature, and entangled flag
  (`gcm_2q_freeze_and_cut_v0_common.py:378-405`).

No row-content mismatch appeared in an in-memory prospective registry build, so the
resolution should be rename-only by row content. It is not "same ID rule" and not a
landed-registry claim.

Concrete samples:

```text
sid 0:   geometry_id gcm2qgeom_478e7b6fb61d05603841; freeze_id gcm2qsurv_d0e240413ea2b2160413
sid 528: geometry_id gcm2qent_a8b9d75772684bcf8a7d; freeze_id gcm2qsurv_395f873a062ac2f6a173
```

## NESTED And Substrate

NESTED passes at the packet's scratch geometry-attach scope. The reference bar says nested
means same object/lineage, lower-to-upper maps, removal/quotient controls, and induced
geometry recomputed after constraints (`gcm_layer_stack_reference_20260612.md:45-49`).
This packet consumes the same `gcm_object_id`, carries the 1Q lineage maps and 2Q survivor
lineage, uses the 2Q carve as parent source, records carve-erasure loss of nested status,
and recomputes the geometry rows (`gcm_geometry_attach_2q_v0_common.py:580-640`).

Substrate enforcement passes. The live payload is green against
`gcmobj_a40e54e13cec01466c9d675028b3574b`, while the lineage-free variant is red with
missing id/hash/lineage errors (`results/gcm_geometry_attach_2q_v0_results.json:45843-45864`).

## Sidecar Receipts

Three read-only Codex sidecars returned:

- Entangled-row sidecar: FAIL for the "actual 2Q state data" bar; formula recomputation
  from Bloch scalars passes; `attach_rows_with_actual_state_key=0`; all fibers singleton.
- Product/ID sidecar: PASS for all 528 product factorizations and shell occupancy; FAIL
  strict literal radius exactness; conditional rename-only pass because freeze artifact is
  absent.
- Language/process sidecar: PASS for G1-pattern wording, G.2a, substrate green/red,
  coordinates, NESTED process, and no overclaim.

Wizard v4.2 route truth: PARTIAL. The controller loaded the v4.2 packet, ran local
recomputation, and spawned three Codex sidecars. No full nine-parent/child Max Assembly
matrix was run, so no FULL Wizard claim is made.

## Checks Run

No live result JSONs were rewritten. I did not run packet `main()` or pytest because the
user allowed only this audit file as a live write surface. Instead I ran no-write imports
and in-process recomputation:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import gcm_geometry_attach_2q_v0_common as common
live = load result JSON
fresh = common.build_packet()
print(fresh["all_pass"])
print(common.validate_payload(live))
PY
```

Result: `fresh_all_pass=True`; `validate_live_errors=[]`; live hash recomputed; product,
entangled, shell, fiber, substrate, z3, cvc5, and G.2a gates matched the live packet.

I also read the JAX/PyTorch/Julia engine lanes. They are acceptable at scratch scope, but
their observables are thin radius/count/fiber-incidence checks; they do not repair the
actual-state/hash caveat.

## Citation Rule

Allowed citation:

`gcm_geometry_attach_2q_v0` is a `PASS_WITH_CAVEATS` scratch diagnostic attaching bounded
2Q geometry readouts to the 544 2Q carve survivors: 528 product rows factor through the
committed 1Q attach realization rule, 16 purification-boundary entangled rows have
subunit marginal radii and formulaic Schmidt/correlation-witness readouts, the normalized
cross-rung shell map lands in occupied 1Q eta shells, and substrate/G.2a/NESTED-process
guards pass.

Required caveats on every citation:

- Entangled geometry is formulaic purification-boundary marginal-coordinate readout, not
  actual 2Q state/hash-carried evidence inside this packet.
- Finite carved marginal-pair fibers are all singleton; non-determination by marginals is
  analytic phase-witness evidence, not multiple carved survivors sharing one marginal pair.
- Product unit radii are exact-class/tolerance controlled, not all literal `1.0` in JSON.
- 2Q freeze registry is not landed; provisional geometry IDs are row-content renameable,
  not the final `gcm2qsurv_*` IDs.
- G1 caveat remains mandatory: shell/fiber patterns are carved-support signature readings
  until proven more.
- The prior 2Q carve's monogamy-type question remains open; this packet does not close it.

Forbidden citation:

Do not cite this packet as strict green, actual-state-derived entangled geometry, canonical
geometry, final 2Q registry landing, THE manifold, bridge/axis/stage/physics evidence,
monogamy evidence, formal admission, or proof that shell/fiber structure is independent
manifold geometry.
