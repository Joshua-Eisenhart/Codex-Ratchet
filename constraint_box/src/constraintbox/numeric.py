from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import Disposition, ProfileOutcome
from .intake import IntakeError, parse_json_object


@dataclass(frozen=True)
class NumpyAggregateProfile:
    operation: str
    profile_id: str = "constraintbox.numeric.numpy.aggregate.v1"
    claim_ceiling: str = "one bounded aggregate was independently recomputed"
    tolerance: float = 1e-12

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome:
        del run_dir
        try:
            body = parse_json_object(payload)
        except IntakeError as exc:
            return ProfileOutcome(
                Disposition.BLOCKED, "strict_intake_failed", {"error": str(exc)}
            )
        if set(body) != {"values", "claimed_value"}:
            return ProfileOutcome(
                Disposition.BLOCKED, "numeric_contract_keys_mismatch"
            )
        values = body["values"]
        claimed = body["claimed_value"]
        # bool is a subclass of int, so a bare isinstance check admits JSON
        # true/false as numbers and reports [true, true] as summing to 2. This
        # profile means real-number input; booleans are a category error, not a
        # value of 1.
        def _is_number(value: object) -> bool:
            return isinstance(value, (int, float)) and not isinstance(value, bool)

        if (
            not isinstance(values, list)
            or not values
            or any(not _is_number(value) for value in values)
            or not _is_number(claimed)
        ):
            return ProfileOutcome(Disposition.BLOCKED, "numeric_contract_invalid")
        try:
            import numpy as np  # type: ignore
        except ImportError:
            return ProfileOutcome(Disposition.PARKED, "numpy_unavailable")

        array = np.asarray(values, dtype=np.float64)
        if self.operation == "mean":
            numpy_value = float(np.mean(array))
            reference = math.fsum(float(v) for v in values) / len(values)
        elif self.operation == "sum":
            numpy_value = float(np.sum(array))
            reference = math.fsum(float(v) for v in values)
        else:
            return ProfileOutcome(Disposition.BLOCKED, "unsupported_operation")
        evidence: dict[str, Any] = {
            "operation": self.operation,
            "numpy_value": numpy_value,
            "stdlib_reference": reference,
            "claimed_value": float(claimed),
            "tolerance": self.tolerance,
            "numpy_version": str(np.__version__),
        }
        if not math.isclose(
            numpy_value, reference, rel_tol=self.tolerance, abs_tol=self.tolerance
        ):
            return ProfileOutcome(
                Disposition.PARKED, "reduction_order_is_load_bearing", evidence
            )
        if not math.isclose(
            reference, float(claimed), rel_tol=self.tolerance, abs_tol=self.tolerance
        ):
            return ProfileOutcome(
                Disposition.BLOCKED, "aggregate_mismatch", evidence
            )
        return ProfileOutcome(Disposition.ELIGIBLE, "aggregate_recomputed", evidence)
