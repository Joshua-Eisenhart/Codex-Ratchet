from __future__ import annotations

from gcm_ratchet_order_matrix_v0_common import SIM_ID, write_outputs


def main() -> int:
    payload = write_outputs()
    print(
        {
            "sim_id": SIM_ID,
            "classification": payload["classification"],
            "matrix_entries": len(payload["pairwise_matrix"]),
            "forced_edges": payload["measured_order"]["forced_precedence_edges"],
            "substrate_ok": payload["substrate_enforcement"]["positive_payload_ok"]["ok"],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
