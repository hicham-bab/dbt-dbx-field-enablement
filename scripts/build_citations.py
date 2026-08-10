#!/usr/bin/env python3
"""Generate the Sources block at the bottom of each doc from sources.yml.

Every `[^claim-id]` footnote used in a Markdown file must resolve to a claim in
sources.yml. This script regenerates the footnote definitions so they are never
hand-maintained: when Databricks renames something again, you edit sources.yml
and re-run this.

    python3 scripts/build_citations.py           # rewrite the Sources blocks
    python3 scripts/build_citations.py --check   # fail if anything is stale

Exit codes: 0 ok, 1 unknown claim id, 2 blocks out of date (--check only).
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources.yml"
START = "<!-- BEGIN GENERATED SOURCES - edit sources.yml, then run scripts/build_citations.py -->"
END = "<!-- END GENERATED SOURCES -->"

REF = re.compile(r"\[\^([a-z0-9][a-z0-9-]*)\](?!:)")
SKIP = {"NAMING.md"}  # keeps its own hand-written footnote list
# Vendored / generated trees we must never rewrite.
SKIP_DIRS = {".git", "dbt_packages", "target", "node_modules", "logs"}
SEP = "\n\n---\n\n"


def docs() -> list[pathlib.Path]:
    return sorted(
        p for p in ROOT.rglob("*.md")
        if not SKIP_DIRS & set(p.parts) and p.name not in SKIP
    )


INLINE_CODE = re.compile(r"`[^`]*`")
FENCE = re.compile(r"^```.*?^```", re.S | re.M)


def split_body(text: str) -> str:
    """Return the file content before the generated block, separator removed."""
    body = text.split(START)[0]
    if body.rstrip().endswith("---"):
        body = body.rstrip()[: -len("---")]
    return body.rstrip()


def refs_in(body: str) -> list[str]:
    """Footnote ids used in prose. Code spans and fenced blocks don't count, so a
    doc can show `[^claim-id]` as an example without CI treating it as a citation."""
    prose = INLINE_CODE.sub("", FENCE.sub("", body))
    return sorted(set(REF.findall(prose)))


def expected_text(text: str, claims: dict[str, dict[str, str]]) -> str:
    body = split_body(text)
    ids = refs_in(body)
    if not ids:
        return body + "\n"
    return body + SEP + render(ids, claims) + "\n"


def load_claims() -> dict[str, dict[str, str]]:
    """Minimal parser for the claims: block of sources.yml.

    Deliberately dependency-free so CI needs no pip install.
    """
    claims: dict[str, dict[str, str]] = {}
    current: str | None = None
    in_claims = False
    for raw in SOURCES.read_text(encoding="utf-8").splitlines():
        if raw.startswith("claims:"):
            in_claims = True
            continue
        if not in_claims or not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = re.match(r"^  ([a-z0-9][a-z0-9-]*):\s*$", raw)
        if m:
            current = m.group(1)
            claims[current] = {}
            continue
        m = re.match(r"^    (url|retrieved|source_type):\s*(.+?)\s*$", raw)
        if m and current:
            claims[current][m.group(1)] = m.group(2)
    return claims


def render(ids: list[str], claims: dict[str, dict[str, str]]) -> str:
    lines = [START, "", "## Sources", ""]
    lines.append(
        "Generated from `sources.yml`. Every claim about a competitor's "
        "capabilities cites one of these. Do not edit by hand."
    )
    lines.append("")
    for cid in ids:
        c = claims[cid]
        url = c.get("url", "")
        retrieved = c.get("retrieved", "unknown")
        lines.append(f"[^{cid}]: {url} (retrieved {retrieved})")
    lines.append("")
    lines.append(END)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    claims = load_claims()
    if not claims:
        print("error: no claims parsed from sources.yml", file=sys.stderr)
        return 1

    bad = stale = 0
    for path in docs():
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        ids = refs_in(split_body(text))

        unknown = [i for i in ids if i not in claims]
        if unknown:
            bad += 1
            for u in unknown:
                print(f"{rel}: unknown claim id [^{u}] - add it to sources.yml or remove the footnote")
            continue

        expected = expected_text(text, claims)
        if expected == text:
            continue
        if args.check:
            stale += 1
            print(f"{rel}: Sources block out of date - run scripts/build_citations.py")
        else:
            path.write_text(expected, encoding="utf-8")
            print(f"updated {rel}")

    if bad:
        return 1
    if stale:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
