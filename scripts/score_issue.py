#!/usr/bin/env python3
"""
Scores one inbox item (a GitHub Issue) against interests.md, pushes a
Telegram alert if it's urgent, enriches with pillar tagging, and appends
it to knowledge_base.jsonl as a permanent, numbered entry.

Standard library only — nothing to pip install.
"""

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")

MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
URGENCY_THRESHOLD = int(os.environ.get("URGENCY_THRESHOLD", "9"))

PROFILE_PATH = "interests.md"
KB_PATH = "knowledge_base.jsonl"

IMAGE_URL_RE = re.compile(r"!\[[^\]]*\]\((https?://[^\s)]+)\)")

PILLARS = [
    "Financial & Market Intelligence",
    "AI / Research / AGI",
    "Saudi Economy / Urban / Labour",
    "Products & Platforms",
    "Mobile & Infrastructure",
    "News & Dashboards",
]


def build_messages(item_text: str, profile: str) -> list:
    pillar_list = "\n".join(f"  - {p}" for p in PILLARS)
    instruction = (
        "You are scoring one inbox item for a personal attention system.\n\n"
        f"Interest profile:\n{profile}\n\n"
        "Score the item below from 1-10 on relevance (fits the profile), "
        "novelty (new vs. already well known), and urgency (needs "
        "attention today vs. can wait for a weekly digest).\n\n"
        "Also classify it into exactly one pillar from this list:\n"
        f"{pillar_list}\n\n"
        "Reply with only a JSON object, no other text, no markdown fences:\n"
        '{"relevance": int, "novelty": int, "urgency": int, '
        '"pillar": "one of the pillar names above", '
        '"summary": "one sentence", "reason": "one sentence on the '
        'urgency score"}\n\nItem:\n'
    )
    content = [{"type": "text", "text": instruction + item_text}]
    for url in IMAGE_URL_RE.findall(item_text)[:3]:
        content.append({"type": "image_url", "image_url": {"url": url}})
    return [{"role": "user", "content": content}]


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            first_line, rest = text.split("\n", 1)
            text = rest if first_line.strip().lower() in ("json", "") else text
    return json.loads(text)


def call_openrouter(item_text: str, profile: str) -> dict:
    body = json.dumps(
        {
            "model": MODEL,
            "messages": build_messages(item_text, profile),
            "response_format": {"type": "json_object"},
        }
    ).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": "mono-signal-os",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.load(resp)

    content = payload["choices"][0]["message"]["content"]
    return extract_json(content)


def next_id() -> int:
    if not os.path.exists(KB_PATH):
        return 1
    last = 0
    with open(KB_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                last = json.loads(line)["id"]
    return last + 1


def append_entry(entry: dict) -> None:
    with open(KB_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def send_telegram(text: str) -> None:
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return
    body = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=30).read()
    except urllib.error.URLError as exc:
        print(f"Telegram send failed: {exc}")


def comment_and_close(entry_id: int, score: dict) -> None:
    pillar = score.get("pillar", "Unknown")
    pillar_emoji = {
        "Financial & Market Intelligence": "🔵",
        "AI / Research / AGI": "🟣",
        "Saudi Economy / Urban / Labour": "🟢",
        "Products & Platforms": "🟠",
        "Mobile & Infrastructure": "🔴",
        "News & Dashboards": "🟡",
    }
    emoji = pillar_emoji.get(pillar, "⚪")

    comment = (
        f"Filed as entry **#{entry_id}** {emoji} {pillar}\n\n"
        f"| Metric | Score |\n"
        f"|--------|-------|\n"
        f"| Relevance | {score['relevance']}/10 |\n"
        f"| Novelty | {score['novelty']}/10 |\n"
        f"| Urgency | {score['urgency']}/10 |\n\n"
        f"**Summary:** {score['summary']}\n\n"
        f"**Reason:** {score['reason']}"
    )
    subprocess.run(
        ["gh", "issue", "comment", ISSUE_NUMBER, "--body", comment], check=True
    )
    # Add pillar label
    label = f"pillar:{pillar}"
    subprocess.run(
        ["gh", "issue", "edit", ISSUE_NUMBER, "--add-label", label],
        check=False,  # Label may not exist yet
    )
    subprocess.run(["gh", "issue", "close", ISSUE_NUMBER], check=True)


def main() -> None:
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        profile = f.read()

    item_text = f"{ISSUE_TITLE}\n\n{ISSUE_BODY}".strip()
    score = call_openrouter(item_text, profile)

    entry_id = next_id()
    entry = {
        "id": entry_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "issue_number": ISSUE_NUMBER,
        "pillar": score.get("pillar", "Unknown"),
        "content": item_text,
        "relevance": score["relevance"],
        "novelty": score["novelty"],
        "urgency": score["urgency"],
        "summary": score["summary"],
        "reason": score["reason"],
    }
    append_entry(entry)

    if score["urgency"] >= URGENCY_THRESHOLD:
        pillar = score.get("pillar", "Unknown")
        msg = (
            f"🚨 <b>INTERRUPT #{entry_id}</b>\n"
            f"<b>Pillar:</b> {pillar}\n"
            f"<b>Urgency:</b> {score['urgency']}/10\n\n"
            f"{score['summary']}\n\n"
            f"<i>{score['reason']}</i>"
        )
        send_telegram(msg)
    elif score["urgency"] >= 5:
        pillar = score.get("pillar", "Unknown")
        msg = (
            f"📋 <b>#{entry_id}</b> — {pillar}\n"
            f"Score: {score['urgency']}/10\n"
            f"{score['summary']}"
        )
        send_telegram(msg)

    comment_and_close(entry_id, score)


if __name__ == "__main__":
    main()
