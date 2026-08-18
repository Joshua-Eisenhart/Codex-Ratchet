#!/usr/bin/env python3
"""Emit a deterministic host-hook installation plan without writing files.

The plan is intentionally the only installer surface in this candidate.  It
reports the bindings and template placements a human may review later; it
never reads, creates, edits, or replaces a host configuration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


HOOKS = Path(__file__).resolve().parent
TEMPLATES = HOOKS / "templates"
HOSTS = ("codex", "claude", "grok", "hermes")
SCHEMA = "constraintbox.integrated.host-hook-install-plan.v1"
BOOTSTRAP_PYTHON = "/usr/bin/python3"
CANONICAL_EVENT_LOG = Path("integrated_system") / "runs" / "hook-events.jsonl"


def _path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    return Path(value).expanduser().absolute()


def _canonical_member(path: Path) -> Path:
    lexical = Path(os.path.abspath(str(path)))
    return lexical.parent.resolve(strict=False) / lexical.name


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.resolve().open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_native_interpreter(path: Path) -> bool:
    try:
        with path.resolve().open("rb") as stream:
            magic = stream.read(4)
    except OSError:
        return False
    return magic in {
        b"\xfe\xed\xfa\xce",
        b"\xce\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
        b"\xcf\xfa\xed\xfe",
        b"\x7fELF",
    }


def _has_path_traversal(path: str | Path) -> bool:
    return ".." in Path(str(path)).parts


def _source_parent_custody(source: Path, root: Path) -> str | None:
    current = Path(os.path.abspath(str(root)))
    for component in ("integrated_system", "hooks"):
        current = current / component
        if current.is_symlink():
            return "HOLD_CB_HOOK_SOURCE_PARENT_SYMLINK"
        if current.exists() and not current.is_dir():
            return "HOLD_CB_HOOK_SOURCE_PARENT_NOT_DIRECTORY"
    return None


def _light_venv_binding(
    light: Path,
    root: Path,
    *,
    raw_root: Path | None = None,
) -> dict[str, Any]:
    if _has_path_traversal(light):
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_INTERPRETER_PATH_TRAVERSAL"}
    lexical_root = Path(os.path.abspath(str(root)))
    raw_light = Path(os.path.abspath(str(light)))
    raw_root_abs = Path(os.path.abspath(str(raw_root))) if raw_root is not None else lexical_root
    try:
        lexical_light = lexical_root / raw_light.relative_to(raw_root_abs)
    except ValueError:
        lexical_light = _canonical_member(light)
    if not lexical_light.is_file() or not os.access(lexical_light, os.X_OK):
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_INTERPRETER_MISSING"}
    try:
        lexical_light.relative_to(lexical_root)
    except ValueError:
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_INTERPRETER_OUTSIDE_PRODUCT"}
    if lexical_light.parent.name != "bin":
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_INTERPRETER_NOT_VENV_ENTRYPOINT"}
    venv_root = lexical_light.parent.parent
    if venv_root == lexical_root:
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_VENV_OUTSIDE_PRODUCT"}
    if not _under(venv_root, lexical_root):
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_VENV_ESCAPED"}
    cfg = venv_root / "pyvenv.cfg"
    if _has_path_traversal(cfg) or cfg.is_symlink() or not cfg.is_file():
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_PYVENV_CONFIG_INVALID"}
    if not _under(cfg, lexical_root):
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_PYVENV_CONFIG_ESCAPED"}
    target = lexical_light.resolve()
    if not _is_native_interpreter(target):
        return {"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_INTERPRETER_NOT_NATIVE"}
    return {
        "status": "PASS",
        "venv_root": str(venv_root),
        "venv_root_resolved": str(venv_root.resolve()),
        "pyvenv_cfg": str(cfg),
        "pyvenv_cfg_resolved": str(cfg.resolve()),
        "pyvenv_cfg_sha256": _sha256_file(cfg),
        "light_interpreter_lexical": str(lexical_light),
        "light_interpreter_resolved": str(target),
        "light_interpreter_sha256": _sha256_file(target),
        "light_interpreter_target_sha256": _sha256_file(target),
        "light_interpreter_is_symlink": lexical_light.is_symlink(),
    }


def build_plan(
    *,
    product_root: str | Path | None = None,
    light_interpreter: str | Path | None = None,
    target_root: str | Path | None = None,
    hook_source: str | Path | None = None,
) -> dict[str, Any]:
    """Build a plan whose rows describe intended changes but perform none."""

    root_input = _path(product_root or os.environ.get("CB_PRODUCT_ROOT"))
    root = root_input.resolve(strict=False) if root_input is not None else None
    light = _path(
        light_interpreter
        or os.environ.get("CB_LIGHT_PYTHON")
        or os.environ.get("CB_LIGHT_INTERPRETER")
    )
    target = _path(target_root or os.environ.get("CB_HOOK_PLAN_TARGET") or Path.home())
    source_input = _path(hook_source or os.environ.get("CB_HOOK_SOURCE") or TEMPLATES.parent / "portable_host_hook.py")
    source = _canonical_member(source_input) if source_input is not None else None
    raw_expected_source = (
        Path(os.path.abspath(str(root_input)))
        / "integrated_system"
        / "hooks"
        / "portable_host_hook.py"
        if root_input is not None
        else None
    )
    expected_source = (
        root / "integrated_system" / "hooks" / "portable_host_hook.py"
        if root is not None
        else None
    )
    event_log = root / CANONICAL_EVENT_LOG if root is not None else None
    checks: list[dict[str, Any]] = []
    if root_input is not None and _has_path_traversal(root_input):
        checks.append({"status": "HOLD", "reason_code": "HOLD_CB_PRODUCT_ROOT_PATH_TRAVERSAL"})
    elif root is None:
        checks.append({"status": "HOLD", "reason_code": "HOLD_CB_PRODUCT_ROOT_REQUIRED"})
    elif not root.is_dir():
        checks.append(
            {
                "status": "HOLD",
                "reason_code": "HOLD_CB_PRODUCT_ROOT_MISSING",
                "product_root": str(root),
            }
        )
    if light is None:
        checks.append({"status": "HOLD", "reason_code": "HOLD_CB_LIGHT_INTERPRETER_REQUIRED"})
    else:
        light_binding = _light_venv_binding(light, root, raw_root=root_input) if root is not None else {
            "status": "HOLD",
            "reason_code": "HOLD_CB_PRODUCT_ROOT_REQUIRED",
        }
        if light_binding["status"] != "PASS":
            checks.append(
                {
                    "status": "HOLD",
                    "reason_code": light_binding["reason_code"],
                    "light_interpreter": str(light),
                }
            )
    if source_input is not None and _has_path_traversal(source_input):
        checks.append(
            {
                "status": "HOLD",
                "reason_code": "HOLD_CB_HOOK_SOURCE_PATH_TRAVERSAL",
                "hook_source": str(source_input),
            }
        )
    elif source_input is not None and raw_expected_source is not None and Path(os.path.abspath(str(source_input))) != raw_expected_source:
        checks.append(
            {
                "status": "HOLD",
                "reason_code": "HOLD_CB_HOOK_SOURCE_PATH_MISMATCH",
                "hook_source": str(source_input),
                "expected_hook_source": str(raw_expected_source),
            }
        )
    elif source_input is not None and root_input is not None and _source_parent_custody(source_input, root_input):
        checks.append(
            {
                "status": "HOLD",
                "reason_code": _source_parent_custody(source_input, root_input),
                "hook_source": str(source_input),
            }
        )
    elif source_input is not None and source_input.is_symlink():
        checks.append(
            {
                "status": "HOLD",
                "reason_code": "HOLD_CB_HOOK_SOURCE_SYMLINK",
                "hook_source": str(source_input),
            }
        )
    elif source is None or not source.is_file():
        checks.append(
            {
                "status": "HOLD",
                "reason_code": "HOLD_CB_HOOK_SOURCE_NOT_REGULAR",
                "hook_source": str(source) if source is not None else None,
            }
        )
    elif os.lstat(source_input).st_nlink != 1:
        checks.append(
            {
                "status": "HOLD",
                "reason_code": "HOLD_CB_HOOK_SOURCE_MULTILINK",
                "hook_source": str(source_input),
            }
        )
    elif expected_source is not None and source != expected_source:
        checks.append(
            {
                "status": "HOLD",
                "reason_code": "HOLD_CB_HOOK_SOURCE_PATH_MISMATCH",
                "hook_source": str(source),
                "expected_hook_source": str(expected_source),
            }
        )
    if target is None:
        checks.append({"status": "HOLD", "reason_code": "HOLD_PLAN_TARGET_REQUIRED"})
    if not Path(BOOTSTRAP_PYTHON).is_file() or not os.access(BOOTSTRAP_PYTHON, os.X_OK):
        checks.append(
            {
                "status": "HOLD",
                "reason_code": "HOLD_CB_HOOK_BOOTSTRAP_INTERPRETER_MISSING",
                "bootstrap_interpreter": BOOTSTRAP_PYTHON,
            }
        )

    status = "DRY_RUN" if not checks else "HOLD"
    changes: list[dict[str, Any]] = []
    if status == "DRY_RUN":
        assert root is not None and light is not None and target is not None and source is not None
        light_binding = _light_venv_binding(light, root, raw_root=root_input)
        light_digest = light_binding["light_interpreter_sha256"]
        source_digest = _sha256_file(source)
        # A generic target shape keeps this plan independent of any particular
        # host's home layout.  It is a review artifact, not a write command.
        for host in HOSTS:
            template = TEMPLATES / host / "hook.sh"
            changes.append(
                {
                    "action": "WOULD_INSTALL_TEMPLATE",
                    "host": host,
                    "source": str(template),
                    "target": str(target / "constraintbox-hooks" / host / "hook.sh"),
                    "command": f'"${{CB_HOOK_ROOT}}/cb_hook.sh" {host}',
                }
            )
        changes.append(
            {
                "action": "WOULD_BIND_RUNTIME",
                "target": str(target / "constraintbox-hooks" / "binding.json"),
                "binding": {
                    "CB_PRODUCT_ROOT": str(root),
                    "CB_LIGHT_PYTHON": str(light),
                    "CB_HOOK_EVENT_LOG": str(event_log),
                    "CB_HOOK_SOURCE": str(source),
                    "CB_HOOK_BOOTSTRAP_PYTHON": BOOTSTRAP_PYTHON,
                    "CB_LIGHT_PYTHON_SHA256": light_digest,
                    "CB_HOOK_SOURCE_SHA256": source_digest,
                    "CB_PYVENV_CFG": light_binding["pyvenv_cfg"],
                    "CB_PYVENV_CFG_SHA256": light_binding["pyvenv_cfg_sha256"],
                },
            }
        )
        changes.append(
            {
                "action": "WOULD_BIND_EVENT_LOG",
                "target": str(event_log),
                "binding": {"CB_HOOK_EVENT_LOG": str(event_log)},
                "confined_under": str(root),
            }
        )
    return {
        "schema": SCHEMA,
        "status": status,
        "dry_run": True,
        "mutates": False,
        "promotion_allowed": False,
        "product_root": str(root) if root is not None else None,
        "light_interpreter": str(light) if light is not None else None,
        "light_interpreter_sha256": light_digest if status == "DRY_RUN" else None,
        "light_interpreter_resolved": (
            light_binding["light_interpreter_resolved"] if status == "DRY_RUN" else None
        ),
        "hook_source": str(source) if source is not None else None,
        "hook_source_sha256": source_digest if status == "DRY_RUN" else None,
        "pyvenv_cfg": light_binding["pyvenv_cfg"] if status == "DRY_RUN" else None,
        "pyvenv_cfg_sha256": light_binding["pyvenv_cfg_sha256"] if status == "DRY_RUN" else None,
        "bootstrap_interpreter": BOOTSTRAP_PYTHON,
        "target_root": str(target) if target is not None else None,
        "event_log": str(event_log) if event_log is not None else None,
        "checks": checks,
        "changes": changes,
        "planned_changes": changes,
        "claim_ceiling": "plan_only;no_host_configuration_mutation;no_activation",
    }


# Descriptive aliases for callers that treat this as a plan-only installer
# API.  Both names return the same immutable-in-practice JSON-shaped mapping.
plan = build_plan
dry_run_install = build_plan


def _legacy_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-root", default=None)
    parser.add_argument("--light-interpreter", default=None)
    parser.add_argument("--target-root", default=None)
    parser.add_argument("--hook-source", default=None)
    args = parser.parse_args(argv)
    result = build_plan(
        product_root=args.product_root,
        light_interpreter=args.light_interpreter,
        target_root=args.target_root,
        hook_source=args.hook_source,
    )
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if result["status"] == "DRY_RUN" else 2


# The original ``install_plan.py`` API remains available for existing callers,
# while the contained installer adds explicit plan/apply/verify/rollback
# modes.  Importing this sibling does not import the provider or hook runtime.
try:
    from host_hook_installer import (  # noqa: E402
        InstallerError,
        apply_install,
        main as installer_main,
        plan_install,
        rollback_install,
        verify_install,
    )
except ModuleNotFoundError:  # loaded by a fixture through spec_from_file_location
    import importlib.util

    _installer_path = Path(__file__).with_name("host_hook_installer.py")
    _installer_spec = importlib.util.spec_from_file_location(
        "integrated_host_hook_installer", _installer_path
    )
    if _installer_spec is None or _installer_spec.loader is None:
        raise
    _installer_module = importlib.util.module_from_spec(_installer_spec)
    sys.modules[_installer_spec.name] = _installer_module
    _installer_spec.loader.exec_module(_installer_module)
    InstallerError = _installer_module.InstallerError
    apply_install = _installer_module.apply_install
    installer_main = _installer_module.main
    plan_install = _installer_module.plan_install
    rollback_install = _installer_module.rollback_install
    verify_install = _installer_module.verify_install

install = apply_install
apply = apply_install
verify = verify_install
rollback = rollback_install
contained_plan = plan_install


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if (values and values[0] in {"plan", "apply", "verify", "rollback"}) or "--mode" in values:
        return installer_main(values)
    return _legacy_main(values)


if __name__ == "__main__":
    raise SystemExit(main())
