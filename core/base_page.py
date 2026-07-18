"""
BasePage — the Page Object Model foundation.

Every site-specific page class (AmazonPage, FlipkartPage, ...) inherits
from this. This is where cross-cutting concerns live:
    - human-like randomized delays
    - resilient navigation (network-idle waits + retries)
    - automatic screenshot-on-failure
    - a uniform extraction contract (`extract()` returns the schema dict)

Subclasses only define WHERE things are (locators) and HOW to parse text
(currency-specific parsing), never HOW to wait or retry.
"""
from __future__ import annotations

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

import config

logger = logging.getLogger("price_tracker.page")


class ProductNotFoundError(Exception):
    """Raised when a price/availability selector can't be located after retries."""


class BasePage(ABC):
    """Abstract base for a single product page on a single platform."""

    PLATFORM_NAME: str = "unknown"

    # Subclasses override these with real CSS/XPath/text selectors.
    PRICE_SELECTOR: str = ""
    AVAILABILITY_SELECTOR: str = ""
    TITLE_SELECTOR: str = ""

    def __init__(self, page: Page):
        self.page = page

    # ---------- Resilience primitives (shared by every site) ----------

    async def human_delay(self, min_s: float = None, max_s: float = None) -> None:
        """Sleep a randomized interval to avoid a robotic, evenly-timed
        request pattern — one of the simplest bot-detection tripwires."""
        lo = min_s if min_s is not None else config.MIN_DELAY
        hi = max_s if max_s is not None else config.MAX_DELAY
        await asyncio.sleep(random.uniform(lo, hi))

    async def goto_with_retry(self, url: str) -> None:
        """Navigate with auto-wait for network idle, retrying transient
        failures (timeouts, throttling) with exponential-ish backoff."""
        last_exc: Exception | None = None
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                # Give SPA/JS-heavy pages a chance to settle after the
                # initial DOM load — this is the "bypass JS rendering"
                # part of the pitch: we wait for the network to go quiet
                # rather than scraping a half-rendered page.
                await self.page.wait_for_load_state("networkidle", timeout=15_000)
                await self.human_delay()
                return
            except PlaywrightTimeoutError as exc:
                last_exc = exc
                wait_s = config.RETRY_BACKOFF_SECONDS * attempt
                logger.warning(
                    "Navigation attempt %d/%d failed for %s (%s). Retrying in %ds.",
                    attempt, config.MAX_RETRIES, url, exc, wait_s,
                )
                await asyncio.sleep(wait_s)
        raise ProductNotFoundError(f"Could not load {url} after {config.MAX_RETRIES} attempts") from last_exc

    async def capture_error_screenshot(self, product_name: str) -> str:
        """Save a timestamped screenshot for debugging when a selector
        can't be found — critical for diagnosing silent site-layout changes."""
        safe_name = "".join(c if c.isalnum() else "_" for c in product_name)[:60]
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = config.SCREENSHOT_DIR / f"{self.PLATFORM_NAME}_{safe_name}_{ts}.png"
        try:
            await self.page.screenshot(path=str(path), full_page=True)
            logger.error("Selector failure screenshot saved: %s", path)
        except Exception as exc:  # screenshotting itself can fail (page closed, etc.)
            logger.error("Failed to capture error screenshot: %s", exc)
        return str(path)

    async def safe_text(self, selector: str, timeout_ms: int = 8000) -> str | None:
        """Return inner_text of the first matching element, or None
        (never raises) — lets callers decide how to handle 'missing'."""
        try:
            locator = self.page.locator(selector).first
            await locator.wait_for(state="visible", timeout=timeout_ms)
            return (await locator.inner_text()).strip()
        except PlaywrightTimeoutError:
            return None

    # ---------- Contract every site-specific page must implement ----------

    @abstractmethod
    def parse_price(self, raw_text: str) -> tuple[float, str]:
        """Parse a raw price string into (numeric_value, currency_code).
        Currency symbols/formats differ per site — this stays site-specific."""

    @abstractmethod
    async def get_availability(self) -> str:
        """Return a normalized status string, e.g. 'in_stock' / 'out_of_stock'."""

    async def extract(self, url: str, product_name: str, target_price: float) -> dict:
        """Full extraction pipeline. Returns a dict matching the shared
        data schema. Raises ProductNotFoundError on unrecoverable failure
        (after capturing a debug screenshot)."""
        try:
            await self.goto_with_retry(url)

            raw_price = await self.safe_text(self.PRICE_SELECTOR)
            if raw_price is None:
                await self.capture_error_screenshot(product_name)
                raise ProductNotFoundError(
                    f"Price selector '{self.PRICE_SELECTOR}' not found for '{product_name}'"
                )

            price_value, currency = self.parse_price(raw_price)
            availability = await self.get_availability()

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "product_name": product_name,
                "platform": self.PLATFORM_NAME,
                "target_url": url,
                "current_price": price_value,
                "currency": currency,
                "availability_status": availability,
            }
        except ProductNotFoundError:
            raise
        except Exception as exc:
            # Catch-all so ONE bad product never crashes the whole batch run.
            await self.capture_error_screenshot(product_name)
            logger.exception("Unexpected extraction failure for %s", product_name)
            raise ProductNotFoundError(str(exc)) from exc
