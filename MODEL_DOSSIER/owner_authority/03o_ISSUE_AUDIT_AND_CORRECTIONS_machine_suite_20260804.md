# Issue audit and corrections

## 1. Reachability depth was being described as basin depth

**Issue:** cumulative continuation sets \(E_1\subseteq E_2\subseteq E_3\) are not sub-basins. They only say which continuations are visible within bounded word length.

**Released correction:** the suite constructs total factor maps on 4, 32, and 512 states and exhausts their functional graphs. Each fine recurrent destination has exactly one intermediate parent and each intermediate destination has exactly one coarse parent. The released \(H\) hierarchy is therefore an actual basin → sub-basin → sub-sub-basin forest.

## 2. “Local engine” and “basin engine” were being collapsed

**Issue:** a map driven only by current-prefix features is not yet a map driven by its attractor basin. Conversely, feeding a fully enumerated basin record back into a map is not online self-recognition.

**Released correction:** the architecture is now explicitly two-stage:

1. \(G\) uses \((K_1,K_2,K_3,\sigma)\) to create a local-feature basin atlas.
2. The complete \(G\) atlas is exhausted offline, and its intrinsic basin signature, transient distance, and cycle phase are compiled into \(H\).

The released engine forest is \(H\). No claim is made that \(H\) discovers its own basin online.

## 3. Administrative basin labels could masquerade as DOFs

**Issue:** arbitrary basin numbering is not an invariant and must not control dynamics.

**Released correction:** \(H\) consumes only the basin’s operational signature, the state’s distance to recurrence, the cycle phase, and the level. Administrative IDs are used only to index the exhaustively computed table. Candidate reordering cannot change those intrinsic values.

## 4. Coordinate causality was overstated

**Issue:** proving that a whole level is causal does not prove that every coordinate acts independently at that level.

**Released correction:** both tests are reported separately. Every compiled \(H\) level changes all 10 configured hierarchy-seed traces in all 14 non-null hands. But per-coordinate \(G\) ablations preserve structural zeros:

| Coordinate | level 0 active hands | level 1 active hands | level 2 active hands |
|---|---:|---:|---:|
| \(K_1\) | 6/14 | 0/14 | 14/14 |
| \(K_2\) | 5/14 | 14/14 | 14/14 |
| \(K_3\) | 4/14 | 14/14 | 14/14 |
| \(\sigma\) | 4/14 | 14/14 | 14/14 |

The level-1 \(K_1\) zero follows from the current coefficient/shell-width arithmetic. The other zeros are retained as encoding or value collisions rather than explained away.

## 5. The base selector is encoding-sensitive

**Issue:** candidate continuations are ranked by their capacity tuple and then by numeric bit value. The second term is a tie-breaker tied to representation.

**Current boundary:** the tie-break is now documented as an authored choice. No invariance under alternative encodings is claimed. A matched recoding/substitution campaign is required before an MSS statement about the selector.

## 6. The precedence deletion is confounded with scar deletion

**Issue:** the `precedence_scar_deleted` map both removes hand-specific \(OB/BO\) selection and suppresses the scar-feedback candidate. It cannot attribute the resulting difference to one mechanism.

**Current boundary:** the result keeps the composite intervention name and does not report a pure precedence or pure scar effect. Separate interventions are deferred to the matched MSS campaign.

## 7. Machine causality could be inflated by changing driver bits only

**Issue:** comparing the hash of the whole field after a driver intervention counts the deliberately changed driver region even if tape, stored program, moving defect, resource bits, and boundary fibre remain unchanged.

**Released correction:** the machine causality receipt masks the 9-bit driver region before comparison. Under that stricter observable, compiled-level severance changes 1,077, 1,230, and 792 of the 1,344 sampled runs. Every family-level combination remains active in at least one run; none is described as universally active.

## 8. A one-word state was being read as full material self-sufficiency

**Issue:** storing all runtime coordinates in one binary word does not eliminate an external layout or interpreter.

**Released correction:** the exact claim is one 60-bit persistent word over a uniform `{0,1}` alphabet. The model specification names the external conditions: region layout, cell codebook, unique-defect decoder, rewrite grammar, boundary choice, and driver tables. This is a one-field encoding under a declared interpretation, not a self-describing homogeneous law.

## 9. Resource turnover needed recurrent, causal witnesses

**Issue:** a one-way resource episode or a recurrent driver after machine inactivity does not establish recurrent machine/resource coupling.

**Released correction:** the active-cycle predicate requires recurrent turnover, symbol-changing settlement, active machine steps, and persistent scar. The frozen result contains 40 qualifying runs and 40 unique full-field cycle hashes. Every witness crosses a boundary. Deleting settlement cost, scar-to-accumulator transfer, or accumulator-to-reservoir transfer changes all 40 machine-observable traces and leaves zero qualifying cycles.

## 10. Boundary transport could reverse base motion at a seam

**Issue:** multiplying base motion by a transported orientation label creates a seam bounce.

**Released correction:** base traversal and transported label are separate. Raw left and right scans visit all five tape positions and return after one, two, and four circuits for the three boundary laws, with no bounce.

## 11. Nominal loop length could count inactive repetitions

**Issue:** repeating an already inactive configuration is not additional active evidence.

**Released correction:** this release reports transition comparisons and explicit recurrent-cycle events. The exact paths cover 691,200 base comparisons, including 460,800 active-state comparisons, plus 344,064 driver/severance comparisons. The sampled cycle predicate separately requires active machine steps.

## 12. “Not distinguished” could be mistaken for “same”

**Issue:** a failed probe is not a positive identity witness.

**Released correction:** the object status is typed and witness-based. Full decorated conjugacy earns `ISOMORPHIC_INTERVENTION_DECORATED_DYNAMICS_UNDER_PACKET`; a changed intervention earns `SEPARATED_BY_INTERVENTION_OBSTRUCTION`; failure of every allowed primary relabeling earns `SEPARATED_BY_NO_ALLOWED_PRIMARY_CONJUGACY`; otherwise the status is `UNRESOLVED`. The proposal \(a=a\iff a\sim_\Pi b\) remains a hypothesis whose executable side requires positive receipts.

## 13. The object bridge could be mistaken for general recognition

**Issue:** authored relabelings from one grammar are easier than independently generated objects expressed through unseen representations.

**Released correction:** the fixture boundary is explicit. It exhausts 15 authored views and all 105 unordered pairs under nine allowed cyclic bit-address rotations. It recovers seven authored operational classes and separates two primary-conjugate intervention hard negatives. All views share one grammar, and no LLM is tested.

## 14. Hostile controls could become tautological

**Issue:** comparing two fabricated dictionaries does not show that the real admission path rejects a mutated executable result.

**Released correction:** the eight hostile controls include an executed campaign mutation that changes a map and breaks binding, a spoof of an actual lane result passed through the production parity gate, and an object map/receipt spoof rejected by full recomputation. Duplicate-key and non-finite inputs are also rejected.

## 15. Contained validation could be mistaken for upstream admission

**Issue:** a strong wrapper does not silently become the upstream ConstraintBox kernel.

**Released correction:** `CB_RECEIPT.json` declares `EXTERNAL_NOT_UPSTREAM_CB_KERNEL`. The contained path passes 217/217 checks and 8/8 hostile controls; the independent consumer passes 33/33 checks and the unit/contract suite passes 20/20 tests. Upstream admission remains separate.

## Remaining work

- Generate matched one-variable deformation neighborhoods rather than comparing only eight authored bundles of choices.
- Substitute encoding-invariant selectors for the numeric tie-break and measure map stability.
- Split precedence-only and scar-only controls.
- Build an online basin estimator that does not receive the exhausted \(G\) atlas.
- Replace the external 60-bit interpretation with progressively more local and self-describing rules, then test which scaffolding is necessary.
- Test object packets across independently generated grammars, wider relabeling families, divergent modalities, and actual LLM tasks.
- Run joint deletion and substitution only after these causal confounds are separated.
