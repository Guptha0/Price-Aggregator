import os
import sys
import asyncio
import sqlite3
import time
import random
from datetime import datetime

# Enforce ProactorEventLoopPolicy on Windows for Playwright subprocess compatibility
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    # Reconfigure stdout to use UTF-8 to prevent encoding crashes with the ₹ symbol in Windows PowerShell
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

from core.scraper import scrape_url
from alerts.notifier import evaluate_alerts

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "logs", "price_history.db"))

def run_daily_orchestrator():
    print("\n=====================================================")
    print(f"[{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}] Starting Daily Background Orchestrator")
    print("=====================================================")
    
    if not os.path.exists(DB_PATH):
        print("Database not found. Exiting.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Extract deduplicated list of active URLs currently indexed
    cursor.execute("SELECT DISTINCT target_url, platform FROM price_logs")
    targets = cursor.fetchall()
    
    if not targets:
        print("No URLs found in the tracking ledger. Exiting.")
        conn.close()
        return
        
    print(f"Found {len(targets)} unique product URLs to scrape.")
    
    for url, platform in targets:
        # Human delay (3 to 7 seconds) to prevent WAF rate-limiting
        delay = random.uniform(3.0, 7.0)
        time.sleep(delay)
        
        try:
            result = scrape_url(url)
            
            # Append freshly scraped metrics
            cursor.execute("""
                INSERT INTO price_logs (timestamp, product_name, platform, target_url, current_price, currency, availability_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (result["timestamp"], result["product_name"], result["platform"], 
                  result["target_url"], result["current_price"], result["currency"], result["availability_status"]))
            conn.commit()
            
            print(f"[{datetime.now().strftime('%I:%M:%S %p')}] Successfully scraped {result['platform']}: {result['currency']}{result['current_price']:,.2f} - {result['product_name'][:30]}...")
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%I:%M:%S %p')}] ❌ Error scraping {platform}: {str(e)}")

    conn.close()
    
    # Trigger the multi-channel evaluator
    evaluate_alerts()
    print("Daily scraping routine completed.\n")

if __name__ == "__main__":
    run_daily_orchestrator()
