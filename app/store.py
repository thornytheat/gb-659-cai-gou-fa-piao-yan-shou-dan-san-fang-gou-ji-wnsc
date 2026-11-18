import sqlite3
from app.config import DATABASE_PATH

def connect():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)

def init_db():
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, input_sha256 TEXT NOT NULL, accepted INTEGER NOT NULL, quarantined INTEGER NOT NULL)")
        db.execute("""CREATE TABLE IF NOT EXISTS return_ledger (
            return_no TEXT PRIMARY KEY,
            sku TEXT NOT NULL,
            tax_rate TEXT NOT NULL,
            unit_price TEXT NOT NULL,
            return_boxes TEXT NOT NULL,
            total_pieces TEXT NOT NULL,
            conservative_pieces TEXT NOT NULL,
            covered_pieces TEXT NOT NULL,
            initial_tax TEXT NOT NULL,
            added_tax TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS return_batches (
            return_no TEXT NOT NULL,
            batch_no TEXT NOT NULL,
            pack_code TEXT NOT NULL,
            pieces_per_box TEXT NOT NULL,
            boxes TEXT NOT NULL,
            batch_pieces TEXT NOT NULL,
            batch_tax TEXT NOT NULL,
            run_id TEXT NOT NULL,
            PRIMARY KEY (return_no, batch_no)
        )""")
        # 同一运行（输入摘要+规则版本）对同一退货只能落一次账，重跑直接复用，不重复冲税。
        db.execute("""CREATE TABLE IF NOT EXISTS credit_events (
            run_id TEXT NOT NULL,
            return_no TEXT NOT NULL,
            stage TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (run_id, return_no, stage)
        )""")

def record_run(manifest: dict) -> bool:
    init_db()
    with connect() as db:
        before = db.total_changes
        db.execute("INSERT OR IGNORE INTO runs VALUES (?, ?, ?, ?)", (manifest["run_id"], manifest["input_sha256"], manifest["accepted"], manifest["quarantined"]))
        return db.total_changes > before

def run_count() -> int:
    init_db()
    with connect() as db:
        return db.execute("SELECT COUNT(*) FROM runs").fetchone()[0]

def save_return_ledger(record: dict) -> bool:
    """插入退货台账头。业务键 return_no 已存在则返回 False（幂等复用）。"""
    init_db()
    with connect() as db:
        before = db.total_changes
        db.execute("""INSERT OR IGNORE INTO return_ledger
            (return_no, sku, tax_rate, unit_price, return_boxes, total_pieces,
             conservative_pieces, covered_pieces, initial_tax, added_tax,
             status, created_at, updated_at)
            VALUES (:return_no, :sku, :tax_rate, :unit_price, :return_boxes, :total_pieces,
                    :conservative_pieces, :covered_pieces, :initial_tax, :added_tax,
                    :status, :created_at, :updated_at)""", record)
        return db.total_changes > before

def get_return_ledger(return_no: str) -> dict | None:
    init_db()
    with connect() as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM return_ledger WHERE return_no = ?", (return_no,)).fetchone()
        return dict(row) if row else None

def list_return_ledger() -> list[dict]:
    init_db()
    with connect() as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute("SELECT * FROM return_ledger ORDER BY return_no").fetchall()]

def update_return_progress(return_no: str, covered_pieces: str, added_tax: str,
                           status: str, updated_at: str) -> None:
    init_db()
    with connect() as db:
        db.execute("""UPDATE return_ledger
            SET covered_pieces = ?, added_tax = ?, status = ?, updated_at = ?
            WHERE return_no = ?""", (covered_pieces, added_tax, status, updated_at, return_no))

def record_batch_evidence(row: dict) -> bool:
    """登记批号补齐证据；同退货同批号重复提交返回 False，不重复追加冲税。"""
    init_db()
    with connect() as db:
        before = db.total_changes
        db.execute("""INSERT OR IGNORE INTO return_batches
            (return_no, batch_no, pack_code, pieces_per_box, boxes,
             batch_pieces, batch_tax, run_id)
            VALUES (:return_no, :batch_no, :pack_code, :pieces_per_box, :boxes,
                    :batch_pieces, :batch_tax, :run_id)""", row)
        return db.total_changes > before

def list_batch_evidence(return_no: str) -> list[dict]:
    init_db()
    with connect() as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(
            "SELECT * FROM return_batches WHERE return_no = ? ORDER BY batch_no", (return_no,)).fetchall()]

def record_credit_event(run_id: str, return_no: str, stage: str, created_at: str) -> bool:
    """运行级幂等闸门：同一 run_id 重复执行不产生第二笔冲税事件。"""
    init_db()
    with connect() as db:
        before = db.total_changes
        db.execute("INSERT OR IGNORE INTO credit_events VALUES (?, ?, ?, ?)",
                   (run_id, return_no, stage, created_at))
        return db.total_changes > before
