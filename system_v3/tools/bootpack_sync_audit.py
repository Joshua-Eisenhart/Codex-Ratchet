#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_tags(boot: str) -> List[str]:
    tags: List[str] = []
    m = re.search(
        r"Only the following rejection tags are permitted:(.*?)(?:Any other tag is forbidden|RULE BR-001)",
        boot,
        flags=re.S,
    )
    if not m:
        return tags
    for line in m.group(1).splitlines():
        s = line.strip()
        if re.fullmatch(r"[A-Z_]+", s):
            tags.append(s)
    return tags


def extract_stages(boot: str) -> List[str]:
    out: List[str] = []
    seen = set()
    for line in boot.splitlines():
        s = line.strip()
        if not s.startswith("STAGE "):
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def extract_containers(boot: str) -> List[str]:
    return re.findall(r"CONTAINER\s+([A-Z_]+(?:\s+v\d+)?)", boot)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    b_boot_path = root / "core_docs" / "BOOTPACK_THREAD_B_v3.9.13.md"
    a_boot_path = root / "core_docs" / "BOOTPACK_THREAD_A_v2.60.md"
    if not a_boot_path.exists():
        a_boot_path = root / "core_docs" / "BOOTPACK_THREAD_A0_v2.60.md"
    b_spec_path = root / "system_v3/specs/03_B_KERNEL_SPEC.md"
    a_projection_path = root / "system_v3/specs/14_A_THREAD_BOOTPACK_PROJECTION.md"

    reports_dir = root / "system_v3/specs/reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "bootpack_sync_report.json"

    b_boot = load(b_boot_path)
    a_boot = load(a_boot_path)
    b_spec = load(b_spec_path)
    a_projection = load(a_projection_path) if a_projection_path.exists() else ""

    critical: List[Dict[str, str]] = []
    major: List[Dict[str, str]] = []
    minor: List[Dict[str, str]] = []
    unknown: List[Dict[str, str]] = []

    containers = sorted(set(extract_containers(b_boot)))
    required_container_tokens = ["EXPORT_BLOCK", "SIM_EVIDENCE", "THREAD_S_SAVE_SNAPSHOT"]
    for tok in required_container_tokens:
        if tok not in b_spec:
            critical.append(
                {
                    "class": "container_sync",
                    "token": tok,
                    "reason": "missing from B owner spec",
                }
            )

    tags = extract_tags(b_boot)
    for tag in tags:
        if tag not in b_spec:
            major.append(
                {
                    "class": "tag_fence_sync",
                    "token": tag,
                    "reason": "tag listed in bootpack but absent in B owner spec",
                }
            )

    stages = extract_stages(b_boot)
    for stage in stages:
        if stage not in b_spec:
            major.append(
                {
                    "class": "stage_sync",
                    "token": stage,
                    "reason": "stage line listed in bootpack but absent in B owner spec",
                }
            )

    # Duplicated sections in bootpack are informational drift signals.
    container_section_count = b_boot.count("3) ACCEPTED CONTAINERS")
    if container_section_count > 1:
        minor.append(
            {
                "class": "bootpack_duplication",
                "token": "3) ACCEPTED CONTAINERS",
                "reason": f"section appears {container_section_count} times in bootpack source",
            }
        )

    a_tokens = [
        "A-001 NO_SMOOTHING",
        "A-003 NO_CHOICE_POLICY",
        "A-015 ARTIFACT_DRAFT_PROSE_BAN",
        "A-018 FORMULA_SYMBOL_POLICY",
        "A-019 GLYPH_POLICY",
        "A-110 RULESET_SHA256_HEADER_INJECTION",
        "A-116 MEGABOOT_SHA256_HEADER_INJECTION",
    ]
    if not a_projection:
        unknown.append(
            {
                "class": "a_boot_sync_scope",
                "token": "THREAD_A projection doc missing",
                "reason": "A-thread projection not present in v3 spec surface",
            }
        )
    else:
        for tok in a_tokens:
            if tok not in a_projection:
                major.append(
                    {
                        "class": "a_projection_sync",
                        "token": tok,
                        "reason": "A-thread token not projected in v3 A-thread projection doc",
                    }
                )

    if critical:
        status = "FAIL"
    elif major:
        status = "WARN"
    else:
        status = "PASS" if not unknown else "WARN"

    unique_noncritical = []
    seen_noncritical = set()
    for row in major + minor:
        key = (row["class"], row["token"], row["reason"])
        if key in seen_noncritical:
            continue
        seen_noncritical.add(key)
        unique_noncritical.append(row)

    report = {
        "sync_status": status,
        "critical_drift": critical,
        "noncritical_drift": unique_noncritical,
        "unknown_sections": unknown,
        "source_hashes": {
            "bootpack_b_sha256": sha256_text(b_boot),
            "bootpack_a_sha256": sha256_text(a_boot),
            "b_owner_spec_sha256": sha256_text(b_spec),
            "a_projection_sha256": sha256_text(a_projection) if a_projection else "MISSING",
        },
        "observed_bootpack_containers": containers,
        "observed_bootpack_tags_count": len(tags),
        "observed_bootpack_stages_count": len(stages),
    }

    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "sync_status": status,
                "critical": len(critical),
                "noncritical": len(unique_noncritical),
                "unknown": len(unknown),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
