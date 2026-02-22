import re
from dataclasses import dataclass


_BEGIN_EXPORT_RE = re.compile(r"^BEGIN EXPORT_BLOCK (v\d+)$")
_END_EXPORT_RE = re.compile(r"^END EXPORT_BLOCK (v\d+)$")
_BEGIN_SIM_RE = re.compile(r"^BEGIN SIM_EVIDENCE v1$")
_END_SIM_RE = re.compile(r"^END SIM_EVIDENCE v1$")


@dataclass
class ExportBlock:
    version: str
    export_id: str
    target: str
    proposal_type: str
    ruleset_sha256: str
    megaboot_sha256: str
    content_lines: list[str]


@dataclass
class SimEvidence:
    sim_id: str
    code_hash_sha256: str
    input_hash_sha256: str
    output_hash_sha256: str
    run_manifest_sha256: str
    metrics: dict[str, str]
    evidence_signals: list[tuple[str, str]]
    kill_signals: list[tuple[str, str]]


def build_export_block(
    export_id: str,
    proposal_type: str,
    content_lines: list[str],
    version: str = "v1",
    ruleset_sha256: str = "",
    megaboot_sha256: str = "",
) -> str:
    lines = [
        f"BEGIN EXPORT_BLOCK {version}",
        f"EXPORT_ID: {export_id}",
        "TARGET: THREAD_B_ENFORCEMENT_KERNEL",
        f"PROPOSAL_TYPE: {proposal_type}",
    ]
    if ruleset_sha256:
        lines.append(f"RULESET_SHA256: {ruleset_sha256}")
    if megaboot_sha256:
        lines.append(f"MEGABOOT_SHA256: {megaboot_sha256}")
    lines.append("CONTENT:")
    lines.extend([f"  {line}" for line in content_lines])
    lines.append(f"END EXPORT_BLOCK {version}")
    return "\n".join(lines) + "\n"


def parse_export_block(text: str) -> ExportBlock:
    lines = [line.rstrip("\n") for line in text.splitlines()]
    if not lines:
        raise ValueError("empty container")
    begin = _BEGIN_EXPORT_RE.match(lines[0].strip())
    if begin is None:
        raise ValueError("missing BEGIN EXPORT_BLOCK")
    version = begin.group(1)
    export_id = ""
    target = ""
    proposal_type = ""
    ruleset_sha256 = ""
    megaboot_sha256 = ""
    content_start = -1
    for index, raw in enumerate(lines[1:], start=1):
        line = raw.strip()
        if line == "CONTENT:":
            content_start = index + 1
            break
        if line.startswith("EXPORT_ID:"):
            export_id = line.split(":", 1)[1].strip()
        elif line.startswith("TARGET:"):
            target = line.split(":", 1)[1].strip()
        elif line.startswith("PROPOSAL_TYPE:"):
            proposal_type = line.split(":", 1)[1].strip()
        elif line.startswith("RULESET_SHA256:"):
            ruleset_sha256 = line.split(":", 1)[1].strip()
        elif line.startswith("MEGABOOT_SHA256:"):
            megaboot_sha256 = line.split(":", 1)[1].strip()
    if content_start < 0:
        raise ValueError("missing CONTENT section")
    end_index = -1
    for index in range(len(lines) - 1, -1, -1):
        end = _END_EXPORT_RE.match(lines[index].strip())
        if end is not None:
            if end.group(1) != version:
                raise ValueError("mismatched export version")
            end_index = index
            break
    if end_index < content_start:
        raise ValueError("missing END EXPORT_BLOCK")
    content_lines = []
    for raw in lines[content_start:end_index]:
        if raw.startswith("  "):
            content_lines.append(raw[2:])
        else:
            content_lines.append(raw)
    if not export_id or not target or not proposal_type:
        raise ValueError("missing required export headers")
    return ExportBlock(
        version=version,
        export_id=export_id,
        target=target,
        proposal_type=proposal_type,
        ruleset_sha256=ruleset_sha256,
        megaboot_sha256=megaboot_sha256,
        content_lines=content_lines,
    )


def split_items(content_lines: list[str]) -> list[dict]:
    items: list[dict] = []
    current = None
    for raw in content_lines:
        line = raw.strip()
        if line.startswith("AXIOM_HYP ") or line.startswith("PROBE_HYP ") or line.startswith("SPEC_HYP "):
            if current is not None:
                items.append(current)
            parts = line.split()
            current = {"header": parts[0], "id": parts[1] if len(parts) > 1 else "", "lines": [line]}
            continue
        if current is not None:
            current["lines"].append(line)
    if current is not None:
        items.append(current)
    return items


def parse_sim_evidence_pack(text: str) -> list[SimEvidence]:
    lines = [line.rstrip("\n") for line in text.splitlines()]
    index = 0
    blocks: list[SimEvidence] = []
    seen_sim_ids: set[str] = set()
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue
        if _BEGIN_SIM_RE.match(lines[index].strip()) is None:
            raise ValueError("invalid SIM_EVIDENCE pack")
        index += 1
        sim_id = ""
        code_hash = ""
        input_hash = ""
        output_hash = ""
        manifest_hash = ""
        required_seen = {
            "SIM_ID": 0,
            "CODE_HASH_SHA256": 0,
            "INPUT_HASH_SHA256": 0,
            "OUTPUT_HASH_SHA256": 0,
            "RUN_MANIFEST_SHA256": 0,
        }
        metrics: dict[str, str] = {}
        evidence_signals: list[tuple[str, str]] = []
        kill_signals: list[tuple[str, str]] = []
        while index < len(lines):
            line = lines[index].strip()
            if _END_SIM_RE.match(line):
                index += 1
                break
            if line.startswith("#") or line.startswith("//"):
                raise ValueError("comment not permitted in SIM_EVIDENCE")
            if line.startswith("SIM_ID:"):
                required_seen["SIM_ID"] += 1
                sim_id = line.split(":", 1)[1].strip()
            elif line.startswith("CODE_HASH_SHA256:"):
                required_seen["CODE_HASH_SHA256"] += 1
                code_hash = line.split(":", 1)[1].strip()
            elif line.startswith("INPUT_HASH_SHA256:"):
                required_seen["INPUT_HASH_SHA256"] += 1
                input_hash = line.split(":", 1)[1].strip()
            elif line.startswith("OUTPUT_HASH_SHA256:"):
                required_seen["OUTPUT_HASH_SHA256"] += 1
                output_hash = line.split(":", 1)[1].strip()
            elif line.startswith("RUN_MANIFEST_SHA256:"):
                required_seen["RUN_MANIFEST_SHA256"] += 1
                manifest_hash = line.split(":", 1)[1].strip()
            elif line.startswith("METRIC:"):
                metric_value = line.split(":", 1)[1].strip()
                if "=" in metric_value:
                    key, value = metric_value.split("=", 1)
                    metrics[key.strip()] = value.strip()
                else:
                    raise ValueError("invalid METRIC line")
            elif line.startswith("EVIDENCE_SIGNAL "):
                parts = line.split()
                if len(parts) == 4 and parts[2] == "CORR":
                    evidence_signals.append((parts[1], parts[3]))
                else:
                    raise ValueError("invalid EVIDENCE_SIGNAL line")
            elif line.startswith("KILL_SIGNAL "):
                parts = line.split()
                if len(parts) == 4 and parts[2] == "CORR":
                    kill_signals.append((parts[1], parts[3]))
                else:
                    raise ValueError("invalid KILL_SIGNAL line")
            else:
                raise ValueError("unrecognized line in SIM_EVIDENCE")
            index += 1
        # Unified required fields (canonical harness contract).
        if not sim_id or not code_hash or not input_hash or not output_hash or not manifest_hash:
            raise ValueError("SIM_EVIDENCE missing required fields")
        for field_name, seen_count in required_seen.items():
            if seen_count != 1:
                raise ValueError(f"SIM_EVIDENCE required field cardinality violation:{field_name}")
        if sim_id in seen_sim_ids:
            raise ValueError("duplicate SIM_ID in SIM_EVIDENCE pack")
        seen_sim_ids.add(sim_id)
        for sig_id, _ in evidence_signals:
            if sig_id != sim_id:
                raise ValueError("EVIDENCE_SIGNAL SIM_ID mismatch")
        blocks.append(
            SimEvidence(
                sim_id=sim_id,
                code_hash_sha256=code_hash,
                input_hash_sha256=input_hash,
                output_hash_sha256=output_hash,
                run_manifest_sha256=manifest_hash,
                metrics=metrics,
                evidence_signals=evidence_signals,
                kill_signals=kill_signals,
            )
        )
    return blocks
