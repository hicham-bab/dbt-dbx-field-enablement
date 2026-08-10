#!/usr/bin/env python3
"""Fail the build on retired product names in prose.

The rules live in NAMING.md; this enforces them. It is deliberately
prose-only. Code identifiers are never violations, so the linter ignores:

  - fenced code blocks and inline `code`
  - front matter
  - the generated Sources block and any URL
  - "formerly X" / "(was X)" / "renamed from X" clauses, which are correct usage
  - everything outside .md (SQL COALESCE(), filenames like
    01_lakeflow_pipeline.py, `databricks.yml` keys)

    python3 scripts/naming_lint.py

Exit 0 clean, 1 violations found.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "dbt_packages", "target", "node_modules", "logs"}
SKIP_FILES = {"NAMING.md", "sources.yml"}

# (regex, message). Case-sensitive on purpose: COALESCE() is not Coalesce.
RULES: list[tuple[str, str]] = [
    (r"\bDelta Live Tables?\b", "use 'Lakeflow pipelines' (Delta Live Tables is only OK in a 'formerly' clause)"),
    (r"\bDLT\b", "use 'Lakeflow pipelines'"),
    (r"\bSpark Declarative Pipelines?\b", "'Spark Declarative Pipelines' is the Apache Spark OSS framework, not the Databricks product - use 'Lakeflow pipelines'"),
    (r"\bLakeflow Declarative Pipelines?\b", "stale name - use 'Lakeflow pipelines'"),
    (r"\bSDP\b", "use 'Lakeflow pipelines'"),
    (r"\bDatabricks Asset Bundles?\b", "use 'Declarative Automation Bundles'"),
    (r"\bDeclarative Asset Bundles?\b", "not a real product name - use 'Declarative Automation Bundles'"),
    (r"\bGenie Spaces?\b", "use 'Genie Agents'"),
    (r"\bdbt Cloud\b", "use 'dbt platform'"),
    (r"\bdbt Explorer\b", "use 'dbt Catalog'"),
    (r"\bdbt Studio\b", "use 'Studio IDE'"),
    (r"\bdbt platform IDE\b", "use 'Studio IDE'"),
    (r"\bdbt platform Studio\b", "use 'Studio IDE'"),
    (r"\bCloud IDE\b", "use 'Studio IDE'"),
    (r"\bCoalesce\b", "the Coalesce conference was retired 2026-01-31 (SQL COALESCE() is fine - this check is case-sensitive)"),
    (r"\bDBT\b", "'dbt' is always lowercase"),
]
COMPILED = [(re.compile(p), m) for p, m in RULES]

# A retired name is allowed when it is explicitly flagged as the old name.
ALLOWED = re.compile(
    r"formerly|previously|rename|used to be|old name|was called|no longer|"
    r"don't (say|write)|do not (say|write)|instead of|rather than|is wrong|"
    r"stale name|not a (real |Databricks )*product name|not the Databricks product",
    re.I,
)

INLINE_CODE = re.compile(r"`[^`]*`")
URL = re.compile(r"https?://\S+")


def prose_lines(path: pathlib.Path):
    """Yield (lineno, prose_text) with code, front matter and URLs stripped."""
    in_fence = in_fm = in_generated = False
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = raw.strip()
        if i == 1 and s == "---":
            in_fm = True
            continue
        if in_fm:
            if s == "---":
                in_fm = False
            continue
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "BEGIN GENERATED SOURCES" in raw:
            in_generated = True
        if "END GENERATED SOURCES" in raw:
            in_generated = False
            continue
        if in_generated:
            continue
        yield i, URL.sub("", INLINE_CODE.sub("", raw))


def paragraphs(lines: list[tuple[int, str]]):
    """Group prose lines into paragraphs so names wrapped across a line break
    are still caught. Yields (first_lineno, joined_text)."""
    buf: list[tuple[int, str]] = []
    for lineno, text in lines:
        if text.strip():
            buf.append((lineno, text.strip()))
            continue
        if buf:
            yield buf[0][0], " ".join(t for _, t in buf)
            buf = []
    if buf:
        yield buf[0][0], " ".join(t for _, t in buf)


def main() -> int:
    violations = 0
    for path in sorted(ROOT.rglob("*.md")):
        if SKIP_DIRS & set(path.parts) or path.name in SKIP_FILES:
            continue
        rel = path.relative_to(ROOT)
        lines = list(prose_lines(path))
        seen: set[tuple[int, str]] = set()

        # Pass 1: per line, for precise line numbers.
        # Pass 2: per paragraph, to catch names split across a line break.
        for lineno, text in list(lines) + list(paragraphs(lines)):
            if ALLOWED.search(text):
                continue
            for pattern, message in COMPILED:
                m = pattern.search(text)
                if m and (lineno, m.group(0)) not in seen:
                    seen.add((lineno, m.group(0)))
                    violations += 1
                    print(f"{rel}:{lineno}: '{m.group(0)}' -> {message}")

    if violations:
        print(f"\n{violations} naming violation(s). See NAMING.md.")
        print("If a use is legitimate, phrase it as a 'formerly X' clause or put it in `backticks`.")
        return 1
    print("naming lint: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
