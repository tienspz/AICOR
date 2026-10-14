"""Unit tests for IR polite fetch and feed rate limiting."""

import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from aicor.config import get_settings
from aicor.sources.ir import (
    IR_REQUEST_DELAY_SECONDS,
    IrItem,
    _parse_date,
    dedup_ir_items,
    polite_fetch,
    scrape_ir_blog,
)


def test_polite_fetch_sends_ua_and_sleeps(monkeypatch):
    """Ensure polite_fetch sleeps for IR_REQUEST_DELAY_SECONDS and attaches SEC_USER_AGENT."""
    sleep_calls = []
    sent_headers = {}

    def mock_sleep(seconds):
        sleep_calls.append(seconds)

    class MockResponse:
        status_code = 200
        text = "<html><body>Mock content</body></html>"

        def raise_for_status(self):
            pass

    def mock_get(url, headers=None, timeout=None):
        if headers:
            sent_headers.update(headers)
        return MockResponse()

    monkeypatch.setattr(time, "sleep", mock_sleep)
    monkeypatch.setattr(requests, "get", mock_get)

    settings = get_settings()
    resp = polite_fetch("https://research.google/blog/rss/", settings=settings)

    assert resp.status_code == 200
    assert len(sleep_calls) == 1
    assert sleep_calls[0] == IR_REQUEST_DELAY_SECONDS
    assert sent_headers.get("User-Agent") == settings.sec_user_agent


def test_scrape_ir_blog_with_feedparser_uses_ua_and_sleeps(monkeypatch):
    """Ensure scrape_ir_blog passes request_headers with UA and delays."""
    import feedparser

    sleep_calls = []
    captured_kwargs = {}

    def mock_sleep(seconds):
        sleep_calls.append(seconds)

    def mock_parse(url, **kwargs):
        captured_kwargs.update(kwargs)
        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "title": "New Research",
                "published": "2024-06-01T12:00:00Z",
                "summary": "Summary of research paper",
                "link": "https://research.google/blog/new-research",
            }
        ]
        return mock_feed

    monkeypatch.setattr(time, "sleep", mock_sleep)
    monkeypatch.setattr(feedparser, "parse", mock_parse)

    settings = get_settings()
    items = scrape_ir_blog("https://research.google/blog/rss/", settings=settings)

    assert len(items) == 1
    assert len(sleep_calls) >= 1
    assert sleep_calls[0] == IR_REQUEST_DELAY_SECONDS
    assert captured_kwargs.get("request_headers", {}).get("User-Agent") == settings.sec_user_agent


def test_scrape_ir_blog_fallback_to_polite_fetch(monkeypatch):
    """When feed has 0 entries, fallback to HTML scraping using polite_fetch."""
    import feedparser

    def mock_parse(url, **kwargs):
        mock_feed = MagicMock()
        mock_feed.entries = []
        return mock_feed

    html_content = """
    <html>
      <article class="post">
        <h2><a href="https://research.google/blog/fallback">Fallback Article</a></h2>
        <p>Description of fallback</p>
      </article>
    </html>
    """

    class MockResponse:
        status_code = 200
        text = html_content

        def raise_for_status(self):
            pass

    monkeypatch.setattr(feedparser, "parse", mock_parse)
    monkeypatch.setattr("aicor.sources.ir.polite_fetch", lambda url, settings=None: MockResponse())

    items = scrape_ir_blog("https://research.google/blog/")
    assert len(items) == 1
    assert items[0].product_name == "Fallback Article"
    assert items[0].source_url == "https://research.google/blog/fallback"
