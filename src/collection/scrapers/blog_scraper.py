"""
AICOR Automated RSS/Blog Scraper (Task BE-02)
Implements IF-4 + Appendix A: polls official OpenAI / Anthropic / Microsoft
feeds, auto-tags product category A/B/C via keyword rubric, and appends new
launches to data/raw/events_launch_raw.csv (append-only, dedup by URL).

All HTTP goes through src.common.resilience (rate limiter + retry).
"""
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional

import requests

from src.common.config import COMPANY_NAME_TO_ID
from src.common.resilience import retry_with_backoff, trends_rate_limiter
from src.common.schemas import date_to_quarter, validate_product_category
from src.collection.storage import append_to_raw_csv

logger = logging.getLogger("aicor.scraper.blog")

FEEDS = [
    {
        "company_id": 2,
        "company_name": "OpenAI",
        "feed_url": "https://openai.com/news/rss.xml",
        "page_url": "https://openai.com/news/",
    },
    {
        "company_id": 3,
        "company_name": "Anthropic",
        "feed_url": "https://www.anthropic.com/news/rss.xml",
        "page_url": "https://www.anthropic.com/news",
    },
    {
        "company_id": 1,
        "company_name": "Microsoft",
        "feed_url": "https://blogs.microsoft.com/feed/",
        "page_url": "https://blogs.microsoft.com/",
    },
]

HEADERS = {
    "User-Agent": "AICOR Academic Research Bot/1.0 (contact@aicor-project.edu)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}

# Keyword rubric (Appendix A). Order matters: A checked before B before C.
CATEGORY_A_PATTERNS = [
    "technical report", "introducing", "new model", "frontier",
    "gpt-5", "gpt-5.", "claude 4", "new foundation model",
    "system card",
]
CATEGORY_B_PATTERNS = [
    "api", "preview", "enterprise", "turbo", "fine-tuning", "fine tuning",
    "claude 3.5", "o1-mini", "reasoning model", "agent",
]
CATEGORY_C_PATTERNS = [
    "update", "feature", "integration", "app", "plugin", "availability",
    "copilot", "announcing",
]
AI_FILTER_PATTERNS = [
    "ai", "gpt", "claude", "copilot", "model", "llm", "agent",
    "anthropic", "openai", "azure ai", "machine learning",
]


def classify_category(title: str, summary: str = "") -> str:
    """Auto-tags rubric category A/B/C from title + summary (Appendix A)."""
    text = f"{title or ''} {summary or ''}".lower()
    if any(p in text for p in CATEGORY_A_PATTERNS):
        return validate_product_category("A") and "A"
    if any(p in text for p in CATEGORY_B_PATTERNS):
        return "B"
    if any(p in text for p in CATEGORY_C_PATTERNS):
        return "C"
    return "C"


def is_ai_related(title: str, summary: str = "", source: str = "generic") -> bool:
    """Filters Microsoft blog feed to AI-related posts; vendor feeds pass through."""
    if source in ("openai", "anthropic"):
        return True
    text = f"{title or ''} {summary or ''}".lower()
    return any(p in text for p in AI_FILTER_PATTERNS)


def _parse_date(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%a, %d %b %Y %H:%M:%S %Z",
                "%a, %d %b %Y %H:%M:%S %z"):
        try:
            dt = datetime.strptime(raw[: len(fmt)] if "%" not in raw else raw, fmt)
            return dt.date().isoformat()
        except (ValueError, TypeError):
            continue
    try:
        return parsedate_to_datetime(raw).date().isoformat()
    except (ValueError, TypeError):
        pass
    m = re.search(r"(\d{4}-\d{2}-\d{2})", raw)
    return m.group(1) if m else ""


def parse_feed_xml(
    xml_text: str,
    company_id: int,
    company_name: str,
    coder: str = "AICOR_BOT",
    source_hint: str = "generic",
) -> List[Dict]:
    """Parses RSS 2.0 / Atom XML into events_launch-shaped records.

    Records failing validation (missing date/title) are skipped, never fabricated.
    """
    events: List[Dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning(f"Unparseable feed XML for {company_name}: {e}")
        return []

    items: List[Dict] = []
    # RSS 2.0: channel/item
    for item in root.findall(".//item"):
        items.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "summary": (item.findtext("description") or "").strip(),
                "date": (item.findtext("pubDate") or "").strip(),
            }
        )
    # Atom: entry (namespace-agnostic via local tag match)
    for entry in root.iter():
        if entry.tag.endswith("entry"):
            title, link, summary, date = "", "", "", ""
            for child in entry:
                local = child.tag.split("}")[-1]
                if local == "title":
                    title = (child.text or "").strip()
                elif local == "link":
                    href = child.attrib.get("href", "").strip()
                    if href and not link:
                        link = href
                    elif (child.text or "").strip() and not link:
                        link = (child.text or "").strip()
                elif local in ("summary", "content"):
                    summary = (child.text or "").strip() or summary
                elif local in ("published", "updated"):
                    date = (child.text or "").strip() or date
            items.append({"title": title, "link": link, "summary": summary, "date": date})

    for it in items:
        title = it["title"]
        link = it["link"]
        if not title or not link:
            continue
        if not is_ai_related(title, it["summary"], source_hint):
            continue
        launch_date = _parse_date(it["date"])
        if not launch_date:
            continue
        category = classify_category(title, it["summary"])
        points = {"A": 3.0, "B": 2.0, "C": 1.0}[category]
        try:
            quarter = date_to_quarter(launch_date)
        except ValueError:
            continue
        events.append(
            {
                "company_id": company_id,
                "company_name": company_name,
                "launch_date": launch_date,
                "quarter": quarter,
                "product_name": title[:200],
                "category": category,
                "points": points,
                "source_url": link,
                "coder": coder,
            }
        )
    return events


@retry_with_backoff(max_retries=3, initial_delay=2.0)
def fetch_feed_text(feed_url: str) -> str:
    """Downloads one feed with rate limiting + retry (anti-ban)."""
    trends_rate_limiter.wait()
    resp = requests.get(feed_url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def scrape_feed(feed: Dict, coder: str = "AICOR_BOT") -> List[Dict]:
    """Fetches + parses a single configured feed. Network errors yield []."""
    source_hint = "microsoft" if feed["company_id"] == 1 else (
        "openai" if feed["company_id"] == 2 else "anthropic"
    )
    try:
        xml_text = fetch_feed_text(feed["feed_url"])
    except Exception as e:
        logger.warning(f"Feed fetch failed for {feed['company_name']}: {e}. Keeping prior data.")
        return []
    return parse_feed_xml(xml_text, feed["company_id"], feed["company_name"], coder, source_hint)


def run_blog_scraper(
    feeds: Optional[List[Dict]] = None,
    coder: str = "AICOR_BOT",
) -> int:
    """Runs all feeds and appends genuinely new launches (dedup via storage)."""
    total_added = 0
    for feed in feeds or FEEDS:
        events = scrape_feed(feed, coder)
        if events:
            added = append_to_raw_csv("events_launch", events)
            total_added += added
            logger.info(f"Blog scraper: {feed['company_name']} -> {added} new rows.")
    logger.info(f"Blog scraper finished: {total_added} new records total.")
    return total_added


def resolve_company_id(name: str) -> Optional[int]:
    return COMPANY_NAME_TO_ID.get((name or "").strip().lower())
