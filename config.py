"""
Central configuration for the Hardware & Storage Price Tracker.

Keeping this separate means the scraper, dashboard, and alert modules
all read from ONE source of truth for products, thresholds, and
anti-detection settings.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = BASE_DIR / "screenshots"
LOG_DIR = BASE_DIR / "logs"
DB_PATH = LOG_DIR / "price_history.db"
CSV_PATH = LOG_DIR / "price_history.csv"

SCREENSHOT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# --- Storage backend toggle ---
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "sqlite")  # "sqlite" | "csv"

# --- Playwright behavior ---
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

# Rotate through a small pool of realistic desktop user agents.
# Keep this list short and current — stale/obviously-fake UAs are
# themselves a fingerprinting signal.
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
]

VIEWPORTS: list[dict] = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
]

# Human-like delay bounds (seconds) injected between actions.
MIN_DELAY = 0.8
MAX_DELAY = 2.6

# Retry policy for a single product scrape
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 4


@dataclass
class Product:
    """One row of the 'watchlist' — a specific product on a specific platform."""
    name: str
    platform: str          # "amazon" | "flipkart"
    url: str
    target_price: float    # alert fires when current_price <= target_price
    currency: str = "INR"


# --- Your watchlist. Add/remove products here — nothing else needs to change. ---
TARGET_PRODUCTS: list[Product] = [
    Product(
        name="Samsung 980 PRO 1TB NVMe SSD",
        platform="amazon",
        url="https://www.amazon.in/dp/B08GLX7TNT",
        target_price=6999.0,
    ),
    Product(
        name="WD Black SN770 1TB NVMe SSD",
        platform="flipkart",
        url="https://www.flipkart.com/search?q=wd+black+sn770+1tb",
        target_price=5499.0,
    ),
    # Add more Product(...) entries for your other watched SKUs.
]

# --- Alerting ---
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")
