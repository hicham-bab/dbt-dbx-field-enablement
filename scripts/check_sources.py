#!/usr/bin/env python3
"""HEAD-request every URL in sources.yml and report dead or moved pages.

Databricks moved /dlt -> /ldp and /metric-views -> /business-semantics/metric-views/
inside a year. Run weekly in CI so a rename is caught the week it happens rather
than mid-call.

    python3 scripts/check_sources.py

Exit 0 all good, 1 something is dead or redirects to a different path.
Uses only the standard library so CI needs no pip install.
"""
from __future__ import annotations

import pathlib
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources.yml"
UA = "Mozilla/5.0 (compatible; dbt-dbx-enablement-linkcheck/1.0)"
TIMEOUT = 25


def urls() -> list[tuple[str, str]]:
    out, current = [], "?"
    for raw in SOURCES.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^  ([a-z0-9][a-z0-9-]*):\s*$", raw)
        if m:
            current = m.group(1)
        m = re.match(r"^    url:\s*(\S+)\s*$", raw)
        if m:
            out.append((current, m.group(1)))
    return out


def check(url: str) -> tuple[str, str]:
    """Return (status, detail). status is 'ok', 'moved' or 'dead'."""
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            final = resp.geturl()
            if urlparse(final).path.rstrip("/") != urlparse(url).path.rstrip("/"):
                return "moved", f"redirects to {final}"
            return "ok", str(resp.status)
    except urllib.error.HTTPError as e:
        return "dead", f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001 - network flake should not crash CI silently
        return "dead", f"{type(e).__name__}: {e}"


def main() -> int:
    problems = []
    for claim_id, url in urls():
        status, detail = check(url)
        print(f"{status.upper():6} {claim_id}: {url} ({detail})")
        if status != "ok":
            problems.append(f"- `{claim_id}` -> {url} ({detail})")

    if problems:
        print("\nProblems found:")
        print("\n".join(problems))
        print(
            "\nUpdate the url in sources.yml, re-verify that the page still supports "
            "the claim, bump `retrieved`, then run scripts/build_citations.py."
        )
        return 1
    print("\nall source URLs resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
