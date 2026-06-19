# Independent Audit Verdict - gcm_geometry_attach_2q_v1

Fresh audit / read-only audit. Auditor: independent Codex controller with three
read-only Codex sidecar lanes. Authorized live write: this file only. No git add/commit.

Bottom line: VERDICT = PASS_WITH_BLOCKING_CAVEAT, not clean strict green.

The real-states geometry teeth pass. The v1 packet re-derives the entangled geometry from
stored `rho_AB`, `rho_A`, and `rho_B` under final `gcm2qsurv_*` IDs; all 16 entangled
rows reproduce the committed keystone split `8 @ 0.25` and `8 @ 1/(2*sqrt(2))`; the
Schmidt angles, reduced radii, matrices, fibers, final-ID replacement, and v0 regression
all check out. The v0 scalar derivation is vindicated as a numerical approximation, with
the advertised max metric diff `4.52e-13`.

The blocking caveat is substrate/lineage contract shape: with the hardened helper now in
the repo, the packet passes the default 1Q substrate check and the lineage-free negative
is red, but the same payload fails a direct 2Q-registry positive check with
`GCM2Q_LINEAGE_CONSUMPTION_MISSING`. The packet records 2Q survivor IDs under
`two_q_lineage`, while `scripts/gcm_substrate_check.py` consumes lineage IDs from the
top-level payload or `gcm_lineage`. The packet-local validator still passes because it
checks the 2Q object/hash directly and invokes the helper against the 1Q registry. That is
not enough to call the NESTED 2Q hardened-helper requirement fully satisfied.

Accepted ceiling:
`scratch_diagnostic_carrier_and_pins_relative_2q_geometry_attach`.
`promotion_allowed=false`; `formal_admission_allowed=false`; not THE manifold; not
canonical geometry; not bridge/axis/stage/physics/formal admission evidence. Current
checkout status is also workspace-local: `system_v6/sims/gcm_geometry_attach_2q_v1/` is
untracked.

## Bound Inputs

- Standards codex: `system_v6/receipts/audit_standards_codex_v1.md`.
- v0 cut/audit contract: commit `98c6e4874`, `system_v6/sims/gcm_geometry_attach_2q_v0/audit_verdict.md`.
- Registry keystone: commit `8326405e6`, `system_v6/sims/gcm_2q_freeze_and_cut_v0/`
  plus current `scripts/gcm_substrate_check.py`.
- Target packet: `system_v6/sims/gcm_geometry_attach_2q_v1/`.

Freshness tier: `TIER-3` annotation-verify. Prior audit surfaces were available during
this run, but the numeric geometry, IDs, validator path, and helper behavior below were
freshly recomputed/read in this audit.

## What Passed

Read-only validator import passed without rewriting result JSON:

```text
validate_gcm_geometry_attach_2q_v1.validate_payload(envelope)
read_only_validate_payload_ok = true
error_count = 0
```

The stored result and envelope both report:

```text
all_pass = true
classification = scratch_diagnostic
claim_ceiling = scratch_diagnostic_carrier_and_pins_relative_2q_geometry_attach
counts = 544 survivors, 528 product, 16 entangled, 16 entangled fibers,
         8 quotient classes, 8 one_q geometry classes
gcm_2q_object_id = gcm2qobj_715e9424ea66468243108751fb59395f
gcm_2q_registry_body_sha256 = 57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac
```

Three-engine envelope checks pass at scratch scope:

- `gcm_geometry_attach_2q_v1_julia_results.json`: `all_pass=true`.
- `gcm_geometry_attach_2q_v1_jax_results.json`: `all_pass=true`.
- `gcm_geometry_attach_2q_v1_pytorch_results.json`: `all_pass=true`.
- Envelope consensus says survivor, product, entangled, fiber, and 1Q-regression counts
  agree across lanes.

G.2a passes for builder/audit separation:

- `gcm_geometry_attach_2q_v1_boundary.py` delegates to `builder_audit_boundary_errors(...)`.
- Result fields include `no_builder_audit_verdict=true`,
  `no_builder_audit_verdict_envelope_gate=true`, and
  `builder_gates.G_2a_idempotency_from_birth=true`.
- This audit file has an independent/fresh/read-only header, so post-audit idempotency
  should remain valid.

## Real-State Geometry

I recomputed all 16 entangled rows from the stored matrices in the v1 result and checked
them against the freeze result. The prompt asked for six; the packet contains 16, so all
16 were audited.

Summary:

```text
entangled_rows = 16
negativity split = 8 @ 0.25, 8 @ 1/(2*sqrt(2))
theta families = pi/12 and pi/8
radius families = sqrt(3)/2 and 1/sqrt(2)
max theta delta vs stored = 1.277e-15
max radius_A delta vs stored = 4.441e-16
max radius_B delta vs stored = 1.110e-16
max Schmidt-negativity delta vs stored/freeze = 8.327e-16
max partial-transpose-negativity delta vs stored/freeze = 9.437e-16
max partial-trace rho_A delta from rho_AB vs stored rho_A = 1.413e-15
max partial-trace rho_B delta from rho_AB vs stored rho_B = 9.992e-16
v1 stored matrices vs freeze matrices = 0.0
```

Representative first six recomputations:

| survivor | raw | theta | radius A | radius B | negativity |
| --- | ---: | ---: | ---: | ---: | ---: |
| `gcm2qsurv_395f873a062ac2f6a173` | 528 | `0.261799387799149` | `0.866025403784439` | `0.866025403784440` | `0.25` |
| `gcm2qsurv_79456cb8ae2f2db5481d` | 529 | `0.392699081698724` | `0.707106781186548` | `0.707106781186548` | `0.353553390593274` |
| `gcm2qsurv_21617854fdaa584d624b` | 530 | `0.261799387799149` | `0.866025403784439` | `0.866025403784440` | `0.25` |
| `gcm2qsurv_46219f756205e283baa3` | 531 | `0.261799387799149` | `0.866025403784439` | `0.866025403784440` | `0.25` |
| `gcm2qsurv_242dc13aa652bc016054` | 532 | `0.392699081698724` | `0.707106781186548` | `0.707106781186548` | `0.353553390593274` |
| `gcm2qsurv_b57453033b6ca121e0ba` | 533 | `0.261799387799149` | `0.866025403784439` | `0.866025403784440` | `0.25` |

Source-path check: `schmidt_from_state_row(...)` reads `rho_AB`, `rho_A`, and `rho_B`,
reconstructs the pure state/coefficient matrix, derives the reduced eigensystem and
Schmidt bases, and computes Bloch vectors, radii, theta, and negativity from those
matrices. The expected negativity constants are used as family checks/labels, not as the
source of the computed negativity.

## v0 Regression And Final IDs

PASS.

The v0-vs-v1 regression block recomputes:

```text
row_count = 16
reported max_abs_metric_diff = 4.52e-13
recomputed max_abs_metric_diff from rows = 4.52e-13
max location = raw 529, gcm2qsurv_79456cb8ae2f2db5481d, radius_B
```

The final-ID resolution passes:

```text
product rows = 528
entangled rows = 16
new geometry IDs unique = 544
all new geometry IDs start with gcm2qsurv_
all product rows retain old gcm2qgeom_* only in replaces_v0_provisional_2q_geometry_id
all entangled rows retain old gcm2qent_* only in replaces_v0_provisional_2q_geometry_id
bad final/provisional ID rows = []
```

This resolves the v0 audit's rename-rule difference correctly in the geometry rows. v0's
scalar derivation may now be cited as a scalar-derived approximation/regression baseline
whose error bars are closed by v1 at max diff `4.52e-13`; it may not be cited as
actual-state-derived geometry or final-ID registry evidence.

## Conditionality

RESOLVED externally, stale internally.

The registry conditionality is resolved by the committed keystone `8326405e6`: the audited
2Q registry exists with object `gcm2qobj_715e9424ea66468243108751fb59395f` and body hash
`57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac`. This audit therefore
does not keep v1's claims conditional on an in-flight registry audit.

However, the v1 packet still contains stale conditional text/fields:

- `build_card.md` says claims remain conditional on the 2Q freeze/cut audit.
- `two_q_registry_dependency.claims_conditional_on_2q_registry_audit = true`.
- `two_q_lineage.claims_conditional_on_2q_registry_in_flight_audit = true`.
- `disallowed_claims` includes `2Q registry audit completion beyond the cited in-flight conditional`.

So the audit can uncondition the registry dependency for citation, but the packet source
should still be repaired before anyone calls the artifact language itself clean.

## NESTED And Substrate

PARTIAL.

The 2Q NESTED geometry content is present:

- real states: stored `rho_AB`, `rho_A`, `rho_B`, state vectors, Schmidt bases, and
  reduced matrices are carried in entangled rows;
- maps/coordinates: `layers 3-12 + 17-18`, `integrated-onto-the-carve`, `2Q`,
  `D(C^2) x D(C^2)`, normalized shell maps, reduced radii, and product Bloch pairs;
- removal control: carve-erasure records that geometry feedstock remains but nested
  attachment status is lost;
- recomputed geometry: entangled geometry is re-derived from stored states, and product
  rows are factored through the 1Q attach rule;
- G1-pattern language: shell/fiber patterns remain carved-support signature readings and
  are forbidden from independent manifold promotion.

The hardened-helper 2Q lineage requirement is not satisfied by the payload shape:

```text
gcm_substrate_check(v1_payload, 1Q registry) -> ok=true
gcm_substrate_check(lineage_free_variant, 1Q registry) -> ok=false
gcm_substrate_check(v1_payload, 2Q registry) -> ok=false
  error_codes = ["GCM2Q_LINEAGE_CONSUMPTION_MISSING"]
gcm_substrate_check(lineage_free_variant, 2Q registry) -> ok=false
  error_codes include ["GCM2Q_LINEAGE_CONSUMPTION_MISSING"]
```

Interpretation: the packet has the final 2Q IDs and directly checks the 2Q object/hash,
but it does not feed those IDs to the hardened helper where the helper expects them. The
fix is mechanical: expose the `gcm_2q_survivor_ids` or equivalent 2Q lineage IDs under
`gcm_lineage` or adjust the helper/payload contract explicitly, then require the positive
2Q helper check in the packet validator.

## Sidecar Results

Three read-only Codex sidecars returned:

- Numeric geometry sidecar: audited all 16 entangled rows; real-state geometry, Schmidt
  angles, radii, partial traces, and negativity split pass.
- Provenance/regression sidecar: v0 regression `4.52e-13` and final-ID replacement pass;
  packet still has conditional wording and is untracked.
- Contract sidecar: local validator, strict three-engine envelope, G.2a, G1 language, and
  default substrate green/red pass; no independent audit existed before this file.

Controller correction beyond sidecars: direct 2Q helper positive fails as described above.

Wizard v4.2 route truth: PARTIAL. The controller loaded the v4.2 packet, ran local
recomputation, and spawned three Codex sidecars. No full nine-parent/child Max Assembly
matrix was run, so no FULL Wizard claim is made.

## Citation Rule

Allowed citation:

`gcm_geometry_attach_2q_v1` is a workspace-local, independently audited
`PASS_WITH_BLOCKING_CAVEAT` scratch diagnostic that attaches 2Q geometry to the 544
landed 2Q survivors using final `gcm2qsurv_*` IDs; product rows factor through the 1Q
attach realization rule; all 16 entangled rows are re-derived from stored
`rho_AB/rho_A/rho_B`; the entangled rows reproduce the audited split `8 @ 0.25` and
`8 @ 1/(2*sqrt(2))`; and the v0 scalar approximation is closed as a regression baseline
with max diff `4.52e-13`.

Required caveats:

- Claim ceiling remains `scratch_diagnostic_carrier_and_pins_relative_2q_geometry_attach`.
- Current packet directory is untracked in this checkout.
- Stale conditionality language remains in the v1 packet even though `8326405e6` resolves
  the registry audit externally.
- The hardened 2Q helper positive check fails with `GCM2Q_LINEAGE_CONSUMPTION_MISSING`;
  do not cite this as clean NESTED 2Q helper compliance until repaired.
- G1-pattern caveat remains mandatory: shell/fiber patterns are carved-support signature
  readings until proven more.

Forbidden citation:

- Do not cite as formal admission, canonical geometry, THE manifold, bridge/axis/stage/
  physics evidence, or lineage-free geometry admission.
- Do not cite v0 as actual-state-derived geometry. v0 is now citeable only as the
  scalar-derived baseline/error-bar predecessor vindicated by v1's state-derived
  regression.

## Checks Run

Read-only commands/imports used:

```text
git status --short -- system_v6/sims/gcm_geometry_attach_2q_v1 ...
git log --oneline -- system_v6/sims/gcm_2q_freeze_and_cut_v0/audit_verdict.md ...
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
  import validate_gcm_geometry_attach_2q_v1
  validate_payload(envelope)
PY
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
  recompute partial traces, Schmidt eigensystems, radii, partial-transpose negativities
PY
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
  recompute v0 regression row max and final/provisional ID replacement
PY
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
  run gcm_substrate_check against 1Q and 2Q registries, positive and lineage-free variants
PY
```

I did not run the packet CLI validator or pytest because those writer paths update
validator-result JSON, and the user allowed only this audit file as a live write surface.
