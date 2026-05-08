"""Preset configuration management for batch analysis."""
import json
import datetime
import signal
import os
import subprocess
import atexit
from pathlib import Path
from typing import Optional, Dict, Any, List

DEFAULT_PRESET_DIR = Path.home() / ".tradingagents"
DEFAULT_PRESET_FILE = DEFAULT_PRESET_DIR / "daily_preset.json"
FUNDAMENTALS_CACHE_FILE = DEFAULT_PRESET_DIR / "fundamentals_cache.json"


def get_default_preset() -> Dict[str, Any]:
    """Return default preset configuration."""
    return {
        "output_language": "English",
        "llm_provider": "ollama",
        "shallow_thinker": "phi4-mini:latest",
        "deep_thinker": "phi4-mini:latest",
        "backend_url": "http://localhost:11434",
        "research_depth": 1,
        "google_thinking_level": None,
        "openai_reasoning_effort": None,
        "anthropic_effort": None,
        "analysts": ["market", "social", "news", "fundamentals"],
        "fundamentals_frequency": "weekly",  # daily, weekly, monthly, never, always
        "fundamentals_day": "monday",         # day to run fundamentals (if weekly)
    }


def create_default_preset() -> Path:
    """Create a default preset file if it doesn't exist. Returns the file path."""
    DEFAULT_PRESET_DIR.mkdir(parents=True, exist_ok=True)

    if not DEFAULT_PRESET_FILE.exists():
        with open(DEFAULT_PRESET_FILE, "w", encoding="utf-8") as f:
            json.dump(get_default_preset(), f, indent=2)

    return DEFAULT_PRESET_FILE


def load_preset(preset_path: Optional[str] = None) -> Dict[str, Any]:
    """Load preset configuration from file.

    Args:
        preset_path: Path to preset file. If None, use default location.

    Returns:
        Preset configuration dict

    Raises:
        FileNotFoundError: If preset file doesn't exist and can't be created
    """
    if preset_path:
        file_path = Path(preset_path)
    else:
        file_path = DEFAULT_PRESET_FILE

    if not file_path.exists():
        create_default_preset()
        file_path = DEFAULT_PRESET_FILE

    with open(file_path, "r", encoding="utf-8") as f:
        preset = json.load(f)

    return preset


def load_stocks_from_file(stocks_file: str) -> list[str]:
    """Load stock tickers from a file (one per line, or comma-separated).

    Args:
        stocks_file: Path to file with stock symbols

    Returns:
        List of ticker symbols

    Raises:
        FileNotFoundError: If stocks file doesn't exist
        ValueError: If no stocks found in file
    """
    file_path = Path(stocks_file)

    if not file_path.exists():
        raise FileNotFoundError(f"Stocks file not found: {stocks_file}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse stocks (handle both newline-separated and comma-separated)
    stocks = []
    for line in content.strip().split("\n"):
        # Skip comments and empty lines
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Split by comma and strip whitespace
        symbols = [s.strip().upper() for s in line.split(",")]
        stocks.extend([s for s in symbols if s])

    if not stocks:
        raise ValueError("No stocks found in file")

    return stocks


def create_sample_stocks_file(output_file: str = "stocks_today.txt") -> Path:
    """Create a sample stocks file for daily batch analysis.

    Args:
        output_file: Name of output file

    Returns:
        Path to created file
    """
    sample_content = """# Daily stock analysis list - edit with your 10 stocks
SPY
QQQ
AAPL
MSFT
GOOGL
AMZN
TSLA
NVDA
META
NFLX
"""

    file_path = Path(output_file)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(sample_content)

    return file_path


def load_fundamentals_cache() -> Dict[str, str]:
    """Load fundamentals analysis cache (tracks when each stock was last analyzed).

    Tries S3 first, falls back to local file.

    Returns:
        Dict mapping ticker -> last_analysis_date (YYYY-MM-DD)
    """
    from tradingagents.storage import get_s3_storage

    s3 = get_s3_storage()
    if s3.enabled:
        return s3.load_cache()

    # Fallback to local file
    if not FUNDAMENTALS_CACHE_FILE.exists():
        return {}

    with open(FUNDAMENTALS_CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_fundamentals_cache(cache: Dict[str, str]) -> None:
    """Save fundamentals analysis cache to S3 (preferred) or local file."""
    from tradingagents.storage import get_s3_storage

    s3 = get_s3_storage()
    if s3.enabled:
        s3.save_cache(cache)
        return

    # Fallback to local file
    FUNDAMENTALS_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FUNDAMENTALS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def should_run_fundamentals(
    ticker: str,
    preset: Dict[str, Any],
    analysis_date: str = None,
) -> bool:
    """Determine if fundamentals analyst should run for this stock.

    Args:
        ticker: Stock ticker symbol
        preset: Preset configuration dict
        analysis_date: Analysis date (YYYY-MM-DD). Default: today

    Returns:
        True if fundamentals should run, False otherwise
    """
    if analysis_date is None:
        analysis_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Parse configuration
    freq = preset.get("fundamentals_frequency", "weekly").lower()
    fundamentals_day = preset.get("fundamentals_day", "monday").lower()

    # Never run
    if freq == "never":
        return False

    # Always run
    if freq == "always":
        return True

    # Load cache and check last run
    cache = load_fundamentals_cache()
    last_run = cache.get(ticker)

    # New stock (never analyzed)
    if last_run is None:
        return True

    # Parse dates
    today = datetime.datetime.strptime(analysis_date, "%Y-%m-%d")
    last_run_date = datetime.datetime.strptime(last_run, "%Y-%m-%d")
    days_since = (today - last_run_date).days

    if freq == "daily":
        return days_since >= 1
    elif freq == "weekly":
        # Check if today is the configured day (e.g., Monday)
        today_weekday = today.strftime("%A").lower()
        if today_weekday == fundamentals_day:
            return days_since >= 7
        return False
    elif freq == "monthly":
        return days_since >= 30

    return True


def update_fundamentals_cache(ticker: str, analysis_date: str = None) -> None:
    """Record that fundamentals was analyzed for a stock on the given date.

    Args:
        ticker: Stock ticker symbol
        analysis_date: Analysis date (YYYY-MM-DD). Default: today
    """
    if analysis_date is None:
        analysis_date = datetime.datetime.now().strftime("%Y-%m-%d")

    cache = load_fundamentals_cache()
    cache[ticker] = analysis_date
    save_fundamentals_cache(cache)


def sync_to_s3(cache_file: Path, activity_db: Path = None, reports_dir: Path = None) -> None:
    """Upload activity database to S3.

    Note: Cache and reports are now uploaded directly via S3Storage class.
    This function is a fallback for activity.db syncing on process exit.

    Args:
        cache_file: Path to fundamentals_cache.json (kept for backward compatibility)
        activity_db: Path to activity.db
        reports_dir: Path to daily reports directory (deprecated, not used)
    """
    from tradingagents.storage import get_s3_storage

    s3 = get_s3_storage()
    if not s3.enabled:
        return

    # Upload activity.db as fallback on exit
    if activity_db and activity_db.exists():
        s3.upload_activity_db(activity_db)


def manual_sync_reports(date: str = None) -> bool:
    """Manually sync activity.db to S3 (reports are auto-synced after each analysis).

    Args:
        date: Date parameter (kept for backward compatibility, not used)

    Returns:
        True if sync was successful, False if S3 not configured or error
    """
    from tradingagents.storage import get_s3_storage

    s3 = get_s3_storage()
    if not s3.enabled:
        return False

    activity_db = DEFAULT_PRESET_DIR / "activity.db"
    if not activity_db.exists():
        return False

    return s3.upload_activity_db(activity_db) is not None


def setup_sync_trap(cache_file: Path = None, activity_db: Path = None, reports_dir: Path = None) -> None:
    """Register signal handlers to sync files to S3 on exit (for GPU instances).

    Syncs on: SIGTERM, SIGINT, normal exit. Requires TRADINGAGENTS_S3_BUCKET env var.

    Args:
        cache_file: Path to fundamentals_cache.json (default: ~/.tradingagents/fundamentals_cache.json)
        activity_db: Path to activity.db (default: ~/.tradingagents/activity.db)
        reports_dir: Path to daily reports directory (default: ~/.tradingagents/logs/daily)
    """
    if cache_file is None:
        cache_file = FUNDAMENTALS_CACHE_FILE
    if activity_db is None:
        activity_db = DEFAULT_PRESET_DIR / "activity.db"
    if reports_dir is None:
        reports_dir = DEFAULT_PRESET_DIR / "logs" / "daily"

    if not os.getenv("TRADINGAGENTS_S3_BUCKET"):
        return

    def on_exit(signum=None, frame=None):
        sync_to_s3(cache_file, activity_db, reports_dir)

    signal.signal(signal.SIGTERM, on_exit)
    signal.signal(signal.SIGINT, on_exit)
    atexit.register(on_exit)
