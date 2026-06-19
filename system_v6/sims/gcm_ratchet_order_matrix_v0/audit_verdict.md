# Independent Audit Verdict - gcm_ratchet_order_matrix_v0

audit_mode: read-only audit
auditor: independent recomputation
freshness_tier: TIER-2
write_scope: this file only
standards_codex: system_v6/receipts/audit_standards_codex_v1.md

## Bottom Line

VERDICT: GENUINE-WITH-CAVEATS.

The 5-step matrix itself recomputes: on the frozen GCM object, the packet has 3 unique forced precedence edges, exact order-free commutation for the shell/quotient pair, and an acyclic partial order by both `networkx` and `rustworkx`. The builder's stronger `strict green`/full-C6-control claim does not survive audit because several C6 controls are declared or blocked rather than actually recomputed.

Claim ceiling: `scratch_diagnostic`, carrier-and-pins-relative, 5-step-subset-only. It is not a full Part C alphabet run, not a global ratchet sequence theorem, not a formal proof, and not manifold/physics admission.

Citation rule: cite this only as "a 5-step frozen-GCM order-matrix scratch diagnostic that recomputed three forced edges (`SHELL_PI_OVER_4 -> BRICKWORK_AB`, `SHELL_PI_OVER_4 -> FLUX_HOLONOMY_LOCK`, `PHASE_DENSITY_QUOTIENT -> CHANNEL_DZ_RX`) and exact shell/quotient commutation, with C6-control and Part-C-scope caveats." Future citations must co-cite this audit file and `results/gcm_ratchet_order_matrix_v0_results.json`; they must not cite it as strict-green, full-alphabet Part C, or canonical order.

## Recomputed Matrix

Source implementation audited by hash:

- `gcm_ratchet_order_matrix_v0_common.py`: `8bddfeb5f543de81f7b5160dc7f376398b47b566be87c9f8beb9d65ef7c20ab7`
- `gcm_ratchet_order_matrix_v0.py`: `ade84dcb0daed56f3a791725d5e044ec36136cdf756514f46fc964ddd6a0f0ae`
- `validate_gcm_ratchet_order_matrix_v0.py`: `800bee2c4da05794454f98b3bab8582fc00faf7807fc0070876fe81735af7d42`

Fresh in-memory recomputation covered all 20 off-diagonal ordered pairs of the 5-step alphabet. The packet also emits 25 rows including self-pairs. Counts recomputed from the frozen context: `16` survivors, `4` selected `pi/4` survivors, `8` quotient classes, `6` candidate regions.

Status distribution over the 20 off-diagonal rows:

- `COMMUTES_ORDER_FREE`: 2 ordered rows, the same shell/quotient unordered pair in both orientations.
- `DIRECTIONAL_ENABLE`: 6 ordered rows, deduping to 3 unique forced edges.
- `NOT_COMPARABLE`: 12 ordered rows, all reported as typed missing-object failures rather than silently skipped.
- `NONCOMMUTES_NUMERIC`: 0 rows.
- `NONCOMMUTES_MORTALITY`: 0 rows.

The three unique forced edges recompute with the claimed direction:

- `SHELL_PI_OVER_4 -> BRICKWORK_AB`: reverse dies with `missing_layer_failure`, missing `occupied_T_eta_stratum`.
- `SHELL_PI_OVER_4 -> FLUX_HOLONOMY_LOCK`: reverse dies with `missing_layer_failure`, missing `occupied_T_eta_stratum`.
- `PHASE_DENSITY_QUOTIENT -> CHANNEL_DZ_RX`: reverse dies with `missing_layer_failure`, missing `phase_density_quotient`.

The shell/quotient pair genuinely commutes in this implementation. The check is exact signature/set equality, not a floating tolerance: survivor symmetric difference `0`, witness symmetric difference `0`, numeric gap `"0"`, and identical canonical state signatures.

The missing-layer brickwork failure is real in the implementation: `run_order(["BRICKWORK_AB"])` returns dead with `mortality_class="missing_layer_failure"`, `missing_object="occupied_T_eta_stratum"`, and the stated reason that the pinned A/B local update is typed only after an occupied shell stratum exists.

The measured partial order is acyclic by both backends. One recomputed valid topological order is:

`PHASE_DENSITY_QUOTIENT -> CHANNEL_DZ_RX -> SHELL_PI_OVER_4 -> BRICKWORK_AB -> FLUX_HOLONOMY_LOCK`

## Typing And Hypotheses

Each step has a declared domain, codomain, and required prior object. Illegal compositions are represented as mortality/typed-failure rows: either a single directional missing object or `both_orders_missing_required_objects`. They are not silently skipped.

The 4 hypothesis comparisons trace to computed rows:

- Supported, carrier-relative: quotient before channels, traced to `PHASE_DENSITY_QUOTIENT__CHANNEL_DZ_RX`.
- Supported, carrier-relative: shell before flux lock, traced to `SHELL_PI_OVER_4__FLUX_HOLONOMY_LOCK`.
- Not supported honest null: strict shell/quotient order, traced to `SHELL_PI_OVER_4__PHASE_DENSITY_QUOTIENT`.
- Contradicted: brickwork without shell, traced to `SHELL_PI_OVER_4__BRICKWORK_AB`.

The supported verdicts must remain carrier-relative to the frozen 1Q GCM substrate and the exact source pins. The result does not license the same order for other quotients, depths, channel families, terrain rows, or unfrozen carriers.

## Caveats

G1 - C6 controls are not all computed. The following controls did fire with concrete checks: substrate positive, lineage-free negative, wrong-substrate negative, reversed order, quotient erasure, missing-layer failure, and shell/quotient zero commute. But `label_shuffle` is tautological (`signature == signature`), `local_only_replacement` records a hash-mismatch refusal without executing a replacement, `mortality_replay` is a cited anchor not a replayed computation, `depth_ablation` is blocked as out of scope, and `entropy_readout_ablation` is asserted without an ablated recomputation. This blocks "strict green" and "C6 complete computed" language.

G2 - The alphabet is an honest 5-step subset, not Part C's full alphabet. Part C's first matrix alphabet includes more surfaces, including terrain conditioning, operator residency/precedence, and depth ladder climb. This packet's `CHANNEL_DZ_RX` is a user-requested/hypothesis-receipt channel fixture, but its `part_c_alias` is `D`, while Part C uses `D` for depth ladder climb. Future extension should split channel/flow/stage-flux rows from the depth symbol and add the missing Part C surfaces.

G3 - The three-coordinate declaration is top-level and nonstandard, not row-local Part C compliance. The packet declares `order/nesting axis (cross-layer) | carve-measured | 1Q`, but Part C asks for row-level `geometric layer`, `nesting` state from `free/restricted/quotiented/ratcheted/integrated`, and `qubit depth`. Cite the current result as top-level scoped, not full row-local coordinate compliance.

G4 - `BRICKWORK_AB` is source-pinned but caveated. The builder could not find a literal committed "brickwork" label and pinned the step to the committed A/B local-update feedstock in `manifold_super_sim_v2_weld` by hash. That is usable for this subset audit only if future citations keep the feedstock caveat attached.

## Substrate, G.2a, And Checks

Runtime doctor was green: `ok=True`, canonical Python `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`, no repo-local env pollution, no missing expected modules, and no active installers observed.

Substrate helper reruns:

- Positive payload: `ok=true`, object `gcmobj_a40e54e13cec01466c9d675028b3574b`, registry body `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`.
- Lineage-free negative: red as required, with object/body/lineage-consumption errors.
- Wrong-substrate negative: red as required, with `gcm_object_id` mismatch.

G.2a builder/audit boundary rerun in memory:

- `validate_payload_errors`: `[]`
- `boundary_errors`: `[]`
- This audit file header declares independent read-only audit status, so post-audit idempotency should remain valid under `scripts/builder_audit_boundary.py`.

Not run by design: the packet writer, packet validator CLI, and pytest path, because they rewrite result files and the audit instruction allowed writing only this verdict file.

## Follow-Up Extension

The next admissible extension is a full Part C order-matrix packet over the larger alphabet: shell/leaf conditioning, quotient/lens equivalence, local window/support restriction, flux locking, terrain conditioning, operator residency/precedence, and depth ladder climb. It should make C6 controls executable at birth, use row-local coordinates, and avoid reusing `D` for channels when Part C reserves it for depth.
