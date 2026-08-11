#!/usr/bin/env python3
"""Live PyPI metadata authority, with retrieval provenance.

Why this exists
---------------
The registry at config/cb_light_library_candidates.json carried a `verified`
block per row, stamped `checked_at: 2026-08-09`, that had never been checked
against PyPI. Its tabulate row claimed release_date 2024-12-01 for version
0.10.0; PyPI reports 2026-03-04 for that same version, 458 days apart. The hook
kernel then fired CURRENTNESS_EXPIRED on that fabricated date and called it a
live firing.

Measured scope on 2026-08-09 across the 86 adopted rows: 75 agree with PyPI,
11 disagree, and every one of the 11 is in cb-candidates-passing.in. Together
with tabulate that is the whole 12-row candidates_passing group. Zero adopted
packages are actually stale by live data.

The lesson is not "the dates were wrong". It is that a locally editable file is
authoritative for what the file says, never for what PyPI holds. This module is
the separate authority. It records, for every fetch, the raw response sha256 and
the retrieval time, so a later reader can tell measurement from assertion.

stdlib only, like the rest of the kernel.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import urllib.error
import urllib.request

PYPI_JSON = "https://pypi.org/pypi/{name}/json"
USER_AGENT = "constraintbox-hookkernel/1 (+metadata authority)"


def fetch(name, timeout=20):
    """Fetch one package's PyPI metadata with provenance.

    Returns a dict that always carries `source`, and either the observed fields
    or an `error`. A fetch failure is never silently treated as agreement — the
    caller must decide, and the kernel treats it as HOLD.
    """
    url = PYPI_JSON.format(name=name)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"source": "pypi", "name": name, "error": type(exc).__name__, "detail": str(exc)[:200]}
    try:
        data = json.loads(raw)
    except ValueError as exc:
        return {"source": "pypi", "name": name, "error": "MalformedJSON", "detail": str(exc)[:200]}

    version = data["info"]["version"]
    files = data.get("releases", {}).get(version, [])
    upload = min((f["upload_time_iso_8601"] for f in files), default=None)
    yanked = any(f.get("yanked") for f in files)
    return {
        "source": "pypi",
        "name": name,
        "latest_version": version,
        "release_date": upload[:10] if upload else None,
        "requires_python": data["info"].get("requires_python"),
        "yanked": yanked,
        # provenance: the two fields that separate measurement from assertion
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def compare(declared, observed):
    """Compare a registry row's verified block against a live PyPI observation.

    Returns (status, fields) where status is one of:
      agree                     the registry matches the authority
      METADATA_SOURCE_DISAGREEMENT  they differ on a fact one of them measured
      AUTHORITY_UNAVAILABLE     the authority could not be reached

    Disagreement is preserved as a named result. It is never resolved by
    preferring one side: the registry is authoritative for what the registry
    says, and PyPI is authoritative for what PyPI holds.
    """
    if observed.get("error"):
        return "AUTHORITY_UNAVAILABLE", {"error": observed["error"], "detail": observed.get("detail")}
    differing = {}
    for field in ("latest_version", "release_date", "requires_python"):
        left, right = declared.get(field), observed.get(field)
        if left is not None and right is not None and left != right:
            differing[field] = {"registry": left, "pypi": right}
    if differing:
        return "METADATA_SOURCE_DISAGREEMENT", {
            "fields": differing,
            "raw_sha256": observed["raw_sha256"],
            "retrieved_at": observed["retrieved_at"],
        }
    return "agree", {"raw_sha256": observed["raw_sha256"], "retrieved_at": observed["retrieved_at"]}


def age_days(observed, today=None):
    """Days since the observed release date, or None if unavailable."""
    date = observed.get("release_date")
    if not date:
        return None
    today = today or datetime.date.today()
    return (today - datetime.date.fromisoformat(date)).days
