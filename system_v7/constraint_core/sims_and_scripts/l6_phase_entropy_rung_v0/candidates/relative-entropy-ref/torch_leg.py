#!/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""Torch f64 value leg for declared-reference quantum relative entropy."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import torch


def _load(path: Path) -> tuple[dict[str, object], str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _row_density(row: dict[str, object]) -> torch.Tensor:
    angle = float(row["a"])
    orientation = float(row["orientation"])
    psi = torch.tensor(
        [math.cos(angle), orientation * math.sin(angle)], dtype=torch.complex128
    )
    return torch.outer(psi, torch.conj(psi))


def _reference_density(reference: dict[str, object]) -> torch.Tensor:
    x, y, z = (float(value) for value in reference["reference_bloch_vector"])
    return torch.tensor(
        [
            [(1.0 + z) / 2.0, complex(x, -y) / 2.0],
            [complex(x, y) / 2.0, (1.0 - z) / 2.0],
        ],
        dtype=torch.complex128,
    )


def _relative_entropy_nats(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    rho_eigenvalues = torch.linalg.eigvalsh(rho)
    assert rho_eigenvalues.dtype is torch.float64
    positive = rho_eigenvalues[rho_eigenvalues > 1.0e-300]
    rho_log_rho = torch.sum(positive * torch.log(positive))

    sigma_eigenvalues, sigma_eigenvectors = torch.linalg.eigh(sigma)
    log_sigma = (sigma_eigenvectors * torch.log(sigma_eigenvalues).unsqueeze(0)) @ torch.conj(
        sigma_eigenvectors.T
    )
    rho_log_sigma = torch.real(torch.trace(rho @ log_sigma))
    return float((rho_log_rho - rho_log_sigma).item())


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: torch_leg.py <rows_v1.json> <references_v1.json> <out.json>")

    rows_payload, rows_sha256 = _load(Path(sys.argv[1]))
    references_payload, references_sha256 = _load(Path(sys.argv[2]))
    rows = sorted(rows_payload["rows"], key=lambda row: int(row["row_id"]))
    references = references_payload["references"]
    if len(rows) != 18:
        raise ValueError(f"expected 18 rows, received {len(rows)}")
    if len(references) != 11:
        raise ValueError(f"expected 11 references, received {len(references)}")

    row_densities = [_row_density(row) for row in rows]
    variants = []
    for reference in references:
        sigma = _reference_density(reference)
        assert sigma.dtype is torch.complex128
        variants.append(
            {
                "variant_id": reference["variant_id"],
                "values": [_relative_entropy_nats(rho, sigma) for rho in row_densities],
            }
        )

    output = {
        "schema_version": "l6_phase_entropy_candidate_leg/1.0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "substrate": "torch",
        "version": torch.__version__,
        "dtype": "float64/complex128",
        "rows_input_sha256": rows_sha256,
        "references_input_sha256": references_sha256,
        "variants": variants,
    }
    Path(sys.argv[3]).write_text(
        json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
