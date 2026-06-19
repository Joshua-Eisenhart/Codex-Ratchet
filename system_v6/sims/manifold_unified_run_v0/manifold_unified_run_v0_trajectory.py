#!/usr/bin/env python3
"""Persist the shared step trajectory artifact for manifold_unified_run_v0."""

from __future__ import annotations

import json

from manifold_unified_run_v0_common import TRAJECTORY_ARTIFACT_PATH, TRAJECTORY_ARTIFACT_SHA_PATH, write_trajectory_artifact


def main() -> int:
    artifact = write_trajectory_artifact()
    print(
        json.dumps(
            {
                "ok": True,
                "artifact_path": str(TRAJECTORY_ARTIFACT_PATH),
                "artifact_sha_path": str(TRAJECTORY_ARTIFACT_SHA_PATH),
                "content_sha256": artifact["content_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
