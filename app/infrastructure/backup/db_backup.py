import os
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from app.infrastructure.database.session import engine

BACKUP_DIR = Path("backups")
LOG_DIR = Path("logs")
KEEP_DAYS = int(os.getenv("BACKUP_KEEP_DAYS", 7))


def create_backup() -> Path:
    BACKUP_DIR.mkdir(exist_ok=True)
    # WAL 모드에서는 최근 커밋이 erp.db-wal에 남아있을 수 있어, 그대로 복사하면
    # 최근 데이터가 누락되거나 손상된 스냅샷이 만들어질 수 있다. 복사 전 체크포인트로 반영.
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA wal_checkpoint(FULL)")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"erp_{timestamp}.db"
    shutil.copy2("erp.db", backup_path)
    _cleanup_old(BACKUP_DIR, "erp_*.db", KEEP_DAYS)
    return backup_path


def restore_backup(data: bytes) -> None:
    """업로드된 sqlite DB 파일로 현재 DB를 교체 (교체 전 현재 DB는 안전 백업으로 남김).
    업로드된 파일이 옛날 스키마(배포 전 백업)일 수 있어 교체 직후 migrate()로 스키마를 맞춘다."""
    if not data.startswith(b"SQLite format 3\x00"):
        raise ValueError("올바른 SQLite DB 파일이 아닙니다")
    create_backup()
    db_path = Path(engine.url.database)
    tmp_path = Path(str(db_path) + ".upload")
    tmp_path.write_bytes(data)
    engine.dispose()
    os.replace(tmp_path, db_path)
    for suffix in ("-wal", "-shm"):
        Path(str(db_path) + suffix).unlink(missing_ok=True)
    from migrate import migrate
    migrate()


def create_diagnostics_zip() -> Path:
    """DB 백업 + 로그 파일을 압축한 진단용 zip 생성 (문제 발생 시 의뢰인이 받아서 전달하는 용도)."""
    BACKUP_DIR.mkdir(exist_ok=True)
    db_backup_path = create_backup()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = BACKUP_DIR / f"diagnostics_{timestamp}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_backup_path, arcname=db_backup_path.name)
        if LOG_DIR.exists():
            for f in LOG_DIR.glob("erp.log*"):
                zf.write(f, arcname=f"logs/{f.name}")
    _cleanup_old(BACKUP_DIR, "diagnostics_*.zip", KEEP_DAYS)
    return zip_path


def _cleanup_old(directory: Path, pattern: str, keep_days: int):
    cutoff = datetime.now() - timedelta(days=keep_days)
    for f in directory.glob(pattern):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            f.unlink()
