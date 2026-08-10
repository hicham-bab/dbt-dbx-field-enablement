#!/usr/bin/env python3
"""Recompute the demo's factual claims from the repo itself.

The demo script and comparison docs quote model counts, metric counts and a
revenue figure. Those drift the moment someone adds a model. This recomputes
them from source and fails when the committed facts.yml disagrees, so "the
numbers in the docs are real" is enforced rather than promised.

    python3 scripts/check_facts.py            # print the facts
    python3 scripts/check_facts.py --write    # refresh facts.yml
    python3 scripts/check_facts.py --check    # fail if facts.yml is stale

It also fails on figures we know are fabricated, so they cannot come back.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections import defaultdict
from decimal import Decimal

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    raise SystemExit(1)

ROOT = pathlib.Path(__file__).resolve().parent.parent
FACTS = ROOT / "facts.yml"
SEED = ROOT / "databricks/notebooks/00_setup_raw_data.py"
SKIP_DIRS = {".git", "dbt_packages", "target", "node_modules", "logs"}

# Figures that were invented and must never reappear in prose.
BANNED = {
    "127,450": "fabricated revenue figure; the real total is $14,364.45",
    "131,200": "fabricated revenue figure",
    "129,800": "fabricated revenue figure",
    "a3f7c21": "invented commit hash; use real history from `git log`",
    "9e2b134": "invented commit hash; use real history from `git log`",
    "6d1a8f0": "invented commit hash; use real history from `git log`",
    "PR #47": "invented PR number; show real `git log` output instead",
    "Merged on March 12th": "invented merge date",
}


# --------------------------------------------------------------- seed data ---
def seed_rows(sql: str, table: str) -> list[list[str]]:
    m = re.search(
        rf"INSERT INTO \$\{{catalog\}}\.\$\{{schema\}}\.{table} VALUES(.*?);", sql, re.S
    )
    if not m:
        return []
    out = []
    for line in m.group(1).split("\n"):
        line = re.sub(r"--.*$", "", line).strip().rstrip(",")
        if not (line.startswith("(") and line.endswith(")")):
            continue
        inner = line[1:-1].replace("CURRENT_TIMESTAMP()", "NOW")
        parts, cur, quoted = [], "", False
        for ch in inner:
            if ch == "'":
                quoted = not quoted
            elif ch == "," and not quoted:
                parts.append(cur.strip())
                cur = ""
                continue
            cur += ch
        parts.append(cur.strip())
        out.append([p.strip().strip("'") for p in parts])
    return out


def revenue_facts() -> dict:
    raw = SEED.read_text(encoding="utf-8")
    sql = "\n".join(re.sub(r"^#\s*MAGIC\s?", "", l) for l in raw.split("\n"))
    orders = seed_rows(sql, "raw_orders")
    payments = seed_rows(sql, "raw_payments")

    paid: dict[str, Decimal] = defaultdict(Decimal)
    for p in payments:
        if len(p) >= 5 and p[4] == "success":
            paid[p[1]] += Decimal(p[3])

    by_status_count: dict[str, int] = defaultdict(int)
    completed = Decimal(0)
    all_paid = Decimal(0)
    for o in orders:
        status = o[3]
        by_status_count[status] += 1
        all_paid += paid[o[0]]
        if status == "completed":
            completed += paid[o[0]]

    return {
        "orders": len(orders),
        "payments": len(payments),
        "orders_by_status": dict(sorted(by_status_count.items())),
        "total_recognised_revenue": f"{completed:.2f}",
        "total_amount_paid_all_statuses": f"{all_paid:.2f}",
    }


# ------------------------------------------------------------ dbt project ---
def load(path: pathlib.Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def project_facts() -> dict:
    projects = sorted(
        p.parent.name
        for p in ROOT.rglob("dbt_project.yml")
        if not SKIP_DIRS & set(p.parts)
    )

    models_dir = ROOT / "platform/models"
    by_layer = {}
    for layer in ("staging", "intermediate", "marts", "metrics", "semantic"):
        d = models_dir / layer
        if d.is_dir():
            by_layer[layer] = len(list(d.rglob("*.sql")))

    metrics: set[str] = set()
    contracted: list[str] = []
    tests_by_model: dict[str, int] = {}
    for f in models_dir.rglob("*.yml"):
        d = load(f)
        if not isinstance(d, dict):
            continue
        for m in d.get("metrics") or []:
            if isinstance(m, dict) and "name" in m:
                metrics.add(m["name"])
        for mod in d.get("models") or []:
            if not isinstance(mod, dict):
                continue
            for m in mod.get("metrics") or []:
                if isinstance(m, dict) and "name" in m:
                    metrics.add(m["name"])
            if (mod.get("config") or {}).get("contract", {}).get("enforced"):
                contracted.append(mod["name"])
            n = len(mod.get("data_tests") or mod.get("tests") or [])
            for col in mod.get("columns") or []:
                n += len(col.get("data_tests") or col.get("tests") or [])
            if n:
                tests_by_model[mod["name"]] = n

    return {
        "dbt_projects": projects,
        "platform_models_total": len(list(models_dir.rglob("*.sql"))),
        "platform_models_by_layer": by_layer,
        "metric_definitions": len(metrics),
        "contracted_marts": sorted(contracted),
        "tests_fct_orders": tests_by_model.get("fct_orders", 0),
    }


def raw_tables() -> list[str]:
    sql = SEED.read_text(encoding="utf-8")
    return sorted(set(re.findall(r"raw_[a-z_]+", sql)))


def collect() -> dict:
    facts = {"raw_tables": raw_tables()}
    facts.update(project_facts())
    facts.update(revenue_facts())
    return facts


# ------------------------------------------------------------ banned scan ---
def banned_hits() -> list[str]:
    hits = []
    for path in sorted(ROOT.rglob("*.md")):
        if SKIP_DIRS & set(path.parts):
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for bad, why in BANNED.items():
                if bad in line:
                    hits.append(f"{path.relative_to(ROOT)}:{i}: '{bad}' - {why}")
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    facts = collect()
    rendered = yaml.safe_dump(facts, sort_keys=True, default_flow_style=False)

    hits = banned_hits()
    for h in hits:
        print(f"BANNED FIGURE {h}")

    if args.write:
        FACTS.write_text(
            "# Generated by scripts/check_facts.py - do not edit by hand.\n"
            "# These are the numbers the docs are allowed to quote.\n\n" + rendered,
            encoding="utf-8",
        )
        print(f"wrote {FACTS.relative_to(ROOT)}")
        return 1 if hits else 0

    if args.check:
        if not FACTS.exists():
            print("facts.yml missing - run scripts/check_facts.py --write")
            return 1
        current = yaml.safe_load(FACTS.read_text(encoding="utf-8")) or {}
        if current != facts:
            print("facts.yml is stale. Repo says:\n")
            print(rendered)
            print("Run scripts/check_facts.py --write and update any docs that quote these.")
            return 1
        print("facts.yml matches the repo")
        return 1 if hits else 0

    print(rendered)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
