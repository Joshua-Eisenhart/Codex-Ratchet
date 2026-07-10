#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKET_ROOT="/Users/joshuaeisenhart/.local/share/codex-ratchet/intake/107-20260709"
PACKET_ZIP="/Users/joshuaeisenhart/Desktop/107.zip"

python3 "$HERE/audit_up135_up136.py" \
  --packet-root "$PACKET_ROOT" \
  --packet-zip "$PACKET_ZIP" \
  --output "$HERE/up135_up136_kill_audit_results.json"
python3 "$HERE/validate_packet_107_audit.py" \
  "$HERE/up135_up136_kill_audit_results.json" \
  --self-test
python3 "$HERE/validate_packet_107_audit.py" \
  "$HERE/up135_up136_kill_audit_results.json" \
  --packet-root "$PACKET_ROOT" \
  --packet-zip "$PACKET_ZIP"
python3 "$HERE/audit_up135_up136.py" \
  --packet-root "$PACKET_ROOT" \
  --packet-zip "$PACKET_ZIP" \
  --output "$HERE/up135_up136_kill_audit_rerun_results.json"
python3 "$HERE/validate_packet_107_audit.py" \
  "$HERE/up135_up136_kill_audit_rerun_results.json" \
  --compare "$HERE/up135_up136_kill_audit_results.json" \
  --packet-root "$PACKET_ROOT" \
  --packet-zip "$PACKET_ZIP"
shasum -a 256 \
  "$HERE/up135_up136_kill_audit_results.json" \
  "$HERE/up135_up136_kill_audit_rerun_results.json"
