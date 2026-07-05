"""
기존 erp.db에 새 테이블/컬럼을 추가하는 마이그레이션 스크립트.
기존 데이터는 건드리지 않음.
"""
import os
import sqlite3
from datetime import datetime
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./erp.db")
DB_PATH = Path(DATABASE_URL.replace("sqlite:///", "", 1))


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 현재 테이블 목록
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cur.fetchall()}

    # ── 신규 테이블 생성 ──────────────────────────────────────────

    if "equipment" not in existing_tables:
        cur.execute("""
            CREATE TABLE equipment (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER REFERENCES customers(id),
                chassis_number VARCHAR(100),
                machine_type VARCHAR(100),
                model_name VARCHAR(100),
                purchase_date DATETIME,
                memo TEXT,
                created_at DATETIME
            )
        """)
        print("OK equipment 테이블 생성")

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
                mobile VARCHAR(20),
                email VARCHAR(100),
                bank_account VARCHAR(100),
                updated_at DATETIME
            )
        """)
        print("OK company_settings 테이블 생성")
    else:
        cur.execute("PRAGMA table_info(company_settings)")
        existing_cs_cols = {row[1] for row in cur.fetchall()}
        for col_name, col_def in [
            ("mobile",       "VARCHAR(20)"),
            ("email",        "VARCHAR(100)"),
            ("bank_account", "VARCHAR(100)"),
        ]:
            if col_name not in existing_cs_cols:
                cur.execute(f"ALTER TABLE company_settings ADD COLUMN {col_name} {col_def}")
                print(f"OK company_settings.{col_name} 컬럼 추가")

    # ── company_settings 기본값(진성농기계) 최초 등록 ────────────────

    cur.execute("SELECT COUNT(*) FROM company_settings")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO company_settings
                (registration_number, company_name, owner_name, address,
                 business_type, business_category, phone, mobile, email, bank_account, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "872-09-03007", "진성농기계", "안향진",
            "경기도 용인시 처인구 원삼면 죽양대로 1626번길 47",
            "도소매", "농기계수리", "031-336-7825", "010-2494-6187",
            "ahj82993@naver.com", "농협 351-1325-9033-33", datetime.now().isoformat(sep=" "),
        ))
        print("OK company_settings 기본값(진성농기계) 등록")

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
                product_id INTEGER REFERENCES products(id),
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
    else:
        cur.execute("PRAGMA table_info(estimate_items)")
        existing_ei_cols = {row[1] for row in cur.fetchall()}
        if "product_id" not in existing_ei_cols:
            cur.execute("ALTER TABLE estimate_items ADD COLUMN product_id INTEGER REFERENCES products(id)")
            print("OK estimate_items.product_id 컬럼 추가")

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

    # ── sales 컬럼 추가 ──────────────────────────────────────────

    if "sales" in existing_tables:
        cur.execute("PRAGMA table_info(sales)")
        existing_sale_cols = {row[1] for row in cur.fetchall()}

        if "machine_category" not in existing_sale_cols:
            cur.execute("ALTER TABLE sales ADD COLUMN machine_category VARCHAR(20)")
            print("OK sales.machine_category 컬럼 추가")

    if "sale_items" in existing_tables:
        cur.execute("PRAGMA table_info(sale_items)")
        existing_sale_item_cols = {row[1] for row in cur.fetchall()}

        if "chassis_number" not in existing_sale_item_cols:
            cur.execute("ALTER TABLE sale_items ADD COLUMN chassis_number VARCHAR(100)")
            print("OK sale_items.chassis_number 컬럼 추가")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_sale_items_chassis_number ON sale_items(chassis_number)")

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

    # ── products 컬럼 추가 ───────────────────────────────────────

    cur.execute("PRAGMA table_info(products)")
    existing_product_cols = {row[1] for row in cur.fetchall()}

    product_cols = [
        ("model",           "VARCHAR(200)"),
        ("dealer_price",    "REAL DEFAULT 0"),
        ("center_price",    "REAL DEFAULT 0"),
        ("consumer_price",  "REAL DEFAULT 0"),
        ("old_code",        "VARCHAR(50)"),
        ("updated_at",      "DATETIME"),
    ]
    for col_name, col_def in product_cols:
        if col_name not in existing_product_cols:
            cur.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_def}")
            print(f"OK products.{col_name} 컬럼 추가")

    cur.execute("UPDATE products SET updated_at = created_at WHERE updated_at IS NULL")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_products_old_code ON products(old_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_products_name ON products(name)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_products_updated_at ON products(updated_at)")

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

    # ── 정비 상태 4단계(접수/작업중/완료/출고) → 3단계(작업중/완료/출고) 정리 ──

    cur.execute("UPDATE maintenance_orders SET status = '작업중' WHERE status = '접수'")
    if cur.rowcount:
        print(f"OK maintenance_orders.status '접수' → '작업중' {cur.rowcount}건 변경")

    if "maintenance_photos" not in existing_tables:
        cur.execute("""
            CREATE TABLE maintenance_photos (
                id INTEGER PRIMARY KEY,
                maintenance_id INTEGER NOT NULL REFERENCES maintenance_orders(id),
                content_type VARCHAR(50) NOT NULL,
                image_data BLOB,
                drive_file_id VARCHAR(100),
                created_at DATETIME
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_maintenance_photos_maintenance_id ON maintenance_photos(maintenance_id)")
        print("OK maintenance_photos 테이블 생성")
    else:
        cur.execute("PRAGMA table_info(maintenance_photos)")
        existing_photo_cols = {row[1] for row in cur.fetchall()}
        if "drive_file_id" not in existing_photo_cols:
            # 사진 저장소를 SQLite BLOB → 구글 드라이브로 전환. image_data는 NOT NULL이라
            # 컬럼만 추가해서는 안 되고(신규 사진은 BLOB을 안 채움), 이 시점엔 저장된
            # 사진이 없으므로(image_data 참조 코드 자체가 없어짐) 테이블을 재생성한다.
            cur.execute("SELECT COUNT(*) FROM maintenance_photos")
            if cur.fetchone()[0] == 0:
                cur.execute("DROP TABLE maintenance_photos")
                cur.execute("""
                    CREATE TABLE maintenance_photos (
                        id INTEGER PRIMARY KEY,
                        maintenance_id INTEGER NOT NULL REFERENCES maintenance_orders(id),
                        content_type VARCHAR(50) NOT NULL,
                        image_data BLOB,
                        drive_file_id VARCHAR(100),
                        created_at DATETIME
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS ix_maintenance_photos_maintenance_id ON maintenance_photos(maintenance_id)")
                print("OK maintenance_photos 테이블 재생성 (drive_file_id 추가)")
            else:
                cur.execute("ALTER TABLE maintenance_photos ADD COLUMN drive_file_id VARCHAR(100)")
                print("OK maintenance_photos.drive_file_id 컬럼 추가 (기존 BLOB 사진은 이관되지 않음)")

    # ── customers.is_active 컬럼 추가 (소프트 삭제용) ──────────────

    cur.execute("PRAGMA table_info(customers)")
    existing_customer_cols = {row[1] for row in cur.fetchall()}
    if "is_active" not in existing_customer_cols:
        cur.execute("ALTER TABLE customers ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1")
        print("OK customers.is_active 컬럼 추가")

    conn.commit()
    conn.close()
    print("\n마이그레이션 완료.")


if __name__ == "__main__":
    migrate()
