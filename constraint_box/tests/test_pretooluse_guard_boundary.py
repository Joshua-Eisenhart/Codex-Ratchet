"""Boundary map for the parsed CB Light PreToolUse package gate."""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import tempfile

GUARD = pathlib.Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "cb_pretooluse_guard.sh"
MANDATED = str(pathlib.Path(__file__).resolve().parents[1] / ".venv/bin/python")


def _fires(command: str) -> bool:
    """True when the guard blocks the command (exit != 0).

    The guard receives the real Claude Code PreToolUse envelope on stdin, so the
    probe must feed that exact shape. Feeding a raw command string makes the
    kernel extract an empty command and refuse for the wrong reason.
    """
    envelope = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    with tempfile.TemporaryDirectory() as directory:
        environment = os.environ.copy()
        environment["CB_LIGHT_STATE_DB"] = str(pathlib.Path(directory) / "state.sqlite3")
        environment["CLAUDE_PROJECT_DIR"] = str(GUARD.parents[2])
        proc = subprocess.run(
            ["bash", str(GUARD)],
            input=envelope,
            capture_output=True,
            text=True,
            env=environment,
        )
    return proc.returncode != 0


# --- admit side: inspection commands that name the tool must PASS ---

def test_which_uv_is_admitted():
    assert _fires("which uv") is False


def test_uv_version_is_admitted():
    assert _fires("uv --version") is False


def test_pip_list_is_admitted():
    assert _fires("pip list") is False


def test_pip_show_is_admitted():
    assert _fires("pip show sympy") is False


def test_unrelated_command_is_admitted():
    assert _fires("ls constraint_box/requirements") is False


# --- refuse side: real package mutations on the wrong interpreter must FIRE ---

def test_bare_pip_install_fires():
    assert _fires("pip install numpy") is True


def test_uv_add_fires():
    assert _fires("uv add requests") is True


def test_pip_uninstall_fires():
    assert _fires("pip uninstall sympy") is True


def test_python_m_pip_install_fires():
    assert _fires("python3 -m pip install cvxpy") is True


# --- the point of the whole guard: mandated-interpreter install is admitted,
#     wrong-interpreter install is refused. Same verb, different interpreter. ---

def test_mandated_interpreter_install_is_admitted():
    assert _fires(f"{MANDATED} -m pip install z3-solver==4.16.0.0") is False


def test_unpinned_core_install_is_held():
    assert _fires(f"{MANDATED} -m pip install z3-solver") is True


def test_unselected_candidate_install_is_held():
    assert _fires(f"{MANDATED} -m pip install marshmallow") is True


def test_heavy_ambient_package_does_not_enter_light_domain():
    assert _fires(f"{MANDATED} -m pip install jax") is True


def test_uv_pip_without_explicit_interpreter_is_refused():
    assert _fires("uv pip install z3-solver") is True


def test_uv_pip_with_exact_interpreter_is_admitted():
    assert _fires(f"uv pip install z3-solver==4.16.0.0 --python {MANDATED}") is False


def test_interpreter_path_mentioned_but_not_executed_is_refused():
    assert _fires(f"echo {MANDATED} && pip install z3-solver") is True


def test_nested_shell_install_is_refused():
    assert _fires(f"bash -c '{MANDATED} -m pip install z3-solver==4.16.0.0'") is True


def test_wrong_interpreter_install_is_refused():
    assert _fires("/usr/bin/python3 -m pip install numpy") is True
