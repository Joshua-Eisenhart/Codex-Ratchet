#!/usr/bin/env python3
"""Ingest grok_sim 115-124 tooling-violation handoff as sidequest evidence.

This is not a theory or basin scout. It records the late grok_sim handoff as a
formal-side boundary receipt: useful single-qubit/tooling-block evidence, no
multi-qubit Lindblad, PyTorch tensor-network, PEPS, or PEPS3D promotion.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time
from typing import Any


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_grok_115_124_tooling_violation_handoff_ingest_probe_results.json"

HANDOFF = REPO / "system_v5" / "grok_sim" / "HANDOFF_NESTED_BASIN_ARCHITECTURE_AND_TOOLING_BLOCK_20260520.md"

NAME = "two_root_constraint_grok_115_124_tooling_violation_handoff_ingest_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_grok_115_124_tooling_violation_handoff_ingest"
CLAIM_CEILING = (
    "Formal ingest only: records the grok_sim 115-124 handoff as sidequest "
    "tooling-violation and single-qubit evidence. It cannot promote any "
    "multi-qubit Lindblad, tensor-network, PEPS, PEPS3D, PyTorch-at-scale, "
    "constraint-basin, Clifford, Axis0, engine, physics, or Holodeck claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "supportive durable receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive repo path and handoff loading"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive handoff content hash for provenance"},
    "re": {"tried": True, "used": True, "reason": "supportive section and phrase checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "re": "supportive",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\b.*?(?=^##\s+\d+\.|\Z)", re.M | re.S)
    match = pattern.search(text)
    return match.group(0) if match else ""


def contains_all(text: str, needles: list[str]) -> dict[str, Any]:
    lower = text.lower()
    rows = {needle: (needle.lower() in lower) for needle in needles}
    return {"pass": all(rows.values()), "rows": rows}


def main() -> dict[str, Any]:
    started = time.time()
    text = HANDOFF.read_text(encoding="utf-8", errors="replace") if HANDOFF.exists() else ""
    exec_summary = section(text, "1. Executive summary")
    tooling_blocks = section(text, "2. Tooling blocks encountered")
    findings = section(text, "3. Substantive findings")
    violations = section(text, "4. Methodology violations")
    ingest = section(text, "5. What the formal side should ingest from this turn")
    open_questions = section(text, "6. What grok_sim did NOT test")

    positive = {
        "handoff_exists_and_is_sidequest_only": {
            "pass": HANDOFF.exists() and "claim_ceiling:** side_quest_only" in text,
            "path": rel(HANDOFF),
            "sha256": sha256(HANDOFF),
        },
        "tooling_failures_are_concrete": {
            "pass": all(
                phrase in text
                for phrase in [
                    "local_expectation",
                    "get_function",
                    "SVD shape broadcast",
                    "complex128",
                    "70 GB",
                ]
            ),
            "failure_modes": [
                "quimb MPS observable API mismatch",
                "cotengra get_function AttributeError on hand-built MPOs",
                "SVD shape broadcast at N=64",
                "complex128/MPS device incompatibility",
                "full Liouvillian super-op memory blowup",
            ],
        },
        "surviving_findings_are_single_qubit_or_hamiltonian_only": {
            "pass": "N=1" in text and "NOT Lindblad" in text and "Hamiltonian only" in text,
            "allowed_ingest": [
                "single-qubit 12-dim Liouvillian Lie algebra characterization",
                "single-qubit micro-pseudo-basin locations",
                "small-N Hamiltonian-only spatial reading with no Lindblad promotion",
            ],
        },
        "methodology_violations_are_explicit": {
            "pass": all(
                phrase in text
                for phrase in [
                    "PyTorch was decorative",
                    "PEPS",
                    "PEPS3D",
                    "Multi-qubit Lindblad CPTP: never computed",
                    "Hard tooling lock violation",
                ]
            ),
            "violation_section_present": "## 4. Methodology violations" in text,
        },
        "formal_ingest_boundary_is_explicit": {
            "pass": all(
                phrase in text
                for phrase in [
                    "Ingest as side-quest evidence",
                    "Do NOT ingest as",
                    "Multi-qubit basin formation evidence",
                    "PyTorch + tensor network verification",
                    "PEPS / PEPS3D evidence",
                ]
            ),
            "ingest_section_present": "## 5. What the formal side should ingest" in text,
        },
        "open_questions_are_not_claimed_solved": {
            "pass": all(
                phrase in text
                for phrase in [
                    "Multi-qubit Lindblad CPTP",
                    "PEPS / PEPS3D dynamics",
                    "Vectorized density-matrix MPS",
                    "The bridge",
                    "The cut-state family",
                ]
            ),
            "open_question_section_present": "## 6. What grok_sim did NOT test" in text,
        },
    }

    graveyard_companions = {
        "multi_qubit_lindblad_claim_killed_for_this_handoff": {
            "pass": "Any claim about multi-qubit Lindblad CPTP behavior" in exec_summary
            and "never actually computed" in exec_summary,
            "claim_status": "not_ingestable_as_multi_qubit_lindblad_evidence",
        },
        "peps_peps3d_claim_killed_for_this_handoff": {
            "pass": "Any claim about PEPS / PEPS3D" in exec_summary and "never built" in exec_summary,
            "claim_status": "not_ingestable_as_peps_or_peps3d_evidence",
        },
        "full_pytorch_tensor_network_claim_killed_for_this_handoff": {
            "pass": "NumPy + scipy" in text and "PyTorch + tensor network verification" in ingest,
            "claim_status": "not_ingestable_as_full_pytorch_tensor_network_evidence",
        },
        "tooling_lock_violation_recorded": {
            "pass": "Hard tooling lock violation" in text and "I did basin/manifold/theory exploration anyway" in text,
            "claim_status": "records process violation; does not unlock theory exploration",
        },
    }

    boundary = {
        "sidequest_only": {"pass": True, "value": True},
        "single_qubit_only_for_lindblad_findings": {"pass": "single-qubit only" in text.lower(), "value": True},
        "multi_qubit_lindblad_evidence_allowed": {"pass": True, "value": False},
        "peps_peps3d_evidence_allowed": {"pass": True, "value": False},
        "formal_plan_update_required_before_final_synthesis": {
            "pass": True,
            "value": "final synthesis must mention this handoff as late sidequest/tooling-block evidence",
        },
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "math_object": "grok_sim 115-124 sidequest/tooling-violation handoff boundary",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "Whether to implement the proper post-W1 tensor-network Lindblad scout remains open.",
            "Whether to treat single-qubit pseudo-basins as design hints for W3/W5 remains proposal-only.",
        ],
        "why_not_v4_probes": "This is a v5 formal-scout boundary receipt over a grok_sim handoff, not a v4 proposal or simulation.",
        "summary": {
            "all_pass": all_pass,
            "source_handoff": rel(HANDOFF),
            "claim_ceiling": "sidequest_tooling_violation_ingest_only",
            "multi_qubit_lindblad_evidence_allowed": False,
            "peps_peps3d_evidence_allowed": False,
            "pytorch_tensor_network_scale_evidence_allowed": False,
            "single_qubit_findings_ingest_status": "proposal_or_sidequest_only",
            "formal_next_step": "final synthesis or next W1/W3 design must cite this as tooling-block evidence, not basin evidence",
        },
        "all_pass": all_pass,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": round(time.time() - started, 6),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    receipt = main()
    print(
        json.dumps(
            {
                "all_pass": receipt["all_pass"],
                "source_handoff": receipt["summary"]["source_handoff"],
                "multi_qubit_lindblad_evidence_allowed": receipt["summary"]["multi_qubit_lindblad_evidence_allowed"],
                "peps_peps3d_evidence_allowed": receipt["summary"]["peps_peps3d_evidence_allowed"],
                "out_path": str(OUT_PATH.relative_to(REPO)),
            },
            indent=2,
            sort_keys=True,
        )
    )
