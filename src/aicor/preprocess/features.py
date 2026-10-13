"""Derived feature definitions with metadata.

Implements: SPEC §6.1 — every derived feature must have method, source, confidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FeatureMeta:
    """Metadata for a derived feature (§6.1).

    Every derived feature in the panel must carry this metadata
    for traceability and trust.
    """

    name: str
    definition: str
    calculation_method: str
    reported_or_derived: str = "derived"
    proxy: bool = False
    confidence: str = "HIGH"
    source_fields: tuple[str, ...] = ()


# ---------- Feature registry ----------

FEATURE_REGISTRY: dict[str, FeatureMeta] = {
    "rd_intensity": FeatureMeta(
        name="rd_intensity",
        definition="R&D Expense / Revenue",
        calculation_method="rd_expense / revenue",
        proxy=True,
        confidence="LOW",
        source_fields=("rd_expense", "revenue"),
    ),
    "capex_intensity": FeatureMeta(
        name="capex_intensity",
        definition="CapEx / Revenue",
        calculation_method="capex / revenue",
        proxy=False,
        confidence="MEDIUM",
        source_fields=("capex", "revenue"),
    ),
    "product_score": FeatureMeta(
        name="product_score",
        definition="3*A + 2*B + 1*C product announcement score",
        calculation_method="weighted_count(A=3, B=2, C=1)",
        proxy=False,
        confidence="MEDIUM",
        source_fields=("ir_category_counts",),
    ),
    "is_msft": FeatureMeta(
        name="is_msft",
        definition="Binary dummy: 1 if company is MSFT, 0 if GOOGL",
        calculation_method="company == 'MSFT'",
        reported_or_derived="derived",
        proxy=False,
        confidence="HIGH",
        source_fields=("company",),
    ),
}
