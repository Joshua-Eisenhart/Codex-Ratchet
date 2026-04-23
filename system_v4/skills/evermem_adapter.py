"""
evermem_adapter.py

An API adapter skill for EverMemOS (default `http://localhost:1995/api/v1`).

This file provides a bounded HTTP bridge between Ratchet repo-held memory
surfaces and an external EverMem service. It proves attempted projection and
retrieval behavior, not guaranteed backend availability.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List

from system_v4.skills.runtime_state_kernel import Witness, RuntimeState

EVERMEM_URL = "http://localhost:1995/api/v1"
DEFAULT_TIMEOUT_SECONDS = 2.0

class EverMemClient:
    def __init__(self, base_url: str = EVERMEM_URL, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    def _request_json(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        method: str = "POST",
        query_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query_params:
            normalized = {
                key: value
                for key, value in query_params.items()
                if value not in (None, "", [], {})
            }
            encoded = urllib.parse.urlencode(normalized, doseq=True)
            if encoded:
                url = f"{url}?{encoded}"
        data = None if method.upper() == "GET" else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method=method.upper(),
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
                body: dict[str, Any] | list[Any] | str
                try:
                    body = json.loads(raw_body) if raw_body else {}
                except json.JSONDecodeError:
                    body = raw_body
                return {
                    "ok": response.status in (200, 201),
                    "status_code": response.status,
                    "body": body,
                    "error": "",
                }
        except urllib.error.HTTPError as exc:
            raw_body = exc.read().decode("utf-8", errors="replace")
            try:
                body = json.loads(raw_body) if raw_body else {}
            except json.JSONDecodeError:
                body = raw_body
            return {
                "ok": False,
                "status_code": exc.code,
                "body": body,
                "error": f"HTTPError: {exc.code}",
            }
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            return {
                "ok": False,
                "status_code": None,
                "body": {},
                "error": f"URLError: {reason}",
            }
        except TimeoutError:
            return {
                "ok": False,
                "status_code": None,
                "body": {},
                "error": "TimeoutError",
            }

    def store_memory_result(
        self,
        msg_id: str,
        sender: str,
        content: str,
        memory_types: List[str] | None = None,
    ) -> dict[str, Any]:
        """Stores a new episodic memory and returns a detailed result."""
        data = {
            "message_id": msg_id,
            "create_time": datetime.now(timezone.utc).isoformat(),
            "sender": sender,
            "content": content,
        }
        if memory_types:
            data["memory_types"] = memory_types

        result = self._request_json("/memories", data, method="POST")
        return {
            "success": bool(result.get("ok")),
            "status_code": result.get("status_code"),
            "error": result.get("error", ""),
            "body": result.get("body", {}),
            "message_id": msg_id,
        }

    def store_memory(
        self,
        msg_id: str,
        sender: str,
        content: str,
        memory_types: List[str] | None = None,
    ) -> bool:
        """Boolean compatibility wrapper around detailed store results."""
        return self.store_memory_result(msg_id, sender, content, memory_types).get("success", False)

    def search_result(
        self,
        query: str,
        user_id: str = "system_ratchet",
        method: str = "hybrid",
    ) -> dict[str, Any]:
        """Searches EverMem using the repo's GET search contract and returns a detailed result."""
        query_params = {
            "query": query,
            "user_id": user_id,
            "retrieve_method": method,
        }
        result = self._request_json(
            "/memories/search",
            {},
            method="GET",
            query_params=query_params,
        )
        body = result.get("body", {})
        memories: list[dict[str, Any]] = []
        if isinstance(body, dict):
            memories = body.get("result", {}).get("memories", []) or []
        return {
            "success": bool(result.get("ok")),
            "status_code": result.get("status_code"),
            "error": result.get("error", ""),
            "memories": memories,
        }

    def search(self, query: str, user_id: str = "system_ratchet", method: str = "hybrid") -> List[Dict[str, Any]]:
        """Compatibility wrapper around detailed search results."""
        return self.search_result(query, user_id=user_id, method=method).get("memories", [])

def run_evermem_store(ctx: dict[str, Any]) -> dict[str, Any]:
    """Adapter dispatch hook."""
    client = EverMemClient(
        ctx.get("base_url", EVERMEM_URL),
        timeout_seconds=float(ctx.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
    )
    content = ctx.get("content", "")
    msg_id = ctx.get("msg_id", f"msg_{datetime.now(timezone.utc).timestamp()}")
    sender = ctx.get("sender", "ratchet_v4")
    memory_types = ctx.get("memory_types", ["episodic_memory"])

    result = client.store_memory_result(msg_id, sender, content, memory_types)
    return {
        "success": result.get("success", False),
        "msg_id": msg_id,
        "status_code": result.get("status_code"),
        "error": result.get("error", ""),
    }

if __name__ == "__main__":
    # Self-test (will gracefully fail returning False if Docker container is down)
    client = EverMemClient()
    success = client.store_memory("test_001", "self_test", "EverMem adapter online.")
    print(f"PASS: evermem_adapter self-test (Connection success: {success})")
