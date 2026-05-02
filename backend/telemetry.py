from __future__ import annotations

import os
import sqlite3
from typing import Dict

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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def log_request(
    prompt: str,
    label: str,
    model_used: str,
    latency_ms: float,
    toon_tokens: int,
    json_tokens: int,
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
                json_token_count
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (prompt, label, model_used, latency_ms, toon_tokens, json_tokens),
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

    return {
        "total_requests": int(count or 0),
        "average_latency_ms": float(avg_latency or 0.0),
        "total_tokens_saved": int(saved or 0),
    }


_init_db()
