from __future__ import annotations

import copy
from pathlib import Path

import pytest

from constraint_box.hookkernel.cb_light_domain import (
    compile_domain,
    version_satisfies_requirement,
)
from constraint_box.hookkernel.cb_light_gate import evaluate_install_command
from constraint_box.hookkernel.cb_light_state import (
    StateError,
    connect,
    record_domain,
)
from constraintbox.cb_light_selection import _normal_status, decide_row


MANDATED = Path(__file__).resolve().parents[1] / ".venv/bin/python"
REPO = Path(__file__).resolve().parents[2]


def _domain():
    return compile_domain(
        installed={"z3-solver": "4.16.0.0", "jax": "0.test"},
        distribution_imports={"z3-solver": ["z3"], "jax": ["jax"]},
        interpreter=str(MANDATED),
    )


def _evaluate(command: str, domain=None):
    return evaluate_install_command(
        {"tool_name": "Bash", "tool_input": {"command": command}},
        domain or _domain(),
        mandated_interpreter=MANDATED,
        cwd=REPO,
    )


def test_direct_requirement_windows_are_evaluated_not_merely_recorded():
    assert version_satisfies_requirement(
        "4.16.0.0", "z3-solver>=4.16.0.0,<4.17.0.0"
    )
    assert not version_satisfies_requirement(
        "4.17.0.0", "z3-solver>=4.16.0.0,<4.17.0.0"
    )
    assert version_satisfies_requirement("1.6.0", "maude==1.6.0")
    assert not version_satisfies_requirement("1.6.1", "maude==1.6.0")
    assert version_satisfies_requirement("1.4.9", "example~=1.4")
    assert not version_satisfies_requirement("2.0.0", "example~=1.4")
    assert version_satisfies_requirement("1.4.8", "example~=1.4.5")
    assert not version_satisfies_requirement("1.5.0", "example~=1.4.5")
    assert version_satisfies_requirement("1.4rc1", "example>=1.4") is None


def test_full_proposal_domain_is_row_preserving_and_light_only():
    domain = _domain()
    assert domain["counts"] == {
        "objects": 214,
        "distributions": 186,
        "stdlib_modules": 28,
        "registry_candidates": 139,
        "pyproject_direct": 5,
        "registry_verdict_disagreements": 1,
    }
    ids = {row["candidate_id"] for row in domain["rows"]}
    assert len(ids) == 214
    assert "pypi:z3-solver" in ids
    assert "stdlib:sqlite3" in ids
    assert "pypi:jax" not in ids
    assert "jax" in domain["environment_observation"]["ambient_installed"]
    assert domain["completeness"] == "UNRESOLVED_OWNER_SELECTION"
    tabulate = next(row for row in domain["rows"] if row["candidate_id"] == "pypi:tabulate")
    assert tabulate["registry_metadata"]["verdict_consistent"] is False
    assert tabulate["registry_metadata"]["observed_predicate_verdict"] == "drop"


def test_ambient_install_never_changes_domain_identity():
    first = compile_domain(installed={}, distribution_imports={})
    second = compile_domain(
        installed={"jax": "99", "torch": "99"},
        distribution_imports={"jax": ["jax"], "torch": ["torch"]},
    )
    assert first["domain_sha256"] == second["domain_sha256"]
    assert first["counts"] == second["counts"]


def test_install_gate_maps_admit_hold_refuse_and_spoof_boundaries():
    assert (
        _evaluate(f"{MANDATED} -m pip install z3-solver==4.16.0.0")[
            "reason_code"
        ]
        == "DECLARED_CORE_INSTALL_BOUNDED"
    )
    assert (
        _evaluate(f"{MANDATED} -m pip install z3-solver")["reason_code"]
        == "DECLARED_VERSION_CONSTRAINT_REQUIRED"
    )
    assert (
        _evaluate(f"{MANDATED} -m pip install z3-solver==4.17.0.0")[
            "reason_code"
        ]
        == "DECLARED_VERSION_CONSTRAINT_REQUIRED"
    )
    assert (
        _evaluate(f"{MANDATED} -m pip install marshmallow")["reason_code"]
        == "CANDIDATE_NOT_SELECTED_FOR_INSTALL"
    )
    assert (
        _evaluate(f"{MANDATED} -m pip install jax")["reason_code"]
        == "PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN"
    )
    assert (
        _evaluate(f"echo {MANDATED} && pip install z3-solver")["reason_code"]
        == "COMPOUND_MUTATION_COMMAND"
    )
    assert (
        _evaluate(f"bash -c '{MANDATED} -m pip install z3-solver==4.16.0.0'")[
            "reason_code"
        ]
        == "INDIRECT_MUTATION_WRAPPER"
    )
    assert (
        _evaluate(f"/usr/bin/env -i {MANDATED} -m pip install jax")["reason_code"]
        == "INDIRECT_MUTATION_WRAPPER"
    )
    assert (
        _evaluate(f"sudo -u root {MANDATED} -m pip install jax")["reason_code"]
        == "INDIRECT_MUTATION_WRAPPER"
    )
    assert (
        _evaluate(f"{MANDATED} -B -m pip install jax")["reason_code"]
        == "PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN"
    )
    assert (
        _evaluate(f"{MANDATED} -W ignore -m pip install jax")["reason_code"]
        == "PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN"
    )
    assert (
        _evaluate(f"uv -q pip install jax --python {MANDATED}")["reason_code"]
        == "PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN"
    )
    assert _evaluate("poetry -v add jax")["reason_code"] == (
        "UNBOUNDED_ENVIRONMENT_MUTATION"
    )
    assert _evaluate("pip --disable-pip-version-check install jax")[
        "reason_code"
    ] == "MANDATED_INTERPRETER_REQUIRED"
    assert _evaluate(
        f"{MANDATED} -m pip install z3-solver==4.16.0.0 --requirement=evil.txt"
    )["reason_code"] == "UNBOUNDED_REQUIREMENT_FILE"
    assert _evaluate(
        f"{MANDATED} -m pip install z3-solver==4.16.0.0 -r=evil.txt"
    )["reason_code"] == "UNBOUNDED_REQUIREMENT_FILE"
    assert _evaluate(
        f"{MANDATED} -m pip install z3-solver==4.16.0.0 --editable=/tmp/evil"
    )["reason_code"] == "PROJECT_INSTALL_OUTSIDE_CB_LIGHT"
    assert _evaluate(
        f"{MANDATED} -m pip install z3-solver==4.16.0.0 --target=/tmp/evil"
    )["reason_code"] == "INSTALL_DESTINATION_OUTSIDE_MANDATED_INTERPRETER"
    assert _evaluate(
        f"{MANDATED} -m pip install z3-solver==4.16.0.0 --index-url=https://example.invalid/simple"
    )["reason_code"] == "UNBOUNDED_PACKAGE_SOURCE"
    assert _evaluate(
        f"{MANDATED} -m pip --python /usr/bin/python3 install z3-solver==4.16.0.0"
    )["reason_code"] == "PIP_TARGET_INTERPRETER_OVERRIDE"
    assert _evaluate(
        f"arch -arm64 {MANDATED} -m pip install jax"
    )["reason_code"] == "MANDATED_INTERPRETER_REQUIRED"
    assert _evaluate("doas pip install jax")["reason_code"] == (
        "UNPARSED_PACKAGE_MUTATION"
    )
    assert (
        _evaluate("uv pip install z3-solver")["reason_code"]
        == "UV_MANDATED_INTERPRETER_REQUIRED"
    )
    assert _evaluate("pip list")["reason_code"] == "NOT_A_PACKAGE_MUTATION"
    assert (
        _evaluate(f"{MANDATED} -m pip install -e constraint_box")["reason_code"]
        == "DECLARED_CORE_INSTALL_BOUNDED"
    )


def test_pyproject_declaration_cannot_promote_a_non_core_candidate():
    domain = copy.deepcopy(_domain())
    candidate = next(
        row for row in domain["rows"] if row["normalized_name"] == "marshmallow"
    )
    candidate["declarations"]["pyproject_direct"] = True
    candidate["declarations"]["pyproject_direct_requirement"] = (
        "marshmallow==3.0.0"
    )
    package = _evaluate(
        f"{MANDATED} -m pip install marshmallow==3.0.0", domain
    )
    assert package["reason_code"] == "CANDIDATE_NOT_SELECTED_FOR_INSTALL"
    project = _evaluate(
        f"{MANDATED} -m pip install -e constraint_box", domain
    )
    assert project["reason_code"] == "PROJECT_DEPENDENCY_SET_NOT_CURRENT_CORE"


def _selectable_row():
    return {
        "candidate_id": "stdlib:fixture",
        "kind": "stdlib_module",
        "normalized_name": "fixture",
        "role_claims": ["bounded fixture"],
        "declarations": {"pyproject_direct": True},
        "core_contract": {"tool_id": "fixture"},
        "observation": {"installed": True, "import_visible": True},
        "registry_metadata": None,
    }


def _complete_probe():
    return {
        "facts": {
            "positive_api_case": True,
            "reason_specific_negative": True,
            "single_field_boundary_flip": True,
            "deterministic_replay": True,
            "severance_observed": True,
            "reference_agreement": True,
            "receipt_consumer_bound": True,
        }
    }


def test_smt_selection_distinguishes_selected_open_and_structural_exclusion():
    selected = decide_row(_selectable_row(), _complete_probe())
    assert selected["disposition"] == "SELECTED_FOR_WORK"
    assert selected["solver"]["agree"] is True

    open_probe = _complete_probe()
    open_probe["facts"]["severance_observed"] = None
    open_result = decide_row(_selectable_row(), open_probe)
    assert open_result["disposition"] == "OPEN_BASIN"
    assert open_result["open_variables"] == ["severance_observed"]

    excluded_row = _selectable_row()
    excluded_row["kind"] = "distribution"
    excluded_row["candidate_id"] = "pypi:fixture"
    excluded_row["registry_metadata"] = {
        "registry_verdict": "drop",
        "predicates": {"release_within_bar": False},
    }
    excluded = decide_row(excluded_row, _complete_probe())
    assert excluded["disposition"] == "EXCLUDED_BY_CONSTRAINT"


def test_vote_normalization_never_discards_an_abstention():
    assert (
        _normal_status(
            {"z3": "SAT", "cvc5": "BOUNDED_SAT", "enumeration": "UNKNOWN"}
        )
        is None
    )


def test_sqlite_state_retains_every_row_and_rejects_digest_laundering(tmp_path):
    domain = _domain()
    connection = connect(tmp_path / "state.sqlite3")
    snapshot_id = record_domain(connection, domain)
    count = connection.execute(
        "SELECT COUNT(*) FROM domain_candidate WHERE snapshot_id = ?", (snapshot_id,)
    ).fetchone()[0]
    assert count == 214

    corrupt = copy.deepcopy(domain)
    corrupt["rows"][0]["role_claims"].append("forged")
    with pytest.raises(StateError, match="digest mismatch"):
        record_domain(connection, corrupt)

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {
        "domain_snapshot",
        "domain_candidate",
        "probe_run",
        "probe_case",
        "tool_decision",
        "selection_run",
        "selection_decision",
        "hook_event",
    } <= tables
    connection.close()
