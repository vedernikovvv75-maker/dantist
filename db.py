"""
SQLite: пользователи, бонусные карты, лиды. Статусы: new → got_card → booked → patient → repeat.
"""
import sqlite3
from datetime import datetime
from typing import Optional

from config import DB_PATH


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP,
            last_active_at TIMESTAMP,
            is_owner INTEGER DEFAULT 0,
            status TEXT DEFAULT 'new',
            bonus_card_number TEXT,
            bonus_card_at TIMESTAMP,
            phone TEXT,
            consent_at TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS funnel_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT,
            payload TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )
    conn.commit()
    conn.close()


def get_user(user_id: int) -> Optional[tuple]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def add_user(
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
) -> None:
    now = datetime.now()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id, username, first_name, created_at, last_active_at, is_owner, status)
        VALUES (?, ?, ?, ?, ?, 0, 'new')
        """,
        (user_id, username or "", first_name or "", now, now),
    )
    conn.commit()
    conn.close()


def update_user(user_id: int, **kwargs) -> None:
    if not kwargs:
        return
    conn = get_conn()
    cur = conn.cursor()
    allowed = {
        "username", "first_name", "last_active_at", "is_owner", "status",
        "bonus_card_number", "bonus_card_at", "phone", "consent_at",
    }
    set_parts = []
    values = []
    for key, val in kwargs.items():
        if key in allowed:
            set_parts.append(f"{key} = ?")
            values.append(val)
    if not set_parts:
        conn.close()
        return
    values.append(user_id)
    cur.execute(
        f"UPDATE users SET {', '.join(set_parts)} WHERE user_id = ?",
        values,
    )
    conn.commit()
    conn.close()


def set_owner(user_id: int, is_owner: bool) -> None:
    update_user(user_id, is_owner=1 if is_owner else 0, last_active_at=datetime.now())


def activate_bonus_card(
    user_id: int,
    card_number: str,
    phone: str,
) -> None:
    now = datetime.now()
    update_user(
        user_id,
        bonus_card_number=card_number,
        bonus_card_at=now,
        phone=phone,
        consent_at=now,
        status="got_card",
        last_active_at=now,
    )


def add_funnel_event(user_id: int, event_type: str, payload: str = "") -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO funnel_events (user_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
        (user_id, event_type, payload, datetime.now()),
    )
    conn.commit()
    conn.close()
