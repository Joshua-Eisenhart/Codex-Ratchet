from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
LIGHT_SOURCE = ROOT / "light_runtime" / "src"
PACKAGE_NAME = "_cb_light_wave_entry_gate"


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


def test_wave_cli_refuses_before_request_or_sqlite_when_evaluation_is_not_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    core_cli = _load_core_cli()
    db_path = tmp_path / "wave.sqlite"
    request_path = tmp_path / "unread-request.json"
    monkeypatch.setattr(
        core_cli,
        "_current_cb_light_evaluation_for_wave",
        lambda: (
            False,
            "CB_LIGHT_EVALUATION_GATE_HOLD:MANIFEST_SOURCE_DIGEST_MISMATCH",
            {"mode": "test", "evaluation_reason_code": "MANIFEST_SOURCE_DIGEST_MISMATCH"},
        ),
    )

    with pytest.raises(SystemExit) as raised:
        core_cli.main(["wave", "--request", str(request_path), "--db", str(db_path)])

    assert raised.value.code == 2
    body = json.loads(capsys.readouterr().out)
    assert body["disposition"] == "HOLD"
    assert body["reason_code"] == "HOLD_WAVE_REQUIRES_CURRENT_CB_LIGHT_EVALUATION"
    assert body["persisted"] is False
    assert body["entry_gate"]["mode"] == "test"
    assert not db_path.exists()
