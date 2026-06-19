"""The NOTARY: the ONLY component that signs receipts -- the executor is not the notary.

WHY A SEPARATE NOTARY (executor/notary split; the real fleet flagged this 3x, 2026-06-15):

  Before this split the RUNNER (which drives an untrusted provider and processes its
  output) ALSO held the signing key and signed inline.  That collapses the trust boundary:
  the same code path that handles untrusted model output can mint a valid signature, so a
  compromised/forged execution record is indistinguishable from a real one.  The fix is the
  executor/notary separation -- the executor PRODUCES an UNSIGNED execution record and HANDS
  it to the notary; the notary is the ONLY thing that holds key material and the ONLY thing
  that signs, and it signs an observation ONLY AFTER checking the observation is a well-formed
  unsigned execution record from a REGISTERED producer.

PER-IDENTITY KEYS (author-distinctness becomes KEY-backed, not LABEL-backed):

  Each producer (a provider/agent identity, e.g. "agent-A", "x-ai/grok-4.3") is REGISTERED
  with its OWN secret key and a derived ``key_id``.  The notary signs a producer's observation
  with THAT producer's key and stamps the ``key_id`` into the SIGNED payload.  Distinctness of
  authors (for no-self-grading) is then verified by ``key_id`` -- two receipts are from distinct
  producers iff they carry DIFFERENT key_ids, i.e. they were signed under different registered
  keys.  A free-string ``produced_by`` alone can no longer fake distinctness: minting a receipt
  that claims a different ``produced_by`` without holding that producer's key yields no valid
  signature under a distinct key_id.

KEY ISOLATION (the untrusted path cannot reach key material):

  ``KeyRegistry`` is the secret store.  ``Notary`` wraps it.  The runner/orchestrator code that
  handles untrusted output imports NEITHER -- it produces UNSIGNED receipts and calls
  ``Notary.notarize``.  See ``scripts/llm_harness/SIGNING_BOUNDARY.txt`` (enforced by a test):
  ``runner.py`` and the untrusted branch of ``orchestrator.py`` must not import a signing-key
  capability.  Verification only needs to RESOLVE a key by key_id (read), not to mint one, so the
  gate can verify per-identity signatures without holding a signing capability.

This is still HMAC, not PKI: a per-identity HMAC key proves "signed by the holder of THIS
producer's boundary key".  It closes the hand-edit/recompute forgery (signature binds the whole
canonical receipt, including produced_by and key_id) and makes author-distinctness key-backed.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .signing import (
    SIGNATURE_KEY,
    KEY_ID_KEY,
    canonical_signable,
    hmac_hex,
    normalize_identity,
    register_key_resolver,
    resolve_key as _resolve_key,
)

# Directory holding per-identity secret keys (one file per key_id, 0600).
_KEY_DIR = Path(os.path.expanduser("~/.codex-ratchet/harness_keys"))

# The default/legacy producer identity.  A run that does not name a producer is signed under
# this single shared boundary key (the pre-per-identity-key behaviour), so direct run_job calls
# and the existing single-key fixtures keep verifying.  Its key is the same env/file key the
# legacy ``signing.get_key`` used, so legacy signatures are bit-for-bit compatible.
DEFAULT_PRODUCER = "__default__"


def key_id_for(identity: str) -> str:
    """The stable, NON-secret key id for a producer identity.

    Derived from the NORMALIZED identity so 'agent-A' and 'agent-A ' map to ONE key id (they are
    the same producer; trailing space/case cannot fork a producer into two key ids).  The key id
    is published in the signed receipt; the SECRET key it names never is.
    """
    norm = normalize_identity(identity) or DEFAULT_PRODUCER
    return "k_" + hashlib.sha256(("codex_ratchet.producer_key.v1:" + norm).encode("utf-8")).hexdigest()[:16]


class KeyRegistry:
    """The SECRET store: maps a producer identity -> (key_id, secret key bytes).

    This object is the signing capability.  Only the notary holds it.  The runner/orchestrator
    untrusted path must not import or construct it (enforced by the boundary test).
    """

    def __init__(self, key_dir: Optional[Path] = None) -> None:
        self._key_dir = key_dir or _KEY_DIR
        self._cache: dict[str, bytes] = {}

    def _legacy_default_key(self) -> bytes:
        """The default producer's key == the legacy single boundary key (env / ~/.codex-ratchet/
        harness_hmac.key).  Keeps pre-split signatures verifiable."""
        from .signing import get_key  # legacy single-key source (env override, else key file)

        return get_key()

    def secret_for(self, identity: str) -> bytes:
        """Return (creating if absent) the secret key bytes for a producer identity.

        The default producer reuses the legacy single key.  Every other registered producer gets
        its OWN 32-byte key, persisted 0600 at ``{key_dir}/{key_id}.key``.  An env override
        ``LLM_HARNESS_KEY_<KEYID>`` is honoured first (lets tests inject deterministic per-identity
        keys without touching disk).
        """
        kid = key_id_for(identity)
        if normalize_identity(identity) in ("", DEFAULT_PRODUCER):
            return self._legacy_default_key()
        # env override wins over the cache so a per-test pinned key is honoured even if a prior key
        # was cached under the same key_id (a global registry singleton outlives a single test).
        env = os.environ.get("LLM_HARNESS_KEY_" + kid.upper())
        if env:
            return env.encode("utf-8")
        if kid in self._cache:
            return self._cache[kid]
        path = self._key_dir / f"{kid}.key"
        if path.exists():
            key = path.read_bytes()
        else:
            key = secrets.token_bytes(32)
            self._key_dir.mkdir(parents=True, exist_ok=True)
            path.write_bytes(key)
            try:
                path.chmod(0o600)
            except OSError:
                pass
        self._cache[kid] = key
        return key

    def key_by_id(self, key_id: str, identity_hint: Optional[str] = None) -> Optional[bytes]:
        """Resolve a secret key from its PUBLISHED key_id (verification path).

        The verifier knows the key_id (it is in the signed receipt) and the producer identity (it
        is the signed ``produced_by``).  We confirm the identity_hint hashes to the same key_id
        before returning the key, so a receipt cannot name key_id X while claiming an identity that
        belongs to key_id Y.
        """
        if identity_hint is not None and key_id_for(identity_hint) != key_id:
            return None
        if key_id == key_id_for(DEFAULT_PRODUCER):
            return self._legacy_default_key()
        if identity_hint is not None:
            return self.secret_for(identity_hint)
        # env override wins over the cache (see secret_for: deterministic per-test pinning).
        env = os.environ.get("LLM_HARNESS_KEY_" + key_id.upper())
        if env:
            return env.encode("utf-8")
        if key_id in self._cache:
            return self._cache[key_id]
        path = self._key_dir / f"{key_id}.key"
        if path.exists():
            key = path.read_bytes()
            self._cache[key_id] = key
            return key
        return None


@dataclass
class NotarizeResult:
    """The outcome of a notarization attempt.

    ``ok`` is whether the observation was accepted and signed; ``signature`` / ``key_id`` carry
    the stamped values on success; ``reason`` explains a rejection.
    """

    ok: bool
    signature: Optional[str] = None
    key_id: Optional[str] = None
    reason: str = ""


# The set of receipt fields a well-formed UNSIGNED execution record must carry before the notary
# will sign it.  This is a structural well-formedness check, not a quality gate (the deterministic
# gate scores quality later).  It exists so the notary does not sign arbitrary blobs.
_REQUIRED_OBSERVATION_FIELDS = (
    "schema",
    "task_id",
    "produced_by",
    "status",
    "started_at",
    "completed_at",
)


class Notary:
    """The ONLY signer.  Holds the key registry; signs a well-formed unsigned observation from a
    registered producer under that producer's per-identity key.

    A producer must be REGISTERED before the notary will sign for it.  ``register`` ensures the
    producer's key exists (minting it on first registration).  ``notarize`` refuses to sign an
    already-signed receipt, a malformed observation, or an unregistered producer.
    """

    def __init__(self, registry: Optional[KeyRegistry] = None) -> None:
        self._registry = registry or KeyRegistry()
        self._registered: set[str] = {DEFAULT_PRODUCER}  # the default producer is always registered

    # --- producer registration -------------------------------------------------
    def register(self, identity: str) -> str:
        """Register a producer identity; return its key_id (minting the key if needed)."""
        norm = normalize_identity(identity) or DEFAULT_PRODUCER
        self._registry.secret_for(identity)  # ensure key material exists
        self._registered.add(norm)
        return key_id_for(identity)

    def is_registered(self, identity: str) -> bool:
        return (normalize_identity(identity) or DEFAULT_PRODUCER) in self._registered

    # --- the trust boundary: validate then sign --------------------------------
    @staticmethod
    def _is_well_formed_unsigned_observation(obs: dict[str, Any]) -> tuple[bool, str]:
        """The observation must be an UNSIGNED execution record with the required fields.

        REJECTS: a non-dict, a record already carrying a signature (the notary signs ONCE; a
        pre-signed blob is not an unsigned observation), or a record missing a required field or
        naming no producer.  This is the check that stops the notary from rubber-stamping
        arbitrary input.
        """
        if not isinstance(obs, dict):
            return False, "observation_not_a_dict"
        if obs.get(SIGNATURE_KEY):
            return False, "already_signed: notary signs an UNSIGNED observation only"
        for f in _REQUIRED_OBSERVATION_FIELDS:
            if f not in obs:
                return False, f"missing_required_field: {f}"
        if not normalize_identity(obs.get("produced_by")):
            return False, "no_producer_named: produced_by is empty"
        return True, "well_formed_unsigned_observation"

    def notarize_dict(self, obs: dict[str, Any]) -> NotarizeResult:
        """Validate + sign an unsigned observation dict; return the signature + key_id or a reason.

        The observation is signed under the per-identity key of its ``produced_by``; the signed
        payload INCLUDES the stamped ``key_id`` (so the signature binds which producer key was
        used and the key_id cannot be swapped without breaking the signature).
        """
        ok, reason = self._is_well_formed_unsigned_observation(obs)
        if not ok:
            return NotarizeResult(ok=False, reason=reason)
        identity = obs.get("produced_by") or DEFAULT_PRODUCER
        if not self.is_registered(identity):
            return NotarizeResult(ok=False, reason=f"unregistered_producer: {identity!r}")
        kid = key_id_for(identity)
        key = self._registry.secret_for(identity)
        # Stamp key_id INTO the payload, then sign the payload that INCLUDES key_id.
        payload = dict(obs)
        payload[KEY_ID_KEY] = kid
        payload.pop(SIGNATURE_KEY, None)
        signature = hmac_hex(key, canonical_signable(payload))
        return NotarizeResult(ok=True, signature=signature, key_id=kid)

    def notarize(self, receipt: Any) -> NotarizeResult:
        """Notarize a ModelReceipt-like object IN PLACE.

        The receipt must expose ``to_dict()`` and accept ``.signature`` / ``.key_id`` assignment.
        On success the receipt is mutated to carry the signature + key_id; on failure it is left
        UNSIGNED and the reason is returned (the executor never gets a signature out of a rejected
        observation).
        """
        obs = receipt.to_dict()
        # The to_dict of an unsigned receipt may already carry signature=None / key_id=None keys;
        # strip a None signature so the well-formedness check sees a genuinely unsigned observation.
        if obs.get(SIGNATURE_KEY) is None:
            obs.pop(SIGNATURE_KEY, None)
        res = self.notarize_dict(obs)
        if res.ok:
            receipt.key_id = res.key_id
            receipt.signature = res.signature
        return res


# ---------------------------------------------------------------------------
# Wire the notary's key registry into the verifier so the gate can RESOLVE a
# per-identity key by key_id WITHOUT holding a signing capability.  The resolver
# is read-only key lookup; it cannot mint a signature.
# ---------------------------------------------------------------------------
_VERIFY_REGISTRY = KeyRegistry()


def _verify_key_resolver(receipt_dict: dict[str, Any]) -> Optional[bytes]:
    """Resolve the key a signed receipt was signed under, from its stamped key_id + produced_by."""
    kid = receipt_dict.get(KEY_ID_KEY)
    identity = receipt_dict.get("produced_by")
    if not kid:
        return None
    return _VERIFY_REGISTRY.key_by_id(kid, identity_hint=identity)


# register the resolver so signing.verify_payload can verify per-identity signatures.
register_key_resolver(_verify_key_resolver)
