"""
AICOR Configuration & Paths
Defines project paths, company constants, and default weight presets.
"""
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SEEDS_DATA_DIR = DATA_DIR / "seeds"

# Canonical Company Definitions
COMPANIES = {
    1: {"id": 1, "name": "Microsoft", "ticker": "MSFT", "is_public": True},
    2: {"id": 2, "name": "OpenAI", "ticker": "", "is_public": False},
    3: {"id": 3, "name": "Anthropic", "ticker": "", "is_public": False},
}

COMPANY_NAME_TO_ID = {
    "microsoft": 1,
    "msft": 1,
    "openai": 2,
    "anthropic": 3,
}

# Product Rubric Points (Appendix A)
PRODUCT_CATEGORY_POINTS = {
    "A": 3.0,  # Major new model with technical report / dedicated launch
    "B": 2.0,  # Model variant, major API, significant expansion
    "C": 1.0,  # Product feature, integration, minor update
}

# Tripartite Relationship Types (Appendix B)
VALID_RELATIONSHIP_TYPES = {"invest", "partner", "compete", "statement"}

# Estimation Confidence Levels (Appendix C.4)
VALID_CONFIDENCE_LEVELS = {"high", "medium", "low"}

# Sensitivity Analysis Weight Sets (Appendix C.8)
SENSITIVITY_WEIGHT_SETS = [
    {"name": "Set 1 (Default)", "w_product": 0.6, "w_trends": 0.4},
    {"name": "Set 2 (Balanced)", "w_product": 0.5, "w_trends": 0.5},
    {"name": "Set 3 (Product-heavy)", "w_product": 0.7, "w_trends": 0.3},
]

# Anti-ban & Network Settings
SEC_USER_AGENT = "AICOR Academic Research Bot/1.0 (contact@aicor-project.edu)"
SEC_RATE_LIMIT_DELAY = 0.12  # At most 10 requests per second per SEC guidelines
TRENDS_MIN_DELAY = 3.0       # Minimum delay between pytrends calls
TRENDS_MAX_DELAY = 6.0       # Maximum delay with jitter
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0
