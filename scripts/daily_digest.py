#!/usr/bin/env python3
"""
Generates the daily digest from knowledge_base.jsonl and recent repo
activity. Outputs data/digest.json for the dashboard.

Standard library only.
"""

import json
import os
from datetime import datetime, timezone, timedelta

KB_PATH = "knowledge_base.jsonl"
REPOS_PATH = "data/repos.json"
OUTPUT_PATH = "data/digest.json"


def load_kb() -> list:
    """Load all knowledge base entries."""
    if not os.path.exists(KB_PATH):
        return []
    entries = []
    with open(KB_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def load_repos() -> dict:
    """Load enriched repos data."""
    if not os.path.exists(REPOS_PATH):
        return {"repos": [], "pillars": {}}
    with open(REPOS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_digest() -> dict:
    kb = load_kb()
    repos_data = load_repos()

    now = datetime.now(timezone.utc)
    cutoff_24h = (now - timedelta(hours=24)).isoformat()
    cutoff_7d = (now - timedelta(days=7)).isoformat()

    # Recent KB entries
    recent_24h = [e for e in kb if e.get("timestamp", "") >= cutoff_24h]
    recent_7d = [e for e in kb if e.get("timestamp", "") >= cutoff_7d]

    # Sort by urgency desc
    recent_24h.sort(key=lambda e: e.get("urgency", 0), reverse=True)
    recent_7d.sort(key=lambda e: e.get("urgency", 0), reverse=True)

    # Pillar stats from KB
    pillar_counts = {}
    for e in kb:
        p = e.get("pillar", "Unknown")
        pillar_counts[p] = pillar_counts.get(p, 0) + 1

    # Today's interrupt items (urgency >= 9)
    interrupts = [e for e in recent_24h if e.get("urgency", 0) >= 9]

    # Today's watch items (urgency 5-8)
    watch = [e for e in recent_24h if 5 <= e.get("urgency", 0) <= 8]

    # Repos with recent activity (pushed in last 24h)
    active_repos = []
    for r in repos_data.get("repos", []):
        if r.get("pushed_at", "") >= cutoff_24h:
            active_repos.append({
                "name": r["name"],
                "pillar": r["pillar"],
                "pillar_emoji": r["pillar_emoji"],
                "pushed_at": r["pushed_at"],
                "url": r["url"],
            })

    # Repos with recent activity (pushed in last 7 days)
    weekly_repos = []
    for r in repos_data.get("repos", []):
        if r.get("pushed_at", "") >= cutoff_7d:
            weekly_repos.append({
                "name": r["name"],
                "pillar": r["pillar"],
                "pillar_emoji": r["pillar_emoji"],
                "pushed_at": r["pushed_at"],
                "url": r["url"],
            })

    digest = {
        "generated_at": now.isoformat(),
        "stats": {
            "total_entries": len(kb),
            "last_24h": len(recent_24h),
            "last_7d": len(recent_7d),
            "pillar_counts": pillar_counts,
            "total_repos": repos_data.get("total_repos", 0),
        },
        "interrupts": interrupts[:5],
        "watch": watch[:10],
        "recent_entries": recent_24h[:20],
        "weekly_entries": recent_7d[:50],
        "active_repos_24h": active_repos,
        "active_repos_7d": weekly_repos,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(digest, f, indent=2, ensure_ascii=False)

    print(f"Digest generated: {len(interrupts)} interrupts, "
          f"{len(watch)} watch items, {len(active_repos)} active repos")


if __name__ == "__main__":
    generate_digest()
