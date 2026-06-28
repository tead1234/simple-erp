"""
기존 erp.db에 새 테이블/컬럼을 추가하는 마이그레이션 스크립트.
기존 데이터는 건드리지 않음.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("erp.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 현재 테이블 목록
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cur.fetchall()}

    # ── 신규 테이블 생성 ──────────────────────────────────────────

    if "company_settings" not in existing_tables:
        cur.execute("""
            CREATE TABLE company_settings (
                id INTEGER PRIMARY KEY,
                registration_number VARCHAR(20),
                company_name VARCHAR(100),
                owner_name VARCHAR(50),
                address VARCHAR(200),
                business_type VARCHAR(50),
                business_category VARCHAR(50),
                phone VARCHAR(20),
                updated_at DATETIME
            )
        """)
        print("OK company_settings 테이블 생성")

    if "estimates" not in existing_tables:
        cur.execute("""
            CREATE TABLE estimates (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER REFERENCES customers(id),
                contractor_name VARCHAR(100),
                estimate_date DATETIME NOT NULL,
                subtotal REAL DEFAULT 0,
                vat_amount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                memo TEXT,
                status VARCHAR(10) DEFAULT '작성',
                created_at DATETIME
            )
        """)
        print("OK estimates 테이블 생성")

    if "estimate_items" not in existing_tables:
        cur.execute("""
            CREATE TABLE estimate_items (
                id INTEGER PRIMARY KEY,
                estimate_id INTEGER NOT NULL REFERENCES estimates(id),
                item_number INTEGER,
                region VARCHAR(50),
                model_name VARCHAR(100),
                spec VARCHAR(100),
                quantity INTEGER DEFAULT 1,
                unit_price REAL DEFAULT 0,
                amount REAL DEFAULT 0,
                vat REAL DEFAULT 0
            )
        """)
        print("OK estimate_items 테이블 생성")

    if "payments" not in existing_tables:
        cur.execute("""
            CREATE TABLE payments (
                id INTEGER PRIMARY KEY,
                maintenance_id INTEGER NOT NULL REFERENCES maintenance_orders(id),
                amount REAL NOT NULL,
                payment_date DATETIME NOT NULL,
                memo VARCHAR(200),
                created_at DATETIME
            )
        """)
        print("OK payments 테이블 생성")

    # ── maintenance_orders 컬럼 추가 ─────────────────────────────

    cur.execute("PRAGMA table_info(maintenance_orders)")
    existing_cols = {row[1] for row in cur.fetchall()}

    new_cols = [
        ("estimate_id",    "INTEGER REFERENCES estimates(id)"),
        ("machine_type",   "VARCHAR(100)"),
        ("machine_number", "VARCHAR(100)"),
        ("symptom",        "TEXT"),
        ("total_amount",   "REAL DEFAULT 0"),
        ("completed_date", "DATETIME"),
        ("released_date",  "DATETIME"),
    ]
    for col_name, col_def in new_cols:
        if col_name not in existing_cols:
            cur.execute(f"ALTER TABLE maintenance_orders ADD COLUMN {col_name} {col_def}")
            print(f"OK maintenance_orders.{col_name} 컬럼 추가")

    # ── maintenance_parts 컬럼 추가 ──────────────────────────────

    cur.execute("PRAGMA table_info(maintenance_parts)")
    existing_part_cols = {row[1] for row in cur.fetchall()}

    part_cols = [
        ("part_name", "VARCHAR(100)"),
        ("amount",    "REAL DEFAULT 0"),
    ]
    for col_name, col_def in part_cols:
        if col_name not in existing_part_cols:
            cur.execute(f"ALTER TABLE maintenance_parts ADD COLUMN {col_name} {col_def}")
            print(f"OK maintenance_parts.{col_name} 컬럼 추가")

    # product_id nullable 변경은 SQLite에서 직접 불가 — 기존 데이터 그대로 유지

    conn.commit()
    conn.close()
    print("\n마이그레이션 완료.")


if __name__ == "__main__":
    migrate()
