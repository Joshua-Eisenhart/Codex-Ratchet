# manifold_super_sim_v2_weld Audit Verdict

Bottom line: `VERDICT: GENUINE-WITH-CAVEATS`, scratch diagnostic only.

This is not a collage. The packet holds separate Family A and Family B state objects, rebuilds the
required parent anchors through the live parent builders, declares a row-by-row weld map, computes
finite A+B weld rows from both family summaries, and passes cross-family perturbation controls plus
SMT flips. It is also not a surface-level or independent-backend result: the earned weld content is
finite chart-to-chart bookkeeping, the Julia lane is an anchor-scope literal count/proof lane, and
JAX/PyTorch use the shared Python common builder for the full weld object.

## Accepted Claim

`manifold_super_sim_v2_weld` may be cited as a scratch-diagnostic A+B chart-to-chart weld packet
that:

- preserves separate pinned Family A and Family B state objects;
- rebuilds the committed Family A and Family B anchor rows instead of importing finished anchors;
- declares which rows are independent, related-not-shared, shared-standard, or weld-derived;
- computes finite weld relation rows from both family objects;
- runs A-only, B-only, weld-only, stale-import, decorative-reachability, SMT, validator, and pytest
  checks.

Rejected above ceiling:

- no formal admission;
- no canonical manifold proof;
- no axis, bridge, or physics evidence;
- no charts-on-network / charts-on-surface v3 result;
- no independent full-object Julia/JAX/PyTorch implementation.

## Decisive Recompute

Fresh recomputation through the live parent builders gave the expected anchors.

Family A:

- `G0_transition_graph_sha256 =
  bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0`;
- `G1_terminal_class_sizes = [1, 14, 18]`;
- `D_z_holevo_nats = 0.411341122022618`;
- `stage_word_endpoint_nats = 0.0932927444282512`;
- stale-import control fired.

Family B:

- deep-chain denominator `16`;
- exact final volume `pi**2/4`;
- entropy deltas `[-log(4), -log(2), -log(2)]`;
- compression `384 -> 288 + 96`;
- hash-chain heads:
  - `41d0113914c03390eac69b7e6ba7763d439dd275e981458bb90b5b4eef14e3ff`;
  - `f78beccf9623dd94a9316e03132616bb250e85ee5b0186e02b356db207138b47`;
  - `20d5517a287c8f351a396e4001927cf8a9b789029788c6c4a6ff1a5ce15c8961`;
- conservation defect `0.0`;
- stale-import control fired;
- B3 record rows have row-local `z4_syndrome_record_v0` co-citations;
- no `axis0_*` leak was found in the B-scoped projection.

End-to-end relation spot checks:

- `W3_partition_relation`: Family A terminal-class count `3` plus Family B `Z4 x Z2` orbit order
  `8` gives weld relation value `11`.
- `W4_record_conservation_relation`: Family A erased Z4 record retained nats `0.0` and Family B
  conservation defect `0.0` give a shared finite state-plus-record zero-defect row.
- `W5_entropy_typing_relation`: typed-bookkeeping reconciliation rejects a cross-type sum and does
  not silently declare a product convention.

## Nine-Item Weld List

1. `PASS-WITH-CAVEAT`. Separate pinned state objects exist and are not folded:
   `manifold_super_sim_v0:271b13f6...` and `manifold_family_b_integrated_v0:ce89ce55...`.
   Caveat: both are consumed at their parent scratch ceilings and carry parent caveats.

2. `PASS-WITH-CAVEAT`. The weld map is real, not just juxtaposition. It declares independent state
   objects, related chart/quotient discipline, independent partitions with an explicit relation row,
   related record/accounting convention, related typed-bookkeeping convention, shared lineage
   standard, backend scope, and external two-engine context. At least W3 and W4 are computed from
   both family objects. Caveat: the strongest weld relation is finite count/accounting content, not
   a geometric chart-on-surface map.

3. `PASS`. B-scoped projection is present. The current envelope reports `axis0_leak_detected=false`,
   and B record rows expose projected B fields rather than raw axis-bearing parent payloads.

4. `PASS`. Programmatic pin consumption is live. Family A rebuilds G0/G1/Holevo/endpoint through
   the parent common builder; Family B rebuilds the B1 pin block and B2 compression flow. B-only pin
   mutation moves the B denominator, and A-only mutation moves the A Holevo row.

5. `PASS`. B3 row-local Z4 co-citation is present on both `B3_full_record` and
   `B3_erased_record`, with `finite_counting_state_plus_record` convention labels.

6. `PASS`. Unified-style trajectory lineage is present: file-byte SHA, stable payload SHA,
   `trajectory_step_id`, `row_step_lineage_id`, and `row_step_class_why`. Current row counts are
   A=`5`, B=`16`, WELD=`8`; classes are `STEP_DEPENDENT=17`, `CARRIED=4`, `WELD_DERIVED=8`.

7. `PASS-WITH-CAVEAT`. The backend contract decision is honest:
   `a_b_weld_shared_common_builder_with_julia_anchor_scope`. Caveat: Julia is not a full parent
   object rebuild; it proves count/relation rows over finite anchor values. JAX/PyTorch are package
   backed around the shared common builder, not independent full-object implementations.

8. `PASS-WITH-CAVEAT`. Cross-family controls pass. A-only perturbation moves A and not B; B-only
   perturbation moves B and not A; weld-only perturbation moves only `W3_partition_relation`.
   The decorative detector could fire: a forced no-input signature movement produced
   `decorative_change_detected=true` on `W2_chart_quotient_relation`. Caveat: this detector catches
   no-input row movement, not every possible stable-but-irrelevant decorative row. The anti-collage
   verdict therefore rests on W3/W4 recomputation plus perturbation controls, not on this detector
   alone.

9. `PASS-WITH-CAVEAT`. SMT rows bind Family A values, Family B values, and the weld relation with
   decisive flips. Z3 and cvc5 return `unsat` for the true identities and `sat` for erased/perturbed
   expectations. Caveat: SMT is finite integer/accounting binding, not a formal proof of surface
   geometry.

## Cross-Family Controls

Fresh read-only recomputation reported:

- `A_only_perturbation_control`: Family A anchor moved; Family B anchor signature stayed
  `6013d5f3d8a73c83131dfab8ed30848f1528d7abe2a90b27a538c0b0d8bbfed5`.
- `B_only_perturbation_control`: Family B anchor moved; Family A anchor signature stayed
  `da5b2bfdbd031f078f9429a171b16b75eda7451a5df7c841c9c2d75be927c415`.
- `weld_only_perturbation_control`: only `W3_partition_relation` moved.
- `stale_import_per_family`: both Family A and Family B stale-import controls fired.
- baseline decorative detector: no row moved when neither family input changed.
- forced no-input movement check: detector became reachable and flagged `W2_chart_quotient_relation`.

## SMT

Fresh recomputation produced the expected solver statuses:

- `z3_family_a_anchor`: identity `unsat`, erased flip `sat`;
- `cvc5_family_a_anchor`: identity `unsat`, erased flip `sat`;
- `z3_family_b_anchor`: identity `unsat`, erased flip `sat`;
- `cvc5_family_b_anchor`: identity `unsat`, erased flip `sat`;
- `z3_weld_relation`: binds A=`3`, B=`8`, weld=`11`; identity `unsat`, erased flip `sat`;
- `cvc5_weld_relation`: binds A=`3`, B=`8`, weld=`11`; identity `unsat`, erased flip `sat`.

## Verification

Fresh checks run read-only, avoiding packet commands that rewrite result JSONs:

- runtime doctor:
  `ok=True install_state=stable_observed`;
- packet validator function:
  `packet_validate_payload_ok=true`, `error_count=0`;
- generic validator:
  `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent ...`
  returned `ok=true`;
- pytest with bytecode/cache disabled:
  `5 passed in 19.21s`;
- lane source hashes match recorded `source_sha256` for Julia, JAX, PyTorch, and the envelope source;
- all lane results report `all_pass=true` and `reads_peer_result=false`.

I did not run `git add` or commit. I did not intentionally rewrite builder result artifacts during
the audit.

## Named Caveats

`G1_WELD_RELATION_IS_FINITE_BOOKKEEPING_NOT_SURFACE_GEOMETRY`: W3/W4 are real A+B relation rows,
but they are finite count/accounting rows. They do not establish charts-on-surface, network-level
surface geometry, bridge, axis, or physics claims.

`G2_JULIA_LANE_ANCHOR_SCOPE_IS_LITERAL_COUNT_CHECK`: the Julia lane uses literal Family A terminal
class sizes and a constructed `Z4 x Z2` orbit graph. This is acceptable under the declared
anchor-scope mode, but it must not be cited as an independent Julia rebuild of both parent objects.

`G3_DECORATIVE_DETECTOR_REACHABLE_BUT_NARROW`: the detector can fire for no-input row movement, but
it is not a complete detector for stable decorative rows. Future packets should add a semantic
dependency test for every weld row, not only a no-op signature movement test.

`G4_SHARED_COMMON_BUILDER_BACKEND_SCOPE`: JAX and PyTorch are package-backed around the shared
Python common builder. This is honest in the current mode, but blocks any full independent
all-backend citation.

`G5_PARENT_CAVEATS_CARRIED`: Family A still carries its post-hardening caveats G3-G7, and Family B
still carries backend-scope/raw-parent-width lessons. v2 consumes those objects; it does not promote
or erase their ceilings.

`G6_CURRENT_PACKET_UNTRACKED`: this audit verifies the current filesystem packet. `git status`
shows `system_v6/sims/manifold_super_sim_v2_weld/` as untracked in this checkout, and no commit hash
exists for the v2 packet yet.

## Future-Citation Rule

Allowed citation:

`manifold_super_sim_v2_weld` is a `GENUINE-WITH-CAVEATS` scratch-diagnostic A+B chart-to-chart weld
packet: it keeps separate Family A/B state objects, recomputes their anchor rows from pinned sources,
declares a machine-checkable weld map, computes finite A+B weld relation/accounting rows, and passes
cross-family controls plus SMT flips.

Required suffix:

`Use with caveats G1-G6: the weld relation is finite bookkeeping rather than surface geometry, Julia
is anchor-scope only, the decorative detector is narrow, JAX/PyTorch share the common builder, parent
ceilings/caveats carry, and the packet is currently untracked in this checkout.`

Forbidden citation:

- Do not cite it as `GENUINE` without caveats.
- Do not cite it as canonical, formal, bridge, axis, physics, or charts-on-surface evidence.
- Do not cite it as an independent full-object Julia/JAX/PyTorch implementation.
- Do not use it to claim v3 or Family C integration.

## What v3 Needs

v3 must build charts on the surface, not only a chart-to-chart finite weld. At minimum:

1. a surface/network state object whose coordinates are computed directly, not inferred from A+B
   bookkeeping rows;
2. explicit chart maps and transition functions between the surface coordinates, with quotient
   conventions pinned per row;
3. a source-faithful flux/chirality or L/R asymmetric engine object if two-engine language is used;
4. cross-family controls that perturb surface geometry separately from A anchors, B anchors, and
   weld bookkeeping rows;
5. semantic dependency tests proving each surface row changes under its own admitted input and not
   under unrelated family perturbations;
6. SMT/proof rows that bind actual chart-transition/surface invariants, not only integer anchor
   counts;
7. an honest backend decision: either keep shared-common scope explicit, or implement truly
   independent full-object lanes.

## Sweep 3 Correction Annotation

W3 `B_ORDER_IS_DEFINITIONAL`:
`b_order=8` is definitional in the Family B construction: `orbit_order = len(range(z4_order) x range(z2_order)) = z4_order * z2_order = 4 * 2`. W3 therefore adds a genuinely computed Family A terminal-class count (`a_count=3`) to a definitional Family B orbit-size constant (`b_order=8`). Rows saying W3 is `computed from both family objects` must be narrowed accordingly; the row is not a discovered cross-family group-action relation.

W4/accounting qualifier:
W4's two zeros are structurally guaranteed inside their separate families: Family A uses a single-bin erased record, and Family B uses a uniform phase construction. W4 is a typed bookkeeping/accounting row, not an independently constraining cross-family relation.

Honest summary:
Where this packet is cited compactly, call it `a typed-accounting weld`: separate Family A/B state objects, rebuilt anchors, row-by-row declarations, finite accounting relation rows, and controls/SMT at `scratch_diagnostic` ceiling. Do not cite all weld rows as having discovered cross-family mathematical content.
