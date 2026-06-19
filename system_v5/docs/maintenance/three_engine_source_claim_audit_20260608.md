# Three-Engine Source-Claim Audit — 2026-06-08

Status: source-level audit. This is stricter than the envelope shape validator and does not promote claims.

## Bottom line

The old validator can pass envelopes whose declared package fields look correct. This audit checks whether the declared Julia/JAX/PyTorch load-bearing packages are actually imported and used in source-token evidence. Source-token evidence is still not mathematical proof, but it catches decorative package claims.

Full JSON: `system_v5/evidence/three_engine_source_claim_audit_20260608.json`

## Counts

- envelopes audited: `0`
- source-backed all lanes: `0`
- source-backed but review needed: `0`
- validator false-positive/source-thin: `0`

### Verdict counts


### Engine class counts

## Review-needed / source-thin examples

## Safe interpretation

- `source_backed_*` means there is source evidence that package-native calls exist. It does not mean admission/canon.
- `validator_false_positive_or_source_thin` means the envelope shape validator was too permissive for rich-tool truth.
- Any current/future consolidation should use this audit or a stricter AST/runtime audit before calling a sim rich-tool-backed.

