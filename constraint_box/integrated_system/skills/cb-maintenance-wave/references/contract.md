# Maintenance receipt contract

The runner emits one JSON object with schema `constraintbox.maintenance-receipt.v1`.
The receipt binds:

- explicit repository/package roots;
- declared source and context path manifests and SHA-256 digests;
- diagnostic path states, git status, and supplied ledger/map/hook/provider evidence;
- one exact classification for every candidate;
- blocker/refusal codes;
- `mutation_performed: false` and `writes_allowed: false`;
- a self-hash over the canonical JSON body without `receipt_sha256`.

`READY` means only that the dry-run contract is valid and no blocker/refusal
was found. It does not authorize a later move. `HOLD` is required for a
destructive request, missing required receipt, source/context drift, protected
or owner surface, archive-as-source, cancellation, or invalid input.

The runner is deliberately model-free. A model review may inspect the receipt,
but its prose cannot alter a decision or turn `HOLD` into `READY`.
