"""Concurrent, model-neutral collection of zero-authority advisory receipts."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Mapping, Sequence

from .advisory_provider import PROVIDER_REGISTRY, STATE_ACCEPTED, run_advisory_audit


SCHEMA = "constraintbox.advisory-fanout.v1"


class AdvisoryFanoutError(ValueError):
    pass


def run_advisory_fanout(
    providers: Sequence[str],
    frozen_decision: dict[str, Any],
    *,
    output_contract: tuple[str, ...] = (),
    environ: Mapping[str, str] | None = None,
    runner: Callable[..., Any] = run_advisory_audit,
) -> dict[str, Any]:
    """Collect independently configured provider advice concurrently.

    Selection is an operator-supplied list of registered *routes*; CB does not
    rank models, merge their prose into a decision, or encode a budget policy.
    Every result is retained as advisory data only.
    """

    if not isinstance(providers, Sequence) or isinstance(providers, (str, bytes)):
        raise AdvisoryFanoutError("providers must be an ordered sequence")
    names = tuple(providers)
    if len(names) < 2 or len(names) > 8 or len(set(names)) != len(names):
        raise AdvisoryFanoutError("fanout needs 2..8 distinct provider routes")
    if any(not isinstance(name, str) or name not in PROVIDER_REGISTRY for name in names):
        raise AdvisoryFanoutError("fanout names an unregistered provider route")
    if not isinstance(frozen_decision, dict):
        raise AdvisoryFanoutError("frozen decision must be an object")

    received: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=len(names), thread_name_prefix="cb-advisory") as pool:
        futures = {
            pool.submit(
                runner,
                name,
                frozen_decision,
                output_contract=output_contract,
                environ=environ,
            ): name
            for name in names
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                receipt = future.result()
                row = receipt.to_dict() if hasattr(receipt, "to_dict") else receipt
                if not isinstance(row, dict):
                    raise AdvisoryFanoutError("provider returned no receipt object")
            except Exception:
                row = {"provider_state": "PARKED", "reason_code": "fanout_worker_error"}
            received[name] = row
    ordered = [{"provider": name, "receipt": received[name]} for name in names]
    accepted = [name for name in names if received[name].get("provider_state") == STATE_ACCEPTED]
    return {
        "schema": SCHEMA,
        "state": "COMPLETE" if len(accepted) == len(names) else "PARTIAL",
        "operator_selected_routes": list(names),
        "provider_receipts": ordered,
        "accepted_routes": accepted,
        "advisory_only": True,
        "decision_authority": False,
        "release_allowed": False,
        "promotion_allowed": False,
        "claim_ceiling": "concurrent collection of independently routed advisory receipts; no model ranking, merger, tool selection, gate selection, release, or promotion",
    }
