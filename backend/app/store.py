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
    migrate()


def migrate():
    # Additive, transactional migration; legacy cards and export history stay intact.
    with db(write=True) as c:
        c.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY)')
        if not c.execute('SELECT 1 FROM schema_migrations WHERE version=1').fetchone():
            c.execute('CREATE TABLE catalog_items(id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            c.execute('CREATE TABLE catalog_versions(item_id TEXT NOT NULL REFERENCES catalog_items(id), version INTEGER NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(item_id,version))')
            c.execute('CREATE TABLE catalog_capabilities(id TEXT PRIMARY KEY, fetched_at TEXT NOT NULL, payload TEXT NOT NULL)')
            c.execute('INSERT INTO schema_migrations VALUES(1)')
        if not c.execute('SELECT 1 FROM schema_migrations WHERE version=2').fetchone():
            c.execute('CREATE TABLE decompositions(id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            c.execute('CREATE TABLE decomposition_versions(id TEXT NOT NULL REFERENCES decompositions(id), version INTEGER NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(id,version))')
            c.execute('CREATE TABLE recipes(id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            c.execute('INSERT INTO schema_migrations VALUES(2)')
        if not c.execute('SELECT 1 FROM schema_migrations WHERE version=3').fetchone():
            c.execute('CREATE TABLE catalog_export_plans(id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            c.execute('CREATE TABLE catalog_exports(item_id TEXT NOT NULL, target TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(item_id,target))')
            c.execute('INSERT INTO schema_migrations VALUES(3)')


def encode(value):
    return json.dumps(value, ensure_ascii=False, default=str)
