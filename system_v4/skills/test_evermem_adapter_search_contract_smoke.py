"""
Smoke-test the EverMem adapter search contract.

This verifies that the adapter uses the GET search route expected by the local
EverMemOS checkout instead of POSTing to /memories/search.
"""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse
import urllib.request

from system_v4.skills.evermem_adapter import EverMemClient


class _DummyResponse:
    def __init__(self, body: dict):
        self.status = 200
        self._body = body

    def read(self) -> bytes:
        return json.dumps(self._body).encode("utf-8")

    def __enter__(self) -> "_DummyResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def main() -> None:
    captured: dict[str, object] = {}
    original_urlopen = urllib.request.urlopen

    def fake_urlopen(req, timeout=0):  # type: ignore[override]
        captured["method"] = req.get_method()
        captured["url"] = req.full_url
        captured["data"] = req.data
        return _DummyResponse({"result": {"memories": [{"id": "m_001"}]}})

    urllib.request.urlopen = fake_urlopen
    try:
        client = EverMemClient(base_url="http://localhost:1995/api/v1", timeout_seconds=2.0)
        result = client.search_result(
            query="latest witness retrieval probe",
            user_id="system_ratchet",
            method="keyword",
        )
    finally:
        urllib.request.urlopen = original_urlopen

    parsed = urlparse(str(captured["url"]))
    params = parse_qs(parsed.query)

    assert captured["method"] == "GET"
    assert parsed.path == "/api/v1/memories/search"
    assert params.get("query") == ["latest witness retrieval probe"]
    assert params.get("user_id") == ["system_ratchet"]
    assert params.get("retrieve_method") == ["keyword"]
    assert captured["data"] in (None, b"")
    assert result["success"] is True
    assert len(result["memories"]) == 1
    print("PASS: evermem adapter search contract smoke")


if __name__ == "__main__":
    main()
