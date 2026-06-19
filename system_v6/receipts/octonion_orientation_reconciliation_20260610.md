# Octonion Orientation Reconciliation 2026-06-10

Outcome: PASS as receipt-only reconciliation. No carrier, nonassoc, bridge, axis, or formal-admission claim is promoted.

Compared surfaces:

- Bloch root convention map: `system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json`
- MCT weld basis lift: `system_v6/sims/mct_nonassoc_weld_packet_v0/results/mct_nonassoc_weld_packet_v0_envelope_results.json`

Bloch root old-to-new map:

- `octonion_permutation_old_to_new=[0,3,2,1,6,7,4,5]`
- `octonion_signs_old_to_new=[1,-1,1,1,-1,-1,1,-1]`
- lift rule: apply the same octonion relabel/sign map to both Cayley-Dickson halves before doubling.
- receipt role: translates the blind-sheet sedenion witness into the Bloch packet's explicit convention.

MCT weld committed basis lift:

- `perm=[0,1,2,3,4,7,6,5]`
- `signs=[1,1,1,1,1,-1,1,-1]`
- bracket convention: `left`
- receipt role: packet-local classifier/lift convention after reading the exported canon `C[k][i][j]` table.

Reconciliation:

- The two maps are distinct and intentionally packet-local.
- No cross-packet reuse is allowed without carrying the map name and lift rule.
- A consumer that uses Bloch root witness terms against MCT weld rows must explicitly choose and apply one map before comparing products.
- This receipt closes the estate-level "unmapped octonion orientation reuse" gap only as a map-of-maps ledger.

