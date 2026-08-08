#!/usr/bin/env python3
"""Simple vault analyzer for personal-article."""
import os
import re
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path


def parse_frontmatter(text):
    """Parse simple YAML-like frontmatter."""
    if not text.startswith('---'):
        return {}
    parts = text.split('---', 2)
    if len(parts) < 3:
        return {}
    fm = parts[1]
    data = {}
    for line in fm.splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            # Remove quotes
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            data[key] = val
    return data


def main():
    vault_root = sys.argv[1] if len(sys.argv) > 1 else '.'
    period = sys.argv[2] if len(sys.argv) > 2 else 'weekly'

    today = datetime.now().date()
    # ISO week: Monday start
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    articles = []
    md_files = list(Path(vault_root).rglob('*.md'))
    # Exclude manager/docs/templates/README
    skip_dirs = {'manager', 'docs', 'templates', '.git', '.qoder', '.claude', '.kimi', 'images'}
    for f in md_files:
        rel = f.relative_to(vault_root)
        if any(part in skip_dirs for part in rel.parts):
            continue
        text = f.read_text(encoding='utf-8')
        fm = parse_frontmatter(text)
        date_str = fm.get('published', '') or fm.get('date', '')
        status = fm.get('status', '')
        title = fm.get('title', '') or f.stem
        try:
            article_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        except ValueError:
            article_date = None
        articles.append({
            'path': str(rel),
            'title': title,
            'date': date_str,
            'parsed_date': article_date.isoformat() if article_date else None,
            'status': status,
        })

    this_week = [a for a in articles if a['parsed_date'] and week_start <= datetime.fromisoformat(a['parsed_date']).date() <= week_end]
    this_month = [a for a in articles if a['parsed_date'] and month_start <= datetime.fromisoformat(a['parsed_date']).date()]
    this_year = [a for a in articles if a['parsed_date'] and year_start <= datetime.fromisoformat(a['parsed_date']).date()]
    no_date = [a for a in articles if not a['parsed_date']]

    by_status = {}
    for a in articles:
        by_status[a['status'] or 'unknown'] = by_status.get(a['status'] or 'unknown', 0) + 1

    result = {
        'period': period,
        'period_start': week_start.isoformat(),
        'period_end': week_end.isoformat(),
        'today': today.isoformat(),
        'total_articles': len(articles),
        'period_count': len(this_week),
        'period_articles': this_week,
        'this_month_count': len(this_month),
        'this_year_count': len(this_year),
        'articles_without_date': len(no_date),
        'articles_with_date': len(articles) - len(no_date),
        'by_status': by_status,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
