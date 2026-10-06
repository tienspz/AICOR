"""
Tests for Task BE-02: RSS/Blog scraper (mock feeds, no network).
"""
from src.collection.scrapers.blog_scraper import (
    classify_category,
    is_ai_related,
    parse_feed_xml,
)


MOCK_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>OpenAI News</title>
<item>
<title>Introducing GPT-5: our new frontier model (technical report)</title>
<link>https://openai.com/index/gpt-5/</link>
<description>Technical report for the new model.</description>
<pubDate>Mon, 10 Feb 2025 10:00:00 GMT</pubDate>
</item>
<item>
<title>New API preview for enterprise fine-tuning</title>
<link>https://openai.com/index/api-preview/</link>
<description>API preview with turbo inference.</description>
<pubDate>Tue, 11 Mar 2025 10:00:00 GMT</pubDate>
</item>
<item>
<title>Office holiday party photos</title>
<link>https://openai.com/index/party/</link>
<description>Team celebration, no product news.</description>
<pubDate>Wed, 12 Mar 2025 10:00:00 GMT</pubDate>
</item>
<item>
<title></title>
<link>https://openai.com/index/empty/</link>
<description>No title, must be skipped.</description>
<pubDate>Thu, 13 Mar 2025 10:00:00 GMT</pubDate>
</item>
</channel>
</rss>
"""


def test_classify_category_rubric():
    assert classify_category("Introducing GPT-5 technical report") == "A"
    assert classify_category("New API preview for enterprise") == "B"
    assert classify_category("Copilot feature update with new integration") == "C"


def test_parse_rss_xml_filters_and_tags():
    events = parse_feed_xml(MOCK_RSS, 2, "OpenAI", source_hint="openai")
    # 2 valid product items; party post has no rubric keywords -> still C but kept
    # for vendor feed; empty-title item must be skipped.
    urls = [e["source_url"] for e in events]
    assert "https://openai.com/index/gpt-5/" in urls
    assert "https://openai.com/index/api-preview/" in urls
    assert "https://openai.com/index/empty/" not in urls
    by_url = {e["source_url"]: e for e in events}
    assert by_url["https://openai.com/index/gpt-5/"]["category"] == "A"
    assert by_url["https://openai.com/index/gpt-5/"]["points"] == 3.0
    assert by_url["https://openai.com/index/gpt-5/"]["quarter"] == "2025-Q1"
    assert by_url["https://openai.com/index/api-preview/"]["category"] == "B"


def test_microsoft_feed_filters_non_ai():
    rss = MOCK_RSS.replace("Office holiday party photos", "Quarterly earnings call transcript")
    events = parse_feed_xml(rss, 1, "Microsoft", source_hint="microsoft")
    urls = [e["source_url"] for e in events]
    assert "https://openai.com/index/party/" not in urls  # non-AI filtered
    assert is_ai_related("Copilot feature update", "", "microsoft") is True
    assert is_ai_related("Quarterly earnings call transcript", "finance results", "microsoft") is False
