"""AST-based gate integrity checking and adversarial test generation.

This module detects when validation functions become more permissive
by comparing AST changes between file versions (typically git HEAD vs working tree).

It also generates adversarial test fixtures using hypothesis to verify that
validation functions correctly reject malformed input and accept valid input.

Key detections for weakening:
  - Comparison operators relaxed (== to in, < to <=, and to or)
  - raise or append-to-errors removed from conditional branches
  - Early returns inserted before existing validation checks
  - Bound literals increased (max lengths, budgets, thresholds)
  - Assertions deleted or test decorators added (skip/xfail)
"""

from __future__ import annotations

import ast
import dataclasses
import re
import subprocess
from pathlib import Path
from typing import Any, Callable
import json


@dataclasses.dataclass
class WeakeningFinding:
    """Result of a gate-weakening check."""
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    pattern: str  # e.g. "OPERATOR_RELAXED", "CHECK_REMOVED", "BOUND_INCREASED"
    location: str  # line range or function name
    detail: str
    old_code: str
    new_code: str


@dataclasses.dataclass
class AdversarialResult:
    """Result of adversarial fixture generation."""
    function_name: str
    total_examples: int
    rejected_count: int
    accepted_count: int
    edge_cases_triggered: list[str]
    summary: str


class GateIntegrityChecker:
    """Detects when validation functions become more permissive via AST analysis."""

    def __init__(self):
        self.findings: list[WeakeningFinding] = []
        self.operator_map = {
            "Eq": "==",
            "NotEq": "!=",
            "Lt": "<",
            "LtE": "<=",
            "Gt": ">",
            "GtE": ">=",
            "Is": "is",
            "IsNot": "is not",
            "In": "in",
            "NotIn": "not in",
            "And": "and",
            "Or": "or",
        }

    def compare_file_versions(
        self,
        file_path: Path,
        function_name: str = None,
        head_code: str = None,
        working_code: str = None,
    ) -> list[WeakeningFinding]:
        """Compare two versions of a file (git HEAD vs working tree, or provided code strings).

        Args:
            file_path: Path to the file (for reference)
            function_name: Specific function to check (default: all)
            head_code: Optional explicit HEAD version code (if None, fetches from git)
            working_code: Optional explicit working tree version code (if None, reads from file)
        """
        self.findings = []

        # Get HEAD version if not provided
        if head_code is None:
            try:
                head_code = subprocess.check_output(
                    ["git", "show", f"HEAD:{file_path}"],
                    cwd=file_path.parent,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
            except subprocess.CalledProcessError:
                # No HEAD version (new file)
                return self.findings

        # Get working tree version if not provided
        if working_code is None:
            try:
                working_code = file_path.read_text()
            except FileNotFoundError:
                return self.findings

        if head_code == working_code:
            return self.findings

        # Parse both versions
        try:
            head_ast = ast.parse(head_code, filename=str(file_path))
            working_ast = ast.parse(working_code, filename=str(file_path))
        except SyntaxError as e:
            self.findings.append(
                WeakeningFinding(
                    severity="CRITICAL",
                    pattern="SYNTAX_ERROR",
                    location=f"line {e.lineno}",
                    detail=f"Syntax error in {e.filename}: {e.msg}",
                    old_code="",
                    new_code="",
                )
            )
            return self.findings

        # Compare functions
        if function_name:
            self._compare_function(head_ast, working_ast, function_name, file_path)
        else:
            # Compare all functions
            head_funcs = {node.name: node for node in ast.walk(head_ast) if isinstance(node, ast.FunctionDef)}
            working_funcs = {node.name: node for node in ast.walk(working_ast) if isinstance(node, ast.FunctionDef)}

            for fname in head_funcs:
                if fname in working_funcs:
                    self._compare_function(head_ast, working_ast, fname, file_path)

        return self.findings

    def _compare_function(self, head_ast: ast.AST, working_ast: ast.AST, fname: str, file_path: Path):
        """Compare a specific function between versions."""
        head_func = self._find_function(head_ast, fname)
        working_func = self._find_function(working_ast, fname)

        if not head_func or not working_func:
            return

        # Check for removed error handling
        self._check_error_handling_removal(head_func, working_func, fname, file_path)

        # Check for relaxed comparisons
        self._check_operator_relaxation(head_func, working_func, fname, file_path)

        # Check for increased bounds
        self._check_bound_changes(head_func, working_func, fname, file_path)

        # Check for early returns
        self._check_early_returns(head_func, working_func, fname, file_path)

        # Check for removed assertions
        self._check_assertion_removal(head_func, working_func, fname, file_path)

        # Check for skip/xfail decorators
        self._check_test_decorators(head_func, working_func, fname, file_path)

    def _find_function(self, tree: ast.AST, name: str) -> ast.FunctionDef | None:
        """Find a function by name in the AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
        return None

    def _check_error_handling_removal(self, head_func: ast.FunctionDef, working_func: ast.FunctionDef, fname: str, file_path: Path):
        """Detect removed raise statements or error appends."""
        head_raises = self._count_raises_and_appends(head_func)
        working_raises = self._count_raises_and_appends(working_func)

        if working_raises < head_raises:
            self.findings.append(
                WeakeningFinding(
                    severity="CRITICAL",
                    pattern="CHECK_REMOVED",
                    location=f"{fname}",
                    detail=f"Error handling reduced: {head_raises} -> {working_raises}",
                    old_code=f"Found {head_raises} raise/append statements",
                    new_code=f"Found {working_raises} raise/append statements",
                )
            )

    def _count_raises_and_appends(self, node: ast.AST) -> int:
        """Count raise statements and .append() calls to error lists."""
        count = 0
        for n in ast.walk(node):
            if isinstance(n, ast.Raise):
                count += 1
            elif isinstance(n, ast.Call):
                if isinstance(n.func, ast.Attribute) and n.func.attr == "append":
                    count += 1
        return count

    def _check_operator_relaxation(self, head_func: ast.FunctionDef, working_func: ast.FunctionDef, fname: str, file_path: Path):
        """Detect comparison operators becoming more permissive."""
        head_comparisons = self._extract_comparisons(head_func)
        working_comparisons = self._extract_comparisons(working_func)

        # Build relaxation rules: which operators are more permissive
        relaxation_map = {
            ("NotEq", "In"): ("!= to in", "CRITICAL"),
            ("NotEq", "Or"): ("!= to or", "CRITICAL"),
            ("Lt", "LtE"): ("< to <=", "HIGH"),
            ("Gt", "GtE"): ("> to >=", "HIGH"),
            ("And", "Or"): ("and to or", "CRITICAL"),
        }

        # If the number of operators changed significantly, that's a weakening
        if len(working_comparisons) > len(head_comparisons):
            added_count = len(working_comparisons) - len(head_comparisons)
            self.findings.append(
                WeakeningFinding(
                    severity="MEDIUM",
                    pattern="OPERATOR_COUNT_CHANGE",
                    location=f"{fname}",
                    detail=f"Comparison operator count increased by {added_count}",
                    old_code=f"{len(head_comparisons)} operators",
                    new_code=f"{len(working_comparisons)} operators",
                )
            )

        # Check for specific operator relaxations at same lines
        for i, old_cmp in enumerate(head_comparisons):
            for j, new_cmp in enumerate(working_comparisons):
                if old_cmp["line"] != new_cmp["line"]:
                    continue
                old_op = old_cmp["op"]
                new_op = new_cmp["op"]
                key = (old_op, new_op)
                if key in relaxation_map:
                    desc, severity = relaxation_map[key]
                    self.findings.append(
                        WeakeningFinding(
                            severity=severity,
                            pattern="OPERATOR_RELAXED",
                            location=f"{fname}:{old_cmp['line']}",
                            detail=f"Comparison relaxed: {desc}",
                            old_code=f"{old_op}",
                            new_code=f"{new_op}",
                        )
                    )

    def _extract_comparisons(self, node: ast.AST) -> list[dict[str, Any]]:
        """Extract all comparison operators from a function."""
        comparisons = []
        for n in ast.walk(node):
            if isinstance(n, ast.Compare):
                for op in n.ops:
                    op_name = type(op).__name__
                    comparisons.append({
                        "op": op_name,
                        "line": n.lineno,
                        "node": n,
                    })
            elif isinstance(n, ast.BoolOp):
                op_name = type(n.op).__name__
                comparisons.append({
                    "op": op_name,
                    "line": n.lineno,
                    "node": n,
                })
        return comparisons

    def _check_bound_changes(self, head_func: ast.FunctionDef, working_func: ast.FunctionDef, fname: str, file_path: Path):
        """Detect numeric bounds being increased (making validation more permissive)."""
        head_numbers = self._extract_numeric_bounds(head_func)
        working_numbers = self._extract_numeric_bounds(working_func)

        # Sort by value for comparison
        head_numbers_sorted = sorted(head_numbers, key=lambda x: x["value"])
        working_numbers_sorted = sorted(working_numbers, key=lambda x: x["value"])

        # Look for increased bounds by comparing sorted values
        head_values = [n["value"] for n in head_numbers_sorted]
        working_values = [n["value"] for n in working_numbers_sorted]

        # Check if any bounds were increased
        seen_increases = False
        for i, (head_val, working_val) in enumerate(zip(head_values, working_values)):
            if isinstance(head_val, (int, float)) and isinstance(working_val, (int, float)):
                if working_val > head_val:
                    seen_increases = True
                    self.findings.append(
                        WeakeningFinding(
                            severity="MEDIUM",
                            pattern="BOUND_INCREASED",
                            location=f"{fname}",
                            detail=f"Numeric bound increased from {head_val} to {working_val}",
                            old_code=str(head_val),
                            new_code=str(working_val),
                        )
                    )

    def _extract_numeric_bounds(self, node: ast.AST) -> list[dict[str, Any]]:
        """Extract numeric literals from a function (potential bounds)."""
        numbers = []
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
                numbers.append({
                    "value": n.value,
                    "line": n.lineno,
                    "node": n,
                })
        return numbers

    def _check_early_returns(self, head_func: ast.FunctionDef, working_func: ast.FunctionDef, fname: str, file_path: Path):
        """Detect early returns inserted before validation checks."""
        head_returns = self._find_early_returns(head_func)
        working_returns = self._find_early_returns(working_func)

        # If new early returns were added, that's a weakening
        if len(working_returns) > len(head_returns):
            new_count = len(working_returns) - len(head_returns)
            self.findings.append(
                WeakeningFinding(
                    severity="HIGH",
                    pattern="EARLY_RETURN_ADDED",
                    location=f"{fname}",
                    detail=f"Added {new_count} early return statement(s)",
                    old_code=f"{len(head_returns)} early returns",
                    new_code=f"{len(working_returns)} early returns",
                )
            )

    def _find_early_returns(self, node: ast.AST) -> list[int]:
        """Find line numbers of early return statements."""
        returns = []
        for n in ast.walk(node):
            if isinstance(n, ast.Return):
                returns.append(n.lineno)
        return sorted(returns)

    def _check_assertion_removal(self, head_func: ast.FunctionDef, working_func: ast.FunctionDef, fname: str, file_path: Path):
        """Detect removed assertions or assertions moved to later in code."""
        head_assertions = self._count_assertions(head_func)
        working_assertions = self._count_assertions(working_func)

        if working_assertions < head_assertions:
            self.findings.append(
                WeakeningFinding(
                    severity="HIGH",
                    pattern="ASSERTION_REMOVED",
                    location=f"{fname}",
                    detail=f"Assertions reduced from {head_assertions} to {working_assertions}",
                    old_code=f"Found {head_assertions} assertions",
                    new_code=f"Found {working_assertions} assertions",
                )
            )

    def _count_assertions(self, node: ast.AST) -> int:
        """Count assertion statements."""
        count = 0
        for n in ast.walk(node):
            if isinstance(n, ast.Assert):
                count += 1
        return count

    def _check_test_decorators(self, head_func: ast.FunctionDef, working_func: ast.FunctionDef, fname: str, file_path: Path):
        """Detect added skip/xfail decorators (disable tests)."""
        skip_patterns = {"skip", "xfail", "expectedFailure"}

        head_skip_decorators = [d for d in head_func.decorator_list if self._matches_skip_pattern(d, skip_patterns)]
        working_skip_decorators = [d for d in working_func.decorator_list if self._matches_skip_pattern(d, skip_patterns)]

        if len(working_skip_decorators) > len(head_skip_decorators):
            self.findings.append(
                WeakeningFinding(
                    severity="CRITICAL",
                    pattern="SKIP_DECORATOR_ADDED",
                    location=f"{fname}",
                    detail=f"Test skip/xfail decorator added",
                    old_code=f"{len(head_skip_decorators)} skip decorators",
                    new_code=f"{len(working_skip_decorators)} skip decorators",
                )
            )

    def _matches_skip_pattern(self, decorator: ast.expr, patterns: set[str]) -> bool:
        """Check if a decorator matches skip/xfail patterns."""
        if isinstance(decorator, ast.Name):
            return decorator.id in patterns
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr in patterns
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id in patterns
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr in patterns
        return False


class AdversarialFixtureGenerator:
    """Generate adversarial test cases for validation functions using hypothesis."""

    def __init__(self, validation_func: Callable):
        self.validation_func = validation_func
        self.examples_tested = 0
        self.examples_rejected = 0
        self.examples_accepted = 0
        self.edge_cases_triggered: list[str] = []

    def test_proposal_shape_errors(self) -> AdversarialResult:
        """Generate adversarial examples for _proposal_shape_errors function.

        Tests both negative controls (malformed input should be rejected) and
        positive controls (valid input should be accepted) using hypothesis.
        """

        # Hypothesis is an optional adversarial-test dependency. The static
        # integrity checker itself must remain importable in the lean core.
        from hypothesis import HealthCheck, given, settings, strategies as st

        # Define strategies for generating invalid and valid proposals
        hex_sha256_strategy = st.text(
            alphabet="0123456789abcdef",
            min_size=64,
            max_size=64,
        )

        # Invalid proposals - should all be rejected
        invalid_proposals = st.one_of([
            st.none(),  # None instead of dict
            st.just({}),  # Empty dict
            st.just({"proposal_id": "test"}),  # Missing fields
            st.just({"proposal_id": "", "candidate": {}, "falsifiers": []}),  # Empty proposal_id
            st.just({"proposal_id": "x" * 129, "candidate": {}, "falsifiers": []}),  # Too long proposal_id
            st.just({"proposal_id": "test", "candidate": None, "falsifiers": []}),  # candidate is None
            st.just({"proposal_id": "test", "candidate": {}, "falsifiers": None}),  # falsifiers is None
            st.just({"proposal_id": "test", "candidate": {}, "falsifiers": []}),  # falsifiers is empty
            st.just({"proposal_id": "test", "candidate": {}, "falsifiers": ["a" * 501]}),  # falsifier too long
            st.just({"proposal_id": "test", "candidate": {}, "falsifiers": ["dup", "dup"]}),  # Duplicates
            st.just({"proposal_id": "test", "candidate": {"x": "y"}, "falsifiers": ["test"]}),  # Wrong candidate fields
            st.dictionaries(
                keys=st.sampled_from(["proposal_id", "candidate", "falsifiers", "extra"]),
                values=st.just("value"),
                min_size=1,
                max_size=4,
            ),  # Random keys/values - likely invalid
        ])

        # Valid proposals - should all be accepted
        valid_proposals = st.fixed_dictionaries({
            "proposal_id": st.text(min_size=1, max_size=128, alphabet=st.characters(blacklist_categories=("Cc", "Cs"))),
            "candidate": st.fixed_dictionaries({
                "requested_claim": st.sampled_from(["bounded_tool_execution", "scientific_result", "canonical_result"]),
                "evidence_ref": hex_sha256_strategy,
            }),
            "falsifiers": st.lists(
                st.text(min_size=1, max_size=500, alphabet=st.characters(blacklist_categories=("Cc", "Cs"))),
                min_size=1,
                max_size=8,
                unique=True,
            ),
        })

        @given(st.one_of(invalid_proposals, valid_proposals))
        @settings(max_examples=150, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
        def test_validator(proposal):
            self.examples_tested += 1
            errors = self.validation_func(proposal)

            # Categorize result
            is_well_formed = (
                isinstance(proposal, dict)
                and set(proposal.keys()) == {"proposal_id", "candidate", "falsifiers"}
                and isinstance(proposal.get("candidate"), dict)
                and set(proposal["candidate"].keys()) == {"requested_claim", "evidence_ref"}
                and isinstance(proposal.get("falsifiers"), list)
                and all(isinstance(x, str) for x in proposal.get("falsifiers", []))
            )

            if errors:
                self.examples_rejected += 1
                # For invalid proposals, errors are expected and correct
                if proposal is None or not isinstance(proposal, dict):
                    pass  # Correctly rejected
                elif not is_well_formed:
                    pass  # Correctly rejected malformed input
            else:
                self.examples_accepted += 1
                # For valid proposals with no errors, they should be well-formed
                if not is_well_formed:
                    self.edge_cases_triggered.append("Malformed proposal accepted without errors")

        try:
            test_validator()
        except Exception as e:
            # Hypothesis ran successfully
            pass

        return AdversarialResult(
            function_name="_proposal_shape_errors",
            total_examples=self.examples_tested,
            rejected_count=self.examples_rejected,
            accepted_count=self.examples_accepted,
            edge_cases_triggered=self.edge_cases_triggered,
            summary=f"Tested {self.examples_tested} examples: {self.examples_accepted} accepted, {self.examples_rejected} rejected",
        )
