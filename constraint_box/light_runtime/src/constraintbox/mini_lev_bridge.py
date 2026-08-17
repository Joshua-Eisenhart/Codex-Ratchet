"""One contained, finite CB Light Mini-Lev operation.

This module is intentionally narrow.  It consumes a recorded local
candidate-evaluation row, requires an operation-specific open-basin cohort,
and then runs a typed/schema boundary, a fixed graph topology, an exact SymPy
witness, an independent CVC5 cross-check, and a bounded Z3 gate.  It does not import legacy Mini-Lev code,
providers, simulations, or CB Heavy.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from hookkernel.cb_light_domain import canonical_json, sha256_bytes
from hookkernel.cb_light_minilev_state import SUCCESS, record_attempt
from hookkernel.cb_light_state import StateError, connect


REQUEST_SCHEMA = "constraintbox.mini-lev-polynomial-request.v1"
RESULT_SCHEMA = "constraintbox.mini-lev-polynomial-result.v1"
TASK = "mini_lev.symbolic_polynomial_qq.v1"
PARENT_CANDIDATE_ID = "pydantic"
PARENT_OPERATION_CONTRACT = {
    "candidate_id": PARENT_CANDIDATE_ID,
    "registry_tool_id": "python.pydantic",
    "required_roles": (
        "strict_typed_hostile_input_boundary",
        "bounded_request_normalization",
    ),
    # This is intentionally not a generic-corpus admission.  The parent is
    # authorized by the separately typed control-plane operation; the actual
    # Mini-Lev tool cohort below must still be OPEN_BASIN in its own selection.
    "generic_corpus_selection_required": False,
}
REQUIRED_OPEN_BASIN_TOOLS = (
    "pypi:cvc5",
    "pypi:jsonschema",
    "pypi:rustworkx",
    "pypi:sympy",
    "pypi:z3-solver",
)
CLAIM_CEILING = (
    "Contained CB Light Mini-Lev local operation only; no membership, adoption, "
    "portability, provider, CB Heavy, release, or semantic replay claim."
)

_REQUEST_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://constraintbox.local/schema/mini-lev-polynomial-request-v1",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema",
        "bridge_request_id",
        "candidate_operation_id",
        "task",
        "payload",
    ],
    "properties": {
        "schema": {"const": REQUEST_SCHEMA},
        "bridge_request_id": {
            "type": "string",
            "minLength": 1,
            "maxLength": 128,
            "pattern": "^[A-Za-z0-9._:-]+$",
        },
        "candidate_operation_id": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "task": {"const": TASK},
        "payload": {
            "type": "object",
            "additionalProperties": False,
            "required": ["terms", "claimed_degree"],
            "properties": {
                "terms": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 8,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["coefficient", "exponent"],
                        "properties": {
                            "coefficient": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["numerator", "denominator"],
                                "properties": {
                                    "numerator": {
                                        "type": "integer",
                                        "not": {"const": 0},
                                    },
                                    "denominator": {"type": "integer", "minimum": 1},
                                },
                            },
                            "exponent": {"type": "integer", "minimum": 0, "maximum": 16},
                        },
                    },
                },
                "claimed_degree": {"type": "integer", "minimum": 0, "maximum": 16},
            },
        },
    },
}


class _Coefficient(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    numerator: int
    denominator: int = Field(gt=0)

    @field_validator("numerator")
    @classmethod
    def _nonzero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("numerator must be nonzero")
        return value


class _Term(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    coefficient: _Coefficient
    exponent: int = Field(ge=0, le=16)


class _PolynomialPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    terms: list[_Term] = Field(min_length=1, max_length=8)
    claimed_degree: int = Field(ge=0, le=16)

    @model_validator(mode="after")
    def _distinct_exponents(self) -> "_PolynomialPayload":
        exponents = [term.exponent for term in self.terms]
        if len(exponents) != len(set(exponents)):
            raise ValueError("terms must have distinct exponents")
        return self


class _MiniLevRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, strict=True, populate_by_name=True
    )

    schema_name: Literal[REQUEST_SCHEMA] = Field(alias="schema")
    bridge_request_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    candidate_operation_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    task: Literal[TASK]
    payload: _PolynomialPayload


class MiniLevBridgeError(RuntimeError):
    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail


def _result(disposition: str, reason_code: str, *, detail: str) -> dict[str, Any]:
    return {
        "schema": RESULT_SCHEMA,
        "disposition": disposition,
        "reason_code": reason_code,
        "detail": detail,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def _validate_request(raw: Mapping[str, Any]) -> _MiniLevRequest:
    value = dict(raw)
    try:
        Draft202012Validator(_REQUEST_JSON_SCHEMA).validate(value)
    except JsonSchemaValidationError as exc:
        raise MiniLevBridgeError(
            "REFUSE_MINILEV_JSON_SCHEMA_INVALID",
            f"Independent JSON Schema boundary refused request: {exc.message}",
        ) from exc
    try:
        return _MiniLevRequest.model_validate(value, strict=True)
    except ValidationError as exc:
        raise MiniLevBridgeError(
            "REFUSE_MINILEV_TYPED_BOUNDARY_INVALID",
            f"Pydantic typed boundary refused request: {exc}",
        ) from exc


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_sha256() -> str:
    from hookkernel import cb_light_minilev_state

    return sha256_bytes(
        canonical_json(
            {
                "mini_lev_bridge.py": _sha256_file(Path(__file__)),
                "core_tool_registry_v9.json": _sha256_file(
                    Path(__file__).with_name("core_tool_registry_v9.json")
                ),
                "cb_light_minilev_state.py": _sha256_file(
                    Path(cb_light_minilev_state.__file__ or "")
                ),
            }
        )
    )


def _parent_operation_contract() -> dict[str, Any]:
    """Bind the parent exception to a declared typed-boundary role contract."""

    from .core_tools import load_registry

    registry = load_registry()
    tool = next(
        (
            row
            for row in registry["tools"]
            if row.get("id") == PARENT_OPERATION_CONTRACT["registry_tool_id"]
        ),
        None,
    )
    if not isinstance(tool, dict):
        raise MiniLevBridgeError(
            "HOLD_MINILEV_PARENT_ROLE_CONTRACT_DRIFT",
            "The declared Pydantic typed-boundary role is absent from the packaged registry.",
        )
    required_roles = set(PARENT_OPERATION_CONTRACT["required_roles"])
    observed_roles = tool.get("cb_roles")
    if (
        tool.get("distribution") != PARENT_CANDIDATE_ID
        or not isinstance(observed_roles, list)
        or not required_roles.issubset(set(observed_roles))
    ):
        raise MiniLevBridgeError(
            "HOLD_MINILEV_PARENT_ROLE_CONTRACT_DRIFT",
            "The packaged Pydantic registry no longer declares the required typed-boundary roles.",
        )
    return {
        "candidate_id": PARENT_OPERATION_CONTRACT["candidate_id"],
        "registry_tool_id": PARENT_OPERATION_CONTRACT["registry_tool_id"],
        "required_roles": sorted(required_roles),
        "generic_corpus_selection_required": False,
    }


def _load_parent_and_cohort(
    connection: Any, request: _MiniLevRequest
) -> tuple[str, dict[str, str], dict[str, Any]]:
    parent_contract = _parent_operation_contract()
    parent = connection.execute(
        """
        SELECT operation_id, candidate_id, disposition, selection_id
        FROM candidate_evaluation
        WHERE operation_id = ?
        """,
        (request.candidate_operation_id,),
    ).fetchone()
    if parent is None:
        raise MiniLevBridgeError(
            "REFUSE_MINILEV_PARENT_OPERATION_UNKNOWN",
            "The supplied candidate operation does not exist in this CB Light SQLite state.",
        )
    if parent["disposition"] != "CANDIDATE_EVALUATED_LOCAL":
        raise MiniLevBridgeError(
            "REFUSE_MINILEV_PARENT_DISPOSITION",
            "The parent operation is not a local candidate evaluation.",
        )
    if parent["candidate_id"] != PARENT_CANDIDATE_ID:
        raise MiniLevBridgeError(
            "REFUSE_MINILEV_PARENT_CANDIDATE",
            "The first contained Mini-Lev operation requires the typed pydantic parent.",
        )

    selection_id = str(parent["selection_id"])
    placeholders = ", ".join("?" for _ in REQUIRED_OPEN_BASIN_TOOLS)
    rows = connection.execute(
        f"""
        SELECT candidate_id, disposition, reason_code
        FROM selection_decision
        WHERE selection_id = ? AND candidate_id IN ({placeholders})
        """,
        (selection_id, *REQUIRED_OPEN_BASIN_TOOLS),
    ).fetchall()
    observed = {
        str(row["candidate_id"]): f"{row['disposition']}:{row['reason_code']}"
        for row in rows
    }
    missing_or_closed = [
        tool_id
        for tool_id in REQUIRED_OPEN_BASIN_TOOLS
        if observed.get(tool_id) != "OPEN_BASIN:ADMISSIBLE_COMPLETION_EXISTS"
    ]
    if missing_or_closed:
        raise MiniLevBridgeError(
            "HOLD_MINILEV_REQUIRED_TOOL_COHORT_NOT_OPEN",
            "The contained Mini-Lev operation requires an open-basin cohort: "
            + ", ".join(missing_or_closed),
        )
    return selection_id, observed, parent_contract


def _topology() -> tuple[dict[str, Any], str]:
    import rustworkx

    labels = (
        "typed-envelope",
        "symbolic-witness",
        "cvc5-degree-crosscheck",
        "z3-degree-gate",
    )
    graph = rustworkx.PyDiGraph()
    nodes = graph.add_nodes_from(labels)
    graph.add_edges_from_no_data(
        ((nodes[0], nodes[1]), (nodes[1], nodes[2]), (nodes[2], nodes[3]))
    )
    order = [graph[index] for index in rustworkx.topological_sort(graph)]
    topology = {
        "schema": "constraintbox.mini-lev-topology.v1",
        "nodes": list(labels),
        "edges": [
            [labels[0], labels[1]],
            [labels[1], labels[2]],
            [labels[2], labels[3]],
        ],
        "topological_order": order,
        "edge_count": graph.num_edges(),
    }
    if order != list(labels) or graph.num_edges() != 3:
        raise MiniLevBridgeError(
            "REFUSE_MINILEV_TOPOLOGY_INVALID",
            "The fixed contained Mini-Lev topology did not remain an ordered three-edge DAG.",
        )
    return topology, sha256_bytes(canonical_json(topology))


def _symbolic_and_smt(request: _MiniLevRequest) -> dict[str, Any]:
    try:
        import cvc5
        from cvc5 import Kind
    except ModuleNotFoundError as exc:
        raise MiniLevBridgeError(
            "HOLD_MINILEV_CVC5_RUNTIME_UNAVAILABLE",
            "The declared CVC5 operation gate is unavailable in this runtime.",
        ) from exc
    import sympy
    import z3

    x = sympy.Symbol("x")
    expression = sum(
        sympy.Rational(term.coefficient.numerator, term.coefficient.denominator)
        * x**term.exponent
        for term in request.payload.terms
    )
    polynomial = sympy.Poly(expression, x, domain=sympy.QQ)
    computed_degree = int(polynomial.degree())

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    cvc5_solver.setOption("produce-models", "true")
    integers = cvc5_solver.getIntegerSort()
    cvc5_degree = cvc5_solver.mkConst(integers, "cvc5_degree")
    cvc5_solver.assertFormula(
        cvc5_solver.mkTerm(Kind.GEQ, cvc5_degree, cvc5_solver.mkInteger(0))
    )
    cvc5_solver.assertFormula(
        cvc5_solver.mkTerm(Kind.LEQ, cvc5_degree, cvc5_solver.mkInteger(16))
    )
    cvc5_solver.assertFormula(
        cvc5_solver.mkTerm(
            Kind.EQUAL,
            cvc5_degree,
            cvc5_solver.mkInteger(request.payload.claimed_degree),
        )
    )
    terminal_degree_terms = []
    for term in request.payload.terms:
        exponent = cvc5_solver.mkInteger(term.exponent)
        cvc5_solver.assertFormula(
            cvc5_solver.mkTerm(Kind.LEQ, exponent, cvc5_degree)
        )
        terminal_degree_terms.append(
            cvc5_solver.mkTerm(Kind.EQUAL, cvc5_degree, exponent)
        )
    cvc5_solver.assertFormula(
        terminal_degree_terms[0]
        if len(terminal_degree_terms) == 1
        else cvc5_solver.mkTerm(Kind.OR, *terminal_degree_terms)
    )
    cvc5_result = cvc5_solver.checkSat()
    cvc5_status = str(cvc5_result)
    if not cvc5_result.isSat():
        if cvc5_result.isUnsat():
            raise MiniLevBridgeError(
                "REFUSE_MINILEV_CVC5_DEGREE_CROSSCHECK_UNSAT",
                "The CVC5 degree witness inferred from input exponents disagrees with the claim.",
            )
        raise MiniLevBridgeError(
            "HOLD_MINILEV_CVC5_DEGREE_CROSSCHECK_INDETERMINATE",
            "CVC5 could not determine the bounded polynomial-degree cross-check.",
        )
    cvc5_degree_witness = cvc5_solver.getValue(cvc5_degree).getIntegerValue()

    degree = z3.Int("degree")
    solver = z3.Solver()
    solver.add(degree >= 0, degree <= 16)
    solver.add(degree == computed_degree)
    solver.add(degree == request.payload.claimed_degree)
    solver.add(z3.Or([degree == term.exponent for term in request.payload.terms]))
    status = str(solver.check())
    if status != "sat":
        raise MiniLevBridgeError(
            "REFUSE_MINILEV_Z3_DEGREE_CROSSCHECK_UNSAT",
            "The exact SymPy polynomial degree and bounded Z3 degree constraints disagree.",
        )
    return {
        "symbol": "x",
        "domain": "QQ",
        "expression": str(polynomial.as_expr()),
        "computed_degree": computed_degree,
        "claimed_degree": request.payload.claimed_degree,
        "cvc5": {
            "backend": "cvc5",
            "version": str(cvc5.__version__),
            "logic": "QF_LIA",
            "input_exponents": [term.exponent for term in request.payload.terms],
            "status": cvc5_status,
            "degree_witness": cvc5_degree_witness,
        },
        "cvc5_status": cvc5_status,
        "cvc5_degree_witness": cvc5_degree_witness,
        "smt_status": status,
        "z3_status": status,
    }


def run_mini_lev_bridge(
    raw: Mapping[str, Any], *, db_path: Path
) -> dict[str, Any]:
    """Run and persist the one bounded contained-Light Mini-Lev operation."""

    if not isinstance(raw, Mapping):
        return _result(
            "REFUSE",
            "REFUSE_MINILEV_REQUEST_MAPPING_REQUIRED",
            detail="The Mini-Lev request must be a JSON object.",
        )
    try:
        request = _validate_request(raw)
    except MiniLevBridgeError as exc:
        return _result("REFUSE", exc.reason_code, detail=exc.detail)

    from hookkernel.cb_light_basin_view import hold_result_if_incomplete

    held = hold_result_if_incomplete()
    if held is not None:
        return {
            **_result("HOLD", held["reason_code"], detail=held["detail"]),
            "basin_view": held["basin_view"],
        }

    request_sha256 = sha256_bytes(
        canonical_json(request.model_dump(mode="json", by_alias=True))
    )
    schema_sha256 = sha256_bytes(canonical_json(_REQUEST_JSON_SCHEMA))
    try:
        connection = connect(db_path)
    except (OSError, sqlite3.Error) as exc:
        return _result(
            "HOLD",
            "HOLD_MINILEV_STATE_UNAVAILABLE",
            detail=f"CB Light SQLite state cannot be opened: {exc}",
        )
    try:
        selection_id, cohort, parent_contract = _load_parent_and_cohort(connection, request)
        topology, topology_sha256 = _topology()
        symbolic = _symbolic_and_smt(request)
        cohort_sha256 = sha256_bytes(canonical_json(cohort))
        result_material = {
            "schema": RESULT_SCHEMA,
            "task": TASK,
            "bridge_request_id": request.bridge_request_id,
            "candidate_operation_id": request.candidate_operation_id,
            "selection_id": selection_id,
            "parent_contract": parent_contract,
            "cohort": cohort,
            "topology": topology,
            "symbolic": symbolic,
            "disposition": SUCCESS,
            "reason_code": "MINILEV_TYPED_SYMBOLIC_CVC5_Z3_BOUND",
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        source_sha256 = _source_sha256()
        persisted = record_attempt(
            connection,
            bridge_request_id=request.bridge_request_id,
            candidate_operation_id=request.candidate_operation_id,
            request_sha256=request_sha256,
            schema_sha256=schema_sha256,
            source_sha256=source_sha256,
            selection_id=selection_id,
            topology_sha256=topology_sha256,
            cohort_sha256=cohort_sha256,
            result=result_material,
            claim_ceiling=CLAIM_CEILING,
        )
        return {
            **result_material,
            **persisted,
            "request_sha256": request_sha256,
            "schema_sha256": schema_sha256,
            "source_sha256": source_sha256,
            "topology_sha256": topology_sha256,
            "cohort_sha256": cohort_sha256,
        }
    except MiniLevBridgeError as exc:
        return _result(
            "HOLD" if exc.reason_code.startswith("HOLD_") else "REFUSE",
            exc.reason_code,
            detail=exc.detail,
        )
    except StateError as exc:
        return _result(
            "REFUSE",
            "REFUSE_MINILEV_ATTEMPT_IDENTITY_CONFLICT",
            detail=str(exc),
        )
    finally:
        connection.close()


def run_mini_lev_bridge_file(request_path: Path, *, db_path: Path) -> dict[str, Any]:
    """Read one JSON request for the public contained-Light CLI."""

    try:
        raw = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _result(
            "REFUSE",
            "REFUSE_MINILEV_REQUEST_INVALID_JSON",
            detail=f"Cannot read Mini-Lev JSON request: {exc}",
        )
    return run_mini_lev_bridge(raw, db_path=db_path)
