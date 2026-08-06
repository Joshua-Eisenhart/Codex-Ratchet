#!/usr/bin/env python3
"""Narrow static triage for code-shaped ClaimGate defects.

Usage: ``slop_gate.py [--diff <ref|file>] [--json] <path> [<path> ...]``.

Exit 0 is clean, 1 means one or more suspects, and 2 is a usage/input error.
A nonzero result is a POLICY disposition, never a scientific verdict.

HONEST CEILING
--------------
Every finding is a SUSPECT, not proof. Static analysis cannot prove that a
function does no work; only execution can. S1 sees literal outcome claims next
to named tools but cannot see dynamic imports or remote execution. S2 sees
syntactically toothless tests but cannot judge assertions hidden in helpers.
S3 sees exception paths that syntactically manufacture success but cannot infer
the author's recovery contract. S4 sees operation-named constant bodies but
cannot know whether a constant result is intentionally specified. S5 sees
unused non-stdlib import bindings inside one module but cannot see consumers
that introspect module globals. S6 sees local stubs and simple calls within the
scanned Python set, not reflection, dependency injection, or dynamic dispatch.

False positives are the primary failure. The initial uncomputed-verdict regex
in this repository fired at 1,119 sites in 7,879 files. These rules are narrowed
accordingly: structural rules use AST; S1 requires a named external tool
adjacent to a genuine constant outcome and no launcher import; S2 exempts
declared skips and assertRaises; S3 limits bare ``pass`` to functions with
truthy status returns; S4 requires an operation verb in the name/docstring and
an entirely constant body; S5 excludes stdlib/relative/noqa/re-export,
capability-probe, and annotation uses; S6 requires a return-consuming caller
in the scanned set and refuses ambiguous method dispatch.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import symtable
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

OUTCOME_KEYS = {"ran", "verdict", "passed", "all_pass", "load_bearing", "clean", "ok"}
TOOLS = {
    "z3", "cvc5", "julia", "jax", "torch", "pytorch", "solver", "smt", "tlc",
    "apalache", "pytest", "mypy", "eslint", "ruff", "numpy", "scipy", "quimb",
    "cotengra", "pymdp", "nvidia", "nvidia_smi",
}
LAUNCHERS = {"subprocess", "multiprocessing", "asyncio", "pexpect"}
OPERATION_VERBS = {
    "verify", "check", "validate", "compute", "run", "execute", "solve", "prove",
    "scan", "measure", "fetch", "load", "parse", "analyze", "analyse", "detect", "gate",
}
TODO_RE = re.compile(r"#.*\b(?:TODO|FIXME|XXX)\b", re.I)
NAME_RE = re.compile(r"[A-Za-z_]\w*")
SKIP_WALK_PARTS = {"fixtures", ".git", "node_modules", "__pycache__"}


@dataclass(frozen=True)
class Finding:
    signature_id: str
    path: str
    line: int
    excerpt: str
    why: str

    def as_dict(self) -> dict[str, object]:
        return {
            "signature_id": self.signature_id,
            "path": self.path,
            "line": self.line,
            "excerpt": self.excerpt,
            "why": self.why,
        }


@dataclass
class SourceUnit:
    path: Path
    source: str
    tree: ast.Module
    lines: list[str]

    def excerpt(self, line: int) -> str:
        if 1 <= line <= len(self.lines):
            return self.lines[line - 1].strip()[:240]
        return ""


@dataclass(frozen=True)
class FunctionDef:
    unit: SourceUnit
    node: ast.FunctionDef | ast.AsyncFunctionDef
    class_name: str | None
    stub_line: int | None


def _constant(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(_constant(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            (key is None or _constant(key)) and _constant(value)
            for key, value in zip(node.keys, node.values)
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _constant(node.operand)
    return False


def _truthy_constant(node: ast.AST) -> bool:
    if not _constant(node):
        return False
    try:
        return bool(ast.literal_eval(node))
    except (ValueError, TypeError):
        return False


def _slop_constant(node: ast.AST) -> bool:
    """Literal bodies covered by S4; ``None`` is an ordinary no-result default."""
    if isinstance(node, ast.Constant):
        return node.value is not None
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(_slop_constant(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            (key is None or _slop_constant(key)) and _slop_constant(value)
            for key, value in zip(node.keys, node.values)
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _slop_constant(node.operand)
    return False


def _return_success_constant(node: ast.AST) -> bool:
    return _truthy_constant(node) or (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and node.value == 0
    )


def _key(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.casefold()
    return None


def _toolish(value: str) -> bool:
    bits = set(re.split(r"[^a-z0-9]+", value.casefold()))
    return bool(bits & TOOLS) or any(value.casefold().startswith(tool + "_") for tool in TOOLS)


def _launcher_capability(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0].casefold() in TOOLS | LAUNCHERS for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0].casefold() in TOOLS | LAUNCHERS:
                return True
    return False


def _dict_outcomes(node: ast.Dict, inherited_tool: str | None = None) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for key_node, value in zip(node.keys, node.values):
        name = _key(key_node)
        tool = name if name and _toolish(name) else inherited_tool
        if name in OUTCOME_KEYS and inherited_tool and _constant(value):
            found.append((getattr(value, "lineno", node.lineno), inherited_tool))
        if isinstance(value, ast.Dict):
            found.extend(_dict_outcomes(value, tool))
    return found


def scan_s1(unit: SourceUnit) -> list[Finding]:
    if _launcher_capability(unit.tree):
        return []
    out: list[Finding] = []
    seen: set[int] = set()
    for node in ast.walk(unit.tree):
        if isinstance(node, ast.Dict):
            for line, tool in _dict_outcomes(node):
                if line not in seen:
                    seen.add(line)
                    out.append(Finding(
                        "S1", str(unit.path), line, unit.excerpt(line),
                        f"constant tool outcome is adjacent to {tool!r}, but this file imports no tool or process launcher",
                    ))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if value is None or not _constant(value):
                continue
            for target in targets:
                if isinstance(target, ast.Attribute) and target.attr.casefold() in OUTCOME_KEYS:
                    base = target.value.id if isinstance(target.value, ast.Name) else ""
                    if _toolish(base):
                        line = target.lineno
                        out.append(Finding(
                            "S1", str(unit.path), line, unit.excerpt(line),
                            f"constant {target.attr} outcome is attached to named tool {base!r}, but no launcher is imported",
                        ))
    return out


def _decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_decorator_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return ""


def _declared_skip(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if any("skip" in _decorator_name(item).casefold() for item in node.decorator_list):
        return True
    body = node.body[1:] if ast.get_docstring(node, clean=False) is not None else node.body
    return bool(body) and all(
        isinstance(stmt, (ast.Pass, ast.Expr))
        and (
            isinstance(stmt, ast.Pass)
            or (
                isinstance(stmt.value, ast.Call)
                and "skip" in _decorator_name(stmt.value.func).casefold()
            )
        )
        for stmt in body
    )


def _self_assert_call(node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        and node.func.attr.startswith("assert")
    )


def _assert_raises_context(node: ast.With | ast.AsyncWith) -> bool:
    for item in node.items:
        expr = item.context_expr
        if isinstance(expr, ast.Call) and _decorator_name(expr.func).endswith("assertRaises"):
            return True
    return False


def _assertion_real(node: ast.AST) -> bool:
    def operand_is_constant(operand: ast.AST) -> bool:
        return _constant(operand) or (
            isinstance(operand, ast.Name) and operand.id.isupper()
        )

    if isinstance(node, ast.Assert):
        return not operand_is_constant(node.test)
    if isinstance(node, ast.Call) and _self_assert_call(node):
        name = node.func.attr
        if name in {"assertRaises", "assertRaisesRegex", "assertWarns", "assertWarnsRegex"}:
            return True
        return any(not operand_is_constant(arg) for arg in node.args)
    if isinstance(node, (ast.With, ast.AsyncWith)) and _assert_raises_context(node):
        return True
    return False


def _call_did_not_raise_only(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = node.body[1:] if ast.get_docstring(node, clean=False) is not None else node.body
    if (
        len(body) == 1
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Call)
        and not _self_assert_call(body[0].value)
    ):
        return True
    if len(body) == 1 and isinstance(body[0], ast.Try):
        trial = body[0]
        if not trial.body or not all(
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Call)
            and not _self_assert_call(stmt.value)
            for stmt in trial.body
        ):
            return False
        return bool(trial.handlers) and all(
            any(isinstance(item, (ast.Assert, ast.Raise)) for item in handler.body)
            for handler in trial.handlers
        )
    return False


def _test_functions(unit: SourceUnit) -> Iterable[ast.FunctionDef | ast.AsyncFunctionDef]:
    for node in unit.tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            yield node
        elif isinstance(node, ast.ClassDef):
            is_testcase = any(_decorator_name(base).endswith("TestCase") for base in node.bases)
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                    item.name.startswith("test_") or is_testcase and item.name.startswith("test")
                ):
                    yield item


def scan_s2(unit: SourceUnit) -> list[Finding]:
    out = []
    for node in _test_functions(unit):
        if _declared_skip(node):
            continue
        assertions = [
            item for item in ast.walk(node)
            if isinstance(item, ast.Assert)
            or isinstance(item, (ast.With, ast.AsyncWith)) and _assert_raises_context(item)
            or isinstance(item, ast.Call) and _self_assert_call(item)
        ]
        if _call_did_not_raise_only(node):
            reason = "test only checks that a call did not raise and never checks its result"
        elif not assertions:
            reason = "test has no assertion or self.assert* call"
        elif not any(_assertion_real(item) for item in assertions):
            reason = "every test assertion is constant and cannot discriminate behavior"
        else:
            continue
        out.append(Finding("S2", str(unit.path), node.lineno, unit.excerpt(node.lineno), reason))
    return out


def _enclosing_functions(tree: ast.Module) -> dict[ast.ExceptHandler, ast.FunctionDef | ast.AsyncFunctionDef]:
    result: dict[ast.ExceptHandler, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for fn in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
        for node in ast.walk(fn):
            if isinstance(node, ast.ExceptHandler):
                result.setdefault(node, fn)
    return result


def _success_assignment(node: ast.Assign | ast.AnnAssign) -> bool:
    value = node.value
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    if value is None or not _truthy_constant(value):
        return False
    return any(
        isinstance(target, ast.Name)
        and target.id.casefold() in {"passed", "success", "clean", "ok", "all_pass", "load_bearing"}
        for target in targets
    )


def _name_claims_operation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return bool(set(re.split(r"[^a-z]+", node.name.casefold())) & OPERATION_VERBS)


def scan_s3(unit: SourceUnit) -> list[Finding]:
    out = []
    owners = _enclosing_functions(unit.tree)
    for handler, owner in owners.items():
        # Recovery predicates frequently and legitimately return True to mean
        # "needs attention" or "claim-bearing". Require the enclosing function
        # itself, by name, to claim an operation before reading True/0 as
        # success. Docstring words are too contextual for this polarity test.
        if not _name_claims_operation(owner):
            continue
        reason = None
        if any(isinstance(node, ast.Return) and node.value is not None and (
            _return_success_constant(node.value)
            or isinstance(node.value, ast.Dict) and any(
                _key(key) in {"ok", "passed", "success", "clean"} and _truthy_constant(value)
                for key, value in zip(node.value.keys, node.value.values)
            )
        ) for node in ast.walk(handler)):
            reason = "exception handler returns a literal success status"
        elif any(isinstance(node, (ast.Assign, ast.AnnAssign)) and _success_assignment(node) for node in ast.walk(handler)):
            reason = "exception handler assigns a literal success status"
        elif handler.type is None and len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
            outside_truth = any(
                isinstance(node, ast.Return) and node.value is not None and _truthy_constant(node.value)
                for node in ast.walk(owner)
                if not (handler.lineno <= getattr(node, "lineno", -1) <= getattr(handler, "end_lineno", -1))
            )
            if outside_truth:
                reason = "bare except/pass suppresses failure in a function that otherwise returns success"
        if reason:
            out.append(Finding("S3", str(unit.path), handler.lineno, unit.excerpt(handler.lineno), reason))
    return out


def _operation_claim(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    words = set(re.split(r"[^a-z]+", node.name.casefold()))
    if words & OPERATION_VERBS:
        return True
    doc = ast.get_docstring(node) or ""
    doc_words = set(re.findall(r"[a-z]+", doc.casefold()))
    return bool(doc_words & OPERATION_VERBS)


def _constant_function_body(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = node.body[1:] if ast.get_docstring(node, clean=False) is not None else node.body
    body = [stmt for stmt in body if not isinstance(stmt, ast.Pass)]
    if not body:
        return False
    assigned: dict[str, ast.AST] = {}
    for stmt in body[:-1]:
        if not isinstance(stmt, (ast.Assign, ast.AnnAssign)) or stmt.value is None or not _slop_constant(stmt.value):
            return False
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
        if not all(isinstance(target, ast.Name) for target in targets):
            return False
        assigned.update({target.id: stmt.value for target in targets if isinstance(target, ast.Name)})
    last = body[-1]
    if not isinstance(last, ast.Return) or last.value is None:
        return False
    return _slop_constant(last.value) or isinstance(last.value, ast.Name) and last.value.id in assigned


def scan_s4(unit: SourceUnit) -> list[Finding]:
    out = []
    for node in ast.walk(unit.tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _operation_claim(node) and _constant_function_body(node):
            out.append(Finding(
                "S4", str(unit.path), node.lineno, unit.excerpt(node.lineno),
                "operation-claiming function has an entirely literal body",
            ))
    return out


def _import_bindings(unit: SourceUnit) -> list[tuple[str, str, int]]:
    out = []
    for node in unit.tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((alias.asname or alias.name.split(".")[0], alias.name.split(".")[0], node.lineno))
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module and node.module != "__future__":
            root = node.module.split(".")[0]
            for alias in node.names:
                if alias.name != "*":
                    out.append((alias.asname or alias.name, root, node.lineno))
    return out


def _try_import_lines(tree: ast.Module) -> set[int]:
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for item in node.body:
                if isinstance(item, (ast.Import, ast.ImportFrom)):
                    lines.add(item.lineno)
    return lines


def _used_import_names(unit: SourceUnit) -> set[str]:
    table = symtable.symtable(unit.source, str(unit.path), "exec")
    used: set[str] = set()
    for symbol in table.get_symbols():
        if symbol.is_imported() and symbol.is_referenced() and not symbol.is_assigned():
            used.add(symbol.get_name())
    for child in table.get_children():
        stack = [child]
        while stack:
            scope = stack.pop()
            for symbol in scope.get_symbols():
                if symbol.is_referenced() and symbol.is_global():
                    used.add(symbol.get_name())
            stack.extend(scope.get_children())
    # String annotations are not Name loads in the module AST.
    for node in ast.walk(unit.tree):
        annotation = None
        if isinstance(node, ast.arg):
            annotation = node.annotation
        elif isinstance(node, (ast.AnnAssign, ast.FunctionDef, ast.AsyncFunctionDef)):
            annotation = node.annotation if isinstance(node, ast.AnnAssign) else node.returns
        if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
            used.update(NAME_RE.findall(annotation.value))
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
                value = node.value
                if isinstance(value, (ast.List, ast.Tuple)):
                    used.update(
                        item.value for item in value.elts
                        if isinstance(item, ast.Constant) and isinstance(item.value, str)
                    )
    return used


def scan_s5(unit: SourceUnit) -> list[Finding]:
    stdlib = getattr(sys, "stdlib_module_names", frozenset())
    used = _used_import_names(unit)
    conditional = _try_import_lines(unit.tree)
    is_init = unit.path.name == "__init__.py"
    out = []
    for bound, root, line in _import_bindings(unit):
        if root in stdlib or line in conditional or bound in used:
            continue
        text = unit.excerpt(line)
        if "noqa" in text.casefold() and "f401" in text.casefold():
            continue
        if is_init:
            continue
        out.append(Finding(
            "S5", str(unit.path), line, text,
            f"non-stdlib import binding {bound!r} is never referenced in this module",
        ))
    return out


def _function_stub(unit: SourceUnit, node: ast.FunctionDef | ast.AsyncFunctionDef) -> int | None:
    if any(_decorator_name(item).endswith("abstractmethod") for item in node.decorator_list):
        return None
    body = node.body[1:] if ast.get_docstring(node, clean=False) is not None else node.body
    if len(body) == 1 and isinstance(body[0], ast.Pass):
        return body[0].lineno
    if any(
        isinstance(item, ast.Raise)
        and isinstance(item.exc, (ast.Name, ast.Call))
        and (
            isinstance(item.exc, ast.Name) and item.exc.id == "NotImplementedError"
            or isinstance(item.exc, ast.Call) and _decorator_name(item.exc.func) == "NotImplementedError"
        )
        for item in ast.walk(node)
    ):
        return node.lineno
    start, end = node.lineno, getattr(node, "end_lineno", node.lineno)
    for line in range(start, min(end, len(unit.lines)) + 1):
        if TODO_RE.search(unit.lines[line - 1]):
            return line
    return None


def _definitions(units: list[SourceUnit]) -> list[FunctionDef]:
    out = []
    for unit in units:
        for top in unit.tree.body:
            if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append(FunctionDef(unit, top, None, _function_stub(unit, top)))
            elif isinstance(top, ast.ClassDef):
                for item in top.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out.append(FunctionDef(unit, item, top.name, _function_stub(unit, item)))
    return out


def _call_consumed(call: ast.Call, parents: dict[ast.AST, ast.AST]) -> bool:
    parent = parents.get(call)
    if isinstance(parent, ast.Expr):
        return False
    return isinstance(parent, (
        ast.Assign, ast.AnnAssign, ast.NamedExpr, ast.Return, ast.If, ast.While,
        ast.Assert, ast.Compare, ast.BoolOp, ast.UnaryOp, ast.BinOp, ast.Call,
        ast.Subscript, ast.Dict, ast.List, ast.Tuple, ast.Set,
    ))


def scan_s6(
    units: list[SourceUnit],
    added: dict[Path, set[int]] | None = None,
) -> list[Finding]:
    defs = _definitions(units)
    plain: dict[str, list[FunctionDef]] = {}
    methods: dict[str, list[FunctionDef]] = {}
    for definition in defs:
        (methods if definition.class_name else plain).setdefault(definition.node.name, []).append(definition)
    called: dict[int, tuple[FunctionDef, SourceUnit, int]] = {}
    for unit in units:
        parents = {child: parent for parent in ast.walk(unit.tree) for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(unit.tree):
            if not isinstance(node, ast.Call) or not _call_consumed(node, parents):
                continue
            candidates: list[FunctionDef] = []
            if isinstance(node.func, ast.Name):
                candidates = plain.get(node.func.id, [])
            elif isinstance(node.func, ast.Attribute):
                possible = methods.get(node.func.attr, [])
                if len(possible) == 1:
                    candidates = possible
            if len(candidates) == 1:
                called[id(candidates[0])] = (candidates[0], unit, node.lineno)
    out = []
    for definition, caller_unit, caller_line in called.values():
        if definition.stub_line is None:
            continue
        path = definition.unit.path
        line = definition.stub_line
        excerpt = definition.unit.excerpt(line)
        if added is not None and line not in added.get(path, set()):
            if caller_line not in added.get(caller_unit.path, set()):
                continue
            path = caller_unit.path
            line = caller_line
            excerpt = caller_unit.excerpt(line)
        out.append(Finding(
            "S6", str(path), line, excerpt,
            f"stub {definition.node.name!r} has a scanned caller that consumes its return value",
        ))
    return out


def _parse_unit(path: Path) -> tuple[SourceUnit | None, str | None]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as exc:
        return None, f"{path}: {type(exc).__name__}: {exc}"
    return SourceUnit(path, source, tree, source.splitlines()), None


def _walk_paths(paths: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for root in paths:
        if root.is_file():
            if root.suffix == ".py":
                files.add(root.resolve())
        elif root.is_dir():
            for path in root.rglob("*.py"):
                relative_parts = set(path.relative_to(root).parts[:-1])
                if not relative_parts & SKIP_WALK_PARTS:
                    files.add(path.resolve())
        else:
            raise ValueError(f"path does not exist: {root}")
    return sorted(files)


def _diff_text(spec: str) -> str:
    path = Path(spec)
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace")
    proc = subprocess.run(
        ["git", "diff", spec, "--"], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise ValueError(f"git diff {spec!r} failed: {proc.stderr.strip()}")
    return proc.stdout


def _added_lines(diff: str) -> dict[Path, set[int]]:
    result: dict[Path, set[int]] = {}
    current: Path | None = None
    new_line = 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            name = raw[4:].split("\t", 1)[0]
            current = None if name == "/dev/null" else Path(name[2:] if name.startswith("b/") else name).resolve()
        elif raw.startswith("@@ ") and current is not None:
            match = re.search(r"\+(\d+)(?:,(\d+))?", raw)
            if match:
                new_line = int(match.group(1))
        elif current is not None and raw.startswith("+") and not raw.startswith("+++"):
            result.setdefault(current, set()).add(new_line)
            new_line += 1
        elif current is not None and raw.startswith("-") and not raw.startswith("---"):
            continue
        elif current is not None:
            new_line += 1
    return result


def scan(paths: list[Path], diff_spec: str | None = None) -> tuple[list[Finding], list[str]]:
    files = _walk_paths(paths)
    added = _added_lines(_diff_text(diff_spec)) if diff_spec else None
    if added is not None:
        files = [path for path in files if path in added]
    units: list[SourceUnit] = []
    errors: list[str] = []
    for path in files:
        unit, error = _parse_unit(path)
        if error:
            errors.append(error)
        elif unit:
            units.append(unit)
    findings: list[Finding] = []
    for unit in units:
        findings.extend(scan_s1(unit))
        findings.extend(scan_s2(unit))
        findings.extend(scan_s3(unit))
        findings.extend(scan_s4(unit))
        findings.extend(scan_s5(unit))
    findings.extend(scan_s6(units, added))
    if added is not None:
        findings = [item for item in findings if item.line in added.get(Path(item.path), set())]
    findings.sort(key=lambda item: (item.path, item.line, item.signature_id))
    return findings, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--diff")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("paths", nargs="+")
    try:
        args = parser.parse_args(argv)
        findings, errors = scan([Path(item) for item in args.paths], args.diff)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps([item.as_dict() for item in findings], indent=2))
    else:
        for item in findings:
            print(f"{item.path}:{item.line}: {item.signature_id} {item.why}: {item.excerpt}")
        print(f"slop_gate: {len(findings)} suspect(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
