from __future__ import annotations

from gcm_ratchet_order_matrix_v1_common import SIM_ID, write_outputs


def main() -> int:
    payload = write_outputs()
    print(
        {
            "sim_id": SIM_ID,
            "classification": payload["classification"],
            "matrix_entries": len(payload["pairwise_matrix"]),
            "forced_edges": payload["measured_order"]["forced_precedence_edges"],
            "substrate_ok": payload["substrate_enforcement"]["positive_payload_ok"]["ok"],
            "v0_regression": payload["v0_regression"]["reproduced"],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
