#!/usr/bin/env python3
"""
Scans both GitHub accounts (muxd22-alt and Muxd21), enriches each repo
with metadata, classifies into pillars, and writes repos.json for the
dashboard. Runs daily via GitHub Actions.

Standard library only.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone

GH_TOKEN = os.environ.get("GH_PAT", os.environ.get("GH_TOKEN", ""))

ACCOUNTS = ["muxd22-alt", "Muxd21"]

OUTPUT_PATH = "data/repos.json"

# ── Repo → Pillar mapping ──────────────────────────────────────────

PILLAR_MAP = {
    # 🔵 Financial & Market Intelligence
    "SectorShift": "financial",
    "TASI-Quant-Replicator": "financial",
    "TASI": "financial",
    "Tasi": "financial",
    "TASI-Quant-Replicator-Public": "financial",
    "daily_stock_analysis": "financial",
    "BlockMesh": "financial",
    "tasi-quant-model": "financial",
    "calc": "financial",
    "EconomicCompass": "financial",
    "Crash_Detector": "financial",
    "Intelligence_Platform": "financial",
    "Dashboard-Orchestrator-Pro": "financial",
    "Crypto": "financial",
    "market": "financial",
    "hyper-analytical": "financial",
    "daily-alpha-loop": "financial",
    "BMHQ": "financial",
    # 🟣 AI / Research / AGI
    "AGI_Track": "ai",
    "ai_research_dashboard": "ai",
    "MSA": "ai",
    "PAI": "ai",
    "reseaech": "ai",
    "AI_RACE_CLEAN": "ai",
    "ai_scientist": "ai",
    "autoresearch": "ai",
    "autoresearch-amd": "ai",
    "ClawBio": "ai",
    "agenthub": "ai",
    # 🟢 Saudi Economy / Urban / Labour
    "UHI_SAUDI": "saudi",
    "UHI_tracker": "saudi",
    "post_labour_tracker": "saudi",
    "jobs": "saudi",
    "agri": "saudi",
    "india-jobs-ai-exposure": "saudi",
    "FASTING": "saudi",
    # 🟠 Products & Platforms
    "hud_live": "products",
    "HudhudLive-Production": "products",
    "hudhud-platform": "products",
    "AcomZ": "products",
    "SocialMedia": "products",
    "medoasbot": "products",
    # 🔴 Mobile & Infrastructure
    "openclaw-android": "mobile",
    "termux_reader": "mobile",
    "Deepin_OGC_Intel": "mobile",
    "APHONE": "mobile",
    "radar_2": "mobile",
    "openclaw_mission_debain_VPS": "mobile",
    "Claw-Mission-One": "mobile",
    "moltis": "mobile",
    "moltis-termux": "mobile",
    "moltisdroid": "mobile",
    "molclaw-android": "mobile",
    "openpocket": "mobile",
    # 🟡 News & Dashboards
    "iran-news-dashboard": "news",
    "global-news-dashboard": "news",
    "oooooo": "news",
    "agent-os": "news",
}

# Dismissed repos (games, trivial forks, tests, duplicates)
DISMISSED = {
    "N-r", "fay", "cesium-unity", "unity-roadmap", "post-labour-tracker",
    "https-github.com-muxd22-alt-hud_live", "claude-code-rev",
    "yt-bot-history", "youBOT", "Auto", "r3r4", "STUPID_2", "open2a",
    "neon", "MAP_GEN", "text_ads", "pixels", "know", "VOICE2", "VOiCE",
    "GAME_WORD", "truck3d", "TRUCK", "Seed---Soil", "kaledh4",
    "Arabic-Text-to-Crosswords", "Map-with-advertisements", "Book",
    "pdf-chat-agent", "map-widget", "all_promot",
}

PILLAR_META = {
    "financial": {
        "name": "Financial & Market Intelligence",
        "emoji": "🔵",
        "color": "#3B82F6",
    },
    "ai": {
        "name": "AI / Research / AGI",
        "emoji": "🟣",
        "color": "#A855F7",
    },
    "saudi": {
        "name": "Saudi Economy / Urban / Labour",
        "emoji": "🟢",
        "color": "#22C55E",
    },
    "products": {
        "name": "Products & Platforms",
        "emoji": "🟠",
        "color": "#F97316",
    },
    "mobile": {
        "name": "Mobile & Infrastructure",
        "emoji": "🔴",
        "color": "#EF4444",
    },
    "news": {
        "name": "News & Dashboards",
        "emoji": "🟡",
        "color": "#EAB308",
    },
}


def build_github_headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Mono-Signal-OS",
    }
    if GH_TOKEN:
        headers["Authorization"] = f"Bearer {GH_TOKEN}"
    return headers


def fetch_repos(username: str) -> list:
    """Fetch all public+private repos for a user via GitHub API."""
    repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{username}/repos"
            f"?per_page=100&page={page}&sort=updated"
        )
        req = urllib.request.Request(url, headers=build_github_headers())
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                batch = json.load(resp)
        except urllib.error.HTTPError as e:
            print(f"Error fetching {username} page {page}: {e}")
            break

        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def fetch_open_issues(owner: str, repo: str, limit: int = 5) -> list:
    """Fetch recent open issues for a repo."""
    url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues"
        f"?state=open&per_page={limit}&sort=updated"
    )
    req = urllib.request.Request(url, headers=build_github_headers())
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)
    except (urllib.error.HTTPError, urllib.error.URLError):
        return []


def enrich_repo(raw: dict, account: str) -> dict | None:
    """Transform raw GitHub API repo data into enriched format."""
    name = raw["name"]

    if name in DISMISSED:
        return None

    pillar_key = PILLAR_MAP.get(name)
    if not pillar_key:
        return None  # Not in any pillar → skip

    pillar = PILLAR_META[pillar_key]

    # Fetch recent issues
    issues = fetch_open_issues(account, name, limit=3)
    issue_data = [
        {
            "number": i["number"],
            "title": i["title"],
            "url": i["html_url"],
            "updated_at": i["updated_at"],
            "labels": [l["name"] for l in i.get("labels", [])],
        }
        for i in issues
        if not i.get("pull_request")  # Exclude PRs
    ]

    return {
        "name": name,
        "full_name": raw["full_name"],
        "account": account,
        "description": raw.get("description") or "",
        "url": raw["html_url"],
        "language": raw.get("language") or "Unknown",
        "stars": raw.get("stargazers_count", 0),
        "forks": raw.get("forks_count", 0),
        "open_issues": raw.get("open_issues_count", 0),
        "private": raw.get("private", False),
        "fork": raw.get("fork", False),
        "pushed_at": raw.get("pushed_at", ""),
        "updated_at": raw.get("updated_at", ""),
        "created_at": raw.get("created_at", ""),
        "pillar": pillar_key,
        "pillar_name": pillar["name"],
        "pillar_emoji": pillar["emoji"],
        "pillar_color": pillar["color"],
        "recent_issues": issue_data,
    }


def main() -> None:
    all_repos = []
    for account in ACCOUNTS:
        print(f"Fetching repos for {account}...")
        raw_repos = fetch_repos(account)
        print(f"  Found {len(raw_repos)} repos")
        for raw in raw_repos:
            enriched = enrich_repo(raw, account)
            if enriched:
                all_repos.append(enriched)

    # Deduplicate by name (keep the one updated most recently)
    seen = {}
    for repo in all_repos:
        name = repo["name"]
        if name not in seen or repo["updated_at"] > seen[name]["updated_at"]:
            seen[name] = repo
    deduped = sorted(seen.values(), key=lambda r: r["updated_at"], reverse=True)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_repos": len(deduped),
        "pillars": PILLAR_META,
        "repos": deduped,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(deduped)} repos to {OUTPUT_PATH}")
    for key, meta in PILLAR_META.items():
        count = sum(1 for r in deduped if r["pillar"] == key)
        print(f"  {meta['emoji']} {meta['name']}: {count}")


if __name__ == "__main__":
    main()
