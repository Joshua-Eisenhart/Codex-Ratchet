# Ratchet Process v1

Status: executable process proposal. Not Ratchet canon.

This directory turns the foundation-first Ratchet doctrine into a closed,
machine-checkable intake surface. It does not admit any mathematical layer.

Read in this order:

1. `RATCHET_SPEC.md` - formal process and claim boundary.
2. `ratchet_card.schema.json` - closed card shape.
3. `examples/coratchet_recursive_foundations_v1.card.json` - proposal-only
   example for the missing recursive core.
4. `CURRENT_EVIDENCE_CEILING.md` - current blocked/earned boundary.
5. `INDEPENDENT_PROCESS_AUDIT_20260710.md` - advisory adversarial review and
   repaired bypasses.
6. `SOURCE_MANIFEST.json` - provenance, including external packet 122.

Run:

```bash
python3 system_v7/control/ratchet_process_v1/validate_ratchet_card.py \
  system_v7/control/ratchet_process_v1/examples/coratchet_recursive_foundations_v1.card.json

python3 -m unittest discover \
  -s system_v7/control/ratchet_process_v1/tests -v
```

A green validator means only that the proposal is structurally honest. It is
not evidence that the proposed Ratchet ran.
