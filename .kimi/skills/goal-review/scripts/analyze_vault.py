#!/usr/bin/env python3
"""Analyze Obsidian vault articles and output statistics as JSON."""

import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import yaml


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}


def is_system_path(path: Path) -> bool:
    """Check if path is a system directory that should be skipped."""
    parts = set(path.parts)
    return bool(parts & {".claude", ".obsidian", ".git", "templates"})


def get_period_start(now: datetime, period: str) -> datetime:
    """Calculate the start of the current period."""
    if period == "weekly":
        return now - timedelta(days=now.weekday())
    if period == "monthly":
        return now.replace(day=1)
    if period == "yearly":
        return now.replace(month=1, day=1)
    raise ValueError(f"Unknown period: {period}")


def analyze_vault(vault_path: str, period: str) -> dict:
    """Scan vault and collect article statistics for the given period."""
    vault = Path(vault_path)
    articles = []

    META_FILES = {"goals.md", "reward.md", "wiki.md", "CLAUDE.md"}
    for md_file in vault.rglob("*.md"):
        rel = md_file.relative_to(vault)
        if is_system_path(rel):
            continue
        if md_file.name in META_FILES and rel.parent == Path("."):
            continue
        if rel.parts and rel.parts[0] == "manager":
            continue

        content = md_file.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)

        stat = frontmatter.get("status", "unknown")
        tags = frontmatter.get("tags", [])

        # Pick date from published > date > created
        date_str = ""
        for key in ("published", "date", "created"):
            val = frontmatter.get(key)
            if val:
                date_str = str(val)
                break

        parsed_date = None
        if date_str:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M"):
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue

        articles.append(
            {
                "path": str(md_file.relative_to(vault)),
                "status": stat,
                "date": str(date_str) if date_str else None,
                "parsed_date": parsed_date.isoformat() if parsed_date else None,
                "tags": tags if isinstance(tags, list) else [tags],
                "word_count": len(re.findall(r"\b\w+\b", content)),
            }
        )

    now = datetime.now()
    period_start = get_period_start(now, period)
    week_start = get_period_start(now, "weekly")
    month_start = get_period_start(now, "monthly")
    year_start = get_period_start(now, "yearly")

    by_status = {}
    by_tag = {}
    period_articles = []
    this_week = []
    this_month = []
    this_year = []

    for a in articles:
        by_status[a["status"]] = by_status.get(a["status"], 0) + 1
        for tag in a["tags"]:
            by_tag[tag] = by_tag.get(tag, 0) + 1
        if a["parsed_date"]:
            dt = datetime.fromisoformat(a["parsed_date"])
            if dt >= period_start:
                period_articles.append(a)
            if dt >= week_start:
                this_week.append(a)
            if dt >= month_start:
                this_month.append(a)
            if dt >= year_start:
                this_year.append(a)

    def summarize(items):
        return [
            {"path": a["path"], "date": a["date"], "status": a["status"]} for a in items
        ]

    return {
        "period": period,
        "period_start": period_start.strftime("%Y-%m-%d"),
        "total_articles": len(articles),
        "by_status": by_status,
        "by_tag": by_tag,
        "period_count": len(period_articles),
        "period_articles": summarize(period_articles),
        "this_week_count": len(this_week),
        "this_week_articles": summarize(this_week),
        "this_month_count": len(this_month),
        "this_month_articles": summarize(this_month),
        "this_year_count": len(this_year),
        "this_year_articles": summarize(this_year),
        "articles_with_date": sum(1 for a in articles if a["parsed_date"]),
        "articles_without_date": sum(1 for a in articles if not a["parsed_date"]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze vault article statistics")
    parser.add_argument("vault_path", nargs="?", default=".", help="Path to vault root")
    parser.add_argument(
        "--period",
        choices=["weekly", "monthly", "yearly"],
        default="weekly",
        help="Time period for goal comparison (default: weekly)",
    )
    args = parser.parse_args()
    result = analyze_vault(args.vault_path, args.period)
    print(json.dumps(result, ensure_ascii=False, indent=2))
