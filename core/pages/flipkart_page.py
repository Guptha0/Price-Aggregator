"""
FlipkartPage — site-specific locators + parsing for flipkart.com product pages.
"""
from __future__ import annotations

import re

from core.base_page import BasePage


class FlipkartPage(BasePage):
    PLATFORM_NAME = "flipkart"

    # Flipkart's class names are obfuscated/rotate periodically. If these
    # go stale, re-inspect via devtools and update only here.
    PRICE_SELECTOR = "div._30jeq3, div.Nx9bqj"
    TITLE_SELECTOR = "span.B_NuCI, span.VU-ZEz"
    AVAILABILITY_SELECTOR = "div._16FRp0, div.Z8JjpR"

    def parse_price(self, raw_text: str) -> tuple[float, str]:
        # Flipkart format example: "₹5,299"
        currency = "INR" if "₹" in raw_text else "UNKNOWN"
        numeric = re.sub(r"[^\d.]", "", raw_text)
        return float(numeric), currency

    async def get_availability(self) -> str:
        text = await self.safe_text(self.AVAILABILITY_SELECTOR, timeout_ms=4000)
        if text is None:
            # Absence of an explicit "sold out" banner on Flipkart usually
            # means the item is purchasable.
            return "in_stock"
        text_lower = text.lower()
        if "sold out" in text_lower or "out of stock" in text_lower:
            return "out_of_stock"
        return "in_stock"
