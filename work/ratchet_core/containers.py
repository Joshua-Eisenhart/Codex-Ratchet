import re


class ExportBlock:
    def __init__(self, version, export_id, target, proposal_type, ruleset_sha256, megaboot_sha256, content_lines):
        self.version = version
        self.export_id = export_id
        self.target = target
        self.proposal_type = proposal_type
        self.ruleset_sha256 = ruleset_sha256
        self.megaboot_sha256 = megaboot_sha256
        self.content_lines = list(content_lines)


_BEGIN_RE = re.compile(r"^BEGIN EXPORT_BLOCK (v\d+)")
_END_RE = re.compile(r"^END EXPORT_BLOCK (v\d+)")


def parse_export_block(text):
    lines = text.splitlines()
    if not lines:
        raise ValueError("empty export block")
    m = _BEGIN_RE.match(lines[0].strip())
    if not m:
        raise ValueError("missing BEGIN EXPORT_BLOCK")
    version = m.group(1)
    export_id = None
    target = None
    proposal_type = None
    ruleset_sha256 = None
    megaboot_sha256 = None
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
        elif s.startswith("MEGABOOT_SHA256:"):
            megaboot_sha256 = s.split(":", 1)[1].strip()
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
    content_lines = []
    for line in lines[content_idx:end_idx]:
        if line.startswith("  "):
            content_lines.append(line[2:])
        else:
            content_lines.append(line)
    return ExportBlock(version, export_id, target, proposal_type, ruleset_sha256, megaboot_sha256, content_lines)


def build_export_block(export_id, proposal_type, content_lines, version="v1", ruleset_sha256=None, megaboot_sha256=None):
    lines = []
    lines.append(f"BEGIN EXPORT_BLOCK {version}")
    lines.append(f"EXPORT_ID: {export_id}")
    lines.append("TARGET: THREAD_B_ENFORCEMENT_KERNEL")
    lines.append(f"PROPOSAL_TYPE: {proposal_type}")
    if ruleset_sha256:
        lines.append(f"RULESET_SHA256: {ruleset_sha256}")
    if megaboot_sha256:
        lines.append(f"MEGABOOT_SHA256: {megaboot_sha256}")
    lines.append("CONTENT:")
    for line in content_lines:
        lines.append("  " + line)
    lines.append(f"END EXPORT_BLOCK {version}")
    return "\n".join(lines) + "\n"


def split_items(content_lines):
    items = []
    current = None
    for line in content_lines:
        s = line.strip()
        if s.startswith("AXIOM_HYP ") or s.startswith("SPEC_HYP ") or s.startswith("PROBE_HYP "):
            if current:
                items.append(current)
            parts = s.split()
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
