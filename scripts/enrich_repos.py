#!/usr/bin/env python3
"""
Scans both GitHub accounts (muxd22-alt and Muxd21), enriches each repo
with metadata, classifies into pillars, and writes repos.json for the
dashboard. Runs daily via GitHub Actions.

Standard library only — clean, modular, and resilient.
"""

import json
import logging
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

GH_TOKEN: str = os.environ.get("GH_PAT", os.environ.get("GH_TOKEN", ""))
ACCOUNTS: List[str] = ["muxd22-alt", "Muxd21"]
OUTPUT_PATH: str = "data/repos.json"

PILLAR_MAP: Dict[str, str] = {
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

DISMISSED: set = {
    "N-r", "fay", "cesium-unity", "unity-roadmap", "post-labour-tracker",
    "https-github.com-muxd22-alt-hud_live", "claude-code-rev",
    "yt-bot-history", "youBOT", "Auto", "r3r4", "STUPID_2", "open2a",
    "neon", "MAP_GEN", "text_ads", "pixels", "know", "VOICE2", "VOiCE",
    "GAME_WORD", "truck3d", "TRUCK", "Seed---Soil", "kaledh4",
    "Arabic-Text-to-Crosswords", "Map-with-advertisements", "Book",
    "pdf-chat-agent", "map-widget", "all_promot",
}

PILLAR_META: Dict[str, Dict[str, str]] = {
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


def build_github_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Mono-Signal-OS",
    }
    if GH_TOKEN:
        headers["Authorization"] = f"Bearer {GH_TOKEN}"
    return headers


def make_request_with_retry(url: str, max_retries: int = 3, backoff_factor: float = 1.0) -> Optional[Any]:
    req = urllib.request.Request(url, headers=build_github_headers())
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and attempt < max_retries:
                sleep_time = backoff_factor * (2 ** (attempt - 1))
                logging.warning(f"Rate limited on {url}. Retrying in {sleep_time:.1f}s...")
                time.sleep(sleep_time)
            else:
                logging.error(f"HTTP error {e.code} fetching {url}: {e.reason}")
                break
        except urllib.error.URLError as e:
            logging.error(f"URL error fetching {url}: {e.reason}")
            break
        except Exception as e:
            logging.error(f"Unexpected error fetching {url}: {e}")
            break
    return None


def fetch_repos(username: str) -> List[Dict[str, Any]]:
    """Fetch all public+private repos for a user via GitHub API."""
    repos: List[Dict[str, Any]] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{username}/repos"
            f"?per_page=100&page={page}&sort=updated"
        )
        batch = make_request_with_retry(url)
        if not batch or not isinstance(batch, list):
            break
        repos.extend(batch)
        page += 1
    return repos


def fetch_open_issues(owner: str, repo: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch recent open issues for a repo."""
    url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues"
        f"?state=open&per_page={limit}&sort=updated"
    )
    issues = make_request_with_retry(url)
    if not issues or not isinstance(issues, list):
        return []
    return issues


def enrich_repo(raw: Dict[str, Any], account: str) -> Optional[Dict[str, Any]]:
    """Transform raw GitHub API repo data into enriched format."""
    name = raw.get("name", "")
    if not name or name in DISMISSED:
        return None

    pillar_key = PILLAR_MAP.get(name)
    if not pillar_key:
        return None

    pillar = PILLAR_META[pillar_key]

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
        if isinstance(i, dict) and not i.get("pull_request")
    ]

    return {
        "name": name,
        "full_name": raw.get("full_name", f"{account}/{name}"),
        "account": account,
        "description": raw.get("description") or "",
        "url": raw.get("html_url", f"https://github.com/{account}/{name}"),
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
    all_repos: List[Dict[str, Any]] = []
    for account in ACCOUNTS:
        logging.info(f"Fetching repos for {account}...")
        raw_repos = fetch_repos(account)
        logging.info(f"  Found {len(raw_repos)} raw repos for {account}")
        for raw in raw_repos:
            enriched = enrich_repo(raw, account)
            if enriched:
                all_repos.append(enriched)

    seen: Dict[str, Dict[str, Any]] = {}
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

    logging.info(f"Successfully wrote {len(deduped)} repos to {OUTPUT_PATH}")
    for key, meta in PILLAR_META.items():
        count = sum(1 for r in deduped if r["pillar"] == key)
        logging.info(f"  {meta['emoji']} {meta['name']}: {count}")


if __name__ == "__main__":
    main()
