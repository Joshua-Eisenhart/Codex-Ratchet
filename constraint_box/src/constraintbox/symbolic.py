from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import math
import platform
import re
import sys
import types
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from .contracts import Disposition, ProfileOutcome
from .intake import IntakeError, canonical_json, parse_json_object
from .runtime_profiles import RuntimeProfileError, load_runtime_profile_registry


_EXACT_OPERATION = "poly_qq_as_dict"
_EXACT_API = "sympy.Poly(..., domain=sympy.QQ).as_dict()"
_TERM_KEYS = {"degree", "numerator", "denominator"}
_SYMPY_API_BINDINGS = (
    ("Symbol", "sympy.core.symbol"),
    ("Add", "sympy.core.add"),
    ("Rational", "sympy.core.numbers"),
    ("Poly", "sympy.polys.polytools"),
    ("QQ", "sympy.polys.domains.rationalfield"),
)


class _SymbolicContractError(ValueError):
    pass


@dataclass(frozen=True)
class _SympyOperationBindings:
    Symbol: object
    Add: object
    Rational: object
    Poly: object
    QQ: object
    Symbol_new: object
    Add_new: object
    Rational_new: object
    Poly_new: object
    Poly_as_dict: object


def _is_plain_int(value: object) -> bool:
    return type(value) is int


def _fraction_json(degree: int, value: Fraction) -> dict[str, int]:
    return {
        "degree": degree,
        "numerator": value.numerator,
        "denominator": value.denominator,
    }


def _qualified_type_name(value: object) -> str:
    """Return a stable, data-only type label for a controller receipt."""

    value_type = type(value)
    return f"{value_type.__module__}.{value_type.__qualname__}"


class _SympyRuntimeError(RuntimeError):
    """A required portable SymPy compatibility condition was not met."""


@dataclass(frozen=True)
class _SympyCompatibilityPolicy:
    profile_id: str
    registry_sha256: str
    minimum_version: str
    maximum_exclusive_version: str
    required_attributes: tuple[str, ...]


_SEMANTIC_WITNESS_CASES = (
    (
        "constant-and-square",
        ((0, 1, 2), (2, 3, 4)),
    ),
    (
        "mixed-sign-sparse",
        ((0, -5, 6), (1, 7, 3), (4, -9, 10)),
    ),
)


def _active_sympy_policy() -> _SympyCompatibilityPolicy:
    """Resolve SymPy's version/API policy from the active core registry."""

    try:
        registry = load_runtime_profile_registry()
    except RuntimeProfileError as exc:
        raise _SympyRuntimeError(
            f"ConstraintBox runtime-profile registry unavailable: {exc}"
        ) from exc
    candidates = [
        profile
        for profile in registry.profiles
        if profile.implementation == platform.python_implementation()
        and profile.python_minor == tuple(sys.version_info[:2])
    ]
    if len(candidates) != 1:
        raise _SympyRuntimeError(
            "no unique active ConstraintBox runtime profile for SymPy"
        )
    requirements = [
        requirement
        for requirement in candidates[0].libraries
        if requirement.distribution == "sympy"
    ]
    if len(requirements) != 1:
        raise _SympyRuntimeError(
            "active ConstraintBox runtime profile lacks one SymPy requirement"
        )
    requirement = requirements[0]
    required_api = {"Symbol", "Add", "Rational", "Poly", "QQ"}
    if not required_api.issubset(requirement.required_attributes):
        raise _SympyRuntimeError(
            "active ConstraintBox runtime profile lacks the bounded SymPy API"
        )
    return _SympyCompatibilityPolicy(
        profile_id=candidates[0].profile_id,
        registry_sha256=registry.registry_sha256,
        minimum_version=requirement.minimum_version,
        maximum_exclusive_version=requirement.maximum_exclusive_version,
        required_attributes=requirement.required_attributes,
    )


def _default_sympy_minimum_version() -> str:
    return _active_sympy_policy().minimum_version


def _default_sympy_maximum_exclusive_version() -> str:
    return _active_sympy_policy().maximum_exclusive_version


def _version_tuple(value: object, *, label: str) -> tuple[int, ...]:
    if not isinstance(value, str) or not value:
        raise _SympyRuntimeError(f"SymPy {label} must be a numeric version")
    parts = value.split(".")
    if any(not part.isascii() or not part.isdigit() for part in parts):
        raise _SympyRuntimeError(f"SymPy {label} must be a numeric version")
    return tuple(int(part) for part in parts)


def _version_in_policy(value: object, policy: _SympyCompatibilityPolicy) -> bool:
    observed = _version_tuple(value, label="observed version")
    minimum = _version_tuple(policy.minimum_version, label="minimum version")
    maximum = _version_tuple(
        policy.maximum_exclusive_version,
        label="maximum exclusive version",
    )
    return minimum <= observed < maximum


def _sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _sympy_distribution_paths() -> tuple[object, set[Path]]:
    try:
        distribution = importlib.metadata.distribution("sympy")
        files = distribution.files
    except importlib.metadata.PackageNotFoundError as exc:
        raise _SympyRuntimeError("SymPy distribution metadata is unavailable") from exc
    except Exception as exc:
        raise _SympyRuntimeError(
            f"SymPy distribution metadata inspection failed: {exc}"
        ) from exc
    if files is None:
        raise _SympyRuntimeError("SymPy distribution file inventory is unavailable")
    try:
        paths = {
            Path(distribution.locate_file(item)).resolve()
            for item in files
        }
    except (OSError, TypeError, ValueError) as exc:
        raise _SympyRuntimeError(
            "SymPy distribution file inventory is unusable"
        ) from exc
    if not paths:
        raise _SympyRuntimeError("SymPy distribution file inventory is empty")
    return distribution, paths


def _module_observation(
    module: object,
    *,
    label: str,
    distribution_paths: set[Path],
) -> dict[str, str | None]:
    try:
        module_path = Path(getattr(module, "__file__")).resolve()
        spec = getattr(module, "__spec__")
        spec_path = Path(getattr(spec, "origin")).resolve()
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        raise _SympyRuntimeError(f"SymPy {label} module origin unavailable") from exc
    if module_path not in distribution_paths or spec_path not in distribution_paths:
        raise _SympyRuntimeError(
            f"SymPy {label} module origin is outside the installed distribution"
        )
    return {
        "origin": str(module_path),
        "origin_sha256": _sha256_file(module_path),
        "spec_origin": str(spec_path),
    }


def _callable_observation(
    candidate: object,
    *,
    label: str,
    expected_module: str,
    expected_qualname: str,
    distribution_paths: set[Path],
) -> dict[str, str | None]:
    if type(candidate) is not types.FunctionType:
        raise _SympyRuntimeError(f"SymPy {label} is not one Python function")
    try:
        code = candidate.__code__
        code_path = Path(code.co_filename).resolve()
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        raise _SympyRuntimeError(
            f"SymPy {label} code origin unavailable"
        ) from exc
    if code_path not in distribution_paths:
        raise _SympyRuntimeError(
            f"SymPy {label} code origin is outside the installed distribution"
        )
    if (
        candidate.__module__ != expected_module
        or candidate.__qualname__ != expected_qualname
    ):
        raise _SympyRuntimeError(f"SymPy {label} function metadata drift")
    return {
        "callable": f"{expected_module}.{expected_qualname}",
        "function_type": "function",
        "module": candidate.__module__,
        "qualname": candidate.__qualname__,
        "code_origin": str(code_path),
        "code_origin_sha256": _sha256_file(code_path),
        "code_sha256": hashlib.sha256(code.co_code).hexdigest(),
    }


def _capture_sympy_operation_bindings(
    sympy: object,
) -> _SympyOperationBindings:
    try:
        Symbol = getattr(sympy, "Symbol")
        Add = getattr(sympy, "Add")
        Rational = getattr(sympy, "Rational")
        Poly = getattr(sympy, "Poly")
        QQ = getattr(sympy, "QQ")
        return _SympyOperationBindings(
            Symbol=Symbol,
            Add=Add,
            Rational=Rational,
            Poly=Poly,
            QQ=QQ,
            Symbol_new=getattr(Symbol, "__new__"),
            Add_new=getattr(Add, "__new__"),
            Rational_new=getattr(Rational, "__new__"),
            Poly_new=getattr(Poly, "__new__"),
            Poly_as_dict=getattr(Poly, "as_dict"),
        )
    except Exception as exc:
        raise _SympyRuntimeError("SymPy operation bindings are unavailable") from exc


def _same_sympy_operation_bindings(
    left: _SympyOperationBindings,
    right: _SympyOperationBindings,
) -> bool:
    return all(
        getattr(left, field) is getattr(right, field)
        for field in left.__dataclass_fields__
    )


def _require_direct_staticmethod(
    owner: object,
    name: str,
    candidate: object,
) -> None:
    try:
        descriptor = owner.__dict__[name]  # type: ignore[attr-defined]
    except (AttributeError, KeyError, TypeError) as exc:
        raise _SympyRuntimeError(
            f"SymPy direct class binding unavailable: {name}"
        ) from exc
    if type(descriptor) is not staticmethod or descriptor.__func__ is not candidate:
        raise _SympyRuntimeError(f"SymPy direct class binding drift: {name}")


def _expected_witness_output(
    terms: tuple[tuple[int, int, int], ...],
) -> dict[tuple[int], tuple[int, int]]:
    return {
        (degree,): (numerator, denominator)
        for degree, numerator, denominator in terms
    }


def _check_witness_output(
    value: object,
    *,
    expected: dict[tuple[int], tuple[int, int]],
    case_id: str,
) -> list[dict[str, int]]:
    if type(value) is not dict or len(value) != len(expected):
        raise _SympyRuntimeError(
            f"SymPy semantic witness failed: {case_id} output shape"
        )
    observed: list[dict[str, int]] = []
    for monomial, expected_fraction in expected.items():
        try:
            coefficient = value[monomial]
        except (KeyError, TypeError) as exc:
            raise _SympyRuntimeError(
                f"SymPy semantic witness failed: {case_id} missing monomial"
            ) from exc
        if (
            type(coefficient).__module__ != "sympy.core.numbers"
            or getattr(coefficient, "is_Rational", False) is not True
        ):
            raise _SympyRuntimeError(
                f"SymPy semantic witness failed: {case_id} non-rational coefficient"
            )
        numerator = getattr(coefficient, "p", None)
        denominator = getattr(coefficient, "q", None)
        if (
            not _is_plain_int(numerator)
            or not _is_plain_int(denominator)
            or (numerator, denominator) != expected_fraction
        ):
            raise _SympyRuntimeError(
                f"SymPy semantic witness failed: {case_id} coefficient mismatch"
            )
        observed.append(
            {
                "degree": monomial[0],
                "numerator": numerator,
                "denominator": denominator,
            }
        )
    return observed


def _run_semantic_witnesses(
    operation_bindings: _SympyOperationBindings,
) -> dict[str, Any]:
    """Exercise fixed controller-owned exact operations before request data.

    This is intentionally a finite calibration corpus, not model-authored
    SymPy text.  It prevents a function with forged metadata or a constant
    fixture response from satisfying a path-only runtime check.
    """

    results: list[dict[str, Any]] = []
    for case_id, terms in _SEMANTIC_WITNESS_CASES:
        try:
            variable = operation_bindings.Symbol("_constraintbox_sympy_witness")  # type: ignore[operator]
            expression = operation_bindings.Add(  # type: ignore[operator]
                *(
                    operation_bindings.Rational(numerator, denominator)  # type: ignore[operator]
                    * variable**degree
                    for degree, numerator, denominator in terms
                )
            )
            polynomial = operation_bindings.Poly(  # type: ignore[operator]
                expression,
                variable,
                domain=operation_bindings.QQ,
            )
            if polynomial.domain is not operation_bindings.QQ:
                raise _SympyRuntimeError(
                    f"SymPy semantic witness failed: {case_id} escaped QQ"
                )
            observed = operation_bindings.Poly_as_dict(polynomial)  # type: ignore[operator]
        except _SympyRuntimeError:
            raise
        except Exception as exc:
            raise _SympyRuntimeError(
                f"SymPy semantic witness failed: {case_id} execution error: {exc}"
            ) from exc
        results.append(
            {
                "case_id": case_id,
                "input": [
                    {
                        "degree": degree,
                        "numerator": numerator,
                        "denominator": denominator,
                    }
                    for degree, numerator, denominator in terms
                ],
                "output": _check_witness_output(
                    observed,
                    expected=_expected_witness_output(terms),
                    case_id=case_id,
                ),
            }
        )
    return {
        "schema": "constraintbox.symbolic.semantic-witness.v1",
        "controller_owned": True,
        "results": results,
    }


def _verify_sympy_runtime(
    sympy: object,
    operation_bindings: _SympyOperationBindings,
) -> dict[str, Any]:
    """Verify portable SymPy compatibility without pinning one wheel image."""

    policy = _active_sympy_policy()
    distribution, distribution_paths = _sympy_distribution_paths()
    try:
        metadata_version = str(distribution.version)
        public_version = str(getattr(sympy, "__version__"))
    except Exception as exc:
        raise _SympyRuntimeError("SymPy version inspection failed") from exc
    if not _version_in_policy(metadata_version, policy):
        raise _SympyRuntimeError("installed SymPy metadata version is out of profile")
    if public_version != metadata_version:
        raise _SympyRuntimeError(
            "SymPy public version disagrees with installed distribution metadata"
        )

    sympy_module = _module_observation(
        sympy,
        label="public package",
        distribution_paths=distribution_paths,
    )
    bindings: dict[str, dict[str, str | None]] = {}
    for public_name, module_name in _SYMPY_API_BINDINGS:
        implementation_module = importlib.import_module(module_name)
        module_receipt = _module_observation(
            implementation_module,
            label=module_name,
            distribution_paths=distribution_paths,
        )
        try:
            public_api = getattr(sympy, public_name)
            implementation_api = getattr(implementation_module, public_name)
            captured_api = getattr(operation_bindings, public_name)
        except AttributeError as exc:
            raise _SympyRuntimeError(
                f"SymPy API binding unavailable: {public_name}"
            ) from exc
        if public_api is not captured_api or public_api is not implementation_api:
            raise _SympyRuntimeError(
                f"SymPy public API binding drift: {public_name}"
            )
        bindings[public_name] = {"module": module_name, **module_receipt}

    for public_name, expected_module, expected_qualname in (
        ("Symbol", "sympy.core.symbol", "Symbol"),
        ("Add", "sympy.core.add", "Add"),
        ("Rational", "sympy.core.numbers", "Rational"),
        ("Poly", "sympy.polys.polytools", "Poly"),
    ):
        public_type = getattr(operation_bindings, public_name)
        if (
            type(public_type) is not type
            or getattr(public_type, "__module__", None) != expected_module
            or getattr(public_type, "__qualname__", None) != expected_qualname
        ):
            raise _SympyRuntimeError(
                f"SymPy public constructor type drift: {public_name}"
            )

    _require_direct_staticmethod(
        operation_bindings.Symbol,
        "__new__",
        operation_bindings.Symbol_new,
    )
    _require_direct_staticmethod(
        operation_bindings.Rational,
        "__new__",
        operation_bindings.Rational_new,
    )
    _require_direct_staticmethod(
        operation_bindings.Poly,
        "__new__",
        operation_bindings.Poly_new,
    )
    try:
        poly_as_dict_binding = operation_bindings.Poly.__dict__["as_dict"]
    except (AttributeError, KeyError, TypeError) as exc:
        raise _SympyRuntimeError(
            "SymPy Poly.as_dict direct binding unavailable"
        ) from exc
    if poly_as_dict_binding is not operation_bindings.Poly_as_dict:
        raise _SympyRuntimeError("SymPy Poly.as_dict live binding drift")

    operations_module = importlib.import_module("sympy.core.operations")
    try:
        assoc_descriptor = operations_module.AssocOp.__dict__["__new__"]
    except (AttributeError, KeyError, TypeError) as exc:
        raise _SympyRuntimeError(
            "SymPy AssocOp.__new__ binding unavailable"
        ) from exc
    if (
        type(assoc_descriptor) is not staticmethod
        or assoc_descriptor.__func__ is not operation_bindings.Add_new
        or operation_bindings.Add.__new__ is not operation_bindings.Add_new
    ):
        raise _SympyRuntimeError("SymPy Add.__new__ binding drift")

    callable_bindings = {
        "Symbol.__new__": _callable_observation(
            operation_bindings.Symbol_new,
            label="Symbol.__new__",
            expected_module="sympy.core.symbol",
            expected_qualname="Symbol.__new__",
            distribution_paths=distribution_paths,
        ),
        "Add.__new__": _callable_observation(
            operation_bindings.Add_new,
            label="Add.__new__",
            expected_module="sympy.core.operations",
            expected_qualname="AssocOp.__new__",
            distribution_paths=distribution_paths,
        ),
        "Rational.__new__": _callable_observation(
            operation_bindings.Rational_new,
            label="Rational.__new__",
            expected_module="sympy.core.numbers",
            expected_qualname="Rational.__new__",
            distribution_paths=distribution_paths,
        ),
        "Poly.__new__": _callable_observation(
            operation_bindings.Poly_new,
            label="Poly.__new__",
            expected_module="sympy.polys.polytools",
            expected_qualname="Poly.__new__",
            distribution_paths=distribution_paths,
        ),
        "Poly.as_dict": _callable_observation(
            operation_bindings.Poly_as_dict,
            label="Poly.as_dict",
            expected_module="sympy.polys.polytools",
            expected_qualname="Poly.as_dict",
            distribution_paths=distribution_paths,
        ),
    }

    rationalfield_module = importlib.import_module(
        "sympy.polys.domains.rationalfield"
    )
    try:
        rationalfield_type = rationalfield_module.RationalField
        rationalfield_qq = rationalfield_module.QQ
    except AttributeError as exc:
        raise _SympyRuntimeError("SymPy QQ implementation unavailable") from exc
    if (
        operation_bindings.QQ is not rationalfield_qq
        or type(operation_bindings.QQ) is not rationalfield_type
        or type(operation_bindings.QQ).__module__
        != "sympy.polys.domains.rationalfield"
        or type(operation_bindings.QQ).__qualname__ != "RationalField"
    ):
        raise _SympyRuntimeError("SymPy QQ singleton/type identity drift")

    return {
        "schema": "constraintbox.symbolic.runtime-compatibility.v2",
        "distribution": "sympy",
        "observed_version": metadata_version,
        "version_window": {
            "minimum_inclusive": policy.minimum_version,
            "maximum_exclusive": policy.maximum_exclusive_version,
        },
        "runtime_profile": {
            "profile_id": policy.profile_id,
            "registry_sha256": policy.registry_sha256,
            "required_attributes": list(policy.required_attributes),
        },
        "distribution_observation": {
            "module": sympy_module,
            "file_count": len(distribution_paths),
        },
        "api_bindings": bindings,
        "callable_bindings": callable_bindings,
        "object_bindings": {
            "QQ": {
                "module": "sympy.polys.domains.rationalfield",
                "type": "RationalField",
                "identity": "module_singleton",
            },
        },
        "semantic_witness": _run_semantic_witnesses(operation_bindings),
        "trust_boundary": {
            "host_process_must_be_trusted": True,
            "verified_surfaces": [
                "active runtime-profile version and API contract",
                "installed-distribution module origins",
                "selected public API bindings",
                "controller-owned finite exact-operation witnesses",
                "QQ singleton and type",
            ],
            "not_verified": [
                "complete transitive SymPy internal call graph",
                "hostile same-process mutation after the post-operation check",
                "OS process isolation",
                "a globally trusted package wheel or host image",
            ],
        },
    }


@dataclass(frozen=True)
class _ValidatedTerm:
    degree: int
    numerator: int
    denominator: int
    reference: Fraction


@dataclass(frozen=True)
class SympyRationalPolynomialProfile:
    """Check one bounded exact polynomial claim from typed rational data.

    The profile never accepts an expression language.  The controller fixes the
    single supported operation and all resource bounds; the request supplies
    integers only.
    """

    variable_name: str = "x"
    max_degree: int = 16
    max_coefficient_bits: int = 256
    expected_operation: str = _EXACT_OPERATION
    required_version: str = field(default_factory=_default_sympy_minimum_version)
    maximum_exclusive_version: str = field(
        default_factory=_default_sympy_maximum_exclusive_version
    )
    profile_id: str = "constraintbox.symbolic.sympy.poly-qq.v1"
    claim_ceiling: str = (
        "one bounded rational univariate polynomial coefficient claim was "
        "recomputed exactly"
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.variable_name, str)
            or re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,31}", self.variable_name)
            is None
        ):
            raise ValueError("variable_name must be a bounded ASCII identifier")
        if (
            not _is_plain_int(self.max_degree)
            or not 0 <= self.max_degree <= 64
        ):
            raise ValueError("max_degree must be an integer from 0 through 64")
        if (
            not _is_plain_int(self.max_coefficient_bits)
            or not 1 <= self.max_coefficient_bits <= 4096
        ):
            raise ValueError(
                "max_coefficient_bits must be an integer from 1 through 4096"
            )
        if self.expected_operation != _EXACT_OPERATION:
            raise ValueError(f"expected_operation must be {_EXACT_OPERATION!r}")
        try:
            runtime_policy = _active_sympy_policy()
        except _SympyRuntimeError as exc:
            raise ValueError(f"runtime-profile policy unavailable: {exc}") from exc
        if (
            self.required_version != runtime_policy.minimum_version
            or self.maximum_exclusive_version
            != runtime_policy.maximum_exclusive_version
        ):
            raise ValueError(
                "required_version and maximum_exclusive_version must match "
                "the active ConstraintBox runtime profile"
            )

    def _read_terms(
        self,
        value: object,
        *,
        field: str,
        require_canonical: bool,
    ) -> list[_ValidatedTerm]:
        if not isinstance(value, list):
            raise _SymbolicContractError(f"{field} must be a list")
        if len(value) > self.max_degree + 1:
            raise _SymbolicContractError(f"{field} exceeds the term-count bound")

        terms: list[_ValidatedTerm] = []
        seen_degrees: set[int] = set()
        previous_degree = -1
        for index, item in enumerate(value):
            if not isinstance(item, dict) or set(item) != _TERM_KEYS:
                raise _SymbolicContractError(
                    f"{field}[{index}] must contain exactly {sorted(_TERM_KEYS)}"
                )
            degree = item["degree"]
            numerator = item["numerator"]
            denominator = item["denominator"]
            if not all(
                _is_plain_int(part)
                for part in (degree, numerator, denominator)
            ):
                raise _SymbolicContractError(
                    f"{field}[{index}] values must be integers, not booleans"
                )
            if not 0 <= degree <= self.max_degree:
                raise _SymbolicContractError(
                    f"{field}[{index}] degree exceeds the configured bound"
                )
            if degree in seen_degrees:
                raise _SymbolicContractError(
                    f"{field}[{index}] repeats degree {degree}"
                )
            seen_degrees.add(degree)
            if denominator == 0:
                raise _SymbolicContractError(
                    f"{field}[{index}] denominator must be nonzero"
                )
            if (
                abs(numerator).bit_length() > self.max_coefficient_bits
                or abs(denominator).bit_length() > self.max_coefficient_bits
            ):
                raise _SymbolicContractError(
                    f"{field}[{index}] coefficient exceeds the bit-length bound"
                )

            fraction = Fraction(numerator, denominator)
            if require_canonical:
                if degree <= previous_degree:
                    raise _SymbolicContractError(
                        f"{field} must be ordered by strictly increasing degree"
                    )
                if numerator == 0:
                    raise _SymbolicContractError(
                        f"{field} must omit zero coefficients"
                    )
                if denominator <= 0:
                    raise _SymbolicContractError(
                        f"{field} denominators must be positive"
                    )
                if math.gcd(abs(numerator), denominator) != 1:
                    raise _SymbolicContractError(
                        f"{field} fractions must be reduced"
                    )
                previous_degree = degree
            terms.append(
                _ValidatedTerm(
                    degree=degree,
                    numerator=numerator,
                    denominator=denominator,
                    reference=fraction,
                )
            )
        return terms

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome:
        del run_dir
        try:
            body = parse_json_object(payload)
        except IntakeError as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "strict_intake_failed",
                {"error": str(exc)},
            )
        if set(body) != {"coefficients", "claimed_canonical"}:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "symbolic_contract_keys_mismatch",
            )
        try:
            source_terms = self._read_terms(
                body["coefficients"],
                field="coefficients",
                require_canonical=False,
            )
            claimed_terms = self._read_terms(
                body["claimed_canonical"],
                field="claimed_canonical",
                require_canonical=True,
            )
        except _SymbolicContractError as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "symbolic_contract_invalid",
                {"error": str(exc)},
            )
        if not any(item.reference != 0 for item in source_terms):
            return ProfileOutcome(
                Disposition.BLOCKED,
                "symbolic_contract_invalid",
                {
                    "error": (
                        "coefficients must describe a nonzero polynomial"
                    )
                },
            )

        import_evidence = {
            "expected_operation": self.expected_operation,
            "exact_api": _EXACT_API,
            "required_version": self.required_version,
            "maximum_exclusive_version": self.maximum_exclusive_version,
            "phase": "module_import",
        }
        try:
            import sympy  # type: ignore
        except ModuleNotFoundError as exc:
            evidence = {
                **import_evidence,
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "missing_module": exc.name,
            }
            if exc.name == "sympy":
                return ProfileOutcome(
                    Disposition.PARKED,
                    "sympy_unavailable",
                    evidence,
                )
            return ProfileOutcome(
                Disposition.BLOCKED,
                "sympy_import_error",
                evidence,
            )
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "sympy_import_error",
                {
                    **import_evidence,
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )

        try:
            runtime_policy = _active_sympy_policy()
            sympy_version = str(sympy.__version__)
            version_matches_policy = _version_in_policy(
                sympy_version,
                runtime_policy,
            )
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "sympy_version_inspection_error",
                {
                    **import_evidence,
                    "phase": "version_inspection",
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        version_evidence = {
            **import_evidence,
            "phase": "version_check",
            "observed_version": sympy_version,
            "version_matches_policy": version_matches_policy,
            "runtime_profile_id": runtime_policy.profile_id,
            "runtime_profile_registry_sha256": runtime_policy.registry_sha256,
        }
        if not version_matches_policy:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "sympy_version_drift",
                version_evidence,
            )
        try:
            operation_bindings = _capture_sympy_operation_bindings(sympy)
            runtime_identity_before = _verify_sympy_runtime(
                sympy,
                operation_bindings,
            )
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "sympy_runtime_identity_error",
                {
                    **version_evidence,
                    "phase": "runtime_identity_pre_operation",
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )

        reference_by_degree = {
            item.degree: item.reference
            for item in source_terms
            if item.reference != 0
        }
        raw_input = [
            {
                "degree": item.degree,
                "numerator": item.numerator,
                "denominator": item.denominator,
            }
            for item in source_terms
        ]
        canonical_input = [
            _fraction_json(item.degree, item.reference)
            for item in sorted(source_terms, key=lambda item: item.degree)
        ]
        stdlib_reference = [
            _fraction_json(degree, coefficient)
            for degree, coefficient in sorted(reference_by_degree.items())
        ]
        claimed_canonical = [
            _fraction_json(item.degree, item.reference)
            for item in claimed_terms
        ]
        evidence: dict[str, Any] = {
            "tool": "sympy",
            "sympy_version": sympy_version,
            "required_version": self.required_version,
            "maximum_exclusive_version": self.maximum_exclusive_version,
            "version_matches_policy": True,
            "runtime_identity": runtime_identity_before,
            "expected_operation": self.expected_operation,
            "exact_api": _EXACT_API,
            "raw_validated_input": raw_input,
            "raw_validated_input_sha256": hashlib.sha256(
                canonical_json(raw_input)
            ).hexdigest(),
            "canonical_input": canonical_input,
            "canonical_input_sha256": hashlib.sha256(
                canonical_json(canonical_input)
            ).hexdigest(),
            "stdlib_fraction_reference": stdlib_reference,
            "claimed_canonical": claimed_canonical,
            "limits": {
                "variable_name": self.variable_name,
                "max_degree": self.max_degree,
                "max_coefficient_bits": self.max_coefficient_bits,
                "max_terms": self.max_degree + 1,
            },
            "claim_ceiling": self.claim_ceiling,
        }

        try:
            variable = operation_bindings.Symbol(self.variable_name)  # type: ignore[operator]
            if (
                type(variable) is not operation_bindings.Symbol
                or getattr(variable, "name", None) != self.variable_name
            ):
                raise TypeError(
                    "Symbol construction returned an unexpected generator"
                )

            expression = operation_bindings.Add(  # type: ignore[operator]
                *(
                    operation_bindings.Rational(  # type: ignore[operator]
                        item.numerator,
                        item.denominator,
                    )
                    * variable**item.degree
                    for item in source_terms
                )
            )
            polynomial = operation_bindings.Poly(  # type: ignore[operator]
                expression,
                variable,
                domain=operation_bindings.QQ,
            )
            if (
                polynomial.domain is not operation_bindings.QQ
                or type(polynomial.domain) is not type(operation_bindings.QQ)
            ):
                raise TypeError("Poly construction escaped the QQ univariate domain")
            if (
                type(polynomial) is not operation_bindings.Poly
                or type(polynomial.gens) is not tuple
                or len(polynomial.gens) != 1
                or polynomial.gens[0] is not variable
                or type(polynomial.gens[0]) is not operation_bindings.Symbol
            ):
                raise TypeError("Poly construction returned an unexpected type")
            raw_coefficients = operation_bindings.Poly_as_dict(  # type: ignore[operator]
                polynomial
            )
            if type(raw_coefficients) is not dict:
                raise TypeError("Poly.as_dict must return one plain dict")
            if len(raw_coefficients) > self.max_degree + 1:
                raise ValueError(
                    "Poly.as_dict result exceeds the configured term bound"
                )
            sympy_canonical: list[dict[str, int]] = []
            for monomial, coefficient in sorted(raw_coefficients.items()):
                if (
                    type(monomial) is not tuple
                    or len(monomial) != 1
                    or not _is_plain_int(monomial[0])
                ):
                    raise TypeError("Poly.as_dict returned an invalid monomial")
                degree = monomial[0]
                if not 0 <= degree <= self.max_degree:
                    raise ValueError(
                        "Poly.as_dict returned a degree outside the configured bound"
                    )
                if (
                    type(coefficient).__module__ != "sympy.core.numbers"
                    or getattr(coefficient, "is_Rational", False) is not True
                ):
                    raise TypeError(
                        "Poly.as_dict returned a coefficient outside the "
                        "expected SymPy rational domain"
                    )
                numerator = coefficient.p
                denominator = coefficient.q
                if not all(
                    _is_plain_int(part)
                    for part in (numerator, denominator)
                ):
                    raise TypeError(
                        "Poly.as_dict returned non-integer rational components"
                    )
                if numerator == 0 or denominator <= 0:
                    raise ValueError(
                        "Poly.as_dict returned a noncanonical rational coefficient"
                    )
                if (
                    abs(numerator).bit_length() > self.max_coefficient_bits
                    or abs(denominator).bit_length()
                    > self.max_coefficient_bits
                ):
                    raise ValueError(
                        "Poly.as_dict result exceeds the coefficient bit bound"
                    )
                if math.gcd(abs(numerator), denominator) != 1:
                    raise ValueError(
                        "Poly.as_dict returned an unreduced rational coefficient"
                    )
                sympy_canonical.append(
                    {
                        "degree": degree,
                        "numerator": numerator,
                        "denominator": denominator,
                    }
                )
            observed_rational_type_names = sorted(
                {
                    _qualified_type_name(coefficient)
                    for coefficient in raw_coefficients.values()
                }
            )
            exact_operation_receipt = {
                "schema": "constraintbox.symbolic.exact-operation.v1",
                "operation": self.expected_operation,
                "api": _EXACT_API,
                "domain": {
                    "requested": "sympy.QQ",
                    "observed_is_captured_qq": True,
                    "observed_type": _qualified_type_name(polynomial.domain),
                },
                "generator": {
                    "count": 1,
                    "name": self.variable_name,
                    "observed_type": _qualified_type_name(variable),
                    "matches_requested_symbol": True,
                },
                "output": {
                    "mapping_type": _qualified_type_name(raw_coefficients),
                    "term_count": len(raw_coefficients),
                    "permitted_rational_module": "sympy.core.numbers",
                    "observed_rational_types": observed_rational_type_names,
                    "all_output_coefficients_are_supported_rationals": True,
                },
            }
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "sympy_operation_error",
                {
                    **evidence,
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )

        try:
            operation_bindings_after = _capture_sympy_operation_bindings(
                sympy
            )
            runtime_identity_after = _verify_sympy_runtime(
                sympy,
                operation_bindings_after,
            )
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "sympy_runtime_identity_error",
                {
                    **evidence,
                    "phase": "runtime_identity_post_operation",
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        if (
            not _same_sympy_operation_bindings(
                operation_bindings_after,
                operation_bindings,
            )
            or runtime_identity_after != runtime_identity_before
        ):
            return ProfileOutcome(
                Disposition.BLOCKED,
                "sympy_runtime_identity_drift",
                {
                    **evidence,
                    "runtime_identity_post_operation": (
                        runtime_identity_after
                    ),
                },
            )
        evidence["runtime_identity_post_operation"] = runtime_identity_after

        sympy_canonical_bytes = canonical_json(sympy_canonical)
        stdlib_reference_bytes = canonical_json(stdlib_reference)
        claimed_canonical_bytes = canonical_json(claimed_canonical)
        exact_operation_receipt_bytes = canonical_json(exact_operation_receipt)
        crosscheck_agrees = sympy_canonical_bytes == stdlib_reference_bytes
        evidence.update(
            {
                "exact_operation_receipt": exact_operation_receipt,
                "exact_operation_receipt_sha256": hashlib.sha256(
                    exact_operation_receipt_bytes
                ).hexdigest(),
                "sympy_canonical": sympy_canonical,
                "canonical_output": sympy_canonical,
                "canonical_output_sha256": hashlib.sha256(
                    sympy_canonical_bytes
                ).hexdigest(),
                "stdlib_crosscheck_agrees": crosscheck_agrees,
            }
        )
        if not crosscheck_agrees:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "symbolic_crosscheck_disagreement",
                evidence,
            )
        if claimed_canonical_bytes != stdlib_reference_bytes:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "canonical_coefficient_mismatch",
                evidence,
            )
        return ProfileOutcome(
            Disposition.ELIGIBLE,
            "exact_polynomial_recomputed",
            evidence,
        )
