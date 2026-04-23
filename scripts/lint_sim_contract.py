#!/usr/bin/env python3
"""lint_sim_contract.py -- Static contract linter for system_v4/probes/sim_*.py.

Checks, by AST parse only (no import side-effects):
  C1: module-level `classification` in {"classical_baseline","canonical"}
  C2: module-level `TOOL_MANIFEST` dict with non-empty `reason` per tool
  C3: module-level `TOOL_INTEGRATION_DEPTH` dict present, values in allowed set
  C4: if classification == "classical_baseline", non-empty `divergence_log`
  C5: if any tool in TOOL_INTEGRATION_DEPTH == "load_bearing",
      `sim_<canonical>_capability.py` exists AND
      a2_state/sim_results/<canonical>_capability_results.json has summary.all_pass == True
      (self-probe exception: a capability probe is trivially its own evidence)

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

REPO = Path(__file__).resolve().parent.parent
PROBES_DIR = REPO / "system_v4" / "probes"
RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"

VALID_CLASSIFICATIONS = {"classical_baseline", "canonical"}
VALID_DEPTHS = {"load_bearing", "supportive", "decorative", None}

ALIASES = {
    "pytorch": "pytorch", "torch": "pytorch",
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
    "numpy": "numpy", "np": "numpy",
    "networkx": "networkx", "nx": "networkx",
}


def canonical(tool: str) -> str:
    return ALIASES.get(tool.strip().lower().replace("-", "_"),
                       tool.strip().lower().replace("-", "_"))


def _is_ignored_sim_path(path: Path) -> bool:
    return path.name.endswith(" 2.py")


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


def _module_level_assignments(tree: ast.Module) -> dict:
    """Collect module-level assignments that are static after simple name resolution."""
    out: dict = {}

    def _literalish_eval(node: ast.AST):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in out:
                return out[node.id]
            raise ValueError(node.id)
        if isinstance(node, ast.List):
            return [_literalish_eval(elt) for elt in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(_literalish_eval(elt) for elt in node.elts)
        if isinstance(node, ast.Set):
            return {_literalish_eval(elt) for elt in node.elts}
        if isinstance(node, ast.Dict):
            return {
                _literalish_eval(k): _literalish_eval(v)
                for k, v in zip(node.keys, node.values)
            }
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
                result_key = key if isinstance(node.key, ast.Name) and node.key.id == target_name else _literalish_eval(node.key)
                if isinstance(node.value, ast.Name) and node.value.id == target_name:
                    result_val = key
                else:
                    # Only support the common "{k: None for k in TOOL_MANIFEST}" pattern.
                    if isinstance(node.value, ast.Constant):
                        result_val = node.value.value
                    else:
                        raise ValueError("dictcomp_value")
                result[result_key] = result_val
            return result
        raise ValueError(type(node).__name__)

    for node in tree.body:
        targets = []
        value = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        else:
            continue
        for t in targets:
            if isinstance(t, ast.Name):
                try:
                    out[t.id] = _literalish_eval(value)
                except (ValueError, SyntaxError):
                    pass
    return out


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
    if not any_probe:
        return False, "missing_probe"
    return False, "probe_stale"


def lint_sim(path: Path) -> list[dict]:
    violations: list[dict] = []
    rel = str(path.relative_to(REPO))
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        violations.append({"sim": rel, "rule": "parse_error", "detail": str(exc)})
        return violations

    assigns = _module_level_assignments(tree)

    # C1: classification
    cls = assigns.get("classification", "__MISSING__")
    if cls == "__MISSING__":
        violations.append({"sim": rel, "rule": "C1_classification_missing", "detail": None})
    elif cls not in VALID_CLASSIFICATIONS:
        violations.append({"sim": rel, "rule": "C1_classification_invalid",
                           "detail": repr(cls)})

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
        elif not (isinstance(dl, str) and dl.strip()):
            violations.append({"sim": rel, "rule": "C4_divergence_log_empty",
                               "detail": repr(dl)})

    # C5: load_bearing tools need passing capability probe
    if isinstance(depth, dict):
        for tool, lvl in depth.items():
            if lvl != "load_bearing":
                continue
            canon = canonical(str(tool))
            # Self-probe exception
            if _is_capability_probe(path, canon):
                continue
            ok, detail = _capability_ok(canon)
            if not ok:
                violations.append({"sim": rel, "rule": f"C5_{detail}",
                                   "detail": f"{tool}->{canon}"})

    # C6: classical_baseline sims may not carry load_bearing tools, except explicit
    # capability/integration tool-surface baselines.
    if (
        cls == "classical_baseline"
        and isinstance(depth, dict)
        and not (_is_capability_probe(path) or _is_integration_probe(path))
    ):
        for tool, lvl in depth.items():
            if lvl == "load_bearing":
                violations.append({"sim": rel, "rule": "C6_classical_has_load_bearing",
                                   "detail": str(tool)})

    return violations


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-archive", action="store_true",
                    help="Include _archive_lane_c sims (default: excluded).")
    args = ap.parse_args()

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
