from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .maintenance import TrustedReceiptSet, bind_trusted_receipts


DEFAULT_DENSITY_FIELDS = (
    "trace",
    "eigenvalues",
    "rank",
    "hartley_bits",
    "von_neumann_bits",
    "dephased_entropy_bits",
)
PARITY_CLAIM_CEILING = (
    "bound receipt values were compared for numerical consistency only; "
    "parity does not prove execution, operation use, engine independence, "
    "engine readiness, scientific truth, or promotion"
)


def _close(left: Any, right: Any, tolerance: float) -> bool:
    if isinstance(left, list):
        return (
            isinstance(right, list)
            and len(left) == len(right)
            and all(
                _close(a, b, tolerance)
                for a, b in zip(left, right, strict=True)
            )
        )
    if isinstance(left, (int, float)) and not isinstance(left, bool):
        return (
            isinstance(right, (int, float))
            and not isinstance(right, bool)
            and math.isfinite(float(left))
            and math.isfinite(float(right))
            and abs(float(left) - float(right)) <= tolerance
        )
    return left == right


def _result(
    *,
    state: str,
    tolerance: float,
    sources: list[str],
    families_present: dict[str, bool],
    comparisons: list[dict[str, Any]],
    receipt_sha256: dict[str, str],
    trust_binding: dict[str, Any],
    problems: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "schema": "constraintbox.cross-estate-parity.v2",
        "state": state,
        "consistency_only": True,
        "tolerance": tolerance,
        "sources": sources,
        "families_present": families_present,
        "comparisons": comparisons,
        "receipt_sha256": receipt_sha256,
        "trust_binding": trust_binding,
        "problems": problems,
        "execution_verified": False,
        "engine_readiness_verified": False,
        "claim_ceiling": PARITY_CLAIM_CEILING,
        "promotion_allowed": False,
    }


def compare_density_receipts(
    receipt_paths: list[Path],
    tolerance: float = 1e-8,
    *,
    trusted_receipts: TrustedReceiptSet | None = None,
) -> dict[str, Any]:
    """Compare controller-bound values without issuing a readiness verdict."""
    if (
        isinstance(tolerance, bool)
        or not isinstance(tolerance, (int, float))
        or not math.isfinite(float(tolerance))
        or tolerance <= 0
    ):
        raise ValueError("tolerance must be a positive finite number")

    validated, trust_problems, trust_binding = bind_trusted_receipts(
        receipt_paths, trusted_receipts
    )
    empty_families = {
        "numpy": False,
        "jax": False,
        "quimb": False,
        "torch": False,
    }
    if trust_problems:
        return _result(
            state="PARKED",
            tolerance=float(tolerance),
            sources=[],
            families_present=empty_families,
            comparisons=[],
            receipt_sha256={},
            trust_binding=trust_binding,
            problems=trust_problems,
        )

    sources: dict[str, dict[str, Any]] = {}
    digests: dict[str, str] = {}
    parity_problems: list[dict[str, str]] = []
    for path, receipt, receipt_sha256 in validated:
        digests[str(path)] = receipt_sha256
        for row in receipt["capabilities"]:
            capability_id = row["capability_id"]
            if capability_id not in {
                "numpy_density",
                "jax_density",
                "quimb_tensor",
                "torch_density",
                "jax_cuda_parity",
                "torch_cuda_parity",
            } or row["state"] != "READY":
                continue
            observed = row["evidence"].get("observed")
            if not isinstance(observed, dict):
                parity_problems.append(
                    {
                        "path": str(path),
                        "reason": f"parity_observed_values_missing:{capability_id}",
                    }
                )
                continue
            if capability_id in sources:
                parity_problems.append(
                    {
                        "path": str(path),
                        "reason": f"duplicate_parity_source:{capability_id}",
                    }
                )
                continue
            sources[capability_id] = observed

    ordered = sorted(sources)
    comparisons: list[dict[str, Any]] = []
    for index, left_id in enumerate(ordered):
        for right_id in ordered[index + 1 :]:
            left = sources[left_id]
            right = sources[right_id]
            field_results = {
                field: (
                    field in left
                    and field in right
                    and _close(left[field], right[field], float(tolerance))
                )
                for field in DEFAULT_DENSITY_FIELDS
            }
            comparisons.append(
                {
                    "left": left_id,
                    "right": right_id,
                    "fields": field_results,
                    "consistent": all(field_results.values()),
                }
            )

    families_present = {
        "numpy": any(item.startswith("numpy") for item in sources),
        "jax": any(item.startswith("jax") for item in sources),
        "quimb": "quimb_tensor" in sources,
        "torch": any(item.startswith("torch") for item in sources),
    }
    family_count = sum(families_present.values())
    if parity_problems:
        state = "PARKED"
    elif family_count < 2 or not comparisons:
        state = "INSUFFICIENT"
    elif all(row["consistent"] for row in comparisons):
        state = "CONSISTENT"
    else:
        state = "INCONSISTENT"
    return _result(
        state=state,
        tolerance=float(tolerance),
        sources=ordered,
        families_present=families_present,
        comparisons=comparisons,
        receipt_sha256=digests,
        trust_binding=trust_binding,
        problems=parity_problems,
    )
