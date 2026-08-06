"""HMAC primitives + signature VERIFICATION for harness receipts.

box-viii L1c (2026-06-15): no-self-grading on self-asserted PLAINTEXT receipts is forgeable -- a
work-author can hand-edit produced_by / status / gate_ceiling_rung and recompute the content
hashes.  The fix is an HMAC signature over the canonical receipt: the gate VERIFIES it; an unsigned
or tampered receipt is CAPPED at scratch_diagnostic and cannot self-promote.

EXECUTOR/NOTARY SPLIT (this module no longer signs in the executor path):

  This module holds the HMAC PRIMITIVES (``hmac_hex``, ``canonical_signable``) and the
  VERIFICATION path (``verify_payload``).  SIGNING is done ONLY by ``notary.Notary`` -- the single
  component that holds key material and is separated from the untrusted-output executor.  The
  legacy single-key helpers (``get_key`` / ``sign_payload``) remain for the default producer and
  for direct verification fixtures, but the runner/orchestrator no longer call ``sign_payload``;
  they hand an UNSIGNED observation to the notary.

VERIFICATION is read-only key lookup -- it never mints a signature, so it is safe to expose to the
gate.  ``verify_payload`` resolves the signing key from the receipt's stamped ``key_id`` via a
registered resolver (the notary registers one that reads the per-identity key registry); if no
key_id is present (a legacy single-key receipt) it falls back to the legacy boundary key.

Key source (default-producer secret; NEVER written into any receipt):
  env CONSTRAINTBOX_PROVIDER_HMAC_KEY (legacy LLM_HARNESS_HMAC_KEY is accepted),
  else an explicit CONSTRAINTBOX_PROVIDER_KEY_FILE or a file below the explicit
  CONSTRAINTBOX_RUNTIME_DIR.  There is deliberately no home-directory fallback.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Any, Callable, Optional

SIGNATURE_KEY = "signature"  # the receipt field holding the HMAC
KEY_ID_KEY = "key_id"        # the receipt field naming WHICH per-identity key signed it
_RUNTIME_DIR_ENV = "CONSTRAINTBOX_RUNTIME_DIR"
_KEY_FILE_ENV = "CONSTRAINTBOX_PROVIDER_KEY_FILE"
_KEY_ENV = "CONSTRAINTBOX_PROVIDER_HMAC_KEY"


def _absolute_directory(value: str, *, name: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise RuntimeError(f"{name} must be an absolute path")
    return path.resolve()


def _configured_key_file() -> Path:
    explicit = os.environ.get(_KEY_FILE_ENV)
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_absolute():
            raise RuntimeError(f"{_KEY_FILE_ENV} must be an absolute path")
        return path.resolve()
    runtime_dir = os.environ.get(_RUNTIME_DIR_ENV)
    if not runtime_dir:
        raise RuntimeError(
            "no provider-key location: set CONSTRAINTBOX_RUNTIME_DIR, "
            "CONSTRAINTBOX_PROVIDER_KEY_FILE, or CONSTRAINTBOX_PROVIDER_HMAC_KEY"
        )
    return (
        _absolute_directory(runtime_dir, name=_RUNTIME_DIR_ENV)
        / "provider_harness"
        / "default_hmac.key"
    )


def get_key() -> bytes:
    """Return the default-producer secret from an explicit runtime location.

    An environment secret wins.  Otherwise a new 0600 key is created below a
    caller-selected runtime directory.  The package never creates a hidden
    key under the user's home directory.
    """
    env = os.environ.get(_KEY_ENV) or os.environ.get("LLM_HARNESS_HMAC_KEY")
    if env:
        return env.encode("utf-8")
    key_file = _configured_key_file()
    if key_file.exists():
        return key_file.read_bytes()
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_bytes(32)
    key_file.write_bytes(key)
    try:
        key_file.chmod(0o600)
    except OSError:
        pass
    return key


def canonical_signable(receipt_dict: dict[str, Any]) -> str:
    """Canonical JSON of the receipt EXCLUDING the signature field itself.

    The ``key_id`` field IS included (it is part of what the signature binds), so a signed receipt
    cannot have its key_id swapped without invalidating the signature.
    """
    d = {k: v for k, v in receipt_dict.items() if k != SIGNATURE_KEY}
    return json.dumps(d, sort_keys=True, ensure_ascii=False, default=str)


# back-compat alias for the old private name.
def _signable_payload(receipt_dict: dict[str, Any]) -> str:
    return canonical_signable(receipt_dict)


def hmac_hex(key: bytes, message: str) -> str:
    """HMAC-SHA256 hex over a message under a key.  The single MAC primitive."""
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).hexdigest()


def sign_payload(receipt_dict: dict[str, Any], key: Optional[bytes] = None) -> str:
    """LEGACY single-key signer: HMAC over the canonical receipt under the default boundary key.

    Retained for the default producer and for verification fixtures.  The EXECUTOR path (runner /
    orchestrator) no longer calls this -- signing goes through ``notary.Notary``.
    """
    k = key if key is not None else get_key()
    return hmac_hex(k, canonical_signable(receipt_dict))


# ---------------------------------------------------------------------------
# Per-identity key resolution for VERIFICATION.  The notary registers a resolver
# that maps a signed receipt -> the secret key it was signed under (via key_id).
# Verification is read-only: a resolver returns a key for VERIFYING, and this
# module never exposes a way to MINT a signature from it.
# ---------------------------------------------------------------------------
_KEY_RESOLVER: Optional[Callable[[dict[str, Any]], Optional[bytes]]] = None


def register_key_resolver(resolver: Callable[[dict[str, Any]], Optional[bytes]]) -> None:
    """Install the verification key resolver (called once by ``notary`` on import)."""
    global _KEY_RESOLVER
    _KEY_RESOLVER = resolver


def resolve_key(receipt_dict: dict[str, Any]) -> Optional[bytes]:
    """Resolve the key a receipt was signed under.

    If the receipt carries a ``key_id`` and a resolver is registered, use it (per-identity key).
    Otherwise fall back to the legacy single boundary key (a pre-per-identity-key receipt).
    """
    if receipt_dict.get(KEY_ID_KEY) and _KEY_RESOLVER is not None:
        return _KEY_RESOLVER(receipt_dict)
    return get_key()


def verify_payload(receipt_dict: dict[str, Any], key: Optional[bytes] = None) -> bool:
    """True iff the receipt carries a signature matching its canonical content under its key.

    A missing signature, a tampered field, an unknown/unresolvable key_id, or the wrong key all
    return False (constant-time compare).  The key is resolved per-identity from the receipt's
    key_id unless an explicit ``key`` is given (verification fixtures)."""
    sig = receipt_dict.get(SIGNATURE_KEY)
    if not sig:
        return False
    k = key if key is not None else resolve_key(receipt_dict)
    if k is None:
        return False  # key_id named a producer we cannot resolve -> cannot verify
    return hmac.compare_digest(str(sig), hmac_hex(k, canonical_signable(receipt_dict)))


def normalize_identity(s: Optional[str]) -> str:
    """Author identity comparison key: trailing/leading whitespace and case must not create a
    spurious distinctness ('agent-A' vs 'agent-A ' must NOT count as two authors)."""
    return (s or "").strip().lower()
