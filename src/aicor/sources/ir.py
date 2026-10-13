"""IR / Events crawler — products + events (RQ-02, Tier A).

Implements: SPEC §6.3, §6.5 — blog scraping, A/B/C classification, dedup.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse, urlunparse

import pandas as pd
import yaml

from aicor.config import get_settings
from aicor.sources import (
    SyncRecord,
    append_manifest,
    sha256_file,
    write_sync_log,
)

# Canonical IR and product blog feeds (SPEC §3.3)
IR_FEEDS: dict[str, list[str]] = {
    "MSFT": [
        "https://blogs.microsoft.com/feed/",
        "https://azure.microsoft.com/en-us/blog/feed/",
    ],
    "GOOGL": [
        "https://blog.google/rss/",
        "https://cloud.google.com/blog/rss/",
    ],
}


# ---------- Data classes ----------

@dataclass
class IrItem:
    """One product announcement / event from an IR blog."""

    product_name: str
    announcement_date: date | str
    description: str
    source_url: str
    category: str | None = None          # A / B / C (set by classify_abc)
    category_rationale: str | None = None
    review_status: str = "pending"        # pending / reviewed / rejected (§6.3)

    @property
    def normalized_url(self) -> str:
        """Canonical form for dedup — strip trailing slash, fragment, query."""
        parsed = urlparse(self.source_url.strip().lower())
        path = parsed.path.rstrip("/")
        return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


# ---------- Rubric ----------

DEFAULT_RUBRIC_PATH = Path("rubric/v1.yaml")


def load_rubric(path: str | Path | None = None) -> dict[str, Any]:
    """Load the A/B/C classification rubric from YAML."""
    p = Path(path) if path else DEFAULT_RUBRIC_PATH
    if not p.exists():
        # Return hardcoded provisional rubric
        return _provisional_rubric()
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _provisional_rubric() -> dict[str, Any]:
    return {
        "version": "v1-provisional",
        "provisional": True,
        "categories": {
            "A": {
                "label": "Major product launch / GA release",
                "score_weight": 3,
                "examples": ["Copilot GA", "Gemini 1.5 launch"],
                "rules": [
                    "Publicly available product (not preview/beta)",
                    "Named product with pricing or GA date",
                ],
            },
            "B": {
                "label": "Significant update / preview of major product",
                "score_weight": 2,
                "examples": ["Azure OpenAI Service preview", "Bard → Gemini rebrand"],
                "rules": [
                    "Public preview or major version update",
                    "Enterprise feature expansion",
                ],
            },
            "C": {
                "label": "Minor update / research announcement",
                "score_weight": 1,
                "examples": ["Research paper release", "Minor API update"],
                "rules": [
                    "Research-only with no product implication",
                    "Incremental patch or regional rollout",
                ],
            },
        },
    }


def classify_abc(
    item: IrItem,
    rubric: dict[str, Any] | None = None,
) -> tuple[Literal["A", "B", "C"], str]:
    """Classify an IR item as A, B, or C using the rubric.

    Returns ``(category, rationale)``.

    This is a rule-based heuristic classifier (provisional).
    In production, this would be replaced by LLM-assisted classification.
    """
    if rubric is None:
        rubric = load_rubric()

    desc_lower = (item.description + " " + item.product_name).lower()

    # Simple keyword heuristic (provisional)
    a_signals = ["launch", "ga ", "general availability", "generally available", "release"]
    b_signals = ["preview", "beta", "update", "upgrade", "expand", "rebrand"]

    for signal in a_signals:
        if signal in desc_lower:
            return ("A", f"Matched A-signal: '{signal}'")

    for signal in b_signals:
        if signal in desc_lower:
            return ("B", f"Matched B-signal: '{signal}'")

    return ("C", "No major launch or update signals detected")


# ---------- Dedup ----------

def dedup_ir_items(items: list[IrItem]) -> list[IrItem]:
    """Deduplicate IR items by normalized URL (§6.3: no counting duplicates)."""
    seen: set[str] = set()
    result: list[IrItem] = []
    for item in items:
        key = item.normalized_url
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


# ---------- Scraper (RSS / HTML) ----------

def scrape_ir_blog(
    feed_url: str,
    *,
    offline_fixture: bool = False,
) -> list[IrItem]:
    """Scrape an IR blog feed for product announcements.

    Uses RSS/Atom parsing first, falls back to HTML scraping.
    """
    if offline_fixture:
        return _fixture_ir_items()

    import feedparser
    import requests

    feed = feedparser.parse(feed_url)

    items: list[IrItem] = []
    for entry in feed.entries:
        items.append(
            IrItem(
                product_name=entry.get("title", "Unknown"),
                announcement_date=_parse_date(entry.get("published", "")),
                description=_strip_html(entry.get("summary", "")),
                source_url=entry.get("link", feed_url),
            )
        )

    if not items:
        # Fallback: try HTML scraping
        try:
            resp = requests.get(feed_url, timeout=30)
            resp.raise_for_status()
            items = _scrape_html(resp.text, feed_url)
        except Exception:
            pass

    return items


def _parse_date(date_str: str) -> str:
    """Best-effort date parsing → ISO format string."""
    if not date_str:
        return ""
    try:
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(date_str)
        return dt.date().isoformat()
    except Exception:
        return date_str[:10]


def _strip_html(html: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", html).strip()


def _scrape_html(html: str, base_url: str) -> list[IrItem]:
    """Fallback HTML scraper for blog pages."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    items: list[IrItem] = []

    for article in soup.find_all(["article", "div"], class_=re.compile(r"post|entry|blog")):
        title_el = article.find(["h1", "h2", "h3", "a"])
        title = title_el.get_text(strip=True) if title_el else "Unknown"
        link = title_el.get("href", base_url) if title_el and title_el.name == "a" else base_url
        desc_el = article.find("p")
        desc = desc_el.get_text(strip=True) if desc_el else ""
        items.append(
            IrItem(
                product_name=title,
                announcement_date="",
                description=desc,
                source_url=str(link),
            )
        )

    return items


def _fixture_ir_items() -> list[IrItem]:
    """Offline fixture items for testing."""
    return [
        IrItem(
            product_name="Copilot GA",
            announcement_date="2024-03-15",
            description="Microsoft launches Copilot as generally available product",
            source_url="https://blogs.microsoft.com/copilot-ga",
        ),
        IrItem(
            product_name="Azure AI Preview",
            announcement_date="2024-04-01",
            description="Azure AI model preview update for enterprise",
            source_url="https://azure.microsoft.com/blog/ai-preview",
        ),
    ]


def save_ir_csv(
    items: list[IrItem],
    company: str,
    settings=None,
) -> Path:
    """Save classified IR items to data/raw/ir/ir_{company}.csv."""
    if settings is None:
        settings = get_settings()

    raw_dir = Path(settings.data_dir) / "raw" / "ir"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"ir_{company.lower()}.csv"

    rows = []
    for item in items:
        rows.append({
            "product_name": item.product_name,
            "announcement_date": str(item.announcement_date),
            "description": item.description,
            "source_url": item.source_url,
            "category": item.category,
            "category_rationale": item.category_rationale,
            "review_status": item.review_status,
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)

    sha = sha256_file(path)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    append_manifest(
        raw_dir / "manifest.csv",
        filename=f"ir_{company.lower()}.csv",
        sha256=sha,
        source_url=f"ir:{company}",
        retrieved_at=retrieved_at,
    )
    write_sync_log(
        SyncRecord(
            source_type="ir_events",
            company=company,
            started_at=retrieved_at,
            finished_at=datetime.now(timezone.utc).isoformat(),
            sync_status="success",
            records_fetched=len(items),
            records_new=len(items),
            raw_file_path=str(path),
            raw_sha256=sha,
        ),
        log_dir=settings.data_dir,
    )
    return path


def main() -> None:
    settings = get_settings()
    rubric = load_rubric()
    for company, feeds in IR_FEEDS.items():
        all_items: list[IrItem] = []
        for feed in feeds:
            try:
                items = scrape_ir_blog(feed)
                all_items.extend(items)
            except Exception as exc:
                print(f"Error scraping {feed}: {exc}")
        deduped = dedup_ir_items(all_items)
        classified: list[IrItem] = []
        for item in deduped:
            cat, rationale = classify_abc(item, rubric)
            item.category = cat
            item.category_rationale = rationale
            classified.append(item)
        if classified:
            save_ir_csv(classified, company, settings=settings)
            print(f"Saved {len(classified)} IR items for {company}")


if __name__ == "__main__":
    main()
