"""Tiny SQLite storage for speed test results."""
import sqlite3
import time

DB_PATH = "dashboard.db"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS speedtests (
                        ts INTEGER NOT NULL,
                        download_mbps REAL,
                        latency_ms REAL)""")
    return conn


def save(result):
    with connect() as conn:
        conn.execute("INSERT INTO speedtests VALUES (?, ?, ?)",
                     (int(time.time()), result["download_mbps"], result["latency_ms"]))


def recent(limit=200):
    """Newest `limit` results, returned oldest first so a chart can plot them left to right."""
    with connect() as conn:
        rows = conn.execute("SELECT * FROM speedtests ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in reversed(rows)]
