"""
Tests for Task BE-03: SEC EDGAR 10-Q filing monitor (mock Atom, no network).
"""
import csv

from src.collection.edgar_monitor import check_new_filings, parse_atom_latest


MOCK_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>EDGAR Current Filings</title>
<entry>
<title>10-Q - MICROSOFT CORP (0000789019)</title>
<link href="https://www.sec.gov/Archives/edgar/data/789019/000095017025001234/"/>
<updated>2025-10-29T16:00:00-04:00</updated>
</entry>
<entry>
<title>10-Q - MICROSOFT CORP (0000789019)</title>
<link href="https://www.sec.gov/Archives/edgar/data/789019/000095017025000999/"/>
<updated>2025-07-30T16:00:00-04:00</updated>
</entry>
</feed>
"""


def test_parse_atom_latest_picks_newest():
    latest = parse_atom_latest(MOCK_ATOM)
    assert latest is not None
    assert latest[0] == "2025-10-29"


def _write_rnd_raw(tmp_path, filing_date):
    with open(tmp_path / "rnd_msft_raw.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["company_id", "company_name", "filing_date", "quarter", "rnd_spend", "source_url"],
        )
        w.writeheader()
        w.writerow(
            {
                "company_id": 1, "company_name": "Microsoft", "filing_date": filing_date,
                "quarter": "2025-Q3", "rnd_spend": 8700000000, "source_url": "https://www.sec.gov/",
            }
        )


def test_check_new_filings_detects_newer(tmp_path):
    _write_rnd_raw(tmp_path, "2025-07-30")
    assert check_new_filings(atom_xml=MOCK_ATOM, raw_dir=tmp_path) is True


def test_check_new_filings_no_new_when_current(tmp_path):
    _write_rnd_raw(tmp_path, "2025-10-29")
    assert check_new_filings(atom_xml=MOCK_ATOM, raw_dir=tmp_path) is False
