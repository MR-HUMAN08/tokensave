from __future__ import annotations

import os
import sqlite3
from typing import Dict, Iterable

_DB_PATH = os.path.join(os.path.dirname(__file__), "omni_route.db")


def _init_db() -> None:
    with sqlite3.connect(_DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                label TEXT NOT NULL,
                model_used TEXT NOT NULL,
                latency_ms REAL NOT NULL,
                toon_token_count INTEGER NOT NULL,
                json_token_count INTEGER NOT NULL,
                confidence REAL,
                tier_blurred INTEGER NOT NULL DEFAULT 0,
                fallback_used INTEGER NOT NULL DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        _ensure_columns(
            connection,
            "logs",
            [
                ("confidence", "REAL"),
                ("tier_blurred", "INTEGER NOT NULL DEFAULT 0"),
                ("fallback_used", "INTEGER NOT NULL DEFAULT 0"),
            ],
        )
        connection.commit()


def _ensure_columns(
    connection: sqlite3.Connection,
    table: str,
    columns: Iterable[tuple[str, str]],
) -> None:
    cursor = connection.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    for name, ddl in columns:
        if name in existing:
            continue
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def log_request(
    prompt: str,
    label: str,
    model_used: str,
    latency_ms: float,
    toon_tokens: int,
    json_tokens: int,
    confidence: float,
    tier_blurred: bool,
    fallback_used: bool,
) -> None:
    with sqlite3.connect(_DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO logs (
                prompt,
                label,
                model_used,
                latency_ms,
                toon_token_count,
                json_token_count,
                confidence,
                tier_blurred,
                fallback_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prompt,
                label,
                model_used,
                latency_ms,
                toon_tokens,
                json_tokens,
                confidence,
                int(tier_blurred),
                int(fallback_used),
            ),
        )
        connection.commit()


def get_stats() -> Dict[str, float]:
    with sqlite3.connect(_DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*), AVG(latency_ms) FROM logs")
        count, avg_latency = cursor.fetchone()
        cursor.execute(
            "SELECT SUM(json_token_count - toon_token_count) FROM logs"
        )
        saved = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(json_token_count) FROM logs")
        json_total = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(tier_blurred) FROM logs")
        tier_blurs = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(fallback_used) FROM logs")
        fallbacks = cursor.fetchone()[0]

    total_saved = int(saved or 0)
    total_json = int(json_total or 0)
    tokens_saved_percent = 0.0
    if total_json > 0:
        tokens_saved_percent = (total_saved / total_json) * 100

    return {
        "total_requests": int(count or 0),
        "average_latency_ms": float(avg_latency or 0.0),
        "total_tokens_saved": total_saved,
        "tier_blurs_total": int(tier_blurs or 0),
        "fallbacks_total": int(fallbacks or 0),
        "tokens_saved_percent": float(tokens_saved_percent),
    }


def get_recent_requests(limit: int = 10) -> list[Dict[str, object]]:
    with sqlite3.connect(_DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM logs ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


_init_db()
