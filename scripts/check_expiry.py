#!/usr/bin/env python3
"""Fail (or warn) when a doc is past its `expires` date.

Stale competitive content should look stale. Every .md carries front matter with
`last_verified` and `expires`; this checks it.

    python3 scripts/check_expiry.py            # warn only, exit 0
    python3 scripts/check_expiry.py --strict   # exit 1 if anything is expired

Also fails on docs missing front matter entirely, so new files can't skip it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "dbt_packages", "target", "node_modules", "logs"}
FIELD = re.compile(r"^(version|last_verified|expires|owner):\s*(.+?)\s*$")


def front_matter(path: pathlib.Path) -> dict[str, str] | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fm: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fm
        m = FIELD.match(line)
        if m:
            fm[m.group(1)] = m.group(2)
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    today = dt.date.today()
    soon = today + dt.timedelta(days=14)
    expired: list[str] = []
    missing: list[str] = []
    warning: list[str] = []

    for path in sorted(ROOT.rglob("*.md")):
        if SKIP_DIRS & set(path.parts):
            continue
        rel = str(path.relative_to(ROOT))
        fm = front_matter(path)
        if not fm or "expires" not in fm:
            missing.append(rel)
            continue
        try:
            exp = dt.date.fromisoformat(fm["expires"])
        except ValueError:
            missing.append(rel)
            continue
        if exp < today:
            expired.append(f"{rel} (expired {exp}, {(today - exp).days} days ago)")
        elif exp <= soon:
            warning.append(f"{rel} (expires {exp})")

    for rel in missing:
        print(f"MISSING front matter or expires: {rel}")
    for item in expired:
        print(f"EXPIRED: {item}")
    for item in warning:
        print(f"expiring soon: {item}")

    if not (missing or expired or warning):
        print(f"all docs current (checked {today})")

    if missing:
        print("\nAdd front matter: version / last_verified / expires / owner.")
        return 1
    if expired:
        print(
            "\nRe-verify the claims, bump last_verified and expires, then re-run "
            "scripts/build_citations.py."
        )
        return 1 if args.strict else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
