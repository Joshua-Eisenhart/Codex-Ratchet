# Independent audit verdict - manifold_ab_weld_relation_v0

Bottom line: **GENUINE-WITH-CAVEATS**. The packet is real scratch-diagnostic A/B weld-relation evidence for the finite relation surface, especially `A_terminal_class_count=3`, `B_composite_order=8`, and `W=11`. It is not a full closure of the weld program's named gap because parts of the coordinate map are still declared/mixed rather than computed numerical relations, the weld-only control table overstates value movement by using whole-row signatures, and the Family A parent commit label does not match the consumed bytes.

Freshness tier: `TIER-2` results-available fresh audit. I read the build card, standards, feedstock, source, and results; no prior target audit existed. Audit mode was read-only except this file.

Standards: `system_v6/receipts/audit_standards_codex_v1.md`, including `G.2a`; feedstock authority: `system_v6/receipts/weld_feedstock_inventory_20260611.md` GAPS rows 1-3; ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Verdict details

### 1. Coordinate-map computedness

The result has 8 coordinate-map rows and all are rebuilt byte-identical from `manifold_ab_weld_relation_v0_common.py`, but the row-level computedness is not uniform:

| row | verdict | audit note |
|---|---|---|
| `state_object_identity` | COMPUTED | Compares the two hash-loaded state ids and computes `not_equal=true`. |
| `chart_carrier` | DECLARED/MIXED | Reads A/B labels, but `computed_relation_value` is a constant `true`; no numerical relation or predicate over the labels is checked. |
| `finite_carrier_size` | COMPUTED | Computes `divmod(384,33) = quotient 11, remainder 21`. |
| `partition_order` | COMPUTED | Computes `3 + 8 = 11`; this is the load-bearing SMT row. |
| `zero_record_conservation` | COMPUTED | Checks A zero and B zero with numeric tolerances. |
| `entropy_type_surface` | COMPUTED/MIXED | Checks parent typed-ledger flags from both state objects, but `product_convention_declared=false` is packet policy, not computed from a parent object. |
| `trajectory_lineage_standard` | DECLARED | The row asserts a shared standard with constant `true`; it does not inspect parent trajectory artifacts as a numerical relation. |
| `backend_scope` | DECLARED/MIXED | Reads B mode, but A mode is hardcoded as `manifold_super_sim_v0`; this is a boundary statement, not a computed backend relation. |

So the coordinate-map part of feedstock GAP row 1 is only partially closed. The finite/counting rows are computed; the chart/lineage/backend horizon rows must be cited as declared or mixed.

### 2. Weld-only rows and nonrecoverability

I recomputed the relation object and the committed rows matched exactly. Three explicit reconstruction checks:

| row | baseline | A erased | B erased | audit |
|---|---:|---|---|---|
| `WO2_partition_sum_relation` | `11` | `not_recoverable` | `not_recoverable` | Pass for erased-input reconstruction. |
| `WO3_partition_product_relation` | `24` | `not_recoverable` | `not_recoverable` | Pass for erased-input reconstruction. |
| `WO6_relation_polynomial_residual` | `0` | `not_recoverable` | `not_recoverable` | Pass for erased-input reconstruction. |

All 6 nonrecoverability rows use the same operation: call `compute_weld_row_value` with A missing, B missing, or both missing and require `recoverable=false`. That is a real reconstruction-attempt failure, not a dimension or information-theoretic nonrecoverability proof. Cite it at that strength only.

### 3. Scoped controls

A-only and B-only controls are honest at value level:

- A-only perturbation moves A internal rows and weld values, and does not move B-internal rows.
- B-only perturbation moves B internal rows and weld values, and does not move A-internal rows.

The weld-only perturbation keeps A and B internal anchors fixed, but the published movement table is too broad if read as value movement. It reports all six weld rows moved because row signatures include `relation_offset`; value recomputation shows only `WO2_partition_sum_relation` and `WO6_relation_polynomial_residual` actually change value. This is a caveat, not a kill, because scoped isolation is real; the citation must say signature movement for all six, value movement for two.

### 4. SMT load-bearingness

The z3 and cvc5 rows bind the measured packet values:

- A value: `3`, from `G1_terminal_class_count`.
- B value: `8`, from `deep_chain_composite_order`.
- weld relation value: `11`, from `WO2_partition_sum_relation`.

The valid row is `UNSAT` under the mismatch assertion. The erased/perturbed flips are `SAT`, so they fail with the intended polarity. This is not decorative-SMT disconnected from the run, but it is narrow: it is load-bearing for the finite sum relation only, not for the whole coordinate map or every weld-only row.

### 5. Parent hashes

Current source pins match the packet's expected hashes for A, B, v2 weld, feedstock, and C fence. Commit existence also checks out for `42542f120`, `29e133f2f`, and `d6815079e`.

There is one lineage caveat: the current Family A envelope hash is `e993259c...`, and that is what this packet consumes. The file at commit `42542f120` hashes to `88e084b9...`; the consumed current bytes match later hardening commit `2ad726598`. B at `29e133f2f` and v2 weld at `d6815079e` match byte-for-byte. Cite Family A by current hash/current hardening lineage, not as exact `42542f120` bytes.

### 6. Fences

Fences pass:

- classification is `scratch_diagnostic`;
- no promotion/formal admission;
- weld-relation evidence only;
- no manifold, axis, bridge, or physics admission;
- charts-on-surface horizon remains open;
- Family C is `fence_check_citation_only` and not an A/B relation input.

`G.2a` passes: packet validator and tests delegate the audit boundary to `scripts/builder_audit_boundary.py`, so this audit file is allowed after a legitimate independent audit header.

Circularity species: `[]`.

## Program status

Feedstock GAP row 1, A+B weld relation itself: **partially closed**. Separate hash-loaded A/B state objects and finite weld-only rows are real; the coordinate map is not fully computed row-by-row.

Feedstock GAP row 2, cross-family controls: **partially closed**. A-only and B-only controls pass; weld-only control is honest for isolation but overbroad if cited as all-six value movement.

Feedstock GAP row 3, weld-relation SMT: **closed only for the finite sum relation** `3 + 8 = 11`. It does not SMT-bind the whole coordinate map or all weld-only rows.

Still open: global/backend-independent full-object A+B implementation; source-faithful flux/chirality-asymmetric L/R two-engine joint object; Family C integrated super-sim; charts-on-surface closure; any promotion above scratch.

## Citation rule

Allowed citation: `manifold_ab_weld_relation_v0` is a GENUINE-WITH-CAVEATS scratch-diagnostic A/B weld-relation packet that hash-loads current A/B state objects, computes finite A/B relation rows including `3+8=11`, checks erased-input nonrecoverability, and uses z3+cvc5 as load-bearing finite-sum relation checks with SAT flips.

Required suffix: coordinate-map rows `chart_carrier`, `trajectory_lineage_standard`, and `backend_scope` are declared/mixed; weld-only perturbation moves all six row signatures but only two computed values; Family A exact consumed bytes are the current `e993259c...` hardening lineage, not the exact `42542f120` file bytes.

Forbidden citation: do not cite this as canonical manifold evidence, formal admission, axis/bridge/physics evidence, global full-object backend independence, source-faithful flux/chirality L/R evidence, Family C integration, charts-on-surface closure, or promotion beyond `scratch_diagnostic`.

## Fresh checks run

- Rebuilt relation object in-process: coordinate map, weld rows, nonrecoverability table, controls, SMT rows, parent checks, and C fence all matched committed result rows.
- Packet validator in-process: `error_count=0`.
- Strict three-engine validator: `ok=true` with `--require-pytorch --strict-source-backed --require-tool-intent`.
- Unit tests: 5 tests passed.
- Parent byte checks: B and v2 weld match named commits; A matches current pinned hash but not the bytes at `42542f120`.
