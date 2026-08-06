from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from .intake import canonical_json


SEAL_SCHEMA = "constraintbox.run-seal.v2"
LEGACY_SEAL_SCHEMA = "constraintbox.run-seal.v1"
REQUIRED_MANIFEST_SCHEMA = "constraintbox.required-reference-manifest.v1"
_HEX = "0123456789abcdef"
_CHUNK = 65536


class EvidenceError(ValueError):
    """A reference or seal that cannot be admitted."""


class SealFailedClosed(EvidenceError):
    """Sealing refused because a reference was not observed at seal time."""


class RefKind(str, Enum):
    """What the pointed-at record is, never what it says."""

    RECEIPT = "receipt"
    TRACE = "trace"
    LOG = "log"
    ARTIFACT = "artifact"
    GATE_PROOF = "gate_proof"
    MEASUREMENT = "measurement"
    VERDICT = "verdict"


class SealVerdict(str, Enum):
    """Operational disposition of a re-verified seal."""

    SEALED = "SEALED"
    REF_MISSING = "REF_MISSING"
    REF_CHANGED = "REF_CHANGED"
    MALFORMED = "MALFORMED"


def _utc(now: datetime | None) -> str:
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()


def _is_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _is_digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in _HEX for character in value)
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


class EvidenceRoute:
    """Turns a locator string into a location that can be observed.

    A route that is never resolved is decoration.  Every route here must be
    able to produce a filesystem location, and sealing resolves all of them.
    """

    route_id = ""

    def check_shape(self, ref: str) -> None:
        raise NotImplementedError

    def locate(self, ref: str) -> Path:
        raise NotImplementedError

    def confirm(self, ref: str, digest: str | None) -> None:
        """Route-specific check of observed bytes.  Raises to fail closed."""
        return None


class FileRoute(EvidenceRoute):
    """The locator is a relative path under a fixed evidence root."""

    route_id = "file"

    def __init__(self, root: Path):
        self.root = Path(root)

    def check_shape(self, ref: str) -> None:
        if not ref:
            raise EvidenceError("file ref must be a non-empty relative path")
        candidate = Path(ref)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise EvidenceError(
                f"file ref must be relative and free of '..': {ref!r}"
            )

    def locate(self, ref: str) -> Path:
        self.check_shape(ref)
        return self.root / ref


class DigestRoute(EvidenceRoute):
    """The locator IS the sha256 of the stored bytes, in a flat store."""

    route_id = "digest"

    def __init__(self, store: Path):
        self.store = Path(store)

    def check_shape(self, ref: str) -> None:
        if not _is_digest(ref):
            raise EvidenceError(f"digest ref must be 64 lowercase hex: {ref!r}")

    def locate(self, ref: str) -> Path:
        self.check_shape(ref)
        return self.store / ref

    def confirm(self, ref: str, digest: str | None) -> None:
        if digest is not None and digest != ref:
            raise EvidenceError(
                f"content-addressed blob does not hash to its name: {ref}"
            )


def route_table(*routes: EvidenceRoute) -> dict[str, EvidenceRoute]:
    table: dict[str, EvidenceRoute] = {}
    for route in routes:
        if not route.route_id:
            raise EvidenceError("route must declare a route_id")
        if route.route_id in table:
            raise EvidenceError(f"duplicate route_id: {route.route_id}")
        table[route.route_id] = route
    return table


@dataclass(frozen=True)
class EvidenceRef:
    """A pointer to evidence.  It carries no evidence and no verdict.

    ``exists``, ``observed_sha256`` and ``observed_at_utc`` are not constructor
    arguments.  They are written only by :func:`observe`, from what the world
    showed at that moment.  A caller cannot assert them.
    """

    kind: RefKind
    ref: str
    route: str
    exists: bool | None = field(default=None, init=False)
    observed_sha256: str | None = field(default=None, init=False)
    observed_at_utc: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, RefKind):
            raise EvidenceError("kind must be a RefKind")
        if not isinstance(self.ref, str) or not self.ref.strip():
            raise EvidenceError("ref must be a non-empty locator string")
        if self.ref != self.ref.strip():
            raise EvidenceError("ref must not carry surrounding whitespace")
        if not isinstance(self.route, str) or not self.route.strip():
            raise EvidenceError("route must name an evidence route")
        if self.route != self.route.strip():
            raise EvidenceError("route must not carry surrounding whitespace")

    @property
    def observed(self) -> bool:
        return self.exists is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "ref": self.ref,
            "route": self.route,
            "exists": self.exists,
            "observed_sha256": self.observed_sha256,
            "observed_at_utc": self.observed_at_utc,
        }


def _with_observation(
    ref: EvidenceRef, exists: bool, digest: str | None, stamp: str
) -> EvidenceRef:
    fresh = EvidenceRef(kind=ref.kind, ref=ref.ref, route=ref.route)
    object.__setattr__(fresh, "exists", exists)
    object.__setattr__(fresh, "observed_sha256", digest)
    object.__setattr__(fresh, "observed_at_utc", stamp)
    return fresh


def ref_from_dict(body: Mapping[str, Any]) -> EvidenceRef:
    """Rebuild a recorded reference, keeping its recorded observation."""
    if not isinstance(body, Mapping):
        raise EvidenceError("reference record must be a mapping")
    try:
        kind = RefKind(body["kind"])
    except (KeyError, ValueError) as exc:
        raise EvidenceError(f"unusable reference kind: {exc}") from exc
    fresh = EvidenceRef(
        kind=kind, ref=body.get("ref", ""), route=body.get("route", "")
    )
    exists = body.get("exists")
    if exists is not None and not isinstance(exists, bool):
        raise EvidenceError("recorded exists must be a boolean or absent")
    object.__setattr__(fresh, "exists", exists)
    object.__setattr__(fresh, "observed_sha256", body.get("observed_sha256"))
    object.__setattr__(fresh, "observed_at_utc", body.get("observed_at_utc"))
    return fresh


def _strict_observed_ref_from_dict(body: Mapping[str, Any]) -> EvidenceRef:
    if not isinstance(body, Mapping):
        raise EvidenceError("v2 seal reference must be a mapping")
    expected = {
        "kind",
        "ref",
        "route",
        "exists",
        "observed_sha256",
        "observed_at_utc",
    }
    if set(body) != expected:
        raise EvidenceError(
            "v2 seal reference must contain exactly "
            f"{sorted(expected)!r}; got {sorted(body)!r}"
        )
    ref = ref_from_dict(body)
    if ref.exists is not True:
        raise EvidenceError("v2 seal reference exists must be true")
    if not _is_digest(ref.observed_sha256):
        raise EvidenceError("v2 seal reference digest is missing or malformed")
    if not _is_timestamp(ref.observed_at_utc):
        raise EvidenceError("v2 seal reference timestamp is missing or malformed")
    return ref


def _ref_identity(ref: EvidenceRef) -> dict[str, str]:
    return {
        "kind": ref.kind.value,
        "ref": ref.ref,
        "route": ref.route,
    }


def _identity_from_dict(body: Mapping[str, Any]) -> EvidenceRef:
    if not isinstance(body, Mapping):
        raise EvidenceError("required-reference row must be a mapping")
    expected = {"kind", "ref", "route"}
    if set(body) != expected:
        raise EvidenceError(
            "required-reference row must contain exactly "
            f"{sorted(expected)!r}; got {sorted(body)!r}"
        )
    try:
        kind = RefKind(body["kind"])
    except (KeyError, ValueError) as exc:
        raise EvidenceError(f"unusable required-reference kind: {exc}") from exc
    return EvidenceRef(kind=kind, ref=body["ref"], route=body["route"])


def _manifest_body(
    schema: str,
    manifest_id: str,
    refs: Sequence[EvidenceRef],
) -> dict[str, Any]:
    return {
        "schema": schema,
        "manifest_id": manifest_id,
        "refs": [_ref_identity(ref) for ref in refs],
    }


@dataclass(frozen=True)
class RequiredReferenceManifest:
    """Controller-owned list of references a run is required to seal.

    This object stays outside the run seal.  Verification receives it again
    from the controller so an editor of the seal cannot redefine which
    references were required.
    """

    schema: str
    manifest_id: str
    refs: tuple[EvidenceRef, ...]
    manifest_sha256: str

    def __post_init__(self) -> None:
        if self.schema != REQUIRED_MANIFEST_SCHEMA:
            raise EvidenceError(f"unknown required-reference schema: {self.schema!r}")
        if (
            not isinstance(self.manifest_id, str)
            or not self.manifest_id.strip()
            or self.manifest_id != self.manifest_id.strip()
        ):
            raise EvidenceError("manifest_id must be a non-empty trimmed string")
        if not isinstance(self.refs, tuple):
            raise EvidenceError("required manifest refs must be a tuple")
        if not self.refs:
            raise EvidenceError("required manifest must contain at least one reference")
        seen: set[tuple[str, str]] = set()
        for index, ref in enumerate(self.refs):
            if type(ref) is not EvidenceRef:
                raise EvidenceError(
                    f"required manifest element {index} is "
                    f"{type(ref).__name__}, not an EvidenceRef"
                )
            if ref.observed:
                raise EvidenceError(
                    f"required manifest element {index} carries an observation"
                )
            key = (ref.route, ref.ref)
            if key in seen:
                raise EvidenceError(
                    f"duplicate required reference at element {index}: "
                    f"{ref.route}:{ref.ref}"
                )
            seen.add(key)
        if not _is_digest(self.manifest_sha256):
            raise EvidenceError(
                "required manifest digest must be 64 lowercase hex characters"
            )

    def to_dict(self) -> dict[str, Any]:
        body = _manifest_body(self.schema, self.manifest_id, self.refs)
        body["manifest_sha256"] = self.manifest_sha256
        return body


def build_required_manifest(
    manifest_id: str,
    refs: Sequence[EvidenceRef],
) -> RequiredReferenceManifest:
    """Freeze the controller's exact required-reference set."""
    frozen_refs = tuple(refs)
    candidate = RequiredReferenceManifest(
        schema=REQUIRED_MANIFEST_SCHEMA,
        manifest_id=manifest_id,
        refs=frozen_refs,
        manifest_sha256="0" * 64,
    )
    body = _manifest_body(REQUIRED_MANIFEST_SCHEMA, manifest_id, frozen_refs)
    return RequiredReferenceManifest(
        schema=candidate.schema,
        manifest_id=candidate.manifest_id,
        refs=candidate.refs,
        manifest_sha256=hashlib.sha256(canonical_json(body)).hexdigest(),
    )


def required_manifest_from_dict(
    body: Mapping[str, Any],
) -> RequiredReferenceManifest:
    """Strictly parse a controller-owned required-reference manifest."""
    if not isinstance(body, Mapping):
        raise EvidenceError("required-reference manifest must be a mapping")
    expected = {"schema", "manifest_id", "refs", "manifest_sha256"}
    if set(body) != expected:
        raise EvidenceError(
            "required-reference manifest must contain exactly "
            f"{sorted(expected)!r}; got {sorted(body)!r}"
        )
    rows = body["refs"]
    if not isinstance(rows, list):
        raise EvidenceError("required-reference manifest refs must be a list")
    manifest = RequiredReferenceManifest(
        schema=body["schema"],
        manifest_id=body["manifest_id"],
        refs=tuple(_identity_from_dict(row) for row in rows),
        manifest_sha256=body["manifest_sha256"],
    )
    expected_digest = hashlib.sha256(
        canonical_json(
            _manifest_body(manifest.schema, manifest.manifest_id, manifest.refs)
        )
    ).hexdigest()
    if manifest.manifest_sha256 != expected_digest:
        raise EvidenceError("required-reference manifest digest does not match")
    return manifest


def observe(
    ref: EvidenceRef,
    routes: Mapping[str, EvidenceRoute],
    *,
    now: datetime | None = None,
) -> EvidenceRef:
    """Re-check one reference against the world and record what was seen.

    It never trusts an incoming observation; it discards it and looks again.
    An unregistered route raises rather than returning an unobserved ref.
    """
    if type(ref) is not EvidenceRef:
        raise EvidenceError(
            f"observe takes an EvidenceRef, not {type(ref).__name__}"
        )
    route = routes.get(ref.route)
    if route is None:
        raise EvidenceError(f"unregistered evidence route: {ref.route!r}")
    location = route.locate(ref.ref)
    exists = location.is_file()
    digest = _sha256_file(location) if exists else None
    route.confirm(ref.ref, digest)
    return _with_observation(ref, exists, digest, _utc(now))


@dataclass(frozen=True)
class RunSeal:
    """A run closed over evidence references only.

    The seal has no field able to hold a verdict value.  It holds locators,
    and what observation saw at each locator when the run closed.
    """

    schema: str
    run_id: str
    sealed_at_utc: str
    refs: tuple[EvidenceRef, ...]
    seal_sha256: str
    required_manifest_id: str | None = None
    required_manifest_sha256: str | None = None
    promotion_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.refs, tuple):
            raise EvidenceError("refs must be a tuple")
        for index, ref in enumerate(self.refs):
            if type(ref) is not EvidenceRef:
                raise EvidenceError(
                    f"seal element {index} is {type(ref).__name__}, not an "
                    "EvidenceRef: a seal stores references, never values"
                )

    def to_dict(self) -> dict[str, Any]:
        body = {
            "schema": self.schema,
            "run_id": self.run_id,
            "sealed_at_utc": self.sealed_at_utc,
            "refs": [ref.to_dict() for ref in self.refs],
            "seal_sha256": self.seal_sha256,
            "promotion_allowed": self.promotion_allowed,
        }
        if self.schema == SEAL_SCHEMA:
            body["required_manifest_id"] = self.required_manifest_id
            body["required_manifest_sha256"] = self.required_manifest_sha256
        return body


def _seal_body(
    schema: str,
    run_id: str,
    sealed_at_utc: str,
    refs: Sequence[EvidenceRef],
    required_manifest_id: str | None = None,
    required_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    body = {
        "schema": schema,
        "run_id": run_id,
        "sealed_at_utc": sealed_at_utc,
        "refs": [ref.to_dict() for ref in refs],
    }
    if schema == SEAL_SCHEMA:
        body["required_manifest_id"] = required_manifest_id
        body["required_manifest_sha256"] = required_manifest_sha256
    return body


def seal_run(
    run_id: str,
    required_manifest: RequiredReferenceManifest,
    routes: Mapping[str, EvidenceRoute],
    *,
    now: datetime | None = None,
) -> RunSeal:
    """Close a run over references, re-checking every one at seal time.

    Sealing is the observation.  A reference that cannot be resolved produces
    no seal at all, so a run cannot close over evidence nobody looked for.
    """
    if (
        not isinstance(run_id, str)
        or not run_id.strip()
        or run_id != run_id.strip()
    ):
        raise EvidenceError("run_id must be a non-empty trimmed string")
    if type(required_manifest) is not RequiredReferenceManifest:
        raise EvidenceError(
            "seal_run requires a controller-owned RequiredReferenceManifest"
        )
    manifest_body = _manifest_body(
        required_manifest.schema,
        required_manifest.manifest_id,
        required_manifest.refs,
    )
    manifest_digest = hashlib.sha256(canonical_json(manifest_body)).hexdigest()
    if manifest_digest != required_manifest.manifest_sha256:
        raise EvidenceError("required-reference manifest digest does not match")
    stamp = _utc(now)
    observed: list[EvidenceRef] = []
    for index, candidate in enumerate(required_manifest.refs):
        if type(candidate) is not EvidenceRef:
            raise EvidenceError(
                f"seal element {index} is {type(candidate).__name__}, not an "
                "EvidenceRef: a seal stores references, never values"
            )
        fresh = observe(candidate, routes, now=now)
        if not fresh.exists:
            raise SealFailedClosed(
                "reference not observed at seal time: "
                f"{candidate.route}:{candidate.ref}"
            )
        observed.append(fresh)
    frozen_refs = tuple(observed)
    body = _seal_body(
        SEAL_SCHEMA,
        run_id,
        stamp,
        frozen_refs,
        required_manifest.manifest_id,
        required_manifest.manifest_sha256,
    )
    return RunSeal(
        schema=SEAL_SCHEMA,
        run_id=run_id,
        sealed_at_utc=stamp,
        refs=frozen_refs,
        seal_sha256=hashlib.sha256(canonical_json(body)).hexdigest(),
        required_manifest_id=required_manifest.manifest_id,
        required_manifest_sha256=required_manifest.manifest_sha256,
    )


def seal_from_dict(body: Mapping[str, Any]) -> RunSeal:
    """Rebuild a recorded seal without re-observing anything.

    The legacy v1 shape remains parseable for diagnosis, but
    :func:`verify_seal` never accepts it as sealed because it has no external
    required-reference binding.
    """
    if not isinstance(body, Mapping):
        raise EvidenceError("seal record must be a mapping")
    schema = body.get("schema")
    common = {
        "schema",
        "run_id",
        "sealed_at_utc",
        "refs",
        "seal_sha256",
        "promotion_allowed",
    }
    if schema == SEAL_SCHEMA:
        expected = common | {
            "required_manifest_id",
            "required_manifest_sha256",
        }
        if set(body) != expected:
            raise EvidenceError(
                "v2 seal record must contain exactly "
                f"{sorted(expected)!r}; got {sorted(body)!r}"
            )
    elif schema == LEGACY_SEAL_SCHEMA:
        required = common - {"promotion_allowed"}
        if not required.issubset(body) or not set(body).issubset(common):
            raise EvidenceError(
                "legacy seal record contains missing or unknown fields"
            )
    else:
        raise EvidenceError(f"unknown seal schema: {schema!r}")
    rows = body.get("refs")
    if not isinstance(rows, list):
        raise EvidenceError("seal record must carry a refs list")
    promotion_allowed = body.get("promotion_allowed", False)
    if not isinstance(promotion_allowed, bool):
        raise EvidenceError("seal promotion_allowed must be a boolean")
    if schema == SEAL_SCHEMA:
        if promotion_allowed is not False:
            raise EvidenceError("v2 evidence seals never allow promotion")
        if (
            not isinstance(body["run_id"], str)
            or not body["run_id"].strip()
            or body["run_id"] != body["run_id"].strip()
        ):
            raise EvidenceError("v2 seal run_id must be a non-empty trimmed string")
        if not _is_timestamp(body["sealed_at_utc"]):
            raise EvidenceError("v2 seal timestamp is missing or malformed")
        if not _is_digest(body["seal_sha256"]):
            raise EvidenceError("v2 seal digest is missing or malformed")
        if (
            not isinstance(body["required_manifest_id"], str)
            or not body["required_manifest_id"].strip()
            or body["required_manifest_id"]
            != body["required_manifest_id"].strip()
        ):
            raise EvidenceError(
                "v2 seal required_manifest_id must be a non-empty trimmed string"
            )
        if not _is_digest(body["required_manifest_sha256"]):
            raise EvidenceError(
                "v2 seal required_manifest_sha256 is missing or malformed"
            )
        parsed_refs = tuple(_strict_observed_ref_from_dict(row) for row in rows)
    else:
        parsed_refs = tuple(ref_from_dict(row) for row in rows)
    return RunSeal(
        schema=schema,
        run_id=body.get("run_id", ""),
        sealed_at_utc=body.get("sealed_at_utc", ""),
        refs=parsed_refs,
        seal_sha256=body.get("seal_sha256", ""),
        required_manifest_id=body.get("required_manifest_id"),
        required_manifest_sha256=body.get("required_manifest_sha256"),
        promotion_allowed=promotion_allowed,
    )


@dataclass(frozen=True)
class RefStatus:
    ref: EvidenceRef
    verdict: SealVerdict
    reason: str
    current_sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.ref.route,
            "ref": self.ref.ref,
            "kind": self.ref.kind.value,
            "verdict": self.verdict.value,
            "reason": self.reason,
            "sealed_sha256": self.ref.observed_sha256,
            "current_sha256": self.current_sha256,
        }


@dataclass(frozen=True)
class SealVerification:
    schema: str
    run_id: str
    verdict: SealVerdict
    reason: str
    refs: tuple[RefStatus, ...]
    promotion_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "verdict": self.verdict.value,
            "reason": self.reason,
            "refs": [row.to_dict() for row in self.refs],
            "promotion_allowed": self.promotion_allowed,
        }


def _verify_ref(
    ref: EvidenceRef, routes: Mapping[str, EvidenceRoute]
) -> RefStatus:
    if ref.exists is not True:
        return RefStatus(
            ref, SealVerdict.MALFORMED, "reference was never observed at seal time"
        )
    if not _is_digest(ref.observed_sha256):
        return RefStatus(
            ref, SealVerdict.MALFORMED, "sealed digest missing or malformed"
        )
    if not _is_timestamp(ref.observed_at_utc):
        return RefStatus(
            ref, SealVerdict.MALFORMED, "sealed timestamp missing or malformed"
        )
    route = routes.get(ref.route)
    if route is None:
        return RefStatus(
            ref,
            SealVerdict.MALFORMED,
            f"unregistered evidence route: {ref.route!r}",
        )
    try:
        location = route.locate(ref.ref)
    except EvidenceError as exc:
        return RefStatus(ref, SealVerdict.MALFORMED, f"malformed locator: {exc}")
    if not location.is_file():
        return RefStatus(ref, SealVerdict.REF_MISSING, "location no longer exists")
    current = _sha256_file(location)
    route_problem: EvidenceError | None = None
    try:
        route.confirm(ref.ref, current)
    except EvidenceError as exc:
        route_problem = exc
    if current != ref.observed_sha256:
        return RefStatus(
            ref,
            SealVerdict.REF_CHANGED,
            "target content differs from the digest observed at seal time",
            current,
        )
    if route_problem is not None:
        return RefStatus(
            ref,
            SealVerdict.MALFORMED,
            f"route-specific content check failed: {route_problem}",
            current,
        )
    return RefStatus(ref, SealVerdict.SEALED, "target unchanged since seal", current)


_ORDER = (SealVerdict.MALFORMED, SealVerdict.REF_MISSING, SealVerdict.REF_CHANGED)


def _required_manifest_problem(
    required_manifest: RequiredReferenceManifest | None,
) -> str | None:
    if type(required_manifest) is not RequiredReferenceManifest:
        return "controller-owned required-reference manifest was not supplied"
    body = _manifest_body(
        required_manifest.schema,
        required_manifest.manifest_id,
        required_manifest.refs,
    )
    digest = hashlib.sha256(canonical_json(body)).hexdigest()
    if digest != required_manifest.manifest_sha256:
        return "controller-owned required-reference manifest digest does not match"
    return None


def verify_seal(
    seal: RunSeal,
    routes: Mapping[str, EvidenceRoute],
    *,
    required_manifest: RequiredReferenceManifest | None = None,
) -> SealVerification:
    """Re-verify a seal by looking at the world again.

    Anything that stops the check from running is MALFORMED, never SEALED.
    An unregistered route is such a case: an unreachable reference has not
    been checked, and a seal that cannot be checked has not passed.
    """
    if type(seal) is not RunSeal:
        raise EvidenceError(
            f"verify_seal takes a RunSeal, not {type(seal).__name__}"
        )
    rows = tuple(_verify_ref(ref, routes) for ref in seal.refs)
    problems: list[str] = []
    if seal.schema != SEAL_SCHEMA:
        if seal.schema == LEGACY_SEAL_SCHEMA:
            problems.append(
                "legacy seal has no controller-owned required-reference binding"
            )
        else:
            problems.append(f"unknown seal schema: {seal.schema!r}")
    if (
        not isinstance(seal.run_id, str)
        or not seal.run_id.strip()
        or seal.run_id != seal.run_id.strip()
    ):
        problems.append("seal run_id must be a non-empty trimmed string")
    if not _is_timestamp(seal.sealed_at_utc):
        problems.append("seal timestamp is missing or malformed")
    if not _is_digest(seal.seal_sha256):
        problems.append("seal digest is missing or malformed")
    if seal.promotion_allowed is not False:
        problems.append("evidence seals never allow promotion")
    if not seal.refs:
        problems.append("seal closes over zero references")
    if len({(ref.route, ref.ref) for ref in seal.refs}) != len(seal.refs):
        problems.append("seal contains duplicate references")

    manifest_problem = _required_manifest_problem(required_manifest)
    if manifest_problem is not None:
        problems.append(manifest_problem)
    elif seal.schema == SEAL_SCHEMA:
        controller_manifest = required_manifest
        if seal.required_manifest_id != controller_manifest.manifest_id:
            problems.append(
                "seal required-manifest id differs from controller manifest"
            )
        if (
            seal.required_manifest_sha256
            != controller_manifest.manifest_sha256
        ):
            problems.append(
                "seal required-manifest digest differs from controller manifest"
            )
        sealed_identities = tuple(_ref_identity(ref) for ref in seal.refs)
        required_identities = tuple(
            _ref_identity(ref) for ref in controller_manifest.refs
        )
        if sealed_identities != required_identities:
            problems.append(
                "seal references differ from controller required-reference manifest"
            )

    body = _seal_body(
        seal.schema,
        seal.run_id,
        seal.sealed_at_utc,
        seal.refs,
        seal.required_manifest_id,
        seal.required_manifest_sha256,
    )
    if hashlib.sha256(canonical_json(body)).hexdigest() != seal.seal_sha256:
        problems.append("seal digest does not match its own contents")

    verdict = SealVerdict.SEALED
    reason = f"{len(rows)} reference(s) unchanged since seal"
    if problems:
        verdict = SealVerdict.MALFORMED
        reason = problems[0]
    else:
        for level in _ORDER:
            hits = [row for row in rows if row.verdict is level]
            if hits:
                verdict = level
                reason = f"{hits[0].ref.route}:{hits[0].ref.ref}: {hits[0].reason}"
                break

    return SealVerification(
        schema="constraintbox.seal-verification.v1",
        run_id=seal.run_id,
        verdict=verdict,
        reason=reason,
        refs=rows,
    )
