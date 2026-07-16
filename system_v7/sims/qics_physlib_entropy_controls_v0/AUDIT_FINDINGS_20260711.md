# Fresh-context audit — qics_physlib_entropy_controls_v0 (2026-07-11)

Verdict: FINDINGS (one moderate), concrete artifacts authentic.

FINDING: TOOL_INTEGRATION_DEPTH claimed qics=load_bearing, but the auditor's stub test (SDP call replaced by the
spectral value with fake-consistent metadata) left the full 17-test verdict unchanged — the acceptance rule gates on
AGREEMENT between QICS and the spectral comparator, so QICS is a supportive independent cross-check, not the decisive
gate. Label demoted in qics_battery.py per the audit prescription (new versioned result generated post-edit).
Mitigation noted by the auditor: the committed results carry genuine SDP telemetry (nonzero residuals 7.3e-14/5.5e-12,
8-9 iterations) — the runs are real; the finding is a design/labeling overclaim only.

Survived attack: min DPI margin -1.9e-10 = legitimate pass-by-slack (1e-9); false-variant abort-before-write genuinely
fires (identity-variant patch → RuntimeError before any file write); determinism byte-identical; Physlib scope honest.

Open item (design): to EARN load_bearing, restructure acceptance so a genuinely diverging QICS value (not mere
agreement) is required to flip a verdict — e.g. gate a case class where the spectral comparator is known-insufficient.
