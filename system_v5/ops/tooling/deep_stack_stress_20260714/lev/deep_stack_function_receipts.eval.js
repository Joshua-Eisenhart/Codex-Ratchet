import { readFileSync } from 'node:fs';

const lane = 'system_v5/ops/tooling/deep_stack_stress_20260714';
const registry = `${lane}/registry/tool_roster_v1.json`;
const edges = `${lane}/registry/integration_edges_v1.json`;
const results = `${lane}/results`;
const runner =
  'system_v5/codex_skills/codex-ratchet-deep-stack-stress/scripts/run_deep_stack_stress.py';
const validator =
  'system_v5/codex_skills/codex-ratchet-deep-stack-stress/scripts/validate_deep_stack_receipt.py';
const python = '/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3';
const sandbox = '/usr/bin/sandbox-exec';
const offlineProfile = '(version 1) (allow default) (deny network*)';
const levRuntime = JSON.parse(readFileSync(new URL('./current_lev_runtime.json', import.meta.url), 'utf8'));
const runtimeString = (field) => {
  const value = levRuntime[field];
  if (typeof value !== 'string' || value.trim() === '') {
    throw new Error(`Lev runtime binding field ${field} must be a non-empty string.`);
  }
  return value;
};
const levRoot = runtimeString('root');
const levLauncher = runtimeString('launcher');
const levBranch = runtimeString('branch');
const levBin = runtimeString('executable');
const levCommit = runtimeString('commit');
const levTree = runtimeString('tree');
const levBinSha256 = runtimeString('executable_sha256');
const estate = `${results}/deep_stack_estate_lev.json`;
const verdict = `${results}/deep_stack_estate_lev_verdict.json`;
const levShortCommit = levCommit.slice(0, 9);
const finalRunId = `deep-stack-lev-${levShortCommit}`;
const seamReceipt = `${results}/lev_qit_bridge_seam_${levShortCommit}/receipt.json`;
const seamRequestedAt = '2026-07-16T00:00:00.000Z';

const exactCoverageProgram = `
import hashlib
import json
import re
import shlex
import sys
from collections import Counter
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_RAW_ROLES = {
    "python_core",
    "julia_core",
    "jl_tensorkit",
    "jl_pepskit",
    "jl_intervalarithmetic",
    "cross_tensor",
    "cross_dynamics",
}
REPRESENTATIVE_EXECUTION_MODES = {
    "direct_current_probe",
    "controller_invoked_nested_fixture",
    "isolated_disposable_projection",
}
REPRESENTATIVE_FIXTURE_CREDIT = "representative_consumer_only_not_seven_case_replacement"
MAPPED_TOOL_CLAIM_CEILING = (
    "One-to-one registry/source/output contract or exact structured artifact identity only; "
    "direct load-bearing API evidence remains in the raw four-case probe."
)

def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def command_signature(record):
    return (
        tuple(record["command"]),
        record["command_line"],
        record["exit_code"],
        record["timed_out"],
    )

def normalized_identity(value):
    return "".join(character for character in str(value).lower() if character.isalnum())

def structured_tool_identities(value):
    identities = set()
    scalar_keys = {"tool", "package", "target_tool", "tool_id"}
    list_keys = {"packages_used", "aligned_packages_load_bearing"}
    map_keys = {"TOOL_MANIFEST", "tool_manifest", "package_versions"}
    if isinstance(value, dict):
        for key, item in value.items():
            if key in scalar_keys and isinstance(item, str):
                identities.add(item)
            if key in list_keys and isinstance(item, list):
                identities.update(entry for entry in item if isinstance(entry, str))
            if key in map_keys and isinstance(item, dict):
                identities.update(str(entry) for entry in item)
            identities.update(structured_tool_identities(item))
    elif isinstance(value, list):
        for item in value:
            identities.update(structured_tool_identities(item))
    return sorted(identities)

def parsed_stdout_receipt(record):
    stdout = str(record.get("stdout") or "").strip()
    if not stdout:
        return None
    for candidate in [stdout, *reversed(stdout.splitlines())]:
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
    return None

def leaves(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from leaves(item)
    elif isinstance(value, list):
        for item in value:
            yield from leaves(item)
    else:
        yield value

def named_values(value, name):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == name:
                yield item
            yield from named_values(item, name)
    elif isinstance(value, list):
        for item in value:
            yield from named_values(item, name)

estate = json.load(open(sys.argv[1], encoding="utf-8"))
registry = json.load(open(sys.argv[2], encoding="utf-8"))
edges = json.load(open(sys.argv[3], encoding="utf-8"))
verdict = json.load(open(sys.argv[4], encoding="utf-8"))
registry_ids = [row["tool_id"] for row in registry["tools"]]
registry_by_id = {row["tool_id"]: row for row in registry["tools"]}
registry_source_tool_ids = {}
for row in registry["tools"]:
    if row.get("requires_deep_stress") is True:
        registry_source_tool_ids.setdefault(row["representative_sim"]["path"], []).append(row["tool_id"])
for source_tool_ids in registry_source_tool_ids.values():
    source_tool_ids.sort()
receipt_ids = [row["tool_id"] for row in estate["tool_receipts"]]
deep_stress_ids = [row["tool_id"] for row in registry["tools"] if row.get("requires_deep_stress") is True]
deep_stress_id_set = set(deep_stress_ids)
deep_stress_receipts = [row for row in estate["tool_receipts"] if row["tool_id"] in deep_stress_id_set]
required_buckets = set(registry["required_operational_buckets"])
required_operational_ids = [
    row["tool_id"]
    for row in registry["tools"]
    if row.get("requires_deep_stress") is True and row.get("bucket") in required_buckets
]
policy_receipts = [row for row in estate["tool_receipts"] if row["tool_id"] not in deep_stress_id_set]
edge_ids = [row["id"] for row in edges["edges"]]
edge_receipt_ids = [row["edge_id"] for row in estate["integration_edge_receipts"]]
edge_receipts_by_id = {row["edge_id"]: row for row in estate["integration_edge_receipts"]}
summary = estate["producer_summary"]
raw_refs = [value for value in leaves(estate["raw_receipts"]) if isinstance(value, str)]
raw_bindings = estate["raw_receipt_bindings"]
raw_reuse_values = list(named_values(estate, "raw_reuse_used"))
commands = estate["commands"]
representatives = [row["representative_sim"] for row in deep_stress_receipts]
registry_representative_sources = {
    row["representative_sim"]["path"]
    for row in registry["tools"]
    if row.get("requires_deep_stress") is True
}
receipt_representative_sources = {row["source_path"] for row in representatives}
assert estate["run_id"] == "${finalRunId}"
assert len(registry_ids) == 139
assert len(registry_ids) == len(set(registry_ids))
assert len(receipt_ids) == 139
assert len(receipt_ids) == len(set(receipt_ids))
assert set(receipt_ids) == set(registry_ids)
assert len(deep_stress_ids) == 95
assert len(deep_stress_id_set) == 95
assert len(deep_stress_receipts) == 95
assert all(row["verdict"]["operational_pass"] is True for row in deep_stress_receipts)
assert len(required_operational_ids) == 86
assert len(set(required_operational_ids)) == 86
assert len(policy_receipts) == 44
assert all(row["policy_check"]["passed"] is True for row in policy_receipts)
assert all(row["verdict"]["operational_status"] == "policy_passed" for row in policy_receipts)
assert len(edge_ids) == 29
assert len(edge_ids) == len(set(edge_ids))
assert len(edge_receipt_ids) == 29
assert len(edge_receipt_ids) == len(set(edge_receipt_ids))
assert set(edge_receipt_ids) == set(edge_ids)
assert all(row["verdict"]["operational_pass"] is True for row in estate["integration_edge_receipts"])
assert Counter(row["evidence_kind"] for row in estate["integration_edge_receipts"]) == {
    "member_cohealth_compatibility_witness": 25,
    "independent_shared_crosscheck": 3,
    "direct_value_handoff": 1,
}
independent_edges = {"cross_tensor", "cross_dynamics", "cross_proof"}
direct_edges = {"cross_jax_torch"}
for edge_id, edge_receipt in edge_receipts_by_id.items():
    if edge_id in independent_edges:
        assert edge_receipt["evidence_kind"] == "independent_shared_crosscheck"
        assert edge_receipt["witness_mode"] in {
            "independent_shared_obligation_crosscheck",
            "independent_shared_fixture_crosscheck",
        }
    elif edge_id in direct_edges:
        assert edge_receipt["evidence_kind"] == "direct_value_handoff"
        assert edge_receipt["witness_mode"] == "direct_value_handoff"
    else:
        assert edge_receipt["evidence_kind"] == "member_cohealth_compatibility_witness"
        assert edge_receipt["witness_mode"] == "executed_member_case_conjunction"
        assert "does not assert a direct inter-member value handoff" in edge_receipt["exchange_claim_ceiling"]
assert summary["deep_stress_tool_count"] == 95
assert summary["operational_pass_count"] == 95
assert summary["operational_red_count"] == 0
assert summary["operational_red_tools"] == []
assert summary["integration_edge_count"] == 29
assert summary["operational_red_edge_count"] == 0
assert summary["operational_red_edges"] == []
assert verdict["receipt_valid"] is True
assert verdict["operational_pass"] is True
assert verdict["release_eligible"] is False
assert verdict["projection_only"] is True
assert verdict["scientific_claim_proven"] is False
assert verdict["summary"]["registry_tool_count"] == 139
assert verdict["summary"]["receipt_tool_count"] == 139
assert verdict["summary"]["required_operational_count"] == 86
assert verdict["summary"]["operational_pass_count"] == 86
assert verdict["summary"]["operational_red_count"] == 0
assert verdict["summary"]["policy_red_count"] == 0
assert verdict["summary"]["integration_edge_count"] == 29
assert verdict["summary"]["integration_edge_red_count"] == 0
assert verdict["summary"]["raw_reuse_used"] is False
assert verdict["summary"]["reused_command_count"] == 0
assert verdict["summary"]["missing_raw_receipt_count"] == 0
assert verdict["summary"]["failed_command_count"] == 0
assert verdict["summary"]["accepted_scientific_red_command_count"] == 0
assert verdict["findings"] == []
assert verdict["per_tool_findings"] == {}
assert verdict["operational_red_tools"] == []
assert verdict["policy_red_tools"] == []
assert verdict["operational_red_edges"] == []
assert verdict["missing_raw_receipt_roles"] == []
assert len(raw_refs) == 7
assert len(set(raw_refs)) == 7
assert all("/raw/${finalRunId}/" in "/" + value for value in raw_refs)
assert len(raw_bindings) == 7
assert {row["role"] for row in raw_bindings} == EXPECTED_RAW_ROLES
assert len({row["role"] for row in raw_bindings}) == 7
assert {row["path"] for row in raw_bindings} == set(raw_refs)
raw_producers_by_role = {
    role: [
        command
        for command in commands
        if command.get("role") == "raw_producer" and command.get("raw_role") == role
    ]
    for role in EXPECTED_RAW_ROLES
}
assert all(len(producers) == 1 for producers in raw_producers_by_role.values())
assert sum(command.get("role") == "raw_producer" for command in commands) == 7
for binding in raw_bindings:
    assert binding["exists"] is True
    assert SHA256.fullmatch(binding["sha256"])
    path = Path(binding["path"])
    path = path if path.is_absolute() else Path.cwd() / path
    assert path.is_file()
    assert sha256_file(path) == binding["sha256"]
    producer = raw_producers_by_role[binding["role"]][0]
    assert binding["producer_command_count"] == 1
    assert binding["producer_bound"] is True
    assert binding["producer_exit_code"] == 0
    assert binding["producer_timed_out"] is False
    assert binding["producer_output_path"] == binding["path"] == producer["output_path"]
    assert binding["producer_output_sha256"] == binding["sha256"] == producer["output_sha256"]
    assert binding["producer_output_created_after_explicit_unlink"] is True
    assert producer["output_created_after_explicit_unlink"] is True
    assert binding["producer_output_boundary_cleared_before_execution"] is True
    assert producer["output_boundary_cleared_before_execution"] is True
    assert "preexisting_output_removed" in producer
    assert producer["output_exists"] is True
    assert binding["producer_invoked_source_path"] == producer["invoked_source_path"]
    assert binding["producer_invoked_source_sha256"] == producer["invoked_source_sha256"]
    assert binding["producer_invoked_source_argument_present"] is True
    assert producer["invoked_source_argument_present"] is True
    assert producer["invoked_source_argument"] in producer["command"]
    invoked_source = Path(producer["invoked_source_path"])
    invoked_source = invoked_source if invoked_source.is_absolute() else Path.cwd() / invoked_source
    assert invoked_source.is_file()
    assert sha256_file(invoked_source) == producer["invoked_source_sha256"]
assert estate["raw_reuse_used"] is False
assert summary["raw_reuse_used"] is False
assert raw_reuse_values
assert all(value is False for value in raw_reuse_values)
assert len(commands) >= 10
for command in commands:
    assert isinstance(command, dict)
    assert "reused_raw" not in command
    assert isinstance(command.get("command"), list) and command["command"]
    assert all(isinstance(part, str) and part for part in command["command"])
    assert command.get("command_line") == shlex.join(command["command"])
    assert "--reuse-raw" not in command["command"]
    assert "--reuse-raw" not in command["command_line"]
    assert command.get("exit_code") == 0
    assert command.get("timed_out") is False
    launcher = Path(command["process_launcher_path"])
    assert launcher.is_file()
    assert command["process_launcher_realpath"] == str(launcher.resolve())
    assert command["process_launcher_sha256"] == sha256_file(launcher)
    assert command["process_launcher_realpath_sha256"] == sha256_file(launcher.resolve())
assert len(representatives) == 95
assert len(registry_representative_sources) == 48
assert receipt_representative_sources == registry_representative_sources
representative_command_signatures = set()
mapped_tool_evidence_pass_count = 0
for receipt in deep_stress_receipts:
    representative = receipt["representative_sim"]
    assert representative["source_path"] == registry_by_id[receipt["tool_id"]]["representative_sim"]["path"]
    assert representative["source_path"] in registry_representative_sources
    assert SHA256.fullmatch(representative["source_sha256"])
    source_path = Path(representative["source_path"])
    source_path = source_path if source_path.is_absolute() else Path.cwd() / source_path
    assert source_path.is_file()
    assert sha256_file(source_path) == representative["source_sha256"]
    assert isinstance(representative["execution_source_path"], str) and representative["execution_source_path"]
    assert SHA256.fullmatch(representative["execution_source_sha256"])
    execution_source_path = Path(representative["execution_source_path"])
    execution_source_path = (
        execution_source_path
        if execution_source_path.is_absolute()
        else Path.cwd() / execution_source_path
    )
    assert execution_source_path.is_file()
    assert sha256_file(execution_source_path) == representative["execution_source_sha256"]
    assert isinstance(representative["source_rewrites"], list)
    if representative["source_rewrites"]:
        assert representative["execution_mode"] == "isolated_disposable_projection"
        assert representative["execution_source_sha256"] != representative["source_sha256"]
        for rewrite in representative["source_rewrites"]:
            assert rewrite["kind"] == "disposable_projection_root_rewrite"
            assert rewrite["original"] == "/Users/joshuaeisenhart/Codex-Ratchet"
            assert isinstance(rewrite["replacement"], str) and rewrite["replacement"]
            assert rewrite["scope"] == "temporary execution copy only"
    else:
        assert representative["execution_source_sha256"] == representative["source_sha256"]
    assert representative["executed"] is True
    assert representative["execution_mode"] in REPRESENTATIVE_EXECUTION_MODES
    assert isinstance(representative["command"], list) and representative["command"]
    assert all(isinstance(part, str) and part for part in representative["command"])
    assert representative["command_line"] == shlex.join(representative["command"])
    assert "--reuse-raw" not in representative["command"]
    assert "--reuse-raw" not in representative["command_line"]
    assert representative["exit_code"] == 0
    assert representative["timed_out"] is False
    signature = command_signature(representative)
    matches = [command for command in commands if command_signature(command) == signature]
    assert matches
    representative_command_signatures.add(signature)
    if representative["execution_mode"] == "isolated_disposable_projection":
        assert any(command.get("role") == "representative_sim" for command in matches)
    assert isinstance(representative["invoked_source_path"], str) and representative["invoked_source_path"]
    assert representative["invoked_source_argument"] in representative["command"]
    assert representative["invoked_source_argument_present"] is True
    assert SHA256.fullmatch(representative["invoked_source_sha256"])
    for match in matches:
        assert match["invoked_source_path"] == representative["invoked_source_path"]
        assert match["invoked_source_argument"] == representative["invoked_source_argument"]
        assert match["invoked_source_sha256"] == representative["invoked_source_sha256"]
        assert match["invoked_source_argument_present"] is True
    assert representative["operational_execution_pass"] is True
    assert representative["passed"] is representative["operational_execution_pass"]
    assert representative["api_failure_signals"] == []
    assert isinstance(representative["stdout_nonempty"], bool)
    assert all(
        representative["stdout_nonempty"] is bool(str(command.get("stdout") or "").strip())
        for command in matches
    )
    assert all(representative["stdout_receipt"] == parsed_stdout_receipt(command) for command in matches)
    assert isinstance(representative["emitted_artifacts"], list)
    assert representative["emitted_artifacts"]
    artifact_payloads = []
    artifact_paths = []
    for artifact in representative["emitted_artifacts"]:
        assert isinstance(artifact.get("path"), str) and artifact["path"]
        assert SHA256.fullmatch(artifact["sha256"])
        assert artifact["exists"] is True
        assert artifact["changed_or_created"] is True
        assert artifact["created_after_explicit_unlink"] is True
        artifact_path = Path(artifact["path"])
        artifact_paths.append(artifact["path"])
        artifact_path = artifact_path if artifact_path.is_absolute() else Path.cwd() / artifact_path
        assert artifact_path.is_file()
        assert sha256_file(artifact_path) == artifact["sha256"]
        assert isinstance(artifact["size"], int) and artifact["size"] == artifact_path.stat().st_size
        if artifact_path.suffix.lower() in {".json", ".jsonl"}:
            assert artifact["json_object_parsed"] is True
            try:
                artifact_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                artifact_payload = None
            if isinstance(artifact_payload, dict):
                artifact_payloads.append(artifact_payload)
    output_contracts = representative["output_contract_paths"]
    assert isinstance(output_contracts, list) and output_contracts
    assert len(output_contracts) == len(set(output_contracts))
    assert representative["emitted_output_contract_paths"] == sorted(output_contracts)
    assert representative["output_contract_exact"] is True
    assert len(representative["emitted_artifacts"]) == len(output_contracts)
    if representative["execution_mode"] == "isolated_disposable_projection":
        assert sorted(artifact["projection_path"] for artifact in representative["emitted_artifacts"]) == sorted(output_contracts)
        assert representative["invoked_source_sha256"] == representative["execution_source_sha256"]
        assert representative["invoked_source_matches_preserved"] is True
        assert representative["output_contract_boundary_cleared_before_execution"] is True
        for match in matches:
            assert match["output_contract_paths"] == output_contracts
            assert match["emitted_output_contract_paths"] == sorted(output_contracts)
            assert match["output_contract_exact"] is True
            assert match["outputs_created_after_explicit_unlink"] is True
            assert match["invoked_source_matches_preserved"] is True
    else:
        assert artifact_paths == output_contracts
        assert set(artifact_paths).issubset(set(raw_refs))
        assert any(
            match.get("output_path") in artifact_paths
            and match.get("output_created_after_explicit_unlink") is True
            and match.get("output_boundary_cleared_before_execution") is True
            for match in matches
        )
    assert isinstance(representative["reported_scientific_status"], dict)
    assert representative["reported_scientific_status"].get("state") in {"green", "red", "unknown"}
    assert representative["scientific_status_preserved"] is True
    assert representative["promotion_allowed"] is False
    assert representative["scientific_claim_proven"] is False
    assert isinstance(representative["mapped_tool_ids"], list) and receipt["tool_id"] in representative["mapped_tool_ids"]
    assert representative["mapped_tool_ids"] == sorted(set(representative["mapped_tool_ids"]))
    assert representative["tool_id"] == receipt["tool_id"]
    mapping = representative["mapped_tool_evidence"]
    expected_aliases = sorted({
        str(value)
        for value in (
            registry_by_id[receipt["tool_id"]].get("package"),
            registry_by_id[receipt["tool_id"]].get("import_name"),
            receipt["tool_id"].removeprefix("py_").removeprefix("jl_"),
        )
        if isinstance(value, str) and value
    })
    structured_identities = structured_tool_identities(artifact_payloads)
    if representative["stdout_receipt"] is not None:
        structured_identities = sorted(
            set(structured_identities) | set(structured_tool_identities(representative["stdout_receipt"]))
        )
    normalized_aliases = {normalized_identity(alias) for alias in expected_aliases}
    matched_identities = [
        identity
        for identity in structured_identities
        if normalized_identity(identity) in normalized_aliases
    ]
    expected_source_tool_ids = registry_source_tool_ids[representative["source_path"]]
    single_tool_source_contract = len(expected_source_tool_ids) == 1
    expected_mode = (
        "registry_single_tool_source_contract"
        if single_tool_source_contract
        else "structured_artifact_tool_identity"
    )
    expected_mapping_pass = single_tool_source_contract or bool(matched_identities)
    assert mapping == {
        "mode": expected_mode,
        "registry_tool_ids_for_source": expected_source_tool_ids,
        "registry_aliases": expected_aliases,
        "structured_artifact_identities": structured_identities,
        "matched_structured_identities": matched_identities,
        "passed": expected_mapping_pass,
        "claim_ceiling": MAPPED_TOOL_CLAIM_CEILING,
    }
    assert expected_mapping_pass is True
    mapped_tool_evidence_pass_count += 1
    assert representative["source_family"] in {
        "ratchet_repo_current_probe",
        "ratchet_repo_representative_consumer",
        "frozen_claude_fixture_untrusted",
    }
    if "claude_campaign_20260713" in representative["source_path"]:
        assert representative["source_family"] == "frozen_claude_fixture_untrusted"
    if representative["execution_mode"] == "controller_invoked_nested_fixture":
        assert isinstance(representative.get("nested_controller_path"), str)
        nested_controller_path = Path(representative["nested_controller_path"])
        nested_controller_path = (
            nested_controller_path
            if nested_controller_path.is_absolute()
            else Path.cwd() / nested_controller_path
        )
        assert nested_controller_path.is_file()
    assert representative["fixture_credit"] == REPRESENTATIVE_FIXTURE_CREDIT
for command in commands:
    signature = command_signature(command)
    if command.get("role") == "representative_sim":
        assert signature in representative_command_signatures
assert estate.get("claude_bridge_used") is False
assert estate.get("install_attempted") is False
assert estate.get("promotion_allowed") is False
assert estate.get("scientific_claim_proven") is False
assert estate.get("release_eligible") is False
print(json.dumps({
    "registry_tool_count": len(registry_ids),
    "receipt_tool_count": len(receipt_ids),
    "deep_stress_tool_count": len(deep_stress_receipts),
    "deep_stress_operational_pass_count": sum(row["verdict"]["operational_pass"] is True for row in deep_stress_receipts),
    "required_operational_count": len(required_operational_ids),
    "required_operational_pass_count": verdict["summary"]["operational_pass_count"],
    "policy_receipt_count": len(policy_receipts),
    "policy_red_count": verdict["summary"]["policy_red_count"],
    "operational_red_count": summary["operational_red_count"],
    "integration_edge_count": len(edge_ids),
    "integration_edge_operational_pass_count": sum(row["verdict"]["operational_pass"] is True for row in estate["integration_edge_receipts"]),
    "operational_red_edge_count": summary["operational_red_edge_count"],
    "edge_coverage_exact": True,
    "member_cohealth_edge_count": 25,
    "independent_crosscheck_edge_count": 3,
    "direct_handoff_edge_count": 1,
    "raw_receipt_binding_count": len(raw_bindings),
    "raw_producer_binding_exact": True,
    "reused_command_count": verdict["summary"]["reused_command_count"],
    "accepted_scientific_red_command_count": verdict["summary"]["accepted_scientific_red_command_count"],
    "all_command_exit_zero": True,
    "representative_receipt_count": len(representatives),
    "representative_unique_source_count": len(receipt_representative_sources),
    "mapped_tool_evidence_pass_count": mapped_tool_evidence_pass_count,
    "representative_execution_exact": True,
    "fresh_run_id": estate["run_id"],
    "raw_reuse_used": False,
    "claude_bridge_used": False,
    "install_attempted": False,
    "promotion_allowed": False,
    "scientific_claim_proven": False,
}, sort_keys=True))
`;

export const deepStackFunctionReceiptsEval = {
  id: 'codex-ratchet-deep-stack-function-receipts',
  target: './target.md',
  flowmind: './flow.yaml',
  fixtures: {
    lev_runtime: './current_lev_runtime.json',
    qit_bridge_seam_contract: './qit_bridge_seam_contract.json',
    qit_bridge_seam_runner: './qit_bridge_seam_runner.mjs',
  },
  greenChecks: [
    'the current Lev launcher, branch, commit, tree, clean tracked bytes, and executable hash match the tracked non-model runtime binding',
    'a fresh Codex QIT stream crosses the bound Lev sim-witness ingester and deterministic sensor with a complete non-promotional seam receipt',
    'the independent receipt validator passes its full authentic-plus-mutation selftest',
    'the parent runner processes every roster row and executes every required deep row under no-install and network-denied policy',
    'the estate contains exactly all 139 registry tool receipts without duplicates',
    'the fresh estate contains exactly 95 deep-stress tool receipts, all 95 pass operationally, and the required-bucket subset is exactly 86 of 86',
    'the fresh estate has exactly 25 member co-health edges, three independent shared cross-checks, and one direct value handoff, all operationally green',
    'all seven run-scoped raw roles have exactly one successful producer bound to the live path, hash, explicit output clearing, and invoked source',
    'every parent and representative command exits zero without timeout or raw reuse',
    'all 95 deep rows bind exact fresh output contracts and invoked sources across exactly 48 unique consumer sources',
    'all 95 representative rows carry exact structured mapped-tool evidence with no free-text or partial-name matching',
    'the independent schema-aware validator is finding-free and the final estate passes its strict operational gate',
    'the nested zero-execution control blocks instead of projecting a false green',
  ],
  redChecks: [
    'a scientific-red payload cannot excuse a nonzero exit, timeout, stale output, or API failure',
    'a missing, duplicate, extra, stale-hash, import-only, or promotion-bearing receipt blocks validation',
    'file existence or a deep-fixture pass without an exact representative command record, artifact-or-stdout receipt, API-failure scan, and source-hash binding cannot satisfy representative execution',
    'Claude bridge use is forbidden and must remain false in the estate',
    'package installation, model adapters, provider calls, and network access are outside this eval lane',
    'integration diagnostics and Lev projection cannot prove a Ratchet or QIT scientific claim',
  ],
  commandCases: [
    {
      id: 'verify-codex-ratchet-tracked-bytes-clean',
      command: '/usr/bin/git',
      argv: ['diff', '--quiet', 'HEAD', '--'],
      expectedExit: 'zero',
    },
    {
      id: 'verify-bound-global-lev-launcher',
      command: '/usr/bin/readlink',
      argv: [levLauncher],
      expectedExit: 'zero',
      stdoutContains: levBin,
    },
    {
      id: 'verify-bound-lev-executor-branch',
      command: '/usr/bin/git',
      argv: ['-C', levRoot, 'rev-parse', '--abbrev-ref', 'HEAD'],
      expectedExit: 'zero',
      stdoutContains: levBranch,
    },
    {
      id: 'verify-bound-lev-executor-head',
      command: '/usr/bin/git',
      argv: ['-C', levRoot, 'rev-parse', 'HEAD'],
      expectedExit: 'zero',
      stdoutContains: levCommit,
    },
    {
      id: 'verify-bound-lev-executor-tree',
      command: '/usr/bin/git',
      argv: ['-C', levRoot, 'rev-parse', 'HEAD^{tree}'],
      expectedExit: 'zero',
      stdoutContains: levTree,
    },
    {
      id: 'verify-bound-lev-tracked-bytes-clean',
      command: '/usr/bin/git',
      argv: ['-C', levRoot, 'diff', '--quiet', 'HEAD', '--'],
      expectedExit: 'zero',
    },
    {
      id: 'verify-bound-lev-executable-hash',
      command: '/usr/bin/shasum',
      argv: ['-a', '256', levBin],
      expectedExit: 'zero',
      stdoutContains: levBinSha256,
    },
    {
      id: 'execute-codex-to-lev-qit-bridge-seam',
      command: sandbox,
      argv: [
        '-p',
        offlineProfile,
        '/opt/homebrew/bin/bun',
        `${lane}/lev/qit_bridge_seam_runner.mjs`,
        '--repo-root',
        '.',
        '--lev-root',
        levRoot,
        '--python',
        python,
        '--out',
        seamReceipt,
        '--requested-at',
        seamRequestedAt,
      ],
      expectedExit: 'zero',
      stdoutContains: [
        '"schema": "codex_ratchet.lev_qit_bridge_seam_receipt.v1"',
        '"status": "pass"',
        '"all_pass": true',
        '"provider_tick_count": 14',
        '"sensor_decision": "pass"',
        '"negative_control": "stream_schema_mismatch"',
        '"promotion_allowed": false',
        '"release_eligible": false',
        '"scientific_claim_proven": false',
      ],
    },
    {
      id: 'run-independent-validator-selftest',
      command: sandbox,
      argv: [
        '-p',
        offlineProfile,
        python,
        '-B',
        validator,
        'selftest',
        '--out',
        `${results}/validator_selftest_lev.json`,
      ],
      expectedExit: 'zero',
      stdoutContains: [
        '"case_count": 14',
        '"passed_count": 14',
        '"all_pass": true',
      ],
    },
    {
      id: 'execute-deep-stack-parent-runner',
      command: sandbox,
      argv: [
        '-p',
        offlineProfile,
        python,
        '-B',
        runner,
        '--repo-root',
        '.',
        '--registry',
        registry,
        '--edges',
        edges,
        '--run-id',
        finalRunId,
        '--out',
        estate,
        '--no-install',
      ],
      expectedExit: 'zero',
    },
    {
      id: 'validate-deep-stack-estate-require-final-green',
      command: sandbox,
      argv: [
        '-p',
        offlineProfile,
        python,
        '-B',
        validator,
        'estate',
        '--receipt',
        estate,
        '--registry',
        registry,
        '--edges',
        edges,
        '--repo-root',
        '.',
        '--out',
        verdict,
        '--require-operational-pass',
      ],
      expectedExit: 'zero',
      stdoutContains: [
        '"receipt_valid": true',
        '"registry_tool_count": 139',
        '"receipt_tool_count": 139',
        '"required_operational_count": 86',
        '"operational_pass": true',
        '"operational_red_count": 0',
        '"policy_red_count": 0',
        '"integration_edge_red_count": 0',
        '"raw_reuse_used": false',
        '"reused_command_count": 0',
        '"accepted_scientific_red_command_count": 0',
        '"missing_raw_receipt_count": 0',
        '"failed_command_count": 0',
        '"release_eligible": false',
        '"projection_only": true',
        '"scientific_claim_proven": false',
      ],
    },
    {
      id: 'verify-exact-roster-edge-and-bridge-coverage',
      command: sandbox,
      argv: [
        '-p',
        offlineProfile,
        python,
        '-B',
        '-c',
        exactCoverageProgram,
        estate,
        registry,
        edges,
        verdict,
      ],
      expectedExit: 'zero',
      stdoutContains: [
        '"registry_tool_count": 139',
        '"receipt_tool_count": 139',
        '"deep_stress_tool_count": 95',
        '"deep_stress_operational_pass_count": 95',
        '"required_operational_count": 86',
        '"required_operational_pass_count": 86',
        '"policy_receipt_count": 44',
        '"policy_red_count": 0',
        '"operational_red_count": 0',
        '"integration_edge_count": 29',
        '"integration_edge_operational_pass_count": 29',
        '"operational_red_edge_count": 0',
        '"edge_coverage_exact": true',
        '"member_cohealth_edge_count": 25',
        '"independent_crosscheck_edge_count": 3',
        '"direct_handoff_edge_count": 1',
        '"raw_receipt_binding_count": 7',
        '"raw_producer_binding_exact": true',
        '"reused_command_count": 0',
        '"accepted_scientific_red_command_count": 0',
        '"all_command_exit_zero": true',
        '"representative_receipt_count": 95',
        '"representative_unique_source_count": 48',
        '"mapped_tool_evidence_pass_count": 95',
        '"representative_execution_exact": true',
        `"fresh_run_id": "${finalRunId}"`,
        '"raw_reuse_used": false',
        '"claude_bridge_used": false',
        '"install_attempted": false',
        '"promotion_allowed": false',
        '"scientific_claim_proven": false',
      ],
    },
    {
      id: 'lev-zero-execution-control-blocks',
      command: sandbox,
      argv: [
        '-p',
        offlineProfile,
        '/opt/homebrew/bin/bun',
        levBin,
        'eval',
        'run',
        `${lane}/lev/zero_execution.eval.js`,
        '--execute',
        '--json',
        '--project-root',
        '.',
        '--output-root',
        `${results}/lev_zero_runs`,
        '--run-id',
        `deep-stack-zero-${levShortCommit}`,
        '--timeout-ms',
        '60000',
      ],
      expectedExit: 'nonzero',
      stdoutContains: [
        'suite.execution.none',
        '"status": "blocked"',
        '"decision_verdict": "fail"',
        '"executed_count": 0',
        '"code": "EVAL_RUN_BLOCKED"',
      ],
    },
  ],
};

export default deepStackFunctionReceiptsEval;
