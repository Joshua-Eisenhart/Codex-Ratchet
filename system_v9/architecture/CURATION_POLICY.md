# Curation policy

V9 does not copy the Desktop into Git.

1. Inventory candidate source packs by path, size, modification time, and
   SHA-256.
2. Deduplicate byte-identical files and superseded archive generations.
3. Extract only distinct specifications, executable sources, controls,
   receipts, and unresolved findings that change the current product state.
4. Keep the original path and digest in an intake record.
5. Mark conversation synthesis and model-generated proposals as non-canonical
   until reconciled with source or a run.
6. Do not import caches, build output, local environments, repeated result
   estates, or rejected ClaimGate receipts as current evidence.
7. Put research concepts in the wiki with provenance and status. Put runnable
   product contracts and code in this repository.
