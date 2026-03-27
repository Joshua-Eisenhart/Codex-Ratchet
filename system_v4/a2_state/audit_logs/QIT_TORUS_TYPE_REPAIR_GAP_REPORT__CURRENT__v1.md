# QIT Torus/Type Repair Gap Report

- status: `bounded_non_promotional_gap_summary`
- generated_utc: `2026-03-27T00:20:13Z`

## Report Surface
- surface_class: `tracked_current_workspace_report`
- represents: `current workspace torus/type repair-gap state at generation time; may differ from the last committed snapshot until tracked CURRENT artifacts are committed`
- git_sha: `7391077305b05a3e82e5cf38aaf7b42e236f41b3`

## Audit Boundary
- audit_only: `True`
- nonoperative: `True`
- do_not_promote: `True`
- promotion_claim: `none`

## Torus Placement
- supported_now:
  - owner graph has 3 torus carrier nodes
  - owner graph has 2 torus-nesting edges
  - owner graph has 32 STAGE_ON_TORUS edges
  - owner graph supports stage-to-torus carrier assignment counts
- aligned_only:
  - runtime samples align to the same owner engine/stage ids
  - sidecar carrier summaries are hash-aligned to the current owner snapshot
- missing:
  - no direct runtime bridge packet for torus-placement witnesses
  - no promoted torus 2-cells in owner graph
  - no runtime state graph proving torus occupancy over time
- forbidden_to_infer:
  - validated Hopf geometry
  - promoted torus topology semantics
  - runtime proof that torus placement is physically realized
  - promotion-ready torus evidence

## Type Split
- supported_now:
  - owner graph has 2 engine-family nodes
  - owner graph has 1 CHIRALITY_COUPLING edge
  - owner graph has stage ownership split by engine family
  - negative witnesses exist for no-chirality and type-flatten
- aligned_only:
  - runtime bridge resolves type-split alignment to owner engine ids
  - runtime bridge maps neg_type_flatten to the current engine-family ids
  - sidecar readiness says engine-pair-only, not branch-level
- missing:
  - no live WEYL_BRANCH owner nodes
  - no promoted chirality algebra payload in owner truth
  - no runtime/history graph proving branch-level type semantics
- forbidden_to_infer:
  - live Weyl branch semantics
  - promoted chirality truth beyond engine-family split
  - validated clifford/pseudoscalar proof in owner truth
  - promotion-ready type-split evidence

## Minimal Next Repairs
- torus_placement:
  - add a bounded runtime-side torus join table keyed by existing stage ids
  - preserve torus-targeted negatives as explicit bounded context until a faithful owner concept exists
  - avoid promoting torus 2-cells before round-trip owner representation exists
- type_split:
  - keep type split anchored at the two engine owner ids
  - avoid live WEYL_BRANCH owner nodes until a faithful owner anchor exists
  - treat chirality algebra as candidate sidecar evidence only until promotion gates are satisfied
