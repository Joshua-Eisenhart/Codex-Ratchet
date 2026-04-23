#!/usr/bin/env python3
import datetime as dt
import pathlib
import re
import subprocess
import sys
import time

REPO = pathlib.Path('/Users/joshuaeisenhart/Desktop/Codex Ratchet')
WIKI = pathlib.Path('/Users/joshuaeisenhart/wiki/projects/codex-ratchet')
TIER_A = WIKI / 'tier_a.md'
TIER_B = WIKI / 'tier_b.md'
PROMPT = REPO / 'ops' / 'tier_b_launch_prompt.md'
LOG = WIKI / 'tier_b_gate_poller.log'
LAUNCH_LOG = WIKI / 'tier_b_launch_session.log'
POLL_SECONDS = 600
IGNORE_PATTERNS = [
    re.compile(r'^system_v5/ops/queue_.*\.txt$'),
    re.compile(r'^system_v5/ops/sim_queue.*\.txt$'),
    re.compile(r'^system_v4/.*/sim_results/.*\.json$'),
    re.compile(r'^system_v4/a2_state/.*$'),
    re.compile(r'^system_v4/a2_state/audit_logs/.*$'),
    re.compile(r'^overnight_logs/.*$'),
]


def ts() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec='seconds')


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(f'[{ts()}] {msg}\n')


def steward_cycle_end(status: str) -> None:
    steward_log = WIKI / '_steward_log.md'
    with steward_log.open('a', encoding='utf-8') as f:
        f.write(f"{ts()} tier_b_gate_poller tier_b cycle_end status={status}\n")


def tier_a_gate_green() -> bool:
    if not TIER_A.exists():
        return False
    text = TIER_A.read_text(encoding='utf-8', errors='replace')
    return re.search(r'^Gate:\s*green\s*$', text, flags=re.MULTILINE | re.IGNORECASE) is not None


def runner_live() -> bool:
    proc = subprocess.run(['pgrep', '-f', 'system_v5/ops/sim_runner.sh'], cwd=str(REPO), capture_output=True, text=True)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def tier_b_already_owned() -> bool:
    if not TIER_B.exists():
        return False
    text = TIER_B.read_text(encoding='utf-8', errors='replace').lower()
    markers = ['status: in_progress', 'status: gate passed', 'gate: green']
    return any(m in text for m in markers)


def filtered_dirty_paths() -> list[str]:
    proc = subprocess.run(['git', 'status', '--short'], cwd=str(REPO), capture_output=True, text=True)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    remaining = []
    for line in lines:
        path = line[3:] if len(line) > 3 else line
        if any(p.match(path) for p in IGNORE_PATTERNS):
            continue
        remaining.append(line)
    return remaining


def scope_collision() -> bool:
    scope_file = pathlib.Path('/tmp/hermes_active_scopes.txt')
    if not scope_file.exists():
        return False
    text = scope_file.read_text(encoding='utf-8', errors='replace')
    for line in text.splitlines():
        if ':tier_b:' in line or 'system_v5/ops/queue_tier_b.txt' in line or 'tier_b*' in line:
            return True
    return False


def launch_tier_b() -> int:
    prompt = PROMPT.read_text(encoding='utf-8')
    cmd = [
        'hermes', 'chat', '-Q', '--yolo',
        '-s', 'harness-bootstrap,claude-code',
        '--source', 'tool',
        '-q', prompt,
    ]
    with LAUNCH_LOG.open('a', encoding='utf-8') as out:
        out.write(f'\n===== launch started {ts()} =====\n')
        out.flush()
        proc = subprocess.run(cmd, cwd=str(REPO), stdout=out, stderr=subprocess.STDOUT, text=True)
        out.write(f'===== launch exited {ts()} code={proc.returncode} =====\n')
        return proc.returncode


def main() -> int:
    log('poller started')
    while True:
        try:
            if tier_b_already_owned():
                log('tier_b.md already indicates active or terminal state; exiting poller')
                return 0
            if tier_a_gate_green() and runner_live():
                dirty = filtered_dirty_paths()
                if dirty:
                    log('Tier B launch blocked by filtered dirty paths: ' + ', '.join(dirty))
                    steward_cycle_end('polling')
                    return 1
                if scope_collision():
                    log('Tier B launch blocked by scope collision')
                    steward_cycle_end('polling')
                    return 1
                log('Tier A gate green and runner live; launching Tier B session')
                code = launch_tier_b()
                log(f'Tier B launch session returned code={code}')
                if code == 0 or tier_b_already_owned():
                    return 0
            steward_cycle_end('polling')
            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            log('poller interrupted')
            return 130
        except Exception as exc:
            log(f'unhandled error: {exc!r}')
            steward_cycle_end('polling')
            time.sleep(POLL_SECONDS)


if __name__ == '__main__':
    sys.exit(main())
