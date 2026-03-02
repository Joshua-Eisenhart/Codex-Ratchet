#!/usr/bin/env python3
"""
Local A1 LLM lane executor using Ollama (fail-closed).

Takes an A1_LLM_LANE_REQUEST zip (from a1_llm_lane_driver.py), runs a local
Ollama model once per prompt, and emits a role_outputs-only ZIP that can be
ingested by a1_llm_lane_driver.py --role-outputs-zip.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def _run_ollama(*, model: str, prompt_text: str, timeout_sec: int) -> str:
    # We rely on prompt instructions to force JSON-only output.
    cmd = [
        "ollama",
        "run",
        str(model),
        "--format",
        "json",
        "--think",
        "false",
        "--hidethinking",
        "--nowordwrap",
    ]
    p = subprocess.run(
        cmd,
        input=prompt_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=max(1, int(timeout_sec)),
        check=False,
    )
    out = str(p.stdout)
    # Ollama CLI may emit ANSI control sequences (spinners). Strip them.
    out = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", out)
    return out.strip()


def _ensure_json(text: str) -> dict:
    # Fail closed if not JSON. Try a best-effort extraction of the first JSON object.
    try:
        return json.loads(text)
    except Exception as e:
        s = text
        i = s.find("{")
        j = s.rfind("}")
        if 0 <= i < j:
            try:
                return json.loads(s[i : j + 1])
            except Exception:
                pass
        raise ValueError(f"model_output_not_json: {e}") from e


def _zip_dir(zip_path: Path, root_dir: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(root_dir.rglob("*")):
            if p.is_dir():
                continue
            zf.write(p, p.relative_to(root_dir))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run local Ollama over A1 lane prompts and emit role_outputs.zip.")
    ap.add_argument("--request-zip", required=True, help="Path to *_A1_LLM_LANE_REQUEST__v1.zip")
    ap.add_argument("--model", default="qwen3:8b")
    ap.add_argument("--timeout-sec", type=int, default=120)
    ap.add_argument("--out-zip", required=True, help="Where to write role_outputs-only zip.")
    ap.add_argument("--debug-dir", default="", help="If set, write raw model outputs here on failure.")
    args = ap.parse_args()

    request_zip = Path(args.request_zip).expanduser().resolve()
    out_zip = Path(args.out_zip).expanduser().resolve()
    debug_dir = Path(str(args.debug_dir)).expanduser().resolve() if str(args.debug_dir).strip() else None

    if not request_zip.exists():
        raise SystemExit(f"missing request zip: {request_zip}")

    with tempfile.TemporaryDirectory(prefix="a1_llm_lane_ollama_") as td:
        td_path = Path(td)
        with zipfile.ZipFile(str(request_zip), "r") as zf:
            zf.extractall(td_path)

        prompts_dir = td_path / "prompts"
        if not prompts_dir.exists():
            raise SystemExit("request zip missing prompts/ directory")

        role_out = td_path / "role_outputs"
        role_out.mkdir(parents=True, exist_ok=True)

        prompt_paths = sorted(prompts_dir.glob("*_A1_PROMPT.txt"))
        if not prompt_paths:
            raise SystemExit("no prompts found in request zip")

        for p in prompt_paths:
            prompt_text = p.read_text(encoding="utf-8")
            raw = _run_ollama(model=str(args.model), prompt_text=prompt_text, timeout_sec=int(args.timeout_sec))
            try:
                obj = _ensure_json(raw)
            except Exception:
                # Persist raw for debugging and fail closed.
                (role_out / (p.stem + "__RAW.txt")).write_text(raw + "\n", encoding="utf-8")
                if debug_dir:
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    (debug_dir / (p.stem + "__RAW.txt")).write_text(raw + "\n", encoding="utf-8")
                raise
            (role_out / (p.stem + ".json")).write_text(
                json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )

        # Emit a ZIP containing role_outputs/ only.
        tmp_root = td_path / "out_root"
        if tmp_root.exists():
            shutil.rmtree(tmp_root)
        tmp_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(role_out, tmp_root / "role_outputs")
        _zip_dir(out_zip, tmp_root)

    print(json.dumps({"status": "OK", "out_zip": str(out_zip)}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        raise SystemExit(130)
