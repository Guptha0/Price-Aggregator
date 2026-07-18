"""
AmazonPage — site-specific locators + parsing for amazon.in product pages.

If Amazon changes its DOM, this is the ONLY file you should need to touch.
"""
from __future__ import annotations

import re

from core.base_page import BasePage


class AmazonPage(BasePage):
    PLATFORM_NAME = "amazon"

    # NOTE: Amazon runs frequent A/B DOM variants. These are the current
    # common selectors as of this writing — verify with browser devtools
    # if extraction starts failing (that's exactly what the auto-screenshot
    # in BasePage is for).
    PRICE_SELECTOR = "span.a-price span.a-offscreen"
    TITLE_SELECTOR = "#productTitle"
    AVAILABILITY_SELECTOR = "#availability span"

    def parse_price(self, raw_text: str) -> tuple[float, str]:
        # Amazon.in format example: "₹6,499.00"
        currency = "INR" if "₹" in raw_text else "USD" if "$" in raw_text else "UNKNOWN"
        numeric = re.sub(r"[^\d.]", "", raw_text)
        return float(numeric), currency

    async def get_availability(self) -> str:
        text = await self.safe_text(self.AVAILABILITY_SELECTOR, timeout_ms=4000)
        if text is None:
            return "unknown"
        text_lower = text.lower()
        if "in stock" in text_lower:
            return "in_stock"
        if "unavailable" in text_lower or "out of stock" in text_lower:
            return "out_of_stock"
        return "unknown"
