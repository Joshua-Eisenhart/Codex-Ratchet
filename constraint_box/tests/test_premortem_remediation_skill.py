from __future__ import annotations

import pathlib

import pytest


CB = pathlib.Path(__file__).resolve().parents[1]
SKILL_PATH = CB / "skills" / "premortem-remediation" / "SKILL.md"

LINE_CEILING = 300

REQUIRED_TERMINALS = (
    "VERIFIED_DONE",
    "HOLD",
    "REFUSE",
    "EXHAUSTED",
    "PROPOSED_FOR_OWNER",
)

REQUIRED_BINDING_STATES = (
    "declared",
    "bound_reference",
    "invoked",
    "receipt_verified",
)

REQUIRED_HANDOFF_TYPES = (
    "ConcernRecord",
    "Issue",
    "IssueEvent",
    "ResolutionEvent",
    "ProducerBinding",
    "RepairCandidate",
    "RepairAction",
    "ActionApplication",
    "CandidateExclusion",
    "GateRun",
    "Receipt",
)

PROHIBITED_WEBUI_STRINGS = (
    "premortem-report",
    "browser-open",
    "browser_open",
    "<html",
    "report.html",
    "open the browser",
    "launch a webui",
    "start a web server",
)

RED_BASELINE_QUOTES = (
    "treat each prose finding as self-evident",
    "fix the first apparent symptom",
    "rely on a targeted green test, and stop after a clean rerun",
    "each council member returns ACCEPT, REJECT, or HOLD",
    "a repair council authorizes one bounded implementation action",
)


@pytest.fixture(scope="module")
def skill_lines() -> list[str]:
    assert SKILL_PATH.is_file(), f"missing skill contract: {SKILL_PATH}"
    return SKILL_PATH.read_text(encoding="utf-8").splitlines()


@pytest.fixture(scope="module")
def skill_text(skill_lines: list[str]) -> str:
    return "\n".join(skill_lines)


def _frontmatter(lines: list[str]) -> dict[str, str]:
    assert lines[0].strip() == "---", "SKILL.md must open with YAML frontmatter"
    end = lines.index("---", 1)
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def _section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start)
    return text[start:end]


def test_frontmatter_has_name_and_use_when_description(skill_lines: list[str]) -> None:
    fields = _frontmatter(skill_lines)
    assert fields.get("name") == "premortem-remediation"
    description = fields.get("description", "")
    assert description.startswith("Use when"), description


def test_line_ceiling(skill_lines: list[str]) -> None:
    assert len(skill_lines) <= LINE_CEILING, (
        f"SKILL.md is {len(skill_lines)} lines, ceiling is {LINE_CEILING}"
    )


def test_required_terminals_present(skill_text: str) -> None:
    for terminal in REQUIRED_TERMINALS:
        assert terminal in skill_text, f"missing terminal state: {terminal}"


def test_only_verified_done_means_done(skill_text: str) -> None:
    assert "VERIFIED_DONE" in skill_text
    assert (
        "No terminal other than VERIFIED_DONE means done" in skill_text
        or "None of these besides VERIFIED_DONE means done" in skill_text
    )


def test_required_binding_states_present(skill_text: str) -> None:
    for state in REQUIRED_BINDING_STATES:
        assert state in skill_text, f"missing M2M binding state: {state}"


def test_binding_reference_is_not_invocation(skill_text: str) -> None:
    assert "bound_reference is never an invocation" in skill_text.replace(
        "**A bound_reference is never an invocation.**",
        "A bound_reference is never an invocation.",
    )


def test_required_handoff_types_present(skill_text: str) -> None:
    for handoff_type in REQUIRED_HANDOFF_TYPES:
        assert handoff_type in skill_text, f"missing handoff type: {handoff_type}"


def test_producer_binding_is_m2m_and_not_candidate_state(skill_text: str) -> None:
    chain = _section(skill_text, "## Structured handoff chain", "## Operational steps")
    candidate = chain[chain.index("**RepairCandidate**") : chain.index("**RepairAction**")]
    solicitation = _section(skill_text, "### Step 3", "### Step 4")
    assert "**ProducerBinding**" in chain
    assert "(producer_id, issue_id)" in chain
    assert "binding_state" not in candidate
    assert "matching `ProducerBinding(producer_id, issue_id)`" in solicitation
    assert "matching\n  ProducerBinding is `receipt_verified`" in solicitation


def test_requires_declared_completion_gate(skill_text: str) -> None:
    assert "declared completion gate" in skill_text.lower() or (
        "completion_gate" in skill_text
    )
    assert "NO_DECLARED_COMPLETION_GATE" in skill_text
    assert "HOLD" in skill_text


def test_max_iteration_is_a_safety_bound_not_success(skill_text: str) -> None:
    lowered = skill_text.lower()
    assert "safety bound" in lowered
    assert "never counts as success" in lowered or "never claims success" in lowered


def test_no_numeric_bound_requires_complete_well_founded_stop_contract(
    skill_text: str,
) -> None:
    preconditions = _section(skill_text, "### Step 0", "### Step 1")
    for declaration in (
        "measure_id",
        "measure_domain",
        "terminal_value",
        "strict_per_retry_decrease=true",
    ):
        assert declaration in preconditions
    assert "With no numeric bound, all four measure declarations are required" in preconditions
    assert "NO_DECLARED_STOP_CRITERION" in preconditions
    assert "never an invented EXHAUSTED outcome" in preconditions
    assert (
        "no numeric bound is acceptable only with the declared well-founded measure; "
        "absent or insufficient stop policy is HOLD" in skill_text
    )


def test_second_action_requires_a_new_decreasing_repair_round(skill_text: str) -> None:
    promotion = _section(skill_text, "### Step 4", "### Step 5")
    assert "per `(issue_id, round_index)`" in promotion
    assert "round_index=0" in promotion
    assert "explicitly declared next `round_index`" in promotion
    assert "fresh pre-action GateRun" in promotion
    assert "strictly lower than the immediately" in promotion
    assert "SECOND_ACTION_WITHOUT_DECREASING_ROUND" in promotion


def test_failed_candidate_is_excluded_before_another_round(skill_text: str) -> None:
    rerun = _section(skill_text, "### Step 5", "### Step 6")
    assert "appends CandidateExclusion" in rerun
    assert "may not be promoted in a later round" in rerun
    assert rerun.index("CandidateExclusion") < rerun.index("Return to Step 3")


def test_aggregate_completion_requires_every_declared_regression_gate(
    skill_text: str,
) -> None:
    preconditions = _section(skill_text, "### Step 0", "### Step 1")
    rerun = _section(skill_text, "### Step 5", "### Step 6")
    completion = _section(skill_text, "### Step 6", "## Rationalization table")
    assert "required_regression_gates" in preconditions
    assert "every required regression gate PASS" in preconditions
    assert "Any required regression-gate FAIL makes the aggregate completion predicate\n  FAIL" in rerun
    assert "appends or retains an OPEN Issue" in rerun
    assert "every required regression gate PASSes" in completion
    assert "ResolutionEvents are appended" in completion


def test_refuse_precedes_hold_for_prohibited_authority_or_output(skill_text: str) -> None:
    preconditions = _section(skill_text, "### Step 0", "### Step 1")
    refuse_at = preconditions.index("PROHIBITED_OUTPUT_SURFACE")
    hold_at = preconditions.index("NO_DECLARED_COMPLETION_GATE")
    stop_hold_at = preconditions.index("NO_DECLARED_STOP_CRITERION")
    assert refuse_at < hold_at < stop_hold_at
    assert "does not become a lesser HOLD" in preconditions


def test_append_only_records_have_deterministic_receipt_custody(skill_text: str) -> None:
    chain = _section(skill_text, "## Structured handoff chain", "## Operational steps")
    for field in ("receipt_id", "run_id", "terminal", "supersedes", "emitted_by_gate_id"):
        assert field in chain
    assert "Neither event mutates an earlier Issue record" in chain
    assert "never edits the RepairAction" in chain
    assert "Only a deterministic\n   gate may emit or supersede a receipt" in chain


def test_unresolved_owner_proposal_blocks_verified_done(skill_text: str) -> None:
    classification = _section(skill_text, "### Step 2", "### Step 3")
    completion = _section(skill_text, "### Step 6", "## Rationalization table")
    assert "owner-routing record" in classification
    assert "terminal for the whole run and blocks VERIFIED_DONE" in classification
    assert "no Issue remains OPEN,\n  and no unresolved owner-routing record remains" in completion


def test_single_issue_runtime_profile_cannot_claim_multi_issue_completion(
    skill_text: str,
) -> None:
    boundary = _section(
        skill_text, "### Runtime profile boundary", "## Rationalization table"
    )
    assert "generic contract is for a sealed issue set" in boundary
    assert "declare and receipt `single_issue_run`" in boundary
    assert "only to that sealed one-Issue run" in boundary
    assert "never to project" in boundary
    assert "or multi-Issue completion" in boundary
    assert "`sealed_issue_set` artifact" in boundary


def test_forbids_authority_from_model_council_or_prose(skill_text: str) -> None:
    lowered = skill_text.lower()
    assert "non-authoritative" in lowered
    for phrase in (
        "vote",
        "verdict",
        "confidence",
        "consensus",
    ):
        assert phrase in lowered, f"missing coverage of forbidden authority signal: {phrase}"
    assert "never authority" in lowered or "never acted on as\nauthority" in skill_text or (
        "never act" in lowered
    )
    assert "councils cannot authorize" in lowered


def test_forbids_prose_findings_as_self_evident(skill_text: str) -> None:
    assert "Prose is not a ConcernRecord" in skill_text


def test_no_webui_or_report_output_convention(skill_text: str) -> None:
    lowered = skill_text.lower()
    for forbidden in PROHIBITED_WEBUI_STRINGS:
        assert forbidden.lower() not in lowered, (
            f"SKILL.md must not define a WebUI/report output convention: {forbidden!r} found"
        )


def test_states_no_webui_condition_explicitly(skill_text: str) -> None:
    lowered = skill_text.lower()
    assert "no html report" in lowered
    assert "opens a browser" in lowered or "browser open" in lowered
    assert "prohibited_output_surface" in lowered


def test_rationalization_table_has_red_baseline_quotes(skill_text: str) -> None:
    for quote in RED_BASELINE_QUOTES:
        assert quote in skill_text, f"missing RED baseline quote: {quote!r}"
    assert "20 iterations" in skill_text and "90 minutes" in skill_text


def test_rationalization_table_has_at_least_five_rows(skill_text: str) -> None:
    lines = skill_text.splitlines()
    start = next(
        i for i, line in enumerate(lines) if line.strip().startswith("## Rationalization table")
    )
    table_lines = [
        line
        for line in lines[start:]
        if line.strip().startswith("|") and not set(line.strip()) <= {"|", "-", " "}
    ]
    # First remaining pipe row is the header; the rest are data rows.
    data_rows = table_lines[1:]
    assert len(data_rows) >= 5, f"expected 5+ rationalization rows, found {len(data_rows)}"


def test_does_not_touch_runtime_source_or_config(skill_text: str) -> None:
    assert "does\nnot modify package source, configuration, receipts, or global skill" in (
        skill_text
    ) or "does not modify package source" in skill_text


def test_cb_light_independent_of_heavy_and_simulation(skill_text: str) -> None:
    assert "CB Heavy" in skill_text
    assert "simulation" in skill_text.lower()


def test_skill_directory_contains_only_the_contract() -> None:
    directory = SKILL_PATH.parent
    entries = sorted(p.name for p in directory.iterdir())
    assert entries == ["SKILL.md"], entries
