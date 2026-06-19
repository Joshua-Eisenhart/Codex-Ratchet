# Red State Note - ring_checkerboard_automaton_v0

Date: 2026-06-12

This packet is not marked superseded here. The current doctrine still cites
`ring_checkerboard_automaton_v0` as the earned classical floor, and
`ring_checkerboard_qca_v3` imports/recomputes the v0 support rather than
replacing the classical-floor packet.

The current packet-local validator red state is expected-historical for the
checked-in result envelope:

- `all_pass=false`
- `no_builder_audit_verdict=false`
- `builder_gates.no_builder_audit_verdict=false`
- `builder_gates.no_builder_audit_verdict_envelope_gate=false`

Diagnosis: the red rows are a builder/audit boundary contract gap in the stored
envelope, not a new mathematical failure of the independent audit verdict. The
independent audit verdict remains the authority for the packet's scratch ceiling
and caveats. Do not green-wash the envelope by changing result values without a
fresh, explicit rebuild/re-adjudication lane.

Successor context: `ring_checkerboard_qca_v3` is the later QCA/open-chain
fixture lane. It supersedes weaker QCA/index attempts, not this packet's
classical-floor role.

