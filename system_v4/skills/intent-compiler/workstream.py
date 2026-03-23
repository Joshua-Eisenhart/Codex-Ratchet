"""
workstream.py — Git-Like Workstream Manager
=============================================
JP: "you don't have sessions or agents, we killed those, you have workstreams.
     you can merge split, cherry pick branch and pull request workstreams just like git.
     i think i will use git as the primary storage for it. its a dna strand..."

A workstream is a unit of work with:
  - A name and description
  - Parent workstream (for branching)
  - Evidence tokens produced
  - Status (active, merged, killed)
  - Git commit refs for each state change

Workstreams are stored as JSON in the repo, tracked by git.
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional


REPO = str(Path(__file__).resolve().parents[3])
WORKSTREAM_DIR = os.path.join(REPO, "system_v4/runtime_state/workstreams")


@dataclass
class Workstream:
    name: str
    description: str
    status: str = "active"  # active, merged, killed, stalled
    parent: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    evidence_tokens: list = field(default_factory=list)
    kills: list = field(default_factory=list)
    git_refs: list = field(default_factory=list)
    children: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now


def _ws_path(name: str) -> str:
    return os.path.join(WORKSTREAM_DIR, f"{name}.json")


def create(name: str, description: str, parent: Optional[str] = None) -> Workstream:
    """Create a new workstream (like git branch)."""
    os.makedirs(WORKSTREAM_DIR, exist_ok=True)
    ws = Workstream(name=name, description=description, parent=parent)

    if parent:
        parent_ws = load(parent)
        if parent_ws:
            parent_ws.children.append(name)
            save(parent_ws)

    save(ws)
    return ws


def load(name: str) -> Optional[Workstream]:
    """Load a workstream by name."""
    path = _ws_path(name)
    if not os.path.exists(path):
        return None
    data = json.loads(Path(path).read_text())
    return Workstream(**data)


def save(ws: Workstream):
    """Save workstream to disk."""
    os.makedirs(WORKSTREAM_DIR, exist_ok=True)
    ws.updated_at = datetime.now(timezone.utc).isoformat()
    Path(_ws_path(ws.name)).write_text(json.dumps(asdict(ws), indent=2))


def add_evidence(name: str, token_id: str, status: str):
    """Add an evidence token to a workstream."""
    ws = load(name)
    if not ws:
        raise ValueError(f"Workstream {name} not found")
    ws.evidence_tokens.append({
        "token_id": token_id,
        "status": status,
        "added_at": datetime.now(timezone.utc).isoformat(),
    })
    if status == "KILL":
        ws.kills.append(token_id)
    save(ws)


def merge(source: str, target: str) -> dict:
    """Merge one workstream into another (like git merge)."""
    src = load(source)
    tgt = load(target)
    if not src or not tgt:
        raise ValueError(f"Source or target not found")

    tgt.evidence_tokens.extend(src.evidence_tokens)
    tgt.kills.extend(src.kills)
    tgt.notes.append(f"Merged from {source} at {datetime.now(timezone.utc).isoformat()}")

    src.status = "merged"
    src.notes.append(f"Merged into {target}")

    save(src)
    save(tgt)

    return {"merged_tokens": len(src.evidence_tokens), "target": target}


def kill(name: str, reason: str):
    """Kill a workstream (send to graveyard)."""
    ws = load(name)
    if not ws:
        raise ValueError(f"Workstream {name} not found")
    ws.status = "killed"
    ws.notes.append(f"KILLED: {reason}")
    save(ws)


def cherry_pick(source: str, target: str, token_ids: list):
    """Cherry-pick specific tokens from one workstream to another."""
    src = load(source)
    tgt = load(target)
    if not src or not tgt:
        raise ValueError(f"Source or target not found")

    picked = [t for t in src.evidence_tokens if t.get("token_id") in token_ids]
    tgt.evidence_tokens.extend(picked)
    tgt.notes.append(f"Cherry-picked {len(picked)} tokens from {source}")
    save(tgt)
    return {"picked": len(picked)}


def list_all() -> list:
    """List all workstreams."""
    os.makedirs(WORKSTREAM_DIR, exist_ok=True)
    result = []
    for f in sorted(Path(WORKSTREAM_DIR).glob("*.json")):
        ws = load(f.stem)
        if ws:
            result.append({
                "name": ws.name,
                "status": ws.status,
                "tokens": len(ws.evidence_tokens),
                "kills": len(ws.kills),
                "parent": ws.parent,
                "children": ws.children,
            })
    return result


def status_report() -> str:
    """Print a git-log-like status of all workstreams."""
    all_ws = list_all()
    lines = ["WORKSTREAM STATUS", "=" * 50]
    for ws in all_ws:
        icon = {"active": "●", "merged": "◉", "killed": "✗", "stalled": "◌"}.get(ws["status"], "?")
        branch = f"← {ws['parent']}" if ws['parent'] else "(root)"
        lines.append(
            f"  {icon} {ws['name']:30s} [{ws['status']:7s}] "
            f"{ws['tokens']} tokens, {ws['kills']} kills {branch}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    # Bootstrap the initial workstreams
    if not load("main"):
        create("main", "Root workstream — the trunk")
    if not load("qit-probes"):
        create("qit-probes", "QIT simulation probe suite", parent="main")
    if not load("igt-game-theory"):
        create("igt-game-theory", "IGT game theory verification", parent="qit-probes")
    if not load("64-stage-engine"):
        create("64-stage-engine", "64-stage Lindblad engine + dual Szilard", parent="qit-probes")
    if not load("jp-autopoiesis"):
        create("jp-autopoiesis", "JP's bootstrap chain: dna.yaml → heartbeat → workstreams", parent="main")
    if not load("nlm-batch2"):
        create("nlm-batch2", "NLM batch 2: holodeck, FEP, moloch, demon", parent="qit-probes")
    if not load("constraint-gaps"):
        create("constraint-gaps", "CAS04, GZ1, net ratchet, R2, E4 gap closure", parent="qit-probes")

    # Add evidence to workstreams
    report_path = os.path.join(REPO, "system_v4/probes/a2_state/sim_results/unified_evidence_report.json")
    if os.path.exists(report_path):
        report = json.loads(Path(report_path).read_text())
        tokens = report.get("all_tokens", [])

        for token in tokens:
            tid = token.get("token_id", "")
            status = token.get("status", "")
            sim = token.get("sim_spec_id", "")

            # Route to correct workstream
            if "IGT" in sim or "GAME" in sim or "NASH" in sim:
                add_evidence("igt-game-theory", tid, status)
            elif "64STAGE" in sim or "SZILARD" in sim:
                add_evidence("64-stage-engine", tid, status)
            elif "HOLODECK" in sim or "FEP" in sim or "MOLOCH" in sim or "DEMON" in sim:
                add_evidence("nlm-batch2", tid, status)
            elif "CAS04" in sim or "GZ1" in sim or "RATCHET" in sim or "R2" in sim or "E4" in sim:
                add_evidence("constraint-gaps", tid, status)
            else:
                add_evidence("qit-probes", tid, status)

    print(status_report())
