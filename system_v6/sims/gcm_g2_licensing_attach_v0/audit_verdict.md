# Independent Audit Verdict - gcm_g2_licensing_attach_v0

Audit status: independent audit verdict; fresh audit; read-only audit except this file.

## Bottom Line

Verdict: GENUINE-WITH-CAVEATS as a `scratch_diagnostic_carrier_and_pins_relative_g2_compatibility_layer`.

The packet earns only this claim:

> A pinned convention-only 7D real readout subspace `W_A` inside the 63 traceless 3Q Pauli span, equipped with the pinned 3-form `phi = e123+e145+e167+e246-e257-e347-e356`, passes the packet-local standard G2 licensing tests against the landed 3Q survivor carve.

It does not earn:

- natural `W_A` from owner/canon sources;
- "G2 attaches to THE manifold";
- canonical G2 layer admission;
- compact/split theorem status;
- Spin(7), triality, F4, bridge, axis, or physics promotion.

The headline red stays red: `natural_W_A_from_owner_sources=false` is present in the result and envelope, and the claim ceiling keeps the packet carrier-and-pins-relative.

## Binding Sources Checked

- Nesting law G2 licensing source: `system_v6/receipts/nesting_law_final_object_spec_20260612.md`, source lock commit `afe7aa57b`, requires an explicit 7D real readout space in `span{P_alpha}`, the pinned 3-form, 3-form preservation, cross-product closure, associator visibility/erasure, and compact-vs-split branch.
- Standards codex G.2a: `system_v6/receipts/audit_standards_codex_v1.md`, file/builder boundary and post-audit idempotency rules.
- S10 feedstock: `system_v6/receipts/s10_g2_family_mine_20260610.md` plus `system_v6/sims/geo_s10_g2_family_v0/results/geo_s10_g2_family_v0_envelope_results.json`, especially the Der(O) estate.
- 3Q substrate: `system_v6/sims/gcm_constraint_carve_3q_v1/results/gcm_constraint_carve_3q_v1_results.json`.

## Licensing Honesty

Pass, with the convention-only ceiling.

The live result reports:

- `classification=scratch_diagnostic`;
- `claim_ceiling=scratch_diagnostic_carrier_and_pins_relative_g2_compatibility_layer`;
- `promotion_allowed=false`;
- `formal_admission_allowed=false`;
- `carrier_and_pins_relative=true`;
- `not_THE_manifold=true`;
- `licensing.natural_W_A_from_owner_sources=false`;
- `licensing.pinned_convention_flagged=true`.

`W_A = span{XII, ZII, IXI, IZI, IIX, IIZ, XXX}` is explicit and 7D inside the 63 traceless 3Q Pauli span. Its visible motivation is structural but not owner-sourced: six local single-qubit `X/Z` pins plus a global `XXX` parity/GHZ-flavored pin. That is enough for an explicit convention, not enough for a natural/canonical pinning claim.

Fresh readout check over the 3Q survivor states found readout rank `6` and active-axis count `6`; `IIX` is inactive in this survivor readout. That does not kill the explicit 7D convention test, but it reinforces the ceiling: the subspace is pinned as a coordinate convention, not discovered as a fully active natural readout.

## 3-Form And Cross Product

Pass.

I recomputed the 3-form tensor from the terms:

- `phi(e1,e2,e3)=1`;
- `phi(e1,e4,e5)=1`;
- `phi(e1,e6,e7)=1`;
- `phi(e2,e5,e7)=-1`;
- antisymmetry sample: `phi(e2,e1,e3)=-1`.

Using `g(x cross y,z)=phi(x,y,z)` with the standard metric on pinned `W_A`, fresh samples were:

- `e1 cross e2 = e3`;
- `e2 cross e1 = -e3`;
- `e1 cross e6 = e7`;
- `e2 cross e5 = -e7`.

The packet reports all `21` basis pairs closed in `W_A`, and the recomputed samples agree with that closure.

## Derivation Dimension

Pass as feedstock consumption, not as a new theorem in this packet.

I rebuilt the S10 derivation matrices from `geo_s10_g2_family_v0_common.py` table constructors and `D(xy)=D(x)y+xD(y)`, rather than reading only the envelope summary:

| Algebra | equations | unknowns | rank | nullity |
|---|---:|---:|---:|---:|
| H | 64 | 16 | 13 | 3 |
| M2R | 64 | 16 | 13 | 3 |
| O_compact | 512 | 64 | 50 | 14 |
| O_split | 512 | 64 | 50 | 14 |
| O_compact_one_sign_flipped | 512 | 64 | 61 | 3 |

So the `14` is computed for compact and split octonion rows, and the corrupt control returning `3` is a real discriminator. This packet correctly uses that as a branch/feedstock row and says it does not promote a compact/split theorem.

## Can-Fail Controls

Pass.

3-form preservation is not decorative:

- identity map green;
- pinned even-parity signed diagonal map green;
- single-axis sign control red;
- basis-swap control red;
- scrambled-phi control red with error `2.0` after replacing `e167` by `e137`.

Random 7-subspace control is a real gap, not marginal:

- pinned `W_A`: readout rank `6`, active axes `6`;
- deterministic random-looking labels `{YII,IYI,IIY,XXI,XIX,IXX,YYY}`: readout rank `4`, active axes `4`.

The random control therefore underperforms by `2` rank units and `2` active-axis units.

## Associator And Quotient Erasure

Pass, with exact wording.

The octonion associator is computed as `[a,b,c]=(ab)c-a(bc)` from `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json`.

Fresh recomputation found:

- ordered distinct triples checked: `210`;
- nonzero associator rows: `168`, matching the feedstock count;
- state-visible associator rows: `144`;
- sample visible row: triple `[1,2,5]` has associator vector `[0,0,0,2,0,0,0]`, max state score `2.0`, witness survivor `14`, quotient class `Q0`.

Quotient erasure also passes in the limited sense claimed: after the density quotient, each of the `9` quotient classes retains only `class_id_only`; associator triple labels and state witnesses are discarded. This is a bracketing-erasure witness under the packet's density quotient, not a new quotient theory.

## Substrate Lineage

Pass.

The packet does not float free of 3Q:

- source lock points to `gcm_constraint_carve_3q_v1_results.json`, commit `5544ad21c`;
- parent facts are `545` survivors, `9` quotient classes, `1` tripartite-entangled survivor, and `63` traceless 3Q Pauli labels;
- `gcm_substrate_check` passes on the lineage-bearing payload;
- lineage-free negative fails as required.

## Validator And Boundary

Pass, with read-only caveat.

I did not run the packet main script or pytest, because those routes write result/validator artifacts and the audit request allowed only `audit_verdict.md` as a repo write. Instead, I imported the packet validator and called `validate()` directly without invoking its writer. It returned:

```json
{"ok": true, "errors": []}
```

Before this audit file existed, `no_builder_audit_verdict_before_audit=true`. This verdict header declares independent/fresh/read-only audit status, so it satisfies the G.2a post-audit idempotency boundary.

## Final Claim Ceiling

Final accepted wording:

`gcm_g2_licensing_attach_v0` is a genuine scratch diagnostic showing that the explicit pinned convention `W_A` plus pinned `phi` passes the local G2 licensing tests on the 3Q survivor substrate, with can-fail controls and S10 Der(O) feedstock attached.

Forbidden wording:

`G2 attaches to the manifold`, `natural W_A`, `canonical G2 layer`, `G2 admitted`, or any bridge/axis/physics promotion.

## Verification Commands Used

All commands were run from `/Users/joshuaeisenhart/Codex-Ratchet`; imports were later cleaned of generated `__pycache__`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# recomputed phi samples, cross-product samples, preservation controls,
# associator visibility/erasure, random-subspace control, branch feedstock,
# and substrate positive/negative checks from the packet module
PY

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# imported validate_gcm_g2_licensing_attach_v0.py and called validate()
# without invoking main() or write_json()
PY

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# rebuilt S10 derivation matrices from geo_s10_g2_family_v0_common.py
# table constructors and derivation_matrix()
PY
```
