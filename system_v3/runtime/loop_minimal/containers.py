import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import re
from dataclasses import dataclass
from typing import List


_BEGIN_RE = re.compile(r"^BEGIN EXPORT_BLOCK (v\d+)")
_END_RE = re.compile(r"^END EXPORT_BLOCK (v\d+)")


@dataclass
class ExportBlock:
    version: str
    export_id: str
    target: str
    proposal_type: str
    ruleset_sha256: str | None
    content_lines: List[str]


def parse_export_block(text: str) -> ExportBlock:
    lines = text.splitlines()
    if not lines:
        raise ValueError("empty export block")
    m = _BEGIN_RE.match(lines[0].strip())
    if not m:
        raise ValueError("missing BEGIN EXPORT_BLOCK")
    version = m.group(1)
    export_id = ""
    target = ""
    proposal_type = ""
    ruleset_sha256 = None
    content_idx = None
    for i, line in enumerate(lines[1:], start=1):
        s = line.strip()
        if s.startswith("EXPORT_ID:"):
            export_id = s.split(":", 1)[1].strip()
        elif s.startswith("TARGET:"):
            target = s.split(":", 1)[1].strip()
        elif s.startswith("PROPOSAL_TYPE:"):
            proposal_type = s.split(":", 1)[1].strip()
        elif s.startswith("RULESET_SHA256:"):
            ruleset_sha256 = s.split(":", 1)[1].strip()
        elif s == "CONTENT:":
            content_idx = i + 1
            break
    if content_idx is None:
        raise ValueError("missing CONTENT")
    end_idx = None
    for j in range(len(lines) - 1, -1, -1):
        if _END_RE.match(lines[j].strip()):
            end_idx = j
            break
    if end_idx is None or end_idx < content_idx:
        raise ValueError("missing END EXPORT_BLOCK")
    if _END_RE.match(lines[end_idx].strip()).group(1) != version:
        raise ValueError("version mismatch")
    content_lines = []
    for line in lines[content_idx:end_idx]:
        if line.startswith("  "):
            content_lines.append(line[2:])
        else:
            content_lines.append(line)
    return ExportBlock(version, export_id, target, proposal_type, ruleset_sha256, content_lines)


def build_export_block(export_id: str, proposal_type: str, content_lines: List[str], version: str = "v1") -> str:
    out = []
    out.append(f"BEGIN EXPORT_BLOCK {version}")
    out.append(f"EXPORT_ID: {export_id}")
    out.append("TARGET: THREAD_B_ENFORCEMENT_KERNEL")
    out.append(f"PROPOSAL_TYPE: {proposal_type}")
    out.append("CONTENT:")
    for line in content_lines:
        out.append("  " + line)
    out.append(f"END EXPORT_BLOCK {version}")
    return "\n".join(out) + "\n"


def split_items(content_lines: List[str]) -> List[dict]:
    items = []
    current = None
    for raw in content_lines:
        line = raw.strip()
        if line.startswith("PROBE_HYP ") or line.startswith("SPEC_HYP "):
            if current:
                items.append(current)
            parts = line.split()
            current = {
                "header": parts[0],
                "id": parts[1] if len(parts) > 1 else "",
                "lines": [line],
            }
        else:
            if current is None:
                continue
            current["lines"].append(line)
    if current:
        items.append(current)
    return items
