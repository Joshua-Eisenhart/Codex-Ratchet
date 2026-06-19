"""Offline tests for the deterministic LLM harness core.

Every test here MUST be able to fail -- none is a by-construction tautology.
No network in the default suite (the ONE real OpenRouter call is gated behind
RUN_OPENROUTER_LIVE=1 and skips otherwise).  The LocalToolProvider tests run a
REAL subprocess (the sim-stack python compiling a file) and assert on the REAL
captured returncode.  The OpenRouter MAPPING tests run against a RECORDED
fixture (no network) so the field mapping is verified offline.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]  # repo root: .../Codex-Ratchet
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from llm_harness import (  # noqa: E402
    FakeFailureProvider,
    FakeMalformedProvider,
    FakeSuccessProvider,
    FakeTimeoutProvider,
    GateResult,
    LocalToolProvider,
    ModelJob,
    ModelReceipt,
    OpenRouterProvider,
    RECEIPT_SCHEMA,
    TaskSpec,
    canonicalize_content,
    content_canonical_hash,
    gate,
    map_openrouter_response,
    run_job,
    sandbox_config_hash,
)

TS_START = "2026-06-15T00:00:00+00:00"
TS_END = "2026-06-15T00:00:01+00:00"

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "llm_harness"
SUCCESS_FIXTURE = FIXTURES / "openrouter_grok_success.json"
ERROR_FIXTURE = FIXTURES / "openrouter_error_400.json"


def _task(task_id="t1", role="builder", classification="scratch_diagnostic",
          claim_ceiling="", gate_ceiling_rung="scratch_diagnostic",
          input_refs=None, audit_required=False):
    return TaskSpec(
        task_id=task_id,
        role=role,
        prompt="hello offline world",
        classification=classification,
        claim_ceiling=claim_ceiling,
        gate_ceiling_rung=gate_ceiling_rung,
        input_refs=input_refs or [],
        audit_required=audit_required,
    )


def _job(provider, model, output_path, task=None, command=None, cwd=None, produced_by="agent-A",
         temperature=None, max_tokens=None, system_prompt=None, tools=None, effort=None):
    return ModelJob(
        task=task or _task(),
        provider=provider,
        model=model,
        output_path=str(output_path),
        command=command,
        cwd=cwd,
        produced_by=produced_by,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        tools=tools,
        effort=effort,
    )


# ---------------------------------------------------------------------------
# Receipt writing, fully offline
# ---------------------------------------------------------------------------


def test_receipt_writes_to_disk_no_network(tmp_path):
    out = tmp_path / "out.txt"
    receipt_path = tmp_path / "r.receipt.json"
    job = _job("fake_success", "offline-fake", out)
    receipt = run_job(
        job,
        FakeSuccessProvider(),
        started_at=TS_START,
        completed_at=TS_END,
        receipt_path=receipt_path,
    )
    assert receipt.status == "success"
    assert receipt_path.is_file()
    payload = json.loads(receipt_path.read_text())
    assert payload["schema"] == RECEIPT_SCHEMA
    assert payload["schema"] == "codex_ratchet.llm_run_receipt.v1"
    assert payload["prompt_sha256"] == receipt.prompt_sha256
    # mandatory project + derived fields present on disk
    for key in (
        "classification", "claim_ceiling", "gate_ceiling_rung", "promotion_allowed",
        "formal_admission_allowed", "task_id", "role", "provider", "launch_surface",
        "model_requested", "model_resolved", "input_refs", "output_path",
        "artifact_paths", "status", "returncode", "http_status",
        "started_at", "completed_at", "tests", "audit_required",
        "finish_reason", "native_finish_reason", "usage", "content_canonical_hash",
        "success_or_error_discriminator",
    ):
        assert key in payload, f"missing mandatory field: {key}"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False


# ---------------------------------------------------------------------------
# Status mapping for the fakes
# ---------------------------------------------------------------------------


def test_fake_timeout_status_timed_out(tmp_path):
    job = _job("fake_timeout", "offline-fake", tmp_path / "o")
    r = run_job(job, FakeTimeoutProvider(), started_at=TS_START, completed_at=TS_END)
    assert r.status == "timed_out"
    assert r.returncode is None


def test_fake_malformed_status_blocked(tmp_path):
    job = _job("fake_malformed", "offline-fake", tmp_path / "o")
    r = run_job(job, FakeMalformedProvider(), started_at=TS_START, completed_at=TS_END)
    assert r.status == "blocked"


def test_fake_failure_status_error_nonzero_rc(tmp_path):
    job = _job("fake_failure", "offline-fake", tmp_path / "o")
    r = run_job(job, FakeFailureProvider(returncode=3), started_at=TS_START, completed_at=TS_END)
    assert r.status == "error"
    assert r.returncode == 3
    assert r.returncode != 0


# ---------------------------------------------------------------------------
# LocalToolProvider: REAL subprocess, broken file -> error, good file -> success
# ---------------------------------------------------------------------------


def test_local_tool_broken_python_captures_failure(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("def f(:\n    pass\n")  # syntax error
    job = _job(
        "local_tool", "py_compile", tmp_path / "stdout.txt",
        command=[sys.executable, "-m", "py_compile", str(broken)],
    )
    r = run_job(job, LocalToolProvider(), timeout=30, started_at=TS_START, completed_at=TS_END)
    assert r.status == "error", f"expected error, got {r.status} rc={r.returncode}"
    assert r.returncode is not None and r.returncode != 0


def test_local_tool_good_python_captures_success(tmp_path):
    good = tmp_path / "good.py"
    good.write_text("def f():\n    return 1\n")
    job = _job(
        "local_tool", "py_compile", tmp_path / "stdout.txt",
        command=[sys.executable, "-m", "py_compile", str(good)],
    )
    r = run_job(job, LocalToolProvider(), timeout=30, started_at=TS_START, completed_at=TS_END)
    assert r.status == "success", f"expected success, got {r.status} rc={r.returncode}"
    assert r.returncode == 0


def test_local_tool_timeout_maps_to_timed_out(tmp_path):
    # A real subprocess that sleeps longer than the timeout.
    job = _job(
        "local_tool", "sleep", tmp_path / "stdout.txt",
        command=[sys.executable, "-c", "import time; time.sleep(5)"],
    )
    r = run_job(job, LocalToolProvider(), timeout=0.5, started_at=TS_START, completed_at=TS_END)
    assert r.status == "timed_out"
    assert r.returncode is None


# ---------------------------------------------------------------------------
# Gate determinism: same receipt -> byte-identical GateResult
# ---------------------------------------------------------------------------


def test_gate_determinism_byte_identical(tmp_path):
    out = tmp_path / "out.txt"
    job = _job("fake_success", "offline-fake", out)
    receipt = run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)
    g1 = gate(receipt)
    g2 = gate(receipt)
    b1 = json.dumps(g1.to_dict(), sort_keys=True)
    b2 = json.dumps(g2.to_dict(), sort_keys=True)
    assert b1 == b2
    # Spot-check the verdict is actually data, not a constant.
    assert g1.verdict == "admit"
    assert g1.admitted is True


def test_gate_rejects_failed_receipt(tmp_path):
    job = _job("fake_failure", "offline-fake", tmp_path / "o")
    receipt = run_job(job, FakeFailureProvider(), started_at=TS_START, completed_at=TS_END)
    g = gate(receipt)
    assert g.admitted is False
    assert g.verdict == "reject"
    assert any("status_not_success" in r for r in g.reasons)


# ---------------------------------------------------------------------------
# claim_ceiling vs gate_ceiling_rung: the COLLISION fix (punch-list item 1)
# ---------------------------------------------------------------------------


def test_free_text_claim_ceiling_does_not_drive_the_gate(tmp_path):
    # A free-text claim_ceiling (a prose scope sentence, as on a real
    # codex_ratchet.sim_result.v1 receipt) must NOT be treated as a ladder rung:
    # the gate ranks gate_ceiling_rung only, so a scratch_diagnostic-rung run with
    # a long prose claim_ceiling is admitted at scratch_diagnostic WITHOUT an audit.
    out = tmp_path / "out.txt"
    task = _task(
        task_id="freetext",
        claim_ceiling="diagonal_open_channel_memory_fixture_only; not full quantum Hopfield; not QIT admission",
        gate_ceiling_rung="scratch_diagnostic",
    )
    job = _job("fake_success", "offline-fake", out, task=task)
    receipt = run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)
    # The prose claim_ceiling is preserved verbatim on the receipt...
    assert receipt.claim_ceiling.startswith("diagonal_open_channel_memory_fixture_only")
    g = gate(receipt)
    # ...and it does NOT crash or self-promote: the gate ranks the RUNG, not the prose.
    assert g.admitted is True
    assert g.granted_rung == "scratch_diagnostic"


def test_gate_ceiling_rung_drives_promotion_not_claim_ceiling(tmp_path):
    # A canonical RUNG requires an audit; the free-text claim_ceiling is irrelevant
    # to that decision. Same prose, different rung -> different gate outcome.
    out = tmp_path / "out.txt"
    task = _task(
        task_id="rung-promote",
        claim_ceiling="some free text scope",
        gate_ceiling_rung="canonical",
        audit_required=True,
    )
    job = _job("fake_success", "offline-fake", out, task=task)
    receipt = run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)
    g = gate(receipt, audit_receipts=[])  # no separate auditor
    assert g.admitted is False
    assert g.granted_rung == "scratch_diagnostic"
    assert any("self_promotion_blocked" in r for r in g.reasons)


def test_invalid_gate_ceiling_rung_off_ladder_rejected(tmp_path):
    out = tmp_path / "out.txt"
    job = _job("fake_success", "offline-fake", out)
    receipt = run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)
    receipt.gate_ceiling_rung = "not-a-real-rung"
    g = gate(receipt)
    assert g.admitted is False
    assert any("schema_invalid" in r for r in g.reasons)


# ---------------------------------------------------------------------------
# No self-grading: self-promotion above scratch without an audit receipt -> reject
# ---------------------------------------------------------------------------


def test_no_self_grading_rejects_self_promotion(tmp_path):
    out = tmp_path / "out.txt"
    task = _task(task_id="promote-me", gate_ceiling_rung="canonical", audit_required=True)
    job = _job("fake_success", "offline-fake", out, task=task)
    receipt = run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)
    g = gate(receipt, audit_receipts=[])  # no separate auditor
    assert g.admitted is False
    assert g.granted_rung == "scratch_diagnostic"
    assert any("self_promotion_blocked" in r for r in g.reasons)


def test_separate_auditor_receipt_satisfies_promotion(tmp_path):
    out = tmp_path / "out.txt"
    task = _task(task_id="promote-me", gate_ceiling_rung="canonical", audit_required=True)
    job = _job("fake_success", "offline-fake", out, task=task)
    receipt = run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)

    # A SEPARATE auditor receipt: different task_id, role=auditor, refs the task.
    audit_task = _task(
        task_id="audit-of-promote-me",
        role="auditor",
        input_refs=["promote-me"],
    )
    audit_job = _job("fake_success", "offline-fake", tmp_path / "a.txt", task=audit_task, produced_by="agent-B")
    audit_receipt = run_job(audit_job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)

    g = gate(receipt, audit_receipts=[audit_receipt])
    assert g.admitted is True
    assert g.granted_rung == "canonical"


def test_same_author_auditor_does_not_satisfy(tmp_path):
    # box-viii L1 fix: an "auditor" receipt with a DIFFERENT task_id but the SAME author
    # (produced_by) must NOT satisfy -- the same author cannot self-promote by minting a
    # fresh task_id (the forgery the mass audit caught: task_id-difference != author-diff).
    out = tmp_path / "out.txt"
    task = _task(task_id="work", gate_ceiling_rung="canonical", audit_required=True)
    job = _job("fake_success", "offline-fake", out, task=task, produced_by="agent-A")
    receipt = run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)

    forged_task = _task(task_id="audit-of-work", role="auditor", input_refs=["work"])
    forged_job = _job("fake_success", "offline-fake", tmp_path / "a.txt", task=forged_task, produced_by="agent-A")
    forged_audit = run_job(forged_job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)

    g = gate(receipt, audit_receipts=[forged_audit])
    assert g.admitted is False
    assert g.granted_rung == "scratch_diagnostic"


def test_self_audit_does_not_satisfy(tmp_path):
    # An "auditor" receipt with the SAME task_id must NOT satisfy the audit.
    out = tmp_path / "out.txt"
    task = _task(task_id="same", gate_ceiling_rung="canonical", audit_required=True)
    job = _job("fake_success", "offline-fake", out, task=task)
    receipt = run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)

    self_audit_task = _task(task_id="same", role="auditor", input_refs=["same"])
    self_audit_job = _job("fake_success", "offline-fake", tmp_path / "a.txt", task=self_audit_task)
    self_audit = run_job(self_audit_job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)

    g = gate(receipt, audit_receipts=[self_audit])
    assert g.admitted is False
    assert g.granted_rung == "scratch_diagnostic"


# ---------------------------------------------------------------------------
# Audit-guard: ONE clause violated at a time -> NOT satisfied (punch-list item 5)
# Each sub-case isolates a single audit-clause failure so the guard is shown
# load-bearing per clause (not just a single all-or-nothing check).
# ---------------------------------------------------------------------------


def _promotable_receipt(tmp_path):
    task = _task(task_id="needs-audit", gate_ceiling_rung="canonical", audit_required=True)
    job = _job("fake_success", "offline-fake", tmp_path / "w.txt", task=task, produced_by="agent-A")
    return run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)


def _valid_auditor_receipt(tmp_path):
    audit_task = _task(task_id="audit-needs-audit", role="auditor", input_refs=["needs-audit"])
    audit_job = _job("fake_success", "offline-fake", tmp_path / "a.txt", task=audit_task, produced_by="agent-B")
    return run_job(audit_job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)


def test_audit_guard_baseline_valid_auditor_satisfies(tmp_path):
    # Control: the un-violated auditor receipt DOES satisfy (so the violated
    # variants below are isolating a single failing clause, not a dead path).
    receipt = _promotable_receipt(tmp_path)
    g = gate(receipt, audit_receipts=[_valid_auditor_receipt(tmp_path)])
    assert g.admitted is True
    assert g.granted_rung == "canonical"


def test_audit_guard_role_clause_violated(tmp_path):
    # role != "auditor" -> NOT satisfied.
    receipt = _promotable_receipt(tmp_path)
    auditor = _valid_auditor_receipt(tmp_path)
    auditor.role = "builder"  # violate ONLY the role clause
    g = gate(receipt, audit_receipts=[auditor])
    assert g.admitted is False
    assert g.granted_rung == "scratch_diagnostic"


def test_audit_guard_status_clause_violated(tmp_path):
    # status != "success" -> NOT satisfied.
    receipt = _promotable_receipt(tmp_path)
    auditor = _valid_auditor_receipt(tmp_path)
    auditor.status = "error"  # violate ONLY the status clause
    g = gate(receipt, audit_receipts=[auditor])
    assert g.admitted is False
    assert g.granted_rung == "scratch_diagnostic"


def test_audit_guard_input_refs_clause_violated(tmp_path):
    # input_refs no longer names the audited task_id -> NOT satisfied.
    receipt = _promotable_receipt(tmp_path)
    auditor = _valid_auditor_receipt(tmp_path)
    auditor.input_refs = ["some-other-task"]  # violate ONLY the input_refs clause
    g = gate(receipt, audit_receipts=[auditor])
    assert g.admitted is False
    assert g.granted_rung == "scratch_diagnostic"


# ---------------------------------------------------------------------------
# Gate wraps a REAL check: a broken .py artifact fails the compile check
# ---------------------------------------------------------------------------


def test_gate_real_compile_check_fails_on_broken_artifact(tmp_path):
    broken = tmp_path / "art.py"
    broken.write_text("def x(:\n")
    # Hand-build a receipt that is "success" but carries a broken .py artifact.
    receipt = ModelReceipt(
        task_id="art-task",
        role="builder",
        provider="fake_success",
        launch_surface="fake",
        model_requested="offline-fake",
        prompt_sha256="deadbeef",
        input_refs=[],
        output_path=str(broken),
        artifact_paths=[str(broken)],
        status="success",
        returncode=0,
        started_at=TS_START,
        completed_at=TS_END,
    )
    g = gate(receipt)
    assert g.admitted is False
    assert any("artifact_compile_failed" in r for r in g.reasons)
    # And on a GOOD artifact the same check passes (the check could go either way).
    good = tmp_path / "good_art.py"
    good.write_text("y = 1\n")
    receipt_ok = ModelReceipt(
        task_id="art-task-ok",
        role="builder",
        provider="fake_success",
        launch_surface="fake",
        model_requested="offline-fake",
        prompt_sha256="deadbeef",
        input_refs=[],
        output_path=str(good),
        artifact_paths=[str(good)],
        status="success",
        returncode=0,
        started_at=TS_START,
        completed_at=TS_END,
    )
    g_ok = gate(receipt_ok)
    assert g_ok.admitted is True


def test_gate_result_is_gateresult_type(tmp_path):
    job = _job("fake_success", "offline-fake", tmp_path / "o")
    receipt = run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)
    g = gate(receipt)
    assert isinstance(g, GateResult)
    assert g.schema == "codex_ratchet.llm_gate_result.v1"


# ---------------------------------------------------------------------------
# OpenRouter response MAPPING -- offline against a RECORDED fixture
# (punch-list items 2 + 3 mapping verification without network)
# ---------------------------------------------------------------------------


def _map_fixture(fixture_path, *, temperature=0, max_tokens=12):
    fix = json.loads(fixture_path.read_text())
    task = TaskSpec(task_id="map-t", role="builder", prompt="Say the single word: ok")
    job = ModelJob(
        task=task, provider="openrouter", model="x-ai/grok-4.3",
        output_path="/tmp/_unused.out", temperature=temperature, max_tokens=max_tokens,
    )
    prov = OpenRouterProvider(api_key="offline-dummy")
    base = prov._base_receipt_kwargs(job, launch_surface="openrouter")
    base["provider"] = "openrouter"
    return job, map_openrouter_response(
        job, http_status=fix["http_status"], body=fix["body"],
        started_at=TS_START, completed_at=TS_END, duration_ms=123, base_kwargs=base,
    )


def test_openrouter_success_mapping_offline_fixture():
    assert SUCCESS_FIXTURE.is_file(), "recorded success fixture missing"
    _, r = _map_fixture(SUCCESS_FIXTURE)
    assert r.status == "success"
    assert r.success_or_error_discriminator == "choices_present"
    assert r.http_status == 200
    # model_resolved is the DATED slug and DIFFERS from the requested id.
    assert r.model_requested == "x-ai/grok-4.3"
    assert r.model_resolved == "x-ai/grok-4.3-20260430"
    assert r.model_resolved != r.model_requested
    # finish_reason canonicalized; native preserved VERBATIM (not normalized away).
    assert r.finish_reason == "stop"
    assert r.native_finish_reason == "completed"
    # message + reasoning + usage mapped.
    assert r.content == "ok"
    assert r.content_empty is False
    assert r.message_role == "assistant"
    assert r.has_reasoning is True and r.reasoning_content is not None
    assert r.refusal is None
    assert r.usage_prompt_tokens is not None and r.usage_completion_tokens is not None
    assert r.usage_total_tokens is not None
    assert r.usage_is_byok is False
    assert r.cost_usd is not None and r.cost_usd > 0
    # determinism-constructed hashes populated.
    assert r.content_canonical_hash and len(r.content_canonical_hash) == 64
    assert r.sandbox_config_hash and len(r.sandbox_config_hash) == 64
    # and a success receipt is admitted by the gate.
    g = gate(r)
    assert g.admitted is True


def test_openrouter_error_mapping_disjoint_shape():
    assert ERROR_FIXTURE.is_file(), "recorded error fixture missing"
    _, r = _map_fixture(ERROR_FIXTURE)
    # error shape: status error, http 400, error_body + error_user_id only.
    assert r.status == "error"
    assert r.success_or_error_discriminator == "top_level_error"
    assert r.http_status == 400
    assert r.error_body is not None
    assert r.error_body["code"] == 400  # in-body code field (distinct field from http_status)
    assert "not a valid model ID" in r.error_body["message"]
    assert r.error_user_id and r.error_user_id.startswith("user_")
    # the disjoint success-only fields are absent on the error shape.
    assert r.model_resolved is None
    assert r.content is None
    assert r.usage_total_tokens is None
    # an error receipt is REJECTED by the gate.
    g = gate(r)
    assert g.admitted is False
    assert any("status_not_success" in x for x in g.reasons)


def test_native_finish_reason_not_normalized_away():
    # The whole point: grok's native "completed" survives even though the
    # canonical finish_reason is "stop". A normalize-away bug would lose it.
    _, r = _map_fixture(SUCCESS_FIXTURE)
    assert r.finish_reason == "stop"
    assert r.native_finish_reason == "completed"
    assert r.finish_reason != r.native_finish_reason


# ---------------------------------------------------------------------------
# DETERMINISM CONSTRUCTED: canonical content hash + sandbox config hash
# (punch-list item 4) -- both stable AND load-bearing.
# ---------------------------------------------------------------------------


def test_content_canonical_hash_stable_across_trailing_ws():
    # Same canonical content with DIFFERENT trailing whitespace -> SAME hash.
    h1 = content_canonical_hash("hello world", "stop", "stop")
    h2 = content_canonical_hash("hello world   \n", "stop", "stop")
    h3 = content_canonical_hash("hello world\t  ", "stop", "stop")
    assert h1 == h2 == h3


def test_content_canonical_hash_nfc_normalizes():
    # NFD vs NFC of the same grapheme ("é") canonicalize to the same hash.
    nfc = "café"          # é as a single code point
    nfd = "café"          # e + combining acute
    assert nfc != nfd
    assert canonicalize_content(nfc) == canonicalize_content(nfd)
    assert content_canonical_hash(nfc, "stop", "stop") == content_canonical_hash(nfd, "stop", "stop")


def test_content_canonical_hash_load_bearing_on_content():
    # DIFFERENT interior content -> DIFFERENT hash (the canonicalizer doesn't
    # collapse genuinely different output).
    h1 = content_canonical_hash("answer A", "stop", "stop")
    h2 = content_canonical_hash("answer B", "stop", "stop")
    assert h1 != h2


def test_content_canonical_hash_load_bearing_on_finish_reason():
    # Same content, DIFFERENT finish reason -> DIFFERENT hash.
    h_stop = content_canonical_hash("partial", "stop", "completed")
    h_length = content_canonical_hash("partial", "length", "max_output_tokens")
    assert h_stop != h_length


def test_sandbox_config_hash_load_bearing_on_config():
    # DIFFERENT generation config -> DIFFERENT sandbox_config_hash.
    base = dict(
        model_resolved="x-ai/grok-4.3-20260430",
        temperature=0.0, max_tokens=12, effort=None,
        system_prompt="you are helpful", tools=None,
        endpoint="https://openrouter.ai/api/v1/chat/completions",
    )
    h0 = sandbox_config_hash(**base)
    h_temp = sandbox_config_hash(**{**base, "temperature": 0.7})
    h_max = sandbox_config_hash(**{**base, "max_tokens": 4096})
    h_sys = sandbox_config_hash(**{**base, "system_prompt": "different"})
    h_model = sandbox_config_hash(**{**base, "model_resolved": "x-ai/grok-4.3-20260101"})
    assert len({h0, h_temp, h_max, h_sys, h_model}) == 5  # all distinct
    # ...and identical config -> identical hash (stable).
    assert sandbox_config_hash(**base) == h0


# ---------------------------------------------------------------------------
# Cross-family reconciliation: load a REAL on-disk system_v7 sim_result receipt
# and assert the harness's NEW key (gate_ceiling_rung) does not conflict with
# the family's free-text claim_ceiling (punch-list item 5).
# ---------------------------------------------------------------------------


REAL_SIM_RESULT = (
    ROOT / "system_v7" / "sims" / "quantum_hopfield_qca_entropy_information_v0"
    / "results" / "quantum_hopfield_qca_entropy_information_v0_exact_results.json"
)


def test_real_cross_family_receipt_no_key_conflict():
    assert REAL_SIM_RESULT.is_file(), f"expected real sim_result at {REAL_SIM_RESULT}"
    family = json.loads(REAL_SIM_RESULT.read_text())
    assert family["schema"] == "codex_ratchet.sim_result.v1"
    # The family receipt carries claim_ceiling as FREE TEXT (a prose scope sentence),
    # exactly the meaning the harness now preserves -- not a ladder rung.
    assert isinstance(family["claim_ceiling"], str)
    assert " " in family["claim_ceiling"]  # it's prose, not an enum token
    # The harness's NEW promotion field does NOT exist on the family receipt, so
    # adding it introduces NO conflict (no shared key changes meaning).
    assert "gate_ceiling_rung" not in family
    # And the harness gate, if it ever saw this family claim_ceiling as a rung,
    # would NOT crash: a free-text claim_ceiling is just data; only
    # gate_ceiling_rung is ranked. Build a harness receipt that REUSES the
    # family's free-text claim_ceiling and confirm the gate ranks the rung only.
    receipt = ModelReceipt(
        task_id="reuse-family-ceiling",
        role="builder",
        provider="fake_success",
        launch_surface="fake",
        model_requested="offline-fake",
        prompt_sha256="deadbeef",
        input_refs=[],
        output_path=None,
        artifact_paths=[],
        status="success",
        returncode=0,
        started_at=TS_START,
        completed_at=TS_END,
        claim_ceiling=family["claim_ceiling"],   # the real prose scope sentence
        gate_ceiling_rung="scratch_diagnostic",  # harness ladder rung
    )
    g = gate(receipt)
    assert g.admitted is True
    assert g.granted_rung == "scratch_diagnostic"
    # the prose ceiling round-tripped untouched.
    assert receipt.claim_ceiling == family["claim_ceiling"]


# ---------------------------------------------------------------------------
# ONE real OpenRouter call -- gated behind an env flag so the offline suite
# runs with no network. Verifies the live mapping populates the derived fields.
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.environ.get("RUN_OPENROUTER_LIVE") != "1" or not os.environ.get("OPENROUTER_API_KEY"),
    reason="live OpenRouter call gated behind RUN_OPENROUTER_LIVE=1 + OPENROUTER_API_KEY",
)
def test_openrouter_live_call_populates_fields(tmp_path):
    task = TaskSpec(task_id="live-grok", role="builder", prompt="Say the single word: ok")
    job = ModelJob(
        task=task, provider="openrouter", model="x-ai/grok-4.3",
        output_path=str(tmp_path / "live.out"), temperature=0, max_tokens=12,
        produced_by="agent-live",
    )
    r = run_job(
        job, OpenRouterProvider(), timeout=60,
        started_at=TS_START, completed_at=TS_END,
    )
    assert r.status == "success", f"live call status={r.status} err={r.error_body}"
    assert r.http_status == 200
    assert r.model_resolved and r.model_resolved != r.model_requested
    assert r.finish_reason in ("stop", "length", "tool_calls", "content_filter")
    assert r.native_finish_reason is not None
    assert r.usage_total_tokens is not None
    assert r.content_canonical_hash and len(r.content_canonical_hash) == 64
    assert r.sandbox_config_hash and len(r.sandbox_config_hash) == 64
    g = gate(r)
    assert g.admitted is True


# ---------------------------------------------------------------------------
# box-viii L1c: HMAC signing closes the receipt-forgery holes the real fleet found
# (produced_by was unsigned free text; receipts were hand-editable plaintext).
# ---------------------------------------------------------------------------
from llm_harness.signing import sign_payload, verify_payload  # noqa: E402


def _signed_work_and_auditor(tmp_path, work_author="agent-A", audit_author="agent-B"):
    wtask = _task(task_id="w", gate_ceiling_rung="canonical", audit_required=True)
    wjob = _job("fake_success", "offline-fake", tmp_path / "w.txt", task=wtask, produced_by=work_author)
    work = run_job(wjob, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)
    atask = _task(task_id="audit-w", role="auditor", input_refs=["w"])
    ajob = _job("fake_success", "offline-fake", tmp_path / "a.txt", task=atask, produced_by=audit_author)
    auditor = run_job(ajob, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)
    return work, auditor


def test_signing_signed_pair_promotes_control(tmp_path):
    work, auditor = _signed_work_and_auditor(tmp_path)
    g = gate(work, audit_receipts=[auditor])
    assert g.admitted is True and g.granted_rung == "canonical"


def test_signing_tampered_produced_by_breaks_promotion(tmp_path):
    # hand-edit produced_by AFTER signing -> the HMAC no longer matches -> cannot promote.
    work, auditor = _signed_work_and_auditor(tmp_path)
    work.produced_by = "agent-Z"
    g = gate(work, audit_receipts=[auditor])
    assert g.admitted is False and g.granted_rung == "scratch_diagnostic"


def test_signing_unsigned_auditor_does_not_satisfy(tmp_path):
    # a forged auditor with no valid signature cannot authorize a promotion.
    work, auditor = _signed_work_and_auditor(tmp_path)
    auditor.signature = None
    g = gate(work, audit_receipts=[auditor])
    assert g.admitted is False


def test_signing_transitive_invalid_auditor_does_not_satisfy(tmp_path):
    # an auditor receipt that is validly SIGNED but schema-INVALID must not satisfy (transitive).
    work, auditor = _signed_work_and_auditor(tmp_path)
    auditor.schema = "not.a.real.schema"
    auditor.signature = sign_payload(auditor.to_dict())  # re-sign: signature valid, schema still bad
    g = gate(work, audit_receipts=[auditor])
    assert g.admitted is False


def test_signing_trailing_space_author_not_distinct(tmp_path):
    # 'agent-A' vs 'agent-A ' must NOT count as two authors (normalized identity).
    work, auditor = _signed_work_and_auditor(tmp_path, work_author="agent-A", audit_author="agent-A ")
    g = gate(work, audit_receipts=[auditor])
    assert g.admitted is False


def test_adapter_and_gate_reject_forged_scratch_receipt(tmp_path):
    # box-viii L2: a forged SCRATCH-rung receipt must NOT reach the controller as PASS, AND the gate
    # must reject a tampered signature at the BASE path (not only on the promotion path).
    from llm_harness.controller_adapter import receipt_to_controller_drop
    job = _job("fake_success", "offline-fake", tmp_path / "s.txt",
               task=_task(task_id="s", gate_ceiling_rung="scratch_diagnostic"), produced_by="agent-A")
    receipt = run_job(job, FakeSuccessProvider(), started_at=TS_START, completed_at=TS_END)
    g = gate(receipt)
    drop = receipt_to_controller_drop(receipt, g, semantic_verdict="admit", admitted=g.admitted)
    assert drop["overall_pass"] is True  # signed scratch receipt -> PASS (control)

    receipt.produced_by = "agent-FORGED"  # tamper after signing -> signature no longer verifies
    g2 = gate(receipt)
    assert g2.admitted is False           # gate now rejects tampering at BASE (any rung)
    drop2 = receipt_to_controller_drop(receipt, g2, semantic_verdict="reject", admitted=g2.admitted)
    assert drop2["overall_pass"] is False and drop2["signature_verified"] is False

    receipt.signature = None              # unsigned receipt
    drop3 = receipt_to_controller_drop(receipt, gate(receipt), semantic_verdict="keep_scratch", admitted=True)
    assert drop3["overall_pass"] is False  # adapter will not PASS an unsigned receipt even if admitted=True


# ---------------------------------------------------------------------------
# EXECUTOR / NOTARY SPLIT (the real fleet flagged 3x: the executor must NOT be
# the notary).  notary.py is the ONLY signer; per-identity keys make
# author-distinctness for no-self-grading KEY-backed, not label-backed.
#
# Every test below is could-fail and carries a control proving it is not vacuous.
# ---------------------------------------------------------------------------
from llm_harness import Notary, KeyRegistry, key_id_for  # noqa: E402
from llm_harness import runner as _runner_mod  # noqa: E402
from llm_harness import orchestrator as _orch_mod  # noqa: E402


def _inject_producer_key(monkeypatch, identity, secret):
    """Pin a producer's per-identity key via the LLM_HARNESS_KEY_<KEYID> env override.

    Both the signing KeyRegistry and the verification KeyRegistry read this env var BEFORE disk, so
    the test's signer and the gate's verifier resolve the SAME per-identity key deterministically
    (no shared on-disk key dir needed).
    """
    kid = key_id_for(identity)
    monkeypatch.setenv("LLM_HARNESS_KEY_" + kid.upper(), secret)


def _isolated_notary(tmp_path, monkeypatch=None, producers=None):
    """A Notary whose per-identity keys are pinned via env (shared with the verifier).

    ``producers`` maps identity -> secret string; each is injected as an env-pinned per-identity
    key so both signing and verification resolve it.  A tmp key_dir is still passed so any
    non-pinned producer mints under tmp (never the real key dir).
    """
    if monkeypatch is not None and producers:
        for ident, secret in producers.items():
            _inject_producer_key(monkeypatch, ident, secret)
    return Notary(registry=KeyRegistry(key_dir=tmp_path / "keys"))


def _unsigned_observation(task_id="obs", produced_by="agent-A"):
    """A well-formed UNSIGNED execution record (what the executor hands the notary)."""
    return ModelReceipt(
        task_id=task_id, role="builder", provider="fake_success", launch_surface="fake",
        model_requested="m", prompt_sha256="x", input_refs=[], output_path=None,
        artifact_paths=[], status="success", returncode=0,
        started_at=TS_START, completed_at=TS_END, produced_by=produced_by,
    )


# --- (1) orchestrator-cannot-sign: no signing-key capability on the executor path -----------


def test_executor_modules_have_no_signing_key_capability(tmp_path):
    """The runner and orchestrator (which handle UNTRUSTED model output) must NOT expose a
    signing-key capability -- no ``get_key`` / ``sign_payload`` in their namespaces.  They may hold
    the read-only ``verify_payload`` (verification mints nothing).

    Could fail: if the runner re-imported ``sign_payload`` (the pre-split inline-signing code), or
    if either module imported ``get_key``, these asserts would fire.
    """
    for mod in (_runner_mod, _orch_mod):
        assert not hasattr(mod, "sign_payload"), f"{mod.__name__} must not import the signer"
        assert not hasattr(mod, "get_key"), f"{mod.__name__} must not import the key source"
    # CONTROL: the notary module DOES hold the signing capability (so the absence above is a real
    # boundary, not that the capability vanished everywhere).
    import llm_harness.notary as _notary_mod
    assert hasattr(_notary_mod, "KeyRegistry")  # the secret store lives in the notary, not the executor


def test_untrusted_content_cannot_mint_signature_only_notary_can(tmp_path, monkeypatch):
    """The provider's UNTRUSTED captured content cannot produce a valid signature on its own; only
    the notary (after its well-formedness + registered-producer check) can.

    We build a receipt whose CONTENT is attacker-controlled, then show: (a) before notarization it
    is unsigned and does NOT verify; (b) only the notary turns it into a verifying receipt; (c) a
    SECOND hand-edit of the content after notarization breaks the signature again (the executor has
    no key to re-sign with).

    Could fail: if any executor path could re-sign, (c) would still verify.
    """
    nt = _isolated_notary(tmp_path, monkeypatch, {"agent-A": "key-A-secret-0123456789abcdef"})
    obs = _unsigned_observation(task_id="untrusted")
    obs.content = "ATTACKER-CONTROLLED MODEL OUTPUT"
    # (a) unsigned -> does not verify
    assert verify_payload(obs.to_dict()) is False
    # (b) the notary is the ONLY thing that signs
    nt.register("agent-A")
    res = nt.notarize(obs)
    assert res.ok is True and obs.signature is not None
    assert verify_payload(obs.to_dict()) is True  # control: a real notarization verifies
    # (c) hand-edit the untrusted content again, no re-sign -> broken
    obs.content = "ATTACKER-CONTROLLED MODEL OUTPUT v2"
    assert verify_payload(obs.to_dict()) is False


# --- (2) forged observation rejected by notary ----------------------------------------------


def test_notary_rejects_forged_observations(tmp_path):
    """The notary refuses to sign anything that is not a well-formed UNSIGNED record from a
    registered producer.  Each rejection is isolated so the guard is load-bearing per clause; a
    baseline VALID observation is signed (control) so none of these is a dead path.
    """
    nt = _isolated_notary(tmp_path)
    nt.register("agent-A")

    # CONTROL: a well-formed unsigned record from a registered producer IS signed.
    ok = _unsigned_observation()
    res_ok = nt.notarize(ok)
    assert res_ok.ok is True and ok.signature is not None

    # forged #1: an ALREADY-signed blob is not an unsigned observation -> rejected.
    already = nt.notarize_dict({**_unsigned_observation().to_dict(), "signature": "deadbeef"})
    assert already.ok is False and "already_signed" in already.reason

    # forged #2: missing a required execution-record field -> rejected.
    missing = _unsigned_observation().to_dict()
    del missing["status"]
    res_missing = nt.notarize_dict({k: v for k, v in missing.items() if k != "signature"})
    assert res_missing.ok is False and "missing_required_field" in res_missing.reason

    # forged #3: no producer named -> rejected (cannot key-back an anonymous record).
    anon = _unsigned_observation(produced_by="").to_dict()
    res_anon = nt.notarize_dict({k: v for k, v in anon.items() if k != "signature"})
    assert res_anon.ok is False and "no_producer_named" in res_anon.reason

    # forged #4: a producer that was never registered -> rejected (the notary will not sign for an
    # unknown producer even if the record is well-formed).
    res_unreg = nt.notarize_dict(
        {k: v for k, v in _unsigned_observation(produced_by="agent-NEVER-REGISTERED").to_dict().items()
         if k != "signature"}
    )
    assert res_unreg.ok is False and "unregistered_producer" in res_unreg.reason


def test_notarized_receipt_carries_key_id_bound_by_signature(tmp_path, monkeypatch):
    """The notary stamps key_id, key_id is part of the canonical signable payload, and swapping the
    key_id after signing breaks verification (defended at TWO layers: the signature binds key_id,
    and the verifier's resolver rejects a key_id whose identity does not hash to it).

    Could fail: if the notary did not stamp key_id, or key_id were absent from the signable string,
    or the swap still verified.
    """
    from llm_harness.signing import canonical_signable, KEY_ID_KEY

    nt = _isolated_notary(tmp_path, monkeypatch, {"agent-A": "key-A-secret-0123456789abcdef"})
    nt.register("agent-A")
    obs = _unsigned_observation()
    nt.notarize(obs)
    assert obs.key_id == key_id_for("agent-A")
    # key_id is part of what the signature covers (the canonical signable string contains it).
    assert f'"{KEY_ID_KEY}": "{obs.key_id}"' in canonical_signable(obs.to_dict())
    assert verify_payload(obs.to_dict()) is True  # control
    obs.key_id = key_id_for("agent-B")  # swap key_id, do not re-sign
    assert verify_payload(obs.to_dict()) is False  # swap rejected (binding + resolver guard)


# --- (3)/(4) same-key auditor does NOT satisfy no-self-grading; different-key auditor does ----


def _signed_via_notary(nt, task_id, *, role="builder", produced_by, gate_ceiling_rung="scratch_diagnostic",
                       input_refs=None):
    r = ModelReceipt(
        task_id=task_id, role=role, provider="fake_success", launch_surface="fake",
        model_requested="m", prompt_sha256="x", input_refs=list(input_refs or []), output_path=None,
        artifact_paths=[], status="success", returncode=0,
        started_at=TS_START, completed_at=TS_END, produced_by=produced_by,
        gate_ceiling_rung=gate_ceiling_rung, audit_required=(gate_ceiling_rung != "scratch_diagnostic"),
    )
    nt.register(produced_by)
    nt.notarize(r)
    return r


_TWO_PRODUCERS = {"agent-A": "key-A-secret-0123456789abcdef", "agent-B": "key-B-secret-fedcba9876543210"}


def test_different_key_auditor_satisfies_no_self_grading(tmp_path, monkeypatch):
    """A work receipt signed under producer A's key, audited by a receipt signed under producer B's
    DISTINCT key, satisfies no-self-grading -> the gate promotes.  (control for the next test.)
    """
    nt = _isolated_notary(tmp_path, monkeypatch, _TWO_PRODUCERS)
    work = _signed_via_notary(nt, "work-x", produced_by="agent-A", gate_ceiling_rung="canonical")
    auditor = _signed_via_notary(
        nt, "audit-of-work-x", role="auditor", produced_by="agent-B", input_refs=["work-x"]
    )
    assert work.key_id != auditor.key_id  # DISTINCT producer keys (key-backed distinctness)
    g = gate(work, audit_receipts=[auditor])
    assert g.admitted is True and g.granted_rung == "canonical"


def test_same_key_auditor_does_not_satisfy_no_self_grading(tmp_path, monkeypatch):
    """A work receipt and an "auditor" receipt BOTH signed under the SAME producer (agent-A) key do
    NOT satisfy no-self-grading -- the same agent cannot self-promote by minting a fresh-task_id
    auditor receipt under its own key.  Both the key_id (same key -> same producer) and the label
    co-identify A; the different-key control test PROVES this is the only thing flipped.
    """
    nt = _isolated_notary(tmp_path, monkeypatch, _TWO_PRODUCERS)
    work = _signed_via_notary(nt, "work-y", produced_by="agent-A", gate_ceiling_rung="canonical")
    same_key_auditor = _signed_via_notary(
        nt, "audit-of-work-y", role="auditor", produced_by="agent-A", input_refs=["work-y"]
    )
    assert work.key_id == same_key_auditor.key_id  # SAME producer key -> not distinct
    g = gate(work, audit_receipts=[same_key_auditor])
    assert g.admitted is False and g.granted_rung == "scratch_diagnostic"


def test_gate_key_distinctness_clause_is_load_bearing():
    """ISOLATE the KEY-backed distinctness clause: with the LABEL clause satisfied (different
    produced_by) but the KEY_IDs identical, ``_producers_key_distinct`` is the clause that rejects.

    This proves key-distinctness is not redundant decoration: it fires independently of the label
    check.  Could fail: if the clause returned True for equal key_ids (label-only distinctness),
    the first assert would flip.
    """
    from llm_harness.gates import _producers_key_distinct

    class _R:  # minimal stand-in carrying just the two fields the clause reads
        def __init__(self, key_id, produced_by):
            self.key_id = key_id
            self.produced_by = produced_by

    # different LABELS, SAME key_id -> NOT key-distinct (the clause rejects despite distinct labels)
    assert _producers_key_distinct(_R("k_same", "agent-B"), _R("k_same", "agent-A")) is False
    # different key_ids -> key-distinct (control: the clause is not always-False)
    assert _producers_key_distinct(_R("k_b", "agent-B"), _R("k_a", "agent-A")) is True
    # legacy single-key receipts (no key_id on one side) -> clause is a no-op (label clause governs)
    assert _producers_key_distinct(_R(None, "agent-B"), _R("k_a", "agent-A")) is True


def test_relabeled_same_key_auditor_does_not_satisfy(tmp_path, monkeypatch):
    """Defence in depth: an auditor receipt signed under agent-A's key but whose ``produced_by``
    label is hand-edited to 'agent-B' AFTER signing does NOT satisfy -- the relabel breaks the
    signature (key_id still names A's key, produced_by now says B, so verification fails), so a
    label swap cannot fake a distinct producer.

    Could fail: if distinctness were label-only (the pre-split behaviour), the relabel would pass.
    """
    nt = _isolated_notary(tmp_path, monkeypatch, _TWO_PRODUCERS)
    work = _signed_via_notary(nt, "work-z", produced_by="agent-A", gate_ceiling_rung="canonical")
    auditor = _signed_via_notary(
        nt, "audit-of-work-z", role="auditor", produced_by="agent-A", input_refs=["work-z"]
    )
    auditor.produced_by = "agent-B"  # relabel to fake distinctness, do NOT re-notarize
    assert verify_payload(auditor.to_dict()) is False  # the relabel broke the signature
    g = gate(work, audit_receipts=[auditor])
    assert g.admitted is False  # an invalidly-signed auditor cannot authorize promotion
