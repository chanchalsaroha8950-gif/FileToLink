import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from src.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            join_date TEXT
        )"""
    )

    cur.execute(
        """CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY,
            file_path TEXT,
            file_name TEXT,
            user_id INTEGER,
            created_at TEXT,
            expires_at TEXT
        )"""
    )

    cur.execute(
        """CREATE TABLE IF NOT EXISTS channels (
            channel_id TEXT PRIMARY KEY,
            channel_username TEXT,
            added_by INTEGER,
            added_at TEXT
        )"""
    )

    cur.execute(
        """CREATE TABLE IF NOT EXISTS broadcasts (
            message_id INTEGER,
            chat_id INTEGER,
            sent_at TEXT,
            expires_at TEXT
        )"""
    )

    conn.commit()
    conn.close()


def save_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, join_date) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def add_file_record(file_id: str, file_path: str, file_name: str, user_id: int, expires_at: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO files (file_id, file_path, file_name, user_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
        (file_id, file_path, file_name, user_id, datetime.now().isoformat(), expires_at),
    )
    conn.commit()
    conn.close()


def get_active_file(file_id: str) -> Optional[Tuple]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT file_id, file_path, file_name, user_id, created_at, expires_at FROM files WHERE file_id = ? AND expires_at > ?",
        (file_id, datetime.now().isoformat()),
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_expired_files() -> List[Tuple[str, str]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT file_id, file_path FROM files WHERE expires_at < ?",
        (datetime.now().isoformat(),),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_file_record(file_id: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM files WHERE file_id = ?", (file_id,))
    conn.commit()
    conn.close()


def count_users() -> int:
    conn = get_connection()
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return total


def count_active_files() -> int:
    conn = get_connection()
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM files WHERE expires_at > ?", (datetime.now().isoformat(),)).fetchone()[0]
    conn.close()
    return total


def normalize_channel_username(channel_username: str) -> str:
    username = channel_username.strip()
    if username.startswith("https://t.me/"):
        username = "@" + username.split("https://t.me/", 1)[1].strip("/")
    if not username.startswith("@"):
        username = "@" + username
    return username


def add_channel(channel_username: str, added_by: int) -> str:
    normalized = normalize_channel_username(channel_username)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO channels (channel_id, channel_username, added_by, added_at) VALUES (?, ?, ?, ?)",
        (normalized, normalized, added_by, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return normalized


def remove_channel(channel_id: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()


def list_channels() -> List[Tuple[str, str]]:
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT channel_id, channel_username FROM channels ORDER BY added_at DESC").fetchall()
    conn.close()
    return rows
