"""
app/config.py
Configuration and settings for the ZeroWaste Grocer API.
"""
import os
from typing import Optional
from pathlib import Path
from datetime import date
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "ZeroWaste Grocer API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database Settings
    DB_NAME: str = os.getenv("DB_NAME", "zerowaste.db")

    # Artifact paths
    ML_ARTIFACTS_DIR: Path = Path(os.getenv("ML_ARTIFACTS_DIR", str(BASE_DIR / "ml_artifacts")))
    MODEL_PATH: Path = ML_ARTIFACTS_DIR / "production_model.joblib"
    FEATURE_NAMES_PATH: Path = ML_ARTIFACTS_DIR / "master_feature_names.joblib"

    EXPECTED_FEATURE_COUNT: int = 192

    # Level B3 Domain Mathematics Parameters
    DEMAND_SCALE: float = float(os.getenv("DEMAND_SCALE", "250.0"))        # Continuous ML target (~0.08) to physical retail units
    DEFAULT_SALVAGE_PCT: float = 0.20  # Salvage recovery factor (20% of unit cost) for overage cost Co
    SIGMA_FACTOR: float = 0.15         # Forecast error standard deviation (15% of forecasted units)

    # As-of Date Override for Historical / Dataset Replay (e.g. '2023-06-30')
    AS_OF_DATE: Optional[str] = os.getenv("AS_OF_DATE", None)

    # Level 3 Markdown Scheduler & Dismiss Settings
    MARKDOWN_JOB_HOUR: int = 6
    MARKDOWN_JOB_MINUTE: int = 0
    SCHEDULER_ENABLED: bool = True
    DISMISS_POSTPONE_HOURS: int = 6

    def get_effective_today(self) -> date:
        """Returns June 30, 2023 (or AS_OF_DATE) when using zerowaste_real.db, else date.today() for synthetic DB."""
        if "real" in str(self.DB_NAME).lower():
            if self.AS_OF_DATE:
                try:
                    return date.fromisoformat(self.AS_OF_DATE)
                except Exception:
                    pass
            return date(2023, 6, 30)
        return date.today()

settings = Settings()

# Alias export for backward compatibility
DEMAND_SCALE: float = settings.DEMAND_SCALE
