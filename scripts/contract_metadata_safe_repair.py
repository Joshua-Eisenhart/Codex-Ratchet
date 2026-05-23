#!/usr/bin/env python3
"""Apply conservative contract metadata repairs to sim probes.

This is intentionally narrower than the generated proposal reports:

* C1 classification is repaired only when the source already contains a
  compatible classical-baseline signal, either in emitted result literals or an
  explicit prose marker such as "classified as classical_baseline". All
  non-baseline signals stay blocked for review.
* C2/C3 tool metadata is repaired with conservative supportive roles from
  imports; it does not promote tools to load-bearing unless the file already
  says so elsewhere.
* C4 divergence logs are added only after a classical_baseline classification
  is already present or safely inferred.

The script produces a dry-run report by default. Use --apply to edit files.
"""

from __future__ import annotations

import argparse
import ast
import json
import pprint
import re
from pathlib import Path
from typing import Any

import adaptive_controller
import lint_sim_contract


ROOT = Path(__file__).resolve().parents[1]
PROBES = ROOT / "system_v4/probes"
OUT_PATH = ROOT / "system_v5/ops/contract_metadata_safe_repair_preview.json"
VALID_CLASSIFICATIONS = lint_sim_contract.VALID_CLASSIFICATIONS
BASELINE_CLASSIFICATIONS = {"classical_baseline"}

DOC_CLASSIFICATION_RE = re.compile(
    r"(?:classified\s+as|classification)\s*(?:=|:|as)?\s*`?['\"]?"
    r"(classical_baseline|canonical|formal_scout|tool_lego_fit_probe|diagnostic_only|supporting)"
    r"`?['\"]?",
    re.IGNORECASE,
)

IMPORT_TOOL_ALIASES = {
    "torch": "pytorch",
    "torch_geometric": "pyg",
    "z3": "z3",
    "cvc5": "cvc5",
    "sympy": "sympy",
    "clifford": "clifford",
    "geomstats": "geomstats",
    "e3nn": "e3nn",
    "xgi": "xgi",
    "toponetx": "toponetx",
    "gudhi": "gudhi",
    "rustworkx": "rustworkx",
    "networkx": "networkx",
    "numpy": "numpy",
}
REPAIR_SENTINEL = "safe_repair_v1"


def parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def source_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def module_docstring(tree: ast.Module) -> str:
    return ast.get_docstring(tree) or ""


def emitted_classifications(tree: ast.Module) -> set[str]:
    values: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if not (isinstance(key, ast.Constant) and key.value == "classification"):
                continue
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                values.add(value.value)
    return {value for value in values if value in VALID_CLASSIFICATIONS}


def infer_classification(tree: ast.Module) -> tuple[str | None, str | None]:
    emitted = emitted_classifications(tree)
    if len(emitted) == 1:
        return next(iter(emitted)), "single_emitted_result_literal"
    doc = module_docstring(tree)
    match = DOC_CLASSIFICATION_RE.search(doc)
    if match:
        return match.group(1), "explicit_docstring_classification"
    return None, None


def imported_tool_aliases(tree: ast.Module) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                tool = IMPORT_TOOL_ALIASES.get(root)
                if tool:
                    aliases.setdefault(tool, set()).add(alias.asname or root)
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            tool = IMPORT_TOOL_ALIASES.get(root)
            if tool:
                for alias in node.names:
                    aliases.setdefault(tool, set()).add(alias.asname or alias.name)
    return aliases


def called_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            value = func.value
            while isinstance(value, ast.Attribute):
                value = value.value
            if isinstance(value, ast.Name):
                names.add(value.id)
    return names


def imported_tools(tree: ast.Module) -> set[str]:
    return set(imported_tool_aliases(tree))


def existing_manifest(assigns: dict[str, Any]) -> dict[str, Any]:
    value = assigns.get("TOOL_MANIFEST")
    return value if isinstance(value, dict) else {}


def existing_depth(assigns: dict[str, Any]) -> dict[str, Any]:
    value = assigns.get("TOOL_INTEGRATION_DEPTH")
    return value if isinstance(value, dict) else {}


def insertion_index(text: str, tree: ast.Module) -> int:
    lines = text.splitlines(keepends=True)
    insert_after = 0
    if lines and lines[0].startswith("#!"):
        insert_after = 1
    if (
        len(lines) > insert_after
        and re.match(r"#.*coding[:=]\s*[-\w.]+", lines[insert_after])
    ):
        insert_after += 1
    if tree.body:
        first = tree.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            insert_after = max(insert_after, getattr(first, "end_lineno", first.lineno))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            insert_after = max(insert_after, getattr(node, "end_lineno", node.lineno))
    return sum(len(line) for line in lines[:insert_after])


def metadata_block(actions: list[dict[str, Any]]) -> str:
    lines = [
        "",
        "# ---------------------------------------------------------------------",
        "# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.",
        f"contract_metadata_repair = {REPAIR_SENTINEL!r}",
    ]
    for action in actions:
        kind = action["kind"]
        if kind == "classification":
            lines.append(f"classification = {action['value']!r}")
        elif kind == "tool_manifest":
            lines.append(f"TOOL_MANIFEST = {pprint.pformat(action['value'], width=100)}")
        elif kind == "tool_depth":
            lines.append(f"TOOL_INTEGRATION_DEPTH = {pprint.pformat(action['value'], width=100)}")
        elif kind == "divergence_log":
            lines.append(f"divergence_log = {action['value']!r}")
            lines.append(f"divergence_log_source = {REPAIR_SENTINEL!r}")
    lines.append("")
    return "\n".join(lines)


def repair_plan(path: Path) -> dict[str, Any]:
    tree = parse(path)
    rel = str(path.relative_to(ROOT))
    if tree is None:
        return {"sim": rel, "actions": [], "blocked": ["parse_error"]}
    assigns = lint_sim_contract._module_level_assignments(tree)  # noqa: SLF001
    violations = lint_sim_contract.lint_sim(path)
    rules = {violation["rule"] for violation in violations}
    if assigns.get("contract_metadata_repair") == REPAIR_SENTINEL:
        return {
            "sim": rel,
            "rules": sorted(rules),
            "actions": [],
            "blocked": sorted(rules),
        }
    assigned_promoted = {
        key: value
        for key, value in lint_sim_contract._classification_assignments(assigns).items()  # noqa: SLF001
        if value != "classical_baseline"
    }
    if assigned_promoted:
        return {
            "sim": rel,
            "rules": sorted(rules),
            "actions": [],
            "blocked": ["assigned_promoted_classification_needs_review"],
            "assigned_classifications": assigned_promoted,
        }
    emitted_promoted = {
        value
        for value in lint_sim_contract._emitted_classification_literals(tree)  # noqa: SLF001
        if value != "classical_baseline"
    }
    if emitted_promoted:
        return {
            "sim": rel,
            "rules": sorted(rules),
            "actions": [],
            "blocked": ["emitted_promoted_classification_needs_review"],
            "emitted_classifications": sorted(emitted_promoted),
        }
    actions: list[dict[str, Any]] = []
    blocked: list[str] = []

    cls = lint_sim_contract._effective_classification(assigns)  # noqa: SLF001
    has_divergence_log = lint_sim_contract._has_nonempty_divergence_log(  # noqa: SLF001
        assigns.get("divergence_log")
    )
    inferred_cls = None
    inferred_reason = None
    if "C1_classification_missing" in rules:
        inferred_cls, inferred_reason = infer_classification(tree)
        if inferred_cls == "canonical":
            blocked.append("C1_canonical_needs_review")
        elif inferred_cls in BASELINE_CLASSIFICATIONS:
            actions.append({"kind": "classification", "value": inferred_cls, "reason": inferred_reason})
            cls = inferred_cls
            if not has_divergence_log:
                actions.append(
                    {
                        "kind": "divergence_log",
                        "value": (
                            "Classical-baseline contract metadata repair: this probe is retained as a "
                            "baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt."
                        ),
                        "reason": "classical_baseline_requires_nonempty_divergence_log",
                    }
                )
                has_divergence_log = True
        elif inferred_cls:
            blocked.append("C1_non_baseline_classification_needs_review")
        else:
            blocked.append("C1_classification_missing_needs_review")

    if "C2_manifest_missing" in rules:
        tool_aliases = imported_tool_aliases(tree)
        calls = called_names(tree)
        tools = sorted(tool_aliases) or ["python_stdlib"]
        manifest = {
            tool: {
                "tried": True,
                "used": bool(tool_aliases.get(tool, set()) & calls) if tool != "python_stdlib" else True,
                "reason": (
                    "Conservative contract metadata repair: source imports and calls this tool; "
                    "role is marked supportive pending claim-specific review."
                    if tool != "python_stdlib"
                    else "Conservative contract metadata repair: stdlib-only probe metadata."
                ),
            }
            for tool in tools
        }
        for tool, entry in manifest.items():
            if tool != "python_stdlib" and entry["used"] is False:
                entry["reason"] = (
                    "Conservative contract metadata repair: source imports this tool, but no "
                    "direct call site was found; kept as unused/supportive pending review."
                )
        actions.append({"kind": "tool_manifest", "value": manifest, "reason": "import_based_supportive_manifest"})

    if "C3_depth_missing" in rules:
        manifest = existing_manifest(assigns)
        tools = sorted(str(tool) for tool in manifest) or sorted(imported_tools(tree)) or ["python_stdlib"]
        depth = {tool: "supportive" for tool in tools}
        actions.append({"kind": "tool_depth", "value": depth, "reason": "supportive_depth_from_manifest_or_imports"})

    if "C4_divergence_log_missing" in rules or "C4_divergence_log_empty" in rules:
        if cls == "classical_baseline" and not has_divergence_log:
            actions.append(
                {
                    "kind": "divergence_log",
                    "value": (
                        "Classical-baseline contract metadata repair: this probe is retained as a "
                        "baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt."
                    ),
                    "reason": "classical_baseline_requires_nonempty_divergence_log",
                }
            )
            has_divergence_log = True
        else:
            blocked.append("C4_requires_classification_or_stage_review")

    return {
        "sim": rel,
        "rules": sorted(rules),
        "actions": actions,
        "blocked": blocked,
    }


def apply_plan(plan: dict[str, Any]) -> None:
    if not plan["actions"]:
        return
    path = ROOT / plan["sim"]
    text = source_text(path)
    tree = parse(path)
    if tree is None:
        return
    idx = insertion_index(text, tree)
    path.write_text(text[:idx] + metadata_block(plan["actions"]) + text[idx:], encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    if args.paths:
        sims = [ROOT / path if not Path(path).is_absolute() else Path(path) for path in args.paths]
    else:
        sims = sorted(path for path in PROBES.glob("sim_*.py") if path.is_file() and " 2" not in path.name)

    plans = [repair_plan(path) for path in sims]
    actionable = [plan for plan in plans if plan["actions"] and not plan["blocked"]]
    if args.limit:
        allowed = {plan["sim"] for plan in actionable[: args.limit]}
        actionable = [plan for plan in actionable if plan["sim"] in allowed]
    if args.apply:
        for plan in actionable:
            apply_plan(plan)

    report = {
        "schema": "contract_metadata_safe_repair_preview_v1",
        "mode": "apply" if args.apply else "dry_run",
        "checked": len(plans),
        "actionable": len(actionable),
        "blocked": sum(1 for plan in plans if plan["blocked"]),
        "action_counts": {},
        "blocked_counts": {},
        "plans": plans,
        "applied_sims": [plan["sim"] for plan in actionable] if args.apply else [],
    }
    for plan in actionable:
        for action in plan["actions"]:
            report["action_counts"][action["kind"]] = report["action_counts"].get(action["kind"], 0) + 1
    for plan in plans:
        for blocked in plan["blocked"]:
            report["blocked_counts"][blocked] = report["blocked_counts"].get(blocked, 0) + 1
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["mode", "checked", "actionable", "blocked", "action_counts", "blocked_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
