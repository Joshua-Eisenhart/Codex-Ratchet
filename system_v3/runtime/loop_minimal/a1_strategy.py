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


_BEGIN_RE = re.compile(r"^BEGIN A1_STRATEGY v(\d+)$")
_END_RE = re.compile(r"^END A1_STRATEGY v(\d+)$")


@dataclass
class A1Strategy:
    version: str
    goal: str
    candidate_families: List[str]
    required_terms: List[str]
    probes: List[dict]
    sim_specs: List[dict]


def parse_strategy(text: str) -> A1Strategy:
    lines = [l.rstrip("\n") for l in text.splitlines()]
    if not lines or not _BEGIN_RE.match(lines[0].strip()):
        raise ValueError("missing BEGIN A1_STRATEGY")
    if not _END_RE.match(lines[-1].strip()):
        raise ValueError("missing END A1_STRATEGY")
    version = "v" + _BEGIN_RE.match(lines[0].strip()).group(1)

    goal = ""
    candidate_families: List[str] = []
    required_terms: List[str] = []
    probes: List[dict] = []
    sim_specs: List[dict] = []

    section = None
    for line in lines[1:-1]:
        s = line.strip()
        if not s:
            continue
        if s.startswith("GOAL:"):
            goal = s.split(":", 1)[1].strip()
            continue
        if s.startswith("CANDIDATE_FAMILIES:"):
            raw = s.split(":", 1)[1]
            candidate_families = [x.strip() for x in raw.split(",") if x.strip()]
            continue
        if s.startswith("REQUIRED_TERMS:"):
            raw = s.split(":", 1)[1]
            required_terms = [x.strip() for x in raw.split(",") if x.strip()]
            continue
        if s.startswith("PROBES:"):
            section = "PROBES"
            continue
        if s.startswith("SIM_SPECS:"):
            section = "SIM_SPECS"
            continue

        if section == "PROBES" and s.startswith("-"):
            parts = [p.strip() for p in s.lstrip("-").split("|")]
            if len(parts) != 3:
                continue
            probes.append({"probe_id": parts[0], "probe_kind": parts[1], "probe_token": parts[2]})
        elif section == "SIM_SPECS" and s.startswith("-"):
            parts = [p.strip() for p in s.lstrip("-").split("|")]
            if len(parts) != 3:
                continue
            sim_specs.append({"spec_id": parts[0], "requires_probe": parts[1], "evidence_token": parts[2]})

    return A1Strategy(version, goal, candidate_families, required_terms, probes, sim_specs)


def build_default_strategy() -> str:
    return "\n".join([
        "BEGIN A1_STRATEGY v1",
        "GOAL: bind MS_A to FULL16X4 engine sim evidence",
        "CANDIDATE_FAMILIES: SIM_SPEC_BIND",
        "REQUIRED_TERMS: ",
        "PROBES:",
        "  - P94_FULL16X4_ENGINE_PROBE | FULL16X4_ENGINE | PT_P94_FULL16X4_ENGINE",
        "SIM_SPECS:",
        "  - S_BIND_MS_A_FULL16X4 | P94_FULL16X4_ENGINE_PROBE | E_MS_A_FULL16X4",
        "END A1_STRATEGY v1",
        "",
    ])
