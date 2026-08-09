# ClaimGate legacy-root status

This `claimgate/` directory is a small historical Python validator. It is not
the v9 ClaimGate source authority.

The canonical product is `claimgate_plugin/`, versioned independently by
`claimgate_plugin/VERSION`. Existing references to this directory remain valid
as historical provenance only. New bridge records, tests, and release manifests
must point to `claimgate_plugin/`.

The copy formerly shipped inside imported ConstraintBox packs is not tracked as
a second implementation. ConstraintBox reaches the canonical product through
the `cb-to-claimgate` bridge.
