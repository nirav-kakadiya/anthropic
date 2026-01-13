"""
Storage - SQLite database for scan history and trend tracking.

Features:
- Store scan results over time
- Track keyword trends
- Compare historical data
- Query past scans
- Export history
"""

import sqlite3
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class StoredScan:
    """A stored scan record."""
    scan_id: str
    scan_time: str
    url: str
    niche: str
    total_keywords: int
    total_gaps: int
    top_keywords: list[str]
    top_gaps: list[str]
    raw_data: str  # JSON blob


@dataclass
class KeywordHistory:
    """Historical data for a keyword."""
    keyword: str
    first_seen: str
    last_seen: str
    total_occurrences: int
    trend_scores: list[dict]  # [{date, score, source}, ...]
    avg_score: float


class ScanStorage:
    """
    SQLite storage for scan history.

    Usage:
        storage = ScanStorage("./market_research.db")

        # Save a scan
        storage.save_scan(scan_result, url="https://example.com")

        # Get history
        history = storage.get_scan_history(limit=10)

        # Track keyword trends
        trends = storage.get_keyword_trends("flux ai", days=30)

        # Compare scans
        diff = storage.compare_scans(scan_id_1, scan_id_2)
    """

    def __init__(self, db_path: str = "./market_research.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Scans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                scan_id TEXT PRIMARY KEY,
                scan_time TEXT NOT NULL,
                url TEXT,
                niche TEXT,
                total_keywords INTEGER,
                total_gaps INTEGER,
                top_keywords TEXT,
                top_gaps TEXT,
                raw_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Keywords table (for trend tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                scan_id TEXT NOT NULL,
                scan_time TEXT NOT NULL,
                trend_score REAL,
                source TEXT,
                is_gap INTEGER DEFAULT 0,
                FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
            )
        """)

        # Competitors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                name TEXT,
                features TEXT,
                last_scan TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                priority TEXT,
                data TEXT,
                sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
                channels TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_time ON scans(scan_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords_scan ON keywords(scan_id)")

        conn.commit()
        conn.close()

    def save_scan(
        self,
        scan_id: str,
        url: str = "",
        niche: str = "",
        keywords: list[str] = None,
        gaps: list[dict] = None,
        raw_data: dict = None,
    ):
        """Save a scan to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        keywords = keywords or []
        gaps = gaps or []
        raw_data = raw_data or {}

        scan_time = datetime.now().isoformat()
        top_keywords = keywords[:20]
        top_gaps = [g.get("keyword", "") if isinstance(g, dict) else str(g) for g in gaps[:20]]

        cursor.execute("""
            INSERT OR REPLACE INTO scans
            (scan_id, scan_time, url, niche, total_keywords, total_gaps, top_keywords, top_gaps, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scan_id,
            scan_time,
            url,
            niche,
            len(keywords),
            len(gaps),
            json.dumps(top_keywords),
            json.dumps(top_gaps),
            json.dumps(raw_data),
        ))

        # Save keywords for trend tracking
        for kw in keywords[:100]:
            cursor.execute("""
                INSERT INTO keywords (keyword, scan_id, scan_time, trend_score, source, is_gap)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                kw.lower() if isinstance(kw, str) else kw.get("keyword", "").lower(),
                scan_id,
                scan_time,
                80.0,  # Default score
                "scan",
                0,
            ))

        # Save gaps
        for gap in gaps[:50]:
            gap_kw = gap.get("keyword", "") if isinstance(gap, dict) else str(gap)
            cursor.execute("""
                INSERT INTO keywords (keyword, scan_id, scan_time, trend_score, source, is_gap)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                gap_kw.lower(),
                scan_id,
                scan_time,
                gap.get("trend_score", 80.0) if isinstance(gap, dict) else 80.0,
                gap.get("source", "gap_analysis") if isinstance(gap, dict) else "gap_analysis",
                1,
            ))

        conn.commit()
        conn.close()

    def get_scan_history(
        self,
        limit: int = 10,
        url: Optional[str] = None,
    ) -> list[StoredScan]:
        """Get recent scan history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if url:
            cursor.execute("""
                SELECT scan_id, scan_time, url, niche, total_keywords, total_gaps, top_keywords, top_gaps, raw_data
                FROM scans
                WHERE url = ?
                ORDER BY scan_time DESC
                LIMIT ?
            """, (url, limit))
        else:
            cursor.execute("""
                SELECT scan_id, scan_time, url, niche, total_keywords, total_gaps, top_keywords, top_gaps, raw_data
                FROM scans
                ORDER BY scan_time DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            StoredScan(
                scan_id=row[0],
                scan_time=row[1],
                url=row[2] or "",
                niche=row[3] or "",
                total_keywords=row[4] or 0,
                total_gaps=row[5] or 0,
                top_keywords=json.loads(row[6]) if row[6] else [],
                top_gaps=json.loads(row[7]) if row[7] else [],
                raw_data=row[8] or "{}",
            )
            for row in rows
        ]

    def get_keyword_trends(
        self,
        keyword: str,
        days: int = 30,
    ) -> KeywordHistory:
        """Get trend history for a keyword."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT scan_time, trend_score, source, is_gap
            FROM keywords
            WHERE keyword = ? AND scan_time >= ?
            ORDER BY scan_time ASC
        """, (keyword.lower(), cutoff))

        rows = cursor.fetchall()

        if not rows:
            conn.close()
            return KeywordHistory(
                keyword=keyword,
                first_seen="",
                last_seen="",
                total_occurrences=0,
                trend_scores=[],
                avg_score=0.0,
            )

        trend_scores = [
            {"date": row[0], "score": row[1], "source": row[2], "is_gap": bool(row[3])}
            for row in rows
        ]

        avg_score = sum(row[1] for row in rows) / len(rows)

        conn.close()

        return KeywordHistory(
            keyword=keyword,
            first_seen=rows[0][0],
            last_seen=rows[-1][0],
            total_occurrences=len(rows),
            trend_scores=trend_scores,
            avg_score=avg_score,
        )

    def get_top_keywords(
        self,
        days: int = 7,
        limit: int = 20,
        gaps_only: bool = False,
    ) -> list[dict]:
        """Get top keywords by occurrence count."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        if gaps_only:
            cursor.execute("""
                SELECT keyword, COUNT(*) as count, AVG(trend_score) as avg_score
                FROM keywords
                WHERE scan_time >= ? AND is_gap = 1
                GROUP BY keyword
                ORDER BY count DESC, avg_score DESC
                LIMIT ?
            """, (cutoff, limit))
        else:
            cursor.execute("""
                SELECT keyword, COUNT(*) as count, AVG(trend_score) as avg_score
                FROM keywords
                WHERE scan_time >= ?
                GROUP BY keyword
                ORDER BY count DESC, avg_score DESC
                LIMIT ?
            """, (cutoff, limit))

        rows = cursor.fetchall()
        conn.close()

        return [
            {"keyword": row[0], "occurrences": row[1], "avg_score": row[2]}
            for row in rows
        ]

    def compare_scans(self, scan_id_1: str, scan_id_2: str) -> dict:
        """Compare two scans."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get keywords for each scan
        cursor.execute("""
            SELECT keyword FROM keywords WHERE scan_id = ?
        """, (scan_id_1,))
        keywords_1 = set(row[0] for row in cursor.fetchall())

        cursor.execute("""
            SELECT keyword FROM keywords WHERE scan_id = ?
        """, (scan_id_2,))
        keywords_2 = set(row[0] for row in cursor.fetchall())

        # Get scan metadata
        cursor.execute("""
            SELECT scan_time, total_keywords, total_gaps FROM scans WHERE scan_id = ?
        """, (scan_id_1,))
        scan_1_data = cursor.fetchone()

        cursor.execute("""
            SELECT scan_time, total_keywords, total_gaps FROM scans WHERE scan_id = ?
        """, (scan_id_2,))
        scan_2_data = cursor.fetchone()

        conn.close()

        new_keywords = keywords_2 - keywords_1
        removed_keywords = keywords_1 - keywords_2
        common_keywords = keywords_1 & keywords_2

        return {
            "scan_1": {
                "scan_id": scan_id_1,
                "scan_time": scan_1_data[0] if scan_1_data else "",
                "total_keywords": scan_1_data[1] if scan_1_data else 0,
            },
            "scan_2": {
                "scan_id": scan_id_2,
                "scan_time": scan_2_data[0] if scan_2_data else "",
                "total_keywords": scan_2_data[1] if scan_2_data else 0,
            },
            "new_keywords": list(new_keywords)[:50],
            "removed_keywords": list(removed_keywords)[:50],
            "common_keywords": len(common_keywords),
            "change_summary": {
                "added": len(new_keywords),
                "removed": len(removed_keywords),
                "unchanged": len(common_keywords),
            }
        }

    def save_competitor(self, url: str, name: str, features: list[str]):
        """Save or update competitor info."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO competitors (url, name, features, last_scan)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                name = excluded.name,
                features = excluded.features,
                last_scan = excluded.last_scan
        """, (url, name, json.dumps(features), datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_competitors(self) -> list[dict]:
        """Get all saved competitors."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT url, name, features, last_scan FROM competitors
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "url": row[0],
                "name": row[1],
                "features": json.loads(row[2]) if row[2] else [],
                "last_scan": row[3],
            }
            for row in rows
        ]

    def log_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        priority: str,
        data: dict,
        channels: list[str],
    ):
        """Log an alert that was sent."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alerts (alert_type, title, message, priority, data, channels)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            alert_type,
            title,
            message,
            priority,
            json.dumps(data),
            json.dumps(channels),
        ))

        conn.commit()
        conn.close()

    def get_stats(self) -> dict:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM scans")
        total_scans = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT keyword) FROM keywords")
        unique_keywords = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM competitors")
        total_competitors = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM alerts")
        total_alerts = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(scan_time), MAX(scan_time) FROM scans")
        time_range = cursor.fetchone()

        conn.close()

        return {
            "total_scans": total_scans,
            "unique_keywords": unique_keywords,
            "total_competitors": total_competitors,
            "total_alerts": total_alerts,
            "first_scan": time_range[0] if time_range else None,
            "last_scan": time_range[1] if time_range else None,
            "db_path": str(self.db_path),
        }


def create_storage(db_path: str = "./market_research.db") -> ScanStorage:
    """Factory function to create ScanStorage."""
    return ScanStorage(db_path)
