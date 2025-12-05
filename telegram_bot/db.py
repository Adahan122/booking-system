import sqlite3
from datetime import datetime
import asyncio
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / 'telegram_bot.db'

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    full_name TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
'''


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


async def init_db():
    def _init():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = _get_conn()
        cur = conn.cursor()
        cur.executescript(SCHEMA)
        conn.commit()
        conn.close()

    await asyncio.to_thread(_init)


# User helpers
async def get_user_by_telegram_id(telegram_id):
    def _get():
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    return await asyncio.to_thread(_get)


async def create_user(telegram_id, username=None, full_name=None):
    def _create():
        conn = _get_conn()
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        cur.execute('INSERT OR IGNORE INTO users (telegram_id, username, full_name, created_at) VALUES (?, ?, ?, ?)',
                    (telegram_id, username, full_name, now))
        conn.commit()
        cur.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    return await asyncio.to_thread(_create)


# Orders
async def add_order_for_telegram(telegram_id, description):
    def _add():
        conn = _get_conn()
        cur = conn.cursor()
        # ensure user exists
        cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        user_id = row['id']
        now = datetime.utcnow().isoformat()
        cur.execute('INSERT INTO orders (user_id, description, created_at) VALUES (?, ?, ?)', (user_id, description, now))
        conn.commit()
        order_id = cur.lastrowid
        cur.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        order = cur.fetchone()
        conn.close()
        return dict(order)
    return await asyncio.to_thread(_add)


async def list_orders_for_telegram(telegram_id):
    def _list():
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return []
        user_id = row['id']
        cur.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    return await asyncio.to_thread(_list)


async def delete_order_for_telegram(telegram_id, order_id):
    def _delete():
        conn = _get_conn()
        cur = conn.cursor()
        # verify ownership
        cur.execute('SELECT o.id FROM orders o JOIN users u ON o.user_id = u.id WHERE o.id = ? AND u.telegram_id = ?', (order_id, telegram_id))
        if not cur.fetchone():
            conn.close()
            return False
        cur.execute('DELETE FROM orders WHERE id = ?', (order_id,))
        conn.commit()
        conn.close()
        return True
    return await asyncio.to_thread(_delete)


async def stats_for_telegram(telegram_id):
    def _stats():
        conn = _get_conn()
        cur = conn.cursor()
        # total orders
        cur.execute('SELECT COUNT(*) AS cnt FROM orders')
        total = cur.fetchone()['cnt']
        # user orders
        cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cur.fetchone()
        user_count = 0
        if row:
            uid = row['id']
            cur.execute('SELECT COUNT(*) AS cnt FROM orders WHERE user_id = ?', (uid,))
            user_count = cur.fetchone()['cnt']
        # recent orders sample
        cur.execute('SELECT o.id, u.username, o.description, o.created_at FROM orders o JOIN users u ON o.user_id=u.id ORDER BY o.created_at DESC LIMIT 5')
        recent = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {'total_orders': total, 'user_orders': user_count, 'recent': recent}
    return await asyncio.to_thread(_stats)
