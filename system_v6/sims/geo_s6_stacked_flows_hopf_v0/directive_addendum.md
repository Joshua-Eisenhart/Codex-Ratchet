# S6 builder directive addendum

This packet follows the S6 builder-lane request and `system_v6/receipts/s6_build_spec_20260610.md`.

Binding directives:
- Build genuinely new S6 receipts only.
- Use packet id/path `geo_s6_stacked_flows_hopf_v0` as requested by the user, even though the prep spec suggested `geo_s6_stacked_terrain_operator_hopf_v0`.
- Cite S2, S4, S5 v2, Matrix64, and the placement source tables; do not rebuild them.
- Use S5 v2 exported `A,b` rows as the source of terrain leakage.
- Use S2's convention pin for every `A/F/h` or holonomy comparison.
- Treat shell leakage `dz/dt` and its loop/shell integrals as the S6 restricted-mode flux layer.
- Keep projected density-shell behavior separate from pure Hopf-torus preservation.
- Every map names its arrow type and carrier before admission.
- Matrix64 is reused evidence for 64 cells and `Delta_T,O`; it is not S6 leakage evidence.
- `Phi_D` and `Phi_I` are executed as maps on one shared carrier with computed `g_DI`.
- Round-trip gates, consistency gates, executed mutations, and cross-engine fatality from S4/S5 v2 are mandatory.
- Every result includes `classification`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, source lineage, exactness labels, can-fail controls, and claim ceiling.
- If lower receipts and S6 computations disagree, preserve the divergence and mark the packet blocked pending audit.

No separate external `/tmp` S6 directive file was present at build time. This addendum records the user directive and the spec's directive rules as the copied-in directive surface for this packet.
