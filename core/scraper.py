import asyncio
import json
import re
import urllib.parse
from datetime import datetime
from typing import Dict, Any

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth

# Comprehensive regex for global currency matching (Fallback Tier)
# Matches symbols followed by optional spaces, then numbers with commas and optional decimals.
PRICE_REGEX = re.compile(r'([₹$€£]\s*\d+(?:,\d{3})*(?:\.\d{2})?)')

def clean_price(price_str: str) -> float:
    """Extracts numeric value from a price string like '$1,299.99' or '₹ 45,000'"""
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def clean_currency(price_str: str) -> str:
    """Extracts currency symbol from price string."""
    if not price_str:
        return ""
    match = re.search(r'[₹$€£]', price_str)
    return match.group(0) if match else "₹"  # Default to INR if unknown

async def block_resources(route):
    """Aggressively abort loading of heavy, non-essential network resources."""
    blocked_types = {"image", "media", "font", "stylesheet"}
    if route.request.resource_type in blocked_types:
        await route.abort()
    elif any(tracker in route.request.url for tracker in ["google-analytics", "doubleclick", "facebook.net"]):
        await route.abort()
    else:
        await route.continue_()

async def extract_tier_1_json_ld(page) -> Dict[str, Any]:
    """Tier 1: Parse JSON-LD Microdata."""
    try:
        scripts = await page.locator('script[type="application/ld+json"]').all_inner_texts()
        
        for script_text in scripts:
            try:
                data = json.loads(script_text)
                items = data if isinstance(data, list) else [data]
                    
                for item in items:
                    sub_items = item["@graph"] if "@graph" in item else [item]
                        
                    for sub_item in sub_items:
                        if sub_item.get("@type") == "Product":
                            name = sub_item.get("name", "")
                            offers = sub_item.get("offers", {})
                            if isinstance(offers, list) and len(offers) > 0:
                                offers = offers[0]
                                
                            price = offers.get("price") or offers.get("lowPrice")
                            currency = offers.get("priceCurrency", "")
                            availability = offers.get("availability", "")
                            
                            if name and price:
                                status = "In Stock" if "InStock" in str(availability) else "Unknown"
                                return {
                                    "product_name": name,
                                    "current_price": clean_price(str(price)),
                                    "currency": currency if currency else clean_currency(str(price)),
                                    "availability_status": status
                                }
            except Exception:
                continue
    except Exception:
        pass
    return {}

async def extract_tier_2_meta(page) -> Dict[str, Any]:
    """Tier 2: Extract OpenGraph and Meta tags."""
    name = ""
    price_str = ""
    currency = ""
    
    try:
        og_title_loc = page.locator('meta[property="og:title"]')
        if await og_title_loc.count() > 0:
            name = await og_title_loc.first.get_attribute('content', timeout=1000)
            
        for selector in ['meta[property="og:price:amount"]', 'meta[property="product:price:amount"]', 'meta[name="twitter:data1"]']:
            loc = page.locator(selector)
            if await loc.count() > 0:
                val = await loc.first.get_attribute('content', timeout=1000)
                if val:
                    price_str = val
                    break
                    
        og_curr_loc = page.locator('meta[property="og:price:currency"]')
        if await og_curr_loc.count() > 0:
            currency = await og_curr_loc.first.get_attribute('content', timeout=1000)
            
        if name and price_str:
            return {
                "product_name": name,
                "current_price": clean_price(price_str),
                "currency": currency if currency else clean_currency(price_str),
                "availability_status": "Unknown"
            }
    except Exception:
        pass
    return {}

async def extract_tier_3_heuristic(page) -> Dict[str, Any]:
    """Tier 3: Aggressive Heuristic DOM & Regex Fallback for dynamically rendered pages."""
    try:
        # Give dynamic JavaScript payloads 1.5 extra seconds to inject into the DOM
        await page.wait_for_timeout(1500)
        
        # Try to find a clean H1 tag first, fallback to page title
        h1_loc = page.locator('h1')
        if await h1_loc.count() > 0:
            name = await h1_loc.first.inner_text(timeout=1000)
        else:
            name = await page.title()
            name = name.split('|')[0].split('-')[0].strip() # Clean basic brand padding
        
        # Scan raw DOM body text for all currency strings using regex
        body_text = await page.locator('body').inner_text(timeout=1000)
        matches = PRICE_REGEX.findall(body_text)
        
        if matches:
            # Parse all found valid prices greater than 0
            valid_prices = []
            for match in matches:
                p_val = clean_price(match)
                if p_val > 0.0:
                    valid_prices.append((p_val, match))
            
            if valid_prices:
                # E-commerce sites often show multiple prices (e.g. MRP vs Discounted).
                # We assume the lowest valid prominently displayed price is the actual deal price.
                valid_prices.sort(key=lambda x: x[0])
                lowest_price_val, best_match_str = valid_prices[0]
                
                return {
                    "product_name": name.strip(),
                    "current_price": lowest_price_val,
                    "currency": clean_currency(best_match_str),
                    "availability_status": "Unknown"
                }
    except Exception:
        pass
    return {}

async def run_playwright_scrape(url: str, domain: str) -> Dict[str, Any]:
    """Async wrapper for the full playwright scraping pipeline."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base_result = {
        "timestamp": timestamp,
        "product_name": "Unknown Product",
        "platform": domain,
        "target_url": url,
        "current_price": 0.0,
        "currency": "₹",
        "availability_status": "Unavailable"
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--window-size=1920,1080'
        ])
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='Asia/Kolkata'
        )
        
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        await page.route("**/*", block_resources)
        
        try:
            # Wait until domcontentloaded to avoid getting hung up on massive external scripts
            await page.goto(url, wait_until="domcontentloaded", timeout=12000)
            
            # Tier 1 extraction
            extracted = await extract_tier_1_json_ld(page)
            
            # Tier 2 fallback
            if not extracted or extracted["current_price"] == 0.0:
                extracted = await extract_tier_2_meta(page)
                
            # Tier 3 aggressive heuristic fallback
            if not extracted or extracted["current_price"] == 0.0:
                extracted = await extract_tier_3_heuristic(page)
                
            if extracted and extracted.get("current_price", 0.0) > 0.0:
                base_result.update(extracted)
                if base_result["availability_status"] == "Unknown":
                    # Assume in stock if we successfully found a valid numeric price via heuristics
                    base_result["availability_status"] = "In Stock"
                    
        except PlaywrightTimeoutError:
            base_result["product_name"] = "Error: Timeout (Exceeded 12s UI Limit)"
        except Exception as e:
            base_result["product_name"] = f"Extraction Error: {str(e)}"
        finally:
            await browser.close()
            
    return base_result

def scrape_url(url: str) -> Dict[str, Any]:
    """
    Synchronous entry point called by Streamlit and main.py orchestrator.
    Spins up a local asyncio event loop to run the Playwright headless browser logic.
    """
    parsed_url = urllib.parse.urlparse(url)
    netloc = parsed_url.netloc.replace("www.", "")
    domain = netloc.split('.')[0].capitalize() if netloc else "Unknown Platform"
    
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(run_playwright_scrape(url, domain))
    finally:
        loop.close()
        
    return result
