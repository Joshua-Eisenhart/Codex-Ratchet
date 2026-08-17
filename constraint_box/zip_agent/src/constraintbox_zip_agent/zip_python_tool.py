from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .protocol import TaskSpec, ZipJobRefusal, canonical_json_bytes, sha256_bytes, strict_json_loads

SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
_HOST_SANDBOX_ENV = (
    "APP_SANDBOX_CONTAINER_ID",
    "CODEX_SANDBOX",
    "CODEX_SANDBOX_NETWORK",
    "CODEX_SANDBOX_LANDLOCK",
)


def host_sandbox_attested() -> str | None:
    for name in _HOST_SANDBOX_ENV:
        value = os.environ.get(name)
        if isinstance(value, str) and value.strip():
            return f"env:{name}"
    return None


def seatbelt_usable() -> bool:
    if not SANDBOX_EXEC.is_file():
        return False
    try:
        proc = subprocess.run(
            [str(SANDBOX_EXEC), "-p", "(version 1)(allow default)", "/usr/bin/true"],
            capture_output=True,
            timeout=5,
            check=False,
        )
    except OSError:
        return False
    return proc.returncode == 0


def choose_containment() -> dict[str, object]:
    if seatbelt_usable():
        return {
            "containment_profile": "seatbelt",
            "containment_attestation": "sandbox-exec",
            "os_sandbox": True,
            "network_denied": True,
            "containment_hold": False,
        }
    return {
        "containment_profile": "none",
        "containment_attestation": None,
        "os_sandbox": False,
        "network_denied": False,
        "containment_hold": True,
    }


def _sandbox_profile(work: Path) -> str:
    # Keep host-wide file-read*. A work+interpreter allowlist SIGABRT'd the
    # contained CPython on 2026-08-15 (exit -6). That mutation is discarded.
    root = work.resolve()
    return (
        "(version 1)\n"
        "(deny default)\n"
        "(allow file-read*)\n"
        f"(allow file-write* (subpath {json.dumps(str(root))}))\n"
        "(allow process-exec)\n"
        "(allow process-fork)\n"
        "(allow signal)\n"
        "(allow sysctl-read)\n"
        "(allow mach-lookup)\n"
        "(deny network*)\n"
    )


def _tool_command(work: Path, script: Path, *, use_seatbelt: bool) -> list[str]:
    argv = [str(Path(sys.executable).resolve()), str(script)]
    if not use_seatbelt:
        return argv
    profile = work / "meta" / "sandbox.sb"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text(_sandbox_profile(work), encoding="utf-8")
    return [str(SANDBOX_EXEC), "-f", str(profile), *argv]


RESULT_NAME = "output/tool_result.json"
_HEX64 = frozenset("0123456789abcdef")


def _tool_env(work: Path) -> dict[str, str]:
    home = work / "home"
    tmp = work / "tmp"
    home.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)
    python_dir = str(Path(sys.executable).resolve().parent)
    return {
        "PATH": os.pathsep.join([python_dir, "/usr/bin", "/bin"]),
        "HOME": str(home),
        "TMPDIR": str(tmp),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "LANG": "C",
    }


def _contained(root: Path, rel: str, *, reason: str) -> Path:
    if not rel or rel.startswith("/") or "\\" in rel:
        raise ZipJobRefusal(reason, rel)
    parts = Path(rel).parts
    if ".." in parts or not parts:
        raise ZipJobRefusal(reason, rel)
    dest = (root / rel).resolve()
    try:
        dest.relative_to(root.resolve())
    except ValueError as exc:
        raise ZipJobRefusal(reason, rel) from exc
    return dest


def run_zip_python_tool(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    if len(task.input_paths) != 2 or len(task.output_paths) != 1:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    script_path, payload_path = task.input_paths
    output_path = task.output_paths[0]
    if not script_path.startswith("TOOLS/") or not script_path.endswith(".py"):
        raise ZipJobRefusal("REFUSE_ZIP_PYTHON_TOOL_PATH", script_path)
    script = workspace[script_path]
    payload = workspace[payload_path]
    strict_json_loads(payload, label=payload_path)
    with tempfile.TemporaryDirectory(prefix="cb-zip-py-tool-") as tmp:
        work = Path(tmp)
        dest_script = _contained(work, script_path, reason="REFUSE_ZIP_PYTHON_TOOL_PATH")
        dest_payload = _contained(work, payload_path, reason="REFUSE_ZIP_PYTHON_TOOL_PATH")
        dest_script.parent.mkdir(parents=True, exist_ok=True)
        dest_payload.parent.mkdir(parents=True, exist_ok=True)
        (work / "output").mkdir(parents=True, exist_ok=True)
        dest_script.write_bytes(script)
        dest_payload.write_bytes(payload)
        containment = choose_containment()
        if containment["containment_hold"]:
            raise ZipJobRefusal("REFUSE_ZIP_PYTHON_TOOL_SANDBOX_UNAVAILABLE")
        argv = _tool_command(
            work,
            dest_script,
            use_seatbelt=containment["containment_profile"] == "seatbelt",
        )
        proc = subprocess.run(
            argv,
            cwd=str(work),
            env=_tool_env(work),
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or "").strip().replace("\n", " ")[:512]
            raise ZipJobRefusal(
                "REFUSE_ZIP_PYTHON_TOOL_FAILED",
                f"{proc.returncode}:{detail}" if detail else str(proc.returncode),
            )
        result_path = _contained(work, RESULT_NAME, reason="REFUSE_ZIP_PYTHON_TOOL_PATH")
        if not result_path.is_file() or result_path.stat().st_size == 0:
            raise ZipJobRefusal("REFUSE_ZIP_PYTHON_TOOL_MISSING_OUTPUT", RESULT_NAME)
        result = strict_json_loads(result_path.read_bytes(), label=RESULT_NAME)
        if not isinstance(result, dict):
            raise ZipJobRefusal("REFUSE_ZIP_PYTHON_TOOL_RESULT", "not_object")
        reported_token = result.get("canonical_sha256")
        if (
            not isinstance(reported_token, str)
            or len(reported_token) != 64
            or set(reported_token) - _HEX64
        ):
            raise ZipJobRefusal("REFUSE_ZIP_PYTHON_TOOL_RESULT", "canonical_sha256")
        result_raw = result_path.read_bytes()
        evidence_token = sha256_bytes(result_raw)
        evidence = {
            "schema": "constraintbox.zip-python-tool-evidence.v2",
            "script_path": script_path,
            "script_sha256": sha256_bytes(script),
            "payload_path": payload_path,
            "payload_sha256": sha256_bytes(payload),
            "result_sha256": evidence_token,
            "canonical_sha256": evidence_token,
            "untrusted_tool_claim_sha256": reported_token,
            "returncode": proc.returncode,
            "stdout_sha256": sha256_bytes((proc.stdout or "").encode("utf-8")),
            "stderr_sha256": sha256_bytes((proc.stderr or "").encode("utf-8")),
            "env_scrubbed": True,
            "containment_profile": containment["containment_profile"],
            "containment_attestation": containment["containment_attestation"],
            "ambient_host_sandbox_marker": host_sandbox_attested(),
            "containment_hold": containment["containment_hold"],
            "network_denied": containment["network_denied"],
            "os_sandbox": containment["os_sandbox"],
            "host_hooks_used": False,
            "promotion_allowed": False,
            "claim_ceiling": (
                "CB-executed packet Python only; env scrubbed; "
                + f"containment={containment['containment_profile']}; "
                + "canonical_sha256 is a CB-derived token over exact result bytes; "
                + "untrusted_tool_claim_sha256 is untrusted semantic output; "
                + "not LLM tool use; not admission"
            ),
        }
    return {output_path: canonical_json_bytes(evidence)}


DEFAULT_MAKE_TOKEN_PY = b'''from __future__ import annotations

import hashlib
import json
from pathlib import Path

payload = json.loads(Path("inputs/tool_payload.json").read_text(encoding="utf-8"))
canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
token = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
Path("output").mkdir(exist_ok=True)
Path("output/tool_result.json").write_text(
    json.dumps(
        {
            "schema": "constraintbox.zip-python-tool-result.v1",
            "tool_id": "make_token",
            "canonical_sha256": token,
        },
        sort_keys=True,
    )
    + "\\n",
    encoding="utf-8",
)
'''
