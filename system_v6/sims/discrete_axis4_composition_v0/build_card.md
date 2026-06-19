# BUILD CARD - discrete_axis4_composition_v0

You are codex2 (xhigh). Repo: `/Users/joshuaeisenhart/Codex-Ratchet`.

Build in `system_v6/sims/discrete_axis4_composition_v0/` only. File-disjoint packet. No `git add`; no commit.

Ceiling: `axis_readout_candidate_only`.

Authority:

- Work order `f6112e407`, Axis-4 row: `Phi_D = exp(tau_R L_R) exp(tau_C L_C)` versus `Phi_I = exp(tau_C L_C) exp(tau_R L_R)`.
- Witness: `W_4 = ||Phi_D(rho)-Phi_I(rho)||_1`.
- Commutator leading order must be checked separately from the finite readout.
- Axis 4 must never be merged with Axis 6. This packet must include the 4-vs-6 distinction discriminator.
- Committed Axis-4 prior art is context only: executed `Phi_D/Phi_I` trajectories differ and commuting controls collapse in the S6 loop-order and dual-stack packets. This packet must not reuse their different carrier/pins as the primary readout.
- Panel 7 q3 `1f8ddb9e1`: commuting implies `D=I`; small-stroke `D=UEUE`, `I=EUEU` leading order is `2ue[A,B]`.
- Carrier: the 33-cell Family A carrier shared with Axis 0 and Axis 6.
- Extend the carrier-honest independence matrix: 0/4 and 6/4 pairs, with the no-identity-leak standard from `b6fafc67f`.

Pins:

- `L_R`: committed S4 `R_x` generator. `tau_R = 1`.
- `L_C`: committed S4 `D_z` generator. `tau_C = 1`.
- `exp(tau_R L_R)` must reproduce committed `R_x`.
- `exp(tau_C L_C)` must reproduce committed `D_z`.
- `D_z` contraction is `lambda = 7/10`.

Pinned polarity:

- Compute per-cell `Delta_4 = Phi_D(rho_cell)-Phi_I(rho_cell)`.
- `W_4 = ||Delta_4||_1`; for qubit Bloch differences this is `||Delta r||_2`.
- Polarity is the first nonzero sign of `(Delta_y, Delta_z, Delta_x)`, with neutral when `W_4 <= 1e-10`.

Controls:

- Commuting pair: all cells neutral.
- Leading-order magnitude: small-stroke `D=UEUE`, `I=EUEU` matches panel form `2ue[A,B]`.
- Shuffled order: a non-primary order word must not reproduce the primary sign vector.
- Axis-4-vs-Axis-6 discriminator: the committed Axis-6 readout on the same 33 cells must not predict the Axis-4 readout.

Standard contract:

- Three-engine lanes: Julia, JAX/Python, PyTorch.
- Use `scripts/build_three_engine_envelope.py`.
- Use `scripts/builder_audit_boundary.py` fully. Builder emits no `audit_verdict.md`.
- `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Result must name allowed and disallowed claims explicitly.
