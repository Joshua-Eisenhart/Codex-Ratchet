"""
witness_recorder.py

Append-only witness trace recorder + replay.  Works with the runtime
kernel types from runtime_state_kernel.py.

Design doc: §Event Spine — Lev's append-only event spine records
witnesses, positive/negative evidence, counterexamples, replayable
step history.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from system_v4.skills.runtime_state_kernel import (
    Witness, WitnessKind, StepEvent, RuntimeState, BoundaryTag, utc_iso,
)


class WitnessRecorder:
    """Append-only witness recorder backed by a JSON file."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._corpus: list[dict[str, Any]] = []
        if self.path.exists():
            self._corpus = json.loads(self.path.read_text())

    # ── Record ───────────────────────────────────────────────────

    def record(self, witness: Witness, tags: dict[str, str] | None = None) -> int:
        """Append a witness.  Returns the corpus index."""
        entry = {
            "recorded_at": utc_iso(),
            "witness": asdict(witness),
        }
        if tags:
            entry["tags"] = tags
        self._corpus.append(entry)
        return len(self._corpus) - 1

    def record_positive(self, trace: list[StepEvent],
                        touched: list[BoundaryTag] | None = None,
                        tags: dict[str, str] | None = None) -> int:
        return self.record(
            Witness(kind=WitnessKind.POSITIVE, passed=True,
                    touched_boundaries=touched or [], trace=trace),
            tags=tags,
        )

    def record_negative(self, violations: list[str],
                        trace: list[StepEvent],
                        touched: list[BoundaryTag] | None = None,
                        tags: dict[str, str] | None = None) -> int:
        return self.record(
            Witness(kind=WitnessKind.NEGATIVE, passed=False,
                    violations=violations,
                    touched_boundaries=touched or [], trace=trace),
            tags=tags,
        )

    def record_counterexample(self, violations: list[str],
                              trace: list[StepEvent],
                              touched: list[BoundaryTag] | None = None,
                              tags: dict[str, str] | None = None) -> int:
        return self.record(
            Witness(kind=WitnessKind.COUNTEREXAMPLE, passed=False,
                    violations=violations,
                    touched_boundaries=touched or [], trace=trace),
            tags=tags,
        )

    def record_intent(self, intent_text: str,
                      source: str = "maker",
                      trace: list[StepEvent] | None = None,
                      tags: dict[str, str] | None = None) -> int:
        """Record a maker or system intent as a first-class witness.

        Intent is the highest-priority content for A2/A1 refinement.
        It captures goals, design decisions, constraints, and priorities.
        """
        merged_tags = {"source": source, "intent": intent_text[:200]}
        if tags:
            merged_tags.update(tags)
        return self.record(
            Witness(kind=WitnessKind.INTENT, passed=True,
                    violations=[],
                    touched_boundaries=[],
                    trace=trace or [StepEvent(
                        at=utc_iso(), op=f"intent:{source}",
                        before_hash="", after_hash="",
                        notes=[intent_text],
                    )]),
            tags=merged_tags,
        )

    def record_context(self, context_text: str,
                       source: str = "system",
                       trace: list[StepEvent] | None = None,
                       tags: dict[str, str] | None = None) -> int:
        """Record persistent context to prevent information loss across sessions."""
        merged_tags = {"source": source, "context": context_text[:200]}
        if tags:
            merged_tags.update(tags)
        return self.record(
            Witness(kind=WitnessKind.CONTEXT, passed=True,
                    violations=[],
                    touched_boundaries=[],
                    trace=trace or [StepEvent(
                        at=utc_iso(), op=f"context:{source}",
                        before_hash="", after_hash="",
                        notes=[context_text],
                    )]),
            tags=merged_tags,
        )

    # ── Flush ────────────────────────────────────────────────────

    def flush(self) -> int:
        """Persist to disk.  Returns count."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._corpus, indent=2, default=str))
        return len(self._corpus)

    # ── Query ────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._corpus)

    def positives(self) -> list[dict]:
        return [e for e in self._corpus
                if e.get("witness", {}).get("kind") == "positive"]

    def negatives(self) -> list[dict]:
        return [e for e in self._corpus
                if e.get("witness", {}).get("kind") in ("negative", "counterexample")]

    def intents(self) -> list[dict]:
        return [e for e in self._corpus
                if e.get("witness", {}).get("kind") == "intent"]

    def contexts(self) -> list[dict]:
        return [e for e in self._corpus
                if e.get("witness", {}).get("kind") == "context"]

    def by_tag(self, key: str, value: str) -> list[dict]:
        return [e for e in self._corpus
                if e.get("tags", {}).get(key) == value]

    def summary(self) -> dict[str, int]:
        kinds = {}
        for e in self._corpus:
            k = e.get("witness", {}).get("kind", "unknown")
            kinds[k] = kinds.get(k, 0) + 1
        return {"total": len(self._corpus), **kinds}


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        rec = WitnessRecorder(Path(td) / "witnesses.json")

        evt = StepEvent(at=utc_iso(), op="test", before_hash="aaa", after_hash="bbb")
        idx = rec.record_positive([evt], tags={"skill": "self-test"})
        assert idx == 0

        idx2 = rec.record_negative(
            violations=["BAD_PHASE"], trace=[evt],
            touched=[BoundaryTag.BLOCKED],
            tags={"skill": "self-test"},
        )
        assert idx2 == 1

        idx3 = rec.record_counterexample(
            violations=["CROSSING"], trace=[evt],
            tags={"skill": "self-test"},
        )
        assert idx3 == 2

        idx4 = rec.record_intent(
            "Preserve maker intent as first-class graph memory.",
            source="maker",
            tags={"skill": "self-test"},
        )
        assert idx4 == 3

        idx5 = rec.record_context(
            "Batch startup context should persist across sessions.",
            source="system",
            tags={"skill": "self-test"},
        )
        assert idx5 == 4

        assert len(rec) == 5
        assert len(rec.positives()) == 1
        assert len(rec.negatives()) == 2
        assert len(rec.intents()) == 1
        assert len(rec.contexts()) == 1
        assert len(rec.by_tag("skill", "self-test")) == 5

        n = rec.flush()
        assert n == 5
        assert (Path(td) / "witnesses.json").exists()

        # Reload
        rec2 = WitnessRecorder(Path(td) / "witnesses.json")
        assert len(rec2) == 5

        s = rec2.summary()
        assert s["total"] == 5
        assert s["positive"] == 1
        assert s["intent"] == 1
        assert s["context"] == 1

    print("PASS: witness_recorder self-test")
