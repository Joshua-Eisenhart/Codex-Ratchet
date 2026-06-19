# Builder Self-Assessment - ecd03_typed_coratchet_v0

Built a file-disjoint ECD.03 v0 discriminator in `system_v6/sims/ecd03_typed_coratchet_v0/`.

Status: builder-side `scratch_diagnostic`, not an audit verdict.

## What Was Built

- Two-sided searched reachability packet for typed-operation availability trajectories.
- Equal-information shared type-ladder environment hash used by both QIT and baseline sides.
- Symmetric set difference reports QIT-only and baseline-only trajectories.
- Void-carrier gate refuses rows where the ladder unlocks nothing.
- Controls for N01-style permutation, order-blind collapse, dropped-half sensitivity, and label-free fingerprints.
- Local envelope with `three_engine_mode: not_scoped_for_this_packet`.

## Boundary

G.2a is wired from birth through `scripts/builder_audit_boundary.py`. The validator and tests delegate audit-file idempotency through the shared helper and intentionally reject a builder-authored `audit_verdict.md`.

## Ceiling

The packet does not claim engine admission, a formal theorem, a universal entropy scalar, or discovery free of in-packet semantics. Either computed survival, death, or tie remains v0 scratch evidence only.
