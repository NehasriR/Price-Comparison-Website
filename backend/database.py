import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "shop_sense.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT NOT NULL,
                flipkart_price REAL,
                amazon_price REAL,
                croma_price REAL,
                min_site TEXT,
                min_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT NOT NULL,
                target_price REAL NOT NULL,
                user_contact TEXT NOT NULL,
                flipkart_price REAL,
                amazon_price REAL,
                croma_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def save_search(product, flipkart_price, amazon_price, croma_price, min_site, min_url):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO searches (
                product,
                flipkart_price,
                amazon_price,
                croma_price,
                min_site,
                min_url
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (product, flipkart_price, amazon_price, croma_price, min_site, min_url),
        )


def save_notification(product, target_price, user_contact, flipkart_price, amazon_price, croma_price):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO notifications (
                product,
                target_price,
                user_contact,
                flipkart_price,
                amazon_price,
                croma_price
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (product, target_price, user_contact, flipkart_price, amazon_price, croma_price),
        )
