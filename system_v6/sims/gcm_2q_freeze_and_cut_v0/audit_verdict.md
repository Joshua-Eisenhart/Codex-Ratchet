# Independent Audit Verdict - gcm_2q_freeze_and_cut_v0

Audit mode: fresh read-only audit. The only repo write authorized for this audit is this
`audit_verdict.md` file. No git add, commit, or generated-result rewrite was performed.

## Bottom Line

VERDICT: MATH UNLOCK CONFIRMED, STRICT GREEN REJECTED.

The entropy unlock itself is real at `scratch_diagnostic` scope: the packet stores actual
2Q states, the A|B cut is pinned, the 16 entangled survivor negativities recompute from
the stored `rho_AB` matrices, all 528 product rows are PPT with negativity exactly `0.0`,
and the conditional/mutual/coherent information rows are available exactly because the
1Q ladder's missing bipartition/joint-state requirement is now supplied.

But the extended `scripts/gcm_substrate_check.py` is not enforcement-strict for the 2Q
rung. It closes the old object-id-only bypass for both rungs and preserves the old forged
1Q-registry closure, but it still accepts a forged self-consistent 2Q registry and it can
validate a 2Q-registry check with only 1Q lineage consumption. Therefore this packet is
not `strict green` as an enforcement packet.

Claim ceiling: `scratch_diagnostic_carrier_and_pins_relative_2q_registry_and_first_cut`.
No formal admission, no promotion, no "THE manifold", no axis/bridge/physics claim, and
no monogamy/CKW closure.

## Audit Basis

Bound sources checked:

- Standards codex including G.2a:
  `system_v6/receipts/audit_standards_codex_v1.md`
- 1Q freeze audit pattern and helper bypass regressions:
  `system_v6/sims/gcm_object_id_freeze_v0/audit_verdict.md`
- Entropy availability ladder unlock source, commit `c6155e4d7`:
  `system_v6/sims/gcm_entropy_family_sweep_v0/`
- 2Q carve audit source, commit `218fac1a1`:
  `system_v6/sims/gcm_constraint_carve_2q_v0/`
- Target packet:
  `system_v6/sims/gcm_2q_freeze_and_cut_v0/`
- Current helper SHA-256:
  `8b22bb90384cbfab07b08b4c9d0a9ca162e9211bca1bdb90c46673ffb4a25610`

Fresh read-only validator path:

- `validate_gcm_2q_freeze_and_cut_v0.validate_payload(...)`: `ok=true`, `0` errors
  before this audit verdict file was written.
- The same read-only `validate_payload(...)` path returned `ok=true`, `0` errors after
  this independent audit verdict file was written.
- The CLI validator main was not run because it writes validator-result JSON.
- Pytest was not run because the test suite includes writer paths.

## 1. Negativity Recompute From Stored States

PASS for the stored quantum rows.

I recomputed partial transpose on the stored `rho_AB` matrices, using the declared tensor
order `|00>, |01>, |10>, |11>` with index `2*A + B`.

Entangled survivor result:

- Entangled rows checked: `16/16`
- Maximum absolute delta against stored entropy/negativity fields: `5.80e-13`
- Maximum partial-trace delta against stored `rho_A` / `rho_B`: `1.42e-15`
- Structural values:
  - `8` rows at negativity `0.25`
  - `8` rows at negativity `0.35355339059327395`, i.e. `1/(2*sqrt(2))`

Rows at negativity `0.25`:

- `gcm2qsurv_395f873a062ac2f6a173` with `first_bloch_scaled=[-1,-1,-1]`
- `gcm2qsurv_21617854fdaa584d624b` with `first_bloch_scaled=[-1,-1,1]`
- `gcm2qsurv_46219f756205e283baa3` with `first_bloch_scaled=[-1,1,-1]`
- `gcm2qsurv_b57453033b6ca121e0ba` with `first_bloch_scaled=[-1,1,1]`
- `gcm2qsurv_88d1b3c9e8b09d35d5a1` with `first_bloch_scaled=[1,-1,-1]`
- `gcm2qsurv_9713960b95870153b284` with `first_bloch_scaled=[1,-1,1]`
- `gcm2qsurv_a881c6b12abf137de030` with `first_bloch_scaled=[1,1,-1]`
- `gcm2qsurv_53a98ad53613cd44c020` with `first_bloch_scaled=[1,1,1]`

Rows at negativity `1/(2*sqrt(2))`:

- `gcm2qsurv_79456cb8ae2f2db5481d` with `first_bloch_scaled=[-1,-1,0]`
- `gcm2qsurv_242dc13aa652bc016054` with `first_bloch_scaled=[-1,1,0]`
- `gcm2qsurv_d12604eaf6da0aeea9b1` with `first_bloch_scaled=[0,-1,-1]`
- `gcm2qsurv_df2d49b9eb669cb4c7c8` with `first_bloch_scaled=[0,-1,1]`
- `gcm2qsurv_d741e11ede860ab19c56` with `first_bloch_scaled=[0,1,-1]`
- `gcm2qsurv_661e0a93614dd27b30ee` with `first_bloch_scaled=[0,1,1]`
- `gcm2qsurv_0a0a018c1c6e386d9269` with `first_bloch_scaled=[1,-1,0]`
- `gcm2qsurv_45d4118545918cbf215d` with `first_bloch_scaled=[1,1,0]`

The split is structural, not incidental. The `0.25` family has three nonzero first-marginal
Bloch coordinates; after the packet's scale this gives marginal radius `sqrt(3)/2`.
The `1/(2*sqrt(2))` family has two nonzero first-marginal coordinates and one zero,
giving marginal radius `sqrt(2)/2`. For the stored purification-boundary construction,
the negativity follows the marginal Schmidt weights.

Product rows:

- Product rows checked: `528/528`
- Full product max negativity: `0.0`
- Full product minimum partial-transpose eigenvalue: `0.0`
- Deterministic sample of 20 product rows, first 10 and last 10 product entries:
  all recomputed negativity `0.0`, with nonnegative partial-transpose spectra.

## 2. Informative Entropy Rows And Ladder Conformance

PASS for the entropy unlock, at the stated cut-bound scope.

Six representative entangled rows were recomputed from stored `rho_AB`, `rho_A`, and
`rho_B`:

| survivor | negativity | S(A|B) | I(A:B) | I_c(A>B) |
| --- | ---: | ---: | ---: | ---: |
| `gcm2qsurv_395f873a062ac2f6a173` | `0.25` | `-0.245775366668469` | `0.491550733336940` | `0.245775366668469` |
| `gcm2qsurv_21617854fdaa584d624b` | `0.25` | `-0.245775366668469` | `0.491550733336940` | `0.245775366668469` |
| `gcm2qsurv_46219f756205e283baa3` | `0.25` | `-0.245775366668469` | `0.491550733336940` | `0.245775366668469` |
| `gcm2qsurv_79456cb8ae2f2db5481d` | `0.353553390593274` | `-0.416495530699687` | `0.832991061399374` | `0.416495530699687` |
| `gcm2qsurv_242dc13aa652bc016054` | `0.353553390593274` | `-0.416495530699687` | `0.832991061399374` | `0.416495530699687` |
| `gcm2qsurv_d12604eaf6da0aeea9b1` | `0.353553390593274` | `-0.416495530699687` | `0.832991061399374` | `0.416495530699687` |

The negative conditional entropy is a genuine witness for the entangled survivor rows.
This is exactly the family the 1Q entropy ladder gated behind a named bipartition/joint
state/channel/cut. The packet supplies that cut as `qubit A | qubit B` and stores
`rho_AB`, `rho_A`, and `rho_B` for all `544` survivor rows.

## 3. Helper Extension Regression

FAIL for strict helper enforcement.

Fresh adversarial checks against the current modified helper:

| check | result |
| --- | --- |
| Positive packet against 1Q registry | PASS |
| Positive packet against 2Q registry | PASS |
| 1Q object-id-only payload | FAIL as desired |
| 2Q object-id-only payload | FAIL as desired |
| Forged 1Q self-consistent registry with same IDs but changed content | FAIL as desired |
| Forged 2Q self-consistent registry with same IDs but changed content | FAIL: accepted as `ok=true` |
| 2Q registry check with only 1Q lineage consumption | FAIL: accepted as `ok=true` |
| Missing 2Q registry hash | FAIL as desired |

Root cause:

- The helper pins the 1Q registry to `EXPECTED_REGISTRY_BODY_SHA256`.
- For 2Q registries, it verifies only self-consistency of the registry body hash plus the
  base 1Q hash. It does not pin the expected 2Q registry hash.
- For 2Q registries, `resolved_lineage_count` is pooled across 1Q and 2Q IDs, so a payload
  can satisfy the "lineage consumption" requirement without consuming any `gcm_2q_*` row.

The runner audit's hash-drift note is therefore not just a harmless display-text issue
for this packet's enforcement claim. Old stored helper results may be semantically benign
for their own math, but they must not be cited as proving current strict 2Q substrate
enforcement. The geometry attach consumer is also not closed: it still records a provisional
2Q dependency / null SHA path and does not yet consume the landed state-bearing rows.

## 4. Registry Derivation, Lineage, And State Storage

PASS for the registry and stored-state carrier, with the helper caveat above.

Registry facts:

- `gcm_2q_object_id`: `gcm2qobj_715e9424ea66468243108751fb59395f`
- Registry body hash: `57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac`
- Counts: `544` survivors, `8` quotient classes, `6` candidate regions
- Families: `528` product-grid rows and `16` purification-boundary rows
- Registry rebuild from the 2Q carve result and 1Q freeze registry matched byte-level JSON
  structure under the packet common code.

The 2Q survivor IDs are content-derived. A scratch in-memory mutation of the first survivor
row changed its representative survivor id from `gcm2qsurv_d0e240413ea2b2160413` to
`gcm2qsurv_8198a50fb5317c4734aa`. The 2Q object id is derived from pinned upstream source
hashes and summary inputs; a downstream row-only mutation is not the same operation as
changing the upstream 2Q carve bytes.

Cross-rung lineage and 1Q regression:

- `partial_trace_A` image equals the 1Q survivor set.
- The 16 A-fibers each have the expected size `34`.
- Product-control embedding is `16/16`.
- All `544` result rows store `rho_AB`, `rho_A`, `rho_B`, and `rho_ids`.

State-storage distinction:

- The registry stores frozen IDs, hashes, coordinates, signatures, and class metadata.
- The real matrices needed by the 2Q attach handoff are stored in
  `results/gcm_2q_freeze_and_cut_v0_results.json`, not in the registry proper.
- A downstream geometry consumer must consume this state-bearing result surface or an
  equivalent state-bearing artifact, not just the registry metadata.

## 5. Monogamy And G.2a

PASS for overclaim control.

The packet correctly narrows monogamy to `OPEN_REQUIRES_3Q_FOR_CKW`. CKW monogamy requires
a three-party state with pairwise reductions such as `rho_AB` and `rho_AC`; a 2Q A|B cut
cannot close that claim.

G.2a is satisfied for this packet shape:

- The builder did not write `audit_verdict.md`.
- Boundary checks delegate to `scripts/builder_audit_boundary.py`.
- This file declares a fresh independent read-only audit in the header.
- Post-audit read-only `validate_payload(...)` returned `ok=true` with `0` errors.

## Citation Rule

Allowed citation:

> `gcm_2q_freeze_and_cut_v0` is a scratch-diagnostic 2Q freeze/cut carrier with
> `544/8/6` frozen rows, stored `rho_AB/rho_A/rho_B` states, exact A|B entropy rows,
> `528` product PPT-zero controls, and `16` purification-boundary entangled survivors
> split structurally into `8` at negativity `0.25` and `8` at `1/(2*sqrt(2))`.

Required caveat:

> The current helper extension is not strict-green enforcement: forged self-consistent
> 2Q registries and 2Q checks with only 1Q lineage can pass. Cite the entropy unlock as
> mathematically confirmed at scratch scope, not as helper-enforced admission.

Forbidden citation:

- Do not cite this as formal admission, a promoted object, THE manifold, geometry v1
  closure, axis/bridge/physics evidence, CKW monogamy closure, or strict-green helper
  enforcement.
- Do not cite downstream geometry attach as closed against this packet until it records
  the landed freeze/cut hash and consumes the state-bearing rows.

## Fresh Commands

Read-only commands and imports used:

- `sha256sum scripts/gcm_substrate_check.py ...`
- `jq` inspections of the target result, registry, controls, source locks, and prior audit
  surfaces.
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`
  scripts for:
  - partial transpose, eigenvalues, negativity, entropy, partial traces;
  - 20-row product PPT sample and all-528 product recomputation;
  - registry rebuild/hash checks and scratch mutation sensitivity;
  - helper adversarial controls against 1Q and 2Q registries.
- `validate_gcm_2q_freeze_and_cut_v0.validate_payload(...)` imported and run read-only.
