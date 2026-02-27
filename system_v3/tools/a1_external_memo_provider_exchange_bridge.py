#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Bridge provider for A1 external memo exchange: mirrors requests into work sandbox and waits for response."
    )
    ap.add_argument("--request-json", required=True)
    ap.add_argument("--response-json", required=True)
    ap.add_argument(
        "--exchange-root",
        default="work/a1_sandbox/codex_exchange/provider_bridge",
        help="Workspace-relative exchange root containing requests/ and responses/ folders.",
    )
    ap.add_argument("--wait-timeout-sec", type=int, default=0, help="How long to wait for external response file.")
    ap.add_argument("--poll-interval-ms", type=int, default=500)
    args = ap.parse_args(argv)

    request_path = Path(args.request_json).expanduser().resolve()
    response_path = Path(args.response_json).expanduser().resolve()
    exchange_root = Path(args.exchange_root).expanduser().resolve()
    req_dir = exchange_root / "requests"
    resp_dir = exchange_root / "responses"
    req_dir.mkdir(parents=True, exist_ok=True)
    resp_dir.mkdir(parents=True, exist_ok=True)

    req_obj = _read_json(request_path)
    stem = request_path.name
    exchange_request = req_dir / stem
    _write_json(exchange_request, req_obj)

    expected_response_name = stem.replace("REQUEST", "RESPONSE")
    external_response = resp_dir / expected_response_name
    sequence_prefix = stem.split("__", 1)[0] if "__" in stem else ""

    def _resolve_response_path() -> Path | None:
        if external_response.exists():
            return external_response
        # Fallback for asynchronous/manual providers: allow any response for same sequence.
        if sequence_prefix:
            candidates = sorted(resp_dir.glob(f"{sequence_prefix}__A1_EXTERNAL_MEMO_RESPONSE__*.json"))
            if candidates:
                return candidates[-1]
        return None

    timeout_sec = max(0, int(args.wait_timeout_sec))
    interval_sec = max(0.1, int(args.poll_interval_ms) / 1000.0)
    start = time.time()
    while True:
        resolved = _resolve_response_path()
        if resolved is not None:
            obj = _read_json(resolved)
            if not isinstance(obj, dict) or not isinstance(obj.get("memos"), list):
                print(
                    json.dumps(
                        {
                            "schema": "A1_EXTERNAL_MEMO_PROVIDER_BRIDGE_RESULT_v1",
                            "status": "INVALID_EXTERNAL_RESPONSE",
                            "response_path": str(resolved),
                        },
                        sort_keys=True,
                    )
                )
                return 2
            _write_json(response_path, obj)
            print(
                json.dumps(
                    {
                        "schema": "A1_EXTERNAL_MEMO_PROVIDER_BRIDGE_RESULT_v1",
                        "status": "BRIDGED",
                        "request_path": str(exchange_request),
                        "external_response_path": str(resolved),
                        "exact_name_match": bool(resolved == external_response),
                        "response_path": str(response_path),
                        "memo_count": len(obj.get("memos", [])),
                    },
                    sort_keys=True,
                )
            )
            return 0
        if timeout_sec > 0 and (time.time() - start) >= timeout_sec:
            print(
                json.dumps(
                    {
                        "schema": "A1_EXTERNAL_MEMO_PROVIDER_BRIDGE_RESULT_v1",
                        "status": "WAITING_EXTERNAL_RESPONSE",
                        "request_path": str(exchange_request),
                        "expected_external_response_path": str(external_response),
                    },
                    sort_keys=True,
                )
            )
            return 3
        if timeout_sec == 0:
            print(
                json.dumps(
                    {
                        "schema": "A1_EXTERNAL_MEMO_PROVIDER_BRIDGE_RESULT_v1",
                        "status": "WAITING_EXTERNAL_RESPONSE",
                        "request_path": str(exchange_request),
                        "expected_external_response_path": str(external_response),
                    },
                    sort_keys=True,
                )
            )
            return 3
        time.sleep(interval_sec)


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
