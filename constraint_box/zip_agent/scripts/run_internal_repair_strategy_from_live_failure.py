from __future__ import annotations

import json
from pathlib import Path
import sys
import zipfile

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet/constraint_box")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "zip_agent" / "src"))

from constraintbox_zip_agent.cli import _build_council_from_files
from constraintbox_zip_agent.protocol import sha256_bytes
from constraintbox_zip_agent.runtime import execute_packet

BASE = Path("/private/tmp/cb-three-wave-20260815")
BASE.mkdir(parents=True, exist_ok=True)
LIVE = Path("/private/tmp/cb-live-failure-20260815")
WIKI_MMM = Path("/Users/joshuaeisenhart/wiki/wizard/packet-v4-3-current/mmm/mini/compact/voices/md")
OWNER = BASE / "owner.md"
OWNER.write_text(
    "Target: CB ZIP pipeline: handshake -> confirm -> separate execute -> live failure -> repair -> strategy. "
    "Preserve failure, do not promote.\n",
    encoding="utf-8",
)

failure_packet = LIVE / "failure.live.zip"
failure_return = LIVE / "failure.live.return.zip"
if not failure_packet.is_file() or not failure_return.is_file():
    raise SystemExit("missing live failure packet/return")
failure_return_digest = sha256_bytes(failure_return.read_bytes())

SCRIPT_TEMPLATE = r'''
from pathlib import Path
import json, hashlib
agent_id = {agent_id!r}
prior_tokens = {prior_tokens!r}
Path('output').mkdir(exist_ok=True)
Path('meta').mkdir(exist_ok=True)
Path('meta/provider_evidence.json').write_text(
    json.dumps({{'schema':'constraintbox.fixture-provider-evidence.v1','disposition':'OBSERVED','model_observed':'fixture-observed'}}) + '\n',
    encoding='utf-8',
)
tool = json.loads(Path('output/tool_evidence.json').read_text(encoding='utf-8'))['canonical_sha256']
skill = hashlib.sha256(Path('SKILLS/council.md').read_bytes()).hexdigest()
manifest = json.loads(Path('input/council_manifest.json').read_text(encoding='utf-8'))
me = next(row for row in manifest['members'] if row['agent_id'] == agent_id)
mmm = ''.join('mmm-token: ' + digest + '\n' for digest in me['mmm_sha256'].values())
priors = ''.join('prior-return-token: ' + token + '\n' for token in prior_tokens)
Path(f'output/{{agent_id}}.md').write_text(
    f'finding: CB_COUNCIL_ZIP\n'
    f'council: {{agent_id}}\n'
    'support: observed\n'
    'evidence: bound prior return bytes present in packet\n'
    'limit: fixture repair/strategy worker; not live model execution\n'
    'falsifier: if bound prior digest is missing or worker omits required token\n'
    'next: continue only as REQUEST_CONTEXT unless external lane accepts repair\n'
    'keep_or_discard: keep\n'
    'live_patch: false\n'
    'disposition: REQUEST_CONTEXT\n'
    f'tool-token: {{tool}}\n'
    f'skill-token: {{skill}}\n'
    + mmm + priors,
    encoding='utf-8',
)
'''

def config(path: Path, *, run_id: str, seed: int, members: tuple[str, ...], prior_tokens: list[str]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "constraintbox.internal-council-run.v1",
                "run_id": run_id,
                "seed": seed,
                "agents": [
                    {
                        "agent_id": member,
                        "provider": "fixture-subprocess",
                        "model_requested": "fixture-model",
                        "fixture_script": SCRIPT_TEMPLATE.format(agent_id=member, prior_tokens=prior_tokens),
                        "max_attempts": 1,
                        "timeout_seconds": 10,
                    }
                    for member in members
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

repair_cfg = BASE / "repair.run.json"
config(repair_cfg, run_id="repair-from-live-failure", seed=902, members=("smallest", "test", "ceiling"), prior_tokens=[failure_return_digest])
repair_packet = _build_council_from_files(
    owner_prompt=OWNER,
    run_config=repair_cfg,
    mmm_dir=WIKI_MMM,
    council_id="repair",
    failure_packet=failure_packet,
    failure_return=failure_return,
)
repair_packet_path = BASE / "repair.zip"
repair_return_path = BASE / "repair.return.zip"
repair_packet_path.write_bytes(repair_packet)
repair_result = execute_packet(repair_packet)
repair_return_path.write_bytes(repair_result.return_zip_bytes)
repair_return_digest = sha256_bytes(repair_result.return_zip_bytes)

strategy_cfg = BASE / "strategy.run.json"
config(strategy_cfg, run_id="strategy-from-live-failure-and-repair", seed=903, members=("systems_boundary", "object_preservation", "divergent_futures"), prior_tokens=[failure_return_digest, repair_return_digest])
strategy_packet = _build_council_from_files(
    owner_prompt=OWNER,
    run_config=strategy_cfg,
    mmm_dir=WIKI_MMM,
    council_id="strategy",
    failure_packet=failure_packet,
    failure_return=failure_return,
    repair_packet=repair_packet_path,
    repair_return=repair_return_path,
)
strategy_packet_path = BASE / "strategy.zip"
strategy_return_path = BASE / "strategy.return.zip"
strategy_packet_path.write_bytes(strategy_packet)
strategy_result = execute_packet(strategy_packet)
strategy_return_path.write_bytes(strategy_result.return_zip_bytes)
strategy_return_digest = sha256_bytes(strategy_result.return_zip_bytes)

summary = {
    "schema": "constraintbox.three-wave-internal-summary.v1",
    "base": str(BASE),
    "failure_packet_sha256": sha256_bytes(failure_packet.read_bytes()),
    "failure_return_sha256": failure_return_digest,
    "repair_packet_sha256": sha256_bytes(repair_packet),
    "repair_return_sha256": repair_return_digest,
    "strategy_packet_sha256": sha256_bytes(strategy_packet),
    "strategy_return_sha256": strategy_return_digest,
    "promotion_allowed": False,
    "claim_ceiling": "live failure return bound into fixture repair/strategy waves; not admission; not live repair models",
}
(BASE / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2, sort_keys=True))
