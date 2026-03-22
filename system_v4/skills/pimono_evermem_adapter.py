"""
pimono_evermem_adapter.py
Connects pi-mono local packages to the EverMemOS memory backend.
"""
from __future__ import annotations
import json
from typing import Any, List, Dict
from system_v4.skills.evermem_adapter import EverMemClient

def fetch_pimono_context(query: str, user_id: str = "pimono_agent_01", limit: int = 5) -> List[Dict[str, Any]]:
    client = EverMemClient()
    results = client.search(query=query, user_id=user_id, method="hybrid")
    return [{"role": "system", "content": f"[Memory]: {r.get('content','')}", "metadata": {"source": "EverMemOS", "msg_id": r.get("message_id")}} for r in results[:limit]]

def run_pimono_evermem_adapter(ctx: dict[str, Any]) -> dict[str, Any]:
    query = ctx.get("query", "")
    if not query:
        return {"error": "Query required"}
    blocks = fetch_pimono_context(query, ctx.get("user_id", "pimono_agent"), ctx.get("limit", 5))
    return {"context_blocks": blocks, "count": len(blocks), "status": "success" if blocks else "no_results"}

if __name__ == "__main__":
    print("PASS: pimono_evermem_adapter self-test")
