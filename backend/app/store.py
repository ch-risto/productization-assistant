import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def path():
    value = os.getenv('APP_DATABASE_URL', 'sqlite:///data/app.db')
    if not value.startswith('sqlite:///'):
        raise ValueError('Only sqlite:/// is supported')
    p = Path(value.removeprefix('sqlite:///'))
    return p if p.is_absolute() else ROOT / p


@contextmanager
def db(write=False):
    p = path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p, timeout=45)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA foreign_keys=ON')
        if write:
            conn.execute('BEGIN IMMEDIATE')
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS cards(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS card_history(card_id TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(card_id,version));
        CREATE TABLE IF NOT EXISTS exports(export_key TEXT PRIMARY KEY, card_id TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL, remote_id INTEGER, error TEXT);
        CREATE TABLE IF NOT EXISTS fixture_products(code TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS seed_map(target TEXT NOT NULL, source_id TEXT NOT NULL, remote_id INTEGER NOT NULL, PRIMARY KEY(target,source_id));
        ''')


def encode(value):
    return json.dumps(value, ensure_ascii=False, default=str)
