"""
AICOR Sensitivity Analysis Engine
Implements Phụ lục C.8 of CMU SRS v5.1:
Runs calculations across 3 weight sets:
- Set 1 (Default): Product 0.6, Trends 0.4
- Set 2 (Balanced): Product 0.5, Trends 0.5
- Set 3 (Product-heavy): Product 0.7, Trends 0.3
Checks if relative ranking between the 3 companies changes across presets.
Marks results as 'stable' or 'sensitive'.
"""
import copy
from typing import Dict, List, Any, Tuple
from src.common.config import SENSITIVITY_WEIGHT_SETS, COMPANIES
from src.computation.calculator import calculate_indices


def run_sensitivity_analysis(
    base_fact_dict: Dict[Tuple[int, str], Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Evaluates E scores for all 3 companies under the 3 sensitivity weight presets.
    Returns rows formatted for sensitivity_analysis.csv.
    """
    quarters = sorted(list(set(q for cid, q in base_fact_dict.keys())))
    sensitivity_rows = []

    # Run index calculation for each weight set
    results_by_set = {}
    for w_cfg in SENSITIVITY_WEIGHT_SETS:
        set_name = w_cfg["name"]
        fact_copy = copy.deepcopy(base_fact_dict)
        calc_res = calculate_indices(fact_copy, w_product=w_cfg["w_product"], w_trends=w_cfg["w_trends"])
        results_by_set[set_name] = (w_cfg, calc_res)

    # For each quarter, evaluate ranking across all sets
    for q in quarters:
        rankings_for_quarter = {}

        # 1. Collect scores and ranking for each set
        for set_name, (w_cfg, fact_res) in results_by_set.items():
            msft_row = fact_res.get((1, q), {})
            openai_row = fact_res.get((2, q), {})
            anthropic_row = fact_res.get((3, q), {})

            scores = [
                ("Microsoft", msft_row.get("e_score", 0.0)),
                ("OpenAI", openai_row.get("e_score", 0.0)),
                ("Anthropic", anthropic_row.get("e_score", 0.0)),
            ]
            # Rank descending by E
            scores.sort(key=lambda x: x[1], reverse=True)
            rank_order = " > ".join(name for name, sc in scores)
            rankings_for_quarter[set_name] = (rank_order, msft_row, openai_row, anthropic_row)

        # 2. Check if ranking order is identical across all 3 sets
        distinct_rankings = set(rank_order for rank_order, _, _, _ in rankings_for_quarter.values())
        is_quarter_stable = (len(distinct_rankings) == 1)

        # 3. Create output records for each weight set
        for set_name, (w_cfg, _) in results_by_set.items():
            rank_order, msft_r, openai_r, anthropic_r = rankings_for_quarter[set_name]
            sensitivity_rows.append({
                "quarter": q,
                "weight_set": set_name,
                "product_weight": w_cfg["w_product"],
                "trends_weight": w_cfg["w_trends"],
                "msft_out": msft_r.get("out_score", 0.0),
                "openai_out": openai_r.get("out_score", 0.0),
                "anthropic_out": anthropic_r.get("out_score", 0.0),
                "msft_e": msft_r.get("e_score", 0.0),
                "openai_e": openai_r.get("e_score", 0.0),
                "anthropic_e": anthropic_r.get("e_score", 0.0),
                "ranking_order": rank_order,
                "is_stable": is_quarter_stable,
            })

    return sensitivity_rows
