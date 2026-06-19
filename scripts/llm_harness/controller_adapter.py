"""Controller adapter: drop a signed harness receipt where adaptive_controller can read it.

adaptive_controller.py is NOT modified (it is the existing brain).  This adapter
sits BESIDE it and translates an ``llm_run_receipt`` + its CandidateRun verdict
into a shape the controller's own loader (``adaptive_controller.load_result`` ->
plain ``json.loads``) and triage (``adaptive_controller.is_passing``) can parse.

WHY A RESULT DROP, NOT A QUEUE DROP (the direct-drop-is-unsafe finding):

  The controller's ``enqueue`` / ``triage_cycle`` path keys on ``sim_path``
  pointing at a real ``sim_*.py`` file that the runner will EXECUTE, and it
  derives ``runner_class`` / ``plan_bucket`` / lane by READING that source file
  (``runner_class_for`` reads ``path.read_text()``).  An LLM-run receipt has no
  ``sim_*.py`` to run.  Dropping it into ``queue/lane_*`` would make the
  controller try to read+execute a nonexistent sim path -> raise / mis-route.
  So a queue drop is UNSAFE for an LLM receipt.

  Instead we write a RESULT-side drop into ``sim_results/`` in the shape the
  controller's read-only triage understands.  The controller reads results with
  ``load_result`` (json.loads) and judges pass/fail with ``is_passing(r)``,
  which checks, in order: ``overall_pass`` -> ``pass`` -> ``all_pass`` ->
  ``ALL_PASS`` -> ``summary.all_pass`` -> ``result == "PASS"``.  We populate
  ``overall_pass`` directly so the controller triages the candidate as PASSING
  (admitted) or FAILING (rejected) without ever re-running anything.

EXACT FIELD MAPPING (llm_run_receipt + CandidateRun -> controller result drop):

  receipt.task_id                      -> "name"            (the result's identity)
  candidate.admitted                   -> "overall_pass"    (is_passing reads this FIRST)
  gate.verdict                         -> "result"          ("PASS"/"FAIL" fallback key)
  receipt.classification               -> "classification"  (controller reads this for stale/canonical)
  receipt.gate_ceiling_rung            -> "gate_ceiling_rung"
  receipt.promotion_allowed            -> "promotion_allowed" (controller's stage_gate reads this)
  receipt.claim_ceiling                -> "claim_ceiling"
  candidate.semantic_verdict           -> "semantic_verdict"
  full receipt.to_dict()               -> "llm_run_receipt"  (verbatim, signature intact)
  gate.to_dict()                       -> "gate_result"      (verbatim)
  receipt.signature                    -> "signature"        (mirrored to top level)
  "codex_ratchet.llm_controller_drop.v1" -> "schema"

The signed receipt is preserved VERBATIM inside ``llm_run_receipt`` so the
trusted-boundary signature still verifies after the drop (the wrapper keys are
ADDITIVE -- they do not mutate the signed payload).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .signing import verify_payload
from .types import GateResult, ModelReceipt

DROP_SCHEMA = "codex_ratchet.llm_controller_drop.v1"

# The controller's results dir, relative to repo root, kept in lock-step with
# adaptive_controller.RESULTS (PROBES / "a2_state/sim_results").
DEFAULT_RESULTS_SUBPATH = "system_v4/probes/a2_state/sim_results"


def _repo_root() -> Path:
    # scripts/llm_harness/controller_adapter.py -> repo root is parents[2].
    return Path(__file__).resolve().parents[2]


def controller_results_dir(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or _repo_root()
    return root / DEFAULT_RESULTS_SUBPATH


def receipt_to_controller_drop(
    receipt: ModelReceipt,
    gate_result: GateResult,
    *,
    semantic_verdict: str,
    admitted: bool,
) -> dict:
    """Translate a receipt + gate verdict into a controller-readable result dict.

    The returned dict carries ``overall_pass`` (the FIRST key the controller's
    ``is_passing`` reads) plus the full signed receipt verbatim under
    ``llm_run_receipt`` so the signature still verifies.
    """
    receipt_dict = receipt.to_dict()
    # The controller boundary MUST NOT trust an unverified receipt: a forged / unsigned receipt
    # cannot enter triage as PASSING even if the in-memory gate `admitted` flag is True (box-viii
    # L2 fix: the real fleet showed a forged SCRATCH-rung receipt reaching the controller as PASS,
    # because the gate only signature-checks on the promotion path and the adapter trusted `admitted`).
    signature_verified = verify_payload(receipt_dict)
    controller_pass = bool(admitted) and signature_verified
    return {
        "schema": DROP_SCHEMA,
        "name": receipt.task_id,
        # is_passing(r) reads overall_pass FIRST; only an admitted AND validly-signed receipt PASSES.
        "overall_pass": controller_pass,
        "result": "PASS" if controller_pass else "FAIL",
        "signature_verified": signature_verified,
        "classification": receipt.classification,
        "gate_ceiling_rung": receipt.gate_ceiling_rung,
        "granted_rung": gate_result.granted_rung,
        "promotion_allowed": receipt.promotion_allowed,
        "formal_admission_allowed": receipt.formal_admission_allowed,
        "claim_ceiling": receipt.claim_ceiling,
        "semantic_verdict": semantic_verdict,
        "produced_by": receipt.produced_by,
        # top-level mirror of the signature so a quick check does not need to
        # descend; the AUTHORITATIVE signed object is llm_run_receipt below.
        "signature": receipt.signature,
        "llm_run_receipt": receipt_dict,
        "gate_result": gate_result.to_dict(),
    }


def write_controller_drop(
    receipt: ModelReceipt,
    gate_result: GateResult,
    *,
    semantic_verdict: str,
    admitted: bool,
    results_dir: Optional[Path] = None,
) -> Path:
    """Write the controller-readable result drop and return its path.

    Filename is ``{task_id}_results.json`` so the controller's
    ``find_result_file`` (which globs ``*_results.json``) can locate it.
    """
    rdir = results_dir or controller_results_dir()
    rdir.mkdir(parents=True, exist_ok=True)
    drop = receipt_to_controller_drop(
        receipt, gate_result, semantic_verdict=semantic_verdict, admitted=admitted
    )
    target = rdir / f"{receipt.task_id}_results.json"
    target.write_text(json.dumps(drop, indent=2, sort_keys=True), encoding="utf-8")
    return target


def load_controller_drop(path: str | Path) -> dict:
    """Controller-side loader: the same json.loads the controller uses.

    Mirrors ``adaptive_controller.load_result`` (plain json.loads, empty dict on
    error) so a test can assert the drop is parseable by the controller's own
    reading path without importing the controller module.
    """
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def drop_signature_verifies(drop: dict) -> bool:
    """True iff the signed receipt embedded in the drop still verifies.

    The wrapper keys are additive; the authoritative signed object is
    ``llm_run_receipt``.  A forged/unsigned embedded receipt returns False.
    """
    receipt_dict = drop.get("llm_run_receipt")
    if not isinstance(receipt_dict, dict):
        return False
    return verify_payload(receipt_dict)
