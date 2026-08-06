#!/usr/bin/env python3
"""Build a deterministic, source-contained ConstraintBox core ZIP.

The archive intentionally contains the CB core and its local resources, not
CPython, native dependencies, credentials, or the external simulation estate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_VERSION = "0.3.5"
TOP_LEVEL = f"constraintbox-core-{PACKAGE_VERSION}"
MANIFEST_SCHEMA = "constraintbox.contained-core-manifest.v1"

# Source/support closure.  No parent-repository or external-estate path belongs
# here: those workloads must be declared and validated independently.
INCLUDED_DIRECTORIES = (
    "src",
    "config",
    "mmm",
    "fixtures",
    "formal",
    "workers",
    "external_capabilities",
    "claimgate_plugin",
    "docs",
    "doctrine",
    "requirements",
    "scripts",
    "tests",
)
INCLUDED_FILES = ("README.md", "pyproject.toml", "PROVENANCE.md", "00_SEED_STATUS.md")
EXCLUDED_PARTS = frozenset(
    {
        ".git",
        ".hypothesis",
        ".pytest_cache",
        ".DS_Store",
        ".AppleDouble",
        "__pycache__",
        "build",
        "dist",
        "constraintbox.egg-info",
        "receipts",
        "results",
    }
)
EXCLUDED_SUFFIXES = frozenset({".pyc", ".pyo"})
# These are mutable run artifacts, not core source.  Fixture-local evidence
# remains included because it is part of a declared adversarial test corpus.
EXCLUDED_RELATIVE_PATHS = frozenset(
    {
        "claimgate_plugin/failures.jsonl",
        "claimgate_plugin/admissions.jsonl",
    }
)
PRODUCT_BOUNDARY = """# ConstraintBox contained core source bundle

This archive contains the ConstraintBox source core, deterministic checking
resources, MMM/configuration inputs, the in-box ClaimGate chain, fixtures,
developer tests, and build/verification scripts.

It deliberately does **not** contain CPython, Python/native dependencies,
Node.js, Julia, GPU software, credentials, remote providers,
`external_sim_estate`, or the surrounding Codex-Ratchet checkout.  Those are
environmental or external-workload dependencies, not this product closure.

The core declares portable CPython 3.11, 3.12, and 3.13 runtime profiles in
`src/constraintbox/runtime_profiles/core_profiles_v1.json`.  A profile is a
version/API compatibility contract, not a path to the builder's interpreter.
The first verifier operation is therefore `constraintbox runtime verify` under
the interpreter that invoked the verifier.  It reports `ELIGIBLE`, `PARKED`,
or `BLOCKED`; it never chooses another interpreter, installs a dependency, or
turns a missing/incompatible library into a passing result.

The verifier runs only the declared core smoke surface: `demo`, MMM
compilation, a solver-aligned missing-assumptions gate, a typed exact symbolic
task, the source-only controller-origin/failure-repair refusal unit suite, a
fixed Mini-Lev proposal-flow topology unit that performs a real Rustworkx DAG
check, a strict foreign-Lev-eval observation unit, and a fixed historical-only
two-node Mini-Lev foreign-eval retention/replay unit, the controller-owned
Mini-Lev execution-lease unit suite, a receipt-bound Mini-Lev lease lifecycle
with an expiry control, an absent-external-estate park, and two
in-box ClaimGate fixtures, a contained public local-provider refusal path, and
offline static OpenRouter/NVIDIA proposal-route policy/transport tests. The topology and observation units use contained
fixtures to challenge CB's own deterministic contracts; they do not attest a
live Lev producer or a real simulation. The foreign-eval flow retains a
controller-bound historical path, persists a source-private binding record,
replays the retained bytes after source removal, and stops at `PARKED` even
when replay succeeds; foreign verdict/status never selects a CB terminal.
The contained Leviathan-reference unit tests the CB-native reference flow, its
strict named-flow observer, and rejection of proof-bearing/non-dry-run seal
variants using local fixtures only. It never requires, packages, or invokes a
Lev runtime, provider, model, or FlowMind evaluator.
The lease suite proves only the
contained lifecycle around a fixed hook: acquire, pre-hook verification,
invoke, post-hook verification, and release or `HOLD`. The receipt-bound
control is driven by fixed controller-derived receipt hashes and proves that
the exact-TTL boundary prevents a positive terminal after the hook ran. It has
no live provider
and is not an OS sandbox or a general agent-lease claim. The broader
controller-flow fault-injection test requires the separate estate and is not a
contained-core smoke operation. One ClaimGate fixture is admitted by its
declared local policy; the other stops at insufficient depth. Neither result
authorizes promotion.

External simulation-engine runtime dependencies, their broad estate, and their
operational receipts are intentionally outside this archive.  The source
archive may contain external-adapter code and fixtures so that its contracts
remain inspectable, but that code is not a packaged engine runtime and is not
part of the contained-core smoke claim.  Each adapter must retain its own
bounded receipt and must park or fail when its estate is absent.  It cannot be
replaced by import checks, NumPy-only work, or handwritten JSON that claims
another engine ran.

The opt-in `workers/attractor_basin_v1` validation source and its setup guide
are included under that same boundary.  JAX/Diffrax, Julia/Attractors, and
PyTorch/PyG remain external simulation engines.  The finite Z3/CVC5/CPython
checker is CB-owned gate machinery, not a fourth simulation engine.  The core
verifier checks only that this adapter is present, path-portable, and can expose
its CLI; it does not install or claim execution of the external engines.

The role boundary is explicit: `cb:*` denotes the contained controller,
formal-gate, Mini-LevOS, and adapter roles; `sim:*` denotes an external bounded
operation profile; and `evidence:*` denotes a receipt or index, never a
component.  A library name alone does not change its role.  The contained
source includes the deterministic typed boundary-contract gate and regression
fixtures, but it does not include the `sim:*` engine runtimes or their
operational receipts.

This product has no Java/TLC/Apalache requirement and does not invoke those
tools. A historical temporal adapter may be visible in the source tree, but it
is outside this product's execution surface and cannot block the contained core
or its local Python/Julia simulation bindings.

This is a source product and local verification boundary, not a self-contained
Python/native runtime, complete simulation-engine package, truth engine,
hostile-host containment boundary, or automatic LLM tuning loop.  LLMs remain
untrusted proposal/advisory inputs; they do not determine gate outcomes or
promotion.
"""


class BundleError(ValueError):
    """The source tree cannot form the declared contained-core artifact."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return (
        relative.as_posix() not in EXCLUDED_RELATIVE_PATHS
        and not any(part in EXCLUDED_PARTS for part in relative.parts)
        and path.suffix not in EXCLUDED_SUFFIXES
    )


def _payload_paths() -> list[Path]:
    paths: list[Path] = []
    for name in INCLUDED_FILES:
        path = ROOT / name
        if path.is_symlink():
            raise BundleError(f"symlink payload is not permitted: {name}")
        if not path.is_file():
            raise BundleError(f"required root file is missing: {name}")
        paths.append(path)
    for name in INCLUDED_DIRECTORIES:
        directory = ROOT / name
        if directory.is_symlink():
            raise BundleError(f"symlink source directory is not permitted: {name}")
        if not directory.is_dir():
            raise BundleError(f"required resource directory is missing: {name}")
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise BundleError(
                    "symlink payload is not permitted: "
                    f"{path.relative_to(ROOT).as_posix()}"
                )
            if path.is_file() and _include(path):
                paths.append(path)
    by_name = {path.relative_to(ROOT).as_posix(): path for path in paths}
    return [by_name[name] for name in sorted(by_name)]


def _manifest(paths: list[Path]) -> dict[str, Any]:
    files = []
    for path in paths:
        payload = path.read_bytes()
        files.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": len(payload),
                "sha256": _sha256(payload),
            }
        )
    return {
        "schema": MANIFEST_SCHEMA,
        "bundle_kind": "contained-core-source",
        "package_name": "constraintbox",
        "package_version": PACKAGE_VERSION,
        "top_level": TOP_LEVEL,
        "source_root": "constraint_box",
        "file_count": len(files),
        "files": files,
        "included_directories": list(INCLUDED_DIRECTORIES),
        "excluded_parts": sorted(EXCLUDED_PARTS),
        "external_estate_included": False,
        "promotion_allowed": False,
    }


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    return info


def build_bundle(output: Path) -> dict[str, Any]:
    """Write a new ZIP once; never silently replace an existing artifact."""

    if output.exists():
        raise BundleError(f"refusing to overwrite existing output: {output}")
    paths = _payload_paths()
    manifest = _manifest(paths)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=True,
        ) as archive:
            for path in paths:
                member = f"{TOP_LEVEL}/constraint_box/{path.relative_to(ROOT).as_posix()}"
                archive.writestr(_zip_info(member), path.read_bytes())
            archive.writestr(
                _zip_info(f"{TOP_LEVEL}/CONTAINMENT_MANIFEST.json"),
                json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n",
            )
            archive.writestr(
                _zip_info(f"{TOP_LEVEL}/PRODUCT_BOUNDARY.md"),
                PRODUCT_BOUNDARY.encode("utf-8"),
            )
        temporary.replace(output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return {
        "schema": "constraintbox.contained-core-build.v1",
        "bundle": str(output),
        "bundle_sha256": _sha256(output.read_bytes()),
        "bundle_bytes": output.stat().st_size,
        "manifest_file_count": manifest["file_count"],
        "external_estate_included": False,
        "promotion_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = build_bundle(args.output.resolve())
    except (BundleError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({"schema": "constraintbox.contained-core-build.v1", "state": "FAILED", "error": str(exc), "promotion_allowed": False}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
