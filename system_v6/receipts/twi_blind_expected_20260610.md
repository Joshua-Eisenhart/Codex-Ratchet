# BLIND Expected Values: twistor_incidence_finite_packet_v0

Blind rule honored: this sheet does not use or inspect `system_v6/sims/twistor_incidence_finite_packet_v0/`. Inputs used: `/tmp/twi_build_card_20260610.md`, `system_v6/receipts/twistor_incidence_mine_20260610.md`, standard finite-projective-geometry derivations, and committed PG(3,2)/MCT evidence outside the blind packet.

## Source Pins

- Build-card claim/fence: `/tmp/twi_build_card_20260610.md:3-5`.
- Build-card PIN block: `/tmp/twi_build_card_20260610.md:13-18`.
- Build gates G1-G7 and controls: `/tmp/twi_build_card_20260610.md:20-30`.
- Mine receipt finite translation: `system_v6/receipts/twistor_incidence_mine_20260610.md:126-130`.
- Mine receipt PG(3,2) route and precedent: `system_v6/receipts/twistor_incidence_mine_20260610.md:136-149`.
- Mine receipt packet shape/baseline/fence: `system_v6/receipts/twistor_incidence_mine_20260610.md:171-188`.
- Committed MCT baseline pins: `system_v6/sims/mct_dynamic_admissibility_packet_v0/audit_verdict.md:47-56`, `:85-91`, `:107`.

## 1. PG(3,2) Counts

Value:

- Points: `15`.
- Lines: `35`.
- Planes: `15`.
- Points per line: `3`.
- Lines through each point: `7`.
- Lines per plane: `7`.

Derivation:

- Points in `PG(3,q)` are 1D subspaces of `F_q^4`, so `[# points] = [4 choose 1]_q = (q^4 - 1)/(q - 1)`. For `q=2`: `(2^4 - 1)/(2 - 1) = 15/1 = 15`.
- Lines are 2D subspaces, so `[# lines] = [4 choose 2]_q = ((q^4 - 1)(q^3 - 1))/((q^2 - 1)(q - 1))`. For `q=2`: `((16 - 1)(8 - 1))/((4 - 1)(2 - 1)) = (15*7)/(3*1) = 35`.
- Planes are 3D subspaces, dual to points: `[# planes] = [4 choose 3]_q = [4 choose 1]_q = 15`.
- A projective line has `[2 choose 1]_q = (q^2 - 1)/(q - 1)` points. For `q=2`: `(4 - 1)/(2 - 1) = 3`.
- Lines through a fixed point correspond to 1D subspaces in the quotient `F_2^4 / P`, a 3D vector space: `[3 choose 1]_2 = (2^3 - 1)/(2 - 1) = 7`.
- Lines in a fixed plane `PG(2,2)` are `[3 choose 2]_2 = [3 choose 1]_2 = 7`.

Source/PIN line:

- Build card pins `15 points`, `35 lines`, and `7 lines through each point`: `/tmp/twi_build_card_20260610.md:14`.
- Mine receipt independently records the same `PG(3,2)` size and finite geometry source: `system_v6/receipts/twistor_incidence_mine_20260610.md:136-138`.
- Committed PG(3,2) precedent reports `line count: 35`, `total planes: 15`: `system_v6/receipts/twistor_incidence_mine_20260610.md:148`.

## 2. Intersection Graph of the 35 Lines

Value:

- Vertices: `35` projective lines.
- Regular degree: `18`.
- Edges: `315`.
- Connectivity: connected, diameter at most `2`; in fact any two skew lines share common transversals.

Derivation:

- Vertices are lines, so vertex count is the line count: `35`.
- Fix a line `L`. It has `3` points.
- Through each point of `L`, there are `7` lines total, of which one is `L`; so there are `6` other lines through that point.
- Distinct points on `L` cannot contribute the same other line, because a line through two points of `L` would equal `L`.
- Lines meeting `L`: `3 * 6 = 18`. Thus the line-intersection graph is `18`-regular.
- Edge count by handshaking: `35 * 18 / 2 = 315`.
- Lines not adjacent to a fixed line: `35 - 1 - 18 = 16`, the skew lines.
- Connectivity: adjacent lines are distance `1`; for a skew line `M`, choose any point `p` on `L` and any point `m` on `M`. The unique projective line through `p` and `m` meets both `L` and `M`, so distance is at most `2`.

Source/PIN line:

- The line-intersection graph is pinned as the null-relation candidate with `35` vertices and adjacency iff lines meet in a point: `/tmp/twi_build_card_20260610.md:15`.
- G2 requires graph invariants and a scramble-incidence control: `/tmp/twi_build_card_20260610.md:22`.
- Mine receipt gives the same finite line-intersection translation: `system_v6/receipts/twistor_incidence_mine_20260610.md:164-166`.

## 3. Pencil Structure

Value:

- Pencil through each point: `7` lines.
- Per-plane line count: `7` lines.
- Per-plane point count: `7` points.
- Lines through a point inside a fixed plane containing that point: `3` lines.

Derivation:

- Full-space pencil through point `p`: `[3 choose 1]_2 = 7`.
- A plane in `PG(3,2)` is a `PG(2,2)` Fano plane. It has `[3 choose 1]_2 = 7` points and `[3 choose 2]_2 = 7` lines.
- Inside that plane, lines through a fixed point are `[2 choose 1]_2 = 3`.

Source/PIN line:

- Alpha-star row is the `7`-line pencil through a point: `/tmp/twi_build_card_20260610.md:15`.
- `P_pencil` is a required probe family: `/tmp/twi_build_card_20260610.md:16`.
- Mine receipt maps alpha-plane/star to the finite family of lines through a projective point: `system_v6/receipts/twistor_incidence_mine_20260610.md:166-167`.

## 4. Reconstruction From Incidence

Value:

- Expected full-line-membership recovery: exact recovery of all `15` points.
- Expected mismatch count on true incidence: `0`.
- Random bipartite control: should fail exact reconstruction or produce non-isomorphic invariants before any high-level readout can honestly separate.
- First diverging invariant expected in random control: pair axiom / co-pencil intersection structure. In true `PG(3,2)`, any two distinct points share exactly one line; in a random 15-by-35 bipartite table with row degree `7` and column degree `3`, duplicate or missing co-line counts should appear first.

Derivation:

- Each point is represented by its line-membership row: a `7`-element subset of the `35` lines.
- Distinct projective points cannot have identical line-membership rows. If two distinct points `p,q` had the same incident lines, every line through `p` would pass through `q`; but in projective geometry there is exactly one line through `p` and `q`, while `p` has `7` incident lines.
- Therefore the set of `15` distinct 7-line rows reconstructs the points exactly from full line-membership data.
- The incidence table also reconstructs the unique-line-through-two-points relation: intersections of point rows have size `1` for any distinct pair and size `7` for identical rows.
- A random degree-matched bipartite control can preserve row/column degrees (`7` and `3`) while breaking the pair axiom. Its earliest honest failure should be a row-pair intersection histogram not equal to `{same: 7, distinct: 1}`.

Source/PIN line:

- G3 requires recovering all `15` points from line-membership data and expects random-bipartite failure or non-isomorphic invariants: `/tmp/twi_build_card_20260610.md:23`.
- `P_recon` is a pinned probe family: `/tmp/twi_build_card_20260610.md:16`.
- Mine receipt lists reconstruction-from-incidence as new for this packet: `system_v6/receipts/twistor_incidence_mine_20260610.md:169`.

## 5. q=2 Projective-Quotient Caveat and q=3 Discriminator

Value:

- For `q=2`, `F_2^* = {1}`. The projective scalar quotient is structurally present but extensionally identity on nonzero vectors.
- Honest G4 prediction for q=2: dropping the scalar quotient may be a no-op for point counts, line sets, incidence rows, line-intersection graph, and reconstruction. If it changes nothing, that is a valid q=2 limitation, not a failure to force.
- Discriminating q=3 counts:
  - Points: `(3^4 - 1)/(3 - 1) = 80/2 = 40`.
  - Lines: `((3^4 - 1)(3^3 - 1))/((3^2 - 1)(3 - 1)) = (80*26)/(8*2) = 2080/16 = 130`.
  - Planes: `[4 choose 3]_3 = [4 choose 1]_3 = 40`.
  - Points per line: `(3^2 - 1)/(3 - 1) = 8/2 = 4`.
  - Lines through each point: `[3 choose 1]_3 = (3^3 - 1)/(3 - 1) = 26/2 = 13`.
  - Lines per plane: `[3 choose 2]_3 = [3 choose 1]_3 = 13`.

Derivation:

- Projective points are nonzero vector orbits under multiplication by `F_q^*`.
- For `q=2`, the only nonzero scalar is `1`, so each orbit has size `1`; quotient and raw nonzero-vector carrier coincide as sets.
- For `q=3`, each projective point is an orbit of size `2`, so raw nonzero vectors number `80` but quotient points number `40`; dropping quotient should double point representatives and can change quotient-sensitive readouts.

Source/PIN line:

- Build card explicitly says q=2 quotient is trivial but must still be computed, and G4 must report no-op honestly while flagging q=3: `/tmp/twi_build_card_20260610.md:14`, `:24`.
- Mine receipt defines projective quotient `Z ~ lambda Z` and nonzero scalar quotient: `system_v6/receipts/twistor_incidence_mine_20260610.md:120`, `:130`, `:177`.

## 6. SMT Predictions

Value:

- Two distinct lines in `PG(3,2)` meet in at most `1` point: true; solver check should be `UNSAT` for existence of distinct lines with at least `2` common points.
- Pencil regularity: every point is incident to exactly `7` lines; solver check should prove or validate the 7-regular point-line incidence row.
- Scrambled-incidence control:
  - If scramble preserves only coarse degrees, it may keep the `7`-regular row but should break the pair axiom / line-line intersection bound.
  - If scramble does not preserve point degrees, it should break both pencil regularity and pair/intersection facts.

Derivation:

- In a projective space, two distinct lines span at least a plane if they meet, and if they shared two distinct points then both lines would equal the unique line through those two points. Therefore distinct lines have intersection size `0` or `1`.
- In `PG(3,2)`, each point is incident to `[3 choose 1]_2 = 7` lines, as derived above.
- SMT should consume computed incidence rows: for all line pairs `L_i != L_j`, assert `|L_i intersect L_j| >= 2`; this should be unsatisfiable under true incidence. For the pencil fact, assert existence of a point with incident-line count not equal to `7`; this should be unsatisfiable under true incidence.

Source/PIN line:

- G6 asks z3 and cvc5 to derive incidence-structure facts such as no two distinct lines meeting in `>=2` points and 7-pencil regularity, with scrambled control flipping: `/tmp/twi_build_card_20260610.md:26`.
- Mine receipt precedent notes prior pair axiom checks and SMT tool precedent: `system_v6/receipts/twistor_incidence_mine_20260610.md:145`, `:149`.

## 7. Baseline Separation Expectations vs Committed MCT

Committed baseline values:

- MCT support size: `384`.
- Exact density quotient: `12`.
- Active quotient without phase: `24 = 12 density classes * 2 sheet rows`.
- Active quotient with phase: `192 = 12 density classes * 2 sheet rows * 8 phase bins`.
- Relation components: full relation `1`; ablated/product/local/null controls `384`.
- Current hardening also reports full row-location tables with `384` rows and presentation agreement on quotient class count.

Source/PIN line:

- Baseline comparison is required by the build card: `/tmp/twi_build_card_20260610.md:17`, `:25`.
- Mine receipt says the MCT baseline has `support_size=384`, emitted probe rows, relation-dependent readout, and scratch ceiling: `system_v6/receipts/twistor_incidence_mine_20260610.md:185`.
- Committed audit gives density/quotient arithmetic: `system_v6/sims/mct_dynamic_admissibility_packet_v0/audit_verdict.md:47-56`.
- Committed post-hardening audit gives computed sheet quotient, presentation table closure, and unchanged values: `system_v6/sims/mct_dynamic_admissibility_packet_v0/audit_verdict.md:85-91`, `:107`.

Expected separation rows:

| Row | Twistor PG(3,2) expected value | MCT committed value | Should differ structurally? | Derivation / audit risk |
|---|---:|---:|---|---|
| Carrier support size | `15` points or `35` line-objects, depending on readout | `384` support rows | Yes | Incidence geometry is finite projective point/line carrier; MCT is a spinor/Hopf sample grid. Like-for-like comparison must name which twistor carrier is used. |
| Projective quotient count, q=2 | `15` projective point classes from `15` raw nonzero vectors | `24` without phase, `192` with phase, density base `12` | Yes in count, but q=2 quotient operation itself is identity | Structural row can separate by object type/count, but audit must not overclaim quotient-ablation separation at q=2. |
| Relation components, true relation | Line-intersection graph connected: `1` component | Full MCT relation components: `1` | Might coincide numerically by accident | Both can report `1` component for different reasons. This is an accidental-coincidence risk unless degree distribution, edge count, or ablation behavior separates. |
| Relation components, ablated/null relation | No relation edges should give `35` line components if line-objects are vertices; `15` if point-objects are vertices | MCT ablated relation components: `384` | Yes if vertex universe is declared | Audit must check vertex universe before comparing numbers. `35` vs `384` separates; `1` vs `1` does not. |
| Relation degree | Line graph degree `18`; point-line bipartite degrees `point=7`, `line=3` | MCT relation degree is grid/operation-specific, not PG line-regular | Yes | This should be a strong structural separator: projective incidence has forced regularity from Gaussian-binomial counts. |
| Pencil/star structure | `15` pencils, each size `7`; each plane has `7` lines | No PG pencil row; MCT has shell/phase/chirality probe rows | Yes | Strong separator if compared as named invariant, not only as class count. |
| Reconstruction from full incidence | Exact recovery of `15` points, mismatch `0` | MCT reconstruction behavior is probe/grid relation dependent, not projective point recovery | Should differ structurally | Audit risk: if both emit a success boolean, `true` may coincide accidentally. Require recovered object count and pair-axiom histogram. |
| q=2 quotient ablation | Expected no-op | MCT phase/probe quotient changes `24 -> 192` when phase is included; ablation controls affect relation components `1 -> 384` | Mixed | Do not compare "no-op quotient ablation" to "phase probe included" as if same operation. It is only evidence that q=2 is a weak quotient discriminator. |
| Chirality row | depends_on_builder_pin: fixed symplectic/dual pairing choice should flip under orientation reversal and survive label shuffle | MCT active `P_chirality` had label-derived caveat, with computed `P_weyl_gap` hardening | Open until builder PIN | Only chirality pairing choice genuinely depends on builder PIN. Expected audit focus: distinguish computed pairing row from label echo. |

Accidental-coincidence risks for audit:

- `relation_components=true/full = 1` can coincide for PG line graph and MCT full relation while the mechanisms differ.
- A boolean reconstruction success can coincide if not paired with recovered cardinality, row-pair intersection histogram, and object type.
- q=2 quotient-ablation no-op must not be treated as a failed implementation if the quotient map is explicitly computed and reported as identity.
- Quotient class numbers can coincide by small arithmetic accident in future variants; require source object, active probe family, and equivalence relation, not just integer equality.

## Builder-PIN Dependency

Only the chirality/orientation row is marked `depends_on_builder_pin`. The finite PG(3,2) counts, line graph, pencil structure, reconstruction expectation, q=2 quotient caveat, SMT incidence facts, and baseline separation arithmetic are derivable before the builder chooses a pairing. The chirality row depends on the pinned symplectic/dual pairing or sign convention named by the builder and must flip under orientation reversal while surviving label shuffle.
