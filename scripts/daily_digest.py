#!/usr/bin/env python3
"""
Generates the daily digest from knowledge_base.jsonl and recent repo
activity. Outputs data/digest.json for the dashboard.

Standard library only — clean, modular, and typed.
"""

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

KB_PATH: str = "knowledge_base.jsonl"
REPOS_PATH: str = "data/repos.json"
OUTPUT_PATH: str = "data/digest.json"


def load_kb() -> List[Dict[str, Any]]:
    """Load all knowledge base entries safely."""
    if not os.path.exists(KB_PATH):
        return []
    entries: List[Dict[str, Any]] = []
    with open(KB_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as err:
                    logging.warning(f"Skipping malformed line {line_num} in {KB_PATH}: {err}")
    return entries


def load_repos() -> Dict[str, Any]:
    """Load enriched repos data safely."""
    if not os.path.exists(REPOS_PATH):
        return {"repos": [], "pillars": {}}
    try:
        with open(REPOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as err:
        logging.error(f"Error loading {REPOS_PATH}: {err}")
        return {"repos": [], "pillars": {}}


def generate_digest() -> Dict[str, Any]:
    kb = load_kb()
    repos_data = load_repos()

    now = datetime.now(timezone.utc)
    cutoff_24h = (now - timedelta(hours=24)).isoformat()
    cutoff_7d = (now - timedelta(days=7)).isoformat()

    recent_24h = [e for e in kb if e.get("timestamp", "") >= cutoff_24h]
    recent_7d = [e for e in kb if e.get("timestamp", "") >= cutoff_7d]

    recent_24h.sort(key=lambda e: e.get("urgency", 0), reverse=True)
    recent_7d.sort(key=lambda e: e.get("urgency", 0), reverse=True)

    pillar_counts: Dict[str, int] = {}
    for e in kb:
        p = e.get("pillar", "Unknown")
        pillar_counts[p] = pillar_counts.get(p, 0) + 1

    interrupts = [e for e in recent_24h if e.get("urgency", 0) >= 9]
    watch = [e for e in recent_24h if 5 <= e.get("urgency", 0) <= 8]

    active_repos: List[Dict[str, Any]] = []
    for r in repos_data.get("repos", []):
        if r.get("pushed_at", "") >= cutoff_24h:
            active_repos.append({
                "name": r.get("name", ""),
                "pillar": r.get("pillar", ""),
                "pillar_emoji": r.get("pillar_emoji", "⚪"),
                "pushed_at": r.get("pushed_at", ""),
                "url": r.get("url", ""),
            })

    weekly_repos: List[Dict[str, Any]] = []
    for r in repos_data.get("repos", []):
        if r.get("pushed_at", "") >= cutoff_7d:
            weekly_repos.append({
                "name": r.get("name", ""),
                "pillar": r.get("pillar", ""),
                "pillar_emoji": r.get("pillar_emoji", "⚪"),
                "pushed_at": r.get("pushed_at", ""),
                "url": r.get("url", ""),
            })

    digest: Dict[str, Any] = {
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

    logging.info(
        f"Digest generated: {len(interrupts)} interrupts, "
        f"{len(watch)} watch items, {len(active_repos)} active repos"
    )
    return digest


if __name__ == "__main__":
    generate_digest()
