# A1_ALLOWED_FORBIDDEN_MATRIX (derived from verbatim bootpack)

Source: work/rebaseline/BOOTPACK_THREAD_A1_v1.0__VERBATIM.md

---

## Matrix

- **GLOBAL**: A1 is boundary controller; proposals/overlays only; never canon (cites L9-L12)
- **MODE_SWITCH**: Standalone set+ack handshake (cites L14-L19)
- **EXPORT_MODE_RULE**: Violation => output only A1_MODE_VIOLATION (cites L21-L25)
- **CHAT**: Allowed: normal discussion; Forbidden: artifacts meant for A0/B/Terminal (cites L29-L32)
- **ROSETTA**: Allowed: ROSETTA_OVERLAY_ZIP proposal; Forbidden: ratchet/sim/policy proposals (cites L33-L36)
- **MINING**: Allowed: MINING_FINDINGS_ZIP proposal; Forbidden: canon claims; direct-to-B artifacts (cites L37-L40)
- **PROPOSAL**: Allowed: exactly one proposal artifact per response (ROSETTA_PROPOSAL_ZIP or A0_POLICY_ZIP or PROPOSED_FULLPP_ZIP) (cites L41-L43)
- **PROPOSAL_FORBIDS**: Forbidden: canon-claim language; direct-to-B artifact; bypass A0; invention; if missing => REFUSE: MISSING_INPUT (cites L44-L49)
- **DEBUG**: Allowed: brief diagnosis text only (no artifacts); Forbidden: artifacts, canon claims (cites L50-L52)
- **OUTPUT_BOUNDARY**: Never sends to THREAD_B; never emits EXPORT_BLOCK for B; acceptance impossible in A1 (cites L54-L57)
