"""phase_06_tool_integration.py — every claimed tool must be load-bearing.

For each TOOL_MANIFEST entry with `used: True`, this phase independently verifies:
  1. The corresponding package is imported in the candidate source (any alias)
  2. At least one method/attribute call on that alias appears in the source body

This catches the iter_60-style cheat where Grok claimed 8 tools but only 3 had
actual function calls — the rest were import-only decoration.

Each tool gets its own check_id so the Auditor can diagnose individual tool gaps.
"""
import ast
import re
import inspect


# Map TOOL_MANIFEST tool names to one or more Python package names that satisfy them
TOOL_TO_PACKAGES = {
    "pytorch":  ["torch"],
    "qutip":    ["qutip"],
    "clifford": ["clifford"],
    "z3":       ["z3", "z3-solver"],
    "cvc5":     ["cvc5"],
    "sympy":    ["sympy"],
    "toponetx": ["toponetx"],
    "gudhi":    ["gudhi"],
    "pyg":      ["torch_geometric", "torch_geometric.nn"],
    "rustworkx": ["rustworkx"],
    "xgi":       ["xgi"],
    "geomstats": ["geomstats"],
}


def _parse_imports(source):
    """Return dict {alias_or_name: top_level_package} from AST."""
    aliases = {}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return aliases
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                alias = n.asname or n.name
                aliases[alias] = n.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module:
            for n in node.names:
                alias = n.asname or n.name
                aliases[alias] = node.module.split(".")[0]
    return aliases


def _alias_for_package(aliases, package_name):
    """Find an alias whose top-level package matches package_name."""
    for alias, pkg in aliases.items():
        if pkg == package_name or pkg.startswith(package_name + "."):
            return alias
    return None


def _has_method_call(source, alias):
    """Crude: look for `alias.something` outside the import lines."""
    pat = re.compile(rf"\b{re.escape(alias)}\.[\w_]+", re.MULTILINE)
    matches = pat.findall(source)
    return len(matches) >= 1


def run(candidate):
    failures = []
    metrics = {"tool_status": {}}

    # Get the candidate source code
    try:
        source = inspect.getsource(candidate)
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "candidate_source", "msg": f"could not read source: {str(e)[:200]}"}],
            "metrics": metrics,
        }

    aliases = _parse_imports(source)

    # Get the candidate's tool manifest
    try:
        manifest = candidate.tool_manifest()
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "tool_manifest_call", "msg": f"raised {type(e).__name__}: {str(e)[:200]}"}],
            "metrics": metrics,
        }

    # For each tool with used=True, verify import + method call
    used_tools = [name for name, spec in manifest.items()
                  if isinstance(spec, dict) and spec.get("used") is True]
    metrics["used_tools_claimed"] = used_tools
    metrics["used_tools_count"] = len(used_tools)

    if len(used_tools) < 5:
        failures.append({
            "check": "tool_count_minimum",
            "msg": f"Only {len(used_tools)} tools marked `used: True` in tool_manifest(). "
                   f"Required ≥5 load-bearing tools per side-quest doctrine.",
        })

    for tool_name in used_tools:
        packages = TOOL_TO_PACKAGES.get(tool_name, [tool_name])
        # Find any alias that satisfies one of the packages
        alias_found = None
        for pkg in packages:
            alias_found = _alias_for_package(aliases, pkg)
            if alias_found:
                break
        if alias_found is None:
            failures.append({
                "check": f"tool_imported_{tool_name}",
                "msg": f"`{tool_name}` claimed used=True in tool_manifest, but no matching package "
                       f"({packages}) imported in candidate source.",
            })
            metrics["tool_status"][tool_name] = {"imported": False, "called": False}
            continue
        # Check at least one method call on that alias
        called = _has_method_call(source, alias_found)
        metrics["tool_status"][tool_name] = {"imported": True, "alias": alias_found, "called": called}
        if not called:
            failures.append({
                "check": f"tool_load_bearing_{tool_name}",
                "msg": f"`{tool_name}` is imported as `{alias_found}` but no `{alias_found}.something` "
                       f"call appears in candidate source. Decorative import — not load-bearing.",
            })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "tool imported but never called — fails load_bearing check",
            "tool listed used=True without import — fails imported check",
            "all tools commented out — fails tool_count_minimum",
        ],
        "baseline_variants": [
            "numpy-only candidate (all other tools absent) — should fail count + per-tool checks",
            "imports-only candidate (no function bodies use the imports) — should fail load_bearing",
        ],
    }
