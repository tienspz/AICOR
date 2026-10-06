"""
AICOR Aggregator Subsystem
Aggregates cleaned data by company and quarter:
- Product Score: 3*A + 2*B + 1*C (Phụ lục A)
- Quarterly average Google Trends (trends_qavg)
- Rolling 4-quarter Moving Averages (Product MA 4Q & Trends MA 4Q)
"""
import csv
import logging
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from pathlib import Path

from src.common.config import CLEANED_DATA_DIR, COMPANIES

logger = logging.getLogger("aicor.aggregator")


def build_company_quarter_index(start_year: int = 2022, end_year: int = 2026, max_q: int = 2) -> List[Tuple[int, str]]:
    """Builds sorted list of (company_id, quarter) pairs from 2022-Q1 to end_year-Qn."""
    cq_list = []
    quarters = []
    for y in range(start_year, end_year + 1):
        for q in range(1, 5):
            if y == end_year and q > max_q:
                break
            quarters.append(f"{y}-Q{q}")

    for cid in sorted(COMPANIES.keys()):
        for q in quarters:
            cq_list.append((cid, q))
    return cq_list


def aggregate_quarterly_data(cleaned_dir: Path = CLEANED_DATA_DIR) -> Dict[Tuple[int, str], Dict[str, Any]]:
    """
    Reads cleaned CSV files and aggregates metrics by (company_id, quarter).
    Returns a dictionary keyed by (company_id, quarter).
    """
    # 1. Initialize dictionary for all company-quarters
    cq_index = build_company_quarter_index()
    fact_dict = {}
    for cid, q in cq_index:
        fact_dict[(cid, q)] = {
            "company_id": cid,
            "company_name": COMPANIES[cid]["name"],
            "quarter": q,
            "rnd_spend": None,
            "ai_spend_est": None,
            "est_confidence": "medium" if cid != 1 else "high",
            "trends_qavg": 0.0,
            "product_score": 0.0,
            "product_ma4q": 0.0,
            "trends_ma4q": 0.0,
            "in_score": 0.0,
            "out_score": 0.0,
            "e_score": 0.0,
            "valid_from": f"{q[:4]}-{'03-31' if 'Q1' in q else '06-30' if 'Q2' in q else '09-30' if 'Q3' in q else '12-31'}",
        }

    # 2. Ingest Microsoft R&D spend
    rnd_file = cleaned_dir / "rnd_msft_clean.csv"
    if rnd_file.exists():
        with open(rnd_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                cid = int(r["company_id"])
                q = r["quarter"]
                val = float(r["rnd_spend"])
                if (cid, q) in fact_dict:
                    fact_dict[(cid, q)]["rnd_spend"] = val
                    fact_dict[(cid, q)]["est_confidence"] = "high"

    # 3. Ingest AI spend estimates (OpenAI & Anthropic)
    spend_file = cleaned_dir / "ai_spend_est_clean.csv"
    if spend_file.exists():
        with open(spend_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                cid = int(r["company_id"])
                q = r["quarter"]
                val = float(r["ai_spend_est"])
                conf = r.get("est_confidence", "medium")
                if (cid, q) in fact_dict:
                    fact_dict[(cid, q)]["ai_spend_est"] = val
                    fact_dict[(cid, q)]["est_confidence"] = conf

    # 4. Ingest Product Launches & sum points (Phụ lục A: 3A + 2B + 1C)
    launch_file = cleaned_dir / "events_launch_clean.csv"
    if launch_file.exists():
        with open(launch_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                cid = int(r["company_id"])
                q = r["quarter"]
                pts = float(r.get("points", 1.0))
                if (cid, q) in fact_dict:
                    fact_dict[(cid, q)]["product_score"] += pts

    # 5. Ingest Google Trends & calculate quarterly average
    trends_file = cleaned_dir / "trends_clean.csv"
    trends_sums = defaultdict(float)
    trends_counts = defaultdict(int)
    if trends_file.exists():
        with open(trends_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                cid = int(r["company_id"])
                q = r["quarter"]
                val = float(r["trend_value"])
                trends_sums[(cid, q)] += val
                trends_counts[(cid, q)] += 1

        for (cid, q), total in trends_sums.items():
            if (cid, q) in fact_dict and trends_counts[(cid, q)] > 0:
                fact_dict[(cid, q)]["trends_qavg"] = round(total / trends_counts[(cid, q)], 2)

    # 6. Compute 4-quarter rolling moving averages (MA 4Q) for each company
    for cid in COMPANIES.keys():
        comp_quarters = [q for c, q in cq_index if c == cid]
        comp_quarters.sort()

        product_history = []
        trends_history = []

        for q in comp_quarters:
            row = fact_dict[(cid, q)]
            product_history.append(row["product_score"])
            trends_history.append(row["trends_qavg"])

            # 4-quarter rolling window
            window_prod = product_history[-4:]
            window_trends = trends_history[-4:]

            row["product_ma4q"] = round(sum(window_prod) / len(window_prod), 3)
            row["trends_ma4q"] = round(sum(window_trends) / len(window_trends), 3)

    return fact_dict
