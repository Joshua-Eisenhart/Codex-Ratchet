# Reconciled M(C,t) Spec

Status ceiling: formal_probe_plan. The future packet result ceiling is `scratch_diagnostic` with `promotion_allowed: false` unless later validators and owner review explicitly raise it.

Inputs reconciled:
- `/tmp/found/grok_mct_draft.md`
- `/tmp/found/gemini_mct_draft.md`
- `system_v6/foundations/working_math_scaffold_20260609.md` sections 19-21
- `~/wiki/concepts/field-wide-compression-probe-contract.md`
- `~/wiki/concepts/constraint-manifold-architecture.md`

## 1. Reconciled Core Object

Use the following finite dynamic admissibility object as the working packet target:

```text
M(C,t) = (
  S_t, C_t, Probe_t, Val_t, ~_t, Q_t, Adm_t, E_t,
  Poss_t, H_t, R_t, Var_t, U_t, Ctrl_t, Rec_t
)
```

where:

| Field | Meaning | Contract mapping |
|---|---|---|
| `S_t` | finite support/state set | `X_n` in `W_n`; `S` in `M(C)` |
| `C_t` | active finite admissibility constraints, with fixed root `C` unless explicitly updated | `C`, `Adm_C` |
| `Probe_t` | finite family of probes `p: S_t -> Val_p` | draft `P_t`; `Q_n`; `P` in `M(C)` |
| `Val_t` | finite probe codomain registry | draft `V_t`, renamed to avoid conflict with variant ledger |
| `~_t` | probe-induced equivalence: `x ~_t y iff forall p in Probe_t, p(x)=p(y)` | `~_P` |
| `Q_t` | quotient classes `S_t / ~_t` | required quotient/equivalence object |
| `Adm_t` | `{x in S_t : all active constraints pass on x/probe row}` | `Adm_C` |
| `E_t` | finite directed relation/dependency/adjacency data | `E_n`; neighborhood/path rules |
| `Poss_t(x)` | finite represented possibility set at each support cell | field contract `P_n(x)` |
| `H_t` | finite history, provenance, graveyard, merge/kill/preserve ledger | `H_n`; controls/receipts support |
| `R_t` | readout registry: each readout names object, probe, pass, kill | `R_n`; local readouts |
| `Var_t` | variant/source ledger, preserving live lanes or marking out of scope | `V_n` |
| `U_t` | finite update composition from the operation vocabulary | composition/bracketing |
| `Ctrl_t` | negative controls and ablations | controls |
| `Rec_t` | source/result/validator/rerun handles | receipts |

The static `M(C)` tuple is therefore preserved, but the object carries time/update structure from the start, matching the standing `M(C,t)` amendment and the `W_n -> W_{n+1}` witness contract.

## 2. Convergence Table: Adopt

| Point | Grok draft | Gemini draft | Reconciled adoption |
|---|---|---|---|
| Finite carrier | finite `S_n subset U` | finite `S_t` | Adopt finite `S_t`; no completed infinity at one witness. |
| Finite probes | finite maps to finite values | finite probe functions to finite `V_t` | Adopt finite `Probe_t` with finite per-probe codomains. |
| Probe equivalence | `s ~ s'` iff all probes agree | same | Adopt as `~_t`; quotient `Q_t = S_t / ~_t` is required. |
| Admissibility | finite predicates in `C` decide `Adm_n` | finite boolean constraints on probe rows | Adopt finite `Adm_t`; preserve a choice point for state-predicate vs probe-row predicate form. |
| Relation data | binary `E_n subset S_n x S_n` | directed adjacency `E_t` | Adopt finite directed relation/dependency object `E_t`. |
| Dynamic update | `U_n` finite composition of five primitives | `U_t` composition of five primitives | Adopt five-operation vocabulary: compression, expansion, warping, folding, reindexing. |
| Ratchet/order condition | noncommuting update order on `(S,P,E)` | noncommuting up to isomorphism | Adopt order-sensitivity as a finite table witness with explicit equality/isomorphism policy. |
| SMT shape | quantifier-free finite tables | SMT falsifiable claims | Adopt exact finite table obligations in z3 and cvc5. |
| Reindexing | bijective transport preserves structure | same | Adopt as label-shuffle control and invariance check. |
| Folding | partial/surjective gluing | surjective quotient/gluing | Adopt folding as finite surjection with a default equivalence-respecting mode and a separate aggregation mode choice point. |

## 3. Divergence Table: Preserve As Choice Points

Do not collapse these. The owner can choose, or the packet sim can run both modes and report discriminating behavior.

| Choice point | Alternative A | Alternative B | Consequence / discriminator |
|---|---|---|---|
| Compression representation | Grok materializes quotient: `S_{t+1}=S_t/~'`. | Gemini retains support: `S_{t+1}=S_t`, updates `Q_t`. | Run both as `representation_mode=quotient_materialized` vs `carrier_retained`. Counts of `S_t`, `E_t`, and later fold domain differ. |
| Constraint form | Grok constraints are predicates on states `c(s)`. | Gemini constraints are predicates on probe rows. | Keep both as `state_predicate` and `probe_row_predicate`. Probe-row form needs arity/transport rules when probes are dropped/added. |
| Constraint time index | Fixed active `C`. | Implied arity changes with `V_t`/`P_t`. | Default: fixed root `C` plus explicit `C_t` view. Any active-constraint update must be logged as its own operation, not hidden inside probe changes. |
| Folding legality | Grok allows identifying non-equivalent states, with probe transport/aggregation where defined. | Gemini requires `ker(pi) subseteq ~_t`; aggregation is a choice point. | Default fixture uses equivalence-respecting fold. Non-equivalent fold is an `aggregation_mode` branch requiring explicit aggregation, killed-information ledger, and controls. |
| Relation warp | Grok allows arbitrary replacement `E_{t+1} subset S x S`. | Gemini uses finite delta update `(E union Delta+) \ Delta-`. | Adopt delta update for fixtures; keep arbitrary replacement as a broader operation mode requiring relation-ablation controls. |
| Entropy/ambiguity direction | Grok says compression increases class-size ambiguity/entropy. | Gemini defines Shannon entropy over quotient classes and predicts compression decreases `H_Q`. | Do not use one unnamed `H`. Track `H_Q` = class-distribution entropy, `A_Q` = average indistinguishability/ambiguity, plus field contract `support_size` and `possibility_mass`. |
| Ratchet fixture | Grok uses compression/expansion on a 4-state probe square. | Gemini uses warping/folding on an 8-state cycle. | Adopt Gemini as pinned main fixture because it exercises `E_t` and whole-field controls. Preserve Grok as a focused quotient ratchet side-control, but it needs explicit `p3` and representation semantics. |
| Equality in ratchet condition | Grok uses literal inequality of final `(S,P,E)`. | Gemini uses non-isomorphism and witness pair/admissibility xor. | Build must report both `literal_table_diff` and `non_isomorphic_diff`; owner decides which is the packet pass condition. |
| Folded self-loops | Gemini predicted `|E_3|=4`, implying self-loops erased or ignored. | Relation pushforward retains self-loops, giving `|E_3|=8` for the pinned fixture. | Pin both values under `self_loop_policy=erase` vs `retain`; relation readouts must state policy. |
| Whole-field readout | Drafts mostly compute local quotient/admissibility counts. | Field-wide contract needs load-bearing cross-cell relation dependency. | Build must include at least one `E_t`-dependent readout, e.g. relation-ablation gap, connectedness, order-commutator, or edge transport ledger. |

## 4. Compatibility Check Against Standing Contracts

| Contract requirement | Status | Notes / required repair |
|---|---|---|
| `M(C)` first, not axes/physics/QIT bridge first | Pass | Both drafts target the finite admissibility object, not a downstream bridge. |
| Build order: root constraints -> `M(C)` -> geometry on `M(C)` -> axes/readouts | Pass with guard | No axis/flux/terrain claim is admitted here. Future terrain/flux work must be geometry on `M(C,t)`, not axis content. |
| Dynamic `M(C,t)` from start | Pass | Both drafts use discrete `n`/`t`; reconciled object makes `U_t`, `H_t`, and witness steps explicit. |
| `W_n = (X_n, P_n, E_n, H_n, Q_n, R_n, V_n)` | Partial in drafts, repaired in reconciled spec | Drafts have `S/E/probes`; they lack explicit `Poss_t`, `H_t`, `R_t`, and `Var_t`. Reconciled object adds them. |
| Finite witness discipline | Pass | All carrier/probe/relation tables are finite in the drafts and fixture. |
| Whole-field dependency | Partial | Gemini's `E_t` supports this, but the packet must make an `E_t`-dependent readout load-bearing and show local-only/relation-ablation/product-null controls. |
| Compression-vs-expansion contract | Partial | Drafts track quotient counts and entropy but not `support_size`, `possibility_mass`, and named compression quality together. Build must emit all three. |
| Readout contract | Partial | Drafts list metrics; build must define each readout with finite object, probe family, pass condition, and kill condition. |
| Variant ledger integrity | Missing in drafts | Build should keep `Var_t` with inactive/out-of-scope lanes marked, not collapsed or silently erased. |
| No casual canonical/admission language | Pass if ceiling held | Spec and build card must remain `formal_probe_plan` / `scratch_diagnostic`, `promotion_allowed=false`. |
| Order correctness checked separately | Pass with guard | Build must test both content equality and operation order equality/noncommutation. |

Compatibility conflicts to flag:

1. Gemini's `C: V_t^{|P_t|} -> {0,1}` conflicts with probe dropping unless `C_t` transport/arity is explicit.
2. Grok's materialized compression quotient can hide support-size accounting unless `S_t` vs `Q_t` representation mode is recorded.
3. Grok's non-equivalent folding is too permissive for default `M(C)` quotient semantics unless aggregation and killed-information ledgers are explicit.
4. Both drafts under-specify the field-wide `H_t/R_t/Var_t/Poss_t` slots.
5. A bare entropy column is incompatible with section 21's entropy-discipline warning. The build must name the entropy object every time.

## 5. Pinned Minimal Fixture

Adopt Gemini's 8-state fixture as the main fixture because it exercises finite support, probe quotient, admissibility, adjacency, warping, folding, relation ablation, and order controls. Merge in Grok's 4-state fixture as a separate quotient/order micro-control, not the main pinned fixture.

### 5.1 Main Fixture Definition

```text
S_0 = {0,1,2,3,4,5,6,7}
Val_0 = {0,1,2,3}
Probe_0 = {p1, p2}
p1(x) = x mod 2
p2(x) = x mod 4
E_0 = {(x, (x+1) mod 8) : x in S_0}
C_root = {c_even}
c_even(x) := p1(x) = 0
Adm_0 = {0,2,4,6}
Poss_t(x) default fixture value = singleton live branch for each represented state unless a branch split operation is explicitly added
Var_t = all source/variant lanes preserved as out_of_scope for this packet; active lane = foundations_MCt_only
```

Readout definitions:

| Readout | Finite object | Probe | Pass condition | Kill condition |
|---|---|---|---|---|
| `support_size` | `S_t` | count | finite count emitted every step | unbounded or implicit support |
| `quotient_count` | `Q_t` | `Probe_t` equivalence | expected `|Q_t|` per step | quotient not recomputable from probe table |
| `H_Q` | class distribution over `S_t/~_t` | finite partition entropy | matches predicted value under chosen log base 2 | entropy named without distribution |
| `A_Q` | average ambiguity `sum_x log2(|[x]|)/|S_t|` | class membership | compression raises ambiguity when probes are dropped | ambiguity conflated with `H_Q` |
| `edge_count` | `E_t` | relation table | expected edge count under self-loop policy | relation policy hidden |
| `cc_weak` | underlying undirected graph of `E_t` | relation connectivity | relation ablation changes value | unchanged under relation ablation and product/null controls |
| `adm_count` | `Adm_t` | active constraints | expected admissible count | constraints not finite or not transported |

### 5.2 Update Sequence

```text
t=0 -> t=1: COMPRESSION
  Drop p2.
  Default representation: carrier_retained.
  Probe_1 = {p1}.

t=1 -> t=2: WARPING
  Add DeltaE+ = {(x, (x+4) mod 8) : x in S_1}.
  DeltaE- = empty.

t=2 -> t=3: FOLDING
  pi(x) = x mod 4.
  Valid in default mode because ker(pi) subseteq ~_2.
  Probe_3 = {p1'} with p1'(pi(x)) = p1(x).
```

### 5.3 Predicted Values

Default representation mode: `carrier_retained` until folding. Default graph connectivity: weak connected components. Entropy base: log2.

| t | operation | `|S_t|` | probes | `|Q_t|` | class sizes | `H_Q` | `A_Q` | `|E_t|` if loops erased | `|E_t|` if loops retained | `cc_weak` | `|Adm_t|` |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | initial | 8 | `{p1,p2}` | 4 | `2,2,2,2` | 2.0 | 1.0 | 8 | 8 | 1 | 4 |
| 1 | drop `p2` | 8 | `{p1}` | 2 | `4,4` | 1.0 | 2.0 | 8 | 8 | 1 | 4 |
| 2 | add opposite edges | 8 | `{p1}` | 2 | `4,4` | 1.0 | 2.0 | 16 | 16 | 1 | 4 |
| 3 | fold `x mod 4` | 4 | `{p1'}` | 2 | `2,2` | 1.0 | 1.0 | 4 | 8 | 1 | 2 |

Relation ablation prediction:

```text
At t=2, replace E_2 with empty relation.
edge_count: 16 -> 0
cc_weak: 1 -> 8
quotient_count: unchanged at 2
adm_count: unchanged at 4
```

This separates relation-dependent readouts from local/probe-only readouts and prevents a false field-wide claim from quotient counts alone.

### 5.4 Controls

| Control | Expected result |
|---|---|
| Constant-probe drop | Dropping a constant probe must not strictly reduce `|Q_t|`; z3/cvc5 expected `UNSAT` for strict merge. |
| Redundant-probe expansion | Adding a probe functionally determined by existing probes must not increase `|Q_t|` or `H_Q`; expected `UNSAT` for strict information gain. |
| Relation ablation | `edge_count` and `cc_weak` change; quotient/admissibility counts do not. |
| Product/null relation | Product/disconnected/null witness must not reproduce the relation-dependent readout. |
| Label shuffle/reindex | `|S|`, `|Q|`, class sizes, `H_Q`, `A_Q`, and `|Adm|` preserved; label-specific claims killed. |
| Wrong-order fold/warp | Under strict domain policy, `warp(0,4)` after fold is invalid; under permissive loop policy it becomes self-loop/redundant. Report both. |
| Invalid fold | If `ker(pi) not subseteq ~_t` in equivalence-respecting mode, fold is rejected; in aggregation mode it must emit aggregation and killed-information ledger. |
| Local-only baseline | Any claimed field-wide output computed only as `f(x, probes(x))` is killed for field-wide compression status. |

### 5.5 Grok 4-State Side-Control

Keep Grok's 4-state square as `fixture_side_control=probe_square_order`.

Required repairs before using it:

```text
S_0 = {a,b,c,d}
Probe_0 = {p1,p2}
p1: a,b -> 0; c,d -> 1
p2: a,c -> 0; b,d -> 1
E_0 = empty
Adm_0 = S_0
```

The draft's claimed reverse-order count depends on:

1. whether compression materializes the quotient or only updates `Q_t`;
2. the full definition of `p3` on all four original states;
3. whether expansion after quotienting can split a previously merged class.

Therefore the side-control is useful, but not pinned as the main fixture until those semantics are explicit.

## 6. BUILD CARD Skeleton: `mct_dynamic_admissibility_packet`

```yaml
packet_id: mct_dynamic_admissibility_packet_v0
claim_ceiling: scratch_diagnostic
promotion_allowed: false
objective: >
  Build and verify a finite dynamic admissibility object M(C,t)
  with explicit compression, expansion, warping, folding, reindexing,
  witness-step bookkeeping, field-wide relation controls, and order-sensitivity checks.

read_first:
  - /tmp/found/mct_reconciled_spec.md
  - system_v6/foundations/working_math_scaffold_20260609.md#sections-19-21
  - ~/wiki/concepts/field-wide-compression-probe-contract.md
  - ~/wiki/concepts/constraint-manifold-architecture.md

bounded_claim:
  sim_id: mct_dynamic_admissibility_packet_v0
  object: M(C,t)
  fixture: eight_state_cycle_mod4_fold
  active_constraints:
    - c_even: p1(x) = 0
  operation_sequence:
    - compression_drop_p2
    - warping_add_opposite_edges
    - folding_mod4
  choice_points_preserved:
    - carrier_retained_vs_quotient_materialized
    - state_predicate_vs_probe_row_predicate_constraints
    - equivalence_respecting_fold_vs_aggregation_fold
    - literal_table_diff_vs_non_isomorphic_diff
    - self_loop_policy_erase_vs_retain
  allowed_claims:
    - finite witness tables constructed
    - predicted fixture values reproduced
    - named controls separate relation-dependent from local/probe-only readouts
    - order-sensitive operation pairs classified under explicit equality/domain policy
  forbidden_claims:
    - canonical manifold admission
    - Axis0 closure
    - terrain or flux finality
    - physics bridge admission
    - QIT/engine admission

engine_contract:
  schema_version: three_engine_sim_result_v1
  mode: all_three_full_sims
  lanes:
    - julia
    - jax
    - pytorch
  audit_order:
    - combined_envelope
    - julia_local
    - jax_local
    - pytorch_local
    - controller_comparison

julia_canon_lane:
  role: semantic_owner
  responsibilities:
    - define exact finite sets, probe tables, quotient relation, admissibility, and operation semantics
    - compute pinned predicted values exactly
    - arbitrate representation/equality/domain policies
    - export canonical fixture tables and hashes
  load_bearing_outputs:
    - quotient tables Q_t
    - operation result tables
    - predicted scalar table
    - policy-tagged fold/warp commutator result

jax_workhorse_lane:
  role: batched_exhaustive_worker
  responsibilities:
    - exhaustively recompute quotient counts, entropy/ambiguity columns, edge counts, controls
    - sweep choice points where finite enough
    - verify local-only and relation-ablation separations across table variants
  load_bearing_outputs:
    - independent scalar recomputation
    - batched control matrix
    - max divergence from Julia canonical values

pytorch_graph_lane:
  role: graph_network_relation_worker
  responsibilities:
    - build adjacency tensors/edge_index for E_t
    - compute relation readouts under original, ablated, product/null, shuffled, and folded graphs
    - confirm relation-dependent readout is not reducible to per-state probe rows
  load_bearing_outputs:
    - graph readout table
    - relation-ablation gap
    - label-shuffle invariance report

smt_obligations:
  solvers:
    - z3
    - cvc5
  obligations:
    - name: finite_equivalence_relation
      expected: prove/refute with finite tables that ~_t is reflexive, symmetric, transitive
    - name: quotient_count_matches_probe_rows
      expected: SAT for fixture construction; UNSAT for mismatched claimed counts
    - name: compression_cannot_increase_quotient_count
      expected: UNSAT for counterexample under finite probe dropping
    - name: expansion_cannot_decrease_quotient_count
      expected: UNSAT for counterexample under adding probes
    - name: constant_drop_no_strict_merge
      expected: UNSAT
    - name: redundant_probe_no_information_gain
      expected: UNSAT for strict gain
    - name: fold_size_nonincrease
      expected: UNSAT for |S_{t+1}| > |S_t|
    - name: equivalence_respecting_fold_well_defined
      expected: SAT for pi(x)=x mod 4 at t=2
    - name: invalid_fold_rejected
      expected: UNSAT in equivalence_respecting mode when ker(pi) not subseteq ~_t
    - name: reindexing_invariants
      expected: UNSAT for changed |S|, |Q|, class multiset, H_Q, A_Q, |Adm|
    - name: relation_ablation_gap
      expected: SAT for cc_weak original != cc_weak ablated in pinned fixture
    - name: local_only_kills_field_wide_claim
      expected: UNSAT for field-wide status if all load-bearing readouts ignore E_t/H_t/Q_t cross-cell data
    - name: order_sensitivity_policy_table
      expected: classify warp/fold and compression/expansion pairs under explicit equality/domain/self-loop policies

controls:
  - constant_probe_drop
  - redundant_probe_add
  - relation_ablation
  - product_null_relation
  - label_shuffle_reindex
  - wrong_order_update
  - invalid_fold
  - local_only_baseline
  - quotient_materialized_vs_carrier_retained
  - self_loop_erase_vs_retain

result_envelope_required_fields:
  - schema_version
  - engine_contract
  - classification: scratch_diagnostic
  - promotion_allowed: false
  - source_paths
  - source_sha256
  - fixture_definition
  - choice_point_results
  - witness_mapping_Wn
  - readout_registry
  - variant_ledger
  - controls
  - engines.julia.reads_peer_result: false
  - engines.jax.reads_peer_result: false
  - engines.pytorch.reads_peer_result: false
  - crossover_proofs.z3
  - crossover_proofs.cvc5
  - divergence.max_divergence
  - claim_ceiling

acceptance:
  - all three engine lanes run or are honestly marked blocked/excluded with reason
  - Julia canonical predicted values match fixture table
  - JAX and PyTorch independently reproduce their scoped values or report bounded divergence
  - z3 and cvc5 agree on each SMT obligation polarity
  - relation-ablation and local-only controls prevent false field-wide status
  - every entropy/ambiguity number names its finite object
  - result validates with the repository three-engine validator for the declared mode
  - final report says scratch_diagnostic only

open_owner_decisions:
  - choose default compression representation for future packets
  - choose whether non-equivalent folding is allowed as aggregation mode
  - choose literal table inequality vs non-isomorphism as the ratchet pass condition
  - choose self-loop retention policy for folded relations
  - choose whether constraints are primarily state predicates or probe-row predicates
```

## 7. Immediate Next Move

The next admissible implementation is a micro packet that encodes the pinned 8-state fixture, emits the full readout table under both self-loop policies, and runs z3/cvc5 on the listed finite obligations. It should not touch terrain, flux, axes, physics bridge, or QIT claims except as explicitly out-of-scope ledger rows.
