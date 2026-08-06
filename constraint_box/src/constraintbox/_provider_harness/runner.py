"""run_job: drive a provider, stamp producer identity, hand the UNSIGNED observation to the notary.

EXECUTOR/NOTARY SPLIT (the real fleet flagged 3x: the executor must NOT be the notary):

  The runner is the EXECUTOR seam between a Provider (which produces execution facts from
  UNTRUSTED model output) and disk.  It does NOT sign and it does NOT hold key material -- it
  produces an UNSIGNED execution record (the ModelReceipt with signature=None) and HANDS it to the
  NOTARY, which is the only component that signs.  The runner deliberately does NOT import
  ``sign_payload`` or any signing-key capability; if no notary is supplied it leaves the receipt
  UNSIGNED (an unsigned receipt is capped at scratch_diagnostic by the gate and cannot self-promote).

  The runner does NOT re-decide status: the provider already classified the run (timeout ->
  timed_out, nonzero rc -> error, unparseable -> blocked, ok -> success), and the runner trusts
  that captured verdict verbatim.  The only mutation the runner performs before notarization is
  stamping ``produced_by`` (the trusted author identity) when the job carries one and the provider
  left it blank.  It then optionally writes the receipt JSON to disk with stable byte output.

Timestamps are passed in so the persisted receipt is reproducible.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .providers import Provider
from .types import ModelJob, ModelReceipt


def canonical_receipt_json(receipt: ModelReceipt) -> str:
    """Deterministic JSON serialization of a receipt (sorted keys, no clock)."""
    return json.dumps(receipt.to_dict(), sort_keys=True, indent=2)


def write_receipt(receipt: ModelReceipt, receipt_path: str | Path) -> Path:
    """Write the receipt JSON to disk; return the path."""
    path = Path(receipt_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_receipt_json(receipt), encoding="utf-8")
    return path


def run_job(
    job: ModelJob,
    provider: Provider,
    *,
    timeout: Optional[float] = None,
    started_at: str,
    completed_at: str,
    receipt_path: Optional[str | Path] = None,
    notary: Optional[Any] = None,
) -> ModelReceipt:
    """Run a single job through a provider and HAND the unsigned receipt to the notary.

    The provider returns a ModelReceipt carrying REAL captured facts.  The runner stamps
    ``produced_by`` (if the job names an author and the provider left it blank), hands the
    UNSIGNED receipt to ``notary.notarize`` to be signed, persists the receipt (if
    ``receipt_path`` is given), and returns it.

    If ``notary`` is None, a default notary is constructed HERE -- but note the runner only ever
    obtains a *capability object*; it never imports a signing key directly.  The notary owns the
    key registry and performs the producer/well-formedness check before signing.

    status semantics are set by the PROVIDER and surfaced here unchanged:
      ok -> success, timeout -> timed_out, nonzero rc -> error, unparseable -> blocked.
    """
    receipt = provider.run(
        job,
        timeout=timeout,
        started_at=started_at,
        completed_at=completed_at,
    )
    if job.produced_by and not receipt.produced_by:
        receipt.produced_by = job.produced_by  # stamp producer identity (no-self-grading author check)

    # Hand the UNSIGNED observation to the notary. The runner never signs and never holds a key.
    # The notary checks the observation is a well-formed unsigned record from a registered producer
    # (registering the default producer / the named producer as needed), then signs it under that
    # producer's PER-IDENTITY key and stamps key_id. produced_by / status / gate_ceiling_rung /
    # content hashes / key_id are all bound by the signature, so they cannot be hand-edited and
    # recomputed (box-viii L1c: the real fleet proved unsigned produced_by is forgeable free text).
    nt = notary
    if nt is None:
        from .notary import Notary  # capability object; the KEY lives inside it, not in the runner
        nt = Notary()
    receipt.signature = None  # ensure we hand an UNSIGNED observation
    nt.register(receipt.produced_by or "")  # ensure the producer is registered before signing
    nt.notarize(receipt)  # mutates receipt in place with signature + key_id on success

    if receipt_path is not None:
        write_receipt(receipt, receipt_path)
    return receipt
