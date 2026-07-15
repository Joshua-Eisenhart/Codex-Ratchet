#!/usr/bin/env python3
"""Fail-closed preregistration hash and object-card validator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    receipt = json.loads((SIM_DIR / "preregistration_receipt.json").read_text(encoding="utf-8"))
    wizard = json.loads((SIM_DIR / "wizard_v4_3_validation.json").read_text(encoding="utf-8"))
    spec = json.loads((SIM_DIR / "spec.json").read_text(encoding="utf-8"))
    checks = {
        "spec_hash": sha256(SIM_DIR / "spec.json") == receipt["spec_sha256"],
        "object_card_hash": sha256(SIM_DIR / "wizard_v4_3_object_card.json") == receipt["object_card_sha256"],
        "object_card_validation": wizard.get("ok") is True and not wizard.get("errors"),
        "builders_absent_at_freeze": receipt.get("builder_sources_present_at_freeze") is False,
        "scratch_only": spec.get("classification") == "scratch_diagnostic",
        "no_promotion": spec.get("promotion_allowed") is False and spec.get("formal_admission_allowed") is False,
        "no_llm_gate": spec.get("llm_verdict_allowed") is False,
    }
    ok = all(checks.values())
    print(json.dumps({"schema": "codex_ratchet.preregistration_validation.v1", "ok": ok, "checks": checks}, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
