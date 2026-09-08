#!/usr/bin/env python3
"""
Scores one inbox item (a GitHub Issue) against interests.md, pushes a
Telegram alert if it's urgent, enriches with pillar tagging, and appends
it to knowledge_base.jsonl as a permanent, numbered entry.

Standard library only — robust, modular, and fault-tolerant.
"""

import json
import logging
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")
TELEGRAM_BOT_TOKEN: Optional[str] = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: Optional[str] = os.environ.get("TELEGRAM_CHAT_ID")
ISSUE_NUMBER: str = os.environ.get("ISSUE_NUMBER", "1")
ISSUE_TITLE: str = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY: str = os.environ.get("ISSUE_BODY", "")

MODEL: str = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
URGENCY_THRESHOLD: int = int(os.environ.get("URGENCY_THRESHOLD", "9"))

PROFILE_PATH: str = "interests.md"
KB_PATH: str = "knowledge_base.jsonl"

IMAGE_URL_RE = re.compile(r"!\[[^\]]*\]\((https?://[^\s)]+)\)")

PILLARS: List[str] = [
    "Financial & Market Intelligence",
    "AI / Research / AGI",
    "Saudi Economy / Urban / Labour",
    "Products & Platforms",
    "Mobile & Infrastructure",
    "News & Dashboards",
]

PILLAR_EMOJI: Dict[str, str] = {
    "Financial & Market Intelligence": "🔵",
    "AI / Research / AGI": "🟣",
    "Saudi Economy / Urban / Labour": "🟢",
    "Products & Platforms": "🟠",
    "Mobile & Infrastructure": "🔴",
    "News & Dashboards": "🟡",
}


def build_messages(item_text: str, profile: str) -> List[Dict[str, Any]]:
    pillar_list = "\n".join(f"  - {p}" for p in PILLARS)
    instruction = (
        "You are scoring one inbox item for a personal attention system.\n\n"
        f"Interest profile:\n{profile}\n\n"
        "Score the item below from 1-10 on relevance (fits the profile), "
        "novelty (new vs. already well known), and urgency (needs "
        "attention today vs. can wait for a weekly digest).\n\n"
        "Also classify it into exactly one pillar from this list:\n"
        f"{pillar_list}\n\n"
        "Reply with only a valid JSON object, no markdown, no quotes, no extra text:\n"
        '{"relevance": int, "novelty": int, "urgency": int, '
        '"pillar": "one of the pillar names above", '
        '"summary": "one sentence", "reason": "one sentence on the '
        'urgency score"}\n\nItem:\n'
    )
    content: List[Dict[str, Any]] = [{"type": "text", "text": instruction + item_text}]
    for url in IMAGE_URL_RE.findall(item_text)[:3]:
        content.append({"type": "image_url", "image_url": {"url": url}})
    return [{"role": "user", "content": content}]


def extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            first_line, rest = text.split("\n", 1)
            text = rest if first_line.strip().lower() in ("json", "") else text
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logging.error(f"JSON decode failed on response: {exc}")
        return {}


def call_openrouter(item_text: str, profile: str) -> Dict[str, Any]:
    if not OPENROUTER_API_KEY:
        logging.warning("OPENROUTER_API_KEY missing. Using default fallback score.")
        return get_fallback_score(item_text)

    body = json.dumps(
        {
            "model": MODEL,
            "messages": build_messages(item_text, profile),
            "response_format": {"type": "json_object"},
        }
    ).encode()

    unique_models = list(dict.fromkeys(FALLBACK_MODELS))

    for model in unique_models:
        logging.info(f"Attempting model scoring with: {model}")
        for use_json_format in [True, False]:
            payload_dict: Dict[str, Any] = {
                "model": model,
                "messages": build_messages(item_text, profile),
            }
            if use_json_format:
                payload_dict["response_format"] = {"type": "json_object"}

            body = json.dumps(payload_dict).encode()
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=body,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "X-OpenRouter-Title": "mono-signal-os",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:
                    payload = json.load(resp)
                if "choices" in payload and len(payload["choices"]) > 0:
                    content = payload["choices"][0]["message"]["content"]
                    parsed = extract_json(content)
                    if validate_score(parsed):
                        logging.info(f"Successfully scored with model {model}")
                        return parsed
            except urllib.error.HTTPError as exc:
                logging.warning(f"HTTP {exc.code} for model {model} (json_format={use_json_format}): {exc.reason}")
            except Exception as exc:
                logging.warning(f"Failed model {model} (json_format={use_json_format}): {exc}")

    logging.error("All OpenRouter models failed to return valid score.")
    return get_fallback_score(
        item_text,
        "OpenRouter API request failed across all free models. Verify OPENROUTER_API_KEY validity and model quota."
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.load(resp)
        content = payload["choices"][0]["message"]["content"]
        parsed = extract_json(content)
        if validate_score(parsed):
            return parsed
        logging.warning("OpenRouter payload missing required fields. Using fallback.")
    except Exception as exc:
        logging.error(f"OpenRouter API call failed: {exc}")

    return get_fallback_score(item_text)


def validate_score(score: Dict[str, Any]) -> bool:
    required_keys = ["relevance", "novelty", "urgency", "pillar", "summary", "reason"]
    return all(k in score for k in required_keys) and score.get("pillar") in PILLARS


def get_fallback_score(item_text: str) -> Dict[str, Any]:
    title = item_text.split("\n")[0][:80] if item_text else "Untitled Inbox Item"
    return {
        "relevance": 5,
        "novelty": 5,
        "urgency": 5,
        "pillar": "News & Dashboards",
        "summary": title,
        "reason": "Scored via fallback system due to API or parsing error.",
    }


def next_id() -> int:
    if not os.path.exists(KB_PATH):
        return 1
    last = 0
    with open(KB_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    last = json.loads(line)["id"]
                except (json.JSONDecodeError, KeyError):
                    continue
    return last + 1


def append_entry(entry: Dict[str, Any]) -> None:
    with open(KB_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def send_telegram(text: str) -> None:
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        logging.info("Telegram notification skipped (missing TOKEN or CHAT_ID)")
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
        logging.info("Telegram message sent successfully.")
    except urllib.error.URLError as exc:
        logging.error(f"Telegram send failed: {exc}")


def comment_and_close(entry_id: int, score: Dict[str, Any]) -> None:
    pillar = score.get("pillar", "News & Dashboards")
    emoji = PILLAR_EMOJI.get(pillar, "⚪")

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
    try:
        subprocess.run(["gh", "issue", "comment", ISSUE_NUMBER, "--body", comment], check=True)
        label = f"pillar:{pillar}"
        subprocess.run(["gh", "issue", "edit", ISSUE_NUMBER, "--add-label", label], check=False)
        subprocess.run(["gh", "issue", "close", ISSUE_NUMBER], check=True)
        logging.info(f"GitHub issue #{ISSUE_NUMBER} updated and closed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"GitHub CLI operation failed: {e}")


def main() -> None:
    profile = ""
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            profile = f.read()

    item_text = f"{ISSUE_TITLE}\n\n{ISSUE_BODY}".strip()
    score = call_openrouter(item_text, profile)

    entry_id = next_id()
    entry = {
        "id": entry_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "issue_number": ISSUE_NUMBER,
        "pillar": score.get("pillar", "News & Dashboards"),
        "content": item_text,
        "relevance": score["relevance"],
        "novelty": score["novelty"],
        "urgency": score["urgency"],
        "summary": score["summary"],
        "reason": score["reason"],
    }
    append_entry(entry)
    logging.info(f"Entry #{entry_id} recorded in knowledge base.")

    if score["urgency"] >= URGENCY_THRESHOLD:
        pillar = score.get("pillar", "News & Dashboards")
        msg = (
            f"🚨 <b>INTERRUPT #{entry_id}</b>\n"
            f"<b>Pillar:</b> {pillar}\n"
            f"<b>Urgency:</b> {score['urgency']}/10\n\n"
            f"{score['summary']}\n\n"
            f"<i>{score['reason']}</i>"
        )
        send_telegram(msg)
    elif score["urgency"] >= 5:
        pillar = score.get("pillar", "News & Dashboards")
        msg = (
            f"📋 <b>#{entry_id}</b> — {pillar}\n"
            f"Score: {score['urgency']}/10\n"
            f"{score['summary']}"
        )
        send_telegram(msg)

    comment_and_close(entry_id, score)


if __name__ == "__main__":
    main()
