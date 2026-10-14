"""SQLite persistence for inventory, carts, users, and chat history."""

import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from config import settings


def get_connection(database_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(database_path or settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: str | Path | None = None, catalog_path: str | Path | None = None) -> None:
    with get_connection(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY, product_name TEXT NOT NULL, brand TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0), processor TEXT, ram TEXT, storage TEXT,
                battery_life TEXT, category TEXT NOT NULL, stock INTEGER NOT NULL CHECK(stock >= 0),
                rating REAL NOT NULL DEFAULT 0, description TEXT DEFAULT '', review_summary TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS carts (
                cart_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'Added'
            );
            CREATE TABLE IF NOT EXISTS cart_items (
                cart_id TEXT NOT NULL REFERENCES carts(cart_id), product_id TEXT NOT NULL REFERENCES products(product_id),
                quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price REAL NOT NULL, PRIMARY KEY(cart_id, product_id)
            );
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
                salt TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, role TEXT NOT NULL,
                content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id, id);
            """
        )
        count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            path = Path(catalog_path or settings.product_catalog_path)
            if path.exists():
                frame = pd.read_csv(path).fillna("")
                fields = ("product_id", "product_name", "brand", "price", "processor", "ram", "storage", "battery_life", "category", "stock", "rating", "description", "review_summary")
                rows = [tuple(row.get(field, "") for field in fields) for row in frame.to_dict(orient="records")]
                connection.executemany(
                    "INSERT INTO products (" + ",".join(fields) + ") VALUES (" + ",".join("?" for _ in fields) + ")", rows
                )


def get_products(database_path: str | Path | None = None) -> list[dict[str, Any]]:
    initialize_database(database_path)
    with get_connection(database_path) as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM products ORDER BY product_id")]


def check_inventory(product_id: str, database_path: str | Path | None = None) -> dict[str, Any]:
    initialize_database(database_path)
    with get_connection(database_path) as connection:
        row = connection.execute("SELECT stock FROM products WHERE product_id = ?", (product_id,)).fetchone()
    if row is None:
        return {"available": False, "stock": 0, "error": "Product not found"}
    return {"available": row["stock"] > 0, "stock": row["stock"]}


def create_cart(product_id: str, user_id: str = "guest", quantity: int = 1, database_path: str | Path | None = None) -> dict[str, Any]:
    if quantity < 1:
        raise ValueError("Quantity must be at least 1")
    initialize_database(database_path)
    with get_connection(database_path) as connection:
        product = connection.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
        if product is None:
            raise ValueError("Product not found")
        if product["stock"] < quantity:
            raise ValueError("Insufficient stock")
        cart_id = "CART" + secrets.token_hex(4).upper()
        connection.execute("INSERT INTO carts (cart_id, user_id) VALUES (?, ?)", (cart_id, user_id))
        connection.execute("INSERT INTO cart_items (cart_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)", (cart_id, product_id, quantity, product["price"]))
        connection.execute("UPDATE products SET stock = stock - ? WHERE product_id = ?", (quantity, product_id))
    return {"cart_id": cart_id, "product_id": product_id, "product": product["product_name"], "quantity": quantity, "status": "Added", "total": product["price"] * quantity}


def register_user(username: str, password: str, database_path: str | Path | None = None) -> str:
    normalized = username.strip().lower()
    if len(normalized) < 3 or len(password) < 8:
        raise ValueError("Username must be 3+ characters and password 8+ characters")
    salt = secrets.token_bytes(16)
    password_hash = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1).hex()
    user_id = "USR" + secrets.token_hex(6).upper()
    initialize_database(database_path)
    try:
        with get_connection(database_path) as connection:
            connection.execute("INSERT INTO users (user_id, username, password_hash, salt) VALUES (?, ?, ?, ?)", (user_id, normalized, password_hash, salt.hex()))
    except sqlite3.IntegrityError as error:
        raise ValueError("Username already exists") from error
    return user_id


def authenticate_user(username: str, password: str, database_path: str | Path | None = None) -> str | None:
    initialize_database(database_path)
    with get_connection(database_path) as connection:
        row = connection.execute("SELECT user_id, password_hash, salt FROM users WHERE username = ?", (username.strip().lower(),)).fetchone()
    if row is None:
        return None
    candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(row["salt"]), n=2**14, r=8, p=1).hex()
    return row["user_id"] if hmac.compare_digest(candidate, row["password_hash"]) else None


def save_chat_message(user_id: str, role: str, content: str, database_path: str | Path | None = None) -> None:
    if role not in {"user", "assistant"}:
        raise ValueError("Role must be user or assistant")
    initialize_database(database_path)
    with get_connection(database_path) as connection:
        connection.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))


def get_chat_history(user_id: str, limit: int = 30, database_path: str | Path | None = None) -> list[dict[str, str]]:
    initialize_database(database_path)
    with get_connection(database_path) as connection:
        rows = connection.execute("SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
    return [dict(row) for row in reversed(rows)]
