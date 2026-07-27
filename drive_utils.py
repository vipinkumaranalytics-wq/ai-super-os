from __future__ import annotations
import shutil, datetime
from pathlib import Path

DRIVE_ROOT = Path("/content/drive/MyDrive/ai_super_os")
DB_PATH    = DRIVE_ROOT / "ai_super_os.db"
BACKUP_DIR = DRIVE_ROOT / "backups"

def backup_database():
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = BACKUP_DIR / f"backup_{ts}.db"
        shutil.copy2(str(DB_PATH), str(dst))
        return {"success": True, "backup_path": str(dst)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def list_backups():
    try:
        return sorted([
            {"path": str(f), "size": f.stat().st_size,
             "created": datetime.datetime.fromtimestamp(
                 f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")}
            for f in BACKUP_DIR.glob("backup_*.db")
        ], key=lambda x: x["created"], reverse=True)
    except Exception:
        return []

def get_drive_usage():
    try:
        total = sum(f.stat().st_size for f in DRIVE_ROOT.rglob("*") if f.is_file())
        return {"total_bytes": total}
    except Exception:
        return {"total_bytes": 0}

def save_to_knowledge_base(filename, content, summary=""):
    try:
        kb = DRIVE_ROOT / "knowledge_base"
        kb.mkdir(exist_ok=True)
        (kb / filename).write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False
