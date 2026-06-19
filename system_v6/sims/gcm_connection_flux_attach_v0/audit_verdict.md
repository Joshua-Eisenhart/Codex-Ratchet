# Fresh Audit Verdict - gcm_connection_flux_attach_v0

Fresh audit / read-only audit except this file. Auditor: cross-backend auditor.
Freshness tier: TIER-2 results-available for packet internals; TIER-3 for resolving the
upstream attach verdict because the landed verdict was intentionally read as binding input.
Authorized live write: this file only. No git add/commit.

Bottom line: VERDICT = GENUINE-WITH-CAVEATS. The packet genuinely evaluates the S2/Hopf
connection `A`, curvature `F=dA`, lifted-cycle holonomy, adjacent shell strip flux, and
Stokes/leakage rows on the attached survivor loci. The exact shell holonomies match the
known closed forms for the five occupied shells, the lineage route survives substrate
enforcement green/red, and the three scoped lanes validate.

This is not admission. Claim ceiling:
`scratch_diagnostic_layers_10_12_1Q_connection_flux_carrier_and_pins_relative`;
`promotion_allowed=false`; `formal_admission_allowed=false`.

Mandatory inherited caveat: `G1_shell_pattern_is_carved_probe_support_signature`. The
attach verdict at `748fca97c` landed `gcm_geometry_attach_v0` as
`GENUINE-WITH-CAVEATS`, and every row here inherits that caveat: the `2-4-4-4-2` shell
pattern is the carved active-probe support's computed signature, not independent manifold
geometry.

Additional audit caveat: `G2_stale_conditionality_metadata`. The packet was built while
`gcm_geometry_attach_v0` was still in flight, and the build card/result/envelope still say
`audit_status=in_flight` and "conditional on its verdict." This audit resolves the
conditionality externally: the condition is satisfied only under the landed
`GENUINE-WITH-CAVEATS` attach verdict and its mandatory G1 caveat. Future packet metadata
should cite that resolved state directly.

## Checks Run

- Read-only packet validation functions with Makefile interpreter:
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.
  Result: `common.validate_payload=[]`, packet boundary errors `[]`, packet validator
  function errors `[]`, strict source-backed three-engine validator errors `[]`.
- Fresh substrate checks:
  real payload `ok=true`; lineage-free negative `ok=false` with `gcm_object_id mismatch`,
  missing registry hash, and missing lineage-consumption errors.
- Independent exact recomputation over existing JSON:
  max holonomy error `3.85e-16`, max curvature error `2.45e-16`, max `A_chi` error
  `4.44e-16`, max Stokes residual `0.0`.
- Five end-to-end lineage samples, one per shell:
  `survivor_id -> spinor_id -> quotient_class_id -> candidate_region_id -> T_eta -> flux row`
  all matched; spinor norm errors were `0` or `6.66e-16`.

I did not run `validate_gcm_connection_flux_attach_v0.py` as an entrypoint because it
rewrites `results/gcm_connection_flux_attach_v0_validator_results.json`, outside this
audit's allowed write scope. I called its validation functions read-only instead.

## Exact Values

The packet's emitted holonomy values match the closed form
`h(eta) = -2*pi*cos(2*eta)` for the five occupied shells:

| shell | packet h | exact target |
| --- | ---: | ---: |
| `0` | `-6.283185307179586` | `-2*pi` |
| `pi/8` | `-4.442882938158366` | `-pi*sqrt(2)` |
| `pi/4` | `0.0` | `0` |
| `3pi/8` | `4.442882938158366` | `pi*sqrt(2)` |
| `pi/2` | `6.283185307179586` | `2*pi` |

The curvature rows also match `F_eta_chi = -2*sin(2*eta)`:
`0`, `-sqrt(2)`, `-2`, `-sqrt(2)`, `0`, up to endpoint floating roundoff. The connection
rows match `A_chi = cos(2*eta)`.

The strip-flux rows are computed, not merely declared, but their meaning is narrow:
they are adjacent occupied-shell Stokes strip fluxes under the pinned S2 convention. They
are not a transport, terrain, runtime, chirality, memory, or QIT-engine leakage process.

## Reuse And Lineage

Formula reuse is honest enough for this ceiling. The packet source locks
`geo_s2_connection_flux_foliation_v0_jax.py` at SHA-256
`b2a5000e43537433f146622353be8d126ef6e823a186b1978af63e17a86cc93f`; git history shows the
S2 estate was committed at `5d8a6f1de` and later strengthened by Manifolds/Grassmann
addenda. The convention pins match the S2 build spec: accumulated lifted-cycle holonomy,
`chi:0->2pi`, `base_angle=2*chi`, and `F=-2*sin(2*eta)deta wedge dchi`.

Survivor-loci evaluation is real. The packet groups rows from
`gcm_geometry_attach_v0_results.json` by `T_eta_label`, carries survivor/class/region IDs
into each shell row, and recomputes `A_chi`, `F_eta_chi`, and `h(eta)` from each occupied
shell eta. The five sampled shell representatives reproduced the emitted row values.

## Fences

The Hermes flux split is respected. Packet language consistently scopes this as geometric
Hopf curvature flux only and explicitly excludes runtime/QIT/memory/chirality flux,
terrain admission, axis admission, physics admission, and formal admission.

The three required coordinates are declared:

- layer: `layers 10-12`;
- nesting: `integrated-onto-the-carve`;
- qubit depth: `1Q`.

G.2a passes. The builder emitted `builder_self_assessment.md`, not this audit verdict;
the packet delegates the audit-boundary check to `scripts/builder_audit_boundary.py`, and
the boundary check returned no errors.

## Citation Rule

Allowed citation:

`gcm_connection_flux_attach_v0` = `GENUINE-WITH-CAVEATS` scratch diagnostic for
geometric-only Hopf connection/curvature flux on the attached 1Q survivor loci. It
computes exact S2-pinned `A`, `F=dA`, lifted-cycle holonomy, adjacent occupied-shell strip
flux, and Stokes-closed leakage rows over the frozen `gcm_object_id` lineage.

Required caveats on every citation:

- `G1_shell_pattern_is_carved_probe_support_signature`: inherited from
  `gcm_geometry_attach_v0`; the shell pattern is the carved active-probe support's
  signature, not independent manifold geometry.
- `G2_stale_conditionality_metadata`: packet metadata still says the attach audit was in
  flight; this audit resolves that condition using the landed attach verdict.

Forbidden citation:

Do not cite this as THE manifold, independent shell law, runtime/QIT/chirality/memory flux,
terrain/stage/engine/axis admission, physics evidence, formal admission, or proof that 1Q
proves a layer.
