"""
AICOR Index & Efficiency Gap Calculator
Implements Phụ lục C of CMU SRS v5.1:
- Within-company Z-Score normalization: z(x) = (x - mean) / std (NFR-09: check std == 0)
- In = z(Spend)
- Out = 0.6 * z(Product MA 4Q) + 0.4 * z(Trends MA 4Q)
- E = Out - In
"""
import math
import logging
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from src.common.config import COMPANIES

logger = logging.getLogger("aicor.calculator")


def compute_z_score(val: float, mean_val: float, std_val: float) -> float:
    """
    Computes standard z-score with zero-variance protection (NFR-09).
    If std == 0, returns 0.0.
    """
    if std_val <= 1e-9:
        return 0.0
    return (val - mean_val) / std_val


def calculate_mean_and_std(values: List[float]) -> Tuple[float, float]:
    """Calculates population mean and standard deviation for a list of values."""
    if not values:
        return 0.0, 0.0
    n = len(values)
    mean_val = sum(values) / n
    variance = sum((x - mean_val) ** 2 for x in values) / n
    std_val = math.sqrt(variance)
    return mean_val, std_val


def calculate_indices(
    fact_dict: Dict[Tuple[int, str], Dict[str, Any]],
    w_product: float = 0.6,
    w_trends: float = 0.4,
) -> Dict[Tuple[int, str], Dict[str, Any]]:
    """
    Computes within-company z-scores, In, Out, and E for all company-quarters.
    Updates fact_dict in-place and returns it.
    """
    # 1. Group historical series by company
    company_data = defaultdict(lambda: {"in_raw": [], "prod_ma": [], "trends_ma": [], "quarters": []})

    for (cid, q), row in sorted(fact_dict.items(), key=lambda x: (x[0][0], x[0][1])):
        # Determine raw input spend: Microsoft uses rnd_spend, others use ai_spend_est
        raw_in = row["rnd_spend"] if cid == 1 else row["ai_spend_est"]
        raw_in_val = float(raw_in) if raw_in is not None else 0.0

        company_data[cid]["quarters"].append(q)
        company_data[cid]["in_raw"].append(raw_in_val)
        company_data[cid]["prod_ma"].append(row["product_ma4q"])
        company_data[cid]["trends_ma"].append(row["trends_ma4q"])

    # 2. Compute within-company statistics
    stats = {}
    for cid, series in company_data.items():
        in_mean, in_std = calculate_mean_and_std(series["in_raw"])
        prod_mean, prod_std = calculate_mean_and_std(series["prod_ma"])
        trends_mean, trends_std = calculate_mean_and_std(series["trends_ma"])

        stats[cid] = {
            "in": (in_mean, in_std),
            "prod": (prod_mean, prod_std),
            "trends": (trends_mean, trends_std),
        }
        logger.info(
            f"Company {COMPANIES[cid]['name']} stats: "
            f"In(mean={in_mean:.1e}, std={in_std:.1e}), "
            f"ProdMA(mean={prod_mean:.2f}, std={prod_std:.2f}), "
            f"TrendsMA(mean={trends_mean:.2f}, std={trends_std:.2f})"
        )

    # 3. Calculate In, Out, E for each quarter
    for (cid, q), row in fact_dict.items():
        st = stats[cid]
        raw_in = row["rnd_spend"] if cid == 1 else row["ai_spend_est"]
        raw_in_val = float(raw_in) if raw_in is not None else 0.0

        z_in = compute_z_score(raw_in_val, st["in"][0], st["in"][1])
        z_prod = compute_z_score(row["product_ma4q"], st["prod"][0], st["prod"][1])
        z_trends = compute_z_score(row["trends_ma4q"], st["trends"][0], st["trends"][1])

        out_score = (w_product * z_prod) + (w_trends * z_trends)
        e_score = out_score - z_in

        row["in_score"] = round(z_in, 3)
        row["out_score"] = round(out_score, 3)
        row["e_score"] = round(e_score, 3)

    return fact_dict
