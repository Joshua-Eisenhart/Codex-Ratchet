# Builder Self-Assessment - ecd02_chiral_information_routing_v1

This is a builder self-assessment, not an audit verdict.

## What Changed From v0

- The packet computes source/readout joint distributions from realized QCA v3 unitaries.
- Mutual-information rows are computed from `P(source_bit, readout_bit)`.
- Directional current is computed as the center of source mutual information over output labels minus the source input label.
- The strongest Szilard baseline is searched over same-alphabet deterministic endpoint policies rather than fixed to `index0`.

## Builder Verdict Boundary

The build records `ECD.02 DIES` because the strongest same-alphabet classical endpoint policy matches or exceeds the QIT directed-current witness. That is a packet result, not an independent audit verdict.

## Known Limits

- The QIT row still uses the QCA v3 open-chain realized-unitary fixture and inherits its open-chain boundary.
- The fair baseline search is intentionally strong; it admits classical endpoint-copy policies with the same alphabet and one-step budget.
- No finite-ring GNVW, all-cells QCA, physics chirality, or QIT-engine admission is claimed.
