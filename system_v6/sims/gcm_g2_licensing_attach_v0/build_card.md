# gcm_g2_licensing_attach_v0 Build Card

Scope: layer 22 (the G2 compatibility layer) | integrated | 3Q.

Ceiling: `scratch_diagnostic`, `carrier-and-pins-relative`, `promotion_allowed=false`, `formal_admission_allowed=false`.

This packet consumes the 3Q v1 state-artifacted survivor result and the committed compact octonion structure constants. It does not rebuild the S10 G2 estate. It consumes S10 feedstock by path/hash and keeps compact-vs-split as a branch row only.

Licensing target from the nesting law at `afe7aa57b`: an explicit 7D real readout space `W_A` in the 3Q traceless Pauli span, with pinned 3-form `e123+e145+e167+e246-e257-e347-e356`, plus tests for 3-form preservation, cross-product closure, associator visibility/erasure, and compact-vs-split branch behavior.

Pinned convention:

- `W_A = span{XII, ZII, IXI, IZI, IIX, IIZ, XXX}`.
- This is a pinned convention only. No natural `W_A` from owner/canon sources is claimed.
- The ambient carrier is the 63 traceless Pauli strings at 3Q.

Controls:

- scrambled-phi: replace `e167` with `e137`; the preserving signed map must fail it.
- random 7-subspace: deterministic random-looking Pauli labels must underperform pinned `W_A`.
- quotient-erasure: associator witness rows are visible before quotient and erased to class-id-only rows under the density quotient.
- substrate negative: lineage-free payload must fail the hardened `gcm_substrate_check`.

G.2a boundary:

- Builder emits result/envelope/validator artifacts only.
- Builder does not write `audit_verdict.md`.
- Any later audit verdict must be independent/fresh.

NO git add/commit.
