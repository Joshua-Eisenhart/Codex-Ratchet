# Foundation-chain binding audit

This lane preserves the fresh v0.2 audit of the attempted shared-candidate
foundation -> basin -> MSS chain. It is a scratch integrity/provenance
diagnostic, not a scientific simulation receipt.

The run intentionally stops at the first red gate:

```text
all_pass = false
break_stage = trust_manifest
scientific_status = blocked_unbound_or_unauthenticated
promotion_allowed = false
```

Only `basin_execution` passes. The trust manifest, root candidate extraction,
F01/N01 constraint bindings, producer identities, authority pins, root-to-basin
binding, MSS execution, and basin-to-MSS binding remain red. Consequently the
paired-engine E2E path, full Ratchet E2E path, scientific manifold admission,
and Lev promotion remain blocked.

The receipt retains hashes of the three scratch inputs and the exact command,
but those `/tmp` input files are not promoted or copied here. Its ceiling is
integrity/provenance evidence only.

Receipt:
`results/foundation_chain_binding_audit_v02_final.json`
