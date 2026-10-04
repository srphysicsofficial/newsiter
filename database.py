"""Small psycopg2 adapter; each transaction closes its connection."""
import os
import hashlib
import threading
from pathlib import Path
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'))
Error = psycopg2.Error
_slots = threading.BoundedSemaphore(2)

class Result:
    def __init__(self, cursor, inserted=False):
        self.cursor = cursor
        self.lastrowid = cursor.fetchone()[0] if inserted else None
    def fetchone(self):
        return self.cursor.fetchone()
    def fetchall(self):
        return self.cursor.fetchall()

class Connection:
    def __init__(self):
        url = os.environ.get('DATABASE_URL', '')
        if not url:
            raise RuntimeError('DATABASE_URL is missing from .env')
        if not _slots.acquire(timeout=8):
            raise psycopg2.OperationalError('Database is busy; retry shortly')
        try:
            self.raw = psycopg2.connect(url, connect_timeout=8,
                application_name='srphysics-web', options='-c timezone=UTC -c statement_timeout=15000 -c lock_timeout=8000')
        except Exception:
            _slots.release()
            raise
        self.cursors = []
        try:
            schema = os.environ.get('SR_DB_SCHEMA', 'sr_physics_local')
            with self.raw.cursor() as cur:
                cur.execute(sql.SQL('SET search_path TO {}, public').format(sql.Identifier(schema)))
        except Exception:
            self.raw.close()
            _slots.release()
            raise
    def execute(self, query, params=None):
        inserted = isinstance(query, str) and query.lstrip().upper().startswith('INSERT INTO')
        if inserted:
            query = query.rstrip().rstrip(';') + ' RETURNING id'
        cur = self.raw.cursor(cursor_factory=DictCursor)
        self.cursors.append(cur)
        cur.execute(query, params)
        return Result(cur, inserted)
    def __enter__(self):
        return self
    def __exit__(self, typ, value, traceback):
        try:
            if typ is None:
                self.raw.commit()
            else:
                self.raw.rollback()
        finally:
            for cur in self.cursors:
                cur.close()
            self.raw.close()
            _slots.release()

connect = Connection

def schema_lock(conn):
    schema = os.environ.get('SR_DB_SCHEMA', 'sr_physics_local')
    key = int.from_bytes(hashlib.sha256(schema.encode()).digest()[:8], 'big') & ((1 << 63) - 1)
    conn.execute('SELECT pg_advisory_xact_lock(%s)', (key,))

def ensure_schema():
    with connect() as conn:
        schema_lock(conn)
        schema = os.environ.get('SR_DB_SCHEMA', 'sr_physics_local')
        conn.execute(sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(schema)))
