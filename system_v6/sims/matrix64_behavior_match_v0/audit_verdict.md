# audit_verdict.md -- matrix64_behavior_match_v0

Auditor: independent Codex cross-backend auditor.
Scope: read-only audit except this verdict file. No `git add` or commit.
Freshness tier: `TIER-3` because the prompt supplied builder claims and prior audit context; decisive descent, closure, controls, and boundary rows were recomputed independently from source/result artifacts.
Wizard route truth: partial/controller-local sim audit with local tools only; no native subagent or child-worker topology is claimed.

Bottom line: **PASS_WITH_CAVEATS as a bounded `scratch_diagnostic` realization-relative behavioral-symmetry table.** The packet earns the narrow claim that, for the pinned 64-stage `eng_64` realization and the committed 16-component fingerprint quotient, exactly the 64 flip-generated translations descend; `vertical_rotation` and `trigram_swap` break all 16 components. It does **not** earn a 64-behavior isomorphism, Matrix64-general symmetry, Matrix64 completion, King-Wen-order correspondence, QIT/physics/bridge/axis admission, formal admission, or promotion beyond scratch diagnostic.

## Citation Anchors

- Build scope/fences: `system_v6/sims/matrix64_behavior_match_v0/build_card.md:20-35` defines the component-descent question and required controls; `build_card.md:37-46` fences the packet to realization-relative scratch evidence and excludes Matrix64-general, 64-behavior iso, King-Wen, QIT, physics, bridge, axis, and completion claims.
- Descent implementation: `system_v6/sims/matrix64_behavior_match_v0/matrix64_behavior_match_v0.py:223-293` reads committed component IDs and applies the correct criterion: every source component's member stages must map into one target component.
- Generator mapping: `matrix64_behavior_match_v0.py:80` pins line-to-axis correspondence as `{1:6,2:5,3:3,4:4,5:1,6:2}`; `matrix64_behavior_match_v0.py:203-220` builds line flips, complement, vertical rotation, trigram swap, and induced engine permutations.
- Full-group enumeration: `matrix64_behavior_match_v0.py:188-200` computes closure over the generated address group; `matrix64_behavior_match_v0.py:411-425` filters every generated element for descent rather than relying only on generator rows.
- Result rows: `results/matrix64_behavior_match_v0_results.json:1061-1064` and `:1221-1224` show `flip_line_5/6` descend with zero pointwise component change; `:421-424` shows nontrivial `flip_line_1` descent; `:1381-1384` shows complement descent; `:2337-2340` and `:3293-3296` show vertical rotation/trigram swap break descent.
- Subgroup/result boundary: `results/matrix64_behavior_match_v0_results.json:4751-4762` reports `64/256` and the translation-only structural description; `:128-139` and `:3309` carry claim fences and scratch classification.
- Prior audit consistency: `system_v6/sims/iching_symmetry_match_v0/audit_verdict.md:138-142` records the earlier quotient-partial `n=16` finding and maps `flip_line_5/6` to the Axis1/Axis2 preservation rows; `system_v6/receipts/iching_engine_symmetry_match_20260612.md:265-275` defines the same `phi(h)=(l5,l6,l3,l4,l2,l1)` line-axis map.
- Fingerprint IDs: `system_v6/sims/eng64_stage_fingerprint_ids_v0/results/eng64_stage_fingerprint_ids_v0_results.json:49-220` lists the 16 stable component IDs, each with four stages; `:1893-1896` reports the 16 fresh fingerprints.

## Fresh Checks Run

1. No-write validator predicate rerun, with `PYTHONDONTWRITEBYTECODE=1` and no validator-result rewrite:

```text
validate_files(errors); validate_payload(errors, result)
=> {"error_count": 0, "errors": [], "ok": true}
```

2. Independent descent/closure recomputation from `eng64_stage_fingerprint_ids_v0_results.json`, not from builder prose:

```text
full_group_size=256
descending_count=64
non_descending_count=192
descending_equals_all_64_translations=true
descending_closed_under_composition=true
descending_closed_under_inverse=true
descending_linear_bases_unique=[[1,2,4,8,16,32]]
descending_translation_masks_minmax_count=[0,63,64]
```

3. Required generator teeth:

```text
flip_line_5: descends=true, pointwise_changed_stage_count=0
flip_line_1: descends=true, pointwise_changed_stage_count=64
complement: descends=true, pointwise_changed_stage_count=64
vertical_rotation: descends=false, breaking_component_count=16
trigram_swap: descends=false, breaking_component_count=16
```

4. Controls:

```text
identity_descends=true
random_control_all_named_break=true
coarsened_changes_table=true
```

## Verdict Teeth

### 1. Descent Criterion

Accepted.

The packet applies the right quotient criterion: a generator descends exactly when each 4-stage fingerprint component maps wholly into one target component. My recomputation from the committed fingerprint component IDs recovered:

- `flip_line_5`: descends pointwise-trivially, 0 changed stages.
- `flip_line_1`: descends nontrivially, 64 changed stages.
- `complement`: descends nontrivially, 64 changed stages.
- `vertical_rotation`: fails descent, 16/16 components break.
- `trigram_swap`: fails descent, 16/16 components break.

This satisfies the requested minimum of one pointwise-trivial flip, one nontrivial flip, one breaking permutation, and complement.

### 2. The 64/256 Claim And Closure

Accepted with a hardening caveat.

This is **not** merely a generator descent table. The source enumerates the full generated 256-element address group and filters all group elements for descent (`matrix64_behavior_match_v0.py:411-425`). Independent recomputation confirms the descending set is exactly the 64 translations `e -> e xor mask`, masks `0..63`, with identity linear basis only. I also explicitly checked closure under composition and inverses.

Caveat: the result JSON should emit a named `closure_checks` row in the next hardening pass. The current packet has enough source/result evidence plus fresh audit evidence to accept the subgroup claim, but making closure explicit would prevent later readers from mistaking `64` for a generator-only inference.

### 3. Prior I Ching Packet Consistency

Accepted.

The line-number to axis-bit correspondence is the committed one, not a relabel: line 5 maps to Axis1 and line 6 maps to Axis2 (`matrix64_behavior_match_v0.py:80`; `iching_engine_symmetry_match_20260612.md:265-275`). Those are exactly the prior audit's Axis1/Axis2 quotient-preserving rows (`iching_symmetry_match_v0/audit_verdict.md:138-142`). The new packet strengthens that from pointwise preservation to the full descent table: line 5/6 preserve each component; the other flips and complement descend nontrivially; vertical rotation and trigram swap do not descend.

### 4. Controls

Accepted.

Identity descends trivially. The random component relabeling control breaks every named generator in my recomputation, and the packet result also records every generator as non-descending under the seeded random relabeling (`results/...json:211-260`). The coarsened quotient changes the table: it makes several formerly-descending translations fail, while line 5/6 remain pointwise trivial (`results/...json:141-197`). These controls are computed, not just declared.

### 5. Fences And Claim Ceiling

Accepted.

The packet keeps the right boundary: realization-relative only, pinned realization only, no Matrix64-general claim, no 64-behavior iso, no Matrix64 completion, King-Wen comparator-only, no QIT/physics/bridge/axis closure (`results/...json:128-139`, `:3309`; `build_card.md:37-46`). Current checkout status matters: `system_v6/sims/matrix64_behavior_match_v0/` is untracked, so this verdict is for the live working-tree packet audited against committed dependencies, not for an already-committed packet object.

### 6. G.2a

Accepted.

G.2a is wired from birth: the build card requires `scripts/builder_audit_boundary.py` (`build_card.md:48-53`), the validator delegates to `builder_audit_boundary_errors(...)` (`validate_matrix64_behavior_match_v0.py:161-165`), and builder gates report `g2a_boundary_helper_from_birth=true` plus `no_hard_audit_absence_assertion=true` (`results/...json:120-123`). This verdict header declares independent/fresh/read-only audit status, so the boundary helper should remain post-audit idempotent.

## Findings

No blocking findings.

Hardening caveat: add explicit `closure_checks` to the result JSON/validator so the subgroup claim is self-contained. The fresh audit confirmed closure, but the result schema should carry that witness directly.

Status caveat: the packet directory is untracked in this checkout. Do not cite it as committed packet truth until it is intentionally checkpointed.

## Accepted Ceiling

Accepted status label: `passes local rerun` for no-write validator predicates and independent local recomputation, with the packet itself still at working-tree/untracked status in this checkout.

Accepted claim: for the pinned 64-stage realization and the committed 16-component fingerprint quotient, the descending subgroup is exactly the flip-generated `Z_2^6` translation subgroup of size 64 inside the 256-element address group; `vertical_rotation` and `trigram_swap` break all 16 components.

Blocked claims: 64-behavior isomorphism, Matrix64-general symmetry, Matrix64 completion, King-Wen-order correspondence, QIT/physics/bridge/axis admission, formal admission, canonical promotion, or any claim beyond `realization_relative_behavioral_symmetry_table_only`.
