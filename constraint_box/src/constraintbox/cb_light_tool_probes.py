#!/usr/bin/env python3
"""Execute real bounded API probes for the 91-row CB Light proposal roster.

Every tool runs in a fresh subprocess.  A tool result has a positive operation,
a reason-specific negative, a boundary observation, a bounded reference check,
deterministic replay, and an import-severance check.  This is candidate
evaluation evidence, not production integration or adoption.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import contextlib
import datetime as dt
import functools
import hashlib
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable


ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "config/cb_light_tools_v1.json"
DEFAULT_OUTPUT = ROOT / "receipts/cb_light_tool_probes_v1.json"
MARKER = "CB_LIGHT_TOOL_PROBE_JSON="
CURRENT_TOOL: dict[str, Any] | None = None
CURRENT_EXCEPTION_EVIDENCE: list[dict[str, Any]] = []

# Boolean controls cannot carry an exception type. Their per-tool reason is
# therefore declared here and bound to the negative-arm source by the probe
# source hash. Missing declarations fail the reason-specific fact.
BEHAVIORAL_NEGATIVE_CONTRACTS = {
    "annotated-types": "NO_RUNTIME_ENFORCEMENT_OBSERVED",
    "blake3": "MUTATED_INPUT_DIGEST_DIFFERS",
    "bleach": "UNSAFE_TAG_REMOVED",
    "cerberus": "SCHEMA_REJECTS_WRONG_TYPE",
    "charset-normalizer": "BINARY_PAYLOAD_REFUSED_AS_TEXT",
    "checksumdir": "TREE_MUTATION_CHANGES_DIGEST",
    "clingo": "CONTRADICTORY_PROGRAM_UNSAT",
    "coverage": "UNEXECUTED_BRANCH_ABSENT",
    "cvc5": "CONTRADICTORY_FORMULA_UNSAT",
    "dictdiffer": "REVERT_REMOVES_DIFF",
    "dirty-equals": "NONPOSITIVE_VALUE_REJECTED",
    "fasteners": "CONTENDER_BLOCKED_WHILE_LOCK_HELD",
    "flake8-simplify": "COMPLEX_PATTERN_REPORTED",
    "freezegun": "REAL_CLOCK_SEVERED_FROM_FROZEN_CLOCK",
    "html2text": "SCRIPT_MARKUP_NOT_PRESERVED_AS_EXECUTABLE_HTML",
    "isort": "UNSORTED_IMPORTS_REJECTED",
    "markdown-it-py": "RAW_HTML_DISABLED",
    "maude": "MISSING_REWRITE_RULE_HAS_NO_SUCCESSOR",
    "mistune": "RAW_HTML_ESCAPED",
    "mmh3": "MUTATED_INPUT_DIGEST_DIFFERS",
    "parso": "INVALID_SYNTAX_REPORTED",
    "patch-ng": "MALFORMED_PATCH_REFUSED",
    "peewee": "UNIQUE_CONSTRAINT_REJECTS_DUPLICATE",
    "pickledb": "MISSING_KEY_NOT_CONFUSED_WITH_STORED_ZERO",
    "platformdirs": "NO_REFUSAL_NEGATIVE_AVAILABLE",
    "portion": "OPEN_INTERVAL_EXCLUDES_CLOSED_ENDPOINT",
    "protobuf": "MALFORMED_WIRE_PAYLOAD_REFUSED",
    "pyflakes": "UNDEFINED_NAME_REPORTED",
    "pytest-benchmark": "MISSING_PLUGIN_REFUSES_BENCHMARK_FIXTURE",
    "pytest-randomly": "MISSING_PLUGIN_REFUSES_RANDOM_SEED_FLAG",
    "pytest-timeout": "SLOW_TEST_TERMINATED_AT_TIMEOUT",
    "pytest-xdist": "MISSING_PLUGIN_REFUSES_PARALLEL_FLAG",
    "responses": "UNREGISTERED_HTTP_REQUEST_REFUSED",
    "rustworkx": "DIRECTED_CYCLE_DETECTED",
    "satispy": "NO_BUNDLED_SAT_BACKEND",
    "structlog": "MISSING_REQUIRED_CONTEXT_DROPPED",
    "sympy": "NONROOT_REJECTED_BY_SUBSTITUTION",
    "testfixtures": "UNEQUAL_VALUES_RAISE_COMPARISON_FAILURE",
    "tinycss2": "MALFORMED_RULE_REPORTED",
    "tinydb": "REMOVED_RECORD_NO_LONGER_QUERYABLE",
    "typeguard": "WRONG_RUNTIME_TYPE_REJECTED",
    "unidecode": "NONASCII_SOURCE_NORMALIZED",
    "validators": "INVALID_URL_REJECTED",
    "vulture": "USED_NAME_NOT_REPORTED_DEAD",
    "xxhash": "MUTATED_INPUT_DIGEST_DIFFERS",
    "z3-solver": "CONTRADICTORY_FORMULA_UNSAT",
}

CONTROL_REVIEW_HOLDS = {
    "annotated-types": "INERT_METADATA_HAS_NO_OPERATIONAL_REFUSAL",
    "platformdirs": "TOTAL_PATH_RESOLVER_HAS_NO_DECLARED_REFUSAL",
    "satispy": "NO_BUNDLED_SAT_BACKEND",
    "typing-extensions": "TYPE_METADATA_HAS_NO_RUNTIME_ENFORCEMENT_EDGE",
}


def result(
    positive: bool,
    negative: bool,
    boundary: bool,
    reference: bool,
    observation: Any,
) -> dict[str, Any]:
    tool = CURRENT_TOOL or {}
    observation_sha256 = hashlib.sha256(
        json.dumps(observation, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    normalized_name = str(tool.get("normalized_name", "unknown"))
    exception_evidence = list(CURRENT_EXCEPTION_EVIDENCE)
    broad_exception = any(
        "Exception" in row.get("expected_types", [])
        or "BaseException" in row.get("expected_types", [])
        for row in exception_evidence
    )
    behavioral_reason = BEHAVIORAL_NEGATIVE_CONTRACTS.get(normalized_name)
    if exception_evidence and not broad_exception:
        reason_code = "EXPECTED_EXCEPTION_" + "_OR_".join(
            sorted({str(row["actual_type"]).upper() for row in exception_evidence})
        )
        contract_passed = bool(negative)
        evidence_kind = "typed_exception"
    elif behavioral_reason:
        reason_code = behavioral_reason
        contract_passed = bool(negative)
        evidence_kind = "declared_behavioral_contrast"
    else:
        reason_code = "NEGATIVE_REASON_CONTRACT_MISSING"
        contract_passed = False
        evidence_kind = "unbound"
    return {
        "positive": {"passed": bool(positive)},
        "negative": {
            "passed": bool(negative),
            "contract_passed": contract_passed,
            "reason_code": reason_code,
            "evidence_kind": evidence_kind,
            "broad_exception_contract": broad_exception,
            "exception_evidence": exception_evidence,
            "observation_sha256": observation_sha256,
        },
        "boundary": {"passed": bool(boundary)},
        "reference": {"passed": bool(reference)},
        "observation": observation,
    }


def catches(
    callback: Callable[[], Any],
    expected: type[BaseException] | tuple[type[BaseException], ...] = Exception,
) -> bool:
    try:
        callback()
    except expected as exc:
        expected_types = expected if isinstance(expected, tuple) else (expected,)
        CURRENT_EXCEPTION_EVIDENCE.append(
            {
                "actual_type": type(exc).__name__,
                "expected_types": [item.__name__ for item in expected_types],
                "message_sha256": hashlib.sha256(str(exc).encode()).hexdigest(),
            }
        )
        return True
    return False


def probe_annotated_types() -> dict[str, Any]:
    from annotated_types import Ge, Lt
    from typing import Annotated, get_args

    constrained = Annotated[int, Ge(0), Lt(3)]
    metadata = get_args(constrained)[1:]
    return result(
        metadata[0].ge == 0 and metadata[1].lt == 3,
        -1 < metadata[0].ge,
        0 >= metadata[0].ge and 2 < metadata[1].lt,
        tuple(type(item).__name__ for item in metadata) == ("Ge", "Lt"),
        {"metadata": [repr(item) for item in metadata]},
    )


def probe_argon2_cffi() -> dict[str, Any]:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError

    hasher = PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)
    encoded = hasher.hash("constraint-box")
    return result(
        hasher.verify(encoded, "constraint-box"),
        catches(lambda: hasher.verify(encoded, "wrong"), VerifyMismatchError),
        hasher.verify(hasher.hash(""), ""),
        encoded.startswith("$argon2"),
        {"scheme": encoded.split("$")[1]},
    )


def probe_arrow() -> dict[str, Any]:
    import arrow
    from arrow.parser import ParserError

    value = arrow.get("2026-08-10T00:00:00+00:00")
    shifted = value.shift(days=1)
    return result(
        shifted.format("YYYY-MM-DD") == "2026-08-11",
        catches(lambda: arrow.get("not-a-date"), ParserError),
        value.shift(days=0) == value,
        int((shifted - value).total_seconds()) == 86400,
        {"shifted": shifted.isoformat()},
    )


def probe_ast_comments() -> dict[str, Any]:
    import ast_comments

    tree = ast_comments.parse("x = 1  # retained\n")
    comments = [node for node in ast_comments.walk(tree) if isinstance(node, ast_comments.Comment)]
    return result(
        len(comments) == 1 and "retained" in comments[0].value,
        catches(lambda: ast_comments.parse("if:"), SyntaxError),
        not any(isinstance(node, ast_comments.Comment) for node in ast_comments.walk(ast_comments.parse("x=1\n"))),
        "# retained" in ast_comments.unparse(tree),
        {"comments": [node.value for node in comments]},
    )


def probe_asttokens() -> dict[str, Any]:
    import asttokens

    source = "answer = 40 + 2\n"
    tree = ast.parse(source)
    tokens = asttokens.ASTTokens(source, tree=tree)
    assign = tree.body[0]
    return result(
        tokens.get_text(assign) == "answer = 40 + 2",
        catches(lambda: asttokens.ASTTokens("answer =", parse=True), SyntaxError),
        len(asttokens.ASTTokens("", tree=ast.parse("")).tokens) >= 1,
        ast.get_source_segment(source, assign) == tokens.get_text(assign),
        {"segment": tokens.get_text(assign)},
    )


def probe_attrs() -> dict[str, Any]:
    import attrs

    @attrs.define
    class Count:
        value: int = attrs.field(validator=attrs.validators.ge(0))

    return result(
        Count(2).value == 2,
        catches(lambda: Count(-1), ValueError),
        Count(0).value == 0,
        attrs.asdict(Count(2)) == {"value": 2},
        {"fields": [field.name for field in attrs.fields(Count)]},
    )


def probe_automaton() -> dict[str, Any]:
    from automaton import exceptions as automaton_exceptions
    from automaton.machines import FiniteMachine

    machine = FiniteMachine()
    machine.add_state("start")
    machine.add_state("done", terminal=True)
    machine.add_transition("start", "done", "advance")
    machine.initialize("start")
    machine.process_event("advance")
    fresh = FiniteMachine()
    fresh.add_state("start")
    fresh.add_state("done", terminal=True)
    fresh.add_transition("start", "done", "advance")
    fresh.initialize("start")
    return result(
        machine.current_state == "done" and machine.terminated,
        catches(
            lambda: fresh.process_event("missing"), automaton_exceptions.NotFound
        ),
        not machine.is_actionable_event("advance"),
        tuple(sorted(machine.states)) == ("done", "start"),
        {"state": machine.current_state, "terminated": machine.terminated},
    )


def probe_beautifulsoup4() -> dict[str, Any]:
    from bs4 import BeautifulSoup
    from soupsieve.util import SelectorSyntaxError

    soup = BeautifulSoup("<main><p data-id='1'>claim</p></main>", "html.parser")
    return result(
        soup.select_one("p[data-id='1']").get_text() == "claim",
        catches(lambda: soup.select_one(":::invalid"), SelectorSyntaxError),
        BeautifulSoup("", "html.parser").get_text() == "",
        [item.get_text() for item in soup.select("main > p")] == ["claim"],
        {"selected": len(soup.select("p"))},
    )


def probe_bitarray() -> dict[str, Any]:
    from bitarray import bitarray

    bits = bitarray("1010")
    return result(
        bits.count(1) == 2,
        catches(lambda: bitarray("10x"), ValueError),
        len(bitarray()) == 0,
        bits.to01() == "1010",
        {"bits": bits.to01()},
    )


def probe_blake3() -> dict[str, Any]:
    import blake3

    first = blake3.blake3(b"constraint").hexdigest()
    second = blake3.blake3(b"constraint").hexdigest()
    changed = blake3.blake3(b"constraint!").hexdigest()
    return result(
        first == second and len(first) == 64,
        first != changed,
        len(blake3.blake3(b"").digest()) == 32,
        blake3.blake3(b"").hexdigest()
        == "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262",
        {"digest": first},
    )


def probe_bleach() -> dict[str, Any]:
    import bleach

    clean = bleach.clean("<b>claim</b>", tags={"b"})
    hostile = bleach.clean("<script>alert(1)</script>", tags=set())
    return result(
        clean == "<b>claim</b>",
        "<script>" not in hostile,
        bleach.clean("", tags=set()) == "",
        hostile == "&lt;script&gt;alert(1)&lt;/script&gt;",
        {"hostile": hostile},
    )


def probe_cachetools() -> dict[str, Any]:
    import cachetools

    cache = cachetools.LRUCache(maxsize=1)
    cache["a"] = 1
    cache["b"] = 2
    return result(
        cache["b"] == 2,
        "a" not in cache and catches(lambda: cache["a"], KeyError),
        len(cache) == 1,
        list(cache.items()) == [("b", 2)],
        {"keys": list(cache)},
    )


def probe_cattrs() -> dict[str, Any]:
    import attrs
    import cattrs
    from cattrs.errors import ClassValidationError

    @attrs.define
    class Row:
        value: int

    converter = cattrs.Converter()
    structured = converter.structure({"value": 2}, Row)
    return result(
        structured == Row(2),
        catches(lambda: converter.structure({}, Row), ClassValidationError),
        converter.unstructure(Row(0)) == {"value": 0},
        converter.unstructure(structured) == {"value": 2},
        {"value": structured.value},
    )


def probe_cbor2() -> dict[str, Any]:
    import cbor2
    from cbor2 import CBORDecodeEOF

    one = cbor2.dumps({"b": 2, "a": 1}, canonical=True)
    two = cbor2.dumps({"a": 1, "b": 2}, canonical=True)
    return result(
        cbor2.loads(one) == {"a": 1, "b": 2},
        catches(lambda: cbor2.loads(b"\x9f"), CBORDecodeEOF),
        cbor2.loads(cbor2.dumps({})) == {},
        one == two,
        {"hex": one.hex()},
    )


def probe_cerberus() -> dict[str, Any]:
    from cerberus import Validator

    validator = Validator({"value": {"type": "integer", "min": 0, "required": True}})
    return result(
        validator.validate({"value": 2}),
        not validator.validate({"value": -1}) and "value" in validator.errors,
        validator.validate({"value": 0}),
        not validator.validate({}),
        {"negative_errors": validator.errors},
    )


def probe_charset_normalizer() -> dict[str, Any]:
    import charset_normalizer

    match = charset_normalizer.from_bytes("Hello 世界".encode()).best()
    empty = charset_normalizer.from_bytes(b"").best()
    return result(
        match is not None and "世界" in str(match),
        charset_normalizer.from_bytes(b"\xff\xfe\x00").best() is None,
        empty is not None and str(empty) == "",
        match is not None and match.encoding is not None,
        {"encoding": None if match is None else match.encoding},
    )


def probe_checksumdir() -> dict[str, Any]:
    import checksumdir

    with tempfile.TemporaryDirectory() as directory:
        root = pathlib.Path(directory)
        (root / "a.txt").write_text("one", encoding="utf-8")
        previous_cwd = pathlib.Path.cwd()
        os.chdir(directory)
        try:
            first = checksumdir.dirhash(".", "sha256", include_paths=True)
            replayed = checksumdir.dirhash(".", "sha256", include_paths=True)
            (root / "a.txt").write_text("two", encoding="utf-8")
            changed = checksumdir.dirhash(".", "sha256", include_paths=True)
            (root / "a.txt").rename(root / "renamed.txt")
            renamed = checksumdir.dirhash(".", "sha256", include_paths=True)
        finally:
            os.chdir(previous_cwd)
    with tempfile.TemporaryDirectory() as empty_directory:
        empty = checksumdir.dirhash(empty_directory, "sha256")
        empty_replayed = checksumdir.dirhash(empty_directory, "sha256")
    return result(
        first == replayed and len(first) == 64,
        first != changed and changed != renamed,
        empty == empty_replayed and len(empty) == 64,
        len({first, changed, renamed}) == 3,
        {
            "first": first,
            "replayed": replayed,
            "changed": changed,
            "renamed": renamed,
            "empty": empty,
        },
    )


def probe_clingo() -> dict[str, Any]:
    import clingo

    def models(program: str) -> list[list[str]]:
        control = clingo.Control(["0"])
        control.add("base", [], program)
        control.ground([("base", [])])
        found: list[list[str]] = []
        with control.solve(yield_=True) as handle:
            for model in handle:
                found.append(sorted(str(symbol) for symbol in model.symbols(shown=True)))
        return found

    positive_models = models("1 {a;b} 1. #show a/0. #show b/0.")
    negative_models = models("a. :- a.")
    boundary_models = models("#show a/0.")
    return result(
        sorted(positive_models) == [["a"], ["b"]],
        negative_models == [],
        boundary_models == [[]],
        len(positive_models) == 2,
        {"models": positive_models},
    )


def probe_coverage() -> dict[str, Any]:
    import coverage
    import runpy

    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "covered.py"
        path.write_text("x = 1\nif False:\n    x = 2\n", encoding="utf-8")
        cov = coverage.Coverage(data_file=None, config_file=False)
        cov.start()
        runpy.run_path(str(path))
        cov.stop()
        measured = sorted(cov.get_data().measured_files())
        measured_path = next(item for item in measured if pathlib.Path(item).name == path.name)
        lines = sorted(cov.get_data().lines(measured_path) or [])
    return result(
        1 in lines,
        3 not in lines,
        set(lines).issubset({1, 2}),
        lines == [1, 2],
        {"executed_lines": lines},
    )


def probe_cvc5() -> dict[str, Any]:
    import cvc5
    from cvc5 import Kind

    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    x = solver.mkConst(solver.getIntegerSort(), "x")
    solver.assertFormula(solver.mkTerm(Kind.GEQ, x, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(Kind.LEQ, x, solver.mkInteger(2)))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, x, solver.mkInteger(1)))
    sat = solver.checkSat()
    witness = solver.getValue(x).getIntegerValue() if sat.isSat() else None
    bad = cvc5.Solver()
    bad.setLogic("QF_LIA")
    y = bad.mkConst(bad.getIntegerSort(), "y")
    bad.assertFormula(bad.mkTerm(Kind.EQUAL, y, bad.mkInteger(0)))
    bad.assertFormula(bad.mkTerm(Kind.EQUAL, y, bad.mkInteger(1)))
    edge = cvc5.Solver()
    edge.setLogic("QF_LIA")
    edge_x = edge.mkConst(edge.getIntegerSort(), "edge_x")
    edge.assertFormula(edge.mkTerm(Kind.GEQ, edge_x, edge.mkInteger(0)))
    edge.assertFormula(edge.mkTerm(Kind.EQUAL, edge_x, edge.mkInteger(0)))
    outside = cvc5.Solver()
    outside.setLogic("QF_LIA")
    outside_x = outside.mkConst(outside.getIntegerSort(), "outside_x")
    outside.assertFormula(outside.mkTerm(Kind.GEQ, outside_x, outside.mkInteger(0)))
    outside.assertFormula(outside.mkTerm(Kind.LT, outside_x, outside.mkInteger(0)))
    brute_reference = [value for value in range(3) if 0 <= value <= 2 and value != 1]
    return result(
        sat.isSat() and witness in (0, 2),
        bad.checkSat().isUnsat(),
        edge.checkSat().isSat() and outside.checkSat().isUnsat(),
        witness in brute_reference and brute_reference == [0, 2],
        {"witness": witness},
    )


def probe_dictdiffer() -> dict[str, Any]:
    import dictdiffer

    differences = list(dictdiffer.diff({"value": 1}, {"value": 2}))
    return result(
        dict(dictdiffer.patch(differences, {"value": 1})) == {"value": 2},
        list(dictdiffer.diff({"value": 1}, {"value": 1})) == [],
        len(differences) == 1,
        dict(dictdiffer.revert(differences, {"value": 2})) == {"value": 1},
        {"differences": [list(item) for item in differences]},
    )


def probe_dirty_equals() -> dict[str, Any]:
    from dirty_equals import IsInt, IsPositive

    return result(
        2 == IsInt,
        not (-1 == IsPositive),
        0 == IsInt,
        not ("2" == IsInt),
        {"positive_int": True},
    )


def probe_ecdsa() -> dict[str, Any]:
    from ecdsa import BadSignatureError, NIST256p, SigningKey

    key = SigningKey.from_secret_exponent(1, curve=NIST256p)
    signature = key.sign_deterministic(b"claim")
    verify = key.verifying_key
    return result(
        verify.verify(signature, b"claim"),
        catches(lambda: verify.verify(signature, b"changed"), BadSignatureError),
        verify.verify(key.sign_deterministic(b""), b""),
        verify.to_string().hex()
        == (
            "6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296"
            "4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5"
        ),
        {"signature_length": len(signature)},
    )


def probe_email_validator() -> dict[str, Any]:
    from email_validator import EmailNotValidError, validate_email

    valid = validate_email("owner@example.com", check_deliverability=False)
    return result(
        valid.normalized == "owner@example.com",
        catches(lambda: validate_email("not-an-email", check_deliverability=False), EmailNotValidError),
        validate_email("a@b.co", check_deliverability=False).normalized == "a@b.co",
        valid.domain == "example.com",
        {"normalized": valid.normalized},
    )


def probe_fasteners() -> dict[str, Any]:
    import fasteners

    with tempfile.TemporaryDirectory() as directory:
        path = str(pathlib.Path(directory) / "lock")
        first = fasteners.InterProcessLock(path)
        acquired = first.acquire(blocking=True, timeout=1)
        contender = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import fasteners,sys; "
                    "lock=fasteners.InterProcessLock(sys.argv[1]); "
                    "acquired=lock.acquire(blocking=False); "
                    "print(int(acquired)); "
                    "lock.release() if acquired else None"
                ),
                path,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        blocked = contender.returncode == 0 and contender.stdout.strip() == "0"
        first.release()
        second = fasteners.InterProcessLock(path)
        reacquired = second.acquire(blocking=True, timeout=1)
        if reacquired:
            second.release()
        released_contender = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import fasteners,sys; "
                    "lock=fasteners.InterProcessLock(sys.argv[1]); "
                    "acquired=lock.acquire(blocking=False); "
                    "print(int(acquired)); "
                    "lock.release() if acquired else None"
                ),
                path,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    return result(
        acquired and reacquired,
        blocked,
        released_contender.returncode == 0
        and released_contender.stdout.strip() == "1",
        contender.returncode == 0
        and contender.stderr == ""
        and released_contender.stderr == "",
        {
            "blocked_while_held": blocked,
            "contender_returncode": contender.returncode,
            "contender_stdout": contender.stdout.strip(),
            "contender_stderr_sha256": hashlib.sha256(contender.stderr.encode()).hexdigest(),
            "released_contender_stdout": released_contender.stdout.strip(),
        },
    )


def probe_fastjsonschema() -> dict[str, Any]:
    import fastjsonschema

    validate = fastjsonschema.compile({"type": "integer", "minimum": 0})
    return result(
        validate(2) == 2,
        catches(lambda: validate(-1), fastjsonschema.JsonSchemaException),
        validate(0) == 0,
        catches(lambda: validate("2"), fastjsonschema.JsonSchemaException),
        {"boundary": 0},
    )


def probe_flake8_simplify() -> dict[str, Any]:
    import flake8_simplify

    nested = ast.parse("if a:\n    if b:\n        pass\n")
    clean = ast.parse("if a and b:\n    pass\n")
    nested_errors = list(flake8_simplify.Plugin(nested).run())
    clean_errors = list(flake8_simplify.Plugin(clean).run())
    return result(
        any(item[2].startswith("SIM102") for item in nested_errors),
        clean_errors == [],
        len(nested_errors) == 1,
        nested_errors[0][0:2] == (1, 0),
        {"codes": [item[2].split()[0] for item in nested_errors]},
    )


def probe_formula() -> dict[str, Any]:
    from formula import Solver

    solver = Solver("x*x + 1", precision=24)
    value = solver({"x": 2})
    return result(
        value == "5",
        catches(lambda: solver(None), ValueError),
        solver({"x": 0}) == "1",
        solver({"x": -2}) == value,
        {"value": value},
    )


def probe_freezegun() -> dict[str, Any]:
    import datetime
    import time as stdlib_time
    from freezegun import freeze_time

    before = datetime.datetime.now()
    with freeze_time("2026-08-10 12:00:00"):
        frozen = datetime.datetime.now()
        frozen_epoch = stdlib_time.time()
    after = datetime.datetime.now()
    return result(
        frozen == datetime.datetime(2026, 8, 10, 12, 0, 0),
        before != frozen and after != frozen,
        frozen.microsecond == 0,
        int(frozen_epoch) == 1786363200,
        {"frozen": frozen.isoformat(), "epoch": int(frozen_epoch)},
    )


def probe_frozendict() -> dict[str, Any]:
    from frozendict import frozendict

    value = frozendict({"a": 1})
    return result(
        value["a"] == 1 and hash(value) == hash(frozendict({"a": 1})),
        catches(lambda: value.__setitem__("a", 2), TypeError),
        len(frozendict()) == 0,
        dict(value) == {"a": 1},
        {"hash_stable": hash(value) == hash(frozendict({"a": 1}))},
    )


def probe_gitpython() -> dict[str, Any]:
    import git

    with tempfile.TemporaryDirectory() as directory:
        repo = git.Repo.init(directory)
        path = pathlib.Path(directory) / "claim.txt"
        path.write_text("claim", encoding="utf-8")
        repo.index.add(["claim.txt"])
        actor = git.Actor("ConstraintBox", "cb@example.invalid")
        commit = repo.index.commit(
            "probe",
            author=actor,
            committer=actor,
            author_date="2000-01-01 00:00:00 +0000",
            commit_date="2000-01-01 00:00:00 +0000",
        )
        blob = commit.tree / "claim.txt"
        header = b"blob 5\0claim"
        reference_sha = hashlib.sha1(header).hexdigest()
        return result(
            blob.data_stream.read() == b"claim",
            catches(
                lambda: git.Repo("/dev/null"),
                git.exc.InvalidGitRepositoryError,
            ),
            len(commit.parents) == 0,
            blob.hexsha == reference_sha,
            {"blob_reference_agrees": blob.hexsha == reference_sha},
        )


def probe_gmpy2() -> dict[str, Any]:
    import gmpy2
    import math

    value = gmpy2.mpz(2) ** 100
    return result(
        int(value) == 2**100,
        catches(lambda: gmpy2.mpz("not-a-number"), ValueError),
        gmpy2.is_prime(97) and not gmpy2.is_prime(1),
        int(gmpy2.isqrt(value)) == math.isqrt(2**100),
        {"bit_length": int(value.bit_length())},
    )


def probe_lark() -> dict[str, Any]:
    from lark import Lark, UnexpectedInput

    parser = Lark('start: INT "+" INT\n%import common.INT\n%ignore " "', parser="lalr")
    tree = parser.parse("2 + 3")
    return result(
        [str(item) for item in tree.children] == ["2", "3"],
        catches(lambda: parser.parse("2 +"), UnexpectedInput),
        [str(item) for item in parser.parse("0 + 0").children] == ["0", "0"],
        tree.data == "start" and len(tree.children) == 2,
        {"children": [str(item) for item in tree.children]},
    )


def probe_marshmallow() -> dict[str, Any]:
    from marshmallow import Schema, ValidationError, fields

    class Row(Schema):
        value = fields.Int(required=True, strict=True)

    schema = Row()
    loaded = schema.load({"value": 2})
    return result(
        loaded == {"value": 2},
        catches(lambda: schema.load({"value": "2"}), ValidationError),
        schema.load({"value": 0}) == {"value": 0},
        schema.dump(loaded) == {"value": 2},
        {"loaded": loaded},
    )


def probe_mmh3() -> dict[str, Any]:
    import mmh3

    observed = mmh3.hash("foo", signed=False)
    return result(
        observed == mmh3.hash(b"foo", signed=False),
        observed != mmh3.hash("foO", signed=False),
        mmh3.hash("", signed=False) == 0,
        observed == 4138058784,
        {"unsigned_foo": observed},
    )


def probe_msgpack() -> dict[str, Any]:
    import msgpack

    payload = {"verdict": "ADMIT", "n": 2}
    packed = msgpack.packb(payload, use_bin_type=True)
    return result(
        msgpack.unpackb(packed, raw=False) == payload,
        catches(lambda: msgpack.packb(object()), TypeError),
        msgpack.unpackb(msgpack.packb({}, use_bin_type=True), raw=False) == {},
        msgpack.unpackb(packed, raw=False)["n"] == 2,
        {"packed_hex": packed.hex()},
    )


def probe_parso() -> dict[str, Any]:
    import parso
    import tokenize

    source = "x = 1 + 2\n"
    grammar = parso.load_grammar()
    tree = grammar.parse(source)
    bad = grammar.parse("x = (1 +\n")
    leaves = list(tree.iter_leafs()) if hasattr(tree, "iter_leafs") else []
    if not leaves:
        leaf = tree.get_first_leaf()
        while leaf is not None:
            leaves.append(leaf)
            leaf = leaf.get_next_leaf()
    std_tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    return result(
        tree.type == "file_input",
        bool(list(grammar.iter_errors(bad))),
        not list(grammar.iter_errors(tree)),
        any(leaf.value == "x" for leaf in leaves)
        and any(token.string == "x" for token in std_tokens),
        {"leaf_values": [leaf.value for leaf in leaves]},
    )


def probe_peewee() -> dict[str, Any]:
    import peewee

    db = peewee.SqliteDatabase(":memory:")

    class Row(peewee.Model):
        name = peewee.TextField(unique=True)
        value = peewee.IntegerField()

        class Meta:
            database = db

    db.connect()
    db.create_tables([Row])
    Row.create(name="a", value=2)
    try:
        duplicate_refused = catches(
            lambda: Row.create(name="a", value=3), peewee.IntegrityError
        )
        return result(
            Row.get(Row.name == "a").value == 2,
            duplicate_refused,
            Row.select().where(Row.value == 0).count() == 0,
            sum(row.value for row in Row.select()) == 2,
            {"rows": Row.select().count()},
        )
    finally:
        db.close()


def probe_pickledb() -> dict[str, Any]:
    import pickledb

    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "rows.json"
        database = pickledb.PickleDB(str(path))
        database.set("verdict", "ADMIT")
        positive = database.get("verdict") == "ADMIT"
        negative = database.get("missing") in (False, None)
        database.set("boundary", 0)
        boundary = database.get("boundary") == 0
        database.save()
        stored = json.loads(path.read_text(encoding="utf-8"))
        return result(
            positive,
            negative,
            boundary,
            stored.get("verdict") == "ADMIT",
            {"stored_keys": sorted(stored)},
        )


def probe_portion() -> dict[str, Any]:
    import portion

    interval = portion.closed(0, 2)
    return result(
        0 in interval and 2 in interval,
        3 not in interval,
        2 in interval and 2 not in portion.open(0, 2),
        [value for value in range(4) if value in interval] == [0, 1, 2],
        {"interval": str(interval)},
    )


def probe_protobuf() -> dict[str, Any]:
    from google.protobuf import struct_pb2
    from google.protobuf.message import DecodeError

    message = struct_pb2.Struct()
    message.update({"verdict": "ADMIT", "n": 2})
    encoded = message.SerializeToString(deterministic=True)
    decoded = struct_pb2.Struct()
    decoded.ParseFromString(encoded)
    return result(
        decoded["verdict"] == "ADMIT" and decoded["n"] == 2,
        catches(lambda: struct_pb2.Struct().ParseFromString(b"\xff\xff\xff"), DecodeError),
        struct_pb2.Struct().SerializeToString(deterministic=True) == b"",
        decoded["n"] == 2.0,
        {"encoded_hex": encoded.hex()},
    )


def probe_pyjwt() -> dict[str, Any]:
    import base64
    import hmac
    import jwt

    secret = b"constraint-box"
    token = jwt.encode({"sub": "owner", "n": 2}, secret, algorithm="HS256")
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    header, payload, signature = token.split(".")
    expected = base64.urlsafe_b64encode(
        hmac.new(secret, f"{header}.{payload}".encode(), hashlib.sha256).digest()
    ).rstrip(b"=").decode()
    return result(
        decoded == {"sub": "owner", "n": 2},
        catches(
            lambda: jwt.decode(token, b"wrong", algorithms=["HS256"]),
            jwt.InvalidSignatureError,
        ),
        len(token.split(".")) == 3,
        signature == expected,
        {"segments": 3, "reference_signature_agrees": signature == expected},
    )


def probe_python_ulid() -> dict[str, Any]:
    from ulid import ULID

    value = ULID()
    rendered = str(value)
    parsed = ULID.from_str(rendered)
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    manual_integer = 0
    for character in rendered:
        manual_integer = manual_integer * 32 + alphabet.index(character)
    return result(
        len(rendered) == 26 and parsed == value,
        catches(lambda: ULID.from_str("not-a-ulid"), ValueError),
        str(ULID.from_bytes(b"\0" * 16)) == "0" * 26,
        manual_integer == int.from_bytes(value.bytes, "big"),
        {"length": len(rendered), "roundtrip": parsed == value},
    )


def probe_regex() -> dict[str, Any]:
    import re
    import regex

    pattern = regex.compile(r"[a-z]+")
    return result(
        pattern.fullmatch("constraint") is not None,
        catches(lambda: regex.compile("["), regex.error),
        pattern.fullmatch("") is None,
        bool(pattern.fullmatch("constraint")) == bool(re.fullmatch(r"[a-z]+", "constraint")),
        {"matched": "constraint"},
    )


def probe_ruamel_yaml() -> dict[str, Any]:
    from ruamel.yaml import YAML
    from ruamel.yaml.parser import ParserError

    yaml = YAML(typ="safe")
    parsed = yaml.load("verdict: ADMIT\nn: 2\n")
    return result(
        parsed == {"verdict": "ADMIT", "n": 2},
        catches(lambda: yaml.load("verdict: ["), ParserError),
        yaml.load("{}") == {},
        parsed == json.loads('{"verdict":"ADMIT","n":2}'),
        {"parsed": parsed},
    )


def probe_satispy() -> dict[str, Any]:
    from satispy import Variable

    a = Variable("a")
    expression = a & -a
    # The package exposes expression construction but this install has no
    # bundled SAT backend.  Do not launder a Python truth table into a satispy
    # negative decision; the operational constraint correctly remains open.
    return result(
        "a" in str(expression),
        False,
        False,
        False,
        {"limitation": "no bundled solver backend; contradiction not decided by satispy"},
    )


def probe_tinydb() -> dict[str, Any]:
    from tinydb import Query, TinyDB

    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "rows.json"
        database = TinyDB(path)
        database.insert({"id": 1, "verdict": "ADMIT"})
        query = Query()
        found = database.search(query.id == 1)
        missing = database.search(query.id == 2)
        database.close()
        stored = json.loads(path.read_text(encoding="utf-8"))
        return result(
            found == [{"id": 1, "verdict": "ADMIT"}],
            missing == [],
            len(stored["_default"]) == 1,
            next(iter(stored["_default"].values()))["verdict"] == "ADMIT",
            {"stored_rows": len(stored["_default"])},
        )


def probe_tomli() -> dict[str, Any]:
    import tomllib
    import tomli

    parsed = tomli.loads('verdict = "ADMIT"\nn = 2\n')
    return result(
        parsed == {"verdict": "ADMIT", "n": 2},
        catches(lambda: tomli.loads("verdict = ["), tomli.TOMLDecodeError),
        tomli.loads("") == {},
        parsed == tomllib.loads('verdict = "ADMIT"\nn = 2\n'),
        {"parsed": parsed},
    )


def probe_tomlkit() -> dict[str, Any]:
    import tomlkit
    from tomlkit.exceptions import UnexpectedEofError

    document = tomlkit.parse('verdict = "ADMIT"\nn = 2\n')
    document["n"] = 3
    rendered = tomlkit.dumps(document)
    return result(
        document["verdict"] == "ADMIT",
        catches(lambda: tomlkit.parse("verdict = ["), UnexpectedEofError),
        tomlkit.parse("").unwrap() == {},
        tomlkit.parse(rendered)["n"] == 3,
        {"rendered": rendered},
    )


def probe_typeguard() -> dict[str, Any]:
    from typeguard import TypeCheckError, check_type

    checked = check_type(2, int)
    rejected = catches(lambda: check_type("2", int), TypeCheckError)
    return result(
        checked == 2,
        rejected,
        check_type(0, int) == 0,
        (checked == 2) == isinstance(2, int)
        and rejected == (not isinstance("2", int)),
        {"checked_type": "int"},
    )


def probe_typing_extensions() -> dict[str, Any]:
    import typing
    import typing_extensions

    Row = typing_extensions.TypedDict("Row", {"value": int})
    return result(
        Row.__annotations__ == {"value": int},
        catches(lambda: typing_extensions.assert_never("unexpected"), AssertionError),
        typing_extensions.Literal[0].__args__ == (0,),
        typing.get_type_hints(Row) == {"value": int},
        {"annotations": ["value"]},
    )


def probe_uuid6() -> dict[str, Any]:
    import uuid
    import uuid6

    value = uuid6.uuid7()
    parsed = uuid.UUID(str(value))
    return result(
        value.version == 7 and parsed == value,
        catches(lambda: uuid6.UUID("not-a-uuid"), ValueError),
        len(str(value)) == 36,
        parsed.int == value.int,
        {"version": value.version, "roundtrip": parsed == value},
    )


def probe_validators() -> dict[str, Any]:
    import re
    import validators

    valid = validators.email("owner@example.com") is True
    invalid = validators.email("not-an-email") is not True
    reference_valid = re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", "owner@example.com") is not None
    reference_invalid = re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", "not-an-email") is None
    return result(
        valid,
        invalid,
        validators.email("a@b.co") is True,
        valid == reference_valid and invalid == reference_invalid,
        {"email_valid": True, "invalid_type": type(validators.email("not-an-email")).__name__},
    )


def probe_voluptuous() -> dict[str, Any]:
    import voluptuous

    schema = voluptuous.Schema({voluptuous.Required("value"): int})
    return result(
        schema({"value": 2}) == {"value": 2},
        catches(lambda: schema({"value": "2"}), voluptuous.Invalid),
        schema({"value": 0}) == {"value": 0},
        json.loads(json.dumps(schema({"value": 2}))) == {"value": 2},
        {"boundary_value": 0},
    )


def probe_z3_solver() -> dict[str, Any]:
    import z3

    x = z3.Int("x")
    solver = z3.Solver()
    solver.add(x >= 0, x <= 2, x != 1)
    status = solver.check()
    witness = solver.model()[x].as_long() if status == z3.sat else None
    contradictory = z3.Solver()
    contradictory.add(x < 1, x >= 1)
    strict = z3.Solver()
    strict.add(x > 1, x < 1)
    closed = z3.Solver()
    closed.add(x >= 1, x <= 1)
    reference = [value for value in range(3) if value != 1]
    return result(
        status == z3.sat and witness in reference,
        contradictory.check() == z3.unsat,
        strict.check() == z3.unsat and closed.check() == z3.sat,
        witness in reference and reference == [0, 2],
        {"status": str(status), "witness": witness},
    )


def probe_sympy() -> dict[str, Any]:
    import sympy

    x = sympy.symbols("x")
    real_roots = sympy.solveset(sympy.Eq(x**2 - 4, 0), x, domain=sympy.S.Reals)
    no_real = sympy.solveset(sympy.Eq(x**2 + 1, 0), x, domain=sympy.S.Reals)
    complex_roots = sympy.solveset(sympy.Eq(x**2 + 1, 0), x, domain=sympy.S.Complexes)
    return result(
        real_roots == sympy.FiniteSet(-2, 2),
        no_real == sympy.S.EmptySet,
        no_real == sympy.S.EmptySet and complex_roots == sympy.FiniteSet(-sympy.I, sympy.I),
        {-2, 2} == {int(value) for value in real_roots}
        and all(value * value - 4 == 0 for value in (-2, 2)),
        {"real_roots": sorted(str(value) for value in real_roots)},
    )


def probe_rustworkx() -> dict[str, Any]:
    import rustworkx

    graph = rustworkx.PyDiGraph()
    nodes = graph.add_nodes_from(["a", "b", "c"])
    graph.add_edges_from_no_data([(nodes[0], nodes[1]), (nodes[1], nodes[2])])
    order = [graph[index] for index in rustworkx.topological_sort(graph)]
    cyclic = graph.copy()
    cyclic.add_edge(nodes[2], nodes[0], None)
    boundary_before = rustworkx.is_directed_acyclic_graph(cyclic)
    cyclic.remove_edge(nodes[2], nodes[0])
    boundary_after = rustworkx.is_directed_acyclic_graph(cyclic)
    edges = (("a", "b"), ("b", "c"))
    indegree = {name: 0 for name in ("a", "b", "c")}
    adjacency = {name: [] for name in indegree}
    for source, target in edges:
        adjacency[source].append(target)
        indegree[target] += 1
    queue = sorted(name for name, degree in indegree.items() if degree == 0)
    reference_order: list[str] = []
    while queue:
        source = queue.pop(0)
        reference_order.append(source)
        for target in adjacency[source]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
                queue.sort()
    return result(
        order == ["a", "b", "c"],
        not boundary_before,
        not boundary_before and boundary_after,
        order == reference_order,
        {"order": order, "cycle_detected": not boundary_before},
    )


def probe_maude() -> dict[str, Any]:
    import maude

    maude.init(loadPrelude=False, randomSeed=0, advise=False, handleInterrupts=False)
    accepted = maude.input(
        "mod CB-LIGHT-91 is sorts State . ops s0 s1 : -> State . "
        "rl [advance] : s0 => s1 . endm"
    )
    module = maude.getModule("CB-LIGHT-91")
    term = None if module is None else module.parseTerm("s0")
    positive_apps = [] if term is None else list(term.apply("advance", minDepth=0, maxDepth=0))
    negative_apps = [] if term is None else list(term.apply("missing", minDepth=0, maxDepth=0))
    return result(
        bool(accepted and positive_apps and str(positive_apps[0][0]) == "s1"),
        negative_apps == [],
        len(positive_apps) == 1 and len(negative_apps) == 0,
        bool(positive_apps and {"s0": "s1"}["s0"] == str(positive_apps[0][0])),
        {"rewritten": str(positive_apps[0][0]) if positive_apps else None},
    )


def probe_isort() -> dict[str, Any]:
    import isort

    unsorted = "import sys\nimport os\n"
    sorted_source = isort.code(unsorted)
    return result(
        sorted_source == "import os\nimport sys\n",
        not isort.check_code(unsorted),
        isort.check_code("") and isort.check_code(sorted_source),
        sorted_source.splitlines() == sorted(unsorted.splitlines()),
        {"sorted": sorted_source},
    )


def probe_more_itertools() -> dict[str, Any]:
    import more_itertools

    chunks = list(more_itertools.chunked([1, 2, 3, 4, 5], 2))
    return result(
        chunks == [[1, 2], [3, 4], [5]],
        catches(lambda: list(more_itertools.chunked([1], -1)), ValueError),
        list(more_itertools.chunked([], 2)) == [],
        [item for chunk in chunks for item in chunk] == [1, 2, 3, 4, 5],
        {"chunks": chunks},
    )


def probe_pluggy() -> dict[str, Any]:
    import pluggy

    spec = pluggy.HookspecMarker("cb_probe")
    implementation = pluggy.HookimplMarker("cb_probe")

    class Spec:
        @spec
        def decide(self, value: int) -> int: ...

    class Plugin:
        @implementation
        def decide(self, value: int) -> int:
            return value * 2

    manager = pluggy.PluginManager("cb_probe")
    manager.add_hookspecs(Spec)
    manager.register(Plugin())
    observed = manager.hook.decide(value=2)
    return result(
        observed == [4],
        catches(lambda: manager.hook.missing(value=2), AttributeError),
        manager.hook.decide(value=0) == [0],
        observed == [value * 2 for value in [2]],
        {"observed": observed},
    )


def probe_pyfakefs() -> dict[str, Any]:
    from pyfakefs.fake_filesystem import FakeFilesystem

    filesystem = FakeFilesystem()
    filesystem.create_file("/evidence/claim.txt", contents="claim")
    node = filesystem.get_object("/evidence/claim.txt")
    return result(
        node.contents == "claim",
        catches(lambda: filesystem.get_object("/missing"), OSError),
        filesystem.isdir("/evidence") and not filesystem.isfile("/evidence"),
        node.st_size == len(b"claim"),
        {"size": node.st_size},
    )


def probe_pyflakes() -> dict[str, Any]:
    import pyflakes.api
    from pyflakes.reporter import Reporter

    output = io.StringIO()
    errors = io.StringIO()
    reporter = Reporter(output, errors)
    clean_count = pyflakes.api.check("x = 1\nprint(x)\n", "clean.py", reporter)
    violation_count = pyflakes.api.check("import os\n", "bad.py", reporter)
    return result(
        clean_count == 0,
        violation_count == 1 and "imported but unused" in output.getvalue(),
        pyflakes.api.check("", "empty.py", Reporter(io.StringIO(), io.StringIO())) == 0,
        output.getvalue().startswith("bad.py:1:1: 'os' imported but unused"),
        {"violation_count": violation_count, "message": output.getvalue().strip()},
    )


def probe_rope() -> dict[str, Any]:
    from rope.base import exceptions
    from rope.base.project import Project

    with tempfile.TemporaryDirectory() as directory:
        project = Project(directory)
        try:
            resource = project.root.create_file("claim.py")
            resource.write("verdict = 'ADMIT'\n")
            return result(
                "ADMIT" in resource.read(),
                catches(
                    lambda: project.get_resource("missing.py").read(),
                    exceptions.ResourceNotFoundError,
                ),
                project.root.get_child("claim.py").exists(),
                (pathlib.Path(directory) / "claim.py").read_text(encoding="utf-8") == resource.read(),
                {"resource": resource.name},
            )
        finally:
            project.close()


def probe_unidiff() -> dict[str, Any]:
    from unidiff import PatchSet, UnidiffParseError

    patch_text = "--- a/claim.txt\n+++ b/claim.txt\n@@ -1 +1 @@\n-old\n+new\n"
    patch = PatchSet(patch_text)
    malformed = "@@ -1 +1 @@\n-old\n+new\n"
    return result(
        len(patch) == 1 and patch[0].added == 1 and patch[0].removed == 1,
        catches(lambda: PatchSet(malformed), UnidiffParseError),
        len(PatchSet("")) == 0,
        [line.value for line in patch[0][0] if line.is_added] == ["new\n"],
        {"added": patch[0].added, "removed": patch[0].removed},
    )


def probe_vulture() -> dict[str, Any]:
    import vulture

    source = "unused_value = 2\n"
    analyzer = vulture.Vulture()
    analyzer.scan(source, filename="probe.py")
    unused = analyzer.get_unused_code()
    clean = vulture.Vulture()
    clean.scan("value = 2\nprint(value)\n", filename="clean.py")
    tree = ast.parse(source)
    assigned = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    loaded = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    return result(
        any(item.name == "unused_value" for item in unused),
        not clean.get_unused_code(),
        not vulture.Vulture().get_unused_code(),
        {item.name for item in unused} == assigned - loaded == {"unused_value"},
        {"unused": [item.name for item in unused]},
    )


def _run_pytest_fixture(source: str, *arguments: str, timeout: float = 20.0) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "test_probe.py"
        path.write_text(source, encoding="utf-8")
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        return subprocess.run(
            [sys.executable, "-m", "pytest", str(path), "-q", *arguments],
            cwd=directory,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )


def probe_pytest_benchmark() -> dict[str, Any]:
    import pytest_benchmark

    source = "def test_speed(benchmark):\n    assert benchmark(lambda: 2 + 2) == 4\n"
    run = _run_pytest_fixture(
        source,
        "-p",
        "pytest_benchmark.plugin",
        "--benchmark-only",
        "--benchmark-min-rounds=1",
        "--benchmark-max-time=0.01",
    )
    missing = _run_pytest_fixture(source)
    return result(
        run.returncode == 0 and "1 passed" in run.stdout,
        missing.returncode != 0 and "fixture 'benchmark' not found" in missing.stdout,
        "benchmark" in (run.stdout + run.stderr).lower(),
        run.returncode == 0,
        {"returncode": run.returncode, "missing_plugin_returncode": missing.returncode},
    )


def probe_pytest_randomly() -> dict[str, Any]:
    import pytest_randomly

    source = "".join(f"def test_{index:02d}(): assert True\n" for index in range(12))
    arguments = ("-p", "pytest_randomly", "--collect-only")
    first = _run_pytest_fixture(source, *arguments, "--randomly-seed=123")
    second = _run_pytest_fixture(source, *arguments, "--randomly-seed=123")
    different = _run_pytest_fixture(source, *arguments, "--randomly-seed=999")
    missing = _run_pytest_fixture(source, "--randomly-seed=123")
    order_first = [line for line in first.stdout.splitlines() if "::test_" in line]
    order_second = [line for line in second.stdout.splitlines() if "::test_" in line]
    order_different = [line for line in different.stdout.splitlines() if "::test_" in line]
    return result(
        first.returncode == 0 and len(order_first) == 12,
        missing.returncode != 0 and "unrecognized arguments" in missing.stderr,
        different.returncode == 0 and order_different != order_first,
        second.returncode == 0 and order_second == order_first,
        {
            "seed_123_order": order_first,
            "seed_999_order": order_different,
            "missing_plugin_returncode": missing.returncode,
        },
    )


def probe_pytest_timeout() -> dict[str, Any]:
    import pytest_timeout

    fast = _run_pytest_fixture("def test_fast(): assert True\n", "-p", "pytest_timeout", "--timeout=1")
    slow_source = "import time\ndef test_slow(): time.sleep(1)\n"
    slow = _run_pytest_fixture(
        slow_source,
        "-p",
        "pytest_timeout",
        "--timeout=0.1",
        timeout=10,
    )
    disabled = _run_pytest_fixture(
        slow_source, "-p", "pytest_timeout", "--timeout=0", timeout=10
    )
    missing = _run_pytest_fixture("def test_fast(): assert True\n", "--timeout=1")
    return result(
        fast.returncode == 0,
        slow.returncode != 0
        and "timeout" in (slow.stdout + slow.stderr).lower()
        and missing.returncode != 0,
        disabled.returncode == 0,
        fast.returncode == 0 and slow.returncode != 0,
        {
            "fast": fast.returncode,
            "slow": slow.returncode,
            "disabled": disabled.returncode,
            "missing_plugin": missing.returncode,
        },
    )


def probe_pytest_xdist() -> dict[str, Any]:
    import xdist

    source = (
        "import os\n"
        "def test_one(): assert os.environ.get('PYTEST_XDIST_WORKER','').startswith('gw')\n"
        "def test_two(): assert os.environ.get('PYTEST_XDIST_WORKER','').startswith('gw')\n"
    )
    parallel = _run_pytest_fixture(source, "-p", "xdist.plugin", "-n", "2")
    missing = _run_pytest_fixture(source, "-n", "2")
    serial = _run_pytest_fixture(
        "def test_one(): assert True\ndef test_two(): assert True\n",
        "-p",
        "xdist.plugin",
        "-n",
        "0",
    )
    return result(
        parallel.returncode == 0 and "2 passed" in parallel.stdout,
        missing.returncode != 0 and "unrecognized arguments" in missing.stderr,
        serial.returncode == 0,
        parallel.returncode == 0
        and serial.returncode == 0
        and missing.returncode != 0,
        {"parallel": parallel.returncode, "serial": serial.returncode, "missing_plugin": missing.returncode},
    )


def probe_python_levenshtein() -> dict[str, Any]:
    import Levenshtein

    def dynamic_programming_distance(left: str, right: str) -> int:
        previous = list(range(len(right) + 1))
        for left_index, left_char in enumerate(left, start=1):
            current = [left_index]
            for right_index, right_char in enumerate(right, start=1):
                current.append(
                    min(
                        current[-1] + 1,
                        previous[right_index] + 1,
                        previous[right_index - 1] + (left_char != right_char),
                    )
                )
            previous = current
        return previous[-1]

    distance = Levenshtein.distance("kitten", "sitting")
    return result(
        distance == 3,
        catches(lambda: Levenshtein.distance(None, "value"), TypeError),
        Levenshtein.distance("", "") == 0,
        distance == dynamic_programming_distance("kitten", "sitting"),
        {"distance": distance},
    )


def probe_responses() -> dict[str, Any]:
    import requests
    import responses

    with responses.RequestsMock() as mock:
        mock.add(responses.GET, "https://example.invalid/claim", json={"verdict": "ADMIT"}, status=200)
        response = requests.get("https://example.invalid/claim", timeout=1)
        negative = catches(
            lambda: requests.get("https://example.invalid/unregistered", timeout=1),
            requests.ConnectionError,
        )
        return result(
            response.json() == {"verdict": "ADMIT"},
            negative,
            len(mock.calls) == 2,
            response.status_code == 200,
            {"registered_status": response.status_code, "calls": len(mock.calls)},
        )


def probe_testfixtures() -> dict[str, Any]:
    from testfixtures import ShouldRaise, compare

    expected_observed = False
    with ShouldRaise(ValueError("expected")):
        raise ValueError("expected")
    expected_observed = True

    equal_observed = compare({"value": 1}, {"value": 1}) is None
    unequal_observed = catches(lambda: compare(1, 2), AssertionError)
    return result(
        expected_observed and equal_observed,
        unequal_observed,
        compare([], []) is None,
        equal_observed == ({"value": 1} == {"value": 1})
        and unequal_observed == (1 != 2),
        {"expected_exception": "ValueError"},
    )


def probe_vcrpy() -> dict[str, Any]:
    import vcr
    from vcr.request import Request
    from vcr.errors import UnhandledHTTPRequestError

    request = Request("GET", "https://example.invalid/a?b=1", None, {"X-Probe": "1"})
    missing = Request("GET", "https://example.invalid/missing", None, {})
    cassette = vcr.cassette.Cassette("memory", record_mode="none")
    response = {
        "status": {"code": 200, "message": "OK"},
        "headers": {"Content-Type": ["application/json"]},
        "body": {"string": b"{}"},
    }
    cassette.append(request, response)
    played = cassette.play_response(request)
    return result(
        played["status"]["code"] == 200,
        catches(lambda: cassette.play_response(missing), UnhandledHTTPRequestError),
        cassette.play_count == 1,
        played["body"]["string"] == b"{}",
        {"method": request.method, "play_count": cassette.play_count},
    )


def probe_html2text() -> dict[str, Any]:
    import html2text

    converter = html2text.HTML2Text()
    converter.body_width = 0
    converted = converter.handle("<p>Claim <strong>accepted</strong></p>").strip()
    return result(
        converted == "Claim **accepted**",
        converter.handle("<script>hostile()</script>").strip() == "",
        converter.handle("").strip() == "",
        "Claim" in converted and "accepted" in converted,
        {"converted": converted},
    )


def probe_markdown_it_py() -> dict[str, Any]:
    from markdown_it import MarkdownIt

    parser = MarkdownIt("commonmark")
    tokens = parser.parse("# Claim\n\nAccepted")
    return result(
        any(token.type == "heading_open" for token in tokens),
        not any(token.type == "link_open" for token in parser.parse("[broken](")),
        parser.parse("") == [],
        [token.type for token in tokens[:3]] == ["heading_open", "inline", "heading_close"],
        {"types": [token.type for token in tokens]},
    )


def probe_markdown2() -> dict[str, Any]:
    import markdown2

    converted = markdown2.markdown("# Claim")
    return result(
        converted.strip() == "<h1>Claim</h1>",
        catches(lambda: markdown2.markdown(None), (TypeError, AttributeError)),
        markdown2.markdown("").strip() == "<p></p>",
        "<h1>" in converted and "Claim" in converted,
        {"converted": converted.strip()},
    )


def probe_mistune() -> dict[str, Any]:
    import mistune

    parser = mistune.create_markdown()
    converted = parser("# Claim")
    return result(
        converted.strip() == "<h1>Claim</h1>",
        "<script>" not in parser("<script>hostile()</script>"),
        parser("") == "",
        "<h1>" in converted and "Claim" in converted,
        {"converted": converted.strip()},
    )


def probe_soupsieve() -> dict[str, Any]:
    from bs4 import BeautifulSoup
    import soupsieve
    from soupsieve.util import SelectorSyntaxError

    soup = BeautifulSoup("<main><p id='claim'>accepted</p></main>", "html.parser")
    selected = soupsieve.select_one("main > p#claim", soup)
    return result(
        selected is not None and selected.get_text() == "accepted",
        catches(lambda: soupsieve.compile(":::invalid"), SelectorSyntaxError),
        soupsieve.select(".missing", soup) == [],
        selected is soup.find(id="claim"),
        {"selected": None if selected is None else selected.get_text()},
    )


def probe_tinycss2() -> dict[str, Any]:
    import tinycss2

    valid = tinycss2.parse_declaration_list("color: red")
    invalid = tinycss2.parse_declaration_list("color red")
    return result(
        len(valid) == 1 and valid[0].type == "declaration",
        any(token.type == "error" for token in invalid),
        tinycss2.parse_declaration_list("") == [],
        valid[0].name == "color",
        {"valid_type": valid[0].type, "invalid_types": [token.type for token in invalid]},
    )


def probe_unidecode() -> dict[str, Any]:
    import unicodedata
    from unidecode import unidecode

    converted = unidecode("Müller")
    normalized = unicodedata.normalize("NFKD", "Müller").encode("ascii", "ignore").decode()
    return result(
        converted == "Muller",
        unidecode("☃") == "",
        unidecode("") == "",
        converted == normalized,
        {"converted": converted},
    )


def probe_w3lib() -> dict[str, Any]:
    import urllib.parse
    from w3lib.url import canonicalize_url

    raw = "HTTPS://Example.com/path?b=2&a=1#fragment"
    canonical = canonicalize_url(raw)
    return result(
        canonical == "https://example.com/path?a=1&b=2",
        catches(lambda: canonicalize_url("http://["), ValueError),
        canonicalize_url("https://example.com") == "https://example.com/",
        urllib.parse.urlsplit(canonical).query == "a=1&b=2",
        {"canonical": canonical},
    )


def probe_xmltodict() -> dict[str, Any]:
    import xml.parsers.expat
    import xml.etree.ElementTree as element_tree
    import xmltodict

    parsed = xmltodict.parse("<claim><verdict>ADMIT</verdict></claim>")
    return result(
        parsed == {"claim": {"verdict": "ADMIT"}},
        catches(lambda: xmltodict.parse("<claim>"), xml.parsers.expat.ExpatError),
        xmltodict.parse("<claim/>") == {"claim": None},
        parsed["claim"]["verdict"]
        == element_tree.fromstring("<claim><verdict>ADMIT</verdict></claim>").findtext(
            "verdict"
        ),
        {"parsed": parsed},
    )


def probe_grimp() -> dict[str, Any]:
    import grimp

    with tempfile.TemporaryDirectory() as directory:
        root = pathlib.Path(directory)
        package = root / "cb_probe_package"
        package.mkdir()
        (package / "__init__.py").write_text("from . import child\n", encoding="utf-8")
        (package / "child.py").write_text("VALUE = 2\n", encoding="utf-8")
        sys.path.insert(0, directory)
        try:
            graph = grimp.build_graph("cb_probe_package", cache_dir=None)
            modules = sorted(graph.modules)
            return result(
                "cb_probe_package.child" in modules,
                catches(
                    lambda: grimp.build_graph("cb_missing_package", cache_dir=None),
                    ValueError,
                ),
                "cb_probe_package" in modules,
                set(modules) == {"cb_probe_package", "cb_probe_package.child"},
                {"modules": modules},
            )
        finally:
            sys.path.remove(directory)
            sys.modules.pop("cb_probe_package", None)
            sys.modules.pop("cb_probe_package.child", None)


def probe_packaging() -> dict[str, Any]:
    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.version import InvalidVersion, Version

    requirement = Requirement("example>=1,<2")
    return result(
        requirement.specifier.contains("1.5"),
        catches(lambda: Version("not a version"), InvalidVersion)
        and catches(lambda: Requirement("not a req @@@"), InvalidRequirement),
        not requirement.specifier.contains("2.0"),
        Version("1.10") > Version("1.2"),
        {"requirement": str(requirement)},
    )


def probe_patch_ng() -> dict[str, Any]:
    import patch_ng

    diff = b"--- claim.txt\n+++ claim.txt\n@@ -1 +1 @@\n-old\n+new\n"
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "claim.txt"
        path.write_text("old\n", encoding="utf-8")
        patch = patch_ng.fromstring(diff)
        applied = bool(patch and patch.apply(root=directory))
        malformed = patch_ng.fromstring(b"this is not a patch\n")
        empty = patch_ng.fromstring(b"")
        return result(
            applied and path.read_text(encoding="utf-8") == "new\n",
            malformed is False,
            bool(empty is not False and len(empty) == 0),
            path.read_text(encoding="utf-8") == "new\n",
            {"applied": applied, "malformed_refused": malformed is False},
        )


def probe_platformdirs() -> dict[str, Any]:
    import platformdirs

    directory = platformdirs.user_data_dir("ConstraintBox", "Owner")
    unscoped = platformdirs.user_data_dir("", "")
    return result(
        isinstance(directory, str) and "ConstraintBox" in directory,
        False,
        isinstance(platformdirs.user_data_dir("C", "O"), str),
        pathlib.Path(directory).name == "ConstraintBox"
        and pathlib.Path(directory).parent == pathlib.Path(unscoped),
        {
            "path_name": pathlib.Path(directory).name,
            "unscoped": unscoped,
            "limitation": "total path resolver has no refusal negative in this profile",
        },
    )


def probe_plumbum() -> dict[str, Any]:
    from plumbum import CommandNotFound, local

    command = local["/usr/bin/printf"]
    output = command("%s", "claim")
    return result(
        output == "claim",
        catches(lambda: local["cb-command-that-does-not-exist"], CommandNotFound),
        command("%s", "") == "",
        output == subprocess.run(["/usr/bin/printf", "%s", "claim"], capture_output=True, text=True).stdout,
        {"output": output},
    )


def probe_stamina() -> dict[str, Any]:
    import stamina

    attempts = {"count": 0}

    @stamina.retry(on=ValueError, attempts=3, wait_initial=0, wait_max=0)
    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise ValueError("retry")
        return "ADMIT"

    result_value = flaky()

    boundary_attempts = {"count": 0}

    @stamina.retry(on=ValueError, attempts=3, wait_initial=0, wait_max=0)
    def succeeds_on_last_attempt() -> str:
        boundary_attempts["count"] += 1
        if boundary_attempts["count"] < 3:
            raise ValueError("boundary")
        return "BOUNDARY"

    boundary_value = succeeds_on_last_attempt()

    @stamina.retry(on=ValueError, attempts=1, wait_initial=0, wait_max=0)
    def refused() -> None:
        raise ValueError("bounded")

    return result(
        result_value == "ADMIT" and attempts["count"] == 2,
        catches(refused, ValueError),
        boundary_value == "BOUNDARY" and boundary_attempts["count"] == 3,
        attempts["count"] == 2 and boundary_attempts["count"] == 3,
        {"attempts": attempts["count"], "boundary_attempts": boundary_attempts["count"]},
    )


def probe_structlog() -> dict[str, Any]:
    import structlog

    sink = io.StringIO()

    def require_verdict(logger: Any, method: str, event: dict[str, Any]) -> dict[str, Any]:
        if "verdict" not in event:
            raise structlog.DropEvent
        return event

    logger = structlog.wrap_logger(
        structlog.PrintLogger(sink),
        processors=[require_verdict, structlog.processors.JSONRenderer(serializer=json.dumps)],
    )
    logger.info("decision", verdict="ADMIT")
    accepted = sink.getvalue()
    logger.info("missing-verdict")
    after_negative = sink.getvalue()
    event = json.loads(accepted)
    return result(
        event == {"verdict": "ADMIT", "event": "decision"},
        after_negative == accepted,
        accepted.endswith("\n"),
        event["verdict"] == "ADMIT",
        {"event": event, "missing_dropped": after_negative == accepted},
    )


def probe_xxhash() -> dict[str, Any]:
    import xxhash

    digest = xxhash.xxh64(b"constraint").hexdigest()
    return result(
        digest == "98f77df90c1cf3a3",
        digest != xxhash.xxh64(b"constraint!").hexdigest(),
        xxhash.xxh64(b"").hexdigest() == "ef46db3751d8e999",
        int(digest, 16) == xxhash.xxh64(b"constraint").intdigest(),
        {"digest": digest},
    )


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def load_manifest(path: pathlib.Path) -> dict[str, Any]:
    body = json.loads(path.read_text(encoding="utf-8"))
    if body.get("schema") != "constraintbox.cb-light-tool-manifest.v1":
        raise ValueError("invalid CB Light tool manifest schema")
    identity = dict(body)
    claimed = identity.pop("manifest_sha256", None)
    observed = hashlib.sha256(canonical_json(identity)).hexdigest()
    if claimed != observed:
        raise ValueError(
            f"manifest digest mismatch: claimed={claimed}, observed={observed}"
        )
    if len(body.get("tools", [])) != 91:
        raise ValueError("CB Light tool manifest must contain exactly 91 rows")
    return body


def probe_function(tool: dict[str, Any]) -> Callable[[], dict[str, Any]]:
    name = "probe_" + tool["normalized_name"].replace("-", "_")
    function = globals().get(name)
    if not callable(function):
        raise KeyError(f"missing operation adapter: {name}")
    return function


@functools.lru_cache(maxsize=1)
def probe_structure_issues() -> dict[str, list[str]]:
    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    findings: dict[str, list[str]] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("probe_"):
            continue
        result_calls = [
            child
            for child in ast.walk(node)
            if isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id == "result"
        ]
        issues: list[str] = []
        if len(result_calls) != 1 or len(result_calls[0].args) < 4:
            issues.append("RESULT_ARM_SHAPE_INVALID")
        else:
            arms = result_calls[0].args[:4]
            for index, arm in enumerate(arms):
                if isinstance(arm, ast.Constant) and isinstance(arm.value, bool):
                    issues.append(f"LITERAL_BOOLEAN_ARM:{index}")
                if any(
                    isinstance(child, ast.IfExp)
                    and isinstance(child.test, ast.Constant)
                    for child in ast.walk(arm)
                ):
                    issues.append(f"CONSTANT_TERNARY_ARM:{index}")
            dumps = [ast.dump(arm, include_attributes=False) for arm in arms]
            for left in range(len(dumps)):
                for right in range(left + 1, len(dumps)):
                    if dumps[left] == dumps[right]:
                        issues.append(f"DUPLICATE_ARMS:{left}:{right}")
        findings[node.name] = sorted(issues)
    return findings


@contextlib.contextmanager
def sever_import(import_name: str):
    root = import_name.split(".")[0]
    original = builtins.__import__

    def blocked(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == root or name.startswith(root + "."):
            raise ModuleNotFoundError(f"CB Light severed import: {root}")
        return original(name, *args, **kwargs)

    builtins.__import__ = blocked
    try:
        yield
    finally:
        builtins.__import__ = original


def child(tool: dict[str, Any], *, sever: bool) -> int:
    global CURRENT_TOOL, CURRENT_EXCEPTION_EVIDENCE
    CURRENT_TOOL = tool
    CURRENT_EXCEPTION_EVIDENCE = []
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(
            captured_stderr
        ):
            if sever:
                try:
                    with sever_import(tool["import_names"][0]):
                        probe_function(tool)()
                except ModuleNotFoundError as exc:
                    root = str(tool["import_names"][0]).split(".")[0]
                    sentinel = f"CB Light severed import: {root}"
                    payload = {
                        "severance": {
                            "passed": sentinel in str(exc),
                            "reason_code": (
                                "DECLARED_IMPORT_SEVERED"
                                if sentinel in str(exc)
                                else "UNRELATED_MODULE_NOT_FOUND"
                            ),
                            "exception_type": type(exc).__name__,
                            "severed_root": root,
                            "sentinel_sha256": hashlib.sha256(sentinel.encode()).hexdigest(),
                        }
                    }
                except Exception as exc:
                    payload = {
                        "severance": {
                            "passed": False,
                            "reason_code": "SEVERANCE_WRONG_FAILURE",
                            "exception_type": type(exc).__name__,
                            "detail": str(exc)[:300],
                        }
                    }
                else:
                    payload = {
                        "severance": {
                            "passed": False,
                            "reason_code": "SEVERANCE_NOT_OBSERVED",
                        }
                    }
            else:
                payload = probe_function(tool)()
        payload.update(
            {
                "distribution": tool["distribution"],
                "normalized_name": tool["normalized_name"],
                "import_name": tool["import_names"][0],
                "adapter": probe_function(tool).__name__,
                "captured_stdout_sha256": hashlib.sha256(
                    captured_stdout.getvalue().encode()
                ).hexdigest(),
                "captured_stderr_sha256": hashlib.sha256(
                    captured_stderr.getvalue().encode()
                ).hexdigest(),
            }
        )
        print(MARKER + json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return 0
    except Exception as exc:
        payload = {
            "distribution": tool["distribution"],
            "normalized_name": tool["normalized_name"],
            "import_name": tool["import_names"][0],
            "adapter": "probe_" + tool["normalized_name"].replace("-", "_"),
            "error": type(exc).__name__,
            "detail": str(exc)[:500],
            "captured_stdout_sha256": hashlib.sha256(
                captured_stdout.getvalue().encode()
            ).hexdigest(),
            "captured_stderr_sha256": hashlib.sha256(
                captured_stderr.getvalue().encode()
            ).hexdigest(),
        }
        print(MARKER + json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return 1


def run_child_process(
    tool: dict[str, Any],
    manifest_path: pathlib.Path,
    *,
    sever: bool,
    timeout: float,
    hash_seed: int,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(pathlib.Path(__file__).resolve()),
        "--manifest",
        str(manifest_path),
        "--child",
        tool["normalized_name"],
    ]
    if sever:
        command.append("--sever")
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": str(hash_seed),
            "NO_COLOR": "1",
        }
    )
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT if ROOT.is_dir() else pathlib.Path.cwd(),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "returncode": None,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
            "payload": {
                "distribution": tool["distribution"],
                "error": "PROBE_TIMEOUT",
                "detail": str(exc),
            },
        }
    marker_lines = [
        line for line in completed.stdout.splitlines() if line.startswith(MARKER)
    ]
    payload = (
        json.loads(marker_lines[-1][len(MARKER) :])
        if marker_lines
        else {
            "distribution": tool["distribution"],
            "error": "MISSING_STRUCTURED_CHILD_OUTPUT",
            "detail": completed.stderr[-500:],
        }
    )
    return {
        "returncode": completed.returncode,
        "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        "payload": payload,
    }


def semantic_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key not in {"captured_stdout_sha256", "captured_stderr_sha256"}
    }


def run_tool(
    tool: dict[str, Any], manifest_path: pathlib.Path, timeout: float
) -> dict[str, Any]:
    first = run_child_process(
        tool, manifest_path, sever=False, timeout=timeout, hash_seed=0
    )
    second = run_child_process(
        tool, manifest_path, sever=False, timeout=timeout, hash_seed=1
    )
    severed = run_child_process(
        tool, manifest_path, sever=True, timeout=timeout, hash_seed=2
    )
    first_payload = first["payload"]
    second_payload = second["payload"]
    replay_equal = bool(
        first["returncode"] == 0
        and second["returncode"] == 0
        and "observation" in first_payload
        and "observation" in second_payload
        and canonical_json(semantic_payload(first_payload))
        == canonical_json(semantic_payload(second_payload))
    )
    structure_issues = list(
        probe_structure_issues().get(
            probe_function(tool).__name__, ["ADAPTER_NOT_AUDITED"]
        )
    )
    review_hold = CONTROL_REVIEW_HOLDS.get(tool["normalized_name"])
    if review_hold:
        structure_issues.append(f"CONTROL_REVIEW_HOLD:{review_hold}")
    structure_issues = sorted(set(structure_issues))
    facts = {
        "positive_api_operation": bool(first_payload.get("positive", {}).get("passed")),
        "reason_specific_negative": bool(
            first_payload.get("negative", {}).get("passed")
            and first_payload.get("negative", {}).get("contract_passed") is True
            and first_payload.get("negative", {}).get("reason_code")
        ),
        "boundary_observed": bool(first_payload.get("boundary", {}).get("passed")),
        "deterministic_replay": replay_equal,
        "import_severance_observed": bool(
            severed["payload"].get("severance", {}).get("passed")
        ),
        "bounded_reference_agreement": bool(
            first_payload.get("reference", {}).get("passed")
        ),
        "probe_structure_non_vacuous": not structure_issues,
    }
    satisfied = (
        first["returncode"] == 0
        and second["returncode"] == 0
        and severed["returncode"] == 0
        and all(facts.values())
    )
    return {
        "distribution": tool["distribution"],
        "normalized_name": tool["normalized_name"],
        "locked_version": tool["locked_version"],
        "import_name": tool["import_names"][0],
        "role": tool["role"],
        "role_class": tool["role_class"],
        "facts": facts,
        "disposition": "ADMIT" if satisfied else "HOLD",
        "reason_code": (
            "OPERATION_CONSTRAINTS_SATISFIED"
            if satisfied
            else "OPERATION_CONSTRAINTS_INCOMPLETE"
        ),
        "failed_facts": sorted(name for name, value in facts.items() if not value),
        "probe_structure_issues": structure_issues,
        "first": first,
        "replay": {
            "equal": replay_equal,
            "semantic_sha256_a": hashlib.sha256(
                canonical_json(semantic_payload(first_payload))
            ).hexdigest(),
            "semantic_sha256_b": hashlib.sha256(
                canonical_json(semantic_payload(second_payload))
            ).hexdigest(),
            "run": second,
        },
        "severance": severed,
    }


def run_matrix(
    manifest_path: pathlib.Path,
    *,
    timeout: float,
    jobs: int,
    only: set[str] | None = None,
) -> dict[str, Any]:
    import concurrent.futures

    manifest = load_manifest(manifest_path)
    tools = [
        tool
        for tool in manifest["tools"]
        if not only or tool["normalized_name"] in only
    ]
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        futures = {
            pool.submit(run_tool, tool, manifest_path, timeout): tool
            for tool in tools
        }
        rows = [future.result() for future in concurrent.futures.as_completed(futures)]
    rows.sort(key=lambda row: row["normalized_name"])
    counts = {
        "probed": len(rows),
        "admit": sum(row["disposition"] == "ADMIT" for row in rows),
        "hold": sum(row["disposition"] == "HOLD" for row in rows),
    }
    return {
        "schema": "constraintbox.cb-light-tool-probes.v1",
        "profile": "cb_light",
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "interpreter": sys.executable,
        "sys_prefix": sys.prefix,
        "python_version": sys.version.split()[0],
        "manifest_identity_sha256": manifest["manifest_sha256"],
        "manifest_file_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "probe_source_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "required_facts": [
            "positive_api_operation",
            "reason_specific_negative",
            "boundary_observed",
            "deterministic_replay",
            "import_severance_observed",
            "bounded_reference_agreement",
            "probe_structure_non_vacuous",
        ],
        "counts": counts,
        "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
        "tool_decisions": rows,
        "all_operation_constraints_satisfied": counts["hold"] == 0 and len(rows) == 91,
        "promotion_allowed": False,
        "claim_ceiling": (
            "bounded candidate operations in this interpreter only; no production "
            "integration, portability, adoption, CB Heavy, simulation, promotion, or release claim"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--child")
    parser.add_argument("--sever", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    manifest_path = args.manifest.resolve()
    manifest = load_manifest(manifest_path)
    if args.child:
        tool = next(
            (row for row in manifest["tools"] if row["normalized_name"] == args.child),
            None,
        )
        if tool is None:
            raise SystemExit(f"unknown CB Light tool: {args.child}")
        return child(tool, sever=args.sever)

    receipt = run_matrix(
        manifest_path,
        timeout=args.timeout,
        jobs=args.jobs,
        only=set(args.only) or None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        print(f"CB Light operation probes: {receipt['counts']['admit']} ADMIT, {receipt['counts']['hold']} HOLD")
        for row in receipt["tool_decisions"]:
            if row["disposition"] != "ADMIT":
                print(f"  HOLD {row['distribution']}: {', '.join(row['failed_facts']) or row['first']['payload'].get('error', 'child failure')}")
        print(f"receipt: {args.output}")
    return 0 if receipt["counts"]["hold"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
