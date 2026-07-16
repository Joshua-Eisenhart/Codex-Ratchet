#!/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""PyTorch value leg for the marginal von Neumann entropy candidate family."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import torch


VARIANTS = (
    ("mvn_bits_from_radius", "from_radius", "bits"),
    ("mvn_nats_from_radius", "from_radius", "nats"),
    ("mvn_bits_from_purity", "from_purity", "bits"),
    ("mvn_nats_from_purity", "from_purity", "nats"),
    ("mvn_bits_from_negativity", "from_negativity", "bits"),
    ("mvn_nats_from_negativity", "from_negativity", "nats"),
    ("mvn_bits_from_state", "from_state", "bits"),
    ("mvn_nats_from_state", "from_state", "nats"),
)


def _entropy_from_eigenvalues(eigenvalues: torch.Tensor, log_base: str) -> float:
    eigenvalues = torch.clamp(eigenvalues, min=0.0)
    positive = eigenvalues[eigenvalues > 1.0e-300]
    entropy_nats = -torch.sum(positive * torch.log(positive))
    value = entropy_nats / math.log(2.0) if log_base == "bits" else entropy_nats
    return float(value.item())


def _diagonal_marginal(row: dict[str, object], route: str) -> torch.Tensor:
    if route == "from_radius":
        p = (1.0 + float(row["shell_radius"])) / 2.0
    elif route == "from_purity":
        p = (1.0 + math.sqrt(max(0.0, 2.0 * float(row["purity"]) - 1.0))) / 2.0
    elif route == "from_negativity":
        negativity = float(row["negativity"])
        p = (1.0 + math.sqrt(max(0.0, 1.0 - 4.0 * negativity * negativity))) / 2.0
    else:
        raise ValueError(f"unsupported diagonal route: {route}")
    marginal = torch.tensor([[p, 0.0], [0.0, 1.0 - p]], dtype=torch.float64)
    assert marginal.dtype is torch.float64
    return marginal


def _state_marginal(row: dict[str, object]) -> torch.Tensor:
    a = float(row["a"])
    orientation = float(row["orientation"])
    psi = torch.tensor(
        [math.cos(a), 0.0, 0.0, orientation * math.sin(a)],
        dtype=torch.complex128,
    )
    assert psi.dtype is torch.complex128
    rho_ab = torch.outer(psi, torch.conj(psi))
    rho_ab_4 = rho_ab.reshape(2, 2, 2, 2)
    marginal = torch.einsum("abcb->ac", rho_ab_4)
    assert marginal.dtype is torch.complex128
    return marginal


def _value(row: dict[str, object], route: str, log_base: str) -> float:
    marginal = _state_marginal(row) if route == "from_state" else _diagonal_marginal(row, route)
    eigenvalues = torch.linalg.eigvalsh(marginal)
    assert eigenvalues.dtype is torch.float64
    return _entropy_from_eigenvalues(eigenvalues, log_base)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: torch_leg.py <rows_v1.json> <out.json>")
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    input_bytes = input_path.read_bytes()
    payload = json.loads(input_bytes)
    rows = sorted(payload["rows"], key=lambda row: int(row["row_id"]))
    if len(rows) != 18:
        raise ValueError(f"expected 18 rows, received {len(rows)}")

    output = {
        "schema_version": "l6_phase_entropy_candidate_leg/1.0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "substrate": "torch",
        "version": torch.__version__,
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "variants": [
            {
                "variant_id": variant_id,
                "values": [_value(row, route, log_base) for row in rows],
            }
            for variant_id, route, log_base in VARIANTS
        ],
    }
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
