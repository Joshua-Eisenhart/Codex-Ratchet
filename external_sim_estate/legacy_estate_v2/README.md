# Legacy full simulation estate

This directory is outside ConstraintBox.

It preserves the older S1-S4 manifest, workers, and neutral fixture so they can
still be audited and maintained. The full estate is not the ConstraintBox
kernel, its tier labels are not ConstraintBox authority levels, and its
receipts do not become release authority merely by saying `READY`.

ConstraintBox may call these workers through its narrow broker. Current
function-level work should prefer `../basic_packet_v1/`.

Status: local candidate/provenance material; no engine-readiness, CR,
scientific, canonical, or promotion claim.
