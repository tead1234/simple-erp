import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

BACKUP_DIR = Path("backups")
KEEP_DAYS = int(os.getenv("BACKUP_KEEP_DAYS", 7))


def create_backup() -> Path:
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"erp_{timestamp}.db"
    shutil.copy2("erp.db", backup_path)
    _cleanup_old(KEEP_DAYS)
    return backup_path


def _cleanup_old(keep_days: int):
    cutoff = datetime.now() - timedelta(days=keep_days)
    for f in BACKUP_DIR.glob("erp_*.db"):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            f.unlink()
