from __future__ import annotations

import json
from pathlib import Path

from constraintbox.process_box import run_in_box
from constraintbox_zip_agent.live_failure_council import build_live_failure_council_packet
from constraintbox_zip_agent.protocol import sha256_bytes

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet/constraint_box")
OUT = Path("/private/tmp/cb-live-failure-20260815")
OWNER = (
    b"Target: packet Python still has host-wide file-read*. "
    b"Do not promote. Internal ZIP is not superior.\n"
)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    packet = build_live_failure_council_packet(owner_prompt=OWNER, run_id="live-failure-20260815")
    packet_path = OUT / "failure.live.zip"
    return_path = OUT / "failure.live.return.zip"
    packet_path.write_bytes(packet)
    (OUT / "packet.sha256").write_text(sha256_bytes(packet) + "\n")
    py = ROOT / ".venv" / "bin" / "python"
    receipt = run_in_box(
        [
            str(py),
            "-m",
            "constraintbox_zip_agent",
            "run",
            str(packet_path),
            "--return-zip",
            str(return_path),
        ],
        use_seatbelt=False,
        timeout=600,
    )
    (OUT / "box_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(
        {
            "packet": str(packet_path),
            "packet_sha256": sha256_bytes(packet),
            "return_exists": return_path.is_file(),
            "box_status": receipt.get("status"),
            "box_returncode": receipt.get("returncode"),
            "seatbelt_used": receipt.get("seatbelt_used"),
            "provider_env_relayed": receipt.get("provider_env_relayed"),
            "box_run_id": receipt.get("run_id"),
        },
        indent=2,
    ))
    return 0 if receipt.get("status") == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
