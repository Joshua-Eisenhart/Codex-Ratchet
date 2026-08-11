#!/usr/bin/env python3
"""Structured, contained CLI for the CB Light install and evidence lifecycle."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
# This broker's source path is the authoritative checkout identity.  Bind it
# before importing the installed wheel: when the command is invoked outside
# the checkout, ``hookkernel.cb_light_runtime`` must not fall back to its
# site-packages location and derive a nonexistent ``.venv`` below it.
os.environ["CB_LIGHT_ROOT"] = str(ROOT)
if str(ROOT) not in sys.path:
    # ``hookkernel`` must resolve from the contained Light wheel; the checkout
    # is appended only to make the hook wrapper importable under ``python -I``.
    sys.path.append(str(ROOT))

from hooks.cb_light_hook import (  # noqa: E402
    CLEAN_INSTALL_REPORT,
    CLEAN_RECEIPT,
    HookRefusal,
    LOCK,
    MANIFEST,
    MANDATED_INTERPRETER,
    RUNTIME_INSTALL_REPORT,
    lifecycle_lock,
    refresh,
    verify_completion_state,
    verify_evaluation,
    verify_manifest,
)


# A freshly created Python 3.13 venv may contain pip but not setuptools.  Use
# its base interpreter only to build the local Light wheel; the wheel is then
# installed and exercised solely by the contained interpreter.
BUILD_INTERPRETER = pathlib.Path(
    getattr(sys, "_base_executable", None) or sys.executable
).resolve()
CLEAN_RUNTIME = ROOT / ".venv-clean"


def _venv_python(
    venv_root: pathlib.Path, *, platform_name: str | None = None
) -> pathlib.Path:
    """Return a venv launcher without assuming a POSIX layout.

    The current manifest still records its supported macOS profile separately.
    This helper only keeps broker-created transient environments from baking
    the POSIX ``bin/python`` spelling into lifecycle execution.
    """

    if (platform_name or os.name) == "nt":
        return venv_root / "Scripts" / "python.exe"
    return venv_root / "bin" / "python"


def _create_venv(target: pathlib.Path) -> int:
    """Create a lifecycle venv from the base builder, never site-packages."""

    completed = subprocess.run(
        [str(BUILD_INTERPRETER), "-m", "venv", "--clear", str(target)],
        cwd=ROOT,
        check=False,
    )
    return completed.returncode


def _remove_generated_light_build_products() -> None:
    """Keep local setuptools output out of the authoritative Light sources."""

    project = ROOT / "light_runtime"
    for path in (project / "build", project / "constraintbox.egg-info"):
        if path.is_dir():
            shutil.rmtree(path)


def _print_command_refusal(command: str, refusal: HookRefusal) -> int:
    """Render a lock/gate refusal as machine-readable fail-closed output."""

    print(
        json.dumps(
            {
                "schema": "constraintbox.cb-light-command-refusal.v1",
                "command": command,
                "disposition": "HOLD",
                "evaluation_allowed": False,
                "completion_allowed": False,
                "reason_code": refusal.reason_code,
                "detail": refusal.detail,
            },
            sort_keys=True,
        )
    )
    return 2


def _rebuild_manifest_under_lifecycle_lock() -> int:
    """Compile the source contract only as an explicit brokered transition.

    A normal install refuses a stale manifest.  A developer who intentionally
    changed contained Light source must opt in to this transition so the
    manifest writer is serialized with the subsequent wheel build and receipt
    refresh instead of being an unlocked side command.
    """

    completed = subprocess.run(
        [
            str(BUILD_INTERPRETER),
            "-I",
            str(ROOT / "scripts/build_cb_light_manifest.py"),
            "--root",
            str(ROOT),
            "--output",
            str(MANIFEST),
        ],
        cwd=ROOT,
        check=False,
    )
    return completed.returncode


def install(*, rebuild_manifest: bool = False) -> int:
    with lifecycle_lock():
        if rebuild_manifest:
            rebuilt = _rebuild_manifest_under_lifecycle_lock()
            if rebuilt != 0:
                return rebuilt
        return _install()


def _install() -> int:
    verify_manifest()
    (ROOT / "receipts").mkdir(parents=True, exist_ok=True)
    created_runtime = _create_venv(ROOT / ".venv")
    if created_runtime != 0:
        return created_runtime
    completed = subprocess.run(
        [
            str(MANDATED_INTERPRETER),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--quiet",
            "--isolated",
            "--no-input",
            "--report",
            str(RUNTIME_INSTALL_REPORT),
            "--requirement",
            str(LOCK),
        ],
        cwd=REPO,
        check=False,
    )
    if completed.returncode != 0:
        return completed.returncode
    # Build the Light-only wheel with the bootstrap interpreter, then install
    # that wheel into the contained runtime.  The fresh venv intentionally has
    # no setuptools build backend, and an editable install would point back at
    # the mixed legacy source tree.  A wheel makes the executable package
    # surface independently inspectable and excludes CB Heavy modules.
    # Remove stale setuptools metadata *before* discovery as well: an old
    # ``SOURCES.txt`` can reintroduce a deleted legacy module into a new wheel.
    _remove_generated_light_build_products()
    with tempfile.TemporaryDirectory(prefix="cb-light-wheel-") as wheel_dir:
        wheel_build = subprocess.run(
            [
                str(BUILD_INTERPRETER),
                "-m",
                "pip",
                "wheel",
                "--disable-pip-version-check",
                "--quiet",
                "--no-input",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                wheel_dir,
                str(ROOT / "light_runtime"),
            ],
            cwd=ROOT,
            check=False,
        )
        if wheel_build.returncode != 0:
            return wheel_build.returncode
        wheels = sorted(pathlib.Path(wheel_dir).glob("constraintbox-*.whl"))
        if len(wheels) != 1:
            return 2
        controller_install = subprocess.run(
            [
                str(MANDATED_INTERPRETER),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--quiet",
                "--isolated",
                "--no-input",
                "--no-deps",
                "--force-reinstall",
                str(wheels[0]),
            ],
            cwd=ROOT,
            check=False,
        )
        if controller_install.returncode != 0:
            return controller_install.returncode
    _remove_generated_light_build_products()
    # Abort before spending time on the clean 91-root environment if a source
    # writer moved the manifest target while the wheel was being assembled.
    # The later refresh repeats this check after all probes as a second race
    # negative, but this one makes the failure early and cheap.
    verify_manifest()
    # Keep the clean candidate environment separate *and persistent*.  A
    # deleted TemporaryDirectory can leave a receipt that appears complete
    # until a later verifier tries to replay or inspect its stated prefix.
    created = _create_venv(CLEAN_RUNTIME)
    if created != 0:
        return created
    clean_python = _venv_python(CLEAN_RUNTIME)
    clean_install = subprocess.run(
        [
            str(clean_python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--quiet",
            "--isolated",
            "--no-input",
            "--report",
            str(CLEAN_INSTALL_REPORT),
            "--requirement",
            str(LOCK),
        ],
        cwd=ROOT,
        check=False,
    )
    if clean_install.returncode != 0:
        return clean_install.returncode
    clean_probe = subprocess.run(
        [
            str(clean_python),
            "-I",
            str(ROOT / "scripts/cb_light_install_probe.py"),
            "--manifest",
            str(ROOT / "config/cb_light_tools_v1.json"),
            "--output",
            str(CLEAN_RECEIPT),
            "--environment-role",
            "clean",
            "--expected-python",
            str(clean_python),
            "--install-report",
            str(CLEAN_INSTALL_REPORT),
            "--quiet",
        ],
        cwd=ROOT,
        check=False,
    )
    if clean_probe.returncode != 0:
        return clean_probe.returncode
    body = refresh(lock_held=True)
    print(
        json.dumps(
            {
                "schema": "constraintbox.cb-light-broker-install.v1",
                "evaluation_allowed": body["evaluation_allowed"],
                "completion_allowed": False,
                "system_completion_reason": body["system_completion_reason"],
                "selection_counts": body["selection_counts"],
                "hook_receipt": str(ROOT / "receipts/cb_light_hook_run_v1.json"),
                "promotion_allowed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if body["evaluation_allowed"] else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cb-light")
    parser.add_argument("command", choices=("install", "refresh", "status", "complete", "list"))
    parser.add_argument(
        "--rebuild-manifest",
        action="store_true",
        help=(
            "compile the current contained-Light source contract under the "
            "install lifecycle lock before building the wheel"
        ),
    )
    args = parser.parse_args(argv)
    if args.rebuild_manifest and args.command != "install":
        parser.error("--rebuild-manifest is valid only with install")
    if args.command == "install":
        try:
            return install(rebuild_manifest=args.rebuild_manifest)
        except HookRefusal as exc:
            return _print_command_refusal(args.command, exc)
    if args.command == "refresh":
        try:
            body = refresh()
        except HookRefusal as exc:
            return _print_command_refusal(args.command, exc)
        print(json.dumps(body, indent=2, sort_keys=True))
        return 0 if body["evaluation_allowed"] else 2
    if args.command == "status":
        allowed, reason = verify_evaluation(require_live_boundary=True)
        print(
            json.dumps(
                {
                    "completion_allowed": False,
                    "evaluation_allowed": allowed,
                    "reason_code": reason,
                    "system_completion_reason": (
                        "LOCAL_CB_LIGHT_EVALUATION_DOES_NOT_EARN_SYSTEM_COMPLETION"
                    ),
                },
                sort_keys=True,
            )
        )
        return 0 if allowed else 1
    if args.command == "complete":
        (
            allowed,
            reason,
            evaluation_allowed,
            evaluation_reason,
        ) = verify_completion_state(require_live_boundary=True)
        print(
            json.dumps(
                {
                    "completion_allowed": allowed,
                    "evaluation_allowed": evaluation_allowed,
                    "evaluation_reason_code": evaluation_reason,
                    "reason_code": reason,
                },
                sort_keys=True,
            )
        )
        return 0 if allowed else 2
    manifest = verify_manifest()
    for index, row in enumerate(manifest["tools"], start=1):
        print(
            f"{index:02d}\t{row['distribution']}=={row['locked_version']}\t"
            f"{row['source_group']}\t{row['role_class']}\t{row['role']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
