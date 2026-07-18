"""
BrowserManager owns the Playwright lifecycle: launching a stealth-patched
Chromium instance, rotating user-agent/viewport per session, and cleaning
up cleanly on exit.

Nothing site-specific lives here. This class only knows how to produce a
ready-to-use `Page` object — extraction logic belongs in core/pages/*.
"""
from __future__ import annotations

import logging
import random

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from playwright_stealth import Stealth

import config

logger = logging.getLogger("price_tracker.browser")


class BrowserManager:
    """Async context manager: `async with BrowserManager() as page: ...`"""

    def __init__(self, headless: bool | None = None):
        self.headless = config.HEADLESS if headless is None else headless
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._stealth = Stealth()

    async def __aenter__(self) -> Page:
        self._playwright = await async_playwright().start()

        # Launch args chosen to reduce the most common headless-detection
        # signals (navigator.webdriver, missing GPU, automation flags).
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )

        user_agent = random.choice(config.USER_AGENTS)
        viewport = random.choice(config.VIEWPORTS)

        self._context = await self._browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )

        await self._stealth.apply_stealth_async(self._context)

        page = await self._context.new_page()

        
        logger.info("Browser session started | UA=%s | viewport=%s", user_agent, viewport)
        return page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser session closed")
        # Returning False/None re-raises any exception that occurred —
        # we want scrape failures to surface, not be swallowed here.
        return False
