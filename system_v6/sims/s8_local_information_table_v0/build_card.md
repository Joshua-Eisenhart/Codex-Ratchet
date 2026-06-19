# BUILD CARD - s8_local_information_table_v0 (the missing S8-local S(A|B)/I(A:B)/I_c table)

You are codex1 (builder, high). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside system_v6/sims/s8_local_information_table_v0/ (file-disjoint). NO git add/commit. Copy this card into build_card.md. FILE BOUNDARY: no audit_verdict.md; set the no_builder_audit_verdict gate.

## Authority + the gap
The S8 adjudication (find the S8 layer's committed packet + verdict via git log/grep - the round-2/round-3 S8 or nested-ratchet surface; the noted gap per the 2026-06-11 review: 'S8-local S(A|B), I(A:B), and I_c table is still missing'). The committed values that DO exist: the nested-ratchet S(A|B) trajectory (0 -> -0.362073 -> -0.678632, nested_ratchet_support/nr_fresh_audit_verdict.md) and the dual-stack I_c (Phi0_Ic_S_to_M = 0.4164955306996874). The entropy-type co-ratchet discipline (60376bd9f) binds: every row's enabling structure constructed before evaluation.

## The object
ON the committed S8-layer object (whatever the S8 packet's pinned carrier/state family is - quote it), compute the LOCAL typed-information table: S(A|B) per declared bipartition, I(A:B), and I_c per declared channel - each w/ its enabling structure constructed (the bipartition object, the channel object) per the v1 discovery standard; exact/certified values typed per the ledger; cross-checked against the two committed values above where the objects coincide (weld-anchor style: if the S8-local computation reproduces the nested-ratchet S(A|B) values on the matching states, that is the continuity anchor; divergence = a finding).

## Controls: separable-state control (S(A|B) >= 0, I_c at its classical bound - computed); the entangled positive case (negativity computed); premature-evaluation structural failures; erased-channel I_c flip; typed-confusion rejection.

## Engineering contract
Honest TOOL_INTENT_MATRIX (Julia QuantumOptics reference + package_observables; JAX; PyTorch honest); SMT binds computed values w/ real flips; envelope via scripts/build_three_engine_envelope.py; validators (honest combo) + packet validator + pytest; classification scratch_diagnostic, promotion_allowed=false. End with the S8-local table + the continuity anchors + every validator command + status.
