#!/usr/bin/env python3
"""Verify CB light-library candidates against the selection bar. Stdlib only.

Reads a registry JSON of candidate PyPI distribution names, fetches
https://pypi.org/pypi/<name>/json for each, and records real metadata:

  - exists on PyPI (404 -> drop)
  - latest version and the release date of that version
  - days since that release
  - requires_python, and whether 3.12 and 3.13 both satisfy it
  - platforms from the wheel filenames of the latest release:
      pure (py3-none-any) / linux / macos / windows / sdist-only
  - largest wheel size in bytes (the lean proxy)
  - declared runtime dependency count from requires_dist (non-extra markers)
  - a verdict against the selection bar

Selection bar (hard drop reasons):
  - nonexistent on PyPI
  - stale: latest release older than STALE_DAYS_MAX (~18 months)
  - no requires_python declared
  - requires_python excludes 3.12 or 3.13
  - not pure python and missing any of linux / macos / windows wheels
  - sdist only (no wheel at all)
  - more than MAX_DEPS declared non-extra runtime dependencies
  - largest wheel over MAX_WHEEL_BYTES (5 MB lean budget)

Network failure for one package never aborts the run; it is recorded as
fetch_error for that package and the run continues.

This script verifies candidates. It installs nothing and decides nothing
about installation. Status ceiling for every row: exists (on PyPI).

Usage:
  /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 \
      constraint_box/scripts/verify_library_candidates.py \
      --registry constraint_box/config/cb_light_library_candidates.json --write
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PYPI_URL = "https://pypi.org/pypi/{name}/json"
STALE_DAYS_MAX = 548          # ~18 months
MAX_DEPS = 3                  # declared non-extra runtime deps
MAX_WHEEL_BYTES = 5 * 1024 * 1024
CHECK_PYTHONS = ((3, 12, 0), (3, 13, 0))
REQUIRED_PLATFORMS = ("linux", "macos", "windows")


def canonical_name(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def fetch_json(name, timeout):
    url = PYPI_URL.format(name=name)
    req = urllib.request.Request(
        url, headers={"User-Agent": "cb-light-library-verifier/1.0 (constraint_box)"}
    )
    last_err = None
    for _attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp), None
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None, "404"
            last_err = "HTTP %s" % exc.code
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last_err = str(exc) or exc.__class__.__name__
    return None, last_err


def parse_version(text):
    parts = []
    for piece in text.strip().split("."):
        if piece == "*":
            break
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _cmp_padded(a, b):
    n = max(len(a), len(b))
    aa = tuple(a) + (0,) * (n - len(a))
    bb = tuple(b) + (0,) * (n - len(b))
    return (aa > bb) - (aa < bb)


def satisfies_clause(version, clause):
    clause = clause.strip()
    if not clause:
        return True
    op = "=="
    rest = clause
    for candidate_op in ("===", "==", "!=", "<=", ">=", "~=", "<", ">"):
        if clause.startswith(candidate_op):
            op = candidate_op
            rest = clause[len(candidate_op):].strip()
            break
    wildcard = rest.endswith(".*")
    if wildcard:
        rest = rest[:-2]
    target = parse_version(rest)
    if op in ("==", "==="):
        if wildcard:
            return version[: len(target)] == target
        return _cmp_padded(version, target) == 0
    if op == "!=":
        if wildcard:
            return version[: len(target)] != target
        return _cmp_padded(version, target) != 0
    if op == ">=":
        return _cmp_padded(version, target) >= 0
    if op == "<=":
        return _cmp_padded(version, target) <= 0
    if op == ">":
        return _cmp_padded(version, target) > 0
    if op == "<":
        return _cmp_padded(version, target) < 0
    if op == "~=":
        if _cmp_padded(version, target) < 0:
            return False
        return version[: max(len(target) - 1, 1)] == target[:-1]
    return True


def python_admitted(version, requires_python):
    return all(
        satisfies_clause(version, clause)
        for clause in requires_python.split(",")
        if clause.strip()
    )


def parse_iso(ts):
    ts = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def runtime_deps(requires_dist):
    names = []
    for entry in requires_dist or []:
        marker = entry.split(";", 1)[1] if ";" in entry else ""
        if "extra" in marker:
            continue
        head = re.split(r"[\s(\[><=!~;]", entry.strip(), maxsplit=1)[0]
        if head:
            names.append(head)
    return names


def wheel_platforms(files):
    plats = set()
    pure = False
    for f in files:
        if f.get("packagetype") != "bdist_wheel":
            continue
        fname = f.get("filename", "")
        if not fname.endswith(".whl"):
            continue
        plat_field = fname[:-4].split("-")[-1]
        for tag in plat_field.split("."):
            if tag == "any":
                pure = True
            elif "linux" in tag:
                plats.add("linux")
            elif "macosx" in tag:
                plats.add("macos")
            elif tag.startswith("win"):
                plats.add("windows")
    return pure, plats


def verify_package(data, now):
    info = data.get("info", {})
    files = data.get("urls") or []
    out = {}
    out["latest_version"] = info.get("version")

    upload_times = [
        parse_iso(f["upload_time_iso_8601"])
        for f in files
        if f.get("upload_time_iso_8601")
    ]
    released = min(upload_times) if upload_times else None
    out["release_date"] = released.date().isoformat() if released else None
    out["days_since_release"] = (now - released).days if released else None

    requires_python = info.get("requires_python") or None
    out["requires_python"] = requires_python
    for major, minor, micro in CHECK_PYTHONS:
        key = "admits_%d_%d" % (major, minor)
        if requires_python:
            out[key] = python_admitted((major, minor, micro), requires_python)
        else:
            out[key] = None

    pure, plats = wheel_platforms(files)
    wheels = [f for f in files if f.get("packagetype") == "bdist_wheel"]
    if not files:
        out["platforms"] = "no-files"
    elif not wheels:
        out["platforms"] = "sdist-only"
    elif pure:
        out["platforms"] = "pure(all)"
    else:
        out["platforms"] = ",".join(sorted(plats)) if plats else "unknown-wheel-tags"
    out["pure_python"] = pure

    sizes = [f.get("size") or 0 for f in wheels]
    out["largest_wheel_bytes"] = max(sizes) if sizes else None
    out["largest_wheel_mb"] = (
        round(max(sizes) / (1024 * 1024), 2) if sizes else None
    )

    deps = runtime_deps(info.get("requires_dist"))
    out["declared_runtime_deps"] = len(deps)
    out["runtime_dep_names"] = deps

    reasons = []
    if out["days_since_release"] is None:
        reasons.append("no release files; cannot date the latest release")
    elif out["days_since_release"] > STALE_DAYS_MAX:
        reasons.append(
            "stale: last release %s (%d days > %d)"
            % (out["release_date"], out["days_since_release"], STALE_DAYS_MAX)
        )
    if not requires_python:
        reasons.append("no requires_python declared")
    else:
        if out["admits_3_12"] is False:
            reasons.append("requires_python %r excludes 3.12" % requires_python)
        if out["admits_3_13"] is False:
            reasons.append("requires_python %r excludes 3.13" % requires_python)
    if out["platforms"] in ("sdist-only", "no-files"):
        reasons.append("no wheel published (%s)" % out["platforms"])
    elif not pure:
        missing = [p for p in REQUIRED_PLATFORMS if p not in plats]
        if missing:
            reasons.append("missing platform wheels: %s" % ",".join(missing))
    if out["largest_wheel_bytes"] is not None and out["largest_wheel_bytes"] > MAX_WHEEL_BYTES:
        reasons.append(
            "largest wheel %.2f MB exceeds 5 MB lean budget" % out["largest_wheel_mb"]
        )
    if len(deps) > MAX_DEPS:
        reasons.append(
            "dependency tree: %d declared runtime deps > %d (%s)"
            % (len(deps), MAX_DEPS, ", ".join(sorted(set(deps))))
        )

    out["verdict"] = "keep" if not reasons else "drop"
    out["drop_reasons"] = reasons
    return out


def fmt(value, width):
    text = "-" if value is None else str(value)
    return text[:width].ljust(width)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--registry",
        default=str(
            Path(__file__).resolve().parents[1]
            / "config"
            / "cb_light_library_candidates.json"
        ),
        help="registry JSON of candidates to verify",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write verification results back into the registry file",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--only", default=None, help="verify a single candidate by name (debug)"
    )
    args = parser.parse_args(argv)

    registry_path = Path(args.registry)
    registry = json.loads(registry_path.read_text())
    candidates = registry["candidates"]
    now = datetime.now(timezone.utc)

    header = (
        fmt("name", 22)
        + fmt("version", 12)
        + fmt("released", 11)
        + fmt("days", 6)
        + fmt("req_python", 15)
        + fmt("312", 4)
        + fmt("313", 4)
        + fmt("platforms", 21)
        + fmt("whl_MB", 8)
        + fmt("deps", 5)
        + fmt("verdict", 8)
        + "reasons"
    )
    print(header)
    print("-" * len(header))

    seen = {}
    keeps = 0
    drops = 0
    errors = 0
    reason_hist = {}
    for cand in candidates:
        name = cand["pypi_name"]
        if args.only and canonical_name(args.only) != canonical_name(name):
            continue
        canon = canonical_name(name)
        if canon in seen:
            cand["verified"] = seen[canon]
        else:
            data, err = fetch_json(name, args.timeout)
            if data is None:
                if err == "404":
                    verified = {
                        "verdict": "drop",
                        "drop_reasons": ["nonexistent on PyPI (404)"],
                    }
                else:
                    verified = {
                        "verdict": "fetch_error",
                        "drop_reasons": [],
                        "fetch_error": err,
                    }
            else:
                verified = verify_package(data, now)
            verified["checked_at"] = now.date().isoformat()
            seen[canon] = verified
            cand["verified"] = verified

        v = cand["verified"]
        if v["verdict"] == "keep":
            keeps += 1
        elif v["verdict"] == "drop":
            drops += 1
        else:
            errors += 1
        for reason in v.get("drop_reasons", []):
            key = reason.split(":")[0]
            reason_hist[key] = reason_hist.get(key, 0) + 1

        y = lambda flag: "-" if flag is None else ("Y" if flag else "N")
        print(
            fmt(name, 22)
            + fmt(v.get("latest_version"), 12)
            + fmt(v.get("release_date"), 11)
            + fmt(v.get("days_since_release"), 6)
            + fmt(v.get("requires_python"), 15)
            + fmt(y(v.get("admits_3_12")), 4)
            + fmt(y(v.get("admits_3_13")), 4)
            + fmt(v.get("platforms"), 21)
            + fmt(v.get("largest_wheel_mb"), 8)
            + fmt(v.get("declared_runtime_deps"), 5)
            + fmt(v["verdict"], 8)
            + ("; ".join(v.get("drop_reasons", []) or [])
               or v.get("fetch_error", ""))
        )

    total = keeps + drops + errors
    print("-" * len(header))
    print(
        "TOTAL %d unique-row candidates: %d keep, %d drop, %d fetch_error"
        % (total, keeps, drops, errors)
    )
    print("Drop reason histogram:")
    for key in sorted(reason_hist, key=reason_hist.get, reverse=True):
        print("  %3d  %s" % (reason_hist[key], key))
    print(
        "Bar: <=%d days since release, requires_python declared and admitting "
        "3.12+3.13, wheels for linux+macos+windows or pure, wheel <=5 MB, "
        "<=%d declared runtime deps." % (STALE_DAYS_MAX, MAX_DEPS)
    )
    print(
        "Status ceiling for every keep: exists (on PyPI). Nothing here was "
        "installed or run."
    )

    if args.write and not args.only:
        registry["verified_at"] = now.isoformat(timespec="seconds")
        registry["selection_bar"] = {
            "stale_days_max": STALE_DAYS_MAX,
            "max_declared_runtime_deps": MAX_DEPS,
            "max_wheel_bytes": MAX_WHEEL_BYTES,
            "python_versions_required": ["3.12", "3.13"],
            "platforms_required": list(REQUIRED_PLATFORMS),
            "requires_python_must_be_declared": True,
        }
        registry_path.write_text(json.dumps(registry, indent=2) + "\n")
        print("Wrote verification results into %s" % registry_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
