# Audit verdict: discrete_axis6_precedence_v0

Audit mode: fresh read-only independent audit. This verdict file is the only audit-lane write; it is not builder output.

Generated: 2026-06-12T06:53:37Z

Bottom line: `GENUINE-WITH-CAVEATS`.

This packet earns the repo-level status of a genuine finite Axis-6 precedence readout candidate on the committed Family A 33-cell carrier. It also earns the "carrier-honest independence pair" label, but only with the explicit identity-leak caveat: if cell identity / coordinates / direct fingerprints are allowed into the predictor, recovery is perfect and the independence claim collapses into identity lookup.

It does not earn Axis-6 admission, canon status, bridge status, a physics claim, or the three-way `b6 = -b0*b3` claim.

## Verdict

- Repo vocabulary: `GENUINE-WITH-CAVEATS`.
- Classification remains `scratch_diagnostic`.
- Claim ceiling remains `axis_readout_candidate_only`.
- `promotion_allowed=false` and `formal_admission_allowed=false` are honored.
- Axis vocabulary is correct: this is `Phi_T(O(rho))` vs `O(Phi_T(rho))`, not Axis-4 composition order and not the other polarity packets.

## Precedence Reality

The pinned computation recomputes:

- counts: `positive=14`, `negative=14`, `neutral=5`, `nonneutral=28`, `total=33`;
- positive label: `operator_first_precedence`;
- negative label: `terrain_first_precedence`;
- neutral cells: `14, 15, 16, 17, 18`.

Three direct recomputes from the pinned matrices:

| cell | coord | weighted z | sign | adjudication |
|---:|---|---:|---:|---|
| 0 | `[-1.0, 0.0, 0.0]` | `0.036755338799217` | `+1` | operator-first |
| 10 | `[0.0, -1.0, 0.0]` | `-0.009955505697` | `-1` | terrain-first |
| 14 | `[0.0, 0.0, -1.0]` | `0.0` | `0` | neutral |

The five neutral cells are not threshold artifacts. Their raw z-component differences and raw weighted values recompute as exactly `0.0`; the minimum absolute nonzero weighted value is `0.0021132196999014943`, far above `EPS=1e-10`.

## Pin Compliance

The card predeclares the pair and functional before the results:

- `O = S4:D_z`, `pin_sha256=0d7ae0b81d7a92ba490818bb37afe2204cb905fdc43d4d58f35387e64fb72566`;
- `Phi_T = S5:Ne_Spiral_R` at `h=1/2`, `pin_sha256=ced1d4a8395b66077defbfa44dade651cac9c02ef7ea95cca9918a4019b0634a`;
- sign functional: `sign(||Phi_T(O(rho_cell)) - O(Phi_T(rho_cell))||_1 * Delta_z)`.

The code consumes those exact pins: constants bind `PRIMARY_OPERATOR="D_z"`, `PRIMARY_TERRAIN="Ne_Spiral_R"`, `TERRAIN_H="1/2"`, and the expected S4/S5 pin hashes. The S5 flow is computed by exponentiating the committed generator at `h=0.5` and cross-checked against the committed basin `h=1/2` row. No silent builder choice was found.

## Carrier-Honest Independence

The 0/6 rows are on the same 33-cell carrier with 198 generator-labelled edges. The packet reports `axis0_alignment.same_carrier=true`, and the recomputed carrier state object matches the Axis-0 carrier object.

Best-predictor checks:

- `axis0_polarity_sign -> b6_sign`: majority accuracy `0.48484848484848486`, pass.
- `b6_sign -> axis0_polarity_sign`: majority accuracy `0.5151515151515151`, pass.
- full non-identity Axis-0 feature bundle -> `b6_sign`: best accuracy `0.9696969696969697`, pass but narrow.
- identity-inclusive predictor -> `b6_sign`: accuracy `1.0`, identity leak detected.

Adjudication: this is the first non-surrogate 0/6 independence pair only under the carrier-honest no-identity-leak standard. Future citations must say that the full Axis-0 feature report was included, that identity leakage was detected, and that the independence pass excludes cell identity, coordinates, and direct output fingerprints.

## Staged b0*b6 Prediction

The `b0_b6_prediction` table is computed per cell, not asserted. It has 33 rows with staged counts:

- `b0*b6 = -1`: 13 rows;
- `b0*b6 = 0`: 5 rows;
- `b0*b6 = +1`: 15 rows.

This is consistent with panel 6 q2's arithmetic convention where evaluable: `b6=-b0*b3`, so `b0*b6` is only a staged prediction of `-b3`. The packet correctly keeps `axis3_same_carrier_status=not_computed_in_this_packet` and blocks the three-way claim.

## Controls And SMT

Controls fired through the real path:

- commuting control: `O=D_z`, `Phi_T=D_z`, all 33 cells neutral;
- shuffled-order / N01: all 28 nonzero signs flip under reversed declared difference;
- frozen-factor projection: best non-identity predictor accuracy `0.9696969696969697`, not perfect;
- constant-field degenerate: identity/identity all 33 cells neutral;
- label permutation: only 11 matches, label-only reproduction fails.

SMT rows are computed-value bindings, not asserted booleans:

- `z3`: identity verdict `unsat`, erased flip `sat`;
- `cvc5`: identity verdict `unsat`, erased flip `sat`;
- bound values include `positive=14`, `negative=14`, `neutral=5`, `stable_edges=174`, `changed_edges=24`, `edge_count=198`, and both non-recovery booleans.

## Cross-Backend And Validator Checks

Read-only audit checks imported the validator functions without running result-writing entrypoints:

- packet-local `validate_payload(...)`: `ok=true`, `error_count=0`;
- generic `validate_three_engine_sim_result.validate(..., require_pytorch=True, strict_source_backed=True, require_tool_intent=True)`: `ok=true`, `error_count=0`;
- lane source hashes in the envelope match current source files;
- `reads_peer_result=false` for Julia, JAX, and PyTorch;
- all three lanes agree on counts: `positive=14`, `negative=14`, `neutral=5`, `nonneutral=28`, `stable_edge_count=174`, `changed_edge_count=24`.

I did not run the packet-local validator `main()` after audit creation because it writes a validator result and also intentionally expects builder packets to lack `audit_verdict.md`. That is a builder-boundary guard, not a math failure.

## Caveats

`G1_identity_leak`: the carrier-honest independence label depends on excluding identity, coordinates, and direct fingerprints from the predictor. Identity-inclusive recovery is `1.0`.

`G2_backend_granularity`: Julia independently recomputes counts/stability/SMT, but its result does not export a comparable per-cell sign table or canonical sign-vector hash. JAX and PyTorch match the controller table per cell; Julia matches the aggregate values. A follow-on hardening should emit the same canonical per-cell sign-vector hash from all lanes.

`G3_provenance_state`: in this checkout, `system_v6/sims/discrete_axis6_precedence_v0/` is still untracked. The parent pins are committed and checked, but future citation should cite this as an audited workspace packet until the packet and this verdict receive a commit hash.

## Future Citation Rule

Cite this packet only as:

> a genuine scratch Axis-6 precedence readout candidate on the committed Family A 33-cell carrier, using pinned `S4:D_z` and pinned `S5:Ne_Spiral_R` at `h=1/2`, with carrier-honest 0/6 independence under the no-identity-leak predictor rule.

Do not cite it as Axis-6 admission, canon, bridge evidence, physics evidence, Axis-4 composition order evidence, or a completed `b6=-b0*b3` three-way result.

## What The Three-Way b6 Packet Needs

The follow-on packet must compute Axis-3 on this same 33-cell carrier, then emit a per-cell `b0`, `b3`, `b6` table. It must check `b6=-b0*b3` per cell where evaluable, define the neutral-row semantics explicitly, preserve the Axis-3 placement / Axis-6 precedence distinction, and carry the same controls and no-identity-leak predictor rule forward.

It also needs a validator gate that fails any prose-only three-way claim, any carrier swap, and any use of the staged `b0*b6` table as if it were an Axis-3 measurement.
