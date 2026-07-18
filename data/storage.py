"""
StorageManager — append-only SQLite persistence for price history.

Design choices:
    - One row per scrape, ever. We never UPDATE or DELETE — history is
      the whole point of a price tracker. "Current price" is just the
      latest row for a given (product_name, platform).
    - WAL mode so the Streamlit dashboard can read concurrently while
      a scrape is writing (they're separate processes).
    - `get_previous_price()` is what powers the alerting hook in
      alerts/notifier.py — it diffs against the last logged price to
      decide whether a drop actually happened, not just whether we're
      below the static target_price.
"""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

import config

logger = logging.getLogger("price_tracker.storage")

SCHEMA = """
CREATE TABLE IF NOT EXISTS price_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    product_name TEXT NOT NULL,
    platform TEXT NOT NULL,
    target_url TEXT NOT NULL,
    current_price REAL NOT NULL,
    currency TEXT NOT NULL,
    availability_status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_product_platform
    ON price_log (product_name, platform);
CREATE INDEX IF NOT EXISTS idx_timestamp
    ON price_log (timestamp);
"""


class StorageManager:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or config.DB_PATH
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL;")  # allows concurrent dashboard reads
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def save_entry(self, entry: dict) -> None:
        """Append one row matching the shared schema:
        [timestamp, product_name, platform, target_url, current_price,
         currency, availability_status]
        """
        required = {
            "timestamp", "product_name", "platform", "target_url",
            "current_price", "currency", "availability_status",
        }
        missing = required - entry.keys()
        if missing:
            raise ValueError(f"Entry missing required fields: {missing}")

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO price_log
                    (timestamp, product_name, platform, target_url,
                     current_price, currency, availability_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["timestamp"],
                    entry["product_name"],
                    entry["platform"],
                    entry["target_url"],
                    entry["current_price"],
                    entry["currency"],
                    entry["availability_status"],
                ),
            )
            conn.commit()
        logger.info(
            "Logged %s [%s] = %s %s",
            entry["product_name"], entry["platform"],
            entry["current_price"], entry["currency"],
        )

    def get_previous_price(self, product_name: str, platform: str) -> float | None:
        """Return the most recent PRIOR price for this product, or None
        if this is the first time we've ever logged it. Used to detect
        an actual drop event (vs. just being below a static threshold)."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT current_price FROM price_log
                WHERE product_name = ? AND platform = ?
                ORDER BY timestamp DESC LIMIT 1
                """,
                (product_name, platform),
            ).fetchone()
        return row[0] if row else None

    def load_history(self, product_name: str | None = None,
                      platform: str | None = None) -> pd.DataFrame:
        """Load history as a DataFrame for the dashboard, optionally
        filtered by product and/or platform."""
        query = "SELECT * FROM price_log WHERE 1=1"
        params: list = []
        if product_name:
            query += " AND product_name = ?"
            params.append(product_name)
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        query += " ORDER BY timestamp ASC"

        with self._connect() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def load_latest_snapshot(self) -> pd.DataFrame:
        """One row per (product_name, platform) — the most recent price
        seen for each watched item. Powers the dashboard's summary table."""
        query = """
            SELECT p.*
            FROM price_log p
            INNER JOIN (
                SELECT product_name, platform, MAX(timestamp) AS max_ts
                FROM price_log
                GROUP BY product_name, platform
            ) latest
            ON p.product_name = latest.product_name
            AND p.platform = latest.platform
            AND p.timestamp = latest.max_ts
            ORDER BY p.product_name
        """
        with self._connect() as conn:
            df = pd.read_sql_query(query, conn)
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def export_csv(self, out_path: Path | None = None) -> Path:
        """Optional: dump the full table to CSV, e.g. for sharing or backup."""
        out_path = out_path or config.CSV_PATH
        df = self.load_history()
        df.to_csv(out_path, index=False)
        logger.info("Exported %d rows to %s", len(df), out_path)
        return out_path
