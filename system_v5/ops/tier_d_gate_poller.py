#!/usr/bin/env python3
import datetime as dt
import glob
import os
import pathlib
import re
import subprocess
import sys
import time

REPO = pathlib.Path('/Users/joshuaeisenhart/Desktop/Codex Ratchet')
WIKI = pathlib.Path('/Users/joshuaeisenhart/wiki/projects/codex-ratchet')
TIER_B = WIKI / 'tier_b.md'
TIER_D = WIKI / 'tier_d.md'
PROMPT = REPO / 'ops' / 'tier_d_launch_prompt.md'
LOG = WIKI / 'tier_d_gate_poller.log'
LAUNCH_LOG = WIKI / 'tier_d_launch_session.log'
POLL_SECONDS = 600


def ts() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec='seconds')


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(f'[{ts()}] {msg}\n')


def steward_cycle_end(status: str) -> None:
    steward_log = WIKI / '_steward_log.md'
    with steward_log.open('a', encoding='utf-8') as f:
        f.write(f"{ts()} tier_d_gate_poller tier_d cycle_end status={status}\n")


def tier_b_gate_green() -> bool:
    if not TIER_B.exists():
        return False
    text = TIER_B.read_text(encoding='utf-8', errors='replace')
    patterns = [
        r'^Gate:\s*green\s*$',
        r'^##\s*Status:\s*GREEN\b',
        r'Tier B gate PASSES',
        r'Tier D is cleared to auto-launch',
    ]
    return any(re.search(p, text, flags=re.MULTILINE | re.IGNORECASE) is not None for p in patterns)


def tier_b_layer_files_exist() -> bool:
    files = [p for p in glob.glob(str(WIKI / 'tier_b_*.md')) if not p.endswith('tier_b_spawn_plan.md')]
    return len(files) >= 5 or tier_b_gate_green()


def tier_d_already_owned() -> bool:
    if not TIER_D.exists():
        return False
    text = TIER_D.read_text(encoding='utf-8', errors='replace').lower()
    markers = ['status: in_progress', 'status: gate passed', 'gate: green', 'status: blocker']
    return any(m in text for m in markers)


def launch_tier_d() -> int:
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
            if tier_d_already_owned():
                log('tier_d.md already indicates active or terminal state; exiting poller')
                return 0
            green = tier_b_gate_green()
            layers = tier_b_layer_files_exist()
            if green and layers:
                log('Tier B gate green and 5 layer files present; launching Tier D session')
                code = launch_tier_d()
                log(f'Tier D launch session returned code={code}')
                if code == 0 or tier_d_already_owned():
                    return 0
                steward_cycle_end('polling')
            else:
                steward_cycle_end('polling')
            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            log('poller interrupted')
            return 130
        except Exception as exc:
            log(f'unhandled error: {exc!r}')
            time.sleep(POLL_SECONDS)


if __name__ == '__main__':
    sys.exit(main())
