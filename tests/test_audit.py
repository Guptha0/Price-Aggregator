import unittest
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from matcher import match_products
from dashboard.app import initialize_database, DB_PATH, GLOBAL_PLATFORMS

class TestSystemAudit(unittest.TestCase):
    def test_database_schema(self):
        """1. Database Schema & Data Integrity"""
        initialize_database()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check price_logs table
        cursor.execute("PRAGMA table_info(price_logs)")
        columns = [col[1] for col in cursor.fetchall()]
        self.assertIn("timestamp", columns)
        self.assertIn("current_price", columns)
        
        # Check price_alerts table
        cursor.execute("PRAGMA table_info(price_alerts)")
        columns = [col[1] for col in cursor.fetchall()]
        self.assertIn("product_name", columns)
        self.assertIn("target_price", columns)
        
        conn.close()

    def test_matcher_veto_traps(self):
        """2. Matcher Veto Traps"""
        # Capacity trap
        is_match, _, _ = match_products("WD Black 1TB SN850X", "WD Black 2TB SN850X")
        self.assertFalse(is_match, "Should veto 1TB vs 2TB")
        
        # Model tier conflict
        is_match, _, _ = match_products("Samsung 980 PRO", "Samsung 970 EVO")
        self.assertFalse(is_match, "Should veto 980 PRO vs 970 EVO")
        
        # Brand padding (should allow if the matcher uses thefuzz fallback)
        is_match, _, _ = match_products(
            "WD_BLACK 1TB SN850X NVMe Internal Gaming SSD Solid State Drive", 
            "Western Digital WD_BLACK 1TB SN850X NVMe Internal Gaming SSD Solid State Drive"
        )
        self.assertTrue(is_match, "Should allow brand padding")
        
    def test_scraper_resilience(self):
        """3. Scraper Resilience & Windows Safety"""
        with open(os.path.join(os.path.dirname(__file__), "..", "core", "scraper.py"), "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("WindowsProactorEventLoopPolicy", content, "WindowsProactorEventLoopPolicy missing")
            self.assertIn("application/ld+json", content, "Tier 1 JSON-LD missing")
            self.assertIn("og:price:amount", content, "Tier 2 OpenGraph missing")
            self.assertIn("PRICE_REGEX", content, "Tier 3 Regex missing")
            self.assertIn("wait_for_timeout", content, "Hydration delay missing")
            self.assertIn("1500", content, "1500ms delay missing")
            
    def test_ui_architecture(self):
        """4. UI Architecture & Registry"""
        self.assertGreaterEqual(len(GLOBAL_PLATFORMS), 100, "Should have 100+ platforms")
        self.assertIn("Amazon", GLOBAL_PLATFORMS)
        self.assertIn("Flipkart", GLOBAL_PLATFORMS)
        
        with open(os.path.join(os.path.dirname(__file__), "..", "dashboard", "app.py"), "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("st.tabs", content, "Tabbed UI missing")
            self.assertIn("multiselect", content, "Multiselect missing")
            self.assertIn("alerts_df", content, "Alerts dataframe missing")

    def test_unicode_and_automation_safety(self):
        """5. Unicode & Automation Safety"""
        with open(os.path.join(os.path.dirname(__file__), "..", "main.py"), "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("reconfigure(encoding='utf-8')", content, "UTF-8 reconfiguration missing in main.py")

if __name__ == "__main__":
    unittest.main(verbosity=2)
