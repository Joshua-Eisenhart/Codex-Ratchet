"""Offline tests for the candidate-flow orchestrator + controller adapter (L2).

Every test here MUST be able to fail -- none is a by-construction tautology.
No network: the micro-eval runs REAL py_compile subprocesses (the sim-stack
python), and the providers are the deterministic offline fakes.

Acceptance coverage (from the L2 task card):
  * the 6 stages each run and record a step
  * a FAILING micro-eval -> semantic_control = reject (could-fail)
  * semantic_control admission == gate().admitted (orchestrator never overrides)
  * the adapter writes a result the controller-side loader can parse
  * an unsigned/forged receipt -> keep_scratch (no promotion through orchestrator)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]  # repo root: .../Codex-Ratchet
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from llm_harness import (  # noqa: E402
    CandidateRun,
    FakeFailureProvider,
    FakeSuccessProvider,
    ModelJob,
    SEMANTIC_ADMIT,
    SEMANTIC_KEEP_SCRATCH,
    SEMANTIC_REJECT,
    STAGE_NAMES,
    TaskSpec,
    drop_signature_verifies,
    gate,
    load_controller_drop,
    receipt_to_controller_drop,
    run_candidate,
    run_job,
    write_controller_drop,
)
from llm_harness.signing import sign_payload, verify_payload  # noqa: E402

TS_START = "2026-06-15T00:00:00+00:00"
TS_END = "2026-06-15T00:00:01+00:00"


def _task(task_id="cand", role="builder", classification="scratch_diagnostic",
          gate_ceiling_rung="scratch_diagnostic", claim_ceiling="", input_refs=None,
          audit_required=False):
    return TaskSpec(
        task_id=task_id,
        role=role,
        prompt="offline candidate prompt",
        classification=classification,
        gate_ceiling_rung=gate_ceiling_rung,
        claim_ceiling=claim_ceiling,
        input_refs=input_refs or [],
        audit_required=audit_required,
    )


def _run(provider, task, tmp_path, *, produced_by="agent-A", micro_eval_cmds=None,
         receipt_path=None):
    return run_candidate(
        task,
        provider,
        model="offline-fake",
        output_path=str(tmp_path / "out.txt"),
        produced_by=produced_by,
        workdir=tmp_path,
        started_at=TS_START,
        completed_at=TS_END,
        timeout=30.0,
        receipt_path=receipt_path,
        micro_eval_cmds=micro_eval_cmds,
    )


# ---------------------------------------------------------------------------
# 1. The six stages each run and record a step.
# ---------------------------------------------------------------------------


def test_all_six_stages_run_and_record_a_step(tmp_path):
    cr = _run(FakeSuccessProvider(), _task("c_six"), tmp_path)
    recorded = [s.stage for s in cr.stages]
    assert recorded == list(STAGE_NAMES)  # exact order, all six
    # each step is a real StageStep with a verdict + detail
    for s in cr.stages:
        assert isinstance(s.ok, bool)
        assert isinstance(s.detail, str) and s.detail != ""


def test_stage_count_is_load_bearing_missing_provider_truncates(tmp_path):
    """could-fail guard: a provider that raises mid-run does NOT silently still
    record all six green stages -- the trace reflects the real failure."""
    class _BoomProvider(FakeSuccessProvider):
        name = "boom"

        def run(self, job, *, timeout=None, started_at=None, completed_at=None):
            from llm_harness.providers import ProviderError

            raise ProviderError("provider blew up")

    cr = _run(_BoomProvider(), _task("c_boom"), tmp_path)
    # observation failed -> no receipt -> verdict keep_scratch, NOT admit.
    assert cr.receipt is None
    assert cr.semantic_verdict == SEMANTIC_KEEP_SCRATCH
    assert cr.admitted is False
    obs = cr.step("typed_observation")
    assert obs is not None and obs.ok is False


# ---------------------------------------------------------------------------
# 2. semantic_control admission == gate().admitted (never overridden).
# ---------------------------------------------------------------------------


def test_semantic_control_admission_equals_gate_admitted(tmp_path):
    cr = _run(FakeSuccessProvider(), _task("c_admit"), tmp_path)
    assert cr.gate_result is not None
    # the orchestrator's admission is byte-for-byte the gate's admission
    assert cr.admitted == cr.gate_result.admitted
    assert cr.admitted is True
    assert cr.semantic_verdict == SEMANTIC_ADMIT
    sc = cr.step("semantic_control")
    assert sc.data["gate_admitted"] == cr.gate_result.admitted


def test_orchestrator_does_not_admit_what_gate_rejects(tmp_path):
    """A failing provider run -> gate rejects on status -> orchestrator MUST NOT
    flip it to admit.  This could fail if the orchestrator re-decided."""
    cr = _run(FakeFailureProvider(), _task("c_fail"), tmp_path)
    assert cr.gate_result.admitted is False
    assert cr.admitted is False  # not overridden to True
    assert cr.semantic_verdict == SEMANTIC_REJECT  # signed but real failure


# ---------------------------------------------------------------------------
# 3. A FAILING micro-eval -> semantic_control = reject (could-fail).
# ---------------------------------------------------------------------------


def test_failing_micro_eval_forces_reject(tmp_path):
    """Make the NEGATIVE micro-eval case SUCCEED (compile a good file) so the
    eval's negative_ok becomes False -> micro-eval fails -> reject.

    This could fail: a passing micro-eval (default broken negative) admits."""
    good = tmp_path / "good_negative.py"
    good.write_text("y = 2\n", encoding="utf-8")
    cr = _run(
        FakeSuccessProvider(),
        _task("c_microfail"),
        tmp_path,
        micro_eval_cmds={"negative": [sys.executable, "-m", "py_compile", str(good)]},
    )
    micro = cr.step("bounded_micro_eval")
    assert micro.ok is False
    assert micro.could_fail is True
    assert cr.semantic_verdict == SEMANTIC_REJECT
    assert cr.admitted is False
    # the run status was demoted so the gate (code-owned) saw a non-success run
    assert cr.receipt.status != "success"


def test_passing_micro_eval_admits_control_for_above(tmp_path):
    """Control: with the DEFAULT (broken) negative case the micro-eval passes
    and the same provider admits -- proving the failing test above is not vacuous."""
    cr = _run(FakeSuccessProvider(), _task("c_micropass"), tmp_path)
    micro = cr.step("bounded_micro_eval")
    assert micro.ok is True
    assert cr.semantic_verdict == SEMANTIC_ADMIT


# ---------------------------------------------------------------------------
# 4. The adapter writes a result the controller-side loader can parse.
# ---------------------------------------------------------------------------


def test_adapter_drop_parses_with_controller_is_passing(tmp_path):
    cr = _run(FakeSuccessProvider(), _task("c_drop"), tmp_path,
              receipt_path=str(tmp_path / "c_drop.receipt.json"))
    results_dir = tmp_path / "sim_results"
    drop_path = write_controller_drop(
        cr.receipt,
        cr.gate_result,
        semantic_verdict=cr.semantic_verdict,
        admitted=cr.admitted,
        results_dir=results_dir,
    )
    assert drop_path.exists()
    # filename matches the controller's *_results.json discovery glob
    assert drop_path.name == "c_drop_results.json"

    # the controller reads results with load_result == json.loads; emulate it.
    parsed = load_controller_drop(drop_path)
    assert parsed != {}  # parseable

    # the controller judges pass/fail with adaptive_controller.is_passing(r);
    # import the REAL function and assert it reads our drop as PASS (admitted).
    sys.path.insert(0, str(SCRIPTS))
    import importlib

    ac = importlib.import_module("adaptive_controller")
    assert ac.is_passing(parsed) is True  # admitted -> overall_pass True -> PASS

    # the embedded signed receipt still verifies (additive wrapper, signature intact)
    assert drop_signature_verifies(parsed) is True


def test_adapter_drop_reflects_rejection_as_failing(tmp_path):
    """A rejected candidate's drop reads as FAILING through the controller's
    is_passing -- could fail if the adapter hardcoded overall_pass=True."""
    cr = _run(FakeFailureProvider(), _task("c_dropfail"), tmp_path)
    results_dir = tmp_path / "sim_results"
    drop_path = write_controller_drop(
        cr.receipt,
        cr.gate_result,
        semantic_verdict=cr.semantic_verdict,
        admitted=cr.admitted,
        results_dir=results_dir,
    )
    parsed = load_controller_drop(drop_path)
    import importlib

    ac = importlib.import_module("adaptive_controller")
    assert ac.is_passing(parsed) is False  # rejected -> overall_pass False
    assert parsed["overall_pass"] is False


def test_adapter_field_mapping_is_exact(tmp_path):
    cr = _run(FakeSuccessProvider(),
              _task("c_map", classification="scratch_diagnostic",
                    claim_ceiling="fixture-only scope sentence"),
              tmp_path)
    drop = receipt_to_controller_drop(
        cr.receipt, cr.gate_result,
        semantic_verdict=cr.semantic_verdict, admitted=cr.admitted,
    )
    assert drop["name"] == cr.receipt.task_id
    assert drop["overall_pass"] is cr.admitted
    assert drop["classification"] == cr.receipt.classification
    assert drop["claim_ceiling"] == "fixture-only scope sentence"
    assert drop["gate_ceiling_rung"] == cr.receipt.gate_ceiling_rung
    assert drop["promotion_allowed"] == cr.receipt.promotion_allowed
    assert drop["semantic_verdict"] == cr.semantic_verdict
    # the full signed receipt is preserved verbatim
    assert drop["llm_run_receipt"] == cr.receipt.to_dict()
    assert drop["signature"] == cr.receipt.signature


# ---------------------------------------------------------------------------
# 5. An unsigned / forged receipt -> keep_scratch (no promotion through orch).
# ---------------------------------------------------------------------------


def test_forged_promotion_receipt_keeps_scratch_not_promote(tmp_path):
    """A receipt that REQUESTS promotion but is hand-edited after signing:
    gate rejects (no valid signature), orchestrator returns keep_scratch_diagnostic.

    Could fail: a validly signed promotion receipt with an auditor would admit.
    """
    # build + sign a promotion-requesting receipt, then forge a field.
    job = ModelJob(
        task=_task("c_forge", gate_ceiling_rung="classical_baseline"),
        provider="fake_success",
        model="m",
        output_path=str(tmp_path / "o.txt"),
        produced_by="agent-A",
    )
    receipt = run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)
    assert verify_payload(receipt.to_dict()) is True  # validly signed first
    receipt.content = "TAMPERED-AFTER-SIGNING"  # forge, do NOT re-sign
    assert verify_payload(receipt.to_dict()) is False  # signature now broken

    g = gate(receipt)
    assert g.admitted is False  # gate refuses to promote a forged receipt
    # the adapter drop reflects keep_scratch, and the embedded receipt fails verify.
    drop = receipt_to_controller_drop(
        receipt, g, semantic_verdict=SEMANTIC_KEEP_SCRATCH, admitted=g.admitted
    )
    assert drop["overall_pass"] is False
    assert drop_signature_verifies(drop) is False


def test_orchestrator_run_with_forged_input_does_not_promote(tmp_path):
    """End-to-end through run_candidate: a candidate requesting promotion with a
    FakeFailure (no valid success) is never admitted and never promoted; granted
    rung stays scratch_diagnostic."""
    cr = _run(
        FakeFailureProvider(),
        _task("c_noprom", gate_ceiling_rung="classical_baseline"),
        tmp_path,
    )
    assert cr.admitted is False
    assert cr.gate_result.granted_rung == "scratch_diagnostic"  # never promoted
    assert cr.semantic_verdict in (SEMANTIC_REJECT, SEMANTIC_KEEP_SCRATCH)


# ---------------------------------------------------------------------------
# determinism: same inputs -> same stage verdicts (selection is deterministic).
# ---------------------------------------------------------------------------


def test_candidate_flow_is_deterministic(tmp_path):
    cr1 = _run(FakeSuccessProvider(), _task("c_det"), tmp_path / "a")
    cr2 = _run(FakeSuccessProvider(), _task("c_det"), tmp_path / "b")
    v1 = [(s.stage, s.ok) for s in cr1.stages]
    v2 = [(s.stage, s.ok) for s in cr2.stages]
    assert v1 == v2
    assert cr1.semantic_verdict == cr2.semantic_verdict
    assert cr1.admitted == cr2.admitted


# ---------------------------------------------------------------------------
# EXECUTOR / NOTARY SPLIT at the orchestrator level: the orchestrator drives
# UNTRUSTED model output and must NOT hold a signing-key capability -- only the
# notary signs.  The receipt that comes out is notary-signed (carries key_id)
# and verifies; the orchestrator module cannot mint a signature itself.
# ---------------------------------------------------------------------------
from llm_harness import orchestrator as _orch  # noqa: E402


def test_orchestrator_cannot_sign_only_notary_can(tmp_path):
    """The orchestrator (untrusted-output path) exposes NO signing-key capability: no
    ``sign_payload`` / ``get_key`` in its namespace.  The receipt it emits is nonetheless validly
    signed -- because it was notarized -- and carries a per-identity ``key_id``.

    Could fail: if the orchestrator re-imported the inline signer (the pre-split code), the first
    asserts fire; if notarization were skipped, the signature/verify asserts fire.
    """
    # 1. the orchestrator module holds no signer/key (verify_payload is read-only and allowed)
    assert not hasattr(_orch, "sign_payload")
    assert not hasattr(_orch, "get_key")

    # 2. an end-to-end candidate run still yields a notary-signed, verifying receipt with a key_id
    cr = _run(FakeSuccessProvider(), _task("c_notary"), tmp_path, produced_by="agent-A")
    assert cr.receipt is not None
    assert cr.receipt.signature is not None
    assert cr.receipt.key_id is not None          # per-identity key stamped by the notary
    assert verify_payload(cr.receipt.to_dict()) is True
    # the gateproof stage's signature check is green (the notary's signature verifies through it)
    gp = cr.step("gateproof")
    assert gp is not None and gp.data["signature_ok"] is True


def test_orchestrator_demotion_branch_renotarizes_not_self_signs(tmp_path):
    """The micro-eval-failure branch demotes the receipt status and MUST re-notarize through the
    notary (not self-sign): the demoted receipt still verifies and the gate sees a signed,
    non-success run.

    Could fail: if the demotion path left the receipt unsigned (or signed with a stale signature),
    verify_payload would be False on the demoted receipt.
    """
    good = tmp_path / "good_negative.py"
    good.write_text("y = 2\n", encoding="utf-8")
    cr = _run(
        FakeSuccessProvider(),
        _task("c_demote"),
        tmp_path,
        produced_by="agent-A",
        micro_eval_cmds={"negative": [sys.executable, "-m", "py_compile", str(good)]},
    )
    assert cr.receipt.status != "success"                 # demoted
    assert cr.receipt.signature is not None
    assert verify_payload(cr.receipt.to_dict()) is True   # re-notarized over the demoted payload
