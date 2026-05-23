#!/usr/bin/env python3
"""lint_sim_contract.py -- Static contract linter for system_v4/probes/sim_*.py.

Checks, by AST parse only (no import side-effects):
  C1: module-level `classification` or `CLASSIFICATION` in
      {"classical_baseline","canonical","tool_lego_fit_probe","formal_scout"}
  C2: module-level `TOOL_MANIFEST` dict with non-empty `reason` per tool
  C3: module-level `TOOL_INTEGRATION_DEPTH` dict present, values in allowed set
  C4: if classification == "classical_baseline", non-empty `divergence_log`
  C5: if any tool in TOOL_INTEGRATION_DEPTH == "load_bearing",
      either a v4 `sim_<canonical>_capability.py` receipt passes, or a v5
      formal tool-admission scout for that tool passes
      (self-probe exception: a capability probe is trivially its own evidence)
  C7: bridge or nonclassical sims may not use numpy as a load-bearing tool.
  C8: nonclassical sims require locally load-bearing pytorch.
  C9: safe-repair metadata sentinel may not coexist with promoted
      classification.

Emits a JSON report to stdout with:
  - checked
  - violations_by_type: counts per rule
  - violations: flat list (each: {sim, rule, detail})
  - top_offenders: up to 10 sims with the most distinct rule violations

Exit 1 if any violation; 0 otherwise.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import two_root_constraints

REPO = Path(__file__).resolve().parent.parent
PROBES_DIR = REPO / "system_v4" / "probes"
RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"
FORMAL_SCOUT_RESULTS_DIR = REPO / "system_v5" / "ops" / "formal_scouts" / "results"
SAFE_REPAIR_SENTINEL = "safe_repair_v1"

VALID_CLASSIFICATIONS = {
    "audit",
    "canonical",
    "classical_baseline",
    "companion_index",
    "comparison_surface",
    "controller_audit",
    "controller_index",
    "controller_overlay",
    "controller_queue_audit",
    "controller_routing_surface",
    "diagnostic_only",
    "formal_scout",
    "supporting",
    "tool_lego_fit_probe",
}
VALID_DEPTHS = {"load_bearing", "supportive", "decorative", None}
TRANSITIVE_ROLE_VALUES = {"transitive", "upstream", "imported", "delegated", "engine-core", "engine_core"}
ADMIN_INTERNAL_TOOLS = {
    "concurrent.futures",
    "concurrent_futures",
    "hashlib",
    "importlib",
    "json",
    "pathlib",
    "python_json",
    "python_pathlib",
    "python_re",
    "python_stdlib",
    "re",
    "subprocess",
}
INTERNAL_REFERENCE_TOOLS = {
    "axis0_guard_utils",
    "composed_manifold_scout",
    "engine_core",
    "engine_v6_reference",
    "engine_v7_reference",
    "holodeck_fep_engine.hopf_map",
    "multitool_carrier_scout",
    "seven_control_scout",
    "source_density_scout",
    "special_form_constraints",
}
MICRO_TOOL_FUNCTION_TOOLS = {
    "auto_lirpa",
    "cotengra",
    "cvc5",
    "e3nn",
    "geomstats",
    "gudhi",
    "le_wm",
    "networkx",
    "opt_einsum",
    "pyg",
    "quimb",
    "rustworkx",
    "sympy",
    "toponetx",
    "xgi",
    "z3",
}
FORMAL_TOOL_ADMISSION_RESULTS = {
    "auto_lirpa": ("auto_lirpa_lewm_latent_surprise_bound_probe_results.json",),
    "cotengra": ("quimb_cotengra_tensor_network_geometry_contraction_probe_results.json",),
    "le_wm": ("lewm_branch_order_latent_dynamics_micro_probe_results.json",),
    "opt_einsum": ("opt_einsum_index_order_contraction_micro_probe_results.json",),
    "quimb": ("quimb_cotengra_tensor_network_geometry_contraction_probe_results.json",),
}

ALIASES = {
    "pytorch": "pytorch", "torch": "pytorch",
    "pytorch_autograd": "pytorch", "torch_autograd": "pytorch",
    "auto_lirpa": "auto_lirpa",
    "pyg": "pyg", "torch_geometric": "pyg", "torch-geometric": "pyg",
    "z3": "z3", "z3-solver": "z3", "z3_solver": "z3",
    "cvc5": "cvc5",
    "sympy": "sympy",
    "clifford": "clifford",
    "geomstats": "geomstats",
    "e3nn": "e3nn",
    "xgi": "xgi",
    "toponetx": "toponetx",
    "gudhi": "gudhi",
    "rustworkx": "rustworkx",
    "hypothesis": "hypothesis",
    "optuna": "optuna",
    "evotorch": "evotorch",
    "datasketch": "datasketch",
    "pynndescent": "pynndescent",
    "lewm": "le_wm", "le_wm": "le_wm", "le_wm_module": "le_wm",
    "numpy": "numpy", "np": "numpy",
    "networkx": "networkx", "nx": "networkx",
}


def canonical(tool: str) -> str:
    return ALIASES.get(tool.strip().lower().replace("-", "_"),
                       tool.strip().lower().replace("-", "_"))


for _tool, _receipt in two_root_constraints.TWO_ROOT_TOOL_MICRO_RECEIPTS.items():
    _canon = canonical(str(_tool))
    _existing = FORMAL_TOOL_ADMISSION_RESULTS.get(_canon, ())
    if _receipt not in _existing:
        FORMAL_TOOL_ADMISSION_RESULTS[_canon] = (*_existing, _receipt)


def _normalized_execution_kind(value: object) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized in {
        "bridge",
        "qit_bridge",
        "nonclassical_bridge",
        "semiclassical",
        "semi_classical",
        "semiclassical_bridge",
        "semiclassical_szilard",
    }:
        return "bridge"
    if normalized == "nonclassical":
        return "nonclassical"
    if normalized == "classical":
        return "classical"
    return ""


def _is_ignored_sim_path(path: Path) -> bool:
    return path.name.endswith(" 2.py")


def _has_nonempty_divergence_log(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple)):
        return any(isinstance(item, str) and item.strip() for item in value)
    return False


def _is_capability_probe(path: Path, tool_canon: str | None = None) -> bool:
    if tool_canon is not None:
        return path.name in {
            f"sim_{tool_canon}_capability.py",
            f"sim_capability_{tool_canon}_isolated.py",
        }
    return path.name.endswith("_capability.py") or (
        path.name.startswith("sim_capability_") and path.name.endswith("_isolated.py")
    )


def _is_integration_probe(path: Path) -> bool:
    return path.name.startswith("sim_integration_")


def _c5_static_overclaim_rule(tool_canon: str) -> str | None:
    if tool_canon in ADMIN_INTERNAL_TOOLS:
        return "C5_admin_internal_load_bearing_overclaim"
    if tool_canon in INTERNAL_REFERENCE_TOOLS:
        return "C5_internal_reference_load_bearing_overclaim"
    return None


def _is_formal_micro_tool_function_probe(path: Path, cls: object, load_bearing: set[str]) -> bool:
    if cls != "formal_scout":
        return False
    if not path.name.endswith("_micro_probe.py"):
        return False
    if not load_bearing or "numpy" in load_bearing:
        return False
    return load_bearing <= MICRO_TOOL_FUNCTION_TOOLS


def _module_level_assignments(tree: ast.Module) -> dict:
    """Collect module-level assignments that are static after simple name resolution."""
    out: dict = {}

    def _literalish_eval(node: ast.AST, local_env: dict | None = None):
        env = out if local_env is None else {**out, **local_env}
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in env:
                return env[node.id]
            if node.id.startswith("HAVE_"):
                return False
            raise ValueError(node.id)
        if isinstance(node, ast.List):
            return [_literalish_eval(elt, local_env) for elt in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(_literalish_eval(elt, local_env) for elt in node.elts)
        if isinstance(node, ast.Set):
            return {_literalish_eval(elt, local_env) for elt in node.elts}
        if isinstance(node, ast.Dict):
            return {
                _literalish_eval(k, local_env): _literalish_eval(v, local_env)
                for k, v in zip(node.keys, node.values)
            }
        if isinstance(node, ast.IfExp):
            return _literalish_eval(node.body if _literalish_eval(node.test, local_env) else node.orelse, local_env)
        if (
            isinstance(node, ast.Compare)
            and len(node.ops) == 1
            and len(node.comparators) == 1
            and isinstance(node.ops[0], (ast.Eq, ast.NotEq, ast.Is, ast.IsNot, ast.In, ast.NotIn))
        ):
            try:
                left = _literalish_eval(node.left, local_env)
            except ValueError:
                left = None
            right = _literalish_eval(node.comparators[0], local_env)
            if isinstance(node.ops[0], ast.In):
                return left in right
            if isinstance(node.ops[0], ast.NotIn):
                return left not in right
            equal = left is right if isinstance(node.ops[0], (ast.Is, ast.IsNot)) else left == right
            return equal if isinstance(node.ops[0], (ast.Eq, ast.Is)) else not equal
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
            if not node.args:
                return {}
            try:
                value = _literalish_eval(node.args[0], local_env)
            except ValueError:
                return {}
            if isinstance(value, dict):
                return dict(value)
            raise ValueError("dict_arg")
        if (
            isinstance(node, ast.DictComp)
            and len(node.generators) == 1
            and not node.generators[0].ifs
            and isinstance(node.generators[0].target, ast.Name)
            and isinstance(node.generators[0].iter, ast.Name)
        ):
            source = out.get(node.generators[0].iter.id)
            if not isinstance(source, dict):
                raise ValueError(node.generators[0].iter.id)
            target_name = node.generators[0].target.id
            result = {}
            for key in source:
                local_env = dict(out)
                local_env[target_name] = key
                result_key = key if isinstance(node.key, ast.Name) and node.key.id == target_name else _literalish_eval(node.key, local_env)
                if isinstance(node.value, ast.Name) and node.value.id == target_name:
                    result_val = key
                else:
                    result_val = _literalish_eval(node.value, local_env)
                result[result_key] = result_val
            return result
        raise ValueError(type(node).__name__)

    for node in tree.body:
        targets = []
        value = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
            applied_subscript_update = False
            for target in targets:
                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Name)
                    and isinstance(out.get(target.value.id), dict)
                ):
                    try:
                        key = _literalish_eval(target.slice)
                        out[target.value.id][key] = _literalish_eval(value)
                        applied_subscript_update = True
                    except (ValueError, SyntaxError):
                        pass
            if applied_subscript_update:
                continue
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        elif (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "update"
            and isinstance(node.value.func.value, ast.Name)
            and node.value.args
        ):
            target = node.value.func.value.id
            if isinstance(out.get(target), dict):
                try:
                    out[target].update(_literalish_eval(node.value.args[0]))
                except (ValueError, SyntaxError):
                    pass
            continue
        elif isinstance(node, ast.For) and isinstance(node.target, ast.Name):
            try:
                iter_values = _literalish_eval(node.iter)
            except (ValueError, SyntaxError):
                continue
            for item in iter_values:
                for stmt in node.body:
                    if not isinstance(stmt, ast.Assign):
                        continue
                    for target in stmt.targets:
                        if (
                            isinstance(target, ast.Subscript)
                            and isinstance(target.value, ast.Name)
                            and isinstance(out.get(target.value.id), dict)
                            and isinstance(target.slice, ast.Name)
                            and target.slice.id == node.target.id
                        ):
                            try:
                                out[target.value.id][item] = _literalish_eval(stmt.value, {node.target.id: item})
                            except (ValueError, SyntaxError):
                                pass
            continue
        else:
            continue
        for t in targets:
            if isinstance(t, ast.Name):
                try:
                    out[t.id] = _literalish_eval(value)
                except (ValueError, SyntaxError):
                    pass
    return out


def _classification_assignments(assigns: dict) -> dict[str, object]:
    values: dict[str, object] = {}
    for key in ("classification", "CLASSIFICATION"):
        if key in assigns:
            values[key] = assigns[key]
    return values


def _effective_classification(assigns: dict) -> object:
    values = _classification_assignments(assigns)
    if "classification" in values:
        return values["classification"]
    if "CLASSIFICATION" in values:
        return values["CLASSIFICATION"]
    return "__MISSING__"


def _emitted_classification_literals(tree: ast.Module) -> set[str]:
    values: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if not (isinstance(key, ast.Constant) and key.value == "classification"):
                continue
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                values.add(value.value)
    return values


def _role_sources(assigns: dict) -> dict[str, str]:
    raw = assigns.get("TOOL_ROLE_SOURCE") or assigns.get("tool_role_source") or {}
    manifest = assigns.get("TOOL_MANIFEST") or {}
    sources: dict[str, str] = {}
    if isinstance(raw, dict):
        sources.update(
            {
                str(tool): str(source).strip().lower().replace("_", "-")
                for tool, source in raw.items()
            }
        )
    if isinstance(manifest, dict):
        for tool, entry in manifest.items():
            if not isinstance(entry, dict):
                continue
            source = (
                entry.get("role_source")
                or entry.get("tool_role_source")
                or entry.get("integration_source")
            )
            if source:
                sources.setdefault(str(tool), str(source).strip().lower().replace("_", "-"))
                continue
            reason = str(entry.get("reason") or "").lower()
            if "transitive" in reason or "through enginecore" in reason or "through engine_core" in reason:
                sources.setdefault(str(tool), "transitive")
    return sources


def _is_local_load_bearing(tool: str, sources: dict[str, str]) -> bool:
    source = sources.get(tool) or sources.get(canonical(tool))
    return source not in TRANSITIVE_ROLE_VALUES


def _capability_ok(tool_canon: str) -> tuple[bool, str]:
    candidates = [
        (
            PROBES_DIR / f"sim_{tool_canon}_capability.py",
            RESULTS_DIR / f"{tool_canon}_capability_results.json",
        ),
        (
            PROBES_DIR / f"sim_capability_{tool_canon}_isolated.py",
            RESULTS_DIR / f"sim_capability_{tool_canon}_isolated_results.json",
        ),
    ]
    any_probe = False
    for probe, result in candidates:
        if not probe.exists():
            continue
        any_probe = True
        if not result.exists():
            continue
        try:
            data = json.loads(result.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if (
            (data.get("summary") or {}).get("all_pass") is True
            or data.get("overall_pass") is True
            or data.get("passed") is True
        ):
            return True, "ok"
        return False, "probe_failing"
    for receipt_name in FORMAL_TOOL_ADMISSION_RESULTS.get(tool_canon, ()):
        result = FORMAL_SCOUT_RESULTS_DIR / receipt_name
        if not result.exists():
            continue
        try:
            data = json.loads(result.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        depth = data.get("TOOL_INTEGRATION_DEPTH") or data.get("tool_integration_depth") or {}
        load_bearing_tools = {
            canonical(str(tool))
            for tool, role in depth.items()
            if role == "load_bearing"
        }
        source_category = str(data.get("source_alignment_category") or "").lower()
        claim_ceiling = str(data.get("claim_ceiling") or "").lower()
        if (
            data.get("classification") == "formal_scout"
            and data.get("promotion_allowed") is False
            and data.get("all_pass") is True
            and tool_canon in load_bearing_tools
            and "tool_admission" in source_category
            and "formal scout only" in claim_ceiling
        ):
            return True, "ok"
    if not any_probe:
        return False, "missing_probe"
    return False, "probe_stale"


def lint_sim(path: Path) -> list[dict]:
    violations: list[dict] = []
    path = path if path.is_absolute() else REPO / path
    try:
        rel = str(path.relative_to(REPO))
    except ValueError:
        rel = str(path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        violations.append({"sim": rel, "rule": "parse_error", "detail": str(exc)})
        return violations

    assigns = _module_level_assignments(tree)

    # C1: classification
    cls = _effective_classification(assigns)
    if cls == "__MISSING__":
        violations.append({"sim": rel, "rule": "C1_classification_missing", "detail": None})
    elif cls not in VALID_CLASSIFICATIONS:
        violations.append({"sim": rel, "rule": "C1_classification_invalid",
                           "detail": repr(cls)})

    repair_marker = assigns.get("contract_metadata_repair")
    if repair_marker == SAFE_REPAIR_SENTINEL:
        promoted = {
            key: value
            for key, value in _classification_assignments(assigns).items()
            if value != "classical_baseline"
        }
        promoted.update(
            {
                f"emitted:{value}": value
                for value in _emitted_classification_literals(tree)
                if value != "classical_baseline"
            }
        )
    else:
        promoted = {}
    if promoted:
        violations.append({
            "sim": rel,
            "rule": "C9_safe_repair_sentinel_blocks_promotion",
            "detail": repr(promoted),
        })

    # C2: TOOL_MANIFEST
    manifest = assigns.get("TOOL_MANIFEST", "__MISSING__")
    if manifest == "__MISSING__":
        violations.append({"sim": rel, "rule": "C2_manifest_missing", "detail": None})
    elif not isinstance(manifest, dict) or not manifest:
        violations.append({"sim": rel, "rule": "C2_manifest_malformed",
                           "detail": type(manifest).__name__})
    else:
        for tool, entry in manifest.items():
            if not isinstance(entry, dict):
                violations.append({"sim": rel, "rule": "C2_manifest_entry_malformed",
                                   "detail": f"{tool}: {type(entry).__name__}"})
                continue
            reason = entry.get("reason")
            # empty reason acceptable when used=False (honest non-use)
            if entry.get("used") is True and (not isinstance(reason, str) or not reason.strip()):
                violations.append({"sim": rel, "rule": "C2_reason_empty",
                                   "detail": str(tool)})

    # C3: TOOL_INTEGRATION_DEPTH
    depth = assigns.get("TOOL_INTEGRATION_DEPTH", "__MISSING__")
    if depth == "__MISSING__":
        violations.append({"sim": rel, "rule": "C3_depth_missing", "detail": None})
    elif not isinstance(depth, dict) or not depth:
        violations.append({"sim": rel, "rule": "C3_depth_malformed",
                           "detail": type(depth).__name__})
    else:
        for tool, lvl in depth.items():
            if lvl not in VALID_DEPTHS:
                violations.append({"sim": rel, "rule": "C3_depth_invalid_value",
                                   "detail": f"{tool}={lvl!r}"})

    # C4: divergence_log required when classical_baseline
    if cls == "classical_baseline":
        dl = assigns.get("divergence_log", "__MISSING__")
        if dl == "__MISSING__":
            violations.append({"sim": rel, "rule": "C4_divergence_log_missing", "detail": None})
        elif not _has_nonempty_divergence_log(dl):
            violations.append({"sim": rel, "rule": "C4_divergence_log_empty",
                               "detail": repr(dl)})

    # C5: load_bearing tools need passing capability probe
    if isinstance(depth, dict):
        for tool, lvl in depth.items():
            if lvl != "load_bearing":
                continue
            canon = canonical(str(tool))
            static_rule = _c5_static_overclaim_rule(canon)
            if static_rule:
                violations.append({"sim": rel, "rule": static_rule,
                                   "detail": f"{tool}->{canon}"})
                continue
            # Self-probe exception
            if _is_capability_probe(path, canon):
                continue
            ok, detail = _capability_ok(canon)
            if not ok:
                violations.append({"sim": rel, "rule": f"C5_{detail}",
                                   "detail": f"{tool}->{canon}"})

    # C7/C8: bridge and nonclassical sims need nonclassical-capable tooling.
    # NumPy-only or NumPy-load-bearing rows are allowed for classical baselines,
    # but not as bridge/nonclassical evidence.
    execution_kind = _normalized_execution_kind(
        assigns.get("sim_execution_kind") or assigns.get("SIM_EXECUTION_KIND")
    )
    if execution_kind in {"bridge", "nonclassical"} and isinstance(depth, dict):
        role_sources = _role_sources(assigns)
        load_bearing = {canonical(str(tool)) for tool, lvl in depth.items() if lvl == "load_bearing"}
        local_load_bearing = {
            canonical(str(tool))
            for tool, lvl in depth.items()
            if lvl == "load_bearing" and _is_local_load_bearing(str(tool), role_sources)
        }
        if "numpy" in load_bearing:
            violations.append({
                "sim": rel,
                "rule": "C7_numpy_load_bearing_for_bridge_or_nonclassical",
                "detail": execution_kind,
            })
        micro_tool_probe = _is_formal_micro_tool_function_probe(path, cls, load_bearing)
        if (
            execution_kind == "nonclassical"
            and "pytorch" not in local_load_bearing
            and not micro_tool_probe
        ):
            violations.append({
                "sim": rel,
                "rule": "C8_nonclassical_requires_local_pytorch_load_bearing",
                "detail": ",".join(sorted(load_bearing)) or "no_load_bearing_tools",
            })

    return violations


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-archive", action="store_true",
                    help="Include _archive_lane_c sims (default: excluded).")
    ap.add_argument(
        "paths",
        nargs="*",
        help="Optional explicit sim files to lint instead of the default system_v4/probes corpus.",
    )
    args = ap.parse_args()

    if args.paths:
        sims = [Path(path) for path in args.paths]
    else:
        sims = sorted(p for p in PROBES_DIR.glob("sim_*.py") if not _is_ignored_sim_path(p))
        if not args.include_archive:
            sims = [s for s in sims if "_archive_lane_c" not in s.parts]

    all_violations: list[dict] = []
    for sim in sims:
        all_violations.extend(lint_sim(sim))

    by_type = Counter(v["rule"] for v in all_violations)
    per_sim: dict = defaultdict(set)
    for v in all_violations:
        per_sim[v["sim"]].add(v["rule"])
    top_offenders = sorted(
        ({"sim": s, "distinct_rules": len(rs),
          "rules": sorted(rs)} for s, rs in per_sim.items()),
        key=lambda x: (-x["distinct_rules"], x["sim"]),
    )[:10]

    report = {
        "checked": len(sims),
        "violation_total": len(all_violations),
        "sims_with_violations": len(per_sim),
        "violations_by_type": dict(by_type.most_common()),
        "top_offenders": top_offenders,
        "violations": all_violations,
    }
    print(json.dumps(report, indent=2))
    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
