from __future__ import annotations

import hashlib
import importlib.metadata
import stat
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuntimeArtifactPin:
    relative_path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class DistributionRuntimePin:
    distribution: str
    version: str
    module_artifact: str
    artifacts: tuple[RuntimeArtifactPin, ...]


class RuntimeIdentityError(RuntimeError):
    pass


def _sha256_sized_file(path: Path, expected_size: int) -> str:
    try:
        metadata = path.stat()
    except OSError as exc:
        raise RuntimeIdentityError(f"runtime artifact unavailable: {path}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise RuntimeIdentityError(f"runtime artifact is not a regular file: {path}")
    if metadata.st_size != expected_size:
        raise RuntimeIdentityError(
            f"runtime artifact size drift for {path}: "
            f"expected {expected_size}, observed {metadata.st_size}"
        )
    digest = hashlib.sha256()
    observed = 0
    try:
        with path.open("rb") as stream:
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                observed += len(block)
                if observed > expected_size:
                    raise RuntimeIdentityError(
                        f"runtime artifact grew during hashing: {path}"
                    )
                digest.update(block)
    except OSError as exc:
        raise RuntimeIdentityError(f"runtime artifact unreadable: {path}") from exc
    if observed != expected_size:
        raise RuntimeIdentityError(
            f"runtime artifact changed during hashing: {path}"
        )
    return digest.hexdigest()


def verify_distribution_runtime(
    module: types.ModuleType,
    pin: DistributionRuntimePin,
) -> dict[str, Any]:
    """Verify one imported module against fixed installed-distribution bytes."""

    if not isinstance(module, types.ModuleType):
        raise RuntimeIdentityError("imported runtime object is not a module")
    try:
        distribution = importlib.metadata.distribution(pin.distribution)
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeIdentityError(
            f"distribution metadata unavailable: {pin.distribution}"
        ) from exc
    except Exception as exc:
        raise RuntimeIdentityError(
            f"distribution metadata inspection failed: {pin.distribution}"
        ) from exc
    if distribution.version != pin.version:
        raise RuntimeIdentityError(
            f"distribution version drift for {pin.distribution}: "
            f"expected {pin.version}, observed {distribution.version}"
        )
    distribution_files = distribution.files
    if distribution_files is None:
        raise RuntimeIdentityError(
            f"distribution file inventory unavailable: {pin.distribution}"
        )
    file_map = {str(item): item for item in distribution_files}
    if len(file_map) != len(distribution_files):
        raise RuntimeIdentityError(
            f"distribution file inventory is ambiguous: {pin.distribution}"
        )

    artifacts: dict[str, dict[str, Any]] = {}
    for artifact in pin.artifacts:
        inventory_path = file_map.get(artifact.relative_path)
        if inventory_path is None:
            raise RuntimeIdentityError(
                f"pinned runtime artifact missing from distribution inventory: "
                f"{artifact.relative_path}"
            )
        path = Path(distribution.locate_file(inventory_path)).resolve()
        observed_sha256 = _sha256_sized_file(path, artifact.size_bytes)
        if observed_sha256 != artifact.sha256:
            raise RuntimeIdentityError(
                f"runtime artifact digest drift: {artifact.relative_path}"
            )
        artifacts[artifact.relative_path] = {
            "path": str(path),
            "size_bytes": artifact.size_bytes,
            "sha256": observed_sha256,
        }

    module_artifact = artifacts.get(pin.module_artifact)
    if module_artifact is None:
        raise RuntimeIdentityError(
            "module artifact must be present in the pinned artifact set"
        )
    try:
        module_path = Path(module.__file__).resolve()
        spec_origin = Path(module.__spec__.origin).resolve()
    except (AttributeError, OSError, TypeError) as exc:
        raise RuntimeIdentityError("imported module origin is unavailable") from exc
    expected_module_path = Path(module_artifact["path"])
    if module_path != expected_module_path or spec_origin != expected_module_path:
        raise RuntimeIdentityError(
            "imported module origin differs from the pinned distribution artifact"
        )

    return {
        "distribution": pin.distribution,
        "version": distribution.version,
        "module_origin": str(module_path),
        "artifacts": artifacts,
    }
