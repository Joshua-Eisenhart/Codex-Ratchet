"""Boundary map for the PreToolUse package guard.

The guard was built with a positive (block a package install on the wrong
interpreter) but no admit-side probe, so it over-fired: `which uv` was refused
with ENV_INTERPRETER_MISMATCH because the command merely contained the token
`uv`. That is the unmapped-admit-region shape.

These probes map both sides. A package-mutation verb on the wrong interpreter
must still fire (fail-closed on the dangerous direction). Inspection commands
that merely name the tool must pass.

Honest boundary note: the matcher works on the raw command string, so a command
that QUOTES an install string (for example `grep 'pip install' .`) still fires.
That is a false positive in the safe direction — it routes to the kernel, which
HOLDs; it never lets a real install through. Missing a real install is the
direction that matters, and the probes below pin it.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

GUARD = pathlib.Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "cb_pretooluse_guard.sh"
MANDATED = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"


def _fires(command: str) -> bool:
    """True when the guard blocks the command (exit != 0).

    The guard receives the real Claude Code PreToolUse envelope on stdin, so the
    probe must feed that exact shape. Feeding a raw command string makes the
    kernel extract an empty command and refuse for the wrong reason.
    """
    envelope = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    proc = subprocess.run(
        ["bash", str(GUARD)],
        input=envelope,
        capture_output=True,
        text=True,
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
    assert _fires(f"{MANDATED} -m pip install numpy") is False


def test_wrong_interpreter_install_is_refused():
    assert _fires("/usr/bin/python3 -m pip install numpy") is True
