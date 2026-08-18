from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_light_jax_wave_bridge.py"
SPEC = importlib.util.spec_from_file_location("run_light_jax_wave_bridge", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


def _children() -> dict:
    return {
        "light_jax_negative": {"status": "PASS"},
        "jax_runtime": {"status": "PROBED"},
        "seed": {"disposition": "ADMIT", "returncode": 0},
        "etf_exact": {"status": "PASS", "returncode": 0},
        "etf_dual": {"status": "PASS", "returncode": 0},
        "maintenance": {"status": "READY", "returncode": 0},
        "context": {"status": "CONTEXT_SNAPSHOT_READY", "returncode": 0},
        "exploration": {"status": "ANTICHAIN_OPEN", "returncode": 0},
        "dualsolve": {"status": "BOUNDED_SAT", "returncode": 0},
    }


def test_all_children_pass_without_promoting_jax_or_wave() -> None:
    status, reasons = bridge.settle(_children())
    assert status == "PASS"
    assert reasons == []


def test_boundary_or_wave_failure_holds() -> None:
    children = _children()
    children["light_jax_negative"] = {"status": "REFUSE_JAX_IN_LIGHT"}
    children["exploration"] = {"status": "HOLD", "returncode": 0}
    status, reasons = bridge.settle(children)
    assert status == "HOLD"
    assert reasons == ["REFUSE_JAX_IN_LIGHT", "HOLD_EXPLORATION_WAVE"]


def test_nonzero_child_returncode_holds_even_with_pass_like_status() -> None:
    children = _children()
    children["etf_exact"] = {"status": "PASS", "returncode": 1}
    status, reasons = bridge.settle(children)
    assert status == "HOLD"
    assert "HOLD_ETF_EXACT_RETURNCODE" in reasons


def test_missing_returncode_field_is_treated_as_a_hold() -> None:
    children = _children()
    del children["dualsolve"]["returncode"]
    status, reasons = bridge.settle(children)
    assert status == "HOLD"
    assert "HOLD_DUALSOLVE_RETURNCODE" in reasons


def test_declared_interpreter_path_is_not_resolved(tmp_path: Path) -> None:
    alias = tmp_path / "python-alias"
    alias.symlink_to(Path(sys.executable))
    declared = bridge.declared_interpreter(alias)
    assert declared == alias.absolute()
    assert declared != alias.resolve()


def test_bridge_output_must_stay_below_product_root(tmp_path: Path) -> None:
    box = tmp_path / "constraint_box"
    box.mkdir()
    inside = bridge.confined_output_dir(box, box / "integrated_system" / "runs" / "one")
    assert inside == (box / "integrated_system" / "runs" / "one").resolve()
    outside = tmp_path / "outside"
    try:
        bridge.confined_output_dir(box, outside)
    except ValueError as exc:
        assert str(exc) == "REFUSE_BRIDGE_OUTPUT_OUTSIDE_PRODUCT"
    else:
        raise AssertionError("bridge must refuse an output path outside the product")


def test_source_checkout_uses_light_first_selected_overlay(tmp_path: Path) -> None:
    box = tmp_path / "constraint_box"
    light_package = box / "light_runtime" / "src" / "constraintbox"
    root_package = box / "src" / "constraintbox"
    light_package.mkdir(parents=True)
    root_package.mkdir(parents=True)
    (light_package / "__init__.py").write_text("LIGHT = True\n", encoding="utf-8")
    (root_package / "distinguishability.py").write_text(
        "ROOT_SELECTED = True\n", encoding="utf-8"
    )
    output = box / "integrated_system" / "runs" / "overlay"
    output.mkdir(parents=True)
    overlay = bridge.selected_controller_overlay(box, output)
    assert overlay == output / ".controller_src"
    assert (overlay / "constraintbox" / "__init__.py").read_text(encoding="utf-8") == "LIGHT = True\n"
    assert (overlay / "constraintbox" / "distinguishability.py").is_file()


def test_replay_projection_ignores_capture_time_but_not_decision() -> None:
    children = _children()
    children["seed"].update(
        {"source_sha256": "a" * 64, "support_counts": [2, 4], "delta_K": [1.0]}
    )
    children["etf_exact"]["result_sha256"] = "b" * 64
    children["etf_dual"].update(
        {"result_sha256": "c" * 64, "jax": {"output_sha256": "d" * 64}}
    )
    children["maintenance"].update(
        {"captured_at": "first", "source_digest": "e" * 64, "context_digest": "f" * 64}
    )
    children["context"].update({"captured_at": "first"})
    children["exploration"].update({"captured_at": "first"})
    first = bridge.replay_projection(
        children, target_sha256="1" * 64, source_bindings={"source": "2" * 64}
    )
    children["maintenance"]["captured_at"] = "second"
    children["context"]["captured_at"] = "second"
    children["exploration"]["captured_at"] = "second"
    second = bridge.replay_projection(
        children, target_sha256="1" * 64, source_bindings={"source": "2" * 64}
    )
    assert first == second
    children["exploration"]["status"] = "HOLD"
    changed = bridge.replay_projection(
        children, target_sha256="1" * 64, source_bindings={"source": "2" * 64}
    )
    assert changed != first
