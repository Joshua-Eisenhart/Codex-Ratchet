# Independent audit verdict -- eng64_stage_fingerprint_ids_v0

Auditor: independent fresh Codex audit. I did not build this packet. I recomputed the key rows from committed source/result data before accepting the packet prose.

## Verdict

VERDICT: PASS / SUSTAINED, under the packet's ceiling only.

Claim ceiling: `scratch_diagnostic`; bounded to `downstream_plumbing_only`. This verdict does not promote `eng_64`, does not claim Matrix64 behavior, does not claim 64-behavior isomorphism, and does not admit QIT/physics claims.

Citation rule: cite this packet only as a label-free stable fingerprint/component-ID plumbing receipt for the committed `eng_64` estate. Any consumer citation must carry the ceiling above and must not use this verdict as evidence for `eng_64` promotion or Matrix64 behavior.

## Fresh Recompute

I imported `eng64_stage_fingerprint_ids_v0.py` and ran `build()` in memory, without running the writer entrypoint. I compared the fresh selected payload fields against `results/eng64_stage_fingerprint_ids_v0_results.json`.

Fresh recomputation returned:

- 64 stage rows.
- 16 distinct fresh fingerprints.
- component size histogram `{4: 16}`.
- committed `eng_64` `fingerprint_counts.n_distinct = 16`.
- label permutation changed 64 labels and left fingerprint IDs unchanged.
- same-component independent recompute checked 16 component pairs, all equal.
- fresh fingerprint components matched the committed collapse-graph components.
- selected committed fields matched fresh recomputation: `summary`, `components`, `controls`, `fingerprint_definition`, `claim_boundary`, `TOOL_MANIFEST`, and `TOOL_INTEGRATION_DEPTH`.

## Label-Freeness

The fingerprint inputs are the axes, `rho_out`, and rounded eight-float vector. The excluded fields are `source_stage_label`, engine label text, direction label text, and collapse pair text. I found no slot-label or label-text input in the fingerprint hash path.

## Estate Untouched

`git status --short -- system_v5/julia_carrier/eng_64_hexagram_julia_results.json system_v5/julia_carrier/eng_64_hexagram_julia.jl` returned no rows. The committed `eng_64` source/result estate was not modified by this audit.

## G.2a State

G.2a state: pre-G.2a / partial boundary. The packet uses `builder_audit_boundary` and the builder did not emit this audit verdict, but the packet does not declare the later explicit `G.2a from birth` / `no_builder_audit_verdict=true` contract used by newer packets. Violation noted here; not repaired by this audit.

## Bottom Line

The claims audited here survive: label-free fingerprints recover 16 components, match the independently inferred `n_distinct=16`, preserve label-permutation invariance, match collapse-graph parity, and leave the `eng_64` estate untouched.
