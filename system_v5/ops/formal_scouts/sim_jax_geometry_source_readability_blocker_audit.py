#!/usr/bin/env python3
"""Audit source readability for JAX native geometry wrapper scripts.

The native-geometry result receipts are readable, but the tiny wrapper scripts
can hang on ordinary reads in this workspace state. This audit records that as
a source-hardening blocker instead of letting the controller pretend the source
emitter was inspected.
"""

from __future__ import annotations

import json
import signal
import time
from pathlib import Path


SRC_DIR = Path("system_v5/ops/formal_scouts")
OUT_DIR = Path("system_v5/ops/wizard_admissions")


def timed_read(path: Path, timeout_sec: int = 2) -> tuple[bool, str]:
    def boom(signum, frame):  # type: ignore[no-untyped-def]
        raise TimeoutError(f"read timeout after {timeout_sec}s")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(timeout_sec)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        signal.alarm(0)
        return True, text[:240]
    except Exception as exc:  # noqa: BLE001 - this is an audit surface.
        signal.alarm(0)
        return False, repr(exc)
    finally:
        signal.signal(signal.SIGALRM, old)


def main() -> int:
    rows = []
    failures = []
    for path in sorted(SRC_DIR.glob("sim_jax_native_geometry_*_probe.py")):
        ok, preview = timed_read(path)
        row = {
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "read_ok_under_timeout": ok,
            "preview_or_error": preview,
        }
        rows.append(row)
        if not ok:
            failures.append({"path": str(path), "reason": "source_read_timeout", "detail": preview})

    out = {
        "kind": "jax_geometry_source_readability_blocker_audit",
        "classification": "source_readability_audit",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "JAX native-geometry wrapper scripts only; no Julia, no PyTorch, no sim execution.",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "allowed_claim": "Source-readability blocker audit only.",
        "blocked_claims": [
            "source emitter inspected",
            "geometry receipt source fence hardened",
            "full layer completion",
            "official G-structure selection",
            "layer stacking readiness",
            "flux",
            "Axis0",
            "FEP",
            "physics/gravity",
            "final manifold admission",
        ],
        "checks": {
            "all_wrapper_sources_readable_under_timeout": all(row["read_ok_under_timeout"] for row in rows),
            "no_completion_claim_made": True,
        },
        "rows": rows,
        "failures": failures,
        "AUDIT_PASS": not failures,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"jax_geometry_source_readability_blocker_audit_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"geometry_source_readability_audit AUDIT_PASS={out['AUDIT_PASS']} rows={len(rows)} failures={len(failures)} path={out_path}")
    return 0 if out["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
