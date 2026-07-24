import os
import sqlite3
import sys


def data_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DB_PATH = os.path.join(data_dir(), 'woge.db')


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS material(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT DEFAULT '',
        name TEXT DEFAULT '',
        spec TEXT DEFAULT '',
        code TEXT DEFAULT '',
        unit TEXT DEFAULT '',
        price REAL DEFAULT 0,
        qty REAL DEFAULT 0,
        date TEXT DEFAULT '',
        contract_no TEXT DEFAULT '',
        total REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS quote(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_date TEXT DEFAULT '',
        project_name TEXT DEFAULT '',
        contract_no TEXT DEFAULT '',
        plan TEXT DEFAULT '',
        seller TEXT DEFAULT '',
        buyer TEXT DEFAULT '',
        total REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS quote_item(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_id INTEGER,
        seq INTEGER,
        name TEXT DEFAULT '',
        spec TEXT DEFAULT '',
        code TEXT DEFAULT '',
        price REAL DEFAULT 0,
        unit TEXT DEFAULT '',
        qty REAL DEFAULT 0,
        total REAL DEFAULT 0,
        remark TEXT DEFAULT '')''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_material_code ON material(code)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_material_name ON material(name)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_material_contract ON material(contract_no)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_item_quote ON quote_item(quote_id)')
    c.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        password TEXT DEFAULT '',
        disabled INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0)''')
    cols = [r[1] for r in c.execute('PRAGMA table_info(users)').fetchall()]
    if 'password' not in cols:
        c.execute("ALTER TABLE users ADD COLUMN password TEXT DEFAULT ''")
    c.execute("UPDATE users SET password='WOGE' WHERE password IS NULL OR password=''")
    if not c.execute('SELECT 1 FROM users LIMIT 1').fetchone():
        c.execute("INSERT INTO users(name, password, disabled, is_admin) VALUES('woge', 'WOGE', 0, 1)")
    conn.commit()
    conn.close()
