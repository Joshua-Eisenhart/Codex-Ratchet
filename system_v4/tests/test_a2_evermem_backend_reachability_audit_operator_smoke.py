"""Smoke test for the EverMem backend reachability audit operator."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from system_v4.skills import a2_evermem_backend_reachability_audit_operator as module


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        evermemos_repo = root / "work/reference_repos/EverMind-AI/EverMemOS"
        evermemos_repo.mkdir(parents=True, exist_ok=True)
        (evermemos_repo / "env.template").write_text("LLM_API_KEY=x\n", encoding="utf-8")
        (evermemos_repo / "docker-compose.yaml").write_text("services: {}\n", encoding="utf-8")
        (evermemos_repo / "uv.lock").write_text("version = 1\n", encoding="utf-8")
        (evermemos_repo / "src").mkdir(parents=True, exist_ok=True)
        (evermemos_repo / "src/run.py").write_text("print('placeholder')\n", encoding="utf-8")

        retrieval_report = root / "system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.json"
        retrieval_report.parent.mkdir(parents=True, exist_ok=True)
        retrieval_report.write_text(
            json.dumps({"status": "attention_required", "gate": {"recommended_next_step": "hold_at_retrieval_probe"}}),
            encoding="utf-8",
        )
        sync_report = root / "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json"
        sync_report.write_text(json.dumps({"status": "sync_failed"}), encoding="utf-8")

        original_which = module._which
        original_run_command = module._run_command
        original_python_probe = module._python_http_probe
        try:
            module._which = lambda name: f"/usr/bin/{name}"  # type: ignore[assignment]

            def fake_run(argv, cwd=None, timeout_seconds=3.0):  # type: ignore[override]
                if argv[:2] == ["docker", "ps"]:
                    return {
                        "ok": False,
                        "returncode": 1,
                        "stdout": "",
                        "stderr": "Cannot connect to the Docker daemon",
                        "argv": argv,
                    }
                if argv and argv[0] == "curl":
                    return {
                        "ok": False,
                        "returncode": 7,
                        "stdout": "",
                        "stderr": "Failed to connect to localhost port 1995",
                        "argv": argv,
                    }
                raise AssertionError(f"unexpected command: {argv}")

            module._run_command = fake_run  # type: ignore[assignment]
            module._python_http_probe = lambda url, timeout: {  # type: ignore[assignment]
                "ok": False,
                "status_code": None,
                "body_preview": "",
                "error": "URLError: blocked",
            }

            result = module.run_a2_evermem_backend_reachability_audit_operator(
                {"repo_root": str(root), "evermemos_repo_path": str(evermemos_repo)}
            )
        finally:
            module._which = original_which  # type: ignore[assignment]
            module._run_command = original_run_command  # type: ignore[assignment]
            module._python_http_probe = original_python_probe  # type: ignore[assignment]

        _assert(result["status"] == "attention_required", "expected attention_required status")
        _assert(result["gate"]["recommended_next_step"] == "start_docker_daemon", "expected docker-daemon next step")
        _assert(result["docker_daemon"]["ok"] is False, "expected docker daemon to be unavailable")
        _assert(result["health_probes"]["curl"]["ok"] is False, "expected curl probe failure")
        _assert(result["health_probes"]["python"]["ok"] is False, "expected python probe failure")
        _assert(Path(result["report_json_path"]).exists(), "expected report json output")
        _assert(Path(result["packet_path"]).exists(), "expected packet output")
        print("PASS: a2 evermem backend reachability audit operator smoke")


if __name__ == "__main__":
    main()
