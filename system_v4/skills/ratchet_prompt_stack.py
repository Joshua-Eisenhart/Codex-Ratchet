"""
Ratchet Prompt Stack — adapted from JP's Leviathan prompt-stack plugin.

Core loop: init → next → record → validate
Each step reveals ONE prompt, validates report against contract, produces
deterministic receipt with SHA256 digest.

Pattern for graph convergence:
  stack = RatchetPromptStack(project_root)
  session = stack.init_session("graph-claim-extraction")
  while (step := stack.next_step(session)):
      report = do_work(step)  # LLM call, extraction, etc.
      stack.record_step(session, step, report)
  manifest = stack.validate_session(session)

Adapted from: lev-os/leviathan/plugins/prompt-stack/src/runtime.ts (1372L)
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class StepDefinition:
    """One step in a prompt stack."""
    id: str
    title: str
    prompt: str
    intent: str = ""
    report_schema: dict = field(default_factory=lambda: {
        "frontmatter_required": ["session_id", "stack_id", "step_id", "status"],
        "sections_required": ["Summary", "Evidence", "Outcome", "Next"],
    })


@dataclass
class StackDefinition:
    """Named prompt stack = ordered sequence of steps."""
    id: str
    title: str
    purpose: str
    steps: list[StepDefinition]
    max_iterations: int = 20  # circuit breaker


@dataclass
class StepReceipt:
    """Deterministic receipt for a completed step."""
    step_id: str
    step_title: str
    prompt_digest: str
    report_path: str
    report_digest: str
    contract_digest: str
    recorded_at: str
    sections_found: list[str]
    input_keys: list[str]
    output_keys: list[str]


@dataclass
class StackSession:
    """Session state — persisted to disk after each step."""
    session_id: str
    stack_id: str
    stack_title: str
    project_dir: str
    status: str  # active | completed | blocked
    created_at: str
    updated_at: str
    active_step_index: int
    active_step_id: str | None
    completed_step_ids: list[str]
    report_receipts: list[StepReceipt]
    validation_status: str  # unknown | pass | fail
    manifest_path: str | None = None


# ---------------------------------------------------------------------------
# Catalog — built-in stacks for Ratchet
# ---------------------------------------------------------------------------

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ")


# Graph claim extraction stack
GRAPH_CLAIM_EXTRACTION = StackDefinition(
    id="graph-claim-extraction",
    title="Graph Claim Extraction Loop",
    purpose="Read every claim in a document and add to the graph until graph and doc are 1:1",
    steps=[
        StepDefinition(
            id="scan-claims",
            title="Scan Document Claims",
            prompt=(
                "Read the source document. Extract every distinct claim, definition, "
                "constraint, or relationship. Output as a numbered list.\n"
                "Each claim must be:\n"
                "  - Atomic (one idea per claim)\n"
                "  - Verifiable (can be checked against code/docs)\n"
                "  - Tagged with type: DEFINITION | CONSTRAINT | RELATIONSHIP | ASSERTION | PATTERN\n"
                "\nDo NOT summarize. Extract exhaustively."
            ),
        ),
        StepDefinition(
            id="match-existing",
            title="Match Claims to Existing Graph Nodes",
            prompt=(
                "For each extracted claim, check if it already exists as a concept "
                "in the A2 graph. Report:\n"
                "  - MATCHED: claim maps to existing node (give node ID)\n"
                "  - PARTIAL: claim overlaps but isn't fully captured\n"
                "  - MISSING: claim has no representation in graph\n"
                "  - CONTRADICTS: claim conflicts with an existing node\n"
                "\nOutput the match matrix."
            ),
        ),
        StepDefinition(
            id="ingest-missing",
            title="Ingest Missing Claims",
            prompt=(
                "For each MISSING and PARTIAL claim:\n"
                "  1. Create a new concept node with proper tags and description\n"
                "  2. Link to source document with SOURCE_MAP edge\n"
                "  3. Link to related existing concepts with RELATED_TO or DEPENDS_ON\n"
                "  4. For CONTRADICTS: add CONTRADICTS edge with evidence\n"
                "\nReport: nodes created, edges created, contradictions found."
            ),
        ),
        StepDefinition(
            id="verify-coverage",
            title="Verify 1:1 Coverage",
            prompt=(
                "Compare the source document's claims against the graph state.\n"
                "Report coverage ratio: (matched + ingested) / total_claims.\n"
                "If coverage < 0.95, list the uncovered claims.\n"
                "If coverage >= 0.95, mark as CONVERGED.\n"
                "\nThis is the convergence check."
            ),
        ),
    ],
)

# Promoted graph enrichment stack
PROMOTED_ENRICHMENT = StackDefinition(
    id="promoted-enrichment",
    title="Promoted Layer Enrichment",
    purpose="Enrich the promoted subgraph with structural relationships between kernel/refined concepts",
    steps=[
        StepDefinition(
            id="read-descriptions",
            title="Read All Promoted Concept Descriptions",
            prompt=(
                "Load all concepts in the promoted subgraph (kernel + refined).\n"
                "For each concept, read its full description and tags.\n"
                "Output a manifest: concept_id, name, description_digest, tags."
            ),
        ),
        StepDefinition(
            id="identify-relationships",
            title="Identify Structural Relationships",
            prompt=(
                "For each pair of promoted concepts, determine if a structural "
                "relationship exists:\n"
                "  - DEPENDS_ON: concept A requires concept B to function\n"
                "  - CONSTRAINS: concept A limits or gates concept B\n"
                "  - IMPLEMENTS: concept A is a concrete instance of concept B\n"
                "  - CONTRADICTS: concepts are mutually exclusive\n"
                "  - EXCLUDES: anti-edge, concepts should NOT be clustered\n"
                "\nJustify each relationship with evidence from descriptions."
            ),
        ),
        StepDefinition(
            id="apply-edges",
            title="Apply Edges to Promoted Subgraph",
            prompt=(
                "Create the identified edges in the promoted subgraph.\n"
                "Report: edges added, edge types, any rejected (duplicate/invalid).\n"
                "Re-calculate density and clustering coefficient."
            ),
        ),
    ],
)

# Entropy audit stack
ENTROPY_AUDIT = StackDefinition(
    id="entropy-audit",
    title="Source Document Entropy Audit",
    purpose="Score each source document by entropy and flag high-entropy docs that were ingested too early",
    steps=[
        StepDefinition(
            id="score-entropy",
            title="Score Document Entropy",
            prompt=(
                "For each SOURCE_DOCUMENT node in the A2 graph:\n"
                "  1. Read the source file (if accessible)\n"
                "  2. Score entropy 1-5:\n"
                "     1 = formal spec/schema (lowest)\n"
                "     2 = structured doc with clear definitions\n"
                "     3 = mixed: some structure + some prose\n"
                "     4 = chat log / informal notes\n"
                "     5 = raw braindump / stream of consciousness (highest)\n"
                "  3. Tag the node with entropy_score\n"
                "\nReport distribution: how many docs at each entropy level."
            ),
        ),
        StepDefinition(
            id="quarantine-premature",
            title="Quarantine Prematurely Ingested High-Entropy Docs",
            prompt=(
                "For docs with entropy_score >= 4 that were ingested before "
                "lower-entropy docs were fully processed:\n"
                "  1. Move their extracted concepts to QUARANTINE trust zone\n"
                "  2. Remove crosslink edges from quarantined concepts\n"
                "  3. Keep SOURCE_MAP edges (provenance)\n"
                "\nReport: docs quarantined, concepts affected, edges removed."
            ),
        ),
    ],
)


# Stack catalog
RATCHET_CATALOG: dict[str, StackDefinition] = {
    s.id: s for s in [GRAPH_CLAIM_EXTRACTION, PROMOTED_ENRICHMENT, ENTROPY_AUDIT]
}


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------

class RatchetPromptStack:
    """Prompt stack runtime for Ratchet — Python port of Lev's TypeScript runtime."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.sessions_dir = self.project_root / "system_v4" / "a2_state" / "stack_sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def list_stacks(self) -> list[dict[str, str]]:
        """List available stacks."""
        return [
            {"id": s.id, "title": s.title, "purpose": s.purpose, "steps": len(s.steps)}
            for s in RATCHET_CATALOG.values()
        ]

    def show_stack(self, stack_id: str) -> StackDefinition:
        """Show stack metadata without revealing step prompts."""
        if stack_id not in RATCHET_CATALOG:
            raise ValueError(f"Unknown stack: {stack_id}. Available: {list(RATCHET_CATALOG)}")
        return RATCHET_CATALOG[stack_id]

    def init_session(
        self,
        stack_id: str,
        context: dict[str, Any] | None = None,
    ) -> StackSession:
        """Initialize a new session for a stack."""
        stack = self.show_stack(stack_id)
        session_id = f"{stack_id}-{uuid.uuid4().hex[:8]}"

        session = StackSession(
            session_id=session_id,
            stack_id=stack_id,
            stack_title=stack.title,
            project_dir=str(self.project_root),
            status="active",
            created_at=_timestamp(),
            updated_at=_timestamp(),
            active_step_index=0,
            active_step_id=stack.steps[0].id if stack.steps else None,
            completed_step_ids=[],
            report_receipts=[],
            validation_status="unknown",
        )

        self._save_session(session)
        return session

    def next_step(self, session: StackSession) -> StepDefinition | None:
        """Reveal ONLY the active step prompt. Returns None when done."""
        if session.status != "active":
            return None

        stack = RATCHET_CATALOG[session.stack_id]
        if session.active_step_index >= len(stack.steps):
            return None

        return stack.steps[session.active_step_index]

    def record_step(
        self,
        session: StackSession,
        step: StepDefinition,
        report_content: str,
        report_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepReceipt:
        """Validate report, create receipt, advance session."""
        # Validate report against schema
        errors = self._validate_report(report_content, step.report_schema)
        if errors:
            raise ValueError(f"Report validation failed: {errors}")

        # Parse report
        sections = self._extract_sections(report_content)
        fm = self._extract_frontmatter(report_content)

        # Save report file
        if not report_path:
            reports_dir = self.sessions_dir / session.session_id / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            report_path = str(reports_dir / f"{step.id}.md")
            Path(report_path).write_text(report_content)

        # Build receipt
        receipt = StepReceipt(
            step_id=step.id,
            step_title=step.title,
            prompt_digest=_sha256(step.prompt),
            report_path=report_path,
            report_digest=_sha256(report_content),
            contract_digest=_sha256(json.dumps(step.report_schema, sort_keys=True)),
            recorded_at=_timestamp(),
            sections_found=sections,
            input_keys=sorted(fm.get("inputs", {}).keys()) if isinstance(fm.get("inputs"), dict) else [],
            output_keys=sorted(fm.get("outputs", {}).keys()) if isinstance(fm.get("outputs"), dict) else [],
        )

        # Advance session
        session.completed_step_ids.append(step.id)
        session.report_receipts.append(receipt)
        session.active_step_index += 1

        stack = RATCHET_CATALOG[session.stack_id]
        if session.active_step_index >= len(stack.steps):
            session.active_step_id = None
            session.status = "completed"
        else:
            session.active_step_id = stack.steps[session.active_step_index].id

        session.updated_at = _timestamp()
        self._save_session(session)

        return receipt

    def validate_session(self, session: StackSession) -> dict[str, Any]:
        """Validate completed session and emit manifest."""
        checks = []
        stack = RATCHET_CATALOG[session.stack_id]

        # Check all steps completed
        all_done = len(session.completed_step_ids) == len(stack.steps)
        checks.append({
            "id": "all_steps_completed",
            "ok": all_done,
            "detail": f"{len(session.completed_step_ids)}/{len(stack.steps)} steps done",
        })

        # Check all receipts have digests
        all_digested = all(r.report_digest for r in session.report_receipts)
        checks.append({
            "id": "all_receipts_valid",
            "ok": all_digested,
            "detail": f"{len(session.report_receipts)} receipts with valid digests",
        })

        ok = all(c["ok"] for c in checks)
        session.validation_status = "pass" if ok else "fail"

        manifest = {
            "session_id": session.session_id,
            "stack_id": session.stack_id,
            "status": session.validation_status,
            "completed_steps": session.completed_step_ids,
            "receipt_count": len(session.report_receipts),
            "created_at": session.created_at,
            "completed_at": _timestamp(),
            "checks": checks,
        }

        # Save manifest
        manifest_path = self.sessions_dir / session.session_id / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2))
        session.manifest_path = str(manifest_path)

        self._save_session(session)
        return manifest

    def status(self, session: StackSession) -> dict[str, Any]:
        """Get session status."""
        stack = RATCHET_CATALOG[session.stack_id]
        return {
            "session_id": session.session_id,
            "stack": session.stack_id,
            "status": session.status,
            "progress": f"{len(session.completed_step_ids)}/{len(stack.steps)}",
            "active_step": session.active_step_id,
            "completed": session.completed_step_ids,
            "receipts": len(session.report_receipts),
        }

    # -- Helpers --

    def _save_session(self, session: StackSession) -> None:
        session_dir = self.sessions_dir / session.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        session_file = session_dir / "session.json"
        data = {
            "session_id": session.session_id,
            "stack_id": session.stack_id,
            "stack_title": session.stack_title,
            "project_dir": session.project_dir,
            "status": session.status,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "active_step_index": session.active_step_index,
            "active_step_id": session.active_step_id,
            "completed_step_ids": session.completed_step_ids,
            "report_receipts": [
                {
                    "step_id": r.step_id,
                    "step_title": r.step_title,
                    "prompt_digest": r.prompt_digest,
                    "report_path": r.report_path,
                    "report_digest": r.report_digest,
                    "contract_digest": r.contract_digest,
                    "recorded_at": r.recorded_at,
                    "sections_found": r.sections_found,
                    "input_keys": r.input_keys,
                    "output_keys": r.output_keys,
                }
                for r in session.report_receipts
            ],
            "validation_status": session.validation_status,
            "manifest_path": session.manifest_path,
        }
        session_file.write_text(json.dumps(data, indent=2))

    def _validate_report(self, content: str, schema: dict) -> list[str]:
        errors = []
        sections = self._extract_sections(content)
        for req in schema.get("sections_required", []):
            if req not in sections:
                errors.append(f'Missing required section: "{req}"')
        return errors

    def _extract_sections(self, content: str) -> list[str]:
        import re
        return [m.group(1).strip() for m in re.finditer(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)]

    def _extract_frontmatter(self, content: str) -> dict:
        import re
        match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if not match:
            return {}
        try:
            import yaml  # noqa: F811
            return yaml.safe_load(match.group(1)) or {}
        except Exception:
            return {}


# ---------------------------------------------------------------------------
# CLI (for agent/daemon use)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    stack = RatchetPromptStack(".")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "list":
        for s in stack.list_stacks():
            print(f"  {s['id']:40s}  {s['steps']} steps  {s['purpose'][:60]}")
    elif cmd == "help":
        print("Usage: python ratchet_prompt_stack.py <command>")
        print("Commands: list, show <id>, init <id>, status <session-id>")
        print("\nLoop pattern (for agents):")
        print("  init → while (next returns a step) { do work → record } → validate")
    else:
        print(f"Unknown command: {cmd}")
