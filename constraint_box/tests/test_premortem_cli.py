from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
LIGHT_SOURCE = ROOT / "light_runtime" / "src"
PACKAGE_NAME = "_cb_light_premortem_cli"


def _load_core_cli():
    if PACKAGE_NAME not in sys.modules:
        init_py = LIGHT_SOURCE / "constraintbox" / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            PACKAGE_NAME,
            init_py,
            submodule_search_locations=[str(init_py.parent)],
        )
        assert spec is not None and spec.loader is not None
        package = importlib.util.module_from_spec(spec)
        sys.modules[PACKAGE_NAME] = package
        spec.loader.exec_module(package)
    return importlib.import_module(f"{PACKAGE_NAME}.core_cli")


core_cli = _load_core_cli()


def _current_gate() -> tuple[bool, str, dict[str, object]]:
    return True, "CB_LIGHT_EVALUATION_GATE_CURRENT", {"mode": "test-current-light"}


def test_premortem_parser_wires_only_the_declared_path_arguments() -> None:
    args = core_cli.build_parser().parse_args(
        ["premortem", "--request", "request.json", "--db", "state.sqlite", "--output", "result.json"]
    )

    assert args.command == "premortem"
    assert args.request == Path("request.json")
    assert args.db == Path("state.sqlite")
    assert args.output == Path("result.json")


def test_premortem_preflight_short_circuits_before_request_or_controller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request_path = tmp_path / "unread-request.json"
    db_path = tmp_path / "state.sqlite"
    monkeypatch.setattr(
        core_cli,
        "_current_cb_light_evaluation_for_wave",
        lambda: (
            False,
            "CB_LIGHT_EVALUATION_GATE_HOLD:MANIFEST_SOURCE_DIGEST_MISMATCH",
            {"mode": "test-stale-light"},
        ),
    )
    monkeypatch.setattr(
        core_cli,
        "_read_strict_premortem_request",
        lambda _path: (_ for _ in ()).throw(AssertionError("request was read")),
    )
    monkeypatch.setattr(
        core_cli,
        "_run_premortem_remediation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("controller called")),
    )

    with pytest.raises(SystemExit) as raised:
        core_cli.main(["premortem", "--request", str(request_path), "--db", str(db_path)])

    assert raised.value.code == 2
    body = json.loads(capsys.readouterr().out)
    assert body["terminal"] == "HOLD"
    assert body["reason_code"] == "HOLD_PREMORTEM_REQUIRES_CURRENT_CB_LIGHT_EVALUATION"
    assert body["entry_gate"] == {"mode": "test-stale-light"}
    assert not db_path.exists()


def test_premortem_invalid_json_refuses_before_controller_or_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request_path = tmp_path / "invalid.json"
    db_path = tmp_path / "state.sqlite"
    request_path.write_text('{"schema":', encoding="utf-8")
    monkeypatch.setattr(core_cli, "_current_cb_light_evaluation_for_wave", _current_gate)
    monkeypatch.setattr(
        core_cli,
        "_run_premortem_remediation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("controller called")),
    )

    with pytest.raises(SystemExit) as raised:
        core_cli.main(["premortem", "--request", str(request_path), "--db", str(db_path)])

    assert raised.value.code == 2
    body = json.loads(capsys.readouterr().out)
    assert body["terminal"] == "REFUSE"
    assert body["reason_code"] == "REFUSE_PREMORTEM_REQUEST_INVALID_JSON"
    assert body["attempt_id"] is None
    assert not db_path.exists()


def test_premortem_success_writes_exact_structured_json_and_returns_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request_path = tmp_path / "request.json"
    output_path = tmp_path / "result.json"
    db_path = tmp_path / "state.sqlite"
    request = {"request": "sealed"}
    request_path.write_text(json.dumps(request), encoding="utf-8")
    monkeypatch.setattr(core_cli, "_current_cb_light_evaluation_for_wave", _current_gate)
    calls: list[tuple[dict[str, object], Path | None]] = []
    controller_body: dict[str, object] = {
        "schema": "constraintbox.premortem-remediation-result.v1",
        "terminal": "VERIFIED_DONE",
        "reason_code": "FRESH_DECLARED_COMPLETION_GATE_PASS",
        "state_outcome": "SETTLED",
    }

    def fake_controller(
        raw: dict[str, object], *, db_path: Path | None
    ) -> dict[str, object]:
        calls.append((raw, db_path))
        return dict(controller_body)

    monkeypatch.setattr(core_cli, "_run_premortem_remediation", fake_controller)

    core_cli.main(
        [
            "premortem",
            "--request",
            str(request_path),
            "--db",
            str(db_path),
            "--output",
            str(output_path),
        ]
    )

    expected = {**controller_body, "entry_gate": {"mode": "test-current-light"}}
    rendered = json.dumps(expected, sort_keys=True, indent=2) + "\n"
    assert capsys.readouterr().out == rendered
    assert output_path.read_text(encoding="utf-8") == rendered
    assert calls == [(request, db_path)]


def test_premortem_noncompletion_exit_is_two(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(core_cli, "_current_cb_light_evaluation_for_wave", _current_gate)
    monkeypatch.setattr(
        core_cli,
        "_run_premortem_remediation",
        lambda _raw, *, db_path: {
            "schema": "constraintbox.premortem-remediation-result.v1",
            "terminal": "HOLD",
            "reason_code": "AWAITING_NEXT_RECEIPT_VERIFIED_CANDIDATE",
            "state_outcome": "HOLD",
        },
    )

    with pytest.raises(SystemExit) as raised:
        core_cli.main(["premortem", "--request", str(request_path)])

    assert raised.value.code == 2
    assert json.loads(capsys.readouterr().out)["terminal"] == "HOLD"


def test_premortem_branch_has_no_wave_legacy_or_ui_surface() -> None:
    source = inspect.getsource(core_cli.main)
    branch = source[
        source.index('    if args.command == "premortem":') : source.index(
            "\n    body = doctor()", source.index('    if args.command == "premortem":')
        )
    ]
    lazy_controller = inspect.getsource(core_cli._run_premortem_remediation)

    for forbidden in (
        "wave_controller",
        "run_fixture_wave_file",
        "control_plane",
        "cb_run",
        "legacy",
        "browser",
        "webui",
        ".html",
        "provider",
        "heavy",
        "subprocess",
    ):
        assert forbidden not in branch.lower()
        assert forbidden not in lazy_controller.lower()
