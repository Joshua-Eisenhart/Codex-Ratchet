# Independent Audit Verdict - gcm_nesting_tower_le2q_v0

audit_mode: independent fresh read-only audit
auditor: Codex controller with read-only local recomputation and Codex explorer sidecars
audit_date: 2026-06-12 PDT
write_scope: this file only
git_mutation: none
freshness_tier: TIER-2, results-available with independent recomputation
binding_sources: standards codex including G.2a, nesting law spec at afe7aa57b, hardened both-registry helper, committed keystone inputs
classification_ceiling: scratch_diagnostic, carrier-and-pins-relative
route_truth: Wizard v4.2 PARTIAL, compact packet plus relevant mini-MMMs; three bounded Codex explorer sidecars were spawned and returned usable read-only receipts

## Bottom Line

PASS, with one important sharpening and one important correction.

The builder's numeric tower claims verify on the live frozen carrier: exact tower `256` families and triples, probe tower `464` compatible 2Q rows and `1856` family triples, exact orphans `288`, probe orphans `80`, and probe-rescued exact orphans `208`. The fiber distributions, round trips, product baseline, scrambled-pairing control, strict validator, both registry lineages, and G.2a boundary all check out.

The sharpened root-axiom finding is:

> On this carrier-and-pins-relative <=2Q object, the nesting law is probe-relative or product-coordinate-trivial. Exact registry-coordinate compatibility admits only the product-grid sub-tower. Probe compatibility under the committed x/z quotient admits the entangled purification-boundary rows. The root axiom's probe quotient, not tolerance and not exact equality, is what admits entanglement into this tower.

The correction is that the stronger slogan "the 1Q survivor set contains only pure states" is not an unqualified registry fact for this packet. Raw frozen 1Q carrier coordinates have radii below `1`; a geometry-attached normalization can attach pure representative directions, but the packet's exact relation is literal registry-coordinate matching, not density equality against that normalized interpretation. Therefore the earned theorem here is object-relative: exact compatibility excludes the entangled 16 on this frozen carrier and relation because their required B marginal coordinates do not literally exist in the 1Q exact registry.

## Authority And Inputs

Primary audit standard: `system_v6/receipts/audit_standards_codex_v1.md`, especially G.2a's builder-audit separation and idempotency rule.

Binding law: `system_v6/receipts/nesting_law_final_object_spec_20260612.md` at commit `afe7aa57b`. The law requires compatibility by partial trace against the lower-rung equivalence relation, and it explicitly makes exact-vs-probe interpretation rung-dependent.

Live packet: `system_v6/sims/gcm_nesting_tower_le2q_v0/`.

Lineage carriers:

- 1Q object: `gcmobj_a40e54e13cec01466c9d675028b3574b`
- 2Q object: `gcm2qobj_715e9424ea66468243108751fb59395f`
- 1Q registry body hash: `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
- 2Q registry body hash: `57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac`

## Exact Equals Product Identity

Verdict: structural for this object and exact relation, not a lucky count coincidence.

The packet's exact relation is full integer `coord_scaled` lookup in the frozen 1Q registry. Under that relation:

- exact-compatible rows: `256`
- exact-compatible families: `product_grid` only
- product exact sub-tower: `16 * 16 = 256`
- entangled exact-compatible rows: `0`
- entangled A exact hits: `16`
- entangled B exact hits: `0`

The falsifier was checked directly: no non-product or entangled 2Q row has both A and B marginals resolving by exact 1Q coordinate equality. Every exact row is in the product sub-tower, and the exact product sub-tower accounts for all exact rows.

Precise statement:

> For the frozen <=2Q carrier, pinned 1Q/2Q registries, and the packet's exact relation defined as literal integer-coordinate equality, exact compatibility is exactly the product-grid sub-tower. Entangled purification-boundary survivors are structurally excluded by the exact B-side lookup.

This is not promoted to a general theorem about all future rungs, all carriers, or density equality.

## Pure-Only Mechanism Check

The user's proposed mechanism is mathematically right as a conditional but too strong as a claim about this packet's raw registry.

Conditional theorem:

> If the lower rung were pure-only under density equality, then a pure entangled 2Q member with mixed one-body marginals could not be exact-compatible with that lower rung.

That conditional is the right intuition. The entangled 16 are pure 2Q purification-boundary rows with mixed A/B marginals. Their marginal radii are below `1`, split as:

- radius `sqrt(2)/2 ~= 0.707106781187`, `8` rows
- radius `sqrt(3)/2 ~= 0.866025403784`, `8` rows

However, the packet's exact compatibility check does not compare density matrices to a pure-only 1Q density surface. It compares frozen integer registry coordinates. Raw 1Q carrier coordinates are not unambiguously pure-only; a separate geometry-attached normalization may attach pure representative directions, but that is not the equality relation implemented here.

Therefore the audit does not license "exact nesting cannot host entanglement whenever the lower rung is pure-only" as the packet's finding. It licenses the narrower and stronger-in-place finding: exact registry-coordinate compatibility cannot host the entangled 16 on this frozen object because their exact B marginal coordinates are absent from the lower rung.

## Probe Rescue Mechanism

Verdict: the rescue is the computed action of the committed probe quotient, not a tolerance artifact.

The committed 1Q probe relation uses the x/z probe signature:

```text
probe_signature(coord_scaled) = (sign(coord_scaled[0]), sign(coord_scaled[2]))
```

Exact matching uses integer coordinate equality. Probe matching uses membership in the same x/z signature class. There is no local floating tolerance in this rescue step.

For all `16` entangled purification-boundary survivors:

- exact A resolves
- exact B does not resolve
- probe A resolves
- probe B resolves
- each row yields `2` A probe representatives times `2` B probe representatives, hence `4` triples per row
- total entangled probe triples: `16 * 4 = 64`

The B-side probe class is constant across the entangled 16:

- B exact coordinates: `[0, 0, 1]` for `8` rows and `[0, 0, 2]` for `8` rows
- B probe signature: `[0, 1]`
- B probe class: `qcls_e3604e13ed713c04fcf6`
- raw class label: `Q4`
- 1Q representatives: `surv_cbb428726dfac0f03903` with coord `[0, -1, 1]`, and `surv_57e755b7fbea4c5b17cd` with coord `[0, 1, 1]`

Interpretation:

> The x/z probe quotient cannot distinguish the mixed/y-erased B marginal code `[0,0,1]` or `[0,0,2]` from the lower-rung representatives with the same x/z sign pattern. That quotient action is what rescues the entangled boundary rows into the probe tower.

This is quotient-relative compatibility. It is not exact equality, and it is not promotion of the probe relation over the exact relation.

## Counts, Fibers, And Round Trips

Fresh recomputation matched the builder claims:

```text
1Q survivors: 16
2Q survivors: 544
exact compatible rows: 256
exact family triples: 256
probe compatible rows: 464
probe family triples: 1856
exact orphans: 288
probe orphans: 80
probe-rescued exact orphans: 208
entangled probe-compatible rows: 16
entangled probe triples: 64
```

Fiber distributions matched:

```text
exact-A fibers: {34: 16}
exact-B fibers: {16: 16}
probe-A fibers: {68: 16}
probe-B fibers: {48: 8, 64: 6, 80: 2}
```

Relation partition matched:

```text
exact_and_probe: 256
probe_only: 208
incompatible: 80
```

Bidirectional round trips passed for exact/probe down-triples and exact/probe up-fibers.

## Remaining Probe Orphans

The `80` remaining probe orphans are all product-grid rows. None are purification-boundary entangled rows.

They are exactly the B-side x/z-null probe boundary:

```text
family: product_grid, count 80
B coords [0, -2, 0]: 16
B coords [0, -1, 0]: 16
B coords [0,  0, 0]: 16
B coords [0,  1, 0]: 16
B coords [0,  2, 0]: 16
```

Mechanism:

> These rows have B probe signature `(0,0)`, and the frozen 1Q probe quotient has no compatible `(0,0)` lower-rung class. They remain outside even after quotient rescue and mark the real <=2Q probe tower boundary for this object.

## Controls And Lineage

Controls verified:

- product exact sub-tower: `256`, equal to `16 * 16`
- product probe rows/triples: `448 / 1792`
- pinned product embedding: `16`, all survive
- scrambled pairing control: `544 / 544` exact breaks and `544 / 544` probe breaks, with all probe compatibility destroyed
- strict validator payload check: zero errors
- tests: `4 passed`

Lineage verified:

- live packet passes the hardened 1Q substrate helper
- live packet passes the hardened 2Q substrate helper
- lineage-free negative controls exit red for both 1Q and 2Q
- both registry lineages are consumed by the packet

Engine/tool envelope:

- Julia, JAX, and PyTorch lanes report `all_pass=true`
- engine count agreement is true
- max divergence is `0`
- z3/cvc5 arithmetic checks bind count/partition identities only

These engine/tool facts support the scratch diagnostic. They do not promote the packet to a formal admission result or a future-rung result.

## G.2a Boundary

G.2a passes.

The builder did not write this `audit_verdict.md`; this file is a fresh independent audit written after the builder packet and result surfaces existed. The packet-local boundary uses `scripts/builder_audit_boundary.py`, which accepts an existing audit file only when its header declares an independent, fresh, or read-only audit. This header is intentionally idempotent under that rule.

No git staging, commit, push, or broad repo cleanup was performed.

## Claim Ceiling And Licensed Citation

Licensed citation shape:

> On this carrier-and-pins-relative <=2Q object, the nesting law is probe-relative or product-coordinate-trivial: exact compatibility admits only the product-grid sub-tower, while the committed x/z probe quotient admits the entangled purification-boundary rows into the tower.

More pointed form:

> The root axiom's quotient is what admits entanglement into the first tower; exact registry-coordinate compatibility does not.

Required caveats:

- scratch diagnostic only
- carrier-and-pins-relative only
- exact and probe equivalences remain separate
- neither equivalence is crowned
- no future-rung, bridge, axis, or full-system claim is licensed here
- no claim is made that engine parity proves physics or admission
- no claim is made that the raw lower-rung registry is simply pure-only

## Fresh Checks Run

Controller-local fresh checks included:

```text
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  -m pytest -q -p no:cacheprovider \
  system_v6/sims/gcm_nesting_tower_le2q_v0/tests

Result: 4 passed in 0.52s
```

Additional read-only checks:

- `validate_payload(...)` on the live envelope returned zero validator errors
- `build_packet(write=False)` matched the saved result after removing volatile timestamp/hash fields
- local recomputation matched counts, fibers, relation partitions, product baseline, entangled rescue, and scrambled-pairing control
- two independent Codex explorer receipts cross-checked structural exact/product identity, quotient rescue, counts, controls, lineage, and G.2a

## Block K Closeout

Gates cited: G.2a builder/audit boundary, nesting law spec at `afe7aa57b`, frozen 1Q/2Q registry lineage, packet validator, cross-engine envelope, product and scrambled controls.

Admission decisions: accepted as a scratch, carrier-and-pins-relative first-tower diagnostic; no broader admission accepted.

Narrative substitutions intercepted:

- exact-count equality as mere coincidence: rejected
- pure-only lower-rung as unqualified registry fact: rejected
- probe quotient as exact equality: rejected
- engine parity as admission: rejected
- quotient rescue as tolerance artifact: rejected

Worker claims verified locally: counts, fibers, round trips, exact/product identity, entangled probe rescue, product baseline, scrambled control, helper lineage, and G.2a boundary.

Status label changes to registry: none.

Blocked or deferred claims: future-rung tower claims, 3Q extension, bridge/axis claims, full-system claims, and any formal promotion beyond this scratch diagnostic.
