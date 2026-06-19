# Independent Audit Verdict - `gcm_flux_strips_v0`

audit_status: independent audit verdict
freshness_tier: TIER-2 results-available
audit_mode: read-only audit except this verdict file
standards_codex: `system_v6/receipts/audit_standards_codex_v1.md`
binding_boundary: G.2a builder/audit separation and post-audit idempotency

Bottom line: VERDICT = GENUINE-WITH-CAVEATS at `scratch_diagnostic_layers_10_12_1Q_complete_geometric_flux_strip_table` ceiling. The closed-form strip math verifies for all ten increasing occupied-shell pairs, the old "leakage" rows are genuinely closed Stokes residuals at <= `1e-15`, the packet consumes the frozen 1Q registry with a green positive and red lineage-free negative, the geometric-flux-only fence is present, the coordinates/formula pin are declared, and the stored upstream source-lock hashes still match current disk. Caveats: the curvature integral is the orientation-opposite Stokes term, so citations must say `h_delta + int_F = 0` rather than same-sign equality; the packet predates or bypasses the post-G.2a helper pattern because it has no `builder_audit_boundary.py` delegation and no `no_builder_audit_verdict` field; and a fresh no-write rebuild under the current helper differs only in substrate-helper diagnostic shape after later `error_codes` hardening.

## Scope

This backfills the missing independent audit for commit `e6ac0d5f9`. The old controller/Fable spot-check is not treated as authority.

The audit did not run a full Wizard v4.2 Max Assembly because this runtime had no Codex-native subagent spawn receipt surface. This is a controller-led partial Wizard audit with fresh local commands, independent arithmetic, and explicit caveats.

## Math Recompute

Closed form used independently:

- `eta in {0, pi/8, pi/4, 3pi/8, pi/2}`
- `h(eta) = -2*pi*cos(2*eta)`
- stored/source orientation: `h(eta_j)-h(eta_i) + int_[eta_i,eta_j] F = 0`
- therefore `int_F = -[h(eta_j)-h(eta_i)]` for the packet's orientation.

Fresh independent closed-form rows:

| strip | `h_delta` | `int_F` | residual |
|---|---:|---:|---:|
| `0 -> pi/8` | `1.84030236902122` | `-1.84030236902122` | `2.22e-16` |
| `0 -> pi/4` | `6.28318530717959` | `-6.28318530717959` | `8.88e-16` |
| `0 -> 3pi/8` | `10.726068245338` | `-10.726068245338` | `0` |
| `0 -> pi/2` | `12.5663706143592` | `-12.5663706143592` | `0` |
| `pi/8 -> pi/4` | `4.44288293815837` | `-4.44288293815837` | `0` |
| `pi/8 -> 3pi/8` | `8.88576587631673` | `-8.88576587631673` | `0` |
| `pi/8 -> pi/2` | `10.726068245338` | `-10.726068245338` | `0` |
| `pi/4 -> 3pi/8` | `4.44288293815837` | `-4.44288293815837` | `0` |
| `pi/4 -> pi/2` | `6.28318530717959` | `-6.28318530717959` | `0` |
| `3pi/8 -> pi/2` | `1.84030236902122` | `-1.84030236902122` | `-4.44e-16` |

Hand spot checks:

- `0 -> pi/8`: `h(pi/8)-h(0)=1.84030236902122`; `int_F=-1.84030236902122`; sum `2.22e-16`.
- `0 -> 3pi/8`: `h(3pi/8)-h(0)=10.726068245338`; `int_F=-10.726068245338`; sum `0`.
- `pi/8 -> 3pi/8`: `h(3pi/8)-h(pi/8)=8.88576587631673`; `int_F=-8.88576587631673`; sum `0`.
- `3pi/8 -> pi/2`: `h(pi/2)-h(3pi/8)=1.84030236902122`; `int_F=-1.84030236902122`; sum `-4.44e-16`.

The stored table matches the independent closed-form table after the packet's 15-digit quantization. Stored max absolute Stokes residual is `1e-15`.

## Leakage Closure

PASS. The packet does not merely relabel an open leak. Every row has `leakage_adjudication.status = closed_no_leakage`, `stokes_verified = true`, and `abs(stokes_residual) <= 1e-15`. The correct reading is closed geometric Stokes residual, not transport/runtime leakage.

## Substrate Lineage

PASS. Fresh helper checks:

- positive payload: `ok=true`, registry `gcmobj_a40e54e13cec01466c9d675028b3574b`, body hash `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`;
- lineage-free variant: `ok=false` with current error codes `GCM_OBJECT_ID_MISMATCH`, `GCM_LINEAGE_REGISTRY_BODY_SHA256_MISSING`, and `GCM_LINEAGE_CONSUMPTION_MISSING`.

The committed negative result predates later helper `error_codes` output and has older prose formatting, but the polarity and failure reasons are the same.

## Fence, Coordinates, And G2

PASS for the substantive fence:

- geometric flux only; no runtime/QIT/memory/chirality/terrain/axis/physics/formal-admission flux;
- axis declaration: `layers=10-12`, `nesting=integrated`, `qubit_depth=1Q`;
- coordinate/formula pin: `A = d phi + cos(2*eta) d chi`, `F = -2*sin(2*eta) d eta wedge d chi`, and `h(eta) = -2*pi*cos(2*eta)`;
- G2 metadata is corrected to landed geometry attach commit `748fca97c` and contains no `in_flight` status.

## G.2a

CAVEAT, not math rejection. The standards codex requires new validators/tests to delegate `audit_verdict.md` handling to `scripts/builder_audit_boundary.py` from birth and to use the post-audit idempotency pattern. This packet has no hard `audit_verdict.md` absence assertion and had no committed `audit_verdict.md`, but I found no `builder_audit_boundary.py` use, no `no_builder_audit_verdict` field, and no build-card G.2a statement in this packet.

This means the builder/audit boundary was not wired in the current post-G.2a shape. Because there is no evidence that the builder wrote an audit verdict and the validator still accepts a later independent audit, this is a standards caveat rather than a result kill.

## Freshness

PASS with caveat.

Fresh hash checks of stored source locks all matched current disk:

| lock | stored commit | hash status |
|---|---:|---|
| registry | `d9771ebe9` | match |
| connection flux attach result | `5afa1ea53` | match |
| connection flux attach audit | `5afa1ea53` | match |
| geometry attach result | `748fca97c` | match |

Fresh no-write rebuild matched the stored strip table, classification, claim ceiling, fence, formula pin, leakage summary, G2 metadata, validator errors, and `all_pass`. It differed only in `substrate_enforcement` diagnostic shape because `scripts/gcm_substrate_check.py` was later hardened to emit stable `error_codes`.

## Commands

Fresh commands run from `/Users/joshuaeisenhart/Codex-Ratchet`:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# independent closed-form recompute, stored-table comparison, no-write build_payload(write=False),
# validate_payload(live), and source-lock hash checks
PY
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# stored validate_payload, fresh gcm_substrate_check positive,
# and fresh lineage_free_variant negative
PY
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# validate_gcm_flux_strips_v0.validate(write=False)
PY
```

```text
PYTHONPATH=system_v6/sims/gcm_flux_strips_v0:/Users/joshuaeisenhart/Codex-Ratchet/scripts \
  /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  -m pytest -q system_v6/sims/gcm_flux_strips_v0/tests/test_gcm_flux_strips_v0.py
```

Results: validator `ok=true`; tests `3 passed`; stored packet tracked clean before this audit file was written.

## Citation Rule

May cite only as: "GENUINE-WITH-CAVEATS scratch diagnostic complete geometric Hopf curvature strip table over the pinned 1Q GCM lineage; all ten occupied-shell strips close by `h_delta + int_F = 0` with max residual `1e-15`; geometric curvature flux only, not runtime/QIT/terrain/axis/physics flux; consumes 1Q registry with positive green and lineage-free red; carries G2 landed-commit correction to `748fca97c`; carries G.2a helper-pattern caveat and current-helper diagnostic-shape freshness caveat."

Do not cite as runtime flux, leakage dynamics, transport leakage, manifold evidence, terrain/axis admission, physics evidence, bridge evidence, promotion, formal admission, or same-sign equality between `h_delta` and `int_F`.
